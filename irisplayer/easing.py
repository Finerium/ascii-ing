"""Easing functions. Each maps t in [0, 1] -> roughly [0, 1].

`out_back` intentionally overshoots above 1 before settling, for an
organic 'snap'. Inputs are clamped at the edges so callers can pass raw
progress values without guarding.
"""
from __future__ import annotations

import math


def clamp01(t: float) -> float:
    return 0.0 if t < 0.0 else 1.0 if t > 1.0 else t


def linear(t: float) -> float:
    return clamp01(t)


def in_quad(t: float) -> float:
    t = clamp01(t)
    return t * t


def out_quad(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def in_out_cubic(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    f = -2.0 * t + 2.0
    return 1.0 - (f * f * f) / 2.0


def out_expo(t: float) -> float:
    t = clamp01(t)
    if t >= 1.0:
        return 1.0
    return 1.0 - math.pow(2.0, -10.0 * t)


def out_back(t: float, overshoot: float = 1.70158) -> float:
    t = clamp01(t)
    c3 = overshoot + 1.0
    u = t - 1.0
    return 1.0 + c3 * u * u * u + overshoot * u * u


def smoothstep(t: float) -> float:
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def pulse(t: float) -> float:
    """0 -> 1 -> 0 over t in [0, 1]; a smooth there-and-back (sine arch)."""
    return math.sin(clamp01(t) * math.pi)
