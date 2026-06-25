#!/usr/bin/env python3
"""
Create a reference-friendly element library asset.

Pattern applied:
- 02_inherits_arc.md: class prims for element templates
- 03_variantsets_arc.md: representation VariantSet on each element class
- 08_schemas_attributes.md: bio: namespace for scientific metadata

Design intent:
    Unlike element_templates.usda (a sublayer with no default prim), this file
    wraps all element classes under a root Xform /_ElementLibrary and declares
    it as the default prim.  When a caller writes:

        prim.GetReferences().AddReference("element_library.usda")

    USD maps the asset's default prim (/_ElementLibrary) to ``prim``'s path.
    The class hierarchy is then reachable as
    <prim_path>/_ElementLibrary/_class_/<Symbol> instead of /_class_/<Symbol>
    at the stage root — making the dependency explicit and namespace-encapsulated.
"""

import os
import sys

# Setup paths — script may be run from any working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf
from data import ELEMENTS, get_scaled_radius


REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_element_library(output_path: str) -> str:
    """
    Generate a self-contained reference-friendly element library asset.

    Parameters
    ----------
    output_path : str
        Absolute path to write the .usda file.

    Returns
    -------
    str
        The output_path, for chaining / verification.
    """
    # Clean start
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)   # Ångström
    stage.SetMetadata(
        "comment",
        "Reference-friendly element library. Default prim /_ElementLibrary "
        "wraps element class prims for AddReference use.",
    )

    # =========================================================================
    # ROOT WRAPPER — this becomes the default prim so AddReference callers
    # get the entire class hierarchy under their chosen namespace path.
    # =========================================================================
    lib_root = UsdGeom.Xform.Define(stage, "/_ElementLibrary")
    lib_root_prim = lib_root.GetPrim()
    stage.SetDefaultPrim(lib_root_prim)

    # Container class prim under the wrapper — mirrors /_class_/ from
    # element_templates.usda so the class hierarchy is structurally identical.
    stage.CreateClassPrim("/_ElementLibrary/_class_")

    for symbol, data in ELEMENTS.items():
        class_path = f"/_ElementLibrary/_class_/{symbol}"

        # Create class prim (abstract; not instanced directly)
        class_prim = stage.CreateClassPrim(class_path)

        # =====================================================================
        # SCIENTIFIC METADATA (bio: namespace) — identical to element_templates
        # =====================================================================
        class_prim.CreateAttribute("bio:symbol", Sdf.ValueTypeNames.Token).Set(symbol)
        class_prim.CreateAttribute("bio:name", Sdf.ValueTypeNames.String).Set(data["name"])
        class_prim.CreateAttribute(
            "bio:atomicNumber", Sdf.ValueTypeNames.Int
        ).Set(data["atomic_number"])
        class_prim.CreateAttribute(
            "bio:atomicMass", Sdf.ValueTypeNames.Float
        ).Set(data["atomic_mass"])
        class_prim.CreateAttribute(
            "bio:vdwRadius", Sdf.ValueTypeNames.Float
        ).Set(data["vdw_radius"])
        class_prim.CreateAttribute(
            "bio:covalentRadius", Sdf.ValueTypeNames.Float
        ).Set(data["covalent_radius"])
        class_prim.CreateAttribute(
            "bio:electronegativity", Sdf.ValueTypeNames.Float
        ).Set(data["electronegativity"])
        class_prim.CreateAttribute(
            "bio:notes", Sdf.ValueTypeNames.String
        ).Set(data["bio_notes"])
        cpk = Gf.Vec3f(*data["cpk_color"])
        class_prim.CreateAttribute(
            "bio:cpkColor", Sdf.ValueTypeNames.Color3f
        ).Set(cpk)

        # =====================================================================
        # VARIANT SET: representation — same geometry as element_templates
        # =====================================================================
        vset = class_prim.GetVariantSets().AddVariantSet("representation")

        for mode in REPRESENTATIONS:
            vset.AddVariant(mode)

        for mode in REPRESENTATIONS:
            vset.SetVariantSelection(mode)
            with vset.GetVariantEditContext():
                sphere_path = f"{class_path}/Sphere"
                sphere = UsdGeom.Sphere.Define(stage, sphere_path)

                radius = get_scaled_radius(symbol, mode)
                sphere.CreateRadiusAttr(radius)

                color = Gf.Vec3f(*data["cpk_color"])
                sphere.CreateDisplayColorAttr([color])
                sphere.CreateExtentAttr(
                    [(-radius, -radius, -radius), (radius, radius, radius)]
                )

        vset.ClearVariantSelection()

    stage.Save()
    print(f"Created: {output_path}")
    print(f"  Elements: {len(ELEMENTS)}")
    print(f"  Default prim: /_ElementLibrary")
    print(f"  Representations: {REPRESENTATIONS}")
    return output_path


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level1_elements")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "element_library.usda")
    create_element_library(output_path)

    # -------------------------------------------------------------------------
    # Consistency check: default prim valid and /_ElementLibrary/_class_/C exists
    # -------------------------------------------------------------------------
    from pxr import Usd as _Usd
    s = _Usd.Stage.Open(output_path)
    dp = s.GetDefaultPrim()
    assert dp.IsValid(), f"Default prim is not valid: {dp}"
    assert dp.GetPath() == Sdf.Path(
        "/_ElementLibrary"
    ), f"Unexpected default prim path: {dp.GetPath()}"
    c_prim = s.GetPrimAtPath("/_ElementLibrary/_class_/C")
    assert c_prim.IsValid(), "/_ElementLibrary/_class_/C not found"
    vdw = c_prim.GetAttribute("bio:vdwRadius").Get()
    assert vdw is not None and vdw > 0, f"bio:vdwRadius invalid: {vdw}"
    print("PASS — default prim valid, /_ElementLibrary/_class_/C found, bio:vdwRadius OK")
