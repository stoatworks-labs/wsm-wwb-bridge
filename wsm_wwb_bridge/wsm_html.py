"""Parser for the HTML "WSM Coordination Report" WSM can export.

Reverse-engineered from a real report. It has a "Devices:" section made of
one <table id="devices"> per device category (e.g. "FM Mics:", "IEM
Systems:", "Digital devices:" — the text of the preceding
<div class="deviceTitle">), each row:

    #, Name, Stationary device, Frequency range, Frequency, Portable device, Squelch/Max.noise

"Frequency" (not "Frequency range") is the actual assigned channel
frequency, which is what we want. Cross-checked against a same-project
.wsm export and the two agreed exactly on channel count and frequencies.

There's also a "Frequencies/Bands" table (discrete/range frequency
definitions rather than per-device assignments) which was empty in the
sample we had to build this from, so it's not parsed here. Uses the stdlib
html.parser rather than an XML parser because this document isn't
well-formed XML (unescaped entities, unclosed <img> tags).
"""

from html.parser import HTMLParser

from .model import Channel, CoordinationList


def looks_like_wsm_html_report(text: str) -> bool:
    return "WSM Coordination Report" in text[:4000]


class _DeviceTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []  # (category, [cell_text, ...])
        self._category = None
        self._category_buf = []
        self._in_device_title = False
        self._in_devices_table = False
        self._in_row = False
        self._in_cell = False
        self._current_row = []
        self._current_cell_buf = []

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == "div" and attrs_d.get("class") == "deviceTitle":
            self._in_device_title = True
            self._category_buf = []
        elif tag == "table" and attrs_d.get("id") == "devices":
            self._in_devices_table = True
        elif self._in_devices_table and tag == "tr":
            self._in_row = True
            self._current_row = []
        elif self._in_row and tag == "td":
            self._in_cell = True
            self._current_cell_buf = []

    def handle_endtag(self, tag):
        if tag == "div" and self._in_device_title:
            self._in_device_title = False
            self._category = "".join(self._category_buf).strip().rstrip(":")
        elif tag == "table" and self._in_devices_table:
            self._in_devices_table = False
        elif tag == "tr" and self._in_row:
            self._in_row = False
            if self._current_row:
                self.rows.append((self._category, self._current_row))
        elif tag == "td" and self._in_cell:
            self._in_cell = False
            self._current_row.append("".join(self._current_cell_buf).strip())

    def handle_data(self, data):
        if self._in_device_title:
            self._category_buf.append(data)
        elif self._in_cell:
            self._current_cell_buf.append(data)


def read_wsm_html_report(text: str) -> CoordinationList:
    parser = _DeviceTableParser()
    parser.feed(text)

    result = CoordinationList(source_format="wsm-html-report")
    for category, cells in parser.rows:
        cells = (cells + [""] * 7)[:7]
        _row_num, name, stationary, _freq_range, freq_cell, portable, squelch = cells
        try:
            freq_mhz = float(freq_cell.upper().replace("MHZ", "").strip())
        except ValueError:
            continue

        notes_parts = []
        if portable:
            notes_parts.append(f"TX: {portable}")
        if squelch:
            notes_parts.append(f"squelch {squelch}")

        result.add(Channel(
            name=name or f"CH {len(result) + 1}",
            frequency_mhz=freq_mhz,
            zone=category,
            device_type=stationary or None,
            manufacturer="Sennheiser",
            notes=", ".join(notes_parts) or None,
        ))
    return result
