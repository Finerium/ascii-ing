"""Wiring: load cues, build the timeline, and run (live / snapshot / selftest)."""
from __future__ import annotations

import sys
import time
import traceback
from typing import List, Optional

from . import lrc
from . import record as _recorder
from .lrc import Cue
from .canvas import Canvas, Renderer
from .color import BLACK
from .terminal import Terminal, size
from .timeline import Timeline
from .scenes import Intro, Lyrics, Outro

# Default frame rates by mode (--fps overrides both).
_LIVE_FPS = 50.0
_RECORD_FPS = 30.0


# Original, NON-lyric placeholder text for --demo (so the show can be tested
# without the real .lrc).
_DEMO_TEXT = [
    "the engine types like this",
    "each glyph arriving in time",
    "warm light gathers in the dark",
    "a quiet breath, held still",
    "and softer now, it fades",
    "yet it stays, just for tonight",
]
_DEMO_STARTS = [0.0, 4.7, 9.8, 14.5, 19.0, 23.5]
_DEMO_END = 27.3


def _demo_cues() -> List[Cue]:
    cues: List[Cue] = []
    for i, text in enumerate(_DEMO_TEXT):
        start = _DEMO_STARTS[i]
        end = _DEMO_STARTS[i + 1] if i + 1 < len(_DEMO_STARTS) else _DEMO_END
        cues.append(Cue(start, end, text))
    return cues


def _load_cues(args) -> Optional[List[Cue]]:
    if getattr(args, "demo", False):
        return _demo_cues()
    entries = lrc.parse_file(args.lrc)
    return lrc.window(entries,
                      lrc.parse_timestamp(args.start),
                      lrc.parse_timestamp(args.end))


def build_timeline(width: int, height: int, cues: List[Cue], args) -> Timeline:
    density = getattr(args, "density", 0.12)
    intro = Intro(width, height, args.title, args.artist, args.dedication, density=density,
                  dedication_glow=getattr(args, "dedication_glow", 0.38))
    lyrics = Lyrics(width, height, cues, density=density)
    last_line = lyrics.lyric_cues[-1].text if lyrics.lyric_cues else ""
    outro = Outro(width, height, last_line, args.dedication, density=density)
    return Timeline([intro, lyrics, outro])


def _snapshot(args, cues: List[Cue], when: float) -> int:
    w, h = size()
    canvas = Canvas(w, h)
    timeline = build_timeline(w, h, cues, args)
    canvas.clear(bg=BLACK)
    timeline.render(canvas, when)
    print(f"--- snapshot @ {when:.2f}s  (total {timeline.duration:.2f}s, {w}x{h}) ---")
    print(canvas.as_plain())
    return 0


def _selftest(args, cues: List[Cue]) -> int:
    w, h = size()
    timeline = build_timeline(w, h, cues, args)
    frames = 0
    t = 0.0
    step = 0.1
    while t < timeline.duration:
        canvas = Canvas(w, h)
        canvas.clear()  # transparent: native terminal background shows through
        try:
            timeline.render(canvas, t)
        except Exception:
            print(f"FAIL at t={t:.2f}s:\n{traceback.format_exc()}", file=sys.stderr)
            return 1
        frames += 1
        t += step
    print(f"selftest OK — {frames} frames over {timeline.duration:.2f}s at {w}x{h}")
    return 0


def _record(args, cues: List[Cue]) -> int:
    cols = getattr(args, "cols", 110)
    rows = getattr(args, "rows", 30)
    fps = args.fps if getattr(args, "fps", None) else _RECORD_FPS
    if cols <= 0 or rows <= 0:
        print("--cols and --rows must be positive.", file=sys.stderr)
        return 2
    if fps <= 0:
        print("--fps must be positive for recording.", file=sys.stderr)
        return 2
    stats = _recorder.record(args.record, cols, rows, fps, build_timeline, cues, args)
    print(f"recorded {args.record} — {stats['events']} events over "
          f"{stats['duration']:.2f}s at {cols}x{rows}, {fps:g} fps")
    return 0


def _run_live(args, cues: List[Cue]) -> int:
    term = Terminal()
    if not term.is_tty():
        print("Run this in a real terminal (TTY). For a preview, try "
              "--snapshot SECONDS or --selftest.", file=sys.stderr)
        return 1

    fps = args.fps if getattr(args, "fps", None) else _LIVE_FPS
    frame = 1.0 / fps if fps > 0 else 0.02
    with term:
        w, h = size()
        canvas = Canvas(w, h)
        renderer = Renderer()
        timeline = build_timeline(w, h, cues, args)
        start = time.perf_counter()
        try:
            while True:
                t = time.perf_counter() - start
                if t >= timeline.duration:
                    break
                if term.take_resize():
                    w, h = size()
                    canvas = Canvas(w, h)
                    renderer = Renderer()
                    timeline = build_timeline(w, h, cues, args)
                canvas.clear()  # transparent: native terminal background shows through
                timeline.render(canvas, t)
                term.write(renderer.render(canvas))
                term.flush()
                lag = (time.perf_counter() - start) - t
                nap = frame - lag
                if nap > 0:
                    time.sleep(nap)
        except KeyboardInterrupt:
            pass
    return 0


def main(args) -> int:
    try:
        cues = _load_cues(args)
    except FileNotFoundError:
        print(f"LRC file not found: {args.lrc}", file=sys.stderr)
        return 2
    if not cues:
        print("No cues found in the selected window.", file=sys.stderr)
        return 2

    if getattr(args, "record", None):
        return _record(args, cues)
    if args.snapshot is not None:
        return _snapshot(args, cues, args.snapshot)
    if args.selftest:
        return _selftest(args, cues)
    return _run_live(args, cues)
