import unittest

from wsm_wwb_bridge.wsm_xml import looks_like_wsm_xml, read_wsm_project

SAMPLE_WSM = """<!DOCTYPE WSM>
<WSM Version="2.0" AppVersion="4.9.0.13">
    <FrequencyManager RFUnit="2">
        <Devices>
            <Device Version="1.0" Mode="0" UniqueId="1" Type="STANDARD">
                <Name>EW-DX 1</Name>
                <StationaryDeviceType>EW-DX EM2/EM4 (LD off)</StationaryDeviceType>
                <PortableDeviceType>EW-DX SKM</PortableDeviceType>
                <Frequency>470200</Frequency>
                <AllocatedFrequency>470800</AllocatedFrequency>
                <SquelchDescription>-87 dBm</SquelchDescription>
            </Device>
            <Device Version="1.0" Mode="0" UniqueId="2" Type="STANDARD">
                <Name>EW-DX 2</Name>
                <StationaryDeviceType>EW-DX EM2/EM4 (LD off)</StationaryDeviceType>
                <PortableDeviceType>EW-DX SKM</PortableDeviceType>
                <Frequency>470200</Frequency>
                <AllocatedFrequency></AllocatedFrequency>
            </Device>
        </Devices>
    </FrequencyManager>
</WSM>
"""

# Matches the real "uncoordinated" case: devices configured but no
# FrequencyManager/Devices section saved at all (coordination never run).
SAMPLE_WSM_NO_COORDINATION = """<!DOCTYPE WSM>
<WSM Version="2.0" AppVersion="4.9.0.13">
    <FrequencyManager RFUnit="2">
        <NoiseThreshold NoiseThresholdValue="5"/>
    </FrequencyManager>
    <SpareFrequencyPool/>
</WSM>
"""


class TestLooksLikeWsmXml(unittest.TestCase):
    def test_detects_doctype(self):
        self.assertTrue(looks_like_wsm_xml(SAMPLE_WSM))

    def test_rejects_wwb_xml(self):
        self.assertFalse(looks_like_wsm_xml('<show version="1.0"></show>'))

    def test_rejects_csv(self):
        self.assertFalse(looks_like_wsm_xml("name;type;frequency\n"))


class TestReadWsmProject(unittest.TestCase):
    def test_reads_allocated_frequency_not_current_frequency(self):
        cl = read_wsm_project(SAMPLE_WSM)
        # Only one Device has a non-empty AllocatedFrequency.
        self.assertEqual(len(cl), 1)
        ch = cl.channels[0]
        self.assertEqual(ch.name, "EW-DX 1")
        # 470800 kHz, NOT the 470200 in <Frequency> -- that field is a
        # decoy (the receiver's raw port tuning, not the coordinated result).
        self.assertAlmostEqual(ch.frequency_mhz, 470.8)

    def test_device_fields_mapped(self):
        ch = read_wsm_project(SAMPLE_WSM).channels[0]
        self.assertEqual(ch.device_type, "EW-DX EM2/EM4 (LD off)")
        self.assertEqual(ch.manufacturer, "Sennheiser")
        self.assertIn("EW-DX SKM", ch.notes)
        self.assertIn("-87 dBm", ch.notes)

    def test_empty_allocated_frequency_skipped(self):
        cl = read_wsm_project(SAMPLE_WSM)
        names = [c.name for c in cl]
        self.assertNotIn("EW-DX 2", names)

    def test_no_frequency_manager_devices_returns_empty(self):
        cl = read_wsm_project(SAMPLE_WSM_NO_COORDINATION)
        self.assertEqual(len(cl), 0)
        self.assertEqual(cl.source_format, "wsm-project")


if __name__ == "__main__":
    unittest.main()
