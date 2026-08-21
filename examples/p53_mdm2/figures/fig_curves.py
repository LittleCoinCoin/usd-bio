#!/usr/bin/env python3
"""
fig_curves.py -- "fig-curves": P(p53 up) over 500 frames, WildType vs W23A.

Reads ``bio:maboss:prob:p53`` timeSamples straight from the committed
Analysis layer (``examples/p53_mdm2/analysis/p53_mdm2_analysis.usda``) via
the USD API -- never hardcoded, never re-derived from a cached array. Only
the ``WildType`` and ``W23A`` variant scopes under
``/p53_MDM2_complex/maboss/<Variant>`` are ever touched; ``F19A`` and
``L26A`` are not part of this figure and this module never opens their
paths.

Cross-check (the one that must halt the run)
---------------------------------------------
Each series' 500 timeSamples are averaged and compared against the
independently-computed ``bio:maboss:p53TimeAverage`` scalar stored on the
corresponding variant Scope in
``examples/p53_mdm2/demos/p53_mdm2_integrated.usda``. If the two disagree
beyond float tolerance, this module raises ``AssertionError`` rather than
drawing a figure from numbers that don't reconcile -- per the job brief,
three other poster claims have already been corrected exactly this way, so
a fourth silent mismatch here is not an acceptable outcome.

The ``31 %`` / ``86 %`` direct curve labels are never typed as literals --
they are ``round(recomputed_mean * 100)`` for each series, so a future
change to the underlying MaBoSS run would change the printed numbers along
with the plotted curves instead of leaving a stale label behind.

Accent discipline
------------------
The single accent colour (``theme.accent``, resolved from ``themes.json`` --
never hardcoded) marks W23A and nothing else, and is passed straight to the
``ax.plot(...)`` / ``ax.text(...)`` calls that draw it -- never applied by
recolouring after the fact. Wild type is always ``theme.ink``. Because a
printed poster can lose that colour distinction entirely, W23A also gets a
heavier stroke than wild type (see ``_LINEWIDTH_WT`` / ``_LINEWIDTH_W23A``
below), so the two curves stay separable in pure greyscale.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

from pxr import Usd

from make_poster_figures import (
    Theme,
    figure,
    make_figure,
    prov,
    save_figure,
    type_pt,
    usd_source,
)

# ---------------------------------------------------------------------------
# Fixed, committed-evidence paths -- resolved from this file's own location
# so the figure runs regardless of the caller's cwd (same convention as
# make_poster_figures.py's own _HERE).
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ANALYSIS_LAYER = os.path.normpath(
    os.path.join(_HERE, "..", "analysis", "p53_mdm2_analysis.usda")
)
_INTEGRATED_LAYER = os.path.normpath(
    os.path.join(_HERE, "..", "demos", "p53_mdm2_integrated.usda")
)

_MABOSS_ROOT = "/p53_MDM2_complex/maboss"
_INTEGRATION_ROOT = "/p53_MDM2_complex/integration"
_PROB_ATTR = "bio:maboss:prob:p53"
_AVG_ATTR = "bio:maboss:p53TimeAverage"
_EXPECTED_FRAME_COUNT = 500

# The figure's contract: exactly these two variants, never F19A or L26A.
_VARIANTS: Tuple[str, str] = ("WildType", "W23A")
assert set(_VARIANTS) == {"WildType", "W23A"}, (
    "fig-curves reads only WildType and W23A -- not the other maboss "
    "variants (F19A, L26A)"
)

# Stored bio:maboss:p53TimeAverage is float32 (USD `float`), and the mean
# recomputed here in python float64 from the same 500 samples agrees with it
# to ~1e-8 in practice (probed 2026-08-21); this tolerance is generous by
# three orders of magnitude and still tight enough to catch a real
# disagreement rather than a storage-precision artifact.
_MEAN_TOLERANCE = 1e-4

# Curve strokes, in points (matplotlib's `linewidth` is already a physical
# point size at this figure's fixed dpi -- see make_poster_figures.make_figure).
# W23A is deliberately ~2.6x heavier than wild type so the two curves stay
# separable with all colour removed (verified in the greyscale gate).
_LINEWIDTH_WT = 1.4
_LINEWIDTH_W23A = 3.6


def _read_prob_series(stage: Usd.Stage, variant: str) -> Tuple[List[int], List[float]]:
    """Read ``bio:maboss:prob:p53`` timeSamples for one maboss variant scope.

    Returns ``(frames, values)`` where ``frames`` is ``[0, 1, ..., 499]``.
    Raises ``AssertionError`` if the series is not exactly the committed
    500-frame, 0..499 shape every maboss variant scope is documented to
    have (README.md, CLAUDE.md).
    """
    prim_path = f"{_MABOSS_ROOT}/{variant}"
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise RuntimeError(f"missing prim {prim_path!r} in {_ANALYSIS_LAYER}")
    attr = prim.GetAttribute(_PROB_ATTR)
    if not attr.IsValid():
        raise RuntimeError(
            f"missing attribute {_PROB_ATTR!r} on {prim_path!r} in {_ANALYSIS_LAYER}"
        )

    time_codes = attr.GetTimeSamples()
    assert len(time_codes) == _EXPECTED_FRAME_COUNT, (
        f"{variant}: expected exactly {_EXPECTED_FRAME_COUNT} timeSamples on "
        f"{prim_path}.{_PROB_ATTR}, got {len(time_codes)}"
    )
    frames = [int(round(t)) for t in time_codes]
    assert frames == list(range(_EXPECTED_FRAME_COUNT)), (
        f"{variant}: timeSamples on {prim_path}.{_PROB_ATTR} are not exactly "
        f"frames 0..{_EXPECTED_FRAME_COUNT - 1}"
    )

    values = [attr.Get(t) for t in time_codes]
    return frames, values


def _find_mean_crossings(frames: List[int], values: List[float], mean: float) -> List[int]:
    """Return every frame at which ``values`` crosses ``mean``.

    A "crossing" is a sign change of ``value - mean`` between two
    consecutive frames; the reported frame is whichever of the two
    straddling frames has the value closer to ``mean`` (an exact `0`
    difference at a sample is reported directly). Frames are returned in
    ascending order, so ``result[-1]`` is the LAST time the series is at
    its own mean and ``result[0]`` is the first.

    Used to place each curve's direct label where the curve's value
    actually equals the number being printed, instead of at the curve's
    endpoint (which, for a non-monotonic series, can be arbitrarily far
    from the mean -- see the fig-curves adversarial-review fix this
    function exists for).
    """
    diffs = [v - mean for v in values]
    crossings: List[int] = []
    for i in range(len(diffs) - 1):
        a, b = diffs[i], diffs[i + 1]
        if a == 0:
            crossings.append(frames[i])
        elif (a < 0) != (b < 0):
            crossings.append(frames[i] if abs(a) <= abs(b) else frames[i + 1])
    return crossings


def _pt_to_data_span(size_pt: float, ax, axis: str) -> float:
    """Convert a physical point size to a span in data units along `axis`.

    Same conversion as ``make_poster_figures.pt_to_data``, but without that
    function's 22pt text-floor check -- this is used for a line's stroke
    half-width, not a text size, so the floor does not apply.
    """
    fig = ax.figure
    inches = size_pt / 72.0
    px = inches * fig.dpi
    inv = ax.transData.inverted()
    if axis == "y":
        (_, y0), (_, y1) = inv.transform((0, 0)), inv.transform((0, px))
        return abs(y1 - y0)
    (x0, _), (x1, _) = inv.transform((0, 0)), inv.transform((px, 0))
    return abs(x1 - x0)


def _stored_time_average(stage: Usd.Stage, variant: str) -> float:
    """Read the independently-computed ``bio:maboss:p53TimeAverage`` scalar
    for one variant, from the integrated demo layer (not the analysis layer
    the timeSamples themselves come from)."""
    prim_path = f"{_INTEGRATION_ROOT}/{variant}"
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise RuntimeError(f"missing prim {prim_path!r} in {_INTEGRATED_LAYER}")
    attr = prim.GetAttribute(_AVG_ATTR)
    if not attr.IsValid():
        raise RuntimeError(
            f"missing attribute {_AVG_ATTR!r} on {prim_path!r} in {_INTEGRATED_LAYER}"
        )
    return attr.Get()


@figure("fig-curves", ext="svg")
def build_fig_curves(theme: Theme, out_dir: str) -> str:
    analysis_stage = Usd.Stage.Open(_ANALYSIS_LAYER)
    if analysis_stage is None:
        raise RuntimeError(f"could not open {_ANALYSIS_LAYER}")
    integrated_stage = Usd.Stage.Open(_INTEGRATED_LAYER)
    if integrated_stage is None:
        raise RuntimeError(f"could not open {_INTEGRATED_LAYER}")

    series: Dict[str, Tuple[List[int], List[float]]] = {}
    recomputed_means: Dict[str, float] = {}
    stored_averages: Dict[str, float] = {}

    for variant in _VARIANTS:
        frames, values = _read_prob_series(analysis_stage, variant)
        series[variant] = (frames, values)
        prov(
            len(values),
            usd_source(_ANALYSIS_LAYER, f"{_MABOSS_ROOT}/{variant}", _PROB_ATTR),
            note=f"{variant}: sample count (must be {_EXPECTED_FRAME_COUNT})",
        )

        computed_mean = sum(values) / len(values)
        stored_avg = _stored_time_average(integrated_stage, variant)
        recomputed_means[variant] = computed_mean
        stored_averages[variant] = stored_avg

        prov(
            computed_mean,
            usd_source(_ANALYSIS_LAYER, f"{_MABOSS_ROOT}/{variant}", _PROB_ATTR),
            note=f"{variant}: mean of the {_EXPECTED_FRAME_COUNT} timeSamples above",
        )
        prov(
            stored_avg,
            usd_source(_INTEGRATED_LAYER, f"{_INTEGRATION_ROOT}/{variant}", _AVG_ATTR),
            note=f"{variant}: independently-stored time average (cross-check target)",
        )

        diff = abs(computed_mean - stored_avg)
        print(
            f"[fig-curves] {variant}: recomputed_mean={computed_mean!r} "
            f"stored_p53TimeAverage={stored_avg!r} |diff|={diff:.3e} "
            f"(tolerance={_MEAN_TOLERANCE:.0e})"
        )
        if diff > _MEAN_TOLERANCE:
            raise AssertionError(
                f"fig-curves cross-check FAILED for {variant}: recomputed mean of "
                f"the {_EXPECTED_FRAME_COUNT} {_PROB_ATTR} timeSamples in "
                f"{_ANALYSIS_LAYER} is {computed_mean!r}, which disagrees with the "
                f"stored {_AVG_ATTR}={stored_avg!r} in {_INTEGRATED_LAYER} by "
                f"{diff!r} (> tolerance {_MEAN_TOLERANCE!r}). Per the job brief: "
                f"stop and report this disagreement rather than adjusting the "
                f"figure to match either number."
            )

    # The printed direct-curve labels are rounded from the *recomputed* means,
    # never typed as separate display literals.
    display_pct: Dict[str, int] = {
        variant: round(recomputed_means[variant] * 100) for variant in _VARIANTS
    }
    for variant in _VARIANTS:
        prov(
            display_pct[variant],
            note=f"{variant}: round(recomputed mean * 100) -- the direct curve label",
        )

    fig, ax = make_figure(theme=theme)

    # Physical layout, in figure-fraction coordinates. The canvas is only
    # 64.48mm tall, so a conventional ROTATED y-axis label at the 22pt floor
    # does not fit -- a 90-degree-rotated "P(p53 up) (%)" at 22pt needs
    # about as much vertical run as the entire canvas height (measured by
    # rendering it and checking the text's window extent: it overflowed
    # both the top and bottom of the figure). The y quantity is labelled
    # instead as a horizontal line of text above the plot (see
    # ``ax.text(..., transform=ax.transAxes)`` below), which only costs one
    # text-row of height, not the label's full string width. Bottom margin
    # is sized for one tick-label row plus one x-axis-label row, also
    # verified against overflow by rendering.
    left, bottom, width, height = 0.145, 0.40, 0.72, 0.38
    ax.set_position((left, bottom, width, height))

    wt_frames, wt_vals = series["WildType"]
    w23a_frames, w23a_vals = series["W23A"]
    wt_pct_series = [v * 100.0 for v in wt_vals]
    w23a_pct_series = [v * 100.0 for v in w23a_vals]

    # Wild type: ink, light stroke. W23A: accent (from the resolved theme,
    # never a literal hex), heavy stroke. Colour is passed directly to the
    # plotting call -- nothing is recoloured afterward.
    ax.plot(
        wt_frames, wt_pct_series,
        color=theme.ink, linewidth=_LINEWIDTH_WT,
        solid_joinstyle="round", solid_capstyle="round",
        zorder=2,
    )
    ax.plot(
        w23a_frames, w23a_pct_series,
        color=theme.accent, linewidth=_LINEWIDTH_W23A,
        solid_joinstyle="round", solid_capstyle="round",
        zorder=3,
    )

    last_frame = wt_frames[-1]
    ax.set_xlim(-8, last_frame + 20)
    ax.set_ylim(-4, 104)
    ax.set_xticks([0, last_frame // 2, last_frame])
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0", "50", "100"])

    tick_size = type_pt(22)
    ax.tick_params(
        axis="both", labelsize=tick_size, colors=theme.ink_soft,
        length=5, width=1.1,
    )
    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    for spine_name in ("left", "bottom"):
        ax.spines[spine_name].set_color(theme.rule)
        ax.spines[spine_name].set_linewidth(1.1)

    ax.set_xlabel(
        "time (frames)", fontsize=type_pt(22), color=theme.ink, labelpad=6,
    )
    # y quantity + unit as a horizontal line above the plot rather than a
    # rotated ylabel -- see the layout comment above ax.set_position().
    ax.text(
        0.0, 1.14, "P(p53 up) (%)",
        transform=ax.transAxes, fontsize=type_pt(22), color=theme.ink,
        ha="left", va="bottom", clip_on=False,
    )

    # ------------------------------------------------------------------
    # Direct labels -- adjacent to each curve, positioned where the curve's
    # value actually EQUALS the printed number (its own time-average), not
    # at the curve's endpoint. An earlier version of this figure labelled
    # both curves at frame 499 (the right-hand end). W23A ends near its
    # mean (84% vs a labelled 86%, 2.3pp off) but WildType does not (7% vs
    # a labelled 31%, 24pp off) -- an end-of-line label reads as an
    # endpoint value, so that placement silently overstated WildType's
    # steady-state level by a factor of ~4.4, and asymmetrically: the
    # near-honest W23A label calibrated the eye to read the WildType one
    # the same wrong way. Both series do cross their own recomputed mean
    # inside the plotted range (never hardcoded -- see
    # ``_find_mean_crossings``); each label is placed at the LATER such
    # crossing, with a small rightward nudge so the text starts just clear
    # of the line stroke rather than sitting on top of it, falling back to
    # the earlier crossing if the later one turns out to collide with
    # something once actually rendered.
    # ------------------------------------------------------------------
    mean_crossings: Dict[str, List[int]] = {}
    for variant in _VARIANTS:
        frames, values = series[variant]
        crossings = _find_mean_crossings(frames, values, recomputed_means[variant])
        if not crossings:
            # Not observed in this data (both series do cross their own
            # mean), but keep a well-defined fallback rather than raising:
            # the single frame whose value is nearest the mean.
            nearest = min(range(len(frames)), key=lambda i: abs(values[i] - recomputed_means[variant]))
            crossings = [frames[nearest]]
        mean_crossings[variant] = crossings
        prov(
            crossings,
            note=f"{variant}: frame(s) where the curve crosses its own recomputed "
            f"mean (label is placed at the later one)",
        )
        print(f"[fig-curves] {variant}: mean-crossing frames={crossings}")

    # At the 22pt floor, a label's rendered text is tall relative to this
    # figure's y-range -- an analytic "how much room is there" estimate
    # turned out to understate how close a curve stays to its own mean
    # crossing (a hairline collision showed up against the label's OWN
    # curve when checked). Rather than refine that estimate further, this
    # places each label empirically: draw it, measure its ACTUAL rendered
    # bounding box with the real renderer and real font metrics, check that
    # box in data space against every sampled point of both curves (padded
    # by each curve's own stroke half-width), and nudge it further away and
    # re-measure if it doesn't clear -- so "does it collide" is answered by
    # rendering, not by a formula.
    label_x_gap_frames = 14
    ink_halfwidth_pct = 0.5 * _pt_to_data_span(_LINEWIDTH_WT, ax, axis="y")
    accent_halfwidth_pct = 0.5 * _pt_to_data_span(_LINEWIDTH_W23A, ax, axis="y")
    curve_halfwidth_pct = {"WildType": ink_halfwidth_pct, "W23A": accent_halfwidth_pct}
    visual_gap_pct = 1.5

    def _other_variant(variant: str) -> str:
        return _VARIANTS[1] if variant == _VARIANTS[0] else _VARIANTS[0]

    def _bbox_to_data_rect(artist):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox = artist.get_window_extent(renderer=renderer)
        inv = ax.transData.inverted()
        (dx0, dy0) = inv.transform((bbox.x0, bbox.y0))
        (dx1, dy1) = inv.transform((bbox.x1, bbox.y1))
        return min(dx0, dx1), max(dx0, dx1), min(dy0, dy1), max(dy0, dy1)

    def _rect_hits_curve(which: str, x0: float, x1: float, y0: float, y1: float) -> bool:
        pad = curve_halfwidth_pct[which]
        c_frames, c_values = series[which]
        for f, v in zip(c_frames, c_values):
            if x0 <= f <= x1 and (y0 - pad) <= v * 100.0 <= (y1 + pad):
                return True
        return False

    # The label must stay within the plotted quantity's own range -- letting
    # it wander into the (-4, 104) padding ax.set_ylim() carries for visual
    # breathing room would mean straddling or crossing the axis spine
    # (drawn at the ylim edges), which the brief explicitly rules out
    # ("keep them clear of the axis").
    _label_y_bounds = (0.0, 100.0)

    def _try_side(variant: str, other: str, x: float, own_pct: float, va: str, max_iterations: int):
        """Attempt to settle a label on one side (va='bottom' places the
        text above the anchor value, va='top' places it below), nudging
        further away each iteration it still overlaps a curve. Returns
        ``(artist, y, iterations_used)`` on success, else ``None`` (and
        removes the artist it created)."""
        pad0 = curve_halfwidth_pct[variant] + visual_gap_pct
        y = own_pct + pad0 if va == "bottom" else own_pct - pad0
        color = theme.ink if variant == "WildType" else theme.accent
        weight = "normal" if variant == "WildType" else "bold"
        artist = ax.text(
            x, y, f"{display_pct[variant]} %",
            color=color, fontsize=type_pt(24), fontweight=weight,
            va=va, ha="left", clip_on=False,
        )
        for iteration in range(max_iterations):
            x0, x1, y0, y1 = _bbox_to_data_rect(artist)
            out_of_bounds = y0 < _label_y_bounds[0] or y1 > _label_y_bounds[1]
            hit_other = _rect_hits_curve(other, x0, x1, y0, y1)
            hit_own = _rect_hits_curve(variant, x0, x1, y0, y1)
            print(
                f"[fig-curves] {variant} frame_x={x:.0f} va={va!r} iter={iteration}: "
                f"bbox_data=({x0:.1f},{y0:.2f})-({x1:.1f},{y1:.2f}) "
                f"hit_other={hit_other} hit_own={hit_own} out_of_bounds={out_of_bounds}"
            )
            if out_of_bounds:
                artist.remove()
                return None
            if not (hit_other or hit_own):
                return artist, y, iteration
            step = 0.35 * (y1 - y0)
            y += -step if va == "top" else step
            artist.set_position((x, y))
        artist.remove()
        return None

    def _place_and_settle(variant: str, frame: int, max_iterations: int = 12):
        """Draw `variant`'s label at `frame`, trying both sides (above and
        below the curve) and keeping whichever one settles clear of both
        curves and the axis range using the fewest nudges -- i.e. the side
        with genuinely more room, rather than a guessed direction. Returns
        ``(artist, x, y, va)`` or ``None`` if neither side ever works."""
        frames, values = series[variant]
        idx = frames.index(frame)
        own_pct = values[idx] * 100.0
        x = frame + label_x_gap_frames
        other = _other_variant(variant)

        candidates = []
        for va in ("bottom", "top"):
            result = _try_side(variant, other, x, own_pct, va, max_iterations)
            if result is not None:
                artist, y, iterations = result
                candidates.append((iterations, artist, y, va))

        if not candidates:
            return None
        candidates.sort(key=lambda c: c[0])  # fewest nudges = most natural fit
        _iterations, artist, y, va = candidates[0]
        for _iterations, other_artist, _y, _va in candidates[1:]:
            other_artist.remove()
        return artist, x, y, va

    chosen_frame: Dict[str, int] = {}
    label_artists: List = []
    for variant in _VARIANTS:
        crossings = mean_crossings[variant]
        result = None
        for candidate in (crossings[-1], crossings[0]):
            result = _place_and_settle(variant, candidate)
            if result is not None:
                chosen_frame[variant] = candidate
                if candidate != crossings[-1]:
                    print(
                        f"[fig-curves] {variant}: later crossing frame "
                        f"{crossings[-1]} never cleared both curves within "
                        f"the iteration budget; using the earlier crossing "
                        f"frame {candidate} instead."
                    )
                break
            if candidate == crossings[0] and len(crossings) == 1:
                break  # only one crossing exists; nothing left to try
        if result is None:
            raise AssertionError(
                f"fig-curves: could not find a label position for {variant} that "
                f"clears both curves at either mean-crossing frame "
                f"{crossings} within the iteration budget -- a genuinely "
                f"unworkable layout, per the job brief, is reported rather than "
                f"silently shipped as an endpoint label."
            )
        artist, x, y, va = result
        label_artists.append(artist)
        print(
            f"[fig-curves] {variant}: FINAL label at frame {chosen_frame[variant]}, "
            f"x={x:.0f} y={y:.2f}% va={va!r}"
        )

    # Verify at final print size (real renderer, real font metrics): the two
    # labels neither collide with each other nor run off the canvas.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_w_px, fig_h_px = fig.get_size_inches() * fig.dpi
    bboxes = [a.get_window_extent(renderer=renderer) for a in label_artists]
    mutual_overlap = bboxes[0].overlaps(bboxes[1])
    overflow = [
        (bb.x0 < 0 or bb.x1 > fig_w_px or bb.y0 < 0 or bb.y1 > fig_h_px)
        for bb in bboxes
    ]
    print(
        f"[fig-curves] label collision check: mutual_overlap={mutual_overlap} "
        f"overflow={dict(zip(_VARIANTS, overflow))}"
    )
    if mutual_overlap or any(overflow):
        raise AssertionError(
            "fig-curves: the two direct labels collide with each other or run "
            f"off the canvas at final print size (mutual_overlap={mutual_overlap}, "
            f"overflow={dict(zip(_VARIANTS, overflow))}); the mean-crossing "
            "placement needs a different offset, not a fallback to endpoint labels."
        )

    out_path = os.path.join(out_dir, "fig-curves.svg")
    save_figure(fig, out_path, ext="svg")
    return out_path
