"""Record the full animation to an asciinema v2 ``.cast`` file.

This captures the *exact* byte stream the live terminal renderer would
emit -- the same minimal ANSI diffs produced by :class:`Renderer` -- so a
web player (asciinema-player) replays it looking identical to the TTY.

It does NOT pace in real time: frames are generated as fast as possible,
but each event is stamped with its correct *timeline* time ``t = i/fps``.
The recording uses a fixed virtual size (``cols`` x ``rows``) that is
independent of the real terminal, and never uses the alternate-screen
buffer (so the cast plays cleanly inside a web player viewport).

asciinema v2 format (one JSON value per line):
  * line 1: header object
  * line 2..: event arrays ``[time, "o", data]``  ("o" = output stream)
"""
from __future__ import annotations

import json
from typing import List, TextIO

from .canvas import Canvas, Renderer
from .lrc import Cue
from .timeline import Timeline

# Control sequences for a clean start (deliberately NOT the alt-screen).
_HIDE_CURSOR = "\x1b[?25l"
_CLEAR = "\x1b[2J\x1b[H"   # erase display, then home the cursor

# Tiny offset so the very first "clean-start" event sorts strictly before
# frame 0 yet is still effectively t=0 for the player.
_PRIMER_T = 0.0


def _header(cols: int, rows: int) -> str:
    # NOTE: key order is fixed for stable, reviewable output.
    obj = {
        "version": 2,
        "width": cols,
        "height": rows,
        "timestamp": 0,
        "env": {"TERM": "xterm-256color"},
        "title": "Iris",
    }
    return json.dumps(obj, ensure_ascii=False)


def _event(t: float, data: str) -> str:
    # json.dumps escapes every control char (ESC -> , etc.) and emits a
    # compact single line. "o" is the asciinema output-stream marker.
    return json.dumps([t, "o", data], ensure_ascii=False)


def write_cast(out: TextIO, cols: int, rows: int, fps: float,
               build_timeline, cues: List[Cue], args) -> dict:
    """Render the whole timeline into ``out`` as an asciinema v2 cast.

    ``build_timeline`` is :func:`irisplayer.app.build_timeline` (passed in to
    avoid a circular import). Returns a small stats dict for verification.
    """
    if fps <= 0:
        raise ValueError("fps must be > 0 for recording")

    canvas = Canvas(cols, rows)
    renderer = Renderer()
    timeline = build_timeline(cols, rows, cues, args)
    duration = timeline.duration

    out.write(_header(cols, rows))
    out.write("\n")

    events = 0
    last_t = 0.0

    # Clean-start primer at t=0: hide the cursor, then clear the screen so the
    # very first painted frame lands on a blank canvas (no alt-screen buffer).
    out.write(_event(_PRIMER_T, _HIDE_CURSOR + _CLEAR))
    out.write("\n")
    events += 1
    last_t = _PRIMER_T

    # Frame loop: stamp timeline time, emit the identical diff string.
    i = 0
    while True:
        t = i / fps
        if t >= duration:
            break
        canvas.clear()  # transparent: matches the live renderer exactly
        timeline.render(canvas, t)
        diff = renderer.render(canvas)
        out.write(_event(t, diff))
        out.write("\n")
        events += 1
        last_t = t
        i += 1

    return {
        "cols": cols,
        "rows": rows,
        "fps": fps,
        "duration": duration,
        "events": events,
        "last_t": last_t,
    }


def record(path: str, cols: int, rows: int, fps: float,
           build_timeline, cues: List[Cue], args) -> dict:
    """Open ``path`` and write the cast; return verification stats."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        return write_cast(fh, cols, rows, fps, build_timeline, cues, args)
