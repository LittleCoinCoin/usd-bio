#!/usr/bin/env python3
"""
fig_mod_state.py -- poster figure "mod-state": the discrete Boolean network
state of the W23A MaBoSS model, as a 5-row x 500-column on/off raster.

Why this figure is NOT a threshold of the stored probabilities
----------------------------------------------------------------
The brief that spawned this figure assumed Boolean node state was stored on
the USD stage. It is not: the stage carries only continuous per-node
probabilities (``bio:maboss:prob:<node>``, 500 frames) and
``maboss/output/`` holds only the MaBoSS model text (``.bnd``/``.cfg``).
Thresholding a probability into on/off would mean inventing a cut-off,
which this job forbids.

MaBoSS itself resolves this without inventing anything: pyMaBoSS's
``get_states_probtraj()`` returns the occupancy of each *network state* --
and a network state IS a Boolean vector over all five nodes, discrete by
construction. Taking the modal (argmax-occupancy) network state per frame
gives a flicker-free stepped trajectory with no invented threshold anywhere
-- see ``examples/p53_mdm2/figures/README.md``'s "mod-state" section for the
full account and the probed expectation this module asserts against.

Model + backend
----------------
Uses the committed W23A model (``maboss/output/p53_Mdm2_W23A.{bnd,cfg}``,
seed 100, thread_count 1 -> deterministic), driven through the existing
``run_maboss.py`` helpers: ``ensure_backend()`` (the external MaBoSS binary
trap -- see that module's docstring), ``variant_model_paths()`` and
``_sanitise_to_utf8()`` (the .bnd carries two non-UTF-8 bytes in comments).
The external binary is used, never ``cmaboss`` (documented elsewhere as
returning a wrong node set / empty state labels).

Contract for this tile (see figures/README.md for the full canvas contract)
-----------------------------------------------------------------------------
- Canvas 214.94 x 64.482 mm, transparent background, >=22pt type.
- Ink/greyscale only -- NO accent on this tile (the accent is reserved for
  Trp23 / the W23A curve elsewhere); "off" cells are rendered in the
  theme's own ``field`` token (so they blend into the poster tile under
  any theme) and "on" cells are shaded between ``field`` and ``ink`` --
  see "Honesty fix" below.
- No title, no legend, no caption; axis labels are required and present
  (y: the five node names as category labels; x: "frame").

Honesty fix: ON-cell tone encodes the modal state's occupancy
---------------------------------------------------------------
An adversarial review of the first version of this figure (which drew every
ON cell as flat, full-strength ink) found a real defect: the "modal" network
state is only ever an argmax over the ensemble, and for large stretches of
the trajectory it is a MINORITY of that ensemble. Measured on this exact run,
modal-state occupancy ranges from 0.283363 (frame 39) to 0.882683 (frame
252), mean 0.751071258, median 0.835438 -- and 86 of 500 frames (17.2% of
the tile's width) have the "winning" state below 0.5 occupancy. Segments 1-3
(frames 0-73) never exceed 0.44 occupancy; segment 4 does not clear 0.5
until roughly 12 frames into its 426-frame run. Drawing all of that in flat,
maximum-strength ink claimed a certainty the data does not have, exactly
across the transitions -- the visually interesting part of the tile.

The fix: every ON cell's ink tone is linearly mapped from that frame's
modal-state occupancy, using the run's own measured [min, max] occupancy
range (not the full [0, 1] scale, which would waste most of the tile's
tonal range on certainty values this model never reaches) --

    tone_fraction(occ) = TONE_FLOOR + (1 - TONE_FLOOR) *
                          (occ - occ_min) / (occ_max - occ_min)

with ``TONE_FLOOR = 0.35`` (see the constant below), so the least-certain
ON cell (occupancy 0.283363) still renders at 35% of the way from ``field``
to ``ink`` -- a measured 0.298 luminance margin below the OFF/field tone,
comfortably above the noise floor -- and the most-certain ON cell (occupancy
0.882683) renders at full ink. OFF cells are unaffected: always exactly
``field``, one single colour, never confusable with even the palest ON cell.
Both endpoints of the blend (``field``, ``ink``) are the tile's existing
neutral tokens, so this stays ink/greyscale-only -- no new hue, no accent.

Per-frame tone variation is compatible with "hard vertical step edges":
``imshow(..., interpolation="nearest")`` never blends across neighbouring
columns, so each frame is still one flat-coloured rectangle -- it is just
that the rectangle's own shade now tracks that frame's occupancy instead of
being a constant. The Boolean on/off pattern itself (which segments exist,
where they start and end) is completely unchanged from the first version
and is asserted identically.

Run this file directly (``python fig_mod_state.py``) to execute the full
gate suite described in the task brief and print real output, including
the segment table, per-node ON counts, the occupancy range and the tone
range it maps to, and two-run determinism/byte-identity checks.
"""

from __future__ import annotations

import os
import sys
import tempfile
from typing import Dict, List, Tuple

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_EXAMPLES_DIR = os.path.dirname(os.path.dirname(_HERE))  # .../examples
if _EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, _EXAMPLES_DIR)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from make_poster_figures import (  # noqa: E402
    Theme,
    figure,
    make_figure,
    prov,
    save_figure,
    type_pt,
)

from p53_mdm2.maboss import run_maboss  # noqa: E402

# ---------------------------------------------------------------------------
# Fixed facts about this tile's data
# ---------------------------------------------------------------------------
VARIANT = "W23A"
NODES = ["p53", "p53_h", "Mdm2C", "Mdm2N", "Dam"]  # row order, top to bottom
N_FRAMES = 500

# Probed 2026-08-21 on the committed W23A model (README.md "mod-state").
# Asserted, not adjusted to -- a mismatch here means the model changed or the
# run is not actually deterministic, and either matters more than this figure.
EXPECTED_SEGMENTS: List[Tuple[int, str]] = [
    (11, "Mdm2N -- Dam"),
    (29, "Dam"),
    (34, "p53_h -- p53 -- Mdm2C -- Dam"),
    (426, "p53_h -- p53 -- Mdm2C"),
]
EXPECTED_ON_COUNTS: Dict[str, int] = {
    "p53": 460, "p53_h": 460, "Mdm2C": 460, "Mdm2N": 11, "Dam": 74,
}
# Sanity cross-check only -- NOT asserted equal to the modal ON fraction
# (460/500 = 0.920): these are different statistics (time-average of a
# continuous probability vs. the modal-state ON fraction) that merely happen
# to be in the same neighbourhood.
RECORDED_P53_TIME_AVG = 0.861

# Modal-state OCCUPANCY (how much of the ensemble the "winning" state
# actually carries at each frame) -- probed on the same run, on the same
# committed model, same seed. This is what the adversarial review found
# missing from the first version of this figure: the raster's on/off
# pattern was honest, but drawing every ON cell in flat full-strength ink
# implied the modal state was near-certain everywhere, which it is not.
EXPECTED_OCC_MIN = 0.283363
EXPECTED_OCC_MIN_FRAME = 39
EXPECTED_OCC_MAX = 0.882683
EXPECTED_OCC_MAX_FRAME = 252
EXPECTED_OCC_MEAN = 0.751071258
EXPECTED_OCC_MEDIAN = 0.835438
EXPECTED_FRAMES_BELOW_HALF = 86

# ON-cell ink tone floor: an ON cell's tone is linearly mapped from that
# frame's modal-state occupancy over the run's own measured [occ_min,
# occ_max] range onto [TONE_FLOOR, 1.0] (1.0 == full ink). The floor exists
# so that even the least-certain ON cell in this run (occupancy 0.283363)
# is unmistakably darker than an OFF cell -- see _tone_luminance_margin()
# and gate 3 below, which measure that separation rather than assuming it.
TONE_FLOOR = 0.35


def _state_on_set(label: str) -> set:
    """Parse a MaBoSS state label (' -- '-joined ON node names) into a set.

    The empty/all-OFF state comes back as ``''`` (or occasionally ``<nil>``
    depending on pyMaBoSS version) -- either way, no ' -- '-joined token
    survives a split, so the returned set is empty either way for any label
    that is not a genuine node name list.
    """
    if not label or label in ("<nil>", "nil"):
        return set()
    return {tok.strip() for tok in label.split("--")}


def run_modal_states(variant: str = VARIANT):
    """Run the committed MaBoSS model for *variant* and derive the modal
    (argmax-occupancy) network state per frame -- an argmax over discrete
    network-state occupancy, never a threshold on a continuous probability.

    Returns:
        modal_labels: list[str], length 500 -- the argmax-occupancy network
            state label at each frame.
        modal_occ: list[float], length 500 -- that same state's own
            occupancy fraction at each frame (i.e. ``states_df.max(axis=1)``,
            the numerator of the argmax) -- how much of the ensemble the
            "winning" state actually carries, NOT a per-node probability.
        matrix: np.ndarray, shape (5, 500), dtype uint8 -- matrix[i, f] == 1
            iff NODES[i] is ON in modal_labels[f].
        p53_time_avg: float -- get_nodes_probtraj()'s time-average P(p53 up)
            (continuous; recorded for the cross-check only).
        info: dict -- provenance (model paths, backend, engine version, seed).
    """
    binary = run_maboss.ensure_backend()
    import maboss  # imported only after ensure_backend() -- see its docstring

    bnd, cfg = run_maboss.variant_model_paths(variant)
    for p in (bnd, cfg):
        if not os.path.isfile(p):
            raise FileNotFoundError(f"MaBoSS model file missing: {p}")

    tmp = tempfile.mkdtemp(prefix="fig_mod_state_")
    b = os.path.join(tmp, "model.bnd")
    c = os.path.join(tmp, "model.cfg")
    run_maboss._sanitise_to_utf8(bnd, b)
    run_maboss._sanitise_to_utf8(cfg, c)

    sim = maboss.load(b, c)          # external MaBoSS binary, not cmaboss
    result = sim.run()

    states_df = result.get_states_probtraj()  # occupancy per network state
    modal_labels = [str(x) for x in states_df.idxmax(axis=1).tolist()]
    modal_occ = [float(x) for x in states_df.max(axis=1).tolist()]

    nodes_df = result.get_nodes_probtraj()     # continuous P(node up)
    p53_time_avg = float(nodes_df["p53"].mean())

    matrix = np.zeros((len(NODES), len(modal_labels)), dtype=np.uint8)
    for f, label in enumerate(modal_labels):
        on = _state_on_set(label)
        for i, node in enumerate(NODES):
            if node in on:
                matrix[i, f] = 1

    info = {
        "variant": variant,
        "bnd": bnd,
        "cfg": cfg,
        "backend": "MaBoSS (external binary, colomoto)",
        "binary": binary,
        "engine_version": run_maboss.maboss_version(),
        "seed": 100,
        "thread_count": 1,
        "derivation": "argmax over get_states_probtraj() network-state "
                       "occupancy per frame -- not a threshold",
    }
    return modal_labels, modal_occ, matrix, p53_time_avg, info


def _segments(labels: List[str]) -> List[Tuple[int, str]]:
    """Run-length encode a label sequence into (run_length, label) pairs."""
    segs: List[Tuple[int, str]] = []
    cur = None
    n = 0
    for v in labels:
        if v == cur:
            n += 1
        else:
            if cur is not None:
                segs.append((n, cur))
            cur = v
            n = 1
    if cur is not None:
        segs.append((n, cur))
    return segs


def _check_expected(modal_labels: List[str], matrix: np.ndarray):
    """Assert the run against the probed expectation recorded in README.md.

    Raises AssertionError (with both the observed and expected values) on
    any drift -- per the brief, a mismatch is reported, not silently
    absorbed into the figure.
    """
    segs = _segments(modal_labels)
    if segs != EXPECTED_SEGMENTS:
        raise AssertionError(
            f"modal-state segmentation drift: got {segs!r}, "
            f"expected {EXPECTED_SEGMENTS!r}"
        )
    counts = {node: int(matrix[i].sum()) for i, node in enumerate(NODES)}
    if counts != EXPECTED_ON_COUNTS:
        raise AssertionError(
            f"per-node ON count drift: got {counts!r}, "
            f"expected {EXPECTED_ON_COUNTS!r}"
        )
    return segs, counts


def _check_occupancy(modal_occ: List[float]) -> Dict[str, float]:
    """Assert the modal-state occupancy statistics against the probed
    expectation (README.md / the adversarial-review report) -- same
    drift-reporting philosophy as :func:`_check_expected`: a mismatch here
    means the model or run changed, and that matters more than the figure.
    """
    occ_min = min(modal_occ)
    occ_max = max(modal_occ)
    occ_min_frame = modal_occ.index(occ_min)
    occ_max_frame = modal_occ.index(occ_max)
    mean = sum(modal_occ) / len(modal_occ)
    sorted_occ = sorted(modal_occ)
    n = len(sorted_occ)
    median = (sorted_occ[n // 2] if n % 2 else
              (sorted_occ[n // 2 - 1] + sorted_occ[n // 2]) / 2.0)
    below_half = sum(1 for o in modal_occ if o < 0.5)

    stats = {
        "occ_min": occ_min, "occ_min_frame": occ_min_frame,
        "occ_max": occ_max, "occ_max_frame": occ_max_frame,
        "mean": mean, "median": median, "frames_below_half": below_half,
    }
    checks = [
        (abs(occ_min - EXPECTED_OCC_MIN) < 1e-9, "occ_min", occ_min, EXPECTED_OCC_MIN),
        (occ_min_frame == EXPECTED_OCC_MIN_FRAME, "occ_min_frame", occ_min_frame, EXPECTED_OCC_MIN_FRAME),
        (abs(occ_max - EXPECTED_OCC_MAX) < 1e-9, "occ_max", occ_max, EXPECTED_OCC_MAX),
        (occ_max_frame == EXPECTED_OCC_MAX_FRAME, "occ_max_frame", occ_max_frame, EXPECTED_OCC_MAX_FRAME),
        (abs(mean - EXPECTED_OCC_MEAN) < 1e-6, "mean", mean, EXPECTED_OCC_MEAN),
        (abs(median - EXPECTED_OCC_MEDIAN) < 1e-6, "median", median, EXPECTED_OCC_MEDIAN),
        (below_half == EXPECTED_FRAMES_BELOW_HALF, "frames_below_half", below_half, EXPECTED_FRAMES_BELOW_HALF),
    ]
    bad = [(name, got, want) for ok, name, got, want in checks if not ok]
    if bad:
        raise AssertionError(f"modal-state occupancy drift: {bad!r}")
    return stats


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _lerp_rgb(a: Tuple[float, float, float], b: Tuple[float, float, float],
              t: float) -> Tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _rgb_luminance(rgb: Tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _tone_fraction(occ: np.ndarray, occ_min: float, occ_max: float) -> np.ndarray:
    """Map occupancy (over the run's own measured [occ_min, occ_max] range,
    NOT the theoretical [0, 1] range -- see the module docstring's "Honesty
    fix" section for why) onto an ink-tone fraction in [TONE_FLOOR, 1.0].
    """
    return TONE_FLOOR + (1.0 - TONE_FLOOR) * (occ - occ_min) / (occ_max - occ_min)


def _build_rgba(matrix: np.ndarray, tone: np.ndarray,
                 field_rgb: Tuple[float, float, float],
                 ink_rgb: Tuple[float, float, float]) -> np.ndarray:
    """Assemble the (rows, cols, 4) RGBA image actually drawn by imshow.

    Factored out of :func:`build_mod_state` so the gate suite can inspect
    exactly the array that gets rendered (not a re-implementation of it) --
    an OFF cell is always exactly ``field_rgb``; an ON cell is ``field_rgb``
    blended toward ``ink_rgb`` by that column's tone fraction. No smoothing
    across columns happens here or in the ``interpolation="nearest"`` imshow
    call that consumes this array -- each column is one flat RGBA value.
    """
    n_rows, n_cols = matrix.shape
    on_color_per_frame = np.array(
        [_lerp_rgb(field_rgb, ink_rgb, float(t)) for t in tone]
    )  # shape (n_cols, 3)
    image = np.empty((n_rows, n_cols, 3), dtype=np.float64)
    image[:, :, :] = field_rgb  # default: OFF everywhere
    on_mask = matrix.astype(bool)
    for col in range(n_cols):
        rows_on = on_mask[:, col]
        if rows_on.any():
            image[rows_on, col, :] = on_color_per_frame[col]
    alpha = np.ones((n_rows, n_cols, 1), dtype=np.float64)
    return np.concatenate([image, alpha], axis=2)


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
@figure("mod-state", ext="svg")
def build_mod_state(theme: Theme, out_dir: str) -> str:
    modal_labels, modal_occ, matrix, p53_time_avg, info = run_modal_states(VARIANT)
    segs, counts = _check_expected(modal_labels, matrix)
    occ_stats = _check_occupancy(modal_occ)

    if matrix.shape != (len(NODES), N_FRAMES):
        raise AssertionError(f"raster shape {matrix.shape}, want (5, 500)")
    uniq = set(np.unique(matrix).tolist())
    if not uniq <= {0, 1}:
        raise AssertionError(f"on/off pattern not strictly binary: values {uniq}")

    field_rgb = _hex_to_rgb(theme.field)
    ink_rgb = _hex_to_rgb(theme.ink)
    occ_arr = np.asarray(modal_occ, dtype=np.float64)
    tone = _tone_fraction(occ_arr, occ_stats["occ_min"], occ_stats["occ_max"])
    if tone.min() < TONE_FLOOR - 1e-9 or tone.max() > 1.0 + 1e-9:
        raise AssertionError(
            f"tone fraction escaped [{TONE_FLOOR}, 1.0]: "
            f"[{tone.min()!r}, {tone.max()!r}]"
        )

    prov(info["bnd"], note="W23A .bnd model, byte-identical Pipeline-3 emission")
    prov(info["cfg"], note="W23A .cfg (seed_pseudorandom=100, thread_count=1)")
    prov(info["engine_version"], note="external MaBoSS binary, discovered via "
                                       "run_maboss.ensure_backend()")
    prov(segs, note="modal network-state run-length segments; argmax over "
                     "get_states_probtraj() occupancy, not a threshold")
    prov(counts, note="per-node ON frame count under the modal state")
    prov(occ_stats, note="modal-state occupancy stats (get_states_probtraj() "
                         ".max(axis=1)); drives the ON-cell tone mapping")
    prov(TONE_FLOOR, note="ON-cell ink-tone floor; least-certain ON cell "
                          "(occupancy occ_min) renders at this fraction of "
                          "the field->ink blend, most-certain at 1.0")
    prov(p53_time_avg, note="get_nodes_probtraj() time-average P(p53 up); "
                            "sanity cross-check only, distinct statistic from "
                            "the modal-state ON fraction")

    fig, base_ax = make_figure(theme)
    base_ax.set_visible(False)  # only used to get a correctly-sized,
                                 # transparent, theme-spined figure

    # Reserve margin for the y category labels (node names) and the x
    # frame axis + its label -- make_figure()'s own axes is full-bleed
    # (0,0,1,1) and has no room for tick labels outside the data area.
    # This rect (left=0.165, bottom=0.33, width=0.79, height=0.63) was
    # sized by actually measuring rendered label bboxes against the
    # 2560x768 px canvas (see the gate-suite comment below) -- not
    # guessed: at 22pt type the y row labels need >=384px on the left,
    # the x ticks+label need >=248px on the bottom, and the rightmost
    # x tick label's own half-width needs >=88px of right-hand clearance
    # past the axes edge, all inside a canvas that is only 768px tall.
    ax = fig.add_axes((0.165, 0.33, 0.79, 0.63))
    ax.patch.set_alpha(0.0)
    for spine in ax.spines.values():
        spine.set_color(theme.rule)
        spine.set_linewidth(1.2)

    # Ink/greyscale only, and honest about confidence: an OFF cell is always
    # exactly `field` (one single colour). An ON cell is `field` blended
    # toward `ink` by that frame's tone fraction -- pale for a barely-
    # majority modal state, full ink only where the ensemble is genuinely
    # settled. No accent, no new hue: both blend endpoints are this tile's
    # existing neutral tokens.
    rgba = _build_rgba(matrix, tone, field_rgb, ink_rgb)

    ax.imshow(
        rgba,
        aspect="auto",
        interpolation="nearest",  # hard steps -- no smoothing/anti-aliasing,
                                  # even though the per-column colour itself
                                  # now varies continuously with occupancy
        origin="upper",
    )

    # Row separators between the five node lanes, greyscale rule colour.
    for i in range(len(NODES) + 1):
        ax.axhline(i - 0.5, color=theme.rule, linewidth=0.8, zorder=3)

    ax.set_yticks(range(len(NODES)))
    ax.set_yticklabels(NODES, fontsize=type_pt(22), color=theme.ink)
    ax.tick_params(axis="y", length=0, colors=theme.rule)

    ax.set_xlim(-0.5, N_FRAMES - 0.5)
    ax.set_xticks([0, 250, N_FRAMES - 1])
    ax.set_xticklabels(["0", "250", str(N_FRAMES - 1)],
                        fontsize=type_pt(22), color=theme.ink)
    ax.tick_params(axis="x", colors=theme.rule)
    ax.set_xlabel("frame", fontsize=type_pt(22), color=theme.ink, labelpad=8)

    _assert_no_label_clipping(fig, ax)

    out_path = os.path.join(out_dir, "mod-state.svg")
    save_figure(fig, out_path, ext="svg")
    return out_path


def _assert_no_label_clipping(fig, ax) -> Dict[str, float]:
    """Measure the rendered bbox of every axis label/tick against the
    figure's own pixel canvas and raise if any of them falls outside it.

    22pt type is large relative to this tile's 768px-tall canvas, so the
    margins in :func:`build_mod_state` were sized by measurement, not by
    guessing -- this re-runs that same measurement on every build (not
    just at design time) so a future edit that shrinks the axes rect (or
    a matplotlib/font change that widens glyphs) fails loudly here rather
    than shipping a poster tile with a clipped "frame" label or tick.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_w_px, fig_h_px = fig.get_size_inches() * fig.dpi

    x_bbox = ax.xaxis.get_tightbbox(renderer)
    y_bbox = ax.yaxis.get_tightbbox(renderer)
    last_xtick_bbox = ax.get_xticklabels()[-1].get_window_extent(renderer)

    margins = {
        "bottom_clearance_px": x_bbox.y0,             # must be >= 0
        "left_clearance_px": y_bbox.x0,                # must be >= 0
        "right_clearance_px": fig_w_px - last_xtick_bbox.x1,  # must be >= 0
        "top_clearance_px": fig_h_px - ax.get_window_extent(renderer).y1,
    }
    bad = {k: v for k, v in margins.items() if v < 0}
    if bad:
        raise AssertionError(
            f"axis label(s) clipped by the canvas edge: {bad} "
            f"(figure is {fig_w_px:.0f}x{fig_h_px:.0f}px); widen the "
            f"reserved margin in build_mod_state()'s add_axes rect"
        )
    return margins


# ---------------------------------------------------------------------------
# Standalone gate suite -- run with:
#   PYTHONPATH=<OpenUSD lib/python>:<repo>/examples <forOUSD python> \
#       examples/p53_mdm2/figures/fig_mod_state.py
# ---------------------------------------------------------------------------
def _run_gates() -> bool:
    import hashlib
    import re

    from make_poster_figures import resolve_theme

    ok = True
    theme = resolve_theme("slate")
    field_rgb = _hex_to_rgb(theme.field)
    ink_rgb = _hex_to_rgb(theme.ink)

    print("=== gate 1: segment table + per-node ON counts (asserted) ===")
    modal_labels, modal_occ, matrix, p53_time_avg, info = run_modal_states(VARIANT)
    try:
        segs, counts = _check_expected(modal_labels, matrix)
        for n, s in segs:
            print(f"  {n:>4}  {s!r}")
        print(f"  per-node ON counts: {counts}")
        print("  OK: matches the recorded 2026-08-21 probe exactly")
    except AssertionError as exc:
        print(f"  FAIL: {exc}", file=sys.stderr)
        ok = False

    print("\n=== gate 1b: modal-state occupancy stats (asserted) ===")
    try:
        occ_stats = _check_occupancy(modal_occ)
        print(f"  min {occ_stats['occ_min']:.6f} (frame {occ_stats['occ_min_frame']})   "
              f"max {occ_stats['occ_max']:.6f} (frame {occ_stats['occ_max_frame']})   "
              f"mean {occ_stats['mean']:.6f}   median {occ_stats['median']:.6f}")
        print(f"  frames with occupancy < 0.5: {occ_stats['frames_below_half']} "
              f"of {len(modal_occ)} ({100 * occ_stats['frames_below_half'] / len(modal_occ):.1f}%)")
        print("  OK: matches the recorded adversarial-review probe exactly")
    except AssertionError as exc:
        print(f"  FAIL: {exc}", file=sys.stderr)
        ok = False
        occ_stats = None

    print("\n=== gate 2: determinism across two independent runs (seed=100) ===")
    modal_labels_b, modal_occ_b, matrix_b, _, _ = run_modal_states(VARIANT)
    if (modal_labels == modal_labels_b and np.array_equal(matrix, matrix_b)
            and modal_occ == modal_occ_b):
        print("  OK: identical modal-state sequence, occupancy, and derived "
              "matrix on rerun")
    else:
        print("  FAIL: rerun produced a different modal-state sequence/"
              "occupancy/matrix", file=sys.stderr)
        ok = False

    print("\n=== gate 3: ON tones fall inside the intended band; OFF is one "
          "distinct value ===")
    occ_arr = np.asarray(modal_occ, dtype=np.float64)
    tone = _tone_fraction(occ_arr, occ_stats["occ_min"], occ_stats["occ_max"])
    rgba = _build_rgba(matrix, tone, field_rgb, ink_rgb)
    on_mask = matrix.astype(bool)
    off_pixels = rgba[~on_mask][:, :3]
    on_pixels = rgba[on_mask][:, :3]
    off_unique = np.unique(off_pixels, axis=0)
    tone_min, tone_max = float(tone.min()), float(tone.max())
    print(f"  occupancy range measured: [{occ_stats['occ_min']:.6f}, "
          f"{occ_stats['occ_max']:.6f}]")
    print(f"  tone range mapped to:     [{tone_min:.6f}, {tone_max:.6f}]  "
          f"(TONE_FLOOR={TONE_FLOOR}, 1.0=full ink)")
    print(f"  distinct OFF colours in the rendered array: {len(off_unique)}")
    tone_ok = (abs(tone_min - TONE_FLOOR) < 1e-9 and abs(tone_max - 1.0) < 1e-9
               and tone.min() >= TONE_FLOOR - 1e-9 and tone.max() <= 1.0 + 1e-9)
    off_ok = (len(off_unique) == 1
              and np.allclose(off_unique[0], np.array(field_rgb), atol=1e-12))
    # every ON pixel's colour must actually be reachable by the field->ink
    # blend at *some* tone in [TONE_FLOOR, 1.0] -- i.e. never paler than the
    # floor and never past full ink.
    field_arr, ink_arr = np.array(field_rgb), np.array(ink_rgb)
    denom = ink_arr - field_arr
    denom_safe = np.where(denom == 0, 1.0, denom)
    implied_tone = (on_pixels - field_arr) / denom_safe
    on_in_band = bool(np.all(implied_tone >= TONE_FLOOR - 1e-6) and
                       np.all(implied_tone <= 1.0 + 1e-6))
    if tone_ok and off_ok and on_in_band:
        print(f"  OK: {len(on_pixels)} ON pixels all reconstruct to a tone in "
              f"[{TONE_FLOOR}, 1.0]; {len(off_pixels)} OFF pixels are all "
              f"exactly `field` ({theme.field})")
    else:
        print(f"  FAIL: tone_ok={tone_ok} off_ok={off_ok} on_in_band={on_in_band}",
              file=sys.stderr)
        ok = False

    print("\n=== gate 3b: least-certain ON cell is unmistakably darker than "
          "OFF (luminance margin) ===")
    palest_on_rgb = _lerp_rgb(field_rgb, ink_rgb, TONE_FLOOR)
    Y_field = _rgb_luminance(field_rgb)
    Y_ink = _rgb_luminance(ink_rgb)
    Y_palest_on = _rgb_luminance(palest_on_rgb)
    margin = Y_field - Y_palest_on
    MARGIN_THRESHOLD = 0.2
    print(f"  field Y={Y_field:.4f}   palest-ON (tone={TONE_FLOOR}) "
          f"Y={Y_palest_on:.4f}   full-ink Y={Y_ink:.4f}")
    print(f"  luminance margin (field - palest_on) = {margin:.4f}   "
          f"(threshold: > {MARGIN_THRESHOLD})")
    if margin > MARGIN_THRESHOLD:
        print("  OK: in greyscale (luminance alone), the palest possible ON "
              "cell is still clearly separated from OFF -- never confusable")
    else:
        print(f"  FAIL: margin {margin:.4f} <= threshold {MARGIN_THRESHOLD}",
              file=sys.stderr)
        ok = False

    print("\n=== gate 4: exactly 5 rows x 500 columns ===")
    if matrix.shape == (5, 500):
        print(f"  OK: shape = {matrix.shape}")
    else:
        print(f"  FAIL: shape = {matrix.shape}, want (5, 500)", file=sys.stderr)
        ok = False

    print("\n=== gate 4b: no axis label/tick is clipped by the canvas edge ===")
    # build_mod_state() itself calls _assert_no_label_clipping() and would
    # raise before returning if anything were clipped; this just makes the
    # measured clearances visible in the gate output.
    tmp = tempfile.mkdtemp(prefix="fig_mod_state_gates_")
    out0 = build_mod_state(theme, tmp)
    print(f"  OK: figure built without raising (clearances measured and "
          f"enforced inside build_mod_state -> _assert_no_label_clipping)")
    os.remove(out0)

    print("\n=== gate 5+6: build the figure twice, check text floor + byte-identity ===")
    svg_paths = []
    for i in range(2):
        out = build_mod_state(theme, tmp)
        final = os.path.join(tmp, f"run{i}.svg")
        os.replace(out, final)
        svg_paths.append(final)
    with open(svg_paths[0], "rb") as fh:
        svg_a = fh.read()
    with open(svg_paths[1], "rb") as fh:
        svg_b = fh.read()
    # gate 5: every declared text size in this module goes through type_pt(),
    # which raises ValueError below MIN_TYPE_PT -- so a successful build
    # above is itself the gate-5 evidence. Re-assert the floor explicitly:
    if type_pt(22) >= 22:
        print("  OK: every text object in this figure is sized via type_pt() "
              "(22pt node labels, tick labels, and x-axis label) -- floor "
              "enforced in code")
    else:
        ok = False
    if svg_a == svg_b:
        print(f"  OK: byte-identical SVG across two builds "
              f"(sha256={hashlib.sha256(svg_a).hexdigest()})")
    else:
        print("  FAIL: two builds of mod-state.svg are not byte-identical",
              file=sys.stderr)
        ok = False

    print("\n=== gate 7: canvas size 214.94 x 64.482 mm, transparent background ===")
    text = svg_a.decode("utf-8", errors="replace")
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)pt"[^>]*\bheight="([\d.]+)pt"', text)
    if m is None:
        m = re.search(r'<svg[^>]*\bheight="([\d.]+)pt"[^>]*\bwidth="([\d.]+)pt"', text)
        if m:
            height_pt, width_pt = float(m.group(1)), float(m.group(2))
        else:
            width_pt = height_pt = None
    else:
        width_pt, height_pt = float(m.group(1)), float(m.group(2))
    if width_pt is not None:
        width_mm = width_pt * 25.4 / 72.0
        height_mm = height_pt * 25.4 / 72.0
        print(f"  measured: {width_mm:.3f} x {height_mm:.3f} mm "
              f"(from SVG width/height in pt)")
        if abs(width_mm - 214.94) < 0.01 and abs(height_mm - 64.482) < 0.01:
            print("  OK: matches the 214.94 x 64.482 mm contract")
        else:
            print("  FAIL: canvas size does not match the contract", file=sys.stderr)
            ok = False
    else:
        print("  FAIL: could not parse width/height out of the SVG header",
              file=sys.stderr)
        ok = False
    # Transparent background: matplotlib with patch alpha 0 + transparent=True
    # omits an opaque full-canvas background rect entirely.
    has_opaque_bg_rect = re.search(
        r'<rect[^>]*style="fill:#[0-9a-fA-F]{6};"[^>]*/>', text[:2000]
    )
    if not has_opaque_bg_rect:
        print("  OK: no opaque full-canvas background rect in the SVG header")
    else:
        print("  FAIL: an opaque background rect was found near the SVG root",
              file=sys.stderr)
        ok = False

    print("\n=== gate 8: greyscale readability (colour removed), full ink vs "
          "field ===")
    contrast = abs(Y_ink - Y_field)
    print(f"  theme={theme.name}  ink={theme.ink} (Y={Y_ink:.3f})  "
          f"field={theme.field} (Y={Y_field:.3f})  |dY|={contrast:.3f}")
    if contrast > 0.3:
        print("  OK: on/off is encoded purely by luminance (no hue used for "
              "the distinction), readable with all colour removed -- and "
              "gate 3b above already confirmed the palest ON tone alone "
              "still clears OFF by a comfortable margin")
    else:
        print("  FAIL: insufficient luminance contrast between ink and field",
              file=sys.stderr)
        ok = False

    print("\n=== gate 9: provenance ===")
    print(f"  model files: {info['bnd']}")
    print(f"               {info['cfg']}")
    print(f"  backend: {info['backend']}")
    print(f"  MaBoSS binary: {info['binary']}")
    print(f"  MaBoSS version: {info['engine_version']}")
    print(f"  seed_pseudorandom: {info['seed']}  thread_count: {info['thread_count']}")
    print(f"  derivation: {info['derivation']}")
    print(f"  tone mapping: field->ink blend, tone_fraction(occ) = "
          f"{TONE_FLOOR} + {1 - TONE_FLOOR} * (occ - occ_min) / "
          f"(occ_max - occ_min), NOT a threshold -- occupancy is itself an "
          f"argmax over network-state occupancy, and its magnitude then "
          f"linearly sets ink tone")
    print(f"  cross-check: get_nodes_probtraj() time-average P(p53 up) = "
          f"{p53_time_avg:.6f}  (recorded W23A value: {RECORDED_P53_TIME_AVG}; "
          f"modal-state p53 ON fraction = {counts['p53']}/500 = "
          f"{counts['p53'] / 500:.3f} -- a related but distinct statistic, "
          f"not asserted equal)")

    return ok


if __name__ == "__main__":
    sys.exit(0 if _run_gates() else 1)
