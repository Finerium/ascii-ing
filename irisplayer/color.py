"""Truecolor helpers: RGB, blending, and ANSI escape generation.

Pure stdlib. All colors are 24-bit RGB. Terminals that advertise
$COLORTERM=truecolor render these directly; a 256-color fallback lives in
terminal.py.
"""
from __future__ import annotations

from typing import Optional, Sequence, NamedTuple


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    def lerp(self, other: "RGB", t: float) -> "RGB":
        """Linear blend toward `other`. t is clamped to [0, 1]."""
        if t <= 0.0:
            return self
        if t >= 1.0:
            return other
        return RGB(
            int(round(self.r + (other.r - self.r) * t)),
            int(round(self.g + (other.g - self.g) * t)),
            int(round(self.b + (other.b - self.b) * t)),
        )

    def scale(self, factor: float) -> "RGB":
        """Scale brightness toward black (factor 0) or up (clamped at 255)."""
        factor = max(0.0, factor)
        return RGB(
            min(255, int(round(self.r * factor))),
            min(255, int(round(self.g * factor))),
            min(255, int(round(self.b * factor))),
        )


def lerp(a: RGB, b: RGB, t: float) -> RGB:
    return a.lerp(b, t)


def desaturate(c: RGB, amount: float) -> RGB:
    """Blend a color toward its luminance grey. amount in [0, 1]."""
    amount = min(1.0, max(0.0, amount))
    lum = int(round(0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b))
    return c.lerp(RGB(lum, lum, lum), amount)


def gradient(stops: Sequence[RGB], t: float) -> RGB:
    """Sample a multi-stop gradient at t in [0, 1]."""
    if not stops:
        raise ValueError("gradient needs at least one stop")
    if len(stops) == 1 or t <= 0.0:
        return stops[0]
    if t >= 1.0:
        return stops[-1]
    span = t * (len(stops) - 1)
    i = int(span)
    return stops[i].lerp(stops[i + 1], span - i)


# --- ANSI ---------------------------------------------------------------

def fg(c: RGB) -> str:
    return f"\x1b[38;2;{c.r};{c.g};{c.b}m"


def bg(c: RGB) -> str:
    return f"\x1b[48;2;{c.r};{c.g};{c.b}m"


RESET = "\x1b[0m"
DEFAULT_FG = "\x1b[39m"
DEFAULT_BG = "\x1b[49m"


# --- Palette (the hybrid: celestial -> candlelight -> aurora -> dawn) ----

BLACK = RGB(0, 0, 0)
VOID = RGB(6, 7, 16)              # near-black night with a hint of blue
INDIGO = RGB(40, 44, 92)
INDIGO_DEEP = RGB(22, 24, 58)
SILVER = RGB(206, 214, 235)
STARLIGHT = RGB(232, 238, 252)
AMBER = RGB(224, 158, 78)
GOLD = RGB(244, 196, 110)
EMBER = RGB(240, 138, 76)
ROSE = RGB(226, 138, 150)
WARM_WHITE = RGB(248, 240, 226)
MUTED_BLUE = RGB(96, 110, 140)
AURORA_GREEN = RGB(94, 214, 169)
AURORA_TEAL = RGB(74, 182, 196)
AURORA_VIOLET = RGB(150, 124, 214)
DAWN_LOW = RGB(38, 30, 66)        # bottom of the dawn sky
DAWN_MID = RGB(196, 110, 124)     # rose band
DAWN_HIGH = RGB(244, 198, 138)    # gold band

# Lyric text -- white, always (no rainbow).
TEXT_WHITE = RGB(245, 246, 250)

# Approved per-beat star palettes (the "full jewel-field"). The mood lives
# here; the text stays white. Each beat is sampled as a gradient by a star's
# fixed slot, so palette cross-fades recolor the whole field coherently.
STAR_BEATS = [
    # 1 devotion -- cool jewel
    [RGB(150, 200, 255), RGB(120, 220, 230), RGB(170, 150, 240),
     RGB(206, 214, 235), RGB(240, 245, 255), RGB(110, 170, 235)],
    # 2 wanting to stay -- silver warming with gold
    [RGB(230, 235, 250), RGB(206, 214, 235), RGB(244, 196, 110),
     RGB(224, 158, 78), RGB(150, 200, 255)],
    # 3 taste -- candlelight gold/amber/ember
    [RGB(244, 196, 110), RGB(224, 158, 78), RGB(240, 138, 76),
     RGB(255, 190, 150), RGB(248, 240, 226)],
    # 4 breath -- rose/pink + aurora teal
    [RGB(226, 138, 150), RGB(240, 160, 190), RGB(220, 130, 200),
     RGB(248, 240, 226), RGB(94, 214, 169), RGB(74, 182, 196)],
    # 5 it's over -- muted, melancholic
    [RGB(96, 110, 140), RGB(120, 130, 150), RGB(150, 160, 180),
     RGB(90, 100, 120), RGB(170, 178, 195)],
    # 6 longing / close -- warm gold surge
    [RGB(244, 206, 120), RGB(224, 158, 78), RGB(240, 138, 76),
     RGB(255, 224, 170), RGB(248, 240, 226)],
]
STAR_INTRO = STAR_BEATS[0]   # cool jewel for the title card
STAR_OUTRO = [RGB(244, 206, 120), RGB(255, 224, 170), RGB(224, 158, 78),
              RGB(248, 240, 226), RGB(240, 138, 76)]   # warm gold "dawn"

# Cosmos decoration colors
HUD_CYAN = RGB(120, 200, 220)
MOON_SILVER = RGB(228, 234, 246)
MOON_CLOUD = RGB(150, 170, 205)
PLANET_RUST = RGB(204, 112, 80)
PLANET_ICE = RGB(140, 192, 232)
PLANET_GOLD = RGB(226, 190, 120)
COMET_COL = RGB(200, 230, 255)
NEBULA_A = RGB(150, 110, 200)
NEBULA_B = RGB(86, 160, 190)
FLASH = RGB(255, 250, 238)
