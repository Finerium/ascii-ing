#!/usr/bin/env python3
"""Static SAMPLE of the colored starfield (full jewel-field).

This is NOT the real show -- just a swatch so you can approve the star
colors before the rebuild. White lyric placeholder sits in each block so
you can picture the final look. Run it in a truecolor terminal:

    python3 sample_stars.py
"""
import random
import shutil

from irisplayer.color import RGB, fg, RESET

# Mostly small points, a few bright stars (weighted by repetition).
GLYPHS = "······•••✦✧⋆∗"
DENSITY = 0.5  # fraction of columns that get a star -- dense, like you like

# Per-beat palettes. The 'vibe' lives in these colors; the text stays white.
BEATS = [
    ("1 · devotion         cool jewel — ice-blue / cyan / violet / silver",
     [RGB(150, 200, 255), RGB(120, 220, 230), RGB(170, 150, 240),
      RGB(206, 214, 235), RGB(240, 245, 255), RGB(110, 170, 235)]),
    ("2 · wanting to stay   warming — silver + gold creeping in",
     [RGB(230, 235, 250), RGB(206, 214, 235), RGB(244, 196, 110),
      RGB(224, 158, 78), RGB(150, 200, 255)]),
    ("3 · taste the moment  candlelight — gold / amber / ember / peach",
     [RGB(244, 196, 110), RGB(224, 158, 78), RGB(240, 138, 76),
      RGB(255, 190, 150), RGB(248, 240, 226)]),
    ("4 · breath            rose / pink + aurora teal",
     [RGB(226, 138, 150), RGB(240, 160, 190), RGB(220, 130, 200),
      RGB(248, 240, 226), RGB(94, 214, 169), RGB(74, 182, 196)]),
    ("5 · it's over         muted & melancholic — slate / dim silver",
     [RGB(96, 110, 140), RGB(120, 130, 150), RGB(150, 160, 180),
      RGB(90, 100, 120), RGB(170, 178, 195)]),
    ("6 · longing (close)   warm gold surge — bright, tender",
     [RGB(244, 206, 120), RGB(224, 158, 78), RGB(240, 138, 76),
      RGB(255, 224, 170), RGB(248, 240, 226)]),
]


def starline(width, palette, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(max(0, width)):
        if rng.random() > DENSITY:
            out.append(" ")
            continue
        c = rng.choice(palette).scale(rng.uniform(0.6, 1.0))  # baseline twinkle
        out.append(fg(c) + rng.choice(GLYPHS) + RESET)
    return "".join(out)


def field_with_text(width, palette, text, seed):
    pad = max(0, (width - len(text)) // 2)
    left = starline(pad, palette, seed)
    right = starline(width - pad - len(text), palette, seed + 1)
    return left + fg(RGB(245, 245, 250)) + text + RESET + right


def wisp_line(width, seed):
    rng = random.Random(seed)
    aurora = [RGB(94, 214, 169), RGB(74, 182, 196), RGB(120, 200, 180),
              RGB(150, 124, 214)]
    out = []
    for _ in range(width):
        if rng.random() < 0.14:
            c = rng.choice(aurora).scale(rng.uniform(0.5, 0.9))
            out.append(fg(c) + rng.choice("∿~") + RESET)
        else:
            out.append(" ")
    return "".join(out)


def main():
    width = min(shutil.get_terminal_size((80, 24)).columns - 4, 78)
    label = RGB(125, 130, 148)
    print()
    print(fg(RGB(222, 226, 238)) + "  FULL JEWEL-FIELD — sample warna bintang (per beat)" + RESET)
    print(fg(label) + "  latar transparan · tiap titik = glyph berwarna · nol blok/kotak" + RESET)
    print()
    for i, (name, palette) in enumerate(BEATS):
        print(fg(label) + "  " + name + RESET)
        for r in range(3):
            print("  " + starline(width, palette, i * 100 + r))
        print("  " + field_with_text(width, palette, " ‹ teks lirik tetap PUTIH › ",
                                      i * 100 + 40))
        for r in range(3):
            print("  " + starline(width, palette, i * 100 + 70 + r))
        print()
    print(fg(label) + "  bonus · wisp aurora (glyph mengalir, bukan blok)" + RESET)
    for r in range(2):
        print("  " + wisp_line(width, 900 + r))
    print()


if __name__ == "__main__":
    main()
