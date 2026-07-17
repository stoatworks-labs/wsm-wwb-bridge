import unittest

from wsm_wwb_bridge.model import Channel, CoordinationList


class TestChannel(unittest.TestCase):
    def test_defaults(self):
        ch = Channel(name="Lead Vocal", frequency_mhz=606.25)
        self.assertIsNone(ch.group)
        self.assertIsNone(ch.channel)
        self.assertIsNone(ch.device_type)
        self.assertIsNone(ch.manufacturer)
        self.assertIsNone(ch.notes)
        self.assertIsNone(ch.zone)
        self.assertIsNone(ch.inclusion_group)
        self.assertIsNone(ch.is_backup)

    def test_display_frequency_formats_three_decimals(self):
        ch = Channel(name="X", frequency_mhz=606.25)
        self.assertEqual(ch.display_frequency(), "606.250")


class TestCoordinationList(unittest.TestCase):
    def test_starts_empty(self):
        cl = CoordinationList()
        self.assertEqual(len(cl), 0)

    def test_add_increases_length(self):
        cl = CoordinationList()
        cl.add(Channel(name="A", frequency_mhz=470.0))
        cl.add(Channel(name="B", frequency_mhz=471.0))
        self.assertEqual(len(cl), 2)

    def test_iterates_in_insertion_order(self):
        cl = CoordinationList()
        cl.add(Channel(name="A", frequency_mhz=470.0))
        cl.add(Channel(name="B", frequency_mhz=471.0))
        names = [ch.name for ch in cl]
        self.assertEqual(names, ["A", "B"])

    def test_constructed_with_channels_list(self):
        chans = [Channel(name="A", frequency_mhz=470.0)]
        cl = CoordinationList(channels=chans)
        self.assertEqual(len(cl), 1)


if __name__ == "__main__":
    unittest.main()
