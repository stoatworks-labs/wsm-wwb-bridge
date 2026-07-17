"""Exercises the actual committed sample_data/ fixture files end to end,
so a change to those files (or a regression in the parsers) is caught."""

import unittest
from pathlib import Path

from wsm_wwb_bridge.detect import detect_format
from wsm_wwb_bridge.wsm import read_wsm_csv
from wsm_wwb_bridge.wwb import read_wwb_file

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample_data"


def _read(name):
    return (SAMPLE_DATA / name).read_text(encoding="utf-8-sig")


class TestSampleWsmExport(unittest.TestCase):
    def test_detects_as_wsm(self):
        self.assertEqual(detect_format(_read("sample_wsm_export.csv")), "wsm")

    def test_parses_four_channels(self):
        cl = read_wsm_csv(_read("sample_wsm_export.csv"))
        self.assertEqual(len(cl), 4)
        names = {c.name for c in cl}
        self.assertEqual(names, {"Lead Vocal", "Host Mic", "Guitar IEM", "Handheld 4"})


class TestSampleGenericExport(unittest.TestCase):
    def test_detects_as_generic(self):
        self.assertEqual(detect_format(_read("sample_generic_export.csv")), "generic")


class TestSampleWwbFrequencyList(unittest.TestCase):
    def test_detects_as_bare_frequency_list(self):
        self.assertEqual(detect_format(_read("sample_wwb_frequency_list.txt")), "wwb-frequency-list")

    def test_parses_four_channels(self):
        cl = read_wwb_file(_read("sample_wwb_frequency_list.txt"))
        self.assertEqual(len(cl), 4)
        self.assertAlmostEqual(cl.channels[0].frequency_mhz, 606.250)


if __name__ == "__main__":
    unittest.main()
