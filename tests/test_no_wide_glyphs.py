import glob
import os
import unicodedata
import unittest

# The compositor assumes every glyph occupies exactly one terminal cell.
# A double-width (East Asian Wide/Fullwidth) glyph would occupy two, so its
# right half never gets cleared -> "stuck" artifacts. This guards against that.


class TestNoWideGlyphs(unittest.TestCase):
    def test_irisplayer_source_is_single_width_only(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bad = []
        for path in glob.glob(os.path.join(root, "irisplayer", "*.py")):
            with open(path, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    for ch in line:
                        if unicodedata.east_asian_width(ch) in ("W", "F"):
                            bad.append(f"{os.path.basename(path)}:{lineno} "
                                       f"U+{ord(ch):04X} {ch!r}")
        self.assertEqual(bad, [], "double-width glyphs found: " + "; ".join(bad))


if __name__ == "__main__":
    unittest.main()
