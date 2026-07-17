import unittest

from wsm_wwb_bridge.wwb_report import looks_like_wwb_report, read_wwb_report_csv

# A minimal synthetic report matching the real WWB 7.8.2.63 export shape:
# two zones, each with a primary section (one inclusion group + "No
# Inclusion Group") and a backup section.
SAMPLE_REPORT = """demo

Coordination report

RF zone: Default

Primary frequencies (2)
Type,Band,Channel name,Group & Channel,Frequency,
Group 1 (1),,,,,
ADPSM/Narrowband,G57,Shure,G:-- Ch:--,471.950 MHz,
No Inclusion Group (1),,,,,
AD/Standard,G56,Shure,G:1 Ch:2,475.025 MHz,

Backup frequencies (1)

Type,Band,Source,Group & Channel,Frequency,
No Inclusion Group (1),,,,,
AD/Standard,G56,,G:-- Ch:--,489.500 MHz,

RF zone: Zone 1

Primary frequencies (1)
Type,Band,Channel name,Group & Channel,Frequency,
No Inclusion Group (1),,,,,
AD/Standard,G56,Shure,G:-- Ch:--,471.475 MHz,

Frequency coordination parameters

Inclusions

Inclusion list: List 1

Inclusion group,Type,Frequency,TV,
Group 1,Single,471.950 MHz,,

Exclusions

Active TV channels (0)

Other exclusions (0)

Generated using Wireless Workbench 7.8.2.63
"""


class TestLooksLikeWwbReport(unittest.TestCase):
    def test_detects_coordination_report_header(self):
        self.assertTrue(looks_like_wwb_report(SAMPLE_REPORT))

    def test_detects_rf_zone_line_alone(self):
        self.assertTrue(looks_like_wwb_report("RF zone: Default\n"))

    def test_rejects_unrelated_text(self):
        self.assertFalse(looks_like_wwb_report("Name,Frequency\nCH1,470.100\n"))


class TestReadWwbReportCsv(unittest.TestCase):
    def setUp(self):
        self.cl = read_wwb_report_csv(SAMPLE_REPORT)

    def test_total_channel_count(self):
        # 2 primary + 1 backup in Default zone, 1 primary in Zone 1 = 4.
        # The inclusion-list "Group 1,Single,471.950 MHz,," row must NOT be
        # double-counted as a channel (frequency lands in a different column).
        self.assertEqual(len(self.cl), 4)

    def test_primary_backup_split(self):
        primary = [c for c in self.cl if not c.is_backup]
        backup = [c for c in self.cl if c.is_backup]
        self.assertEqual(len(primary), 3)
        self.assertEqual(len(backup), 1)

    def test_zones_assigned_correctly(self):
        zones = {c.zone for c in self.cl}
        self.assertEqual(zones, {"Default", "Zone 1"})

    def test_inclusion_group_threaded_through(self):
        first = self.cl.channels[0]
        self.assertEqual(first.name, "Shure")
        self.assertAlmostEqual(first.frequency_mhz, 471.950)
        self.assertEqual(first.inclusion_group, "Group 1")
        self.assertFalse(first.is_backup)

    def test_no_inclusion_group_recorded(self):
        second = self.cl.channels[1]
        self.assertEqual(second.inclusion_group, "No Inclusion Group")

    def test_group_channel_parsed_when_assigned(self):
        second = self.cl.channels[1]
        self.assertEqual(second.group, "1")
        self.assertEqual(second.channel, "2")

    def test_group_channel_none_when_unassigned(self):
        first = self.cl.channels[0]
        self.assertIsNone(first.group)
        self.assertIsNone(first.channel)

    def test_backup_entry_gets_generated_name(self):
        backups = [c for c in self.cl if c.is_backup]
        self.assertEqual(backups[0].name, "Backup 489.500")

    def test_device_type_combines_type_and_band(self):
        first = self.cl.channels[0]
        self.assertEqual(first.device_type, "ADPSM/Narrowband (G57)")

    def test_zone_resets_inclusion_group(self):
        zone1_channels = [c for c in self.cl if c.zone == "Zone 1"]
        self.assertEqual(len(zone1_channels), 1)
        self.assertEqual(zone1_channels[0].inclusion_group, "No Inclusion Group")

    def test_empty_report_yields_no_channels(self):
        cl = read_wwb_report_csv("Coordination report\n")
        self.assertEqual(len(cl), 0)


if __name__ == "__main__":
    unittest.main()
