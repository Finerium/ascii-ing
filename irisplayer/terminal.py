"""Terminal setup/teardown and capability detection.

Use as a context manager so the screen is always restored -- even on
exceptions or Ctrl-C::

    with Terminal() as term:
        ...

It switches to the alternate screen buffer, hides the cursor, and disables
auto-wrap (so a glyph in the last column never scrolls the view). On exit
it restores everything and resets colors.
"""
from __future__ import annotations

import os
import shutil
import signal
import sys
from typing import Optional, TextIO, Tuple

ENTER_ALT = "\x1b[?1049h"
EXIT_ALT = "\x1b[?1049l"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
DISABLE_WRAP = "\x1b[?7l"
ENABLE_WRAP = "\x1b[?7h"
CLEAR = "\x1b[2J\x1b[H"


def supports_truecolor() -> bool:
    return os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")


def size(fallback: Tuple[int, int] = (80, 24)) -> Tuple[int, int]:
    s = shutil.get_terminal_size(fallback=fallback)
    return s.columns, s.lines


class Terminal:
    def __init__(self, stream: Optional[TextIO] = None):
        self.out: TextIO = stream if stream is not None else sys.stdout
        self._entered = False
        self._resized = False
        self._prev_winch = None

    # -- context manager -------------------------------------------------
    def __enter__(self) -> "Terminal":
        self.write(ENTER_ALT + HIDE_CURSOR + DISABLE_WRAP + CLEAR)
        self.flush()
        self._entered = True
        try:
            self._prev_winch = signal.signal(signal.SIGWINCH, self._on_resize)
        except (ValueError, AttributeError, OSError):
            self._prev_winch = None  # not main thread / unsupported platform
        return self

    def __exit__(self, *exc) -> bool:
        if self._prev_winch is not None:
            try:
                signal.signal(signal.SIGWINCH, self._prev_winch)
            except (ValueError, OSError):
                pass
        self.write(ENABLE_WRAP + SHOW_CURSOR + EXIT_ALT + "\x1b[0m")
        self.flush()
        self._entered = False
        return False  # never suppress exceptions

    # -- resize ----------------------------------------------------------
    def _on_resize(self, *_a) -> None:
        self._resized = True

    def take_resize(self) -> bool:
        """Return True once after the terminal has been resized."""
        was = self._resized
        self._resized = False
        return was

    # -- io --------------------------------------------------------------
    def write(self, s: str) -> None:
        self.out.write(s)

    def flush(self) -> None:
        self.out.flush()

    def is_tty(self) -> bool:
        try:
            return self.out.isatty()
        except Exception:
            return False
