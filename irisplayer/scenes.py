"""The three acts: Intro, Lyrics, Outro.

Design contract (post-redesign):
  * NO background fills -- the terminal's own background shows through.
  * Lyric text is WHITE, always.
  * Color + mood live in the dense, colored STARFIELD, whose palette shifts
    per beat. Plus sparse ASCII craft (aurora wisps, a thin divider).

Each Scene exposes ``duration`` and ``render(canvas, t_local)`` and is
stateless in time, so dropped frames never desync the show.
"""
from __future__ import annotations

import math
from typing import List

from . import easing, textfx, particles, cosmos
from .color import (RGB, TEXT_WHITE, STAR_BEATS, STAR_INTRO, STAR_OUTRO, gradient,
                    AURORA_TEAL, PLANET_GOLD, PLANET_RUST, PLANET_ICE)
from .canvas import Canvas
from .lrc import Cue


def _lerp(a: float, b: float, f: float) -> float:
    return a + (b - a) * f


def dim_canvas(canvas: Canvas, factor: float) -> None:
    """Fade every glyph toward black (factor 1 = unchanged). Backgrounds stay
    transparent -- fading just dims the foreground until it vanishes."""
    if factor >= 1.0:
        return
    factor = max(0.0, factor)
    for y in range(canvas.height):
        row = canvas.cells[y]
        for x in range(canvas.width):
            ch, f, b, bold = row[x]
            row[x] = (ch, f.scale(factor) if f is not None else None, b, bold)


class Scene:
    duration = 0.0

    def render(self, canvas: Canvas, t: float) -> None:  # pragma: no cover
        raise NotImplementedError


# --- Act I: Intro ------------------------------------------------------

class Intro(Scene):
    def __init__(self, width: int, height: int, title: str, artist: str,
                 dedication: str, density: float = 0.12, seed: int = 7,
                 dedication_glow: float = 0.38):
        self.width = width
        self.height = height
        self.title_line = f"{title} by {artist}"
        self.dedication = dedication
        self.dedication_glow = dedication_glow   # lower = more hidden
        # bottom-right "liner notes": the dedication is sandwiched among
        # plausible metadata, all at the same faint glow (intro only).
        self.corner_lines = [
            'from "dizzy up the girl" · 1998',
            dedication,
            'synced lyrics · 4:23',
        ]
        self.stars = particles.StarField(width, height, density=density, seed=seed)
        self.aurora = particles.Aurora(width, height, seed=seed + 1)
        self.duration = 9.0

    def render(self, canvas: Canvas, t: float) -> None:
        self.stars.render(canvas, t, STAR_INTRO, intensity=easing.out_quad(t / 2.5))
        cy = self.height // 2

        # title + dedication appear together
        appear = easing.out_quad((t - 1.8) / 2.2)
        if appear > 0.0:
            self.aurora.render(canvas, t, intensity=0.55 * appear)
            canvas.text_center(cy - 1, self.title_line, TEXT_WHITE.scale(appear), bold=True)
            divider = "·   ·   ✧   ·   ·"
            canvas.text_center(cy + 1, divider,
                               gradient([AURORA_TEAL, TEXT_WHITE], 0.5).scale(0.45 * appear))
            self._render_corner(canvas, appear)

        tail = self.duration - 1.5
        if t > tail:
            dim_canvas(canvas, 1.0 - easing.in_quad((t - tail) / 1.5))

    def _render_corner(self, canvas: Canvas, appear: float) -> None:
        """Faint bottom-right liner-notes; the dedication hides inside it."""
        col = TEXT_WHITE.scale(appear * self.dedication_glow)
        bottom = self.height - 2
        start = bottom - (len(self.corner_lines) - 1)
        for i, line in enumerate(self.corner_lines):
            x = max(0, self.width - 2 - len(line))
            canvas.text(x, start + i, line, col)


# --- Act II: Lyrics ----------------------------------------------------

# Per-beat scalar moods: (ember, aurora, breath) -- palettes come from STAR_BEATS.
_SCALARS = [
    (0.00, 0.10, 0.0),   # devotion
    (0.15, 0.10, 0.0),   # wanting to stay
    (0.90, 0.06, 0.0),   # taste
    (0.50, 0.35, 1.0),   # breath
    (0.20, 0.12, 0.2),   # it's over
    (0.60, 0.10, 0.3),   # longing / close
]


def _fit(seq: list, n: int) -> list:
    if n <= 0:
        return seq
    if n <= len(seq):
        return seq[:n]
    return seq + [seq[-1]] * (n - len(seq))


class Lyrics(Scene):
    def __init__(self, width: int, height: int, cues: List[Cue],
                 density: float = 0.12, seed: int = 7):
        self.width = width
        self.height = height
        self.lyric_cues = [c for c in cues if not c.is_blank]
        self.duration = max((c.end for c in cues), default=0.0)
        self.stars = particles.StarField(width, height, density=density, seed=seed)
        self.embers = particles.Embers(width, height, seed=seed + 2)
        self.aurora = particles.Aurora(width, height, seed=seed + 3)
        self.sched = {
            i: textfx.reveal_schedule(c.text, cps=20.0, seed=1000 + i)
            for i, c in enumerate(self.lyric_cues)
        }
        n = len(self.lyric_cues)
        self.palettes = _fit(list(STAR_BEATS), n)
        self.scalars = _fit(list(_SCALARS), n)

        # parallax: a sparser, brighter near layer that drifts faster
        self.star_near = particles.StarField(width, height, density=density * 0.35, seed=seed + 9)

        # cosmic decorations -- all kept out of the center band (the lyric row)
        burst = self.lyric_cues[4].start if n >= 5 else None
        self.moon = cosmos.Moon(width - 12, 4)
        self.nebula = cosmos.Nebula(11, height - 5, 20, 9)
        self.planets = [
            cosmos.Planet(PLANET_GOLD, y=6, speed=2.4, phase=0.10, glyph="◉", ring=True),
            cosmos.Planet(PLANET_RUST, y=height - 6, speed=1.6, phase=0.55, glyph="●"),
            cosmos.Planet(PLANET_ICE, y=3, speed=3.2, phase=0.82, glyph="◍"),
        ]
        self.comet = cosmos.Comet(width, height, [(5.0, 3, 1), (17.5, 6, -1)])
        self.satellite = cosmos.Satellite(width, height, [(8.0, 2, 1), (21.0, height - 4, -1)])
        self.shooting = cosmos.ShootingStars(width, height, self.duration, burst_at=burst)
        cw = width // 2
        self.constellations = [
            cosmos.Constellation([(cw - 20, 4), (cw - 16, 6), (cw - 11, 5), (cw - 14, 8)],
                                 [(0, 1), (1, 2), (1, 3)], appear=4.0, hold=8.0),
            cosmos.Constellation([(width - 22, height - 7), (width - 17, height - 8),
                                  (width - 13, height - 6)],
                                 [(0, 1), (1, 2)], appear=14.0, hold=7.0),
        ]

    def _beat(self, t: float):
        cues = self.lyric_cues
        if not cues:
            return 0, 0, 0.0
        if t <= cues[0].start:
            return 0, 0, 0.0
        for i in range(len(cues) - 1):
            if cues[i].start <= t < cues[i + 1].start:
                span = cues[i + 1].start - cues[i].start
                f = easing.in_out_cubic((t - cues[i].start) / span) if span > 0 else 0.0
                return i, i + 1, f
        return len(cues) - 1, len(cues) - 1, 0.0

    def render(self, canvas: Canvas, t: float) -> None:
        i, j, f = self._beat(t)
        ember = _lerp(self.scalars[i][0], self.scalars[j][0], f)
        aurora = _lerp(self.scalars[i][1], self.scalars[j][1], f)
        breath_amt = _lerp(self.scalars[i][2], self.scalars[j][2], f)
        breath = 1.0 - breath_amt * 0.10 * (0.5 + 0.5 * math.sin(t * 1.6))

        pa, pb = self.palettes[i], self.palettes[j]
        # far -> near, then the lyric on top; center band stays clear
        self.nebula.render(canvas, t, intensity=0.85)
        self.stars.render(canvas, t, pa, pb, f, intensity=breath, drift=math.sin(t * 0.03) * 1.5)
        for con in self.constellations:
            con.render(canvas, t)
        self.star_near.render(canvas, t, pa, pb, f, intensity=breath, drift=t * 0.6)
        for pl in self.planets:
            pl.render(canvas, t, self.width)
        self.moon.render(canvas, t)
        self.comet.render(canvas, t)
        self.satellite.render(canvas, t)
        self.shooting.render(canvas, t, self.width, self.height)
        if aurora > 0.02:
            self.aurora.render(canvas, t, intensity=aurora * breath)
        if ember > 0.02:
            self.embers.render(canvas, t, intensity=ember * breath)

        self._render_text(canvas, t)

    def _render_text(self, canvas: Canvas, t: float) -> None:
        cues = self.lyric_cues
        if not cues:
            return
        cy = self.height // 2

        latest = -1
        for i, c in enumerate(cues):
            if c.start <= t:
                latest = i
            else:
                break
        if latest < 0:
            return

        c = cues[latest]
        sched = self.sched[latest]
        te = t - c.start
        n = textfx.revealed_count(sched, te)
        total = textfx.total_time(sched)
        text = c.text

        x0 = (self.width - len(text)) // 2
        shown = text[:n]
        canvas.text(x0, cy, shown, TEXT_WHITE, bold=True)
        if te < total + 0.4 and textfx.cursor_visible(te):
            canvas.put(x0 + len(shown), cy, "▏", TEXT_WHITE)

        if latest >= 1:
            f = te / 0.8
            if f < 1.0:
                pc = cues[latest - 1]
                e = easing.out_quad(f)
                dim = 1.0 - e
                if dim > 0.05:
                    px = (self.width - len(pc.text)) // 2
                    yy = cy - 1 - int(round(e * 2))
                    canvas.text(px, yy, pc.text, TEXT_WHITE.scale(0.55 * dim))


# --- Act III: Outro ----------------------------------------------------

class Outro(Scene):
    def __init__(self, width: int, height: int, last_line: str,
                 dedication: str, density: float = 0.12, seed: int = 7):
        # the last line implodes -> singularity -> bang -> new starfield -> fade
        self.bang = cosmos.BigBang(width, height, last_line, seed=seed + 2)
        self.duration = self.bang.duration

    def render(self, canvas: Canvas, t: float) -> None:
        self.bang.render(canvas, t)
