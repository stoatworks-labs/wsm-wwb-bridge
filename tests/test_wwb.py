import unittest

from wsm_wwb_bridge.model import Channel, CoordinationList
from wsm_wwb_bridge.wwb import (
    _looks_like_bare_frequency_list,
    read_wwb_file,
    write_wwb_frequency_list,
    write_wwb_inventory_csv,
)


class TestWriteWwbFrequencyList(unittest.TestCase):
    def test_one_value_per_line_three_decimals(self):
        cl = CoordinationList(channels=[
            Channel(name="A", frequency_mhz=470.1),
            Channel(name="B", frequency_mhz=471.25),
        ])
        out = write_wwb_frequency_list(cl)
        self.assertEqual(out, "470.100\n471.250\n")

    def test_empty_list(self):
        out = write_wwb_frequency_list(CoordinationList())
        self.assertEqual(out, "\n")


class TestLooksLikeBareFrequencyList(unittest.TestCase):
    def test_all_numeric_rows(self):
        self.assertTrue(_looks_like_bare_frequency_list([["470.100"], ["471.100"]]))

    def test_mixed_named_row_rejected(self):
        self.assertFalse(_looks_like_bare_frequency_list([["Lead Vocal", "470.100"]]))

    def test_empty_rows_vacuously_true(self):
        self.assertTrue(_looks_like_bare_frequency_list([]))

    def test_only_checks_first_five_rows(self):
        rows = [["470.100"]] * 5 + [["not-a-number"]]
        self.assertTrue(_looks_like_bare_frequency_list(rows))


class TestReadWwbFile(unittest.TestCase):
    def test_bare_frequency_list(self):
        text = "470.100\n471.100\n472.100\n"
        cl = read_wwb_file(text)
        self.assertEqual(cl.source_format, "wwb-frequency-list")
        self.assertEqual(len(cl), 3)
        self.assertEqual(cl.channels[0].name, "CH 1")
        self.assertAlmostEqual(cl.channels[0].frequency_mhz, 470.1)

    def test_comma_separated_bare_list(self):
        text = "470.100,471.100,472.100"
        cl = read_wwb_file(text)
        self.assertEqual(len(cl), 3)

    def test_structured_csv_uses_column_mapping(self):
        text = "Name,Frequency\nLead Vocal,470.100\nHost Mic,471.100\n"
        cl = read_wwb_file(text)
        self.assertEqual(cl.source_format, "wwb-csv")
        self.assertEqual(len(cl), 2)
        self.assertEqual(cl.channels[0].name, "Lead Vocal")


class TestWriteWwbInventoryCsv(unittest.TestCase):
    def test_round_trip_via_generic_reader(self):
        from wsm_wwb_bridge.csv_generic import read_header_and_rows, read_rows, sniff_mapping

        cl = CoordinationList(channels=[
            Channel(name="Lead Vocal", frequency_mhz=470.1, group="A", channel="1",
                    device_type="ULXD2", manufacturer="Shure", notes="note"),
        ])
        out = write_wwb_inventory_csv(cl)
        _, header, rows = read_header_and_rows(out)
        mapping = sniff_mapping(header)
        back = read_rows(rows, mapping)
        self.assertEqual(len(back), 1)
        ch = back.channels[0]
        self.assertEqual(ch.name, "Lead Vocal")
        self.assertAlmostEqual(ch.frequency_mhz, 470.1)
        self.assertEqual(ch.group, "A")
        self.assertEqual(ch.manufacturer, "Shure")


if __name__ == "__main__":
    unittest.main()
