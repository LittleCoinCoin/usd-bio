"""build_specializes_demo.py — Step 2 of specializes_arc leaf.

Programmatically authors the cross-reference two-layer scene demonstrating
the observable contrast between Specializes and Inherits arcs across a
reference boundary, then reads back from a FRESH stage and prints observed
resolved values.

## Honesty note: flat single-file finding (prior pass cd7b1ea/a117222/f0832f7)

In a flat single-file context, BOTH Inherits and Specializes resolve to the
local opinion (9.99) — no observable contrast. Local (L) is the strongest
LIVERPS arc for both, so the local opinion always wins:
  /Atom_Inherits    -> 9.99  (Local > Inherits in LIVERPS)
  /Atom_Specializes -> 9.99  (Local > Specializes in LIVERPS)
The cross-reference boundary is what reveals the arc difference.

## The correct construction (cross-reference, two-layer scene)

INNER ASSET (asset_specializes.usda):
  /_class_/AtomBase    — base class: bio:vdwRadius = 1.70, bio:charge = 0.0
  /World/Atom_Specializes — specializes AtomBase, local bio:vdwRadius = 9.99
  /World/Atom_Inherits    — inherits AtomBase,    local bio:vdwRadius = 9.99
  (neither child has a local opinion on bio:charge)

OUTER ROOT (specializes_demo.usda):
  References asset_specializes.usda at /World
  Overrides /_class_/AtomBase: bio:vdwRadius = 2.00, bio:charge = -1.0

## Observed contrast (empirically verified, see print_resolved_values below)

bio:vdwRadius (both child prims have LOCAL opinion 9.99 in the inner asset):

  Atom_Specializes -> 9.99  LOCAL WINS
    The specialized prim's own local opinion ALWAYS overrides the base prim.
    Specializes is the WEAKEST arc in LIVERPS (I > R > S ordering means the
    referenced-layer local opinion is stronger than the outer base override
    delivered through the Specializes arc).
    [source: context7 /websites/openusd_release — Specializes glossary:
     'opinions expressed directly on the specialized prim always override
      those on the base prim, regardless of the referencing context.']

  Atom_Inherits -> 2.00  OUTER BASE OVERRIDE WINS
    Inherits (I) is STRONGER than References (R) in LIVERPS.
    The outer-layer opinion on the inherited class propagates through the
    reference boundary and overrides the referenced-layer local opinion (9.99).
    [source: context7 /websites/openusd_release — LIVERPS: I > R]

bio:charge (neither child has a local opinion):
  Both prims -> -1.0  (outer base override propagates to both, no local to block)

## API confirmed via context7 /websites/openusd_release
  - Usd.Stage.CreateNew(path) — create new stage (replaces existing)
  - Usd.Stage.Open(path) — open stage fresh (no prior state)
  - prim.GetSpecializes().AddSpecialize(Sdf.Path(...))
  - prim.GetInherits().AddInherit(Sdf.Path(...))
  - prim.GetReferences().AddReference(asset_path, prim_path)
  - stage.OverridePrim(path) — author an over prim in the edit target
  - attr.Get() — sample a composed attribute value
  - stage.GetCompositionErrors() — check for composition faults

Usage (from repo root):
    . ./load_env.sh
    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 \\
        examples/composition_advanced/specializes_arc/build_specializes_demo.py
"""

import os
import sys

from pxr import Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSET_PATH = os.path.join(_HERE, "asset_specializes.usda")
_DEMO_PATH = os.path.join(_HERE, "specializes_demo.usda")

# ---------------------------------------------------------------------------
# Inner asset: asset_specializes.usda
# ---------------------------------------------------------------------------

def build_asset_stage(asset_path: str) -> None:
    """Author asset_specializes.usda — the inner/referenced layer.

    Creates:
      /_class_/AtomBase       — base class: bio:vdwRadius=1.70, bio:charge=0.0
      /World/Atom_Specializes — specializes AtomBase, local bio:vdwRadius=9.99
      /World/Atom_Inherits    — inherits AtomBase,    local bio:vdwRadius=9.99
      (no local bio:charge on either child — resolves from base)

    [source: context7 /websites/openusd_release — UsdSpecializes, UsdInherits API docs]
    """
    stage = Usd.Stage.CreateNew(asset_path)
    stage.SetMetadata("metersPerUnit", 1e-10)
    stage.SetMetadata("upAxis", "Y")
    stage.GetRootLayer().documentation = (
        "asset_specializes.usda — inner/referenced asset layer for specializes_arc demo.\n"
        "Base class + Atom_Specializes + Atom_Inherits (both with local bio:vdwRadius=9.99).\n"
        "[source: build_specializes_demo.py]"
    )

    # /_class_ namespace (class specifier)
    stage.CreateClassPrim("/_class_")

    # /_class_/AtomBase
    base = stage.CreateClassPrim("/_class_/AtomBase")
    base.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(1.70)
    base.CreateAttribute("bio:charge", Sdf.ValueTypeNames.Float).Set(0.0)
    base.CreateAttribute("bio:elementSymbol", Sdf.ValueTypeNames.String).Set("C")

    # /World defaultPrim
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # /World/Atom_Specializes — specializes base, local vdwRadius=9.99, no local charge
    spe = UsdGeom.Xform.Define(stage, "/World/Atom_Specializes").GetPrim()
    # [source: context7 /websites/openusd_release — prim.GetSpecializes().AddSpecialize()]
    spe.GetSpecializes().AddSpecialize(Sdf.Path("/_class_/AtomBase"))
    spe.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(9.99)
    spe.CreateAttribute("bio:elementSymbol", Sdf.ValueTypeNames.String).Set("C")
    # NOTE: bio:charge deliberately omitted — no local opinion on this prim

    # /World/Atom_Inherits — inherits base, local vdwRadius=9.99, no local charge
    inh = UsdGeom.Xform.Define(stage, "/World/Atom_Inherits").GetPrim()
    # [source: context7 /websites/openusd_release — prim.GetInherits().AddInherit()]
    inh.GetInherits().AddInherit(Sdf.Path("/_class_/AtomBase"))
    inh.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(9.99)
    inh.CreateAttribute("bio:elementSymbol", Sdf.ValueTypeNames.String).Set("C")
    # NOTE: bio:charge deliberately omitted — no local opinion on this prim

    stage.Save()
    print(f"[build] Saved inner asset: {asset_path}")


# ---------------------------------------------------------------------------
# Outer root: specializes_demo.usda
# ---------------------------------------------------------------------------

def build_demo_stage(asset_path: str, demo_path: str) -> None:
    """Author specializes_demo.usda — the outer/root layer.

    References the inner asset at /World, then overrides the base class:
      /_class_/AtomBase.bio:vdwRadius = 2.00  (was 1.70 in asset)
      /_class_/AtomBase.bio:charge    = -1.0  (was 0.0 in asset)

    This override makes the Inherits vs Specializes contrast observable.

    [source: context7 /websites/openusd_release — stage.OverridePrim(),
     prim.GetReferences().AddReference()]
    """
    stage = Usd.Stage.CreateNew(demo_path)
    stage.SetMetadata("metersPerUnit", 1e-10)
    stage.SetMetadata("upAxis", "Y")
    stage.GetRootLayer().documentation = (
        "specializes_demo.usda — outer/root layer for specializes_arc demo.\n"
        "References asset_specializes.usda and overrides /_class_/AtomBase.\n"
        "[source: build_specializes_demo.py]"
    )

    # /World: references the inner asset
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    # [source: context7 /websites/openusd_release — prim.GetReferences().AddReference()]
    world.GetReferences().AddReference(asset_path, "/World")

    # Override /_class_/AtomBase in the root layer.
    # Via Inherits arc: this opinion (root-layer) wins over the referenced-layer
    #   local opinion (9.99) because Inherits > References in LIVERPS.
    # Via Specializes arc: this opinion does NOT override the specialized prim's
    #   local opinion (9.99) because local on the specialized prim always wins.
    # [source: context7 /websites/openusd_release — LIVERPS; Specializes glossary]
    base_over = stage.OverridePrim("/_class_/AtomBase")
    base_over.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(2.00)
    base_over.CreateAttribute("bio:charge", Sdf.ValueTypeNames.Float).Set(-1.0)

    stage.Save()
    print(f"[build] Saved outer demo: {demo_path}")


# ---------------------------------------------------------------------------
# Flat single-file check (documenting the prior finding)
# ---------------------------------------------------------------------------

def print_flat_context(asset_path: str) -> None:
    """Open the INNER asset alone and show both prims resolve 9.99.

    Flat single-file finding (prior pass, commits cd7b1ea/a117222/f0832f7):
    In a single-file context Local (L) wins over BOTH Inherits and Specializes —
    so there is NO observable contrast between the two arc types.
    [source: context7 /websites/openusd_release — LIVERPS: Local is strongest]
    [assumption: confirmed empirically in prior implementation pass]
    """
    stage = Usd.Stage.Open(asset_path)
    spe = stage.GetPrimAtPath("/World/Atom_Specializes")
    inh = stage.GetPrimAtPath("/World/Atom_Inherits")

    spe_r = spe.GetAttribute("bio:vdwRadius").Get()
    inh_r = inh.GetAttribute("bio:vdwRadius").Get()

    print()
    print("=== FLAT SINGLE-FILE CONTEXT (asset alone) ===")
    print(f"  Atom_Specializes bio:vdwRadius: {spe_r:.4f}  (local 9.99 wins, expected: ~9.99)")
    print(f"  Atom_Inherits    bio:vdwRadius: {inh_r:.4f}  (local 9.99 wins, expected: ~9.99)")
    print("  FINDING: No contrast — both arcs yield local opinion. Cross-reference needed.")
    return spe_r, inh_r


# ---------------------------------------------------------------------------
# Cross-reference read-back: the real contrast
# ---------------------------------------------------------------------------

def print_resolved_values(demo_path: str) -> dict:
    """Open specializes_demo.usda fresh and print resolved values showing the contrast.

    OBSERVED BEHAVIOR (cross-reference context):

    bio:vdwRadius (both child prims have LOCAL opinion 9.99 in the inner asset):
      Atom_Specializes -> 9.99  (local wins; specialized prim overrides base always)
      Atom_Inherits    -> 2.00  (outer base override wins; Inherits > References in LIVERPS)

    bio:charge (NEITHER child has a local opinion — resolves from base):
      Atom_Specializes -> -1.0  (outer base override propagates; no local to block)
      Atom_Inherits    -> -1.0  (same)

    [source: context7 /websites/openusd_release — LIVERPS, Specializes glossary]
    [source: empirical — this function's own output]
    """
    stage = Usd.Stage.Open(demo_path)

    errors = stage.GetCompositionErrors()
    if errors:
        print(f"[WARN] Composition errors: {errors}")

    base = stage.GetPrimAtPath("/_class_/AtomBase")
    spe = stage.GetPrimAtPath("/World/Atom_Specializes")
    inh = stage.GetPrimAtPath("/World/Atom_Inherits")

    base_r = base.GetAttribute("bio:vdwRadius").Get()
    base_c = base.GetAttribute("bio:charge").Get()
    spe_r = spe.GetAttribute("bio:vdwRadius").Get()
    spe_c = spe.GetAttribute("bio:charge").Get()
    inh_r = inh.GetAttribute("bio:vdwRadius").Get()
    inh_c = inh.GetAttribute("bio:charge").Get()

    print()
    print("=== CROSS-REFERENCE CONTEXT (specializes_demo.usda references asset) ===")
    print(f"  Base class    bio:vdwRadius: {base_r:.4f}  (root-layer override: 2.00)")
    print(f"  Base class    bio:charge:    {base_c:.4f}  (root-layer override: -1.00)")
    print()
    print(f"  Atom_Specializes bio:vdwRadius: {spe_r:.4f}  LOCAL WINS  (expected ~9.99)")
    print(f"    -> Specialized prim's local opinion overrides base (always, per USD docs).")
    print(f"    -> Specializes is WEAKEST arc; referenced-layer local > outer Specializes-arc base")
    print()
    print(f"  Atom_Inherits bio:vdwRadius: {inh_r:.4f}   BASE WINS   (expected ~2.00)")
    print(f"    -> Inherits (I) > References (R) in LIVERPS.")
    print(f"    -> Outer-layer base class override propagates through reference boundary.")
    print()
    print(f"  Atom_Specializes bio:charge: {spe_c:.4f}  (no local -> base override propagates)")
    print(f"  Atom_Inherits    bio:charge: {inh_c:.4f}  (no local -> base override propagates)")

    return {
        "base_vdwRadius": base_r,
        "base_charge": base_c,
        "spe_vdwRadius": spe_r,
        "spe_charge": spe_c,
        "inh_vdwRadius": inh_r,
        "inh_charge": inh_c,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Build scene files
    build_asset_stage(_ASSET_PATH)
    build_demo_stage(_ASSET_PATH, _DEMO_PATH)

    # Show flat single-file finding (prior pass)
    spe_flat, inh_flat = print_flat_context(_ASSET_PATH)

    # Show cross-reference contrast (the real demonstration)
    vals = print_resolved_values(_DEMO_PATH)

    # Sanity checks
    tol = 1e-2
    ok = True

    # Flat: both local (9.99)
    if abs(spe_flat - 9.99) > tol:
        print(f"[ERROR] Flat Specializes: expected ~9.99, got {spe_flat}")
        ok = False
    if abs(inh_flat - 9.99) > tol:
        print(f"[ERROR] Flat Inherits: expected ~9.99, got {inh_flat}")
        ok = False

    # Cross-reference: Specializes local wins (9.99), Inherits base wins (2.00)
    if abs(vals["spe_vdwRadius"] - 9.99) > tol:
        print(f"[ERROR] XRef Specializes vdwRadius: expected ~9.99 (local), got {vals['spe_vdwRadius']}")
        ok = False
    if abs(vals["inh_vdwRadius"] - 2.00) > tol:
        print(f"[ERROR] XRef Inherits vdwRadius: expected ~2.00 (base override), got {vals['inh_vdwRadius']}")
        ok = False
    if abs(vals["spe_charge"] - (-1.0)) > tol:
        print(f"[ERROR] XRef Specializes charge: expected ~-1.00, got {vals['spe_charge']}")
        ok = False
    if abs(vals["inh_charge"] - (-1.0)) > tol:
        print(f"[ERROR] XRef Inherits charge: expected ~-1.00, got {vals['inh_charge']}")
        ok = False

    print()
    if ok:
        print("[PASS] All cross-reference contrast checks passed.")
    else:
        print("[FAIL] One or more checks failed.")
    sys.exit(0 if ok else 1)
