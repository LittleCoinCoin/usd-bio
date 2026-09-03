#!/usr/bin/env python3
"""fig_mod_text.py -- the "mod-text" poster tile: proof the inputs are
literal plain-text files.

Registers "mod-text" with the make_poster_figures harness (see
figures/README.md for the shared six-tile contract). Draws two columns of
real, unmodified bytes, monospaced:

  left  -- consecutive ``ATOM`` records from the p53-MDM2 crystal structure
           (data/structures/1ycr.pdb), starting at the file's first ATOM
           record. Every PDB ATOM line is exactly 80 characters.
  right -- the MaBoSS Boolean-model source (maboss/reference/p53_Mdm2.bnd),
           contiguous from its first byte -- the opening ``node p53`` block.

The claim is *file-ness*: these are literal bytes from real files, not a
rendering of their meaning. Lines longer than a column are geometrically
clipped at the column boundary using matplotlib's ``set_clip_path`` against
a ``Rectangle`` patch -- never by slicing the Python string, which would
silently change which bytes are on screen. The clip is what shows a line
ran past the frame; a sliced string would be a quiet lie about the bytes.

No accent: this tile carries ink/rule greyscale only (the accent is
reserved for Trp23 / the W23A curve on other tiles).
"""

from __future__ import annotations

import math
import os

from matplotlib.patches import Rectangle

from make_poster_figures import (
    CANVAS_MM,
    Theme,
    figure,
    make_figure,
    prov,
    save_figure,
    type_pt,
)

# ---------------------------------------------------------------------------
# Source files -- resolved relative to this script's own path, not cwd, so
# discovery via make_poster_figures._discover_figure_modules() (which loads
# this file by absolute path) works regardless of the caller's cwd.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_P53_MDM2_DIR = os.path.dirname(_HERE)  # examples/p53_mdm2

PDB_PATH = os.path.join(_P53_MDM2_DIR, "data", "structures", "1ycr.pdb")
BND_PATH = os.path.join(_P53_MDM2_DIR, "maboss", "reference", "p53_Mdm2.bnd")

# ---------------------------------------------------------------------------
# Layout constants (mm, in the poster's own canvas frame -- see
# make_poster_figures.CANVAS_MM). These are design choices, not measurements;
# the geometric clip (computed at render time from actual glyph extents,
# see _clip_and_count() below) is what actually enforces the contract, not
# these numbers.
# ---------------------------------------------------------------------------
FONT_SIZE_PT = 22.0          # the hard floor itself: the smallest size that
                             # still satisfies type_pt(), maximizing how much
                             # of each line's real content fits before the
                             # column boundary clips it.
LEADING = 1.25               # "sane leading" per the figures/README contract
OUTER_MARGIN_MM = 3.0        # left edge of left column / right edge of right
RULE_GAP_MM = 3.0            # gap between columns, the hairline sits in its centre
TOP_BOTTOM_MARGIN_MM = 2.0   # floor for the vertical centering computation


def _read_lines(path: str) -> list:
    """Read *path* as a list of lines (no line-terminators), byte-exact.

    Decodes with ``errors="surrogateescape"`` rather than the platform
    default (strict UTF-8): ``p53_Mdm2.bnd`` contains one non-UTF-8 byte
    later in the file (a stray Latin-1 character inside a comment, well
    past anything this figure ever displays -- see the provenance note
    printed at run time). A strict decode raises before we can even reach
    the six lines we actually need; surrogateescape reads every line we DO
    use byte-for-byte identically to a strict decode, since none of them
    touch the bad byte, while never raising on the byte we don't use.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw.decode("utf-8", errors="surrogateescape").splitlines()


def _byte_offset_of_line(path: str, line_index: int) -> int:
    """Return the byte offset of the start of line *line_index* (0-based)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    parts = raw.splitlines(keepends=True)
    return sum(len(p) for p in parts[:line_index])


def _pt_to_mm(pt: float) -> float:
    return pt * 25.4 / 72.0


def main_lines_available(canvas_h_mm: float, line_height_mm: float) -> int:
    """Whole lines that fit in the vertical space, never a partial line."""
    available = canvas_h_mm - 2 * TOP_BOTTOM_MARGIN_MM
    return max(0, math.floor(available / line_height_mm + 1e-9))


@figure("mod-text", ext="svg")
def build_mod_text(theme: Theme, out_dir: str) -> str:
    font_size = type_pt(FONT_SIZE_PT)
    canvas_w, canvas_h = CANVAS_MM

    line_height_mm = prov(
        round(_pt_to_mm(font_size) * LEADING, 6),
        note=f"{font_size}pt font * {LEADING} leading, pt->mm at 25.4/72",
    )
    n_lines = prov(
        main_lines_available(canvas_h, line_height_mm),
        note="whole lines fitting canvas height minus top/bottom margins; "
        "never a partial last line",
    )

    # -- left column: consecutive ATOM records starting at the file's FIRST
    # ATOM record --------------------------------------------------------
    pdb_path = prov(os.path.relpath(PDB_PATH), note="left column source file")
    pdb_all_lines = _read_lines(PDB_PATH)
    first_atom_idx = next(
        i for i, line in enumerate(pdb_all_lines) if line.startswith("ATOM")
    )
    prov(
        first_atom_idx + 1,
        source=pdb_path,
        note="1-indexed line number of the file's first ATOM record",
    )
    prov(
        _byte_offset_of_line(PDB_PATH, first_atom_idx),
        source=pdb_path,
        note="byte offset of the first ATOM record",
    )
    left_lines = pdb_all_lines[first_atom_idx : first_atom_idx + n_lines]
    prov(len(left_lines), source=pdb_path, note="lines shown, left column")

    # -- right column: the .bnd file, contiguous from byte 0 --------------
    bnd_path = prov(os.path.relpath(BND_PATH), note="right column source file")
    bnd_all_lines = _read_lines(BND_PATH)
    prov(0, source=bnd_path, note="byte offset of the right column's first line")
    right_lines = bnd_all_lines[:n_lines]
    prov(len(right_lines), source=bnd_path, note="lines shown, right column")

    # -- geometry -----------------------------------------------------------
    column_width_mm = (canvas_w - 2 * OUTER_MARGIN_MM - RULE_GAP_MM) / 2.0
    left_x = OUTER_MARGIN_MM
    right_x = OUTER_MARGIN_MM + column_width_mm + RULE_GAP_MM
    rule_x = OUTER_MARGIN_MM + column_width_mm + RULE_GAP_MM / 2.0

    block_height_mm = n_lines * line_height_mm
    top_margin_mm = (canvas_h - block_height_mm) / 2.0
    top_of_block_mm = canvas_h - top_margin_mm

    fig, ax = make_figure()
    ax.set_xlim(0, canvas_w)
    ax.set_ylim(0, canvas_h)
    ax.set_axis_off()

    def _draw_column(x0: float, lines: list) -> list:
        # A clip source purely for geometry: never added to the axes, so it
        # is never itself drawn -- its path + transform is all
        # Text.set_clip_path() reads. transform=ax.transData means the
        # rectangle's (x0, 0, column_width_mm, canvas_h) are in the same mm
        # data space the text is placed in.
        clip_rect = Rectangle((x0, 0.0), column_width_mm, canvas_h)
        clip_rect.set_transform(ax.transData)

        texts = []
        for i, line in enumerate(lines):
            y = top_of_block_mm - line_height_mm * (i + 0.5)
            txt = ax.text(
                x0,
                y,
                line,
                fontsize=font_size,
                fontfamily="monospace",
                color=theme.ink,
                ha="left",
                va="center",
                clip_on=True,
            )
            txt.set_clip_path(clip_rect)
            texts.append(txt)
        return texts

    left_texts = _draw_column(left_x, left_lines)
    right_texts = _draw_column(right_x, right_lines)

    # Thin vertical hairline separating the columns -- structure, not a
    # label, per the figures/README accent rule (no accent on this tile).
    ax.plot(
        [rule_x, rule_x],
        [TOP_BOTTOM_MARGIN_MM * 0.5, canvas_h - TOP_BOTTOM_MARGIN_MM * 0.5],
        color=theme.rule,
        linewidth=0.75,
        solid_capstyle="butt",
    )

    # -- measure real glyph extents to report how many lines actually get
    # clipped by the column boundary vs. how many fit whole. Measured from
    # the drawn Text artists themselves (get_window_extent), not from an
    # assumed characters-per-mm ratio -- so this count is empirical, not
    # projected.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    def _count_clipped(x0: float, texts: list) -> int:
        clipped = 0
        for txt in texts:
            bbox = txt.get_window_extent(renderer=renderer)
            (x_left, _), (x_right, _) = (
                inv.transform((bbox.x0, bbox.y0)),
                inv.transform((bbox.x1, bbox.y0)),
            )
            width_mm = abs(x_right - x_left)
            if width_mm > column_width_mm + 1e-6:
                clipped += 1
        return clipped

    left_clipped = prov(
        _count_clipped(left_x, left_texts),
        note="left column: lines whose real rendered width exceeds the "
        f"{column_width_mm:.3f}mm column and are therefore hard-clipped "
        "(measured from actual glyph extents, not assumed)",
    )
    right_clipped = prov(
        _count_clipped(right_x, right_texts),
        note="right column: lines whose real rendered width exceeds the "
        f"{column_width_mm:.3f}mm column and are therefore hard-clipped "
        "(measured from actual glyph extents, not assumed)",
    )
    print(
        f"mod-text: {n_lines} lines/column; left clipped {left_clipped}/"
        f"{len(left_lines)}, right clipped {right_clipped}/{len(right_lines)}"
    )

    out_path = os.path.join(out_dir, "mod-text.svg")
    save_figure(fig, out_path, ext="svg")
    return out_path
