import unittest

from irisplayer import lrc
from irisplayer.lrc import Entry

# Synthetic fixture -- NOT real lyrics. Times chosen to exercise blanks,
# holds, and window boundaries.
SAMPLE = """[00:05.00]alpha
[00:09.00]bravo
[00:13.00]
[00:14.00]charlie
[00:18.00]
"""


class TestLrcParse(unittest.TestCase):
    def test_parse_count_and_values(self):
        entries = lrc.parse(SAMPLE)
        self.assertEqual(len(entries), 5)
        self.assertEqual(entries[0], Entry(5.0, "alpha"))
        self.assertEqual(entries[1], Entry(9.0, "bravo"))
        self.assertEqual(entries[2].text, "")  # blank kept as marker

    def test_parse_sorts_by_time(self):
        entries = lrc.parse("[00:09.00]b\n[00:05.00]a\n")
        self.assertEqual([e.time for e in entries], [5.0, 9.0])

    def test_multiple_timestamps_per_line(self):
        entries = lrc.parse("[00:01.00][00:03.00]repeat")
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e.text == "repeat" for e in entries))

    def test_parse_timestamp_forms(self):
        self.assertAlmostEqual(lrc.parse_timestamp("01:02.50"), 62.5)
        self.assertAlmostEqual(lrc.parse_timestamp("21.03"), 21.03)


class TestLrcWindow(unittest.TestCase):
    def setUp(self):
        self.entries = lrc.parse(SAMPLE)

    def test_first_cue_relative_and_bounded(self):
        cues = lrc.window(self.entries, 5.0, 18.0)
        self.assertAlmostEqual(cues[0].start, 0.0)
        self.assertAlmostEqual(cues[0].end, 4.0)  # next entry 9 - start 5
        self.assertEqual(cues[0].text, "alpha")

    def test_blank_marker_preserved(self):
        cues = lrc.window(self.entries, 5.0, 18.0)
        blanks = [c for c in cues if c.is_blank]
        self.assertTrue(any(abs(c.start - 8.0) < 1e-6 for c in blanks))

    def test_final_line_holds_to_window_end(self):
        cues = lrc.window(self.entries, 5.0, 18.0)
        charlie = [c for c in cues if c.text == "charlie"][0]
        self.assertAlmostEqual(charlie.start, 9.0)   # 14 - 5
        self.assertAlmostEqual(charlie.end, 13.0)    # 18 (boundary) - 5

    def test_zero_length_boundary_dropped(self):
        cues = lrc.window(self.entries, 5.0, 18.0)
        self.assertTrue(all(c.duration > 0 for c in cues))


if __name__ == "__main__":
    unittest.main()
