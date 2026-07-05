#!/usr/bin/env python3
"""
Demo: BasisCurves bond encoding vs Cylinder bonds — size comparison and trajectory.

Composes the BasisCurves assembly + UsdClipsAPI trajectory clip, prints a
size-comparison table against the cylinder counterparts, and validates the stage.

Pattern applied:
- BasisCurves replaces 2,428 Xform/Cylinder prim pairs with one draw-call prim
- Value Clips: time-sampled points on /ABLComplex/Bonds across MD frames
- SubLayer composition: static topology + dynamic clip wired via UsdClipsAPI
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf, Vt


def compare_file_sizes(curves_assembly_path: str, cylinder_assembly_path: str,
                       curves_clip_path: str, cylinder_clip_path: str):
    """Print METRIC lines comparing BasisCurves vs Cylinder file sizes.

    Prints two lines:
      METRIC artifact=assembly cylinder_bytes=N curves_bytes=N ratio=F
      METRIC artifact=clip cylinder_bytes=N curves_bytes=N ratio=F

    ratio = curves_bytes / cylinder_bytes (< 1.0 means curves is smaller).
    """
    def _size(p):
        return os.path.getsize(p) if os.path.exists(p) else 0

    asm_cyl = _size(cylinder_assembly_path)
    asm_crv = _size(curves_assembly_path)
    asm_ratio = asm_crv / asm_cyl if asm_cyl > 0 else float("inf")
    print(f"METRIC artifact=assembly cylinder_bytes={asm_cyl} "
          f"curves_bytes={asm_crv} ratio={asm_ratio:.4f}")

    clip_cyl = _size(cylinder_clip_path)
    clip_crv = _size(curves_clip_path)
    clip_ratio = clip_crv / clip_cyl if clip_cyl > 0 else float("inf")
    print(f"METRIC artifact=clip cylinder_bytes={clip_cyl} "
          f"curves_bytes={clip_crv} ratio={clip_ratio:.4f}")


def create_curves_demo(output_path: str, curves_assembly_path: str,
                       curves_clip_path: str):
    """Create output/curves_demo.usda composing BasisCurves assembly + clip.

    SubLayers the BasisCurves assembly for static topology, then wires
    UsdClipsAPI on /ABLComplex to animate bond-endpoint positions from the
    BasisCurves trajectory clip.

    Args:
        output_path: Absolute path for the output .usda demo stage.
        curves_assembly_path: Absolute path to abl_kinase_complex_curves.usda.
        curves_clip_path: Absolute path to trajectory_clip_curves.usda.
    """
    # Determine frame count from clip
    clip_stage = Usd.Stage.Open(curves_clip_path)
    bc_clip = UsdGeom.BasisCurves(clip_stage.GetPrimAtPath("/ABLComplex/Bonds"))
    ts = bc_clip.GetPointsAttr().GetTimeSamples()
    n_frames = len(ts)
    del clip_stage

    if os.path.exists(output_path):
        os.remove(output_path)

    output_dir = os.path.dirname(output_path)
    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(n_frames - 1)
    stage.SetFramesPerSecond(10)
    stage.SetMetadata("comment",
        "BasisCurves demo stage: single-prim bond encoding + MD trajectory clip. "
        "Bonds prim uses time-sampled points (one Vec3fArray/frame) vs "
        "per-bond Xform+Cylinder translate+orient+height for the cylinder approach.")

    # SubLayer the BasisCurves assembly (static topology: atoms, bonds, metadata)
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(curves_assembly_path, output_dir)
    )

    # defaultPrim comes from the SubLayered assembly (/ABLComplex)
    stage.SetDefaultPrim(stage.GetPrimAtPath("/ABLComplex"))

    # =========================================================================
    # DEFAULT REPRESENTATION SELECTION
    # =========================================================================
    # /ABLComplex's own topology sublayer never authors a default
    # `representation` selection (by design — see
    # templates/06_create_assembly_curves.py, which calls
    # ClearVariantSelection() after building the cascade, same as
    # templates/04_create_assembly.py for the cylinder assembly). Without a
    # default authored somewhere in THIS demo's composition, fresh-open in
    # usdview resolves representation to "" (no variant selected) on every
    # descendant, so atoms have zero children (no Sphere/Cylinder selected)
    # while /ABLComplex/Bonds falls through to its unguarded base-layer
    # visibility of "inherited" — curves render alone, atoms render nothing
    # (diagnosis Item 3, cause a).
    #
    # WHY NOT a /World-wrapper cascade (the pattern demos/trajectory_demo.py
    # uses): tested directly (Sdf.Layer inspection of both
    # output/trajectory_demo.usda and an earlier draft of this file, plus an
    # isolated Usd.Stage.CreateInMemory() repro) and confirmed
    # `with some_other_prims_vset.GetVariantEditContext(): target.Set(...)`
    # does NOT author a variant-scoped opinion when `target` lives outside
    # the variant-owning prim's own namespace (e.g. /World's variant cannot
    # scope an opinion on sibling prim /ABLComplex, which arrives via
    # SubLayer, not as a child of /World) — each loop iteration instead
    # writes an unconditional opinion at target's own path, and only the
    # LAST iteration's value survives composition. /trajectory_demo.usda's
    # /World selection is therefore decorative today: changing it in usdview
    # has zero effect on /ABLComplex, invisible there only because
    # Sphere+Cylinder are BOTH visible in every mode so the pinned
    # "ballstick" default happens to look correct. That defect is out of
    # scope here (not flagged by the diagnosis, not part of this fix
    # cycle's mandate) — flagging it as a documented pre-existing gap
    # rather than silently inheriting it into curves_demo.py, since here it
    # WOULD be gate-3-visible: Bonds is genuinely visibility-gated per mode
    # (templates/06_create_assembly_curves.py's bonds_vset loop), so a
    # /World proxy would leave Bonds pinned visible under every selection —
    # a real double-display regression.
    #
    # Correct fix, verified directly against
    # assets/level4_assemblies/abl_kinase_complex_curves.usda: setting
    # /ABLComplex's OWN `representation` selection (the variant set that
    # 06_create_assembly_curves.py's complex-level cascade loop already
    # wires correctly, in the SAME layer/namespace as every descendant it
    # cascades to) DOES correctly gate Bonds visibility and every atom's own
    # selection, because that cascade's GetVariantEditContext() calls are
    # scoped within /ABLComplex's own subtree the whole time. One
    # unconditional SetVariantSelection call on /ABLComplex is sufficient;
    # no loop, no proxy prim needed.
    DEFAULT_MODE = "ballstick"  # shows atoms AND bond curves together —
    # this demo's whole point is BasisCurves bonds, so a default that hides
    # Bonds (points/balls/vdw) would silently defeat opening curves_demo.usda.
    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    complex_prim.GetVariantSets().GetVariantSet(
        "representation").SetVariantSelection(DEFAULT_MODE)

    # Wire UsdClipsAPI on /ABLComplex to animate bond-endpoint positions
    clips_api = Usd.ClipsAPI(complex_prim)

    clip_rel_path = os.path.relpath(curves_clip_path, output_dir)
    clips_api.SetClipAssetPaths([Sdf.AssetPath(clip_rel_path)])
    clips_api.SetClipPrimPath("/ABLComplex")

    clip_times = Vt.Vec2dArray(
        [Gf.Vec2d(float(i), float(i)) for i in range(n_frames)]
    )
    clips_api.SetClipTimes(clip_times)
    clips_api.SetClipActive(Vt.Vec2dArray([Gf.Vec2d(0.0, 0.0)]))

    stage.Save()

    print(f"Created: {output_path}")
    print(f"  Timeline: 0-{n_frames - 1} ({n_frames} frames at 10 fps)")
    print(f"  SubLayer: {os.path.basename(curves_assembly_path)}")
    print(f"  Clip: {os.path.basename(curves_clip_path)}")
    print(f"  Default representation: {DEFAULT_MODE} (defaultPrim=/ABLComplex)")

    # Structural assertions
    reopen = Usd.Stage.Open(output_path)
    bonds_prim = reopen.GetPrimAtPath("/ABLComplex/Bonds")
    assert bonds_prim.IsValid(), "/ABLComplex/Bonds not found in demo stage"
    bc = UsdGeom.BasisCurves(bonds_prim)
    assert bc, "/ABLComplex/Bonds is not UsdGeomBasisCurves"
    print("  PASS: /ABLComplex/Bonds is UsdGeomBasisCurves")

    chain_a = reopen.GetPrimAtPath("/ABLComplex/Chain_A")
    assert chain_a.IsValid(), "Chain_A missing from demo stage"
    print("  PASS: /ABLComplex/Chain_A exists")

    clips_check = Usd.ClipsAPI(reopen.GetPrimAtPath("/ABLComplex"))
    asset_paths = clips_check.GetClipAssetPaths()
    assert len(asset_paths) > 0, "UsdClipsAPI clip not wired on /ABLComplex"
    print(f"  PASS: UsdClipsAPI clip wired ({len(asset_paths)} asset path(s))")

    default_prim = reopen.GetDefaultPrim()
    assert default_prim.IsValid() and default_prim.GetPath() == Sdf.Path("/ABLComplex"), (
        f"Expected defaultPrim=/ABLComplex, got {default_prim.GetPath() if default_prim else None}"
    )
    default_sel = default_prim.GetVariantSets().GetVariantSet(
        "representation").GetVariantSelection()
    assert default_sel == DEFAULT_MODE, (
        f"Expected default representation selection {DEFAULT_MODE!r}, got {default_sel!r}"
    )
    print(f"  PASS: fresh-open default representation resolves to {default_sel!r}")

    # A fresh-open atom should have exactly one child gprim selected by the
    # cascade (no double-display, no zero-children).
    sample_atom = reopen.GetPrimAtPath("/ABLComplex/Chain_A/ACE_1/HH31")
    assert sample_atom.IsValid(), "sample atom prim missing"
    atom_children = sample_atom.GetChildren()
    assert len(atom_children) == 1, (
        f"Expected exactly 1 gprim child on fresh-open atom ({DEFAULT_MODE} default), "
        f"got {len(atom_children)}: {[c.GetName() for c in atom_children]}"
    )
    print(f"  PASS: fresh-open sample atom has exactly 1 child gprim "
          f"({atom_children[0].GetTypeName()})")

    # Bonds must be visible-gated EXCLUSIVELY: visible now (ballstick
    # default), and this must actually correspond to the resolved
    # variant selection, not a pinned/unconditional opinion (diagnosis
    # Item 3, cause a — see the WHY-NOT-/World comment above).
    bonds_vis = UsdGeom.Imageable(bonds_prim).ComputeVisibility()
    expected_bonds_vis = (
        UsdGeom.Tokens.inherited if DEFAULT_MODE == "ballstick"
        else UsdGeom.Tokens.invisible
    )
    assert bonds_vis == expected_bonds_vis, (
        f"Expected Bonds visibility={expected_bonds_vis!r} at default mode "
        f"{DEFAULT_MODE!r}, got {bonds_vis!r}"
    )
    print(f"  PASS: /ABLComplex/Bonds visibility={bonds_vis!r} matches "
          f"default mode {DEFAULT_MODE!r}")

    return output_path


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    assets_dir = os.path.join(root_dir, "assets", "level4_assemblies")
    clips_dir = os.path.join(output_dir, "clips")

    curves_assembly = os.path.join(assets_dir, "abl_kinase_complex_curves.usda")
    cylinder_assembly = os.path.join(assets_dir, "abl_kinase_complex.usda")
    curves_clip = os.path.join(clips_dir, "trajectory_clip_curves.usda")
    cylinder_clip = os.path.join(clips_dir, "trajectory_clip.usda")
    demo_output = os.path.join(output_dir, "curves_demo.usda")

    for path, label in [
        (curves_assembly, "BasisCurves assembly"),
        (curves_clip, "BasisCurves clip"),
    ]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    create_curves_demo(demo_output, curves_assembly, curves_clip)

    print("\n--- File Size Comparison ---")
    compare_file_sizes(curves_assembly, cylinder_assembly, curves_clip, cylinder_clip)
