import unittest

from irisplayer import textfx


class TestReveal(unittest.TestCase):
    def test_schedule_length_and_monotonic(self):
        sch = textfx.reveal_schedule("hello world", cps=20, seed=1)
        self.assertEqual(len(sch), len("hello world"))
        self.assertTrue(all(sch[i] < sch[i + 1] for i in range(len(sch) - 1)))

    def test_revealed_count_bounds(self):
        sch = textfx.reveal_schedule("abc", cps=10, seed=0, jitter=0.0)
        self.assertEqual(textfx.revealed_count(sch, -1.0), 0)
        self.assertEqual(textfx.revealed_count(sch, 0.0), 0)
        self.assertEqual(textfx.revealed_count(sch, textfx.total_time(sch) + 1), 3)

    def test_punctuation_adds_pause(self):
        plain = textfx.reveal_schedule("ab", cps=10, seed=0, jitter=0.0)
        with_comma = textfx.reveal_schedule("a,b", cps=10, seed=0, jitter=0.0)
        self.assertGreater(textfx.total_time(with_comma), textfx.total_time(plain))

    def test_cursor_blink_toggles(self):
        self.assertTrue(textfx.cursor_visible(0.0, 2.0))
        seen = {textfx.cursor_visible(t / 10.0, 2.0) for t in range(0, 12)}
        self.assertEqual(seen, {True, False})


if __name__ == "__main__":
    unittest.main()
