#!/usr/bin/env python3
"""fig_mod_display.py -- the "mod-display" poster tile: the same p53-MDM2
complex in its four switchable display modes, side by side.

Registers "mod-display" with the make_poster_figures harness (see
figures/README.md for the shared six-tile contract). Unlike the matplotlib
tiles, this one is a raster: four independent ``usdrecord`` renders of
``examples/p53_mdm2/demos/p53_mdm2_integrated.usda`` -- one per
``representation`` VariantSet selection -- composited side by side with PIL.

The claim of this tile is "it opens in standard viewers with element colours
inherited from the shared templates". That drives two hard rules:

1.  KEEP the CPK colours. No ``displayColor`` override is authored anywhere
    in this file and no accent hex appears -- this is the one deliberately
    polychrome poster tile (see figures/README.md "Accent"). Colour comes
    entirely from each atom's own inherited ``/_class_/<element>`` Sphere
    ``primvars:displayColor``, authored at build time
    (``builders/element_templates.py``) -- this module never touches it.
2.  ONE camera for all four panels. If each panel's camera were fit to its
    own representation's bounding box, "vdw" (full van der Waals radii)
    would frame tighter than "points" (0.15x radii, see
    ``data/element_properties.py`` RADIUS_SCALES) and the molecule would
    read as four different sizes -- four different molecules -- destroying
    the tile's claim that this is ONE structure viewed four ways. Every
    panel is rendered with ``camera_representation="vdw"`` (the largest
    envelope, see ``render_support.author_camera``), varying only
    ``representation``. Because ``camera_representation`` is not yet
    validated by ``render_support`` (a fix is in flight elsewhere), this
    module asserts the resulting framing itself rather than trusting the
    argument silently did the right thing -- see ``_check_common_framing``.

Modes and their order come from ``p53_mdm2.p53_env.DEFAULT_REPRESENTATIONS``
-- read here, never retyped -- so this tile and every other consumer of that
tuple can never drift out of sync with each other.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import numpy as np
from PIL import Image

from make_poster_figures import (
    RASTER_HEIGHT_PX,
    RASTER_WIDTH_PX,
    Theme,
    figure,
    prov,
)

# p53_mdm2.figures.render_support drags in pxr (see figures/__init__.py's
# PEP-562 lazy-import note); p53_mdm2.p53_env and
# p53_mdm2.data.element_properties are pure-Python and safe unconditionally.
from p53_mdm2.p53_env import DEFAULT_REPRESENTATIONS, DEFAULT_ROOT_PATH
from p53_mdm2.data.element_properties import get_element_color
from p53_mdm2.figures import render_support

_HERE = os.path.dirname(os.path.abspath(__file__))
_P53_MDM2_DIR = os.path.dirname(_HERE)  # examples/p53_mdm2
STAGE_PATH = os.path.join(_P53_MDM2_DIR, "demos", "p53_mdm2_integrated.usda")

# The largest-envelope mode -- see module docstring point 2. Passed as
# render_support.render(..., camera_representation=...) for every panel, so
# one identical camera frames all four.
CAMERA_REPRESENTATION = "vdw"

# Alpha threshold above which a pixel counts as "drawn" geometry rather than
# background or an anti-aliased edge fragment.
_DRAWN_ALPHA_THRESHOLD = 10
# Alpha threshold for "fully opaque interior", used for the CPK colour/hue
# sampling so edge-antialiasing blends with the transparent background don't
# muddy the sampled hues.
_OPAQUE_ALPHA_THRESHOLD = 200

# CPK elements this structure actually contains reference values for
# (1YCR is a protein-protein interface: C/N/O always present; S is rare --
# see figures/README.md "sulphur yellow is rare in 1YCR").
_REFERENCE_ELEMENTS = ("C", "N", "O", "S")

# Two standard luma formulas, both reported below -- they disagree with each
# other by enough to matter for this exact question (see the printed
# "greyscale survival" block and the FINDING it produces). BT.601 is what
# PIL's own Image.convert("L") uses (ITU-R 601-2, the traditional broadcast
# formula); Rec.709 is the modern sRGB/HDTV formula. Reporting only one would
# have hidden that the answer to "do C/N/O/S survive greyscale conversion
# distinctly" depends on which convention a downstream print pipeline picks.
_LUMA_COEFFS_BT601 = (0.299, 0.587, 0.114)
_LUMA_COEFFS_REC709 = (0.2126, 0.7152, 0.0722)


def _luma(rgb, coeffs=_LUMA_COEFFS_REC709) -> float:
    r, g, b = rgb
    cr, cg, cb = coeffs
    return cr * r + cg * g + cb * b


def _luma_bt601(rgb) -> float:
    return _luma(rgb, _LUMA_COEFFS_BT601)


def _alpha_stats(png_path: str) -> dict:
    """Silhouette bbox / centroid / drawn-pixel-fraction of one rendered panel."""
    with Image.open(png_path) as im:
        size = im.size
        arr = np.asarray(im)
    if arr.shape[-1] != 4:
        raise RuntimeError(f"{png_path}: expected RGBA, got shape {arr.shape}")
    alpha = arr[..., 3]
    drawn = alpha > _DRAWN_ALPHA_THRESHOLD
    ys, xs = np.nonzero(drawn)
    if xs.size == 0:
        raise RuntimeError(f"{png_path}: nothing rendered (0 drawn pixels)")
    return {
        "size": size,
        "drawn_frac": float(drawn.mean()),
        "centroid": (float(xs.mean()), float(ys.mean())),
        "bbox": (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
        "corner_alpha": (
            int(alpha[0, 0]),
            int(alpha[0, -1]),
            int(alpha[-1, 0]),
            int(alpha[-1, -1]),
        ),
    }


def _hue_deg(r: np.ndarray, g: np.ndarray, b: np.ndarray):
    """Vectorized RGB (0..1 floats) -> hue in degrees, saturation, value."""
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    delta = maxc - minc
    s = np.where(maxc > 0, delta / np.where(maxc == 0, 1, maxc), 0.0)

    delta_safe = np.where(delta == 0, 1, delta)
    hue = np.zeros_like(r)
    is_r = (maxc == r) & (delta > 0)
    is_g = (maxc == g) & (delta > 0) & ~is_r
    is_b = (maxc == b) & (delta > 0) & ~is_r & ~is_g
    hue[is_r] = (((g[is_r] - b[is_r]) / delta_safe[is_r]) % 6) * 60
    hue[is_g] = (((b[is_g] - r[is_g]) / delta_safe[is_g]) + 2) * 60
    hue[is_b] = (((r[is_b] - g[is_b]) / delta_safe[is_b]) + 4) * 60
    return hue, s, v


# (label, hue-range-degrees) for the elements 1YCR is expected to contain.
# Hue ranges are wide bins picked empirically from the CPK swatches (see
# get_element_color()) and around the Storm-lit render itself, not tuned to
# make a desired answer come out -- carbon has no hue bin because it is the
# achromatic (grey, low-saturation) cluster.
_ELEMENT_HUE_BINS = (
    ("O", 0.0, 40.0),      # red   (1.0, 0.051, 0.051) -> hue ~0
    ("S", 40.0, 100.0),    # yellow (1.0, 1.0, 0.188)  -> hue ~60
    ("N", 200.0, 260.0),   # blue  (0.188, 0.314, 0.973) -> hue ~225
)
_SATURATION_FLOOR = 0.15  # below this, a pixel is classed as achromatic (C)


def _sample_element_hues(png_path: str) -> dict:
    """Cluster opaque, fully-drawn pixels of one rendered panel by hue.

    Returns one entry per element found: mean RGB (in the LIT render, not
    the flat CPK albedo), fraction of opaque pixels, and Rec.709 luma.
    Storm's Lambertian shading means a single sphere's surface spans a
    range of brightness even though its albedo is one flat colour, so the
    mean over many pixels/spheres is reported rather than any single pixel.
    """
    with Image.open(png_path) as im:
        arr = np.asarray(im)
    alpha = arr[..., 3]
    mask = alpha > _OPAQUE_ALPHA_THRESHOLD
    if not mask.any():
        raise RuntimeError(f"{png_path}: no fully-opaque pixels to sample")
    rgb = arr[..., :3][mask].astype(np.float64) / 255.0
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    hue, sat, _val = _hue_deg(r, g, b)

    total = rgb.shape[0]
    results = {}

    achromatic = sat <= _SATURATION_FLOOR
    if achromatic.any():
        mean_rgb = (
            float(r[achromatic].mean()),
            float(g[achromatic].mean()),
            float(b[achromatic].mean()),
        )
        results["C"] = {
            "n": int(achromatic.sum()),
            "frac_of_opaque": float(achromatic.sum()) / total,
            "mean_rgb": mean_rgb,
            "luma": _luma(mean_rgb),
        }

    for label, lo, hi in _ELEMENT_HUE_BINS:
        sel = (~achromatic) & (hue >= lo) & (hue < hi)
        if not sel.any():
            continue
        mean_rgb = (
            float(r[sel].mean()),
            float(g[sel].mean()),
            float(b[sel].mean()),
        )
        results[label] = {
            "n": int(sel.sum()),
            "frac_of_opaque": float(sel.sum()) / total,
            "mean_rgb": mean_rgb,
            "luma": _luma(mean_rgb),
        }
    return results


def _check_common_framing(stats_by_mode: dict, modes: tuple, centroid_tol_px: float = 12.0) -> None:
    """Assert the trap the brief calls out did not happen: verify, don't trust.

    1. All four centroids must agree within ``centroid_tol_px`` of their
       shared mean -- if ``camera_representation`` silently framed from the
       wrong geometry (e.g. a typo resolving per-mode instead of pinned to
       "vdw"), the four panels would show the molecule at visibly different
       scale/position and the centroids would diverge far more than
       antialiasing/coverage noise ever would.
    2. Drawn-pixel fraction must be strictly ordered
       points < {balls, ballstick} < vdw -- the only outcome a FIXED camera
       and varying sphere radius (RADIUS_SCALES in
       data/element_properties.py) can produce. A violation here would mean
       the camera was NOT actually fixed across panels.
    """
    cx = np.mean([stats_by_mode[m]["centroid"][0] for m in modes])
    cy = np.mean([stats_by_mode[m]["centroid"][1] for m in modes])
    for m in modes:
        px, py = stats_by_mode[m]["centroid"]
        dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
        if dist > centroid_tol_px:
            raise RuntimeError(
                f"mod-display: common-framing check FAILED for {m!r}: "
                f"centroid {(px, py)} is {dist:.2f}px from the four-panel "
                f"mean {(cx, cy)}, exceeding the {centroid_tol_px}px "
                f"tolerance. This is exactly the trap the brief warns "
                f"about -- camera_representation may have silently framed "
                f"from per-mode geometry instead of a single pinned mode."
            )

    fracs = {m: stats_by_mode[m]["drawn_frac"] for m in modes}
    if not (fracs["points"] < fracs["balls"] and fracs["points"] < fracs["ballstick"]):
        raise RuntimeError(
            f"mod-display: drawn-pixel-fraction ordering FAILED: "
            f"points={fracs['points']:.4f} must be less than both "
            f"balls={fracs['balls']:.4f} and ballstick={fracs['ballstick']:.4f}"
        )
    if not (fracs["balls"] < fracs["vdw"] and fracs["ballstick"] < fracs["vdw"]):
        raise RuntimeError(
            f"mod-display: drawn-pixel-fraction ordering FAILED: "
            f"vdw={fracs['vdw']:.4f} must exceed both "
            f"balls={fracs['balls']:.4f} and ballstick={fracs['ballstick']:.4f}"
        )


@figure("mod-display", ext="png")
def build_mod_display(theme: Theme, out_dir: str) -> str:
    modes = prov(
        tuple(DEFAULT_REPRESENTATIONS),
        source="p53_mdm2/p53_env.py:DEFAULT_REPRESENTATIONS",
        note="canonical (name, order) of the four representation modes -- "
        "read, not retyped",
    )
    n_panels = len(modes)
    if RASTER_WIDTH_PX % n_panels != 0:
        raise RuntimeError(
            f"mod-display: RASTER_WIDTH_PX={RASTER_WIDTH_PX} does not "
            f"divide evenly by {n_panels} panels"
        )
    panel_w = prov(RASTER_WIDTH_PX // n_panels, note="poster raster width / panel count")
    panel_h = prov(RASTER_HEIGHT_PX, note="poster raster height (full canvas height per panel)")
    panel_aperture_ratio = prov(
        panel_w / panel_h,
        note="per-panel horizontalAperture/verticalAperture passed to "
        "render_support.render() -- NOT the whole-poster aperture ratio",
    )
    stage_path = prov(os.path.relpath(STAGE_PATH), note="source stage rendered for every panel")
    camera_rep = prov(
        CAMERA_REPRESENTATION,
        note="camera_representation passed IDENTICALLY to every panel's "
        "render_support.render() call -- the largest envelope, so no mode "
        "overflows the frame it was fit from",
    )

    tmp_dir = tempfile.mkdtemp(prefix="mod_display_panels_")
    try:
        # -- provenance: read back one authored camera's actual parameters,
        # so the printed record shows real numbers, not just the recipe.
        # Built once, independently of the render() calls below (which each
        # build and discard their own copy) -- purely to inspect what
        # author_camera() decided, never mutating the committed stage.
        probe_session, probe_cam_path = render_support.build_render_session_layer(
            modes[0],
            panel_aperture_ratio,
            stage_path=STAGE_PATH,
            root_path=DEFAULT_ROOT_PATH,
            camera_representation=camera_rep,
            out_path=os.path.join(tmp_dir, "_camera_probe_session.usda"),
        )
        from pxr import Usd  # deferred: only this provenance probe needs it directly

        probe_stage = Usd.Stage.Open(probe_session)
        cam_prim = probe_stage.GetPrimAtPath(probe_cam_path)
        h_ap = cam_prim.GetAttribute("horizontalAperture").Get()
        v_ap = cam_prim.GetAttribute("verticalAperture").Get()
        focal = cam_prim.GetAttribute("focalLength").Get()
        translate = cam_prim.GetAttribute("xformOp:translate").Get()
        prov(float(h_ap), source="authored /RenderCamera.horizontalAperture")
        prov(float(v_ap), source="authored /RenderCamera.verticalAperture")
        prov(float(focal), source="authored /RenderCamera.focalLength")
        prov(tuple(translate), source="authored /RenderCamera xformOp:translate")
        del probe_stage
        os.remove(probe_session)

        # -- render all four panels, IDENTICAL camera_representation, only
        # `representation` varies. -----------------------------------------
        panel_paths = {}
        usdrecord_cmds = {}
        for mode in modes:
            panel_png = os.path.join(tmp_dir, f"panel_{mode}.png")
            render_support.render(
                STAGE_PATH,
                panel_png,
                width=panel_w,
                representation=mode,
                aperture_ratio=panel_aperture_ratio,
                root_path=DEFAULT_ROOT_PATH,
                camera_representation=camera_rep,
                # No display_color_overrides -- CPK colours are kept exactly
                # as authored on /_class_/<element> and inherited by every
                # atom's own Sphere. No accent anywhere in this tile.
            )
            panel_paths[mode] = panel_png
            usdrecord_cmds[mode] = (
                f"{render_support.USDRECORD} --renderer Storm "
                f"--sessionLayer <ephemeral tempfile, deleted post-render> "
                f"--camera {render_support.DEFAULT_CAMERA_PATH} "
                f"--imageWidth {panel_w} --complexity high "
                f"{stage_path} <out>/panel_{mode}.png"
            )

        # -- gate 1: exact per-panel size --------------------------------
        stats_by_mode = {}
        for mode in modes:
            stats = _alpha_stats(panel_paths[mode])
            if stats["size"] != (panel_w, panel_h):
                raise RuntimeError(
                    f"mod-display: panel {mode!r} is {stats['size']}, "
                    f"want ({panel_w}, {panel_h})"
                )
            stats_by_mode[mode] = stats

        # -- gate 2: common framing (verify, don't trust) ------------------
        _check_common_framing(stats_by_mode, modes)

        print(f"mod-display: provenance -- stage={stage_path}")
        print(f"mod-display: modes (from p53_env.DEFAULT_REPRESENTATIONS) = {modes}")
        print(
            f"mod-display: camera params -- horizontalAperture={h_ap:.4f} "
            f"verticalAperture={v_ap:.4f} focalLength={focal:.4f} "
            f"translate={tuple(translate)} camera_representation={camera_rep!r}"
        )
        for mode in modes:
            s = stats_by_mode[mode]
            print(
                f"mod-display: panel[{mode:>9}] size={s['size']} "
                f"drawn_frac={s['drawn_frac']:.4f} centroid={s['centroid']} "
                f"bbox={s['bbox']} corner_alpha={s['corner_alpha']} "
                f"cmd: {usdrecord_cmds[mode]}"
            )

        # -- CPK colour sampling on the densest panel (vdw) -----------------
        hue_clusters = _sample_element_hues(panel_paths["vdw"])
        print("mod-display: CPK hue clusters sampled from panel[vdw] (opaque pixels only):")
        for label in ("C", "N", "O", "S"):
            if label not in hue_clusters:
                print(f"  {label}: none found (expected -- rare/absent in 1YCR)"
                      if label == "S" else f"  {label}: NONE FOUND (unexpected)")
                continue
            c = hue_clusters[label]
            print(
                f"  {label}: n={c['n']} frac_of_opaque={c['frac_of_opaque']:.4f} "
                f"rendered_mean_rgb={tuple(round(x, 3) for x in c['mean_rgb'])} "
                f"rendered_luma={c['luma']:.3f}"
            )

        # -- greyscale survival: base CPK albedo (unlit, as authored) vs
        # what the lit render actually produced. Printed under BOTH luma
        # formulas -- they disagree on how close elements land to each
        # other, which is itself the finding (see below). ------------------
        print(
            "mod-display: greyscale survival -- authored CPK albedo (unlit), "
            "BT.601 vs Rec.709 luma:"
        )
        base_lumas_601 = {}
        base_lumas_709 = {}
        for el in _REFERENCE_ELEMENTS:
            rgb = prov(
                get_element_color(el),
                source="p53_mdm2/data/element_properties.py:get_element_color",
                note=f"authored CPK albedo for element {el}",
            )
            base_lumas_601[el] = _luma_bt601(rgb)
            base_lumas_709[el] = _luma(rgb)
            print(
                f"  {el}: rgb={rgb} luma_bt601={base_lumas_601[el]:.3f} "
                f"luma_rec709={base_lumas_709[el]:.3f}"
            )

        # Explicit distinguishability check requested by the gate: flag (do
        # NOT fix by recolouring) any pair of elements whose base-albedo
        # luma is close enough, under EITHER formula, to be hard to tell
        # apart in print/greyscale.
        els = list(base_lumas_601)
        for formula_name, base_lumas in (("BT.601", base_lumas_601), ("Rec.709", base_lumas_709)):
            for i in range(len(els)):
                for j in range(i + 1, len(els)):
                    a, b = els[i], els[j]
                    d = abs(base_lumas[a] - base_lumas[b])
                    if d < 0.05:
                        print(
                            f"mod-display: FINDING -- under {formula_name} luma, "
                            f"{a} ({base_lumas[a]:.3f}) and {b} ({base_lumas[b]:.3f}) "
                            f"differ by only {d:.3f} (out of 1.0); they read as "
                            f"nearly the same grey level in a black-and-white "
                            f"reproduction of this tile. Not fixed here: fixing "
                            f"it would mean overriding CPK colour, which breaks "
                            f"this tile's own claim of unmodified inherited "
                            f"element colour."
                        )

        # Separately: the brief's illustrative expected order (C < N < O < S)
        # does not hold under either standard luma formula for these actual
        # CPK triples -- both put O's converted grey BELOW N's, not above.
        # Reported once, plainly, rather than silently reordered to match.
        order_601 = sorted(els, key=lambda e: base_lumas_601[e])
        order_709 = sorted(els, key=lambda e: base_lumas_709[e])
        print(
            f"mod-display: ascending base-luma order -- "
            f"BT.601={order_601} Rec.709={order_709} "
            f"(brief's illustrative order was C<N<O<S; both formulas put O "
            f"below N, not above -- see report)"
        )

        # -- composite ------------------------------------------------------
        canvas = Image.new("RGBA", (RASTER_WIDTH_PX, RASTER_HEIGHT_PX), (0, 0, 0, 0))
        for i, mode in enumerate(modes):
            with Image.open(panel_paths[mode]) as im:
                canvas.paste(im.convert("RGBA"), (i * panel_w, 0))

        if canvas.size != (RASTER_WIDTH_PX, RASTER_HEIGHT_PX):
            raise RuntimeError(
                f"mod-display: composite is {canvas.size}, want "
                f"({RASTER_WIDTH_PX}, {RASTER_HEIGHT_PX})"
            )
        comp_arr = np.asarray(canvas)
        corner_alphas = (
            int(comp_arr[0, 0, 3]),
            int(comp_arr[0, -1, 3]),
            int(comp_arr[-1, 0, 3]),
            int(comp_arr[-1, -1, 3]),
        )
        if any(a != 0 for a in corner_alphas):
            raise RuntimeError(
                f"mod-display: composite corner alpha not 0: {corner_alphas}"
            )
        print(
            f"mod-display: composite size={canvas.size} mode={canvas.mode} "
            f"corner_alpha={corner_alphas}"
        )

        out_path = os.path.join(out_dir, "mod-display.png")
        canvas.save(out_path)
        return out_path
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
