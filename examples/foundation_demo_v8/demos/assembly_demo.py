#!/usr/bin/env python3
"""
Demo: ABL kinase + ATP assembly with variant switching.

SubLayers the assembly from level4_assemblies and sets defaultPrim directly
to /ABLComplex (the biological geometry root), authoring the top-level
`representation` selection ON that same prim for coordinated visualization
mode switching across the entire complex.

WHY NOT a /World wrapper prim (this demo's pattern before the v8-gap-closure
representation-variant-cascade fix): USD variant-selection fallthrough only
cascades a GetVariantEditContext()-scoped edit to prims that are NAMESPACE
DESCENDANTS of the variant-owning prim in the same composed site. /World and
/ABLComplex were SIBLINGS here -- /ABLComplex arrived via SubLayer at its own
top-level path, not as a child of /World -- so `with world_vset.
GetVariantEditContext(): complex_prim...SetVariantSelection(mode)` did not
scope an opinion under /World's variant at all; each loop iteration instead
wrote an unconditional `over "ABLComplex" { variants = {...} }` block at
/ABLComplex's own path, and only the LAST iteration's value survived
composition (verified directly in output/assembly_demo.usda: the emitted
/World variant blocks are empty `{}`, and /ABLComplex carries one
unconditional `variants = { representation = "ballstick" }` opinion,
regardless of which /World variant is selected in usdview). See
demos/curves_demo.py and demos/departmental_demo.py for the same defect
diagnosed and fixed the same way, and
tests/test_representation_cascade.py for the falsification-resistant
read-back proof. Canonical fix (USD model-hierarchy convention, confirmed
via context7 /websites/openusd_release docs on GetVariantEditContext/
EditTarget scoping): make the actual geometry root ALSO the defaultPrim and
the variant owner, so there is no dispatcher indirection to go stale. No
/World prim is created; there is nothing else on this stage that would need
a shared parent.
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]
DEFAULT_MODE = "balls"


def create_assembly_demo(output_path: str, assembly_path: str):
    """Create demo scene with ABL kinase assembly."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)

    # SubLayer the assembly (brings in /ABLComplex and /_class_/)
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(assembly_path, os.path.dirname(output_path))
    )

    # defaultPrim = the actual geometry root. /ABLComplex's own
    # `representation` VariantSet (declared by templates/04_create_assembly.py's
    # cascade) is the single selection surface for this stage -- no proxy
    # dispatcher prim needed, so there is nothing that can go stale relative
    # to it.
    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    stage.SetDefaultPrim(complex_prim)

    complex_prim.GetVariantSets().GetVariantSet(
        "representation").SetVariantSelection(DEFAULT_MODE)

    stage.Save()

    print(f"Created: {output_path}")
    print(f"Representations: {REPRESENTATIONS}")
    print(f"Default: {DEFAULT_MODE} (defaultPrim=/ABLComplex)")

    # Structural assertions (fresh re-open, not generator in-memory state)
    reopen = Usd.Stage.Open(output_path)
    default_prim = reopen.GetDefaultPrim()
    assert default_prim.IsValid() and default_prim.GetPath() == Sdf.Path("/ABLComplex"), (
        f"Expected defaultPrim=/ABLComplex, got "
        f"{default_prim.GetPath() if default_prim else None}"
    )
    default_sel = default_prim.GetVariantSets().GetVariantSet(
        "representation").GetVariantSelection()
    assert default_sel == DEFAULT_MODE, (
        f"Expected default representation selection {DEFAULT_MODE!r}, got {default_sel!r}"
    )
    print(f"  PASS: fresh-open default representation resolves to {default_sel!r}")

    assert reopen.GetPrimAtPath("/World").IsValid() is False, (
        "Decorative /World dispatcher prim should no longer be authored"
    )
    print("  PASS: no decorative /World dispatcher prim on stage")

    sample_atom = reopen.GetPrimAtPath("/ABLComplex/Chain_A/ACE_1/HH31")
    assert sample_atom.IsValid(), "sample atom prim missing"
    atom_children = sample_atom.GetChildren()
    assert len(atom_children) == 1, (
        f"Expected exactly 1 gprim child on fresh-open atom ({DEFAULT_MODE} default), "
        f"got {len(atom_children)}: {[c.GetName() for c in atom_children]}"
    )
    print(f"  PASS: fresh-open sample atom has exactly 1 child gprim "
          f"({atom_children[0].GetTypeName()})")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    assembly_path = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )

    if not os.path.exists(assembly_path):
        print(f"ERROR: Assembly not found: {assembly_path}")
        print("Run templates/04_create_assembly.py first")
        sys.exit(1)

    output_path = os.path.join(output_dir, "assembly_demo.usda")
    create_assembly_demo(output_path, assembly_path)
    print(f"\nView with: usdview {output_path}")
