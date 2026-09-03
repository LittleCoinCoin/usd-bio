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

No percentages in this figure (decided after adversarial review)
------------------------------------------------------------------
Two earlier revisions tried to print "31 %" / "86 %" directly on the two
curves -- first at each curve's frame-499 endpoint (wrong: WildType is
non-monotonic and ends far from its own mean), then at the frame each curve
crosses its own time-average (numerically correct, but at the 22pt type
floor the label text is so tall relative to this 64.48mm canvas -- roughly
a fifth of the plot's own height -- that neither placement ever read as
attached to its curve; both labels ended up floating in the middle of the
plot at about the same height). The poster's own tile header already
prints both numbers directly above this plot, colour-coded to match the
curves (`W23A 86 %` in the accent colour, `wild type 31 %` in ink-soft) --
duplicating them here a centimetre away, with unavoidable placement
ambiguity, added nothing the header didn't already do correctly. Decision:
this figure carries no percentage text at all; only the two curves plus the
required axis labels and units.

Cross-check (the one that must halt the run -- now load-bearing)
------------------------------------------------------------------
Each series' 500 timeSamples are averaged and compared against the
independently-computed ``bio:maboss:p53TimeAverage`` scalar stored on the
corresponding variant Scope in
``examples/p53_mdm2/demos/p53_mdm2_integrated.usda``. If the two disagree
beyond float tolerance, this module raises ``AssertionError`` rather than
drawing a figure from numbers that don't reconcile -- per the job brief,
three other poster claims have already been corrected exactly this way, so
a fourth silent mismatch here is not an acceptable outcome.

Now that the percentages live ONLY in the poster's tile header and not in
this figure, this assertion is the only thing standing between a stale
header value and a wrong poster -- there is no second, in-figure copy of
the numbers left to cross-check against. Keep it running on every build.

Accent discipline
------------------
The single accent colour (``theme.accent``, resolved from ``themes.json`` --
never hardcoded) marks W23A and nothing else, and is passed straight to the
``ax.plot(...)`` call that draws it -- never applied by recolouring after
the fact. Wild type is always ``theme.ink``. Because a printed poster can
lose that colour distinction entirely, and colour/stroke-weight are now the
ONLY things distinguishing the two series (no labels to fall back on), W23A
also gets a heavier stroke than wild type (see ``_LINEWIDTH_WT`` /
``_LINEWIDTH_W23A`` below) -- verified in the greyscale gate to keep the two
curves separable with all colour removed.
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
# separable with all colour removed (verified in the greyscale gate) -- the
# ONLY distinguishing cues left now that neither curve carries a label.
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

    # ------------------------------------------------------------------
    # The cross-check that must halt the run. This figure no longer prints
    # either percentage anywhere -- the poster's tile header does that, in
    # colours matched to these same two curves -- so this assertion is now
    # the ONLY thing verifying the header's numbers against the underlying
    # MaBoSS data. It must keep running on every build, unconditionally.
    # ------------------------------------------------------------------
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
                f"figure to match either number. This check is now the ONLY "
                f"thing verifying the poster tile header's printed percentage "
                f"against the underlying MaBoSS data -- do not remove it."
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
    # plotting call -- nothing is recoloured afterward. With no labels left
    # on this figure, this colour/stroke-weight pairing is the ONLY thing
    # distinguishing the two series -- see the greyscale gate.
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

    # Axis labels and units -- the explicit exception the brief carves out
    # (no title, no legend, no caption, but axis labels/units are required).
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

    out_path = os.path.join(out_dir, "fig-curves.svg")
    save_figure(fig, out_path, ext="svg")
    return out_path
