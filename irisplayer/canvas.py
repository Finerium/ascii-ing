"""Double-buffered terminal canvas with minimal-diff rendering.

A :class:`Canvas` is a grid of cells. The :class:`Renderer` compares the
new frame against the previously drawn frame and emits only the ANSI
needed to update the cells that changed -- the key to flicker-free, fast
terminal animation.

A cell is an immutable tuple ``(char, fg, bg, bold)`` so whole frames
compare cheaply with ``==``.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .color import RGB, fg as ansi_fg, bg as ansi_bg, RESET, DEFAULT_FG, DEFAULT_BG

Cell = Tuple[str, Optional[RGB], Optional[RGB], bool]
EMPTY: Cell = (" ", None, None, False)


class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[Cell]] = [
            [EMPTY] * width for _ in range(height)
        ]

    def clear(self, char: str = " ", fg: Optional[RGB] = None,
              bg: Optional[RGB] = None) -> None:
        cell: Cell = (char, fg, bg, False)
        for y in range(self.height):
            row = self.cells[y]
            for x in range(self.width):
                row[x] = cell

    def put(self, x: int, y: int, char: str, fg: Optional[RGB] = None,
            bg: Optional[RGB] = None, bold: bool = False) -> None:
        if 0 <= x < self.width and 0 <= y < self.height and char:
            self.cells[y][x] = (char[0], fg, bg, bold)

    def put_bg(self, x: int, y: int, bg: RGB) -> None:
        """Set only the background of a cell, preserving its glyph + fg."""
        if 0 <= x < self.width and 0 <= y < self.height:
            ch, f, _, bold = self.cells[y][x]
            self.cells[y][x] = (ch, f, bg, bold)

    def text(self, x: int, y: int, s: str, fg: Optional[RGB] = None,
             bg: Optional[RGB] = None, bold: bool = False) -> None:
        for i, ch in enumerate(s):
            self.put(x + i, y, ch, fg, bg, bold)

    def text_center(self, y: int, s: str, fg: Optional[RGB] = None,
                    bg: Optional[RGB] = None, bold: bool = False) -> int:
        """Draw ``s`` horizontally centered on row ``y``; returns its start x."""
        x = (self.width - len(s)) // 2
        self.text(x, y, s, fg, bg, bold)
        return x

    def as_plain(self) -> str:
        """Render glyphs only (no color) -- used for snapshot verification."""
        return "\n".join(
            "".join(cell[0] for cell in row).rstrip()
            for row in self.cells
        )


class Renderer:
    """Holds the previous frame and computes minimal ANSI diffs."""

    def __init__(self) -> None:
        self._prev: Optional[List[List[Cell]]] = None

    def reset(self) -> None:
        self._prev = None

    def render(self, canvas: Canvas) -> str:
        prev = self._prev
        out: List[str] = []
        cur_fg: Optional[RGB] = None
        cur_bg: Optional[RGB] = None
        cur_bold = False
        pen_set = False
        last_x = last_y = -2
        for y in range(canvas.height):
            row = canvas.cells[y]
            prow = prev[y] if prev is not None else None
            for x in range(canvas.width):
                cell = row[x]
                if prow is not None and cell == prow[x]:
                    continue
                char, f, b, bold = cell
                if y != last_y or x != last_x + 1:
                    out.append(f"\x1b[{y + 1};{x + 1}H")
                if not pen_set or f != cur_fg:
                    out.append(ansi_fg(f) if f is not None else DEFAULT_FG)
                    cur_fg = f
                if not pen_set or b != cur_bg:
                    out.append(ansi_bg(b) if b is not None else DEFAULT_BG)
                    cur_bg = b
                if not pen_set or bold != cur_bold:
                    out.append("\x1b[1m" if bold else "\x1b[22m")
                    cur_bold = bold
                pen_set = True
                out.append(char)
                last_x, last_y = x, y
        out.append(RESET)
        self._prev = [row[:] for row in canvas.cells]
        return "".join(out)
