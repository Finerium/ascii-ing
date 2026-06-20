import unittest

from irisplayer import color
from irisplayer.color import RGB


class TestColor(unittest.TestCase):
    def test_lerp_endpoints(self):
        a, b = RGB(0, 0, 0), RGB(10, 20, 30)
        self.assertEqual(a.lerp(b, 0.0), a)
        self.assertEqual(a.lerp(b, 1.0), b)

    def test_lerp_midpoint(self):
        self.assertEqual(RGB(0, 0, 0).lerp(RGB(10, 10, 10), 0.5), RGB(5, 5, 5))

    def test_lerp_clamps(self):
        a, b = RGB(0, 0, 0), RGB(10, 10, 10)
        self.assertEqual(a.lerp(b, -1.0), a)
        self.assertEqual(a.lerp(b, 2.0), b)

    def test_scale_down_and_clamp(self):
        self.assertEqual(RGB(100, 100, 100).scale(0.5), RGB(50, 50, 50))
        self.assertEqual(RGB(200, 200, 200).scale(10.0), RGB(255, 255, 255))
        self.assertEqual(RGB(100, 100, 100).scale(-1.0), RGB(0, 0, 0))

    def test_desaturate_grey_unchanged(self):
        c = RGB(80, 80, 80)
        self.assertEqual(color.desaturate(c, 1.0), c)

    def test_desaturate_full_is_grey(self):
        d = color.desaturate(RGB(255, 0, 0), 1.0)
        self.assertEqual(d.r, d.g)
        self.assertEqual(d.g, d.b)

    def test_gradient_stops(self):
        stops = [RGB(0, 0, 0), RGB(10, 10, 10), RGB(20, 20, 20)]
        self.assertEqual(color.gradient(stops, 0.0), RGB(0, 0, 0))
        self.assertEqual(color.gradient(stops, 1.0), RGB(20, 20, 20))
        self.assertEqual(color.gradient(stops, 0.5), RGB(10, 10, 10))

    def test_ansi_format(self):
        self.assertEqual(color.fg(RGB(1, 2, 3)), "\x1b[38;2;1;2;3m")
        self.assertEqual(color.bg(RGB(1, 2, 3)), "\x1b[48;2;1;2;3m")


if __name__ == "__main__":
    unittest.main()
