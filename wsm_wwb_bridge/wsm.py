"""Sennheiser Wireless Systems Manager (WSM) "Frequencies/Bands" CSV.

Real export (WSM 4.9.0.13, Professional Setup > Frequencies/Bands >
"Export list..."), confirmed against an actual file:

    name;type;frequency;tolerance;minfrequency;maxfrequency;priority;squelchlevel
    Band 001;2;705000;0;400000;4000000;2;5

Columns are lowercase, semicolon-delimited, frequencies in kHz. This
contradicts what Sennheiser's own docs imply (they suggest mixed-case
headers and call the range columns "lower/upper frequency") — go with the
real file.

IMPORTANT — this is NOT the same thing as a coordinated channel list.
`minfrequency`/`maxfrequency` in the one real sample spanned 400-4000 MHz,
i.e. a whole-spectrum band/scan-range definition, not a single mic's
frequency with a tight tolerance. This matches how Sennheiser's own docs
describe the WSM import flow for this file (see e.g. Soundbase's WSM
export guide): you import this as a *candidate frequency pool*, then run
WSM's own "Start Coordination" step, then manually drag-allocate results
onto specific device channels in the Allocation tab. It does not write
directly to named channels the way wsm_xml.read_wsm_project() reads them.
For getting actual per-channel coordinated frequencies out of WSM, prefer
wsm_xml.py (the .wsm project file) or wsm_html.py (the HTML report) —
both read real per-channel AllocatedFrequency data, not this pool format.

The `type` column is a numeric enum (band/discrete/interference/usable/
unusable per the HTML report's legend). Confirmed against two real
samples: type=2 was a whole-spectrum band (`minfrequency`/`maxfrequency`
400-4000 MHz), type=0 was a manually-created "Discrete frequency" entry
(`minfrequency == maxfrequency == frequency`, tolerance=0) — so 0 is
correct for a single coordinated mic frequency, which is the only kind of
entry this tool writes.
"""

import csv
import io

from .freq_parse import format_khz, parse_frequency_to_mhz
from .model import Channel, CoordinationList

DEFAULT_TYPE = "0"  # confirmed: discrete frequency, verified against a real WSM export
DELIMITER = ";"

_HEADER = ["name", "type", "frequency", "tolerance", "minfrequency", "maxfrequency", "priority", "squelchlevel"]


def _looks_like_wsm_header(row) -> bool:
    if not row:
        return False
    return row[0].strip().lower() == "name" and len(row) >= 3


def read_wsm_csv(text: str) -> CoordinationList:
    # WSM's importer tolerates several delimiters; try semicolon first
    # (its own export format), then fall back to whatever is present.
    delimiter = DELIMITER if DELIMITER in text.splitlines()[0] else None
    if delimiter is None:
        for candidate in (";", "|", ":", "\t", ","):
            if candidate in text:
                delimiter = candidate
                break
        else:
            delimiter = ";"

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if rows and _looks_like_wsm_header(rows[0]):
        rows = rows[1:]

    result = CoordinationList(source_format="wsm-csv")
    for row in rows:
        if len(row) < 3:
            continue
        name = row[0].strip() or f"CH {len(result) + 1}"
        type_code = row[1].strip() or None
        try:
            freq_mhz = parse_frequency_to_mhz(row[2])
        except ValueError:
            continue
        result.add(Channel(name=name, frequency_mhz=freq_mhz, device_type=type_code))
    return result


def write_wsm_csv(coord_list: CoordinationList) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=DELIMITER)
    writer.writerow(_HEADER)
    for ch in coord_list:
        freq_khz = format_khz(ch.frequency_mhz)
        writer.writerow([
            ch.name,
            ch.device_type or DEFAULT_TYPE,
            freq_khz,
            "0",
            freq_khz,  # min == max == frequency: a zero-width "discrete" range
            freq_khz,
            "",
            "",
        ])
    return buf.getvalue()
