import unittest

from wsm_wwb_bridge.wwb_xml import looks_like_wwb_xml, read_wwb_xml

SAMPLE_SHW = """<show version="1.0" appl_version="7.8.2.63">
    <inventory version="2.1">
        <device>
            <manufacturer type="10">Shure</manufacturer>
            <model type="10">AD4Q-A</model>
            <band type="10">G56</band>
            <zone type="12">Default</zone>
            <channel number="1">
                <channel_name type="10"><![CDATA[Lead Vocal]]></channel_name>
                <frequency type="3">470150</frequency>
                <group_channel type="10">1,2</group_channel>
            </channel>
            <channel number="2">
                <channel_name type="10"><![CDATA[Host Mic]]></channel_name>
                <frequency type="3">0</frequency>
                <group_channel type="10">--,--</group_channel>
            </channel>
        </device>
    </inventory>
</show>
"""

SAMPLE_SHW_NO_INVENTORY = """<show version="1.0">
    <coordinated_data_root>
        <mic_channels units="khz" count="1">
            <freq_entry>
                <compat_key>
                    <zone>Zone 1</zone>
                    <series>AD</series>
                    <mode>Standard</mode>
                </compat_key>
                <value>471475</value>
                <gr_ch>G:-- Ch:--</gr_ch>
                <manufacturer>Shure</manufacturer>
                <source_name>Shure</source_name>
            </freq_entry>
        </mic_channels>
    </coordinated_data_root>
</show>
"""

SAMPLE_CWS = """<coord_workspace_ex_root version="0.1">
    <coordinated_data_root>
        <mic_channels units="khz" count="2">
            <freq_entry>
                <compat_key>
                    <zone>Default</zone>
                    <series>ADPSM</series>
                    <mode>Narrowband</mode>
                </compat_key>
                <value>471950</value>
                <gr_ch>G:-- Ch:--</gr_ch>
                <manufacturer>Shure</manufacturer>
                <source_name>Shure</source_name>
            </freq_entry>
            <freq_entry>
                <compat_key>
                    <zone>Default</zone>
                    <series>AD</series>
                    <mode>Standard</mode>
                </compat_key>
                <value>475025</value>
                <gr_ch>G:1 Ch:2</gr_ch>
                <manufacturer>Shure</manufacturer>
                <source_name>Shure</source_name>
            </freq_entry>
        </mic_channels>
    </coordinated_data_root>
</coord_workspace_ex_root>
"""


class TestLooksLikeWwbXml(unittest.TestCase):
    def test_detects_show_root(self):
        self.assertTrue(looks_like_wwb_xml(SAMPLE_SHW))

    def test_detects_cws_root(self):
        self.assertTrue(looks_like_wwb_xml(SAMPLE_CWS))

    def test_rejects_csv(self):
        self.assertFalse(looks_like_wwb_xml("Name,Frequency\nCH1,470.100\n"))

    def test_rejects_wsm_xml(self):
        self.assertFalse(looks_like_wwb_xml('<WSM Version="2.0"></WSM>'))


class TestReadWwbXmlShwWithInventory(unittest.TestCase):
    def setUp(self):
        self.cl = read_wwb_xml(SAMPLE_SHW)

    def test_prefers_device_inventory(self):
        self.assertEqual(self.cl.source_format, "wwb-shw")

    def test_zero_frequency_channel_skipped(self):
        # Host Mic has frequency=0 (unassigned) and should not appear.
        self.assertEqual(len(self.cl), 1)

    def test_deployed_channel_fields(self):
        ch = self.cl.channels[0]
        self.assertEqual(ch.name, "Lead Vocal")
        self.assertAlmostEqual(ch.frequency_mhz, 470.150)
        self.assertEqual(ch.zone, "Default")
        self.assertEqual(ch.group, "1")
        self.assertEqual(ch.channel, "2")
        self.assertEqual(ch.device_type, "G56")
        self.assertEqual(ch.manufacturer, "Shure")
        self.assertIn("AD4Q-A", ch.notes)


class TestReadWwbXmlShwWithoutInventory(unittest.TestCase):
    def test_falls_back_to_candidate_pool(self):
        cl = read_wwb_xml(SAMPLE_SHW_NO_INVENTORY)
        self.assertEqual(cl.source_format, "wwb-cws")
        self.assertEqual(len(cl), 1)
        self.assertAlmostEqual(cl.channels[0].frequency_mhz, 471.475)
        self.assertEqual(cl.channels[0].zone, "Zone 1")


class TestReadWwbXmlCws(unittest.TestCase):
    def setUp(self):
        self.cl = read_wwb_xml(SAMPLE_CWS)

    def test_source_format(self):
        self.assertEqual(self.cl.source_format, "wwb-cws")

    def test_all_candidates_returned(self):
        self.assertEqual(len(self.cl), 2)

    def test_device_type_combines_series_and_mode(self):
        self.assertEqual(self.cl.channels[0].device_type, "ADPSM/Narrowband")

    def test_group_channel_parsed(self):
        self.assertIsNone(self.cl.channels[0].group)
        self.assertEqual(self.cl.channels[1].group, "1")
        self.assertEqual(self.cl.channels[1].channel, "2")


if __name__ == "__main__":
    unittest.main()
