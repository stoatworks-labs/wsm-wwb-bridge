"""Shure Wireless Workbench (WWB) import/export.

Shure's documentation only fully specifies one CSV shape: raw scan data
(frequency, amplitude pairs). Its coordination-side tools are:

  - "Import Frequencies from File": accepts a flat list of MHz values
    (<=3 decimals), separated by comma, tab, or CR. No names, groups, or
    channel numbers travel through this path — WWB assigns them after
    import. This is the one format we can be certain WWB will accept, so
    it's the default/safe export.

  - The Inventory/Frequency List report: exportable, but its columns are
    user-configurable in the WWB UI rather than a documented fixed schema.
    write_wwb_inventory_csv() below is a best-effort shape (Name, Frequency,
    Group, Channel, Type) for round-tripping between this tool and itself,
    or as a starting point to compare against a real WWB export. If it
    doesn't import cleanly, check what headers your WWB version actually
    produces and adjust the column list here (or just use the plain
    frequency-list export, which always works).

For reading a WWB-originated file back in, we reuse the generic CSV reader
(csv_generic.py) since a structured export will have headers we can
fuzzy-match, and fall back to treating the file as a bare frequency list if
no headers are found.
"""

import csv
import io

from .csv_generic import read_header_and_rows, read_rows, sniff_mapping
from .freq_parse import format_mhz, parse_frequency_to_mhz
from .model import Channel, CoordinationList


def write_wwb_frequency_list(coord_list: CoordinationList) -> str:
    """The format WWB's 'Import Frequencies from File' is documented to accept."""
    lines = [format_mhz(ch.frequency_mhz) for ch in coord_list]
    return "\n".join(lines) + "\n"


def write_wwb_inventory_csv(coord_list: CoordinationList) -> str:
    """Best-effort structured export — see module docstring caveat."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Frequency", "Group", "Channel", "Type", "Manufacturer", "Notes"])
    for ch in coord_list:
        writer.writerow([
            ch.name, ch.display_frequency(), ch.group or "", ch.channel or "",
            ch.device_type or "", ch.manufacturer or "", ch.notes or "",
        ])
    return buf.getvalue()


def _looks_like_bare_frequency_list(rows) -> bool:
    for row in rows[:5]:
        for cell in row:
            cell = cell.strip()
            if not cell:
                continue
            try:
                parse_frequency_to_mhz(cell)
            except ValueError:
                return False
    return True


def read_wwb_file(text: str) -> CoordinationList:
    delimiter, header, rows = read_header_and_rows(text)
    all_rows = ([header] + rows) if header else rows

    if _looks_like_bare_frequency_list(all_rows):
        result = CoordinationList(source_format="wwb-frequency-list")
        n = 1
        for row in all_rows:
            for cell in row:
                cell = cell.strip()
                if not cell:
                    continue
                try:
                    freq = parse_frequency_to_mhz(cell)
                except ValueError:
                    continue
                result.add(Channel(name=f"CH {n}", frequency_mhz=freq))
                n += 1
        return result

    mapping = sniff_mapping(header)
    return read_rows(rows, mapping, source_format="wwb-csv")
