import unittest

from irisplayer import easing

FUNCS = [
    easing.linear,
    easing.in_quad,
    easing.out_quad,
    easing.in_out_cubic,
    easing.out_expo,
    easing.smoothstep,
]


class TestEasing(unittest.TestCase):
    def test_endpoints(self):
        for f in FUNCS:
            self.assertAlmostEqual(f(0.0), 0.0, places=5, msg=f.__name__)
            self.assertAlmostEqual(f(1.0), 1.0, places=5, msg=f.__name__)

    def test_clamps_at_edges(self):
        for f in FUNCS:
            self.assertAlmostEqual(f(-1.0), 0.0, places=5, msg=f.__name__)
            self.assertAlmostEqual(f(2.0), 1.0, places=5, msg=f.__name__)

    def test_monotonic_nondecreasing(self):
        for f in FUNCS:
            prev = -1.0
            for i in range(0, 101):
                v = f(i / 100.0)
                self.assertGreaterEqual(v, prev - 1e-9, msg=f.__name__)
                prev = v

    def test_out_back_overshoots_then_settles(self):
        self.assertAlmostEqual(easing.out_back(0.0), 0.0, places=5)
        self.assertAlmostEqual(easing.out_back(1.0), 1.0, places=5)
        # somewhere in the tail it should exceed 1 (the overshoot)
        self.assertTrue(any(easing.out_back(i / 100.0) > 1.0 for i in range(60, 100)))

    def test_pulse_arch(self):
        self.assertAlmostEqual(easing.pulse(0.0), 0.0, places=5)
        self.assertAlmostEqual(easing.pulse(0.5), 1.0, places=5)
        self.assertAlmostEqual(easing.pulse(1.0), 0.0, places=5)


if __name__ == "__main__":
    unittest.main()
