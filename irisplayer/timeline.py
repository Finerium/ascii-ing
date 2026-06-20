"""Sequences scenes back-to-back and dispatches by the master clock."""
from __future__ import annotations

from typing import List, Tuple

from .canvas import Canvas
from .scenes import Scene


class Timeline:
    def __init__(self, scenes: List[Scene]):
        self.entries: List[Tuple[float, Scene]] = []
        t = 0.0
        for s in scenes:
            self.entries.append((t, s))
            t += s.duration
        self.duration = t

    def render(self, canvas: Canvas, t: float) -> None:
        for start, scene in reversed(self.entries):
            if t >= start:
                scene.render(canvas, t - start)
                return
        if self.entries:
            self.entries[0][1].render(canvas, 0.0)
