import unittest

from wsm_wwb_bridge.wsm_html import looks_like_wsm_html_report, read_wsm_html_report

SAMPLE_REPORT = """<!DOCTYPE html>
<html>
<body>
<div id="headline">WSM Coordination Report</div>
<div class="h3Container">
<div class="innerheadline">
<div class="deviceColorImageContainer"><image src="resources/img/device_microphone.png"/></div>
<div class="deviceTitle">FM Mics:</div>
</div>
</div>
<div id="panel1"><table id="devices" rules="all">
<tr>
<th class="numberCol">#</th>
<th>Name</th>
<th>Stationary device</th>
<th>Frequency range</th>
<th>Frequency</th>
<th>Portable device</th>
<th>Squelch/Max.noise</th>
</tr>
<tr class="greyRow">
<td align="center">1</td>
<td>EM3732</td>
<td>EM 3731/3732</td>
<td>470.000 - 560.000 MHz</td>
<td>470.500 MHz</td>
<td>SK5212/SKM5200</td>
<td>0 &microV</td>
</tr>
</table></div>
<div class="h3Container">
<div class="innerheadline">
<div class="deviceTitle">IEM Systems:</div>
</div>
</div>
<div id="panel2"><table id="devices" rules="all">
<tr>
<th class="numberCol">#</th>
<th>Name</th>
<th>Stationary device</th>
<th>Frequency range</th>
<th>Frequency</th>
<th>Portable device</th>
<th>Squelch/Max.noise</th>
</tr>
<tr class="greyRow">
<td align="center">1</td>
<td>SR2000 I</td>
<td>SR 2000/2050-IEM</td>
<td>516.000 - 558.000 MHz</td>
<td>556.600 MHz</td>
<td>EK 2000-IEM</td>
<td>-1 dB</td>
</tr>
</table></div>
</body>
</html>
"""


class TestLooksLikeWsmHtmlReport(unittest.TestCase):
    def test_detects_report_marker(self):
        self.assertTrue(looks_like_wsm_html_report(SAMPLE_REPORT))

    def test_rejects_unrelated_html(self):
        self.assertFalse(looks_like_wsm_html_report("<html><body>hello</body></html>"))


class TestReadWsmHtmlReport(unittest.TestCase):
    def setUp(self):
        self.cl = read_wsm_html_report(SAMPLE_REPORT)

    def test_header_row_not_treated_as_data(self):
        # Only the two real <td> rows should appear, not the <th> header row.
        self.assertEqual(len(self.cl), 2)

    def test_category_carried_as_zone(self):
        self.assertEqual(self.cl.channels[0].zone, "FM Mics")
        self.assertEqual(self.cl.channels[1].zone, "IEM Systems")

    def test_frequency_column_used_not_range(self):
        ch = self.cl.channels[0]
        self.assertAlmostEqual(ch.frequency_mhz, 470.5)

    def test_fields_mapped(self):
        ch = self.cl.channels[0]
        self.assertEqual(ch.name, "EM3732")
        self.assertEqual(ch.device_type, "EM 3731/3732")
        self.assertEqual(ch.manufacturer, "Sennheiser")
        self.assertIn("SK5212/SKM5200", ch.notes)

    def test_legacy_entity_without_semicolon_resolves_correctly(self):
        # "&microV" (no trailing semicolon) is technically malformed, but
        # html.parser resolves "&micro" via HTML5's legacy no-semicolon
        # entity list, correctly producing "µV" (matching what a real
        # browser renders) rather than crashing or leaving raw "&microV".
        self.assertIn("µV", self.cl.channels[0].notes)


if __name__ == "__main__":
    unittest.main()
