import unittest

from wsm_wwb_bridge.detect import detect_format

from .test_wsm_html import SAMPLE_REPORT as SAMPLE_WSM_HTML
from .test_wsm_xml import SAMPLE_WSM
from .test_wwb_report import SAMPLE_REPORT as SAMPLE_WWB_REPORT
from .test_wwb_xml import SAMPLE_CWS, SAMPLE_SHW


class TestDetectFormat(unittest.TestCase):
    def test_wwb_shw(self):
        self.assertEqual(detect_format(SAMPLE_SHW), "wwb-xml")

    def test_wwb_cws(self):
        self.assertEqual(detect_format(SAMPLE_CWS), "wwb-xml")

    def test_wsm_project_xml(self):
        self.assertEqual(detect_format(SAMPLE_WSM), "wsm-xml")

    def test_wsm_html_report(self):
        self.assertEqual(detect_format(SAMPLE_WSM_HTML), "wsm-html")

    def test_wwb_coordination_report(self):
        self.assertEqual(detect_format(SAMPLE_WWB_REPORT), "wwb-report")

    def test_wsm_csv(self):
        text = "name;type;frequency;tolerance;minfrequency;maxfrequency;priority;squelchlevel\nFrequency 001;0;510100;0;510100;510100;2;5\n"
        self.assertEqual(detect_format(text), "wsm")

    def test_wwb_bare_frequency_list(self):
        self.assertEqual(detect_format("470.100\n471.100\n"), "wwb-frequency-list")

    def test_unrecognized_csv_is_generic(self):
        text = "Talent,Freq (MHz),Zone,Ch,Device,Brand\nLead Vocal,606.250,A,1,ULXD2,Shure\n"
        self.assertEqual(detect_format(text), "generic")

    def test_empty_text(self):
        # Vacuously classified as an (empty) bare frequency list, per
        # _looks_like_bare_frequency_list([]) == True -- harmless, since it
        # just round-trips to zero channels rather than misparsing anything.
        self.assertEqual(detect_format(""), "wwb-frequency-list")


if __name__ == "__main__":
    unittest.main()
