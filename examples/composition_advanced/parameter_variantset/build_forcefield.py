"""build_forcefield.py — Step 2 of parameter_variantset leaf.

Builds forcefield_assembly.usda: a stage with prim /ABLFragment (Xform)
carrying a ForceField VariantSet (variants Amber99 / Charmm36). Inside each
variant's edit context a Reference arc is authored on /ABLFragment pointing to
the matching parameter overlay file. Default variant is Amber99.

## CRITICAL composition caveat — SubLayer-in-variant does NOT work

The leaf spec §3 originally suggested "add a SubLayer (prepend) inside each
variant's edit context." This was investigated and rejected:

  SubLayers are a layer-stack / stage-level construct, not prim-scoped. The
  USD composition glossary confirms: "Except for subLayers, all composition
  arcs target a specific prim in a LayerStack." SubLayers authored inside a
  GetVariantEditContext() context manager apply to the variant's layer spec,
  not to the stage's layer stack, and do NOT propagate the sublayer's opinions
  into the composed result.
  [source: context7 /websites/openusd_release, query "sublayer inside variant
  does not work composition arcs in variants reference payload"]

The chosen mechanism is Reference arcs, matching the pattern used in
perturbation_variantset (build_genotype.py lines 83, 88). A Reference arc is
authored on /ABLFragment inside each variant's edit context, pointing to the
matching parameter overlay file with an explicit primPath="/ABLFragment".
Because the param files author 'over' specs rooted at "ABLFragment", the
Reference brings those over-opinions into the variant namespace, causing
bio:partialCharge to resolve to the force-field-specific value when that
variant is selected.
[source: examples/composition_advanced/perturbation_variantset/build_genotype.py]

API signatures confirmed via context7 /websites/openusd_release:
  - variantSet.AddVariant(name) + SetVariantSelection(name)
  - with variantSet.GetVariantEditContext(): — directs edits into selected
    variant's namespace
  - prim.GetReferences().AddReference(assetPath, primPath=...) — authors a
    Reference arc with explicit prim target
"""

import os
import sys

from pxr import Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTPUT = os.path.join(_THIS_DIR, "forcefield_assembly.usda")

# Relative paths from the assembly file — layer-relative for portability
_AMBER99_PARAMS = "params/amber99.usda"
_CHARMM36_PARAMS = "params/charmm36.usda"

# Sentinel values (must match the param layer files for test assertions)
# [assumption: representative values from AMBER99SB-ILDN and CHARMM36m;
#  not from literal parameter files — see param layer comments]
AMBER_CHARGE_CA = -0.0518   # bio:partialCharge on Atom_CA under Amber99
CHARMM_CHARGE_CA = -0.02    # bio:partialCharge on Atom_CA under Charmm36
AMBER_CHARGE_N = -0.4157    # bio:partialCharge on Atom_N under Amber99
CHARMM_CHARGE_N = -0.47     # bio:partialCharge on Atom_N under Charmm36


def build_forcefield_assembly(output_path: str = _OUTPUT) -> str:
    """Author forcefield_assembly.usda with ForceField VariantSet + Reference arcs.

    For each ForceField variant, a Reference arc is authored on /ABLFragment
    pointing to the matching parameter overlay file (with explicit primPath so
    the 'over ABLFragment' opinions from the overlay compose onto /ABLFragment).

    Returns the path to the written file.
    """
    this_dir = os.path.dirname(os.path.abspath(output_path))

    # Confirm param layers are present
    for relpath in (_AMBER99_PARAMS, _CHARMM36_PARAMS):
        abspath = os.path.join(this_dir, relpath)
        if not os.path.exists(abspath):
            raise FileNotFoundError(f"Parameter overlay missing: {abspath}")

    # Create a new in-memory stage
    stage = Usd.Stage.CreateNew(output_path)

    # Stage metadata
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # -----------------------------------------------------------------------
    # Define /ABLFragment as root Xform (the assembly prim)
    # -----------------------------------------------------------------------
    frag_prim = UsdGeom.Xform.Define(stage, "/ABLFragment").GetPrim()
    stage.SetDefaultPrim(frag_prim)

    # -----------------------------------------------------------------------
    # Author minimal atom hierarchy with default local opinions
    # Chain_A / Res_001 / Atom_N and Atom_CA
    # Default values are placeholders; ForceField variants override them.
    # -----------------------------------------------------------------------
    chain_a = UsdGeom.Xform.Define(stage, "/ABLFragment/Chain_A").GetPrim()
    res_001 = UsdGeom.Xform.Define(stage, "/ABLFragment/Chain_A/Res_001").GetPrim()

    atom_n = UsdGeom.Xform.Define(stage, "/ABLFragment/Chain_A/Res_001/Atom_N").GetPrim()
    atom_n.CreateAttribute("bio:atomName", Sdf.ValueTypeNames.Token).Set("N")
    atom_n.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set("N")
    # NOTE: bio:partialCharge and bio:ljRadius are intentionally NOT authored
    # as local opinions here. Local opinions win over Reference arcs (LIVERPS:
    # Local > References). If we set them to 0.0 locally, the ForceField
    # variant References cannot override them. Values come entirely from the
    # variant-scoped Reference arcs pointing to the param overlay files.

    atom_ca = UsdGeom.Xform.Define(stage, "/ABLFragment/Chain_A/Res_001/Atom_CA").GetPrim()
    atom_ca.CreateAttribute("bio:atomName", Sdf.ValueTypeNames.Token).Set("CA")
    atom_ca.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set("C")
    # Same: bio:partialCharge and bio:ljRadius come from ForceField variant References.

    # -----------------------------------------------------------------------
    # ForceField VariantSet
    # -----------------------------------------------------------------------
    ff_vset = frag_prim.GetVariantSets().AddVariantSet("ForceField")

    # --- Amber99 variant ---
    ff_vset.AddVariant("Amber99")
    ff_vset.SetVariantSelection("Amber99")
    with ff_vset.GetVariantEditContext():
        # Author bio:forceFieldName as provenance metadata on /ABLFragment
        frag_prim.CreateAttribute(
            "bio:forceFieldName", Sdf.ValueTypeNames.String
        ).Set("AMBER99SB-ILDN")
        # Add a Reference arc on /ABLFragment pointing to the AMBER parameter
        # overlay, with explicit primPath="/ABLFragment" so the over-opinions
        # from the overlay (rooted at "ABLFragment") compose onto this prim.
        frag_prim.GetReferences().AddReference(
            _AMBER99_PARAMS, primPath=Sdf.Path("/ABLFragment")
        )

    # --- Charmm36 variant ---
    ff_vset.AddVariant("Charmm36")
    ff_vset.SetVariantSelection("Charmm36")
    with ff_vset.GetVariantEditContext():
        # Author bio:forceFieldName as provenance metadata
        frag_prim.CreateAttribute(
            "bio:forceFieldName", Sdf.ValueTypeNames.String
        ).Set("CHARMM36m")
        # Add a Reference arc to the CHARMM parameter overlay
        frag_prim.GetReferences().AddReference(
            _CHARMM36_PARAMS, primPath=Sdf.Path("/ABLFragment")
        )

    # Set default back to Amber99
    ff_vset.SetVariantSelection("Amber99")

    stage.GetRootLayer().Save()
    print(f"[build_forcefield] Written: {output_path}")
    return output_path


if __name__ == "__main__":
    path = build_forcefield_assembly()
    print(f"[build_forcefield] Done. Verify with:")
    print(f"  usdcat --flatten {path}")
