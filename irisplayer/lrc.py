"""Minimal LRC parser.

Parses lines of the form ``[mm:ss.xx]text`` (several timestamps per line
allowed) into time-ordered entries, and slices a ``[start, end]`` window
into display *cues* with explicit hold/end times. Blank-text entries are
kept as timing markers (instrumental gaps / line-end holds).

This module never contains lyrics; it only reads them from a file at
runtime.
"""
from __future__ import annotations

import re
from typing import List, NamedTuple

_TIME_RE = re.compile(r"\[(\d{1,3}):(\d{1,2}(?:\.\d{1,3})?)\]")


class Entry(NamedTuple):
    time: float   # seconds
    text: str


class Cue(NamedTuple):
    start: float  # seconds, relative to the window start
    end: float    # seconds, relative to the window start (when it stops showing)
    text: str     # "" for an instrumental gap / hold

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def is_blank(self) -> bool:
        return not self.text


def parse(text: str) -> List[Entry]:
    """Parse LRC text into time-ordered entries (blank lines included)."""
    entries: List[Entry] = []
    for raw in text.splitlines():
        stamps = list(_TIME_RE.finditer(raw))
        if not stamps:
            continue
        content = raw[stamps[-1].end():].strip()
        for m in stamps:
            minutes = int(m.group(1))
            seconds = float(m.group(2))
            entries.append(Entry(minutes * 60 + seconds, content))
    entries.sort(key=lambda e: e.time)
    return entries


def parse_file(path: str) -> List[Entry]:
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read())


def parse_timestamp(s: str) -> float:
    """Accept 'MM:SS.xx', 'M:SS', or plain seconds."""
    s = s.strip()
    if ":" in s:
        mm, ss = s.split(":", 1)
        return int(mm) * 60 + float(ss)
    return float(s)


def window(entries: List[Entry], start: float, end: float) -> List[Cue]:
    """Slice ``[start, end]`` (inclusive) into relative-timed cues.

    Each cue runs until the next entry's time (clamped to ``end``). Blank
    entries become blank cues (background only). Zero-length cues at the
    boundary are dropped.
    """
    eps = 1e-6
    selected = [e for e in entries if start - eps <= e.time <= end + eps]
    cues: List[Cue] = []
    for i, e in enumerate(selected):
        nxt = selected[i + 1].time if i + 1 < len(selected) else end
        nxt = min(nxt, end)
        if nxt - e.time <= eps:
            continue
        cues.append(Cue(e.time - start, nxt - start, e.text))
    return cues
