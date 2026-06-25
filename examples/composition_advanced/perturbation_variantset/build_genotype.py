"""build_genotype.py — Step 2 of Exp 5 (perturbation_variantset).

Builds genotype_assembly.usda: a stage with prim /ABLKinase (Xform) carrying
a Genotype VariantSet (variants WildType / T315I). Inside each variant's edit
context a Reference arc is authored on /ABLKinase/Res315 pointing to the
matching geometry file. Default variant is WildType.

API signatures confirmed via context7 /websites/openusd_release:
  - variantSet.AddVariant(name) + SetVariantSelection(name)
  - with variantSet.GetVariantEditContext(): — context manager directing edits
    into the selected variant's namespace
  - res315_prim.GetReferences().AddReference(assetPath) — authors a Reference
    arc. Since each geometry file declares defaultPrim = "Res315", the
    referenced content is namespace-shifted onto /ABLKinase/Res315.

DEVIATION (Step 1 geometry stubs): element-class SubLayer back-reference was
skipped in the geometry files; element properties are inlined. The leaf spec
acknowledges this. [source: res315_wt.usda / res315_t315i.usda comment headers]
"""

import os
import sys

from pxr import Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GEOM_DIR = os.path.join(_THIS_DIR, "geometries")
_OUTPUT = os.path.join(_THIS_DIR, "genotype_assembly.usda")

_WT_GEOM = "geometries/res315_wt.usda"
_T315I_GEOM = "geometries/res315_t315i.usda"


def build_genotype_assembly(output_path: str = _OUTPUT) -> str:
    """Author genotype_assembly.usda with Genotype VariantSet + Reference arcs.

    For each Genotype variant, a Reference arc is authored on /ABLKinase/Res315
    pointing to the matching geometry file. Because each geometry file declares
    defaultPrim = "Res315", the referenced /Res315 prim (with bio:residueName
    and child atoms) composes onto /ABLKinase/Res315.

    Returns the path to the written file.
    """
    # Confirm geometry stubs are present
    for relpath in (_WT_GEOM, _T315I_GEOM):
        abspath = os.path.join(_THIS_DIR, relpath)
        if not os.path.exists(abspath):
            raise FileNotFoundError(f"Geometry stub missing: {abspath}")

    # Create a new in-memory stage
    stage = Usd.Stage.CreateNew(output_path)

    # Stage metadata
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # Define /ABLKinase as the root Xform representing the kinase complex
    kinase_prim = UsdGeom.Xform.Define(stage, "/ABLKinase").GetPrim()
    stage.SetDefaultPrim(kinase_prim)

    # Author provenance attribute: which residue is the mutation site
    kinase_prim.CreateAttribute(
        "bio:mutationSite", Sdf.ValueTypeNames.String
    ).Set("T315")

    # Define /ABLKinase/Res315 as the mutation-site prim. It starts empty;
    # the Genotype VariantSet adds a Reference to fill it with geometry.
    res315_prim = UsdGeom.Xform.Define(stage, "/ABLKinase/Res315").GetPrim()

    # Create the Genotype VariantSet
    genotype_vset = kinase_prim.GetVariantSets().AddVariantSet("Genotype")

    # --- WildType variant ---
    genotype_vset.AddVariant("WildType")
    genotype_vset.SetVariantSelection("WildType")
    with genotype_vset.GetVariantEditContext():
        # Reference geometry/res315_wt.usda onto /ABLKinase/Res315.
        # Relative path — layer-relative to genotype_assembly.usda so the
        # reference survives relocation of the directory.
        res315_prim.GetReferences().AddReference(_WT_GEOM)

    # --- T315I variant ---
    genotype_vset.AddVariant("T315I")
    genotype_vset.SetVariantSelection("T315I")
    with genotype_vset.GetVariantEditContext():
        res315_prim.GetReferences().AddReference(_T315I_GEOM)

    # Set default back to WildType
    genotype_vset.SetVariantSelection("WildType")

    stage.GetRootLayer().Save()
    print(f"[build_genotype] Written: {output_path}")
    return output_path


if __name__ == "__main__":
    path = build_genotype_assembly()
    print(f"[build_genotype] Done. Verify with:")
    print(f"  usdcat --flatten {path}")
