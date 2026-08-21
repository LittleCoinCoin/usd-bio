#!/usr/bin/env python3
"""
render_support.py -- reusable helpers for rendering poster figures from
``examples/p53_mdm2/demos/p53_mdm2_integrated.usda``.

Why this module exists
-----------------------
The committed layer stack authors a ``representation`` VariantSet cascade
(``points`` / ``balls`` / ``vdw`` / ``ballstick``) on ``/p53_MDM2_complex``
(see ``builders/build_assembly.py``), but NO layer ever calls
``SetVariantSelection`` on it and saves that opinion to disk -- the demo's
own ``over`` block in ``demos/p53_mdm2_integrated.usda`` only selects the
unrelated ``Genotype`` VariantSet. A naive ``usdrecord`` on that file
therefore composes with representation UNSELECTED, which resolves to zero
Sphere prims (834 Cylinder bonds still resolve, because bond visibility is
authored per-mode inside each mode's own variant, but the *atoms themselves*
have no geometry at all outside a selected representation variant) --
confirmed empirically:

    naive Usd.Stage.Open(...):           Sphere=0    Cylinder=834
    with a "ballstick" session layer:     Sphere=818  Cylinder=834

This module supplies the render-time opinion via a **session layer** rather
than editing the committed .usda, so the render path never mutates evidence
files. Session layers are the strongest layer in a stage's LIVERPS stack
(stronger than the root layer and every sublayer), which is exactly the
right strength for a variant-selection override plus a camera that has no
business living in the composed demo stage.

There is also no ``UsdGeomCamera`` and no render settings anywhere in the
p53_mdm2 layer stack (confirmed by reading every committed layer under
``examples/p53_mdm2/``), so the poster's 3.3336:1 crop -- measured from the
poster's actual image slot, 214.94 x 64.48 mm -- has to come from a camera
this module authors, framed off the ACTUAL composed bounding box (never
hardcoded numbers), landing at 2560 x 768 px.

Public API
----------
- ``build_representation_session_layer(representation, ...)`` -- session
  layer selecting one representation, with optional per-prim displayColor
  overrides (for a later item's accent highlighting).
- ``author_camera(stage_path, session_layer_path, aperture_ratio, ...)`` --
  adds a framing camera to an existing (or new) session layer, computed from
  ``UsdGeom.BBoxCache`` on the real composed stage.
- ``render(stage_path, out_png, width, representation, ...)`` -- invokes the
  ABSOLUTE-path ``usdrecord`` (never the bare name -- see module docstring
  in RENDER_NOTES.md for the Apple-Metal-stub trap) with ``--renderer Storm``
  and the merged session layer; raises on any failure or missing output.
- ``count_prims_of_type(stage, type_name)`` -- gate helper.
"""

from __future__ import annotations

import contextlib
import math
import os
import subprocess
import tempfile

from pxr import Usd, UsdGeom, Sdf, Gf

# ---------------------------------------------------------------------------
# Fixed, verified paths (CLAUDE.md environment section: NEVER the bare name).
# ---------------------------------------------------------------------------
USDRECORD = "/Users/hacker/Documents/bin/OpenUSD/bin/usdrecord"

DEFAULT_ROOT_PATH = "/p53_MDM2_complex"
DEFAULT_REPRESENTATIONS = ("points", "balls", "vdw", "ballstick")
DEFAULT_CAMERA_PATH = "/RenderCamera"

# Poster crop, measured (not guessed) from the poster's actual image slot:
# 214.94 x 64.48 mm ~= 3.3336:1 (quoted precision). Raster target 2560 x 768 px.
#
# RECONCILIATION NOTE (see RENDER_NOTES.md for the empirical evidence): the
# literal quoted ratio 214.94 / 64.48 = 3.33344 and the literal pixel target
# 2560 x 768 are NOT bit-exact matches of each other -- 2560 / 3.3336 =
# 767.945, and usdrecord derives image height from imageWidth / camera
# aspect ratio by TRUNCATION, not rounding, so a camera built at the quoted
# 3.3336 ratio measurably renders 767px tall, one pixel short of the 768px
# gate (confirmed empirically: see RENDER_NOTES.md "aperture reconciliation").
# The two given numbers agree to 4 significant figures (a ~0.03% difference,
# invisible at print size); POSTER_APERTURE_RATIO uses the pixel-exact form
# (2560 / 768) so the aperture ratio and the raster target are internally
# consistent and the exact-pixel success gate is satisfiable at all.
POSTER_WIDTH_PX = 2560
POSTER_HEIGHT_PX = 768
POSTER_APERTURE_RATIO_MEASURED = 214.94 / 64.48  # provenance / documentation only
POSTER_APERTURE_RATIO = POSTER_WIDTH_PX / POSTER_HEIGHT_PX  # what the camera actually uses


class RenderError(RuntimeError):
    """Raised by :func:`render` when usdrecord fails or produces no output."""


# ---------------------------------------------------------------------------
# Session layer: representation selection (+ optional displayColor accents)
# ---------------------------------------------------------------------------

def build_representation_session_layer(
    representation: str,
    *,
    root_path: str = DEFAULT_ROOT_PATH,
    display_color_overrides: dict | None = None,
    out_path: str | None = None,
) -> str:
    """Build a session layer that selects ``representation`` on ``root_path``.

    The cascade in ``builders/build_assembly.py`` propagates a selection made
    on the complex root down through chain -> residue -> atom/bond (each
    level's variant-edit-context re-selects the same mode on its children at
    build time), so a single ``over`` with a variant selection on the root
    prim is sufficient to bring all 818 atoms and the mode-appropriate bonds
    into resolution -- no per-atom opinion needed.

    Args:
        representation: one of DEFAULT_REPRESENTATIONS ("points", "balls",
            "vdw", "ballstick").
        root_path: the complex root prim path (project convention:
            ``/p53_MDM2_complex``, see ``p53_env.DEFAULT_ROOT_PATH``).
        display_color_overrides: optional {prim_path: (r, g, b)} in 0..1,
            authored as a ``constant primvars:displayColor`` override on each
            named prim via ``UsdGeom.PrimvarsAPI`` (works whether the target
            is a concrete Gprim or an Xform container). Reserved for a later
            figure item's accent-highlight need. CAVEAT for that item: this
            is a session-layer OVER, and USD's inherited-primvar fallback
            only supplies a value where a descendant authors NONE of its
            own -- every atom's Sphere here already has its own per-element
            CPK ``displayColor`` authored at build time
            (``element_templates.py``), so an override on an ancestor
            (residue/chain/atom-container) prim path will NOT visually
            override an atom's own color through inheritance alone. To
            actually recolor atoms, point ``display_color_overrides`` at the
            atoms' own Sphere paths (reached through the selected variant,
            e.g. ``.../<atomName>/Sphere``) or extend this function to
            author the override inside the same variant edit context.
        out_path: destination .usda path for the session layer. A fresh
            NamedTemporaryFile path is used if omitted.

    Returns:
        The absolute path to the written session-layer .usda.
    """
    if representation not in DEFAULT_REPRESENTATIONS:
        raise ValueError(
            f"Unknown representation {representation!r}; use one of "
            f"{DEFAULT_REPRESENTATIONS}"
        )

    if out_path is None:
        fd, out_path = tempfile.mkstemp(suffix=".usda", prefix="p53_session_")
        os.close(fd)

    if os.path.exists(out_path):
        os.remove(out_path)

    layer = Sdf.Layer.CreateNew(out_path)
    stage = Usd.Stage.Open(layer)

    root_prim = stage.OverridePrim(root_path)
    vset = root_prim.GetVariantSets().AddVariantSet("representation")
    vset.SetVariantSelection(representation)

    if display_color_overrides:
        for prim_path, rgb in display_color_overrides.items():
            over_prim = stage.OverridePrim(prim_path)
            # Use the generic PrimvarsAPI rather than UsdGeom.Gprim -- the
            # override target may be an Xform (a residue/chain/atom
            # container) rather than a concrete Gprim (whose actual Sphere/
            # Cylinder lives one level deeper, inside its representation
            # variant), and Imageable itself has no CreateDisplayColorAttr.
            # A primvar authored here is inherited by descendants that don't
            # author their own, which is exactly the "accent a subtree"
            # behavior a later figure item needs.
            primvars_api = UsdGeom.PrimvarsAPI(over_prim)
            color_pv = primvars_api.CreatePrimvar(
                "displayColor", Sdf.ValueTypeNames.Color3fArray,
                interpolation=UsdGeom.Tokens.constant,
            )
            color_pv.Set([Gf.Vec3f(*rgb)])

    stage.GetRootLayer().Save()
    return out_path


# ---------------------------------------------------------------------------
# Camera: framed off the real composed bounding box
# ---------------------------------------------------------------------------

def _compute_world_bbox(
    stage_path: str,
    prim_path: str,
    representation: str,
) -> Gf.Range3d:
    """Open ``stage_path`` fresh with ``representation`` selected in-memory
    (never touching the committed file) and return the world-space aligned
    bounding range of ``prim_path``."""
    stage = Usd.Stage.Open(stage_path)
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise ValueError(f"{prim_path!r} not found on {stage_path!r}")

    vsets = prim.GetVariantSets()
    if "representation" in vsets.GetNames():
        vsets.GetVariantSet("representation").SetVariantSelection(representation)

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render],
        useExtentsHint=True,
    )
    bbox = cache.ComputeWorldBound(prim)
    rng = bbox.ComputeAlignedRange()
    if rng.IsEmpty():
        raise RuntimeError(
            f"{prim_path!r} resolved to an EMPTY bounding box under "
            f"representation={representation!r} -- nothing to frame. This "
            f"means the representation selection did not reach any gprim; "
            f"do not build a camera from a hardcoded fallback."
        )
    return rng


def author_camera(
    stage_path: str,
    session_layer_path: str,
    aperture_ratio: float = POSTER_APERTURE_RATIO,
    *,
    root_path: str = DEFAULT_ROOT_PATH,
    representation: str = "vdw",
    camera_path: str = DEFAULT_CAMERA_PATH,
    fov_deg: float = 50.0,
    padding: float = 1.15,
    vertical_aperture_mm: float = 20.0,
) -> str:
    """Author a UsdGeomCamera into ``session_layer_path`` framing ``root_path``.

    The frame is derived from the ACTUAL composed stage's bounding box (via
    ``UsdGeom.BBoxCache``), not from hardcoded scene numbers. ``representation``
    controls which mode's geometry the bbox is measured against -- default is
    "vdw" (the largest sphere radii, ``RADIUS_SCALES["vdw"] = 1.00`` in
    ``data/element_properties.py``) so the frame comfortably contains every
    other mode's smaller geometry too, avoiding a crop that is correct for
    "points" but clips "vdw".

    Args:
        stage_path: path to the composed integrated .usda (read-only; this
            function never writes to it).
        session_layer_path: existing (or to-be-created) session-layer .usda;
            the camera is ADDED to whatever this layer already contains, so
            a caller can combine this with
            :func:`build_representation_session_layer` into one file before
            handing a single ``--sessionLayer`` to usdrecord.
        aperture_ratio: horizontalAperture / verticalAperture. Defaults to
            the measured poster crop, ``POSTER_APERTURE_RATIO`` (214.94 /
            64.48 mm = 3.3336).
        root_path: prim to frame.
        representation: which mode's geometry to measure the bbox against.
        camera_path: destination prim path for the authored camera.
        fov_deg: vertical field of view used to back-solve focal length and
            camera distance.
        padding: multiplier on the fitted distance so the subject doesn't
            touch the frame edges (1.0 = exact fit).
        vertical_aperture_mm: arbitrary aperture scale in mm; only the RATIO
            to horizontalAperture matters for usdrecord's aspect-derived
            image height, but the absolute value also has to be physically
            sane for the focal-length/FOV relationship used to size the shot.

    Returns:
        ``camera_path`` (the same value passed in), for convenience.
    """
    if representation not in DEFAULT_REPRESENTATIONS:
        # Mirrors build_representation_session_layer's guard. Without this,
        # an unknown mode passed through as camera_representation resolves
        # to NO selection at all (SetVariantSelection on a name the
        # VariantSet doesn't have is a silent no-op), so the bbox measured
        # here is whatever geometry survives an UNSELECTED representation
        # cascade -- which, per this module's own module docstring, is just
        # the 834 bond Cylinders, not the 818 atoms. That silently shrinks
        # the fitted frame around a smaller, wrong subject with no error at
        # all -- a bad `camera_representation` must fail loudly instead of
        # quietly producing an under-framed (and, with a different padding
        # value, potentially clipping) camera.
        raise ValueError(
            f"Unknown representation {representation!r}; use one of "
            f"{DEFAULT_REPRESENTATIONS}"
        )
    rng = _compute_world_bbox(stage_path, root_path, representation)
    center = (rng.GetMin() + rng.GetMax()) / 2.0
    size = rng.GetMax() - rng.GetMin()

    horiz_aperture = vertical_aperture_mm * aperture_ratio

    # Fit both the horizontal and vertical extent of the bbox into the frame;
    # depth (Z) extent doesn't drive framing but is folded in for safety on
    # a near-edge-on view.
    half_height_needed = max(size[1] / 2.0, (size[0] / 2.0) / aperture_ratio)
    half_height_needed = max(half_height_needed, size[2] / 2.0 / aperture_ratio)

    half_fov_rad = math.radians(fov_deg / 2.0)
    distance = (half_height_needed / math.tan(half_fov_rad)) * padding
    focal_length = vertical_aperture_mm / (2.0 * math.tan(half_fov_rad))

    if os.path.exists(session_layer_path):
        layer = Sdf.Layer.FindOrOpen(session_layer_path)
    else:
        layer = Sdf.Layer.CreateNew(session_layer_path)
    stage = Usd.Stage.Open(layer)

    camera = UsdGeom.Camera.Define(stage, camera_path)
    camera.CreateHorizontalApertureAttr(horiz_aperture)
    camera.CreateVerticalApertureAttr(vertical_aperture_mm)
    camera.CreateFocalLengthAttr(focal_length)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, float(distance * 10 + size[2] + 10)))

    xformable = UsdGeom.Xformable(camera.GetPrim())
    xformable.ClearXformOpOrder()
    xformable.AddTranslateOp().Set(
        Gf.Vec3d(center[0], center[1], center[2] + distance)
    )

    stage.GetRootLayer().Save()
    return camera_path


# ---------------------------------------------------------------------------
# Combined session layer: representation + camera in one file
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _temp_session_layer_path(out_path: str | None = None):
    """Allocate (or accept) a session-layer path, GUARANTEED to be removed
    if the wrapped block raises before it finishes -- and left alone
    (ownership transferred to the caller) on a clean exit.

    This exists because ``build_render_session_layer`` writes the
    representation selection and the camera into the SAME file across two
    separate calls (``build_representation_session_layer`` then
    ``author_camera``). The first call unconditionally creates and saves
    the file; the second can raise (bad ``root_path``, nonexistent
    ``stage_path``, an empty-bbox ``RuntimeError``, or -- since the DEFECT-1
    fix above -- a bad ``camera_representation``). Without this, that
    exception leaves the already-written temp ``.usda`` on disk forever:
    nothing downstream of the raise ever reaches the ``os.remove`` call that
    ``render()`` only wraps around its own ``subprocess.run``. Confirmed
    leaking twice in the adversarial verification pass, including two
    pre-existing leaked files already found in the OS temp dir from earlier
    real (non-test) usage.
    """
    owns_path = out_path is None
    if owns_path:
        fd, out_path = tempfile.mkstemp(suffix=".usda", prefix="p53_session_")
        os.close(fd)
    try:
        yield out_path
    except BaseException:
        try:
            os.remove(out_path)
        except OSError:
            pass
        raise


def build_render_session_layer(
    representation: str,
    aperture_ratio: float = POSTER_APERTURE_RATIO,
    *,
    stage_path: str,
    root_path: str = DEFAULT_ROOT_PATH,
    display_color_overrides: dict | None = None,
    camera_representation: str = "vdw",
    camera_path: str = DEFAULT_CAMERA_PATH,
    out_path: str | None = None,
) -> tuple[str, str]:
    """Convenience combiner: one session layer with BOTH the representation
    selection and the framing camera, ready for a single ``--sessionLayer``
    argument to usdrecord.

    Exception-safe: if either the representation-selection write or the
    camera-authoring step raises (see :func:`_temp_session_layer_path`),
    the temp file created for this attempt is removed before the exception
    propagates -- no leaked ``.usda`` on any error path.

    Returns:
        (session_layer_path, camera_path)
    """
    with _temp_session_layer_path(out_path) as session_layer_path:
        build_representation_session_layer(
            representation,
            root_path=root_path,
            display_color_overrides=display_color_overrides,
            out_path=session_layer_path,
        )
        author_camera(
            stage_path,
            session_layer_path,
            aperture_ratio,
            root_path=root_path,
            representation=camera_representation,
            camera_path=camera_path,
        )
    return session_layer_path, camera_path


# ---------------------------------------------------------------------------
# Render wrapper
# ---------------------------------------------------------------------------

def render(
    stage_path: str,
    out_png: str,
    width: int,
    representation: str,
    *,
    aperture_ratio: float = POSTER_APERTURE_RATIO,
    root_path: str = DEFAULT_ROOT_PATH,
    display_color_overrides: dict | None = None,
    camera_representation: str = "vdw",
    camera_path: str = DEFAULT_CAMERA_PATH,
    disable_gpu: bool = False,
    complexity: str = "high",
    renderer: str = "Storm",
    timeout: int = 180,
    keep_session_layer: bool = False,
) -> str:
    """Render ``stage_path`` at ``representation`` to ``out_png`` via the
    ABSOLUTE-path ``usdrecord`` binary.

    Builds a merged session layer (variant selection + framing camera) with
    :func:`build_render_session_layer`, then invokes::

        usdrecord --renderer Storm --sessionLayer <layer> --camera <path> \\
                   --imageWidth <width> [--disableGpu] <stage_path> <out_png>

    Raises :class:`RenderError` if usdrecord exits non-zero OR the output
    file does not exist afterward (usdrecord can exit 0 without writing a
    file in some failure modes, so both are checked).

    Args:
        stage_path: the composed .usda to render (e.g.
            ``demos/p53_mdm2_integrated.usda``).
        out_png: destination PNG path (parent directory must exist or is
            created).
        width: --imageWidth; height follows from the camera's aperture
            ratio.
        representation: which of the four canonical modes to select for this
            render.
        aperture_ratio: horizontalAperture / verticalAperture for the
            authored camera (defaults to the measured poster crop).
        display_color_overrides: forwarded to
            :func:`build_representation_session_layer`.
        camera_representation: which mode's bbox sizes the camera (default
            "vdw", the largest -- see :func:`author_camera`).
        disable_gpu: forwarded as ``--disableGpu``.
        complexity: forwarded as ``--complexity``.
        renderer: forwarded as ``--renderer`` (project requires "Storm").
        timeout: subprocess timeout in seconds.
        keep_session_layer: if False (default), the temp session-layer file
            is removed after the render attempt (success or failure).

    Returns:
        ``out_png``.
    """
    if not os.path.isfile(USDRECORD):
        raise RenderError(
            f"usdrecord not found at the pinned absolute path {USDRECORD!r}. "
            f"Do NOT fall back to a bare 'usdrecord' on PATH -- on this "
            f"machine that resolves to /usr/bin/usdrecord, Apple's "
            f"Metal-only USD 0.25.2 stub, a different build entirely."
        )

    out_dir = os.path.dirname(os.path.abspath(out_png))
    os.makedirs(out_dir, exist_ok=True)

    session_layer_path, cam_path = build_render_session_layer(
        representation,
        aperture_ratio,
        stage_path=stage_path,
        root_path=root_path,
        display_color_overrides=display_color_overrides,
        camera_representation=camera_representation,
        camera_path=camera_path,
    )

    cmd = [
        USDRECORD,
        "--renderer", renderer,
        "--sessionLayer", session_layer_path,
        "--camera", cam_path,
        "--imageWidth", str(width),
        "--complexity", complexity,
    ]
    if disable_gpu:
        cmd.append("--disableGpu")
    cmd += [stage_path, out_png]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False,
        )
    finally:
        if not keep_session_layer:
            try:
                os.remove(session_layer_path)
            except OSError:
                pass

    if result.returncode != 0:
        raise RenderError(
            f"usdrecord exited {result.returncode}.\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    if not os.path.isfile(out_png):
        raise RenderError(
            f"usdrecord exited 0 but did not produce {out_png!r}.\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    return out_png


# ---------------------------------------------------------------------------
# Gate helper
# ---------------------------------------------------------------------------

def count_prims_of_type(stage: Usd.Stage, type_name: str) -> int:
    """Count prims of ``type_name`` (e.g. "Sphere", "Cylinder") on a fresh
    ``Usd.Stage``, by traversal (not by any generator in-memory state)."""
    return sum(1 for p in stage.Traverse() if p.GetTypeName() == type_name)


def open_stage_with_representation(
    stage_path: str,
    representation: str,
    *,
    root_path: str = DEFAULT_ROOT_PATH,
) -> Usd.Stage:
    """Open ``stage_path`` with a session layer selecting ``representation``
    on ``root_path``. Convenience for gate 1 -- does not touch the committed
    file."""
    session_layer_path = build_representation_session_layer(
        representation, root_path=root_path,
    )
    try:
        root_layer = Sdf.Layer.FindOrOpen(stage_path)
        session_layer = Sdf.Layer.FindOrOpen(session_layer_path)
        return Usd.Stage.Open(root_layer, session_layer)
    finally:
        try:
            os.remove(session_layer_path)
        except OSError:
            pass
