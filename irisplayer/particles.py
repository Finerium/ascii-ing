"""Visual effects: a colored starfield, candlelight embers, aurora wisps,
falling stars, and a dissolve.

Hard rule for this piece: **foreground glyphs only**. Every effect draws
colored point/line glyphs with a transparent background -- never a filled
block, never a background color. That keeps the native terminal showing
through and makes 'colored boxes' impossible.

Every effect is a pure function of time, so a given timestamp always
produces the same frame (reproducible snapshots / self-test).
"""
from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from .color import (
    RGB, gradient, AMBER, GOLD, EMBER, STARLIGHT,
    AURORA_GREEN, AURORA_TEAL, AURORA_VIOLET,
)
from .canvas import Canvas

TAU = math.tau

Palette = Sequence[RGB]


class StarField:
    """A dense field of twinkling, *colored* stars.

    Each star owns a fixed ``slot`` in [0, 1); its color is that slot sampled
    from whatever palette the scene passes in. When the scene cross-fades
    between two beat palettes, every star recolors coherently.
    """

    def __init__(self, width: int, height: int, density: float = 0.12, seed: int = 7):
        self.width = max(1, width)
        self.height = max(1, height)
        rng = random.Random(seed)
        count = max(12, int(self.width * self.height * density))
        self.stars: List[Tuple[int, int, float, float, float, float]] = []
        for _ in range(count):
            x = rng.randint(0, self.width - 1)
            y = rng.randint(0, self.height - 1)
            base = rng.uniform(0.35, 1.0)
            phase = rng.uniform(0.0, TAU)
            speed = rng.uniform(0.5, 2.1)
            slot = rng.random()
            self.stars.append((x, y, base, phase, speed, slot))

    def render(self, canvas: Canvas, t: float, pa: Palette,
               pb: Palette = None, blend: float = 0.0, intensity: float = 1.0,
               drift: float = 0.0) -> None:
        if intensity <= 0.02:
            return
        off = int(drift)
        for (x, y, base, phase, speed, slot) in self.stars:
            tw = 0.55 + 0.45 * math.sin(t * speed + phase)
            b = base * tw * intensity
            if b <= 0.10:
                continue
            col = gradient(pa, slot)
            if pb is not None and blend > 0.0:
                col = col.lerp(gradient(pb, slot), blend)
            if base > 0.85:
                ch = "✦" if tw > 0.85 else ("✧" if tw > 0.6 else "·")
            elif base > 0.6:
                ch = "•" if tw > 0.6 else "·"
            else:
                ch = "·" if tw > 0.5 else "."
            canvas.put((x + off) % self.width, y, ch, col.scale(b))


class Embers:
    """Warm motes that rise and fade -- candlelight sparks."""

    def __init__(self, width: int, height: int, count: int = 0, seed: int = 11):
        self.width = max(1, width)
        self.height = max(1, height)
        rng = random.Random(seed)
        n = count or max(8, self.width // 6)
        self.top = self.height * 0.26
        self.bottom = self.height - 1
        self.motes = []
        for _ in range(n):
            x0 = rng.uniform(self.width * 0.10, self.width * 0.90)
            period = rng.uniform(3.5, 7.0)
            offset = rng.uniform(0.0, 1.0)
            sway = rng.uniform(0.8, 2.6)
            sway_speed = rng.uniform(0.4, 1.1)
            sway_phase = rng.uniform(0.0, TAU)
            self.motes.append((x0, period, offset, sway, sway_speed, sway_phase))

    def render(self, canvas: Canvas, t: float, intensity: float = 1.0) -> None:
        if intensity <= 0.02:
            return
        for (x0, period, offset, sway, sway_speed, sway_phase) in self.motes:
            frac = ((t / period) + offset) % 1.0
            y = self.bottom - frac * (self.bottom - self.top)
            x = x0 + sway * math.sin(t * sway_speed + sway_phase)
            b = math.sin(frac * math.pi) * intensity
            if b <= 0.10:
                continue
            col = gradient([EMBER, AMBER, GOLD], frac).scale(0.5 + 0.5 * b)
            ch = "•" if b > 0.7 else ("·" if b > 0.35 else ".")
            canvas.put(int(round(x)), int(round(y)), ch, col)


class Aurora:
    """A soft, broken, *flowing* curtain of wisp glyphs -- the northern-lights
    motif. Line glyphs only (∿ ~), never blocks."""

    def __init__(self, width: int, height: int, seed: int = 23):
        self.width = max(1, width)
        self.height = max(1, height)
        self.cy = self.height * 0.28
        self.palette = [AURORA_GREEN, AURORA_TEAL, RGB(120, 200, 180), AURORA_VIOLET]

    def render(self, canvas: Canvas, t: float, intensity: float = 1.0) -> None:
        if intensity <= 0.02:
            return
        h = self.height
        for x in range(self.width):
            center = (self.cy
                      + math.sin(x * 0.13 + t * 0.5) * h * 0.05
                      + math.sin(x * 0.05 - t * 0.30) * h * 0.04)
            wave = 0.5 + 0.5 * math.sin(x * 0.21 + t * 0.7)
            if wave < 0.62:                       # sparse, broken ribbon
                continue
            y = int(round(center))
            hue = (x / self.width + t * 0.05) % 1.0
            col = gradient(self.palette, hue).scale(intensity * (0.45 + 0.55 * wave))
            canvas.put(x, y, "∿" if (x + int(t * 4)) % 2 == 0 else "~", col)
            if wave > 0.86:
                canvas.put(x, y + 1, "~", col.scale(0.6))


def falling_stars(canvas: Canvas, t: float, width: int, height: int,
                  events: Sequence[Tuple[float, float, float]]) -> None:
    """Short diagonal streaks. Each event is (trigger_time, x0, life)."""
    for (trig, x0, life) in events:
        if not (trig <= t <= trig + life) or life <= 0:
            continue
        p = (t - trig) / life
        dist = p * height * 1.25
        hx = x0 + dist * 0.5
        hy = -2.0 + dist
        for k in range(0, 5):
            yy = int(hy - k)
            xx = int(hx - k * 0.5)
            if not (0 <= yy < height and 0 <= xx < width):
                continue
            b = (1.0 - k / 5.0) * (1.0 - p)
            if b <= 0.10:
                continue
            canvas.put(xx, yy, "✦" if k == 0 else "·", STARLIGHT.scale(b))


def dissolve(canvas: Canvas, t_since: float, text: str, cx: int, cy: int,
             color: RGB, life: float = 2.6, seed: int = 5) -> None:
    """Lift the glyphs of `text` into rising, fading motes."""
    rng = random.Random(seed)
    for i, ch in enumerate(text):
        rise = rng.uniform(2.5, 5.0)
        drift = rng.uniform(-1.2, 1.2)
        phase = rng.uniform(0.0, TAU)
        delay = rng.uniform(0.0, 0.5)
        if ch == " ":
            continue
        tt = t_since - delay
        if tt < 0.0:
            canvas.put(cx + i, cy, ch, color)
            continue
        p = tt / life
        if p >= 1.0:
            continue
        y = cy - p * rise + math.sin(phase + tt * 2.0) * 0.3
        x = cx + i + drift * p
        glyph = ch if p < 0.5 else ("·" if p < 0.8 else ".")
        canvas.put(int(round(x)), int(round(y)), glyph, color.scale(0.4 + 0.6 * (1.0 - p)))
