# ascii-ing

**A terminal lyric film — a from-scratch, zero-dependency truecolor TUI engine that types lyrics over an evolving, hand-drawn cosmos.**

`ascii-ing` turns any `.lrc` file into a short cinematic experience that plays *inside your terminal*: a hushed title card fades up from a starfield, six lines type themselves out — humanized, one glyph at a time — over a sky that shifts color with every emotional beat, and the final line implodes into a singularity and detonates in a big-bang outro that settles back into stars.

No frameworks. No `pip install`. No `curses`. Just Python's standard library, a pile of ANSI escape codes, and a compositor written from the cell up.

> The engine is **content-neutral** and ships **no lyrics of its own** — it renders whatever `.lrc` you point it at. Run `--demo` to see it in motion with built-in, non-lyric placeholder text.

---

## Live demo

**▶ <!-- VERCEL_URL -->**

The web version is a terminal recording played back in the browser via [asciinema-player](https://github.com/asciinema/asciinema-player) — the *exact* frames the engine emits, pixel-for-pixel, no re-implementation. It's **click-to-start**: press play and watch the whole film, including the typewriter, the color cross-fades, and the outro.

> The hosted demo plays the safe, **non-lyric** placeholder reel (`web/demo.cast`). To see it with a song of your own, run it locally (see [Run it](#run-it)).

---

## What you'll see

A three-act film, sequenced on a single master clock:

1. **Intro — the title card.** A colored starfield fades in from the void. The title and artist appear with a soft letter-spaced reveal; a faint aurora ribbon drifts behind a dedication tucked into the corner liner-notes. Hold, then dissolve.
2. **Lyrics — typed over a living sky.** Each line types out with human cadence (micro-pauses after punctuation, a gentle blinking caret); the previous line drifts up and fades. Behind the text, an entire cosmos evolves **per beat** — a dense star-field whose palette cross-fades between moods, plus a crescent moon, drifting ringed planets, comets, satellites, shooting stars, constellations that draw themselves in, a slow nebula, and candlelight embers.
3. **Outro — the big bang.** The last line collapses inward to a single point, pulses as a singularity, then explodes in a radial burst with a shockwave ring. The debris cools into a brand-new starfield and fades to black — and your terminal is restored, clean.

### Features

| | Feature |
|---|---|
| 🎬 | Three-act film: **title card → typed lyrics → big-bang outro**, on one clock |
| ⌨️ | **Humanized typewriter** — per-character jitter, punctuation pauses, blinking caret |
| 🌌 | **Cosmos effect system** — moon, planets, comet, satellite, constellations, nebula, shooting stars |
| ✨ | **Per-beat star palettes** — the whole field recolors coherently as the mood turns |
| 🟦 | **Truecolor** (24-bit) throughout, with transparent backgrounds so your terminal's own backdrop shows through |
| 🪶 | **Flicker-free** at ~50 fps via a double-buffered, minimal-diff compositor |
| 🧱 | **Zero dependencies** — Python 3 standard library only |
| 🛟 | **Ctrl-C-safe** — the alternate screen is always restored, even on exceptions |
| 📐 | **Resize-aware** — rebuilds the scene live on `SIGWINCH` |
| 🌐 | **Web port** via asciinema — identical rendering in the browser, click-to-start |

---

## Engineering highlights

This is the interesting part. The whole thing is a small studio of single-purpose modules, each a pure function of time — so a given timestamp always produces the same frame, dropped frames never desync the show, and any moment can be rendered headlessly for tests.

### A double-buffered, minimal-diff compositor

The heart of the engine is `irisplayer/canvas.py`. A `Canvas` is a grid of immutable cells — `(char, fg, bg, bold)` tuples — so whole frames compare cheaply with `==`. Each frame, the `Renderer` diffs the new grid against the previously drawn one and **emits ANSI only for the cells that actually changed**:

- Unchanged cells are skipped entirely.
- The cursor only jumps (`ESC[y;xH`) when the next dirty cell isn't adjacent to the last one — runs of changes stream out with no repositioning.
- The color/bold "pen" is only re-issued when it differs from the current state, so a row of same-colored glyphs costs one escape, not one per cell.

The result is **flicker-free truecolor animation at ~50 fps** with a fraction of the bytes a naive full-repaint would push. The behavior is pinned by tests: an identical frame emits *no* cursor moves; a single changed cell emits exactly one move to the right coordinate.

### Layered scene + timeline architecture

`timeline.py` sequences three `Scene`s back-to-back with absolute start times and dispatches by a master clock; each scene renders against its own *local* time. Scenes are **stateless in time** — `render(canvas, t_local)` recomputes everything from `t`, never from accumulated state. That's what makes the show robust to frame drops and trivially snapshot-able.

### A particle + "cosmos" effect system

`particles.py` and `cosmos.py` are a library of composable, time-pure effects: a twinkling colored starfield with parallax near/far layers, rising candlelight embers, flowing aurora wisps, plus the celestial set — crescent moon with a cloud halo, ringed drifting planets, a comet with a fading tail, a blinking satellite, self-drawing constellations, a nebula, and shooting-star bursts. Every effect obeys one **hard rule: foreground glyphs only** — colored points and lines on a transparent background, *never* a filled block or background color. That keeps the native terminal showing through and makes "colored boxes" structurally impossible.

The mood lives entirely in the **per-beat star palettes** (`color.py`): each star owns a fixed slot in `[0, 1)` and samples whatever palette the current beat passes in, so when two beats cross-fade the *entire field* recolors in lockstep — while the lyric text stays a constant, readable white.

### A humanized typewriter

`textfx.py` precomputes, for each line, the cumulative time at which every character becomes visible: a base characters-per-second rate, deterministic per-character jitter, and longer pauses *after* punctuation (`,;:` short, `.!?—` longer). Drawing is left to the scene layer, so the timing logic stays pure and unit-tested. The caret is a square-wave blink. Same seed → types the same way every run.

### Bulletproof terminal lifecycle

`terminal.py` is a context manager: on enter it switches to the alternate screen buffer, hides the cursor, and **disables auto-wrap** (so a glyph in the last column can never scroll the view); on exit — *including* on exceptions or Ctrl-C — it restores wrap, the cursor, the main screen, and resets colors. It also installs a `SIGWINCH` handler so the render loop can rebuild the canvas and scenes the instant the window is resized.

### The single-width-glyph invariant (a gotcha, and the test that guards it)

> The compositor's correctness rests on one assumption: **every glyph occupies exactly one terminal cell.**

Early on, the intro divider used a pretty fullwidth tilde — `～` (U+FF5E, FULLWIDTH TILDE) — instead of the plain `~`. It *looks* like one character, but East-Asian **Wide/Fullwidth** glyphs render two columns wide. The minimal-diff renderer advances its cursor by one cell per glyph, so the second column the terminal painted was never tracked — and never cleared. The result was "stuck" smears trailing across the sky that no later frame could erase, because as far as the diff was concerned, nothing there had changed.

The fix was to ban wide glyphs from the render path — and, more importantly, to make the rule *enforceable*. `tests/test_no_wide_glyphs.py` walks every source file in `irisplayer/` and fails if any character has an East-Asian width of `W` or `F`:

```python
if unicodedata.east_asian_width(ch) in ("W", "F"):
    bad.append(f"{os.path.basename(path)}:{lineno} U+{ord(ch):04X} {ch!r}")
self.assertEqual(bad, [], "double-width glyphs found: " + "; ".join(bad))
```

It's a tiny test, but it encodes a hard-won invariant: the engine deliberately uses only single-width box-drawing and astral glyphs (`✦ ✧ • · ∿ ◉ ◍ ╴ ╶`), and the suite won't let a wide one sneak back in.

### How the web port works

The browser version is **not** a rewrite — it's the real engine, recorded. The pipeline is:

1. **The engine records itself** — no external tools: `python3 iris.py --record web/iris.cast` writes an [asciinema v2](https://docs.asciinema.org/manual/asciicast/v2/) cast — the exact minimal-diff ANSI frames the terminal emits, each stamped with its timeline time (`--cols`/`--rows`/`--fps` set the virtual size + rate; default **110 × 30 @ 30 fps**).
2. A static page (`web/index.html`) loads [asciinema-player](https://github.com/asciinema/asciinema-player) and plays that cast.
3. Deploy the static folder to Vercel.

Because the cast carries the engine's own ANSI byte stream, playback is **identical** to the terminal — same truecolor, same minimal-diff frames, same timing — and it starts on a click. `web/demo.cast` (the non-lyric `--demo` recording) is committed as the safe public fallback, so the repo never distributes copyrighted text.

---

## Run it

Requires **Python 3** (3.8+). Nothing to install.

```bash
python3 iris.py            # play the show in your terminal
```

Run it in a real, truecolor terminal (iTerm2, Terminal.app, Ghostty, Kitty, WezTerm…). For the most cinematic result, give it room — **≥ ~90 × 30**. Press **Ctrl-C** any time; the screen restores itself cleanly.

### No file? Use the demo

```bash
python3 iris.py --demo     # built-in NON-lyric placeholder reel
```

### Useful flags

```bash
python3 iris.py --demo                     # original, non-lyric placeholder text
python3 iris.py --from 00:21.03 --to 00:48.34   # choose the lyric window (MM:SS.xx)
python3 iris.py --dedication "for someone, somewhere"
python3 iris.py --density 0.20             # starfield density (0.05 sparse .. 0.30 dense)
python3 iris.py --fps 60                   # smoother playback

python3 iris.py --snapshot 24              # print ONE frame as plain text and exit (no TTY needed)
python3 iris.py --selftest                 # render the whole timeline headlessly and report
```

| Flag | Purpose |
|---|---|
| `--lrc PATH` | The `.lrc` file to render (default `Iris.lrc`) |
| `--from MM:SS.xx` / `--to MM:SS.xx` | Start/end of the lyric window |
| `--title` / `--artist` | Text shown on the intro title card |
| `--dedication TEXT` | A personal dedication, shown in the intro and reprised in the outro |
| `--density N` | Starfield density, `0.05` (sparse) → `0.30` (very dense) |
| `--fps N` | Target frame rate (default `50` live, `30` when recording) |
| `--demo` | Use the built-in non-lyric placeholder text — no file needed |
| `--record PATH` | Capture the whole animation to an asciinema v2 `.cast` (powers the web port) |
| `--cols N` / `--rows N` | The recording's fixed virtual size (default `110 × 30`) |
| `--snapshot SECONDS` | Print a single frame as plain text and exit — handy for verifying composition |
| `--selftest` | Render every frame of the timeline headlessly and report; great for CI |

> **Recording for the web?** The engine records *itself* — no external tools. `python3 iris.py --record web/iris.cast` (real run) or `python3 iris.py --demo --record web/demo.cast` (non-lyric) writes a standard [asciinema v2](https://docs.asciinema.org/manual/asciicast/v2/) `.cast`. It's byte-identical to the live render, so the web playback matches the terminal exactly.

---

## Project structure

```
ascii-ing/
├── iris.py                  # CLI entry point (argparse → app.main)
├── irisplayer/              # the engine (zero-dependency, stdlib only)
│   ├── color.py             #   RGB, lerp/scale/desaturate, gradients, truecolor ANSI, palettes
│   ├── easing.py            #   easing curves (quad/cubic/expo/back, smoothstep, pulse)
│   ├── lrc.py               #   LRC parser + [start,end] windowing into timed cues
│   ├── textfx.py            #   humanized typewriter timing + blinking caret
│   ├── canvas.py            #   Canvas + minimal-diff double-buffered Renderer  ← the compositor
│   ├── terminal.py          #   alt-screen / hide-cursor / no-wrap / Ctrl-C-safe restore, resize
│   ├── particles.py         #   starfield, embers, aurora, falling stars, dissolve
│   ├── cosmos.py            #   moon, planets, comet, satellite, constellation, nebula, big-bang
│   ├── scenes.py            #   the three acts: Intro / Lyrics / Outro (per-beat star palettes)
│   ├── timeline.py          #   sequences scenes on a master clock
│   └── app.py               #   wiring: load cues → build timeline → run (live/snapshot/selftest)
├── tests/                   # stdlib unittest, lyric-free fixtures
│   ├── test_color.py
│   ├── test_easing.py
│   ├── test_lrc.py
│   ├── test_textfx.py
│   ├── test_canvas.py       #   pins the minimal-diff behavior
│   └── test_no_wide_glyphs.py   #   enforces the single-width-glyph invariant
├── docs/superpowers/specs/  # the original design spec
└── web/                     # the web port (built at deploy time)
    ├── index.html           #   asciinema-player page
    └── demo.cast            #   the safe, non-lyric recording (committed)
```

---

## Testing

The pure-logic modules are covered by stdlib `unittest` with **lyric-free, synthetic fixtures** — LRC parsing and window boundaries/holds, color math, easing endpoints and monotonicity, typewriter scheduling, the compositor's diff behavior, and the wide-glyph guard.

```bash
python3 -m unittest discover -s tests -t .
```

A headless end-to-end pass is built into the CLI:

```bash
python3 iris.py --demo --selftest    # renders every frame; fails loudly on any error
```

---

## Content & copyright

`ascii-ing` is a **content-neutral renderer**. The source code, the tests, and this repository contain **no song lyrics** — the engine simply animates whatever `.lrc` file you give it at runtime, and lyric lines are never embedded in the source.

- Use `--demo` to run the show with built-in, **original non-lyric** placeholder text — no file required.
- If you point it at a real `.lrc`, those **lyrics are the property of their respective owners** and are not distributed by this project. (Your local `.lrc` files are git-ignored.)
- The hosted web demo plays only the non-lyric `web/demo.cast`.
- Intended for **personal and educational use**. Please respect the rights of songwriters and publishers.

---

## License

[MIT](./LICENSE) © 2026 Finerium
