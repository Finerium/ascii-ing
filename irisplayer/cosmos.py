"""Cosmic decorations for the lyric phase, plus the big-bang outro.

Same hard rule as everything else: foreground glyphs only, transparent
background, no blocks/fills. Every effect is a pure function of time, so
the center band stays free for the lyric and snapshots stay reproducible.
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from . import easing
from .canvas import Canvas
from .color import (
    RGB, gradient, STARLIGHT, TEXT_WHITE, STAR_BEATS,
    HUD_CYAN, MOON_SILVER, MOON_CLOUD, COMET_COL, NEBULA_A, NEBULA_B, FLASH,
)

TAU = math.tau

FACTS = [
    "the observable universe spans 93 billion light-years",
    "farthest known galaxy JADES-GS-z14-0 — 13.5 billion ly",
    "Proxima Centauri, our nearest star — 4.24 light-years",
    "Voyager 1 — over 24 billion km from earth and counting",
    "Andromeda approaches the Milky Way at 110 km/s",
    "light from the sun reaches earth in about 8 minutes",
    "a neutron-star teaspoon would weigh ~6 billion tons",
    "the Milky Way holds 100 to 400 billion stars",
    "there are more stars than grains of sand on earth",
    "Betelgeuse is 700 light-years away and may already be gone",
]


class Moon:
    """A glowing crescent: a ring of glyphs bright on the lit (left) limb and
    faint on the dark limb, wrapped in a soft, pulsing cloud halo."""

    def __init__(self, cx: int, cy: int, rx: int = 5, ry: int = 3, seed: int = 1):
        self.cx, self.cy = cx, cy
        self.pts: List[Tuple[int, int, float]] = []
        n = max(18, int((rx + ry) * 3))
        for k in range(n):
            a = TAU * k / n
            x = int(round(cx + rx * math.cos(a)))
            y = int(round(cy + ry * math.sin(a)))
            self.pts.append((x, y, a))
        rng = random.Random(seed)
        self.clouds = []
        for _ in range(16):
            a = rng.uniform(0, TAU)
            rr = rng.uniform(1.25, 2.1)
            x = int(round(cx + rx * rr * math.cos(a)))
            y = int(round(cy + ry * rr * math.sin(a)))
            self.clouds.append((x, y, rng.uniform(0, TAU), rng.choice("·˚⋆∴‿⌒")))

    def render(self, canvas: Canvas, t: float, intensity: float = 1.0) -> None:
        glow = 0.65 + 0.35 * math.sin(t * 0.8)
        for (x, y, a) in self.pts:
            limb = (1.0 - math.cos(a)) / 2.0      # 1 on left limb, 0 on right
            b = (0.12 + 0.88 * limb) * glow * intensity
            if b <= 0.08:
                continue
            canvas.put(x, y, "•" if b > 0.5 else "·", MOON_SILVER.scale(b))
        for (x, y, ph, ch) in self.clouds:
            b = (0.20 + 0.30 * (0.5 + 0.5 * math.sin(t * 0.9 + ph))) * glow * intensity
            if b <= 0.08:
                continue
            canvas.put(x, y, ch, MOON_CLOUD.scale(b))


class Planet:
    """A small body that drifts slowly across, optionally ringed."""

    def __init__(self, color: RGB, y: int, speed: float, phase: float,
                 glyph: str = "◉", ring: bool = False):
        self.color, self.y, self.speed, self.phase = color, y, speed, phase
        self.glyph, self.ring = glyph, ring

    def render(self, canvas: Canvas, t: float, width: int) -> None:
        span = width + 10
        x = int((self.phase * span + t * self.speed) % span) - 5
        col = self.color.scale(0.7 + 0.3 * math.sin(t * 0.5 + self.phase * 6))
        if self.ring:
            canvas.put(x - 1, self.y, "╴", col.scale(0.55))
            canvas.put(x + 1, self.y, "╶", col.scale(0.55))
        canvas.put(x, self.y, self.glyph, col)


class ShootingStars:
    """Frequent streaks across the whole phase, plus an optional burst."""

    def __init__(self, width: int, height: int, duration: float,
                 seed: int = 3, rate: float = 3.8, burst_at: float = None):
        rng = random.Random(seed)
        self.events: List[Tuple[float, float, float, int]] = []
        t = rng.uniform(0.5, rate)
        while t < duration:
            self.events.append((t, rng.uniform(width * 0.1, width * 0.9),
                                rng.uniform(1.5, 2.5), rng.choice([1, -1])))
            t += rng.uniform(rate * 0.6, rate * 1.4)
        if burst_at is not None:
            for k in range(5):
                self.events.append((burst_at + k * 0.28 + rng.uniform(0, 0.15),
                                    rng.uniform(width * 0.2, width * 0.8),
                                    rng.uniform(1.5, 2.3), rng.choice([1, -1])))

    def render(self, canvas: Canvas, t: float, width: int, height: int) -> None:
        for (trig, x0, life, d) in self.events:
            if not (trig <= t <= trig + life):
                continue
            p = (t - trig) / life
            dist = p * height * 1.3
            hx = x0 + d * dist * 0.6
            hy = -2.0 + dist
            for k in range(7):
                xx = int(hx - d * k * 0.6)
                yy = int(hy - k)
                b = (1.0 - k / 7.0) * (1.0 - p)
                if b <= 0.08:
                    continue
                ch = "✦" if k == 0 else ("·" if k < 4 else ".")
                canvas.put(xx, yy, ch, STARLIGHT.scale(b))


class Comet:
    """A bright head with a long fading tail, crossing a few times."""

    def __init__(self, width: int, height: int,
                 times: Sequence[Tuple[float, int, int]], life: float = 4.6):
        self.width, self.height, self.times, self.life = width, height, times, life

    def render(self, canvas: Canvas, t: float) -> None:
        for (trig, y0, d) in self.times:
            if not (trig <= t <= trig + self.life):
                continue
            p = (t - trig) / self.life
            hx = -12 + p * (self.width + 24) if d > 0 else self.width + 12 - p * (self.width + 24)
            hy = y0 + math.sin(p * math.pi) * 2.0
            for k in range(16):
                xx = int(hx - d * k)
                yy = int(hy + k * 0.18)
                b = 1.0 - k / 16.0
                ch = "✦" if k == 0 else ("•" if k < 3 else ("·" if k < 9 else "."))
                canvas.put(xx, yy, ch, COMET_COL.scale(b))


class Constellation:
    """A few bright stars joined by faint lines that draw in, hold, fade."""

    def __init__(self, points: Sequence[Tuple[int, int]],
                 edges: Sequence[Tuple[int, int]], appear: float, hold: float = 7.0):
        self.points, self.edges, self.appear, self.hold = points, edges, appear, hold

    def render(self, canvas: Canvas, t: float) -> None:
        lt = t - self.appear
        if lt < 0 or lt > self.hold:
            return
        if lt < 1.5:
            a = easing.out_quad(lt / 1.5)
        elif lt > self.hold - 1.5:
            a = easing.out_quad((self.hold - lt) / 1.5)
        else:
            a = 1.0
        for (i, j) in self.edges:
            self._line(canvas, self.points[i], self.points[j], a * 0.35)
        for (x, y) in self.points:
            canvas.put(x, y, "✦", STARLIGHT.scale(a))

    @staticmethod
    def _line(canvas: Canvas, p, q, b: float) -> None:
        if b <= 0.05:
            return
        (x0, y0), (x1, y1) = p, q
        steps = max(abs(x1 - x0), abs(y1 - y0))
        if steps == 0:
            return
        for s in range(1, steps):
            x = int(round(x0 + (x1 - x0) * s / steps))
            y = int(round(y0 + (y1 - y0) * s / steps))
            canvas.put(x, y, "·", STARLIGHT.scale(b))


class Nebula:
    """A faint, slowly drifting cloud of colored motes."""

    def __init__(self, cx: int, cy: int, w: int, h: int, seed: int = 4):
        self.cx, self.cy = cx, cy
        rng = random.Random(seed)
        self.blobs = []
        for _ in range(max(10, int(w * h * 0.22))):
            self.blobs.append((rng.gauss(0, w * 0.35), rng.gauss(0, h * 0.35),
                               rng.uniform(0, TAU), rng.random()))

    def render(self, canvas: Canvas, t: float, intensity: float = 1.0) -> None:
        drift = math.sin(t * 0.1) * 2.0
        for (dx, dy, ph, hue) in self.blobs:
            b = (0.10 + 0.16 * (0.5 + 0.5 * math.sin(t * 0.3 + ph))) * intensity
            if b <= 0.06:
                continue
            x = int(round(self.cx + dx + drift))
            y = int(round(self.cy + dy))
            canvas.put(x, y, "·" if b < 0.16 else "∴", gradient([NEBULA_A, NEBULA_B], hue).scale(b))


class Satellite:
    """A tiny blinking dot crossing in a straight line, slowly."""

    def __init__(self, width: int, height: int,
                 times: Sequence[Tuple[float, int, int]], life: float = 6.0):
        self.width, self.height, self.times, self.life = width, height, times, life

    def render(self, canvas: Canvas, t: float) -> None:
        for (trig, y0, d) in self.times:
            if not (trig <= t <= trig + self.life):
                continue
            p = (t - trig) / self.life
            x = int(-2 + p * (self.width + 4) if d > 0 else self.width + 2 - p * (self.width + 4))
            on = int(t * 3) % 2 == 0
            canvas.put(x, int(y0), "•" if on else "·", STARLIGHT.scale(0.6 if on else 0.28))


class SpaceFacts:
    """One faint HUD fact at a time along the top edge, fading in and out."""

    def __init__(self, facts: Sequence[str], interval: float = 5.5, row: int = 1):
        self.facts, self.interval, self.row = facts, interval, row

    def render(self, canvas: Canvas, t: float, width: int) -> None:
        idx = int(t / self.interval) % len(self.facts)
        lt = t - int(t / self.interval) * self.interval
        if lt < 1.0:
            a = easing.out_quad(lt)
        elif lt > self.interval - 1.0:
            a = easing.out_quad(self.interval - lt)
        else:
            a = 1.0
        a *= 0.5
        if a <= 0.05:
            return
        text = self.facts[idx]
        x = max(0, (width - len(text)) // 2)
        canvas.text(x, self.row, text, HUD_CYAN.scale(a))


class BigBang:
    """The outro: the last line implodes to a point, flashes, explodes in a
    radial burst with shockwave rings, and the debris settles into a new
    starfield before fading out."""

    def __init__(self, width: int, height: int, last_line: str, seed: int = 9):
        self.w, self.h = width, height
        self.last = last_line
        self.cx, self.cy = width // 2, height // 2
        rng = random.Random(seed)
        self.particles = [(rng.uniform(0, TAU),
                           rng.uniform(0.4, 1.0) * rng.choice([1, 1, 1, 1.6]),
                           rng.random()) for _ in range(150)]
        self.maxr = max(width, height) * 0.85
        # phase clocks (lengthened so the bang reads, not flashes)
        self.t_imp, self.t_sing, self.t_bang, self.t_settle = 1.8, 2.3, 7.5, 11.5
        self.duration = 14.5

    def _pos(self, ang: float, d: float):
        # *0.5 on y compensates for tall cells -> roughly circular on screen
        return int(round(self.cx + math.cos(ang) * d)), int(round(self.cy + math.sin(ang) * d * 0.5))

    def _ring(self, canvas: Canvas, r: float, b: float) -> None:
        if r < 1 or b <= 0.05:
            return
        n = max(8, int(TAU * r))
        for k in range(n):
            a = TAU * k / n
            x, y = self._pos(a, r)
            canvas.put(x, y, "·", FLASH.scale(b * 0.7))

    def render(self, canvas: Canvas, t: float) -> None:
        if t < self.t_imp:                                   # implosion
            p = easing.in_quad(t / self.t_imp)
            x0 = (self.w - len(self.last)) // 2
            for i, ch in enumerate(self.last):
                if ch == " ":
                    continue
                x = int(round((x0 + i) + (self.cx - (x0 + i)) * p))
                canvas.put(x, self.cy, ch, TEXT_WHITE.scale(1.0 - 0.3 * p))
            return
        if t < self.t_sing:                                  # singularity pulse
            b = 0.6 + 0.4 * math.sin((t - self.t_imp) / (self.t_sing - self.t_imp) * math.pi * 3)
            canvas.put(self.cx, self.cy, "✦", FLASH.scale(1.0))
            canvas.put(self.cx - 1, self.cy, "·", FLASH.scale(b * 0.6))
            canvas.put(self.cx + 1, self.cy, "·", FLASH.scale(b * 0.6))
            return
        if t < self.t_bang:                                  # the bang
            p = (t - self.t_sing) / (self.t_bang - self.t_sing)
            ep = easing.out_quad(p)
            self._ring(canvas, ep * self.maxr, 1.0 - ep)   # single shockwave (one boom)
            for (ang, spd, slot) in self.particles:
                d = ep * self.maxr * spd
                x, y = self._pos(ang, d)
                col = FLASH.lerp(gradient(STAR_BEATS[0], slot), easing.out_quad(p)).scale(1.0 - 0.4 * p)
                ch = "✦" if d < 2 else ("•" if d < self.maxr * 0.5 else "·")
                canvas.put(x, y, ch, col)
            return
        if t < self.t_settle:                                # debris twinkles
            for (ang, spd, slot) in self.particles:
                x, y = self._pos(ang, self.maxr * spd)
                tw = 0.5 + 0.5 * math.sin(t * 2.0 + slot * TAU)
                canvas.put(x, y, "•" if tw > 0.6 else "·", gradient(STAR_BEATS[0], slot).scale(0.6 * tw))
            return
        p = (t - self.t_settle) / (self.duration - self.t_settle)   # fade out
        for (ang, spd, slot) in self.particles:
            x, y = self._pos(ang, self.maxr * spd)
            canvas.put(x, y, "·", gradient(STAR_BEATS[0], slot).scale(0.5 * (1.0 - p)))
