"""Guess which format a loaded file is in, so the GUI can pre-select a parser."""

from .csv_generic import read_header_and_rows
from .wsm_html import looks_like_wsm_html_report
from .wsm_xml import looks_like_wsm_xml
from .wwb import _looks_like_bare_frequency_list
from .wwb_report import looks_like_wwb_report
from .wwb_xml import looks_like_wwb_xml


def detect_format(text: str) -> str:
    """Returns one of: 'wwb-xml', 'wsm-xml', 'wsm-html', 'wsm', 'wwb-report',
    'wwb-frequency-list', 'generic'."""
    if looks_like_wwb_xml(text):
        return "wwb-xml"
    if looks_like_wsm_xml(text):
        return "wsm-xml"
    if looks_like_wsm_html_report(text):
        return "wsm-html"

    delimiter, header, rows = read_header_and_rows(text)
    all_rows = ([header] + rows) if header else rows

    if header:
        first_cell = header[0].strip().lower()
        if delimiter == ";" and first_cell == "name" and len(header) >= 6:
            return "wsm"

    if looks_like_wwb_report(text):
        return "wwb-report"

    if _looks_like_bare_frequency_list(all_rows):
        return "wwb-frequency-list"

    return "generic"
