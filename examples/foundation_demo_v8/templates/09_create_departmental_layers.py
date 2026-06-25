#!/usr/bin/env python3
"""
Template 09 — Create departmental layer files for ABL kinase 5-layer stage.

Generates five minimal-but-meaningful .usda layer files under
assets/level6_departmental/, each contributing distinct, non-overlapping
content to the /ABLComplex namespace.

Layers (weakest to strongest opinion):
  biology.usda   — topology: sublayers assembly, representation VariantSet
  protocol.usda  — experimental setup metadata on /ABLComplex/ProtocolMetadata
  dynamics.usda  — UsdClipsAPI wiring: trajectory clip attached to /ABLComplex
  analysis.usda  — time-sampled bio:rmsd float on /ABLComplex (20 samples)
  review.usda    — UsdGeomCamera + annotation Xform on /ABLComplex

Pattern: Departmental SubLayer separation
  WHY: allows each research concern to be independently versioned, loaded,
  and muted without breaking the other layers' composition.
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf, Vt


# ---------------------------------------------------------------------------
# Layer 1: Biology (topology sublayer)
# ---------------------------------------------------------------------------

def _create_biology_layer(layer_dir: str, assembly_rel: str) -> str:
    """Create biology.usda — topology base layer."""
    path = os.path.join(layer_dir, "biology.usda")
    if os.path.exists(path):
        os.remove(path)

    stage = Usd.Stage.CreateNew(path)
    stage.GetRootLayer().documentation = (
        "Biology layer: ABL kinase topology sublayer. "
        "SubLayers the level4 assembly (chain/residue/atom hierarchy, "
        "bio: metadata, element class inheritance, representation VariantSet)."
    )
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # SubLayer the assembly — this brings in all topology + representation variants
    stage.GetRootLayer().subLayerPaths.append(assembly_rel)

    # Set defaultPrim so this layer is standalone-openable
    stage.SetDefaultPrim(stage.GetPrimAtPath("/ABLComplex"))

    stage.GetRootLayer().Save()
    print(f"  biology.usda written: {path}")
    return path


# ---------------------------------------------------------------------------
# Layer 2: Protocol (experimental metadata)
# ---------------------------------------------------------------------------

def _create_protocol_layer(layer_dir: str) -> str:
    """Create protocol.usda — experimental setup metadata."""
    path = os.path.join(layer_dir, "protocol.usda")
    if os.path.exists(path):
        os.remove(path)

    stage = Usd.Stage.CreateNew(path)
    stage.GetRootLayer().documentation = (
        "Protocol layer: ShinobuLab MD simulation setup metadata. "
        "Defines /ABLComplex/ProtocolMetadata Xform with simulation parameters."
    )
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # Define the root prim as an over so it merges with biology topology
    root = stage.OverridePrim("/ABLComplex")
    stage.SetDefaultPrim(root)

    # Protocol metadata prim
    meta = UsdGeom.Xform.Define(stage, "/ABLComplex/ProtocolMetadata")
    meta_prim = meta.GetPrim()

    # Simulation parameters
    # [assumption: box dimensions 75x75x75 Å from ShinobuLab MD; CRYST1 not verified here]
    solvent = meta_prim.CreateAttribute(
        "bio:solventModel", Sdf.ValueTypeNames.Token, custom=True
    )
    solvent.Set("TIP3P")

    box = meta_prim.CreateAttribute(
        "bio:boxDimensions", Sdf.ValueTypeNames.Float3, custom=True
    )
    box.Set(Gf.Vec3f(75.0, 75.0, 75.0))

    ion_count = meta_prim.CreateAttribute(
        "bio:ionCount", Sdf.ValueTypeNames.Int, custom=True
    )
    ion_count.Set(42)

    equil_ns = meta_prim.CreateAttribute(
        "bio:equilibrationNs", Sdf.ValueTypeNames.Float, custom=True
    )
    equil_ns.Set(2.5)

    stage.GetRootLayer().Save()
    print(f"  protocol.usda written: {path}")
    return path


# ---------------------------------------------------------------------------
# Layer 3: Dynamics (Value Clips wiring)
# ---------------------------------------------------------------------------

def _create_dynamics_layer(layer_dir: str, clip_rel: str) -> str:
    """Create dynamics.usda — attaches trajectory Value Clips to /ABLComplex."""
    path = os.path.join(layer_dir, "dynamics.usda")
    if os.path.exists(path):
        os.remove(path)

    stage = Usd.Stage.CreateNew(path)
    stage.GetRootLayer().documentation = (
        "Dynamics layer: attaches MD trajectory data via UsdClipsAPI. "
        "Allows removing trajectory without affecting topology or analysis layers."
    )
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # Override the root prim to attach clips
    root = stage.OverridePrim("/ABLComplex")
    stage.SetDefaultPrim(root)

    # Attach clips via UsdClipsAPI
    clips_api = Usd.ClipsAPI(root)
    clips_api.SetClipAssetPaths([Sdf.AssetPath(clip_rel)])
    clips_api.SetClipPrimPath("/ABLComplex")
    clips_api.SetClipActive([(0.0, 0)])
    clips_api.SetClipTimes([(0.0, 0.0), (19.0, 19.0)])

    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(19)
    stage.SetFramesPerSecond(10)

    stage.GetRootLayer().Save()
    print(f"  dynamics.usda written: {path}")
    return path


# ---------------------------------------------------------------------------
# Layer 4: Analysis (time-sampled bio:rmsd)
# ---------------------------------------------------------------------------

def _create_analysis_layer(layer_dir: str) -> str:
    """Create analysis.usda — time-sampled bio:rmsd on /ABLComplex."""
    path = os.path.join(layer_dir, "analysis.usda")
    if os.path.exists(path):
        os.remove(path)

    stage = Usd.Stage.CreateNew(path)
    stage.GetRootLayer().documentation = (
        "Analysis layer: derived analysis results for /ABLComplex. "
        "Contributes time-sampled bio:rmsd (Å) with 20 synthetic samples. "
        "[assumption: synthetic values 1.0-3.0 Å; real values from MDAnalysis "
        "pipeline substituted when available]"
    )
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    root = stage.OverridePrim("/ABLComplex")
    stage.SetDefaultPrim(root)

    # Create time-sampled bio:rmsd attribute (float, units = Angstroms)
    rmsd_attr = root.CreateAttribute(
        "bio:rmsd", Sdf.ValueTypeNames.Float, custom=True
    )

    # 20 synthetic RMSD values at frames 0-19
    # Values simulate typical RMSD drift during MD equilibration (1.0-3.0 Å)
    import math
    rmsd_values = [
        1.02, 1.18, 1.35, 1.51, 1.67, 1.82, 1.95, 2.08, 2.21, 2.33,
        2.44, 2.54, 2.62, 2.68, 2.72, 2.74, 2.74, 2.73, 2.71, 2.69,
    ]
    for frame, val in enumerate(rmsd_values):
        rmsd_attr.Set(val, Usd.TimeCode(frame))

    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(19)

    stage.GetRootLayer().Save()
    print(f"  analysis.usda written: {path}")
    return path


# ---------------------------------------------------------------------------
# Layer 5: Review (Camera + annotations)
# ---------------------------------------------------------------------------

def _create_review_layer(layer_dir: str) -> str:
    """Create review.usda — UsdGeomCamera and annotation Xform."""
    path = os.path.join(layer_dir, "review.usda")
    if os.path.exists(path):
        os.remove(path)

    stage = Usd.Stage.CreateNew(path)
    stage.GetRootLayer().documentation = (
        "Review layer: camera setup and annotation prims for /ABLComplex. "
        "Defines ReviewCamera and ATPAnnotation for scientific review workflows."
    )
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    root = stage.OverridePrim("/ABLComplex")
    stage.SetDefaultPrim(root)

    # Review camera positioned to view the ABL kinase complex
    camera = UsdGeom.Camera.Define(stage, "/ABLComplex/ReviewCamera")
    camera.CreateFocalLengthAttr(35.0)
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateVerticalApertureAttr(15.2908)
    camera.CreateClippingRangeAttr(Gf.Vec2f(1.0, 10000.0))
    cam_xformable = UsdGeom.Xformable(camera.GetPrim())
    cam_xformable.AddTranslateOp().Set(Gf.Vec3d(0.0, 30.0, 150.0))

    # Annotation marker at ATP binding site
    annotation = UsdGeom.Xform.Define(stage, "/ABLComplex/ATPAnnotation")
    ann_prim = annotation.GetPrim()
    ann_text = ann_prim.CreateAttribute(
        "bio:annotationText", Sdf.ValueTypeNames.String, custom=True
    )
    ann_text.Set("ATP binding site")

    stage.GetRootLayer().Save()
    print(f"  review.usda written: {path}")
    return path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_all_layers(layer_dir: str) -> dict[str, str]:
    """
    Generate all five departmental layer files under layer_dir.

    Parameters
    ----------
    layer_dir : str
        Directory where the five .usda files will be written.
        Created if it does not exist.

    Returns
    -------
    dict mapping layer name -> absolute path written.
    """
    os.makedirs(layer_dir, exist_ok=True)

    # Compute relative paths from layer_dir to dependencies
    repo_root = os.path.dirname(os.path.dirname(layer_dir))
    assembly_abs = os.path.join(
        repo_root, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )
    clip_abs = os.path.join(
        repo_root, "output", "clips", "trajectory_clip.usda"
    )

    assembly_rel = os.path.relpath(assembly_abs, layer_dir)
    clip_rel = os.path.relpath(clip_abs, layer_dir)

    print(f"Creating departmental layers in: {layer_dir}")
    print(f"  assembly_rel = {assembly_rel}")
    print(f"  clip_rel     = {clip_rel}")

    paths = {}
    paths["biology"] = _create_biology_layer(layer_dir, assembly_rel)
    paths["protocol"] = _create_protocol_layer(layer_dir)
    paths["dynamics"] = _create_dynamics_layer(layer_dir, clip_rel)
    paths["analysis"] = _create_analysis_layer(layer_dir)
    paths["review"] = _create_review_layer(layer_dir)

    return paths


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    layer_dir = os.path.join(
        os.path.dirname(script_dir), "assets", "level6_departmental"
    )
    paths = create_all_layers(layer_dir)
    print("\nVerifying each layer opens cleanly...")
    for name, path in paths.items():
        stage = Usd.Stage.Open(path)
        errors = stage.GetCompositionErrors()
        if errors:
            print(f"  FAIL {name}: {errors}")
            sys.exit(1)
        else:
            print(f"  PASS {name}")
    print("\nAll 5 departmental layers created and verified.")
