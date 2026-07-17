import unittest

from wsm_wwb_bridge.freq_parse import (
    format_khz,
    format_mhz,
    parse_frequency_to_mhz,
    parse_wwb_group_channel,
)


class TestParseFrequencyToMhz(unittest.TestCase):
    def test_plain_mhz_decimal(self):
        self.assertAlmostEqual(parse_frequency_to_mhz("470.100"), 470.100)

    def test_raw_khz_integer(self):
        self.assertAlmostEqual(parse_frequency_to_mhz("470100"), 470.100)

    def test_khz_threshold_boundary_stays_mhz(self):
        # Values below the kHz threshold are assumed to already be MHz.
        self.assertAlmostEqual(parse_frequency_to_mhz("2999"), 2999.0)

    def test_khz_threshold_boundary_converts(self):
        self.assertAlmostEqual(parse_frequency_to_mhz("3000"), 3.0)

    def test_comma_as_decimal_separator(self):
        self.assertAlmostEqual(parse_frequency_to_mhz("600,768"), 600.768)

    def test_comma_as_thousands_separator(self):
        # Comma AND dot present -> comma is stripped, not treated as decimal.
        # 1234.5 is below the kHz threshold, so it's taken as already-MHz,
        # not divided by 1000 -- there's no thousands-of-MHz mic frequency,
        # so this combination isn't realistic input, just defensive parsing.
        self.assertAlmostEqual(parse_frequency_to_mhz("1,234.5"), 1234.5)

    def test_whitespace_stripped(self):
        self.assertAlmostEqual(parse_frequency_to_mhz("  606.250  "), 606.250)

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_frequency_to_mhz("")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValueError):
            parse_frequency_to_mhz("   ")

    def test_non_numeric_raises(self):
        with self.assertRaises(ValueError):
            parse_frequency_to_mhz("not-a-frequency")


class TestFormatters(unittest.TestCase):
    def test_format_mhz(self):
        self.assertEqual(format_mhz(470.1), "470.100")

    def test_format_mhz_rounds_to_three_decimals(self):
        self.assertEqual(format_mhz(470.12345), "470.123")

    def test_format_khz(self):
        self.assertEqual(format_khz(470.1), "470100")

    def test_format_khz_rounds(self):
        self.assertEqual(format_khz(470.1234), "470123")

    def test_khz_and_parse_round_trip(self):
        original = 606.250
        self.assertAlmostEqual(parse_frequency_to_mhz(format_khz(original)), original)


class TestParseWwbGroupChannel(unittest.TestCase):
    def test_none_input(self):
        self.assertEqual(parse_wwb_group_channel(None), (None, None))

    def test_empty_string(self):
        self.assertEqual(parse_wwb_group_channel(""), (None, None))

    def test_report_style_unassigned(self):
        self.assertEqual(parse_wwb_group_channel("G:-- Ch:--"), (None, None))

    def test_report_style_assigned(self):
        self.assertEqual(parse_wwb_group_channel("G:1 Ch:2"), ("1", "2"))

    def test_shw_style_unassigned(self):
        self.assertEqual(parse_wwb_group_channel("--,--"), (None, None))

    def test_shw_style_assigned(self):
        self.assertEqual(parse_wwb_group_channel("1,2"), ("1", "2"))

    def test_shw_style_with_spaces(self):
        self.assertEqual(parse_wwb_group_channel(" 3 , 4 "), ("3", "4"))


if __name__ == "__main__":
    unittest.main()
