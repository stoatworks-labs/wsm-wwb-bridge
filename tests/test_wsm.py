import unittest

from wsm_wwb_bridge.model import Channel, CoordinationList
from wsm_wwb_bridge.wsm import DEFAULT_TYPE, read_wsm_csv, write_wsm_csv


class TestReadWsmCsv(unittest.TestCase):
    def test_real_discrete_frequency_shape(self):
        # Matches an actual WSM 4.9.0.13 export exactly (manually-created
        # discrete frequency entry): lowercase headers, semicolon-delimited,
        # kHz, minfrequency == maxfrequency == frequency, type=0.
        text = (
            "name;type;frequency;tolerance;minfrequency;maxfrequency;priority;squelchlevel\n"
            "Frequency 001;0;510100;0;510100;510100;2;5\n"
        )
        cl = read_wsm_csv(text)
        self.assertEqual(len(cl), 1)
        ch = cl.channels[0]
        self.assertEqual(ch.name, "Frequency 001")
        self.assertAlmostEqual(ch.frequency_mhz, 510.1)
        self.assertEqual(ch.device_type, "0")

    def test_real_band_shape(self):
        # A whole-spectrum band entry (type=2) -- not a discrete channel,
        # but should still parse without error since we don't filter by type.
        text = (
            "name;type;frequency;tolerance;minfrequency;maxfrequency;priority;squelchlevel\n"
            "Band 001;2;705000;0;400000;4000000;2;5\n"
        )
        cl = read_wsm_csv(text)
        self.assertEqual(len(cl), 1)
        self.assertAlmostEqual(cl.channels[0].frequency_mhz, 705.0)
        self.assertEqual(cl.channels[0].device_type, "2")

    def test_header_row_stripped(self):
        text = "name;type;frequency\nCH1;0;470100\n"
        cl = read_wsm_csv(text)
        self.assertEqual(len(cl), 1)
        self.assertEqual(cl.channels[0].name, "CH1")

    def test_no_header_still_parses(self):
        text = "CH1;0;470100\nCH2;0;471100\n"
        cl = read_wsm_csv(text)
        self.assertEqual(len(cl), 2)

    def test_blank_lines_ignored(self):
        text = "name;type;frequency\nCH1;0;470100\n\n\n"
        cl = read_wsm_csv(text)
        self.assertEqual(len(cl), 1)

    def test_row_missing_name_gets_fallback(self):
        text = "name;type;frequency\n;0;470100\n"
        cl = read_wsm_csv(text)
        self.assertEqual(cl.channels[0].name, "CH 1")

    def test_short_row_skipped(self):
        text = "name;type;frequency\nCH1;0\n"
        cl = read_wsm_csv(text)
        self.assertEqual(len(cl), 0)


class TestWriteWsmCsv(unittest.TestCase):
    def test_matches_real_discrete_shape(self):
        cl = CoordinationList(channels=[Channel(name="Frequency 001", frequency_mhz=510.1)])
        out = write_wsm_csv(cl)
        lines = out.splitlines()  # csv.writer defaults to \r\n line endings
        self.assertEqual(
            lines[0],
            "name;type;frequency;tolerance;minfrequency;maxfrequency;priority;squelchlevel",
        )
        self.assertEqual(lines[1], "Frequency 001;0;510100;0;510100;510100;;")

    def test_default_type_is_verified_discrete_code(self):
        self.assertEqual(DEFAULT_TYPE, "0")

    def test_device_type_overrides_default(self):
        cl = CoordinationList(channels=[Channel(name="X", frequency_mhz=470.0, device_type="7")])
        out = write_wsm_csv(cl)
        self.assertIn("X;7;470000", out)

    def test_round_trip(self):
        original = CoordinationList(channels=[
            Channel(name="Lead Vocal", frequency_mhz=606.25),
            Channel(name="Host Mic", frequency_mhz=614.1),
        ])
        out = write_wsm_csv(original)
        back = read_wsm_csv(out)
        self.assertEqual(len(back), 2)
        self.assertAlmostEqual(back.channels[0].frequency_mhz, 606.25)
        self.assertAlmostEqual(back.channels[1].frequency_mhz, 614.1)

    def test_empty_list_produces_header_only(self):
        out = write_wsm_csv(CoordinationList())
        self.assertEqual(out.strip("\n").count("\n"), 0)


if __name__ == "__main__":
    unittest.main()
