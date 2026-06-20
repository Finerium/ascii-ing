"""Humanized typewriter timing and a blinking cursor.

Pure logic: given a line of text, precompute when each character becomes
visible (slight jitter, plus pauses after punctuation), then query how
many characters are visible at a given elapsed time. Drawing happens in
the scene layer so this stays testable and content-neutral.
"""
from __future__ import annotations

import bisect
import random
from typing import List


def reveal_schedule(
    text: str,
    cps: float = 22.0,
    seed: int = 0,
    comma_pause: float = 0.18,
    stop_pause: float = 0.34,
    jitter: float = 0.4,
) -> List[float]:
    """Cumulative time (s) at which each character index becomes visible.

    ``cps`` is the base characters-per-second. A human-feeling pause is
    added *after* punctuation. Deterministic for a given ``seed`` so a line
    types the same way every run.
    """
    rng = random.Random(seed)
    base = 1.0 / cps if cps > 0 else 0.0
    times: List[float] = []
    t = 0.0
    for ch in text:
        step = base * (1.0 + rng.uniform(-jitter, jitter))
        t += step
        times.append(t)
        if ch in ",;:":
            t += comma_pause
        elif ch in ".!?—":  # . ! ? and em dash
            t += stop_pause
    return times


def revealed_count(schedule: List[float], elapsed: float) -> int:
    """How many characters are visible at ``elapsed`` seconds."""
    return bisect.bisect_right(schedule, elapsed)


def total_time(schedule: List[float]) -> float:
    return schedule[-1] if schedule else 0.0


def cursor_visible(elapsed: float, blinks_per_sec: float = 2.0) -> bool:
    """Square-wave blink for the typing caret."""
    if blinks_per_sec <= 0:
        return True
    return int(elapsed * blinks_per_sec * 2) % 2 == 0
