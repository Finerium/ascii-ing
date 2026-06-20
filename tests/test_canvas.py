import unittest

from irisplayer.canvas import Canvas, Renderer
from irisplayer.color import RGB


class TestCanvas(unittest.TestCase):
    def test_put_in_bounds(self):
        c = Canvas(5, 3)
        c.put(0, 0, "A", RGB(1, 2, 3))
        self.assertEqual(c.cells[0][0], ("A", RGB(1, 2, 3), None, False))

    def test_put_out_of_bounds_ignored(self):
        c = Canvas(5, 3)
        c.put(-1, 0, "X")
        c.put(99, 99, "X")
        self.assertEqual(c.cells[0][0][0], " ")  # unchanged

    def test_rows_are_independent(self):
        c = Canvas(3, 2)
        c.put(0, 0, "A")
        self.assertEqual(c.cells[1][0][0], " ")  # not aliased to row 0

    def test_text_center(self):
        c = Canvas(10, 1)
        x = c.text_center(0, "abcd")  # (10-4)//2 = 3
        self.assertEqual(x, 3)
        self.assertEqual(c.cells[0][3][0], "a")

    def test_as_plain(self):
        c = Canvas(6, 2)
        c.text(1, 0, "hi")
        self.assertEqual(c.as_plain().split("\n")[0], " hi")


class TestRenderer(unittest.TestCase):
    def test_unchanged_frame_emits_no_moves(self):
        c = Canvas(4, 2)
        r = Renderer()
        first = r.render(c)
        self.assertIn("\x1b[", first)        # full first draw has escapes
        second = r.render(c)                  # identical frame
        self.assertNotIn("H", second)         # no cursor-position codes

    def test_single_change_is_minimal(self):
        c = Canvas(4, 2)
        r = Renderer()
        r.render(c)
        c.put(2, 1, "Z", RGB(9, 9, 9))
        out = r.render(c)
        self.assertIn("Z", out)
        self.assertIn("\x1b[2;3H", out)       # moved to row 2, col 3

    def test_reset_forces_full_redraw(self):
        c = Canvas(4, 2)
        r = Renderer()
        r.render(c)
        r.reset()
        out = r.render(c)
        self.assertIn("H", out)               # treats every cell as changed


if __name__ == "__main__":
    unittest.main()
