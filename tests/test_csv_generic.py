import unittest

from wsm_wwb_bridge.csv_generic import (
    read_header_and_rows,
    read_rows,
    sniff_delimiter,
    sniff_mapping,
    write_generic_csv,
)
from wsm_wwb_bridge.model import Channel, CoordinationList


class TestSniffDelimiter(unittest.TestCase):
    def test_comma(self):
        self.assertEqual(sniff_delimiter("a,b,c\n1,2,3\n"), ",")

    def test_semicolon(self):
        self.assertEqual(sniff_delimiter("a;b;c\n1;2;3\n"), ";")

    def test_tab(self):
        self.assertEqual(sniff_delimiter("a\tb\tc\n1\t2\t3\n"), "\t")


class TestReadHeaderAndRows(unittest.TestCase):
    def test_basic(self):
        text = "Name,Frequency\nCH1,470.100\nCH2,471.100\n"
        delimiter, header, rows = read_header_and_rows(text)
        self.assertEqual(delimiter, ",")
        self.assertEqual(header, ["Name", "Frequency"])
        self.assertEqual(rows, [["CH1", "470.100"], ["CH2", "471.100"]])

    def test_blank_lines_skipped(self):
        text = "Name,Frequency\n\nCH1,470.100\n\n"
        _, header, rows = read_header_and_rows(text)
        self.assertEqual(header, ["Name", "Frequency"])
        self.assertEqual(rows, [["CH1", "470.100"]])

    def test_empty_text(self):
        delimiter, header, rows = read_header_and_rows("")
        self.assertEqual(header, [])
        self.assertEqual(rows, [])


class TestSniffMapping(unittest.TestCase):
    def test_exact_aliases(self):
        header = ["Name", "Frequency", "Group", "Channel", "Type", "Manufacturer", "Notes", "Zone"]
        mapping = sniff_mapping(header)
        self.assertEqual(mapping["name"], 0)
        self.assertEqual(mapping["frequency_mhz"], 1)
        self.assertEqual(mapping["group"], 2)
        self.assertEqual(mapping["channel"], 3)
        self.assertEqual(mapping["device_type"], 4)
        self.assertEqual(mapping["manufacturer"], 5)
        self.assertEqual(mapping["notes"], 6)
        self.assertEqual(mapping["zone"], 7)

    def test_alternate_aliases(self):
        header = ["Talent", "Freq (MHz)", "Zone", "Ch", "Device", "Brand"]
        mapping = sniff_mapping(header)
        self.assertEqual(mapping["name"], 0)
        self.assertEqual(mapping["frequency_mhz"], 1)
        self.assertEqual(mapping["zone"], 2)
        self.assertEqual(mapping["channel"], 3)
        self.assertEqual(mapping["device_type"], 4)
        self.assertEqual(mapping["manufacturer"], 5)

    def test_unrecognized_headers_unmapped(self):
        header = ["Foo", "Bar"]
        mapping = sniff_mapping(header)
        self.assertTrue(all(v is None for v in mapping.values()))

    def test_case_insensitive(self):
        header = ["NAME", "FREQUENCY"]
        mapping = sniff_mapping(header)
        self.assertEqual(mapping["name"], 0)
        self.assertEqual(mapping["frequency_mhz"], 1)


class TestReadRows(unittest.TestCase):
    def test_basic_mapping(self):
        rows = [["Lead Vocal", "606.250", "A", "1"], ["Host Mic", "614.100", "A", "2"]]
        mapping = {"name": 0, "frequency_mhz": 1, "group": 2, "channel": 3,
                   "device_type": None, "manufacturer": None, "notes": None, "zone": None}
        cl = read_rows(rows, mapping)
        self.assertEqual(len(cl), 2)
        first = cl.channels[0]
        self.assertEqual(first.name, "Lead Vocal")
        self.assertAlmostEqual(first.frequency_mhz, 606.250)
        self.assertEqual(first.group, "A")
        self.assertEqual(first.channel, "1")

    def test_missing_name_gets_fallback(self):
        rows = [["", "606.250"]]
        mapping = {"name": 0, "frequency_mhz": 1, "group": None, "channel": None,
                   "device_type": None, "manufacturer": None, "notes": None, "zone": None}
        cl = read_rows(rows, mapping)
        self.assertEqual(cl.channels[0].name, "CH 1")

    def test_row_with_unparseable_frequency_skipped(self):
        rows = [["CH1", "not-a-number"], ["CH2", "470.100"]]
        mapping = {"name": 0, "frequency_mhz": 1, "group": None, "channel": None,
                   "device_type": None, "manufacturer": None, "notes": None, "zone": None}
        cl = read_rows(rows, mapping)
        self.assertEqual(len(cl), 1)
        self.assertEqual(cl.channels[0].name, "CH2")

    def test_row_with_blank_frequency_skipped(self):
        rows = [["CH1", ""]]
        mapping = {"name": 0, "frequency_mhz": 1, "group": None, "channel": None,
                   "device_type": None, "manufacturer": None, "notes": None, "zone": None}
        cl = read_rows(rows, mapping)
        self.assertEqual(len(cl), 0)

    def test_no_name_or_frequency_mapped_raises(self):
        mapping = {"name": None, "frequency_mhz": None, "group": None, "channel": None,
                   "device_type": None, "manufacturer": None, "notes": None, "zone": None}
        with self.assertRaises(ValueError):
            read_rows([["a", "b"]], mapping)

    def test_short_row_missing_columns_handled(self):
        # Row shorter than the mapped index for a field -> treated as blank, not IndexError.
        rows = [["CH1", "470.100"]]
        mapping = {"name": 0, "frequency_mhz": 1, "group": 5, "channel": None,
                   "device_type": None, "manufacturer": None, "notes": None, "zone": None}
        cl = read_rows(rows, mapping)
        self.assertEqual(len(cl), 1)
        self.assertIsNone(cl.channels[0].group)


class TestWriteGenericCsv(unittest.TestCase):
    def test_round_trip(self):
        cl = CoordinationList(channels=[
            Channel(name="Lead Vocal", frequency_mhz=606.25, zone="A", group="1",
                    channel="2", device_type="ULXD2", manufacturer="Shure", notes="note"),
        ])
        csv_text = write_generic_csv(cl)
        _, header, rows = read_header_and_rows(csv_text)
        mapping = sniff_mapping(header)
        back = read_rows(rows, mapping)
        self.assertEqual(len(back), 1)
        ch = back.channels[0]
        self.assertEqual(ch.name, "Lead Vocal")
        self.assertAlmostEqual(ch.frequency_mhz, 606.25)
        self.assertEqual(ch.zone, "A")
        self.assertEqual(ch.group, "1")
        self.assertEqual(ch.channel, "2")
        self.assertEqual(ch.device_type, "ULXD2")
        self.assertEqual(ch.manufacturer, "Shure")
        self.assertEqual(ch.notes, "note")


if __name__ == "__main__":
    unittest.main()
