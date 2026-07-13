"""Parser for WWB7's "Coordination report" CSV export.

Reverse-engineered from a real export (WWB 7.8.2.63, File > Export/Print >
Coordination Report). This is NOT the simple flat table earlier versions of
this tool guessed at — it's a multi-section printable report:

    RF zone: <zone name>

    Primary frequencies (<count>)
    Type,Band,Channel name,Group & Channel,Frequency,
    <inclusion group name> (<count>),,,,,
    <type>,<band>,<name>,<G:x Ch:y>,<freq> MHz,
    ...
    No Inclusion Group (<count>),,,,,
    ...

    Backup frequencies (<count>)
    Type,Band,Source,Group & Channel,Frequency,
    ...

    (repeats per zone, then a "Frequency coordination parameters" section
    with Inclusions/Exclusions lists that are coordinator settings, not
    channels)

Rather than parse this by tracking exact section boundaries (fragile if a
future WWB version reorders things), we key off the one reliable signal: a
data row always has its frequency value, formatted "<number> MHz", in the
5th column (index 4). Section/zone/group headers are tracked as context for
whichever data rows follow them, but a row is only ever treated as a channel
if that positive frequency-column check passes — so this degrades gracefully
if headers shift, rather than silently misparsing unrelated rows.

This is a *report* export, formatted for reading/printing, not a format WWB
imports back in — use wwb.write_wwb_frequency_list() for the WWB-import
direction.
"""

import csv
import io
import re

from .freq_parse import parse_wwb_group_channel
from .model import Channel, CoordinationList

_GROUP_HEADER_RE = re.compile(r"^(.+?)\s*\(\d+\)$")
_FREQ_CELL_RE = re.compile(r"^[\d.]+\s*MHz$", re.IGNORECASE)


def looks_like_wwb_report(text: str) -> bool:
    head = text[:4000]
    return "Coordination report" in head or bool(re.search(r"RF zone:", head))


def read_wwb_report_csv(text: str) -> CoordinationList:
    result = CoordinationList(source_format="wwb-report-csv")
    zone = None
    section = None  # "primary" | "backup" | None
    inclusion_group = None

    reader = csv.reader(io.StringIO(text))
    for row in reader:
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        first = cells[0]
        rest_empty = not any(cells[1:])

        if first.startswith("RF zone:"):
            zone = first[len("RF zone:"):].strip()
            section = None
            inclusion_group = None
            continue
        if first.startswith("Primary frequencies ("):
            section = "primary"
            inclusion_group = None
            continue
        if first.startswith("Backup frequencies ("):
            section = "backup"
            inclusion_group = None
            continue
        if first == "Type" and "Frequency" in cells:
            continue  # column header row for the section we already know
        if rest_empty:
            m = _GROUP_HEADER_RE.match(first)
            if m:
                inclusion_group = m.group(1).strip()
                continue

        if len(cells) >= 5 and _FREQ_CELL_RE.match(cells[4]):
            type_, band, name_or_source, group_channel, freq_cell = cells[:5]
            try:
                freq_mhz = float(freq_cell.upper().replace("MHZ", "").strip())
            except ValueError:
                continue
            group, channel = parse_wwb_group_channel(group_channel)
            is_backup = section == "backup"
            name = name_or_source or (f"Backup {freq_mhz:.3f}" if is_backup else f"CH {len(result) + 1}")
            device_type = f"{type_} ({band})" if type_ and band else (type_ or band or None)
            result.add(Channel(
                name=name,
                frequency_mhz=freq_mhz,
                zone=zone,
                group=group,
                channel=channel,
                device_type=device_type,
                inclusion_group=inclusion_group,
                is_backup=is_backup,
            ))

    return result
