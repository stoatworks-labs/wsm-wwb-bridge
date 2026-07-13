"""Generic, header-driven CSV reader.

Neither Shure nor Sennheiser publish a single fixed schema for
coordination/inventory exports (WSM's scan/frequency-list format is
documented; WWB's structured inventory report is user-configurable, and its
plain "import frequencies" tool only accepts a bare list of numbers). Rather
than hard-code a guess at column names that may not match a given install,
this reader detects the delimiter, then fuzzy-matches whatever headers are
present onto the internal Channel fields. Call `sniff_mapping` to get a best
guess, let the user confirm/adjust it (the GUI exposes this), then call
`read_rows` with the confirmed mapping.
"""

import csv
import io
from typing import Dict, List, Optional

from .freq_parse import parse_frequency_to_mhz
from .model import Channel, CoordinationList

# Field name -> lowercase aliases we'll match against header cells.
FIELD_ALIASES = {
    "name": ["name", "label", "channel name", "tx name", "device name", "talent"],
    "frequency_mhz": [
        "frequency", "freq", "frequency (mhz)", "freq (mhz)", "frequency mhz",
        "mhz", "freq mhz", "rf frequency",
    ],
    "group": ["group", "band group", "inclusion group"],
    "channel": ["channel", "ch", "channel #", "channel number", "chan"],
    "device_type": ["type", "device type", "tx type", "model", "device"],
    "manufacturer": ["manufacturer", "make", "brand"],
    "notes": ["notes", "comment", "comments", "description"],
    "zone": ["zone", "rf zone"],
}

CHANNEL_FIELDS = list(FIELD_ALIASES.keys())


def sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|:")
        return dialect.delimiter
    except csv.Error:
        # Fall back to whichever common delimiter actually appears.
        for delim in (";", "\t", ",", "|"):
            if delim in sample:
                return delim
        return ","


def read_header_and_rows(text: str):
    delimiter = sniff_delimiter(text[:4096])
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return delimiter, [], []
    return delimiter, rows[0], rows[1:]


def sniff_mapping(header: List[str]) -> Dict[str, Optional[int]]:
    """Best-guess header-index -> Channel field mapping. None = unmapped."""
    mapping: Dict[str, Optional[int]] = {field: None for field in CHANNEL_FIELDS}
    normalized = [h.strip().lower() for h in header]
    for field, aliases in FIELD_ALIASES.items():
        for idx, cell in enumerate(normalized):
            if cell in aliases:
                mapping[field] = idx
                break
    return mapping


def read_rows(
    data_rows: List[List[str]],
    mapping: Dict[str, Optional[int]],
    source_format: str = "generic-csv",
) -> CoordinationList:
    if mapping.get("name") is None and mapping.get("frequency_mhz") is None:
        raise ValueError("At least name or frequency must be mapped to a column")

    result = CoordinationList(source_format=source_format)
    for row_num, row in enumerate(data_rows, start=1):
        def cell(field):
            idx = mapping.get(field)
            if idx is None or idx >= len(row):
                return None
            value = row[idx].strip()
            return value or None

        freq_raw = cell("frequency_mhz")
        if not freq_raw:
            continue
        try:
            freq_mhz = parse_frequency_to_mhz(freq_raw)
        except ValueError:
            continue

        name = cell("name") or f"CH {row_num}"
        result.add(
            Channel(
                name=name,
                frequency_mhz=freq_mhz,
                group=cell("group"),
                channel=cell("channel"),
                device_type=cell("device_type"),
                manufacturer=cell("manufacturer"),
                notes=cell("notes"),
                zone=cell("zone"),
            )
        )
    return result


def parse_generic_csv(text: str, mapping: Optional[Dict[str, Optional[int]]] = None):
    """Convenience one-shot parse using auto-detected mapping."""
    _, header, rows = read_header_and_rows(text)
    if mapping is None:
        mapping = sniff_mapping(header)
    return read_rows(rows, mapping)


def write_generic_csv(coord_list: CoordinationList) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Frequency (MHz)", "Zone", "Group", "Channel", "Type", "Manufacturer", "Notes"])
    for ch in coord_list:
        writer.writerow([
            ch.name, ch.display_frequency(), ch.zone or "", ch.group or "", ch.channel or "",
            ch.device_type or "", ch.manufacturer or "", ch.notes or "",
        ])
    return buf.getvalue()
