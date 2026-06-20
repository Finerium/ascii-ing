#!/usr/bin/env python3
"""Iris — a terminal lyric film.

A zero-dependency, content-neutral .lrc renderer. Reads a lyrics file and
plays a short, animated, real-time-typed presentation of a chosen window.

    python3 iris.py                 # the default Iris window
    python3 iris.py --demo          # placeholder (non-lyric) text
    python3 iris.py --snapshot 24   # print one frame as plain text
    python3 iris.py --selftest      # headless render of the whole timeline
    python3 iris.py --record out.cast   # capture to an asciinema v2 .cast
"""
from __future__ import annotations

import argparse
import sys

from irisplayer import app


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="iris.py", description="Iris — a terminal lyric film.")
    p.add_argument("--lrc", default="Iris.lrc", help="path to the .lrc file")
    p.add_argument("--from", dest="start", default="00:21.03",
                   help="window start (MM:SS.xx)")
    p.add_argument("--to", dest="end", default="00:48.34",
                   help="window end (MM:SS.xx)")
    p.add_argument("--title", default="Iris", help="song title for the intro")
    p.add_argument("--artist", default="The Goo Goo Dolls",
                   help="artist for the intro")
    p.add_argument("--dedication", default="pour les aurores boréales",
                   help="dedication shown in the intro and outro")
    p.add_argument("--fps", type=float, default=None,
                   help="target frame rate (default: 50 live, 30 when --record)")
    p.add_argument("--density", type=float, default=0.12,
                   help="starfield density (0.05 sparse .. 0.30 very dense)")
    p.add_argument("--dedication-glow", dest="dedication_glow", type=float, default=0.38,
                   help="dedication visibility (0.15 barely there .. 1.0 full)")
    p.add_argument("--record", default=None, metavar="PATH",
                   help="capture the full animation to an asciinema v2 .cast file")
    p.add_argument("--cols", type=int, default=110,
                   help="recording width in columns (fixed virtual size)")
    p.add_argument("--rows", type=int, default=30,
                   help="recording height in rows (fixed virtual size)")
    p.add_argument("--snapshot", type=float, default=None, metavar="SECONDS",
                   help="print a single frame (plain text) at this time and exit")
    p.add_argument("--selftest", action="store_true",
                   help="render the whole timeline headlessly and report")
    p.add_argument("--demo", action="store_true",
                   help="use built-in non-lyric placeholder text")
    return p


def main() -> int:
    args = build_parser().parse_args()
    return app.main(args)


if __name__ == "__main__":
    sys.exit(main())
