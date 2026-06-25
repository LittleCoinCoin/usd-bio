#!/usr/bin/env python3
"""
Compare SubLayer vs Reference approaches for element template loading.

Prints structured FINDING lines for downstream automation and CI grepping:
    FINDING category=<name> sublayer=<value> reference=<value>

Categories compared:
  encapsulation    — /_class_/C visible at stage root? (True/False)
  prim_count       — total prims after Traverse()
  file_size_bytes  — .usda file size on disk
  override_path_depth — length of path to carbon class prim (component count)

Design note:
    The SubLayer assembly pulls element_templates.usda in as a sublayer, so
    /_class_/C is globally visible at the root layer.  The Reference assembly
    pulls element_library.usda via AddReference onto /ElementLib, scoping the
    class hierarchy behind /ElementLib/_class_/C — invisible at the root.
    This is the fundamental encapsulation difference the experiment tests.
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd


def compare_assemblies(sublayer_path: str, refstyle_path: str) -> None:
    """
    Open both assemblies and print ≥4 structured FINDING lines comparing
    encapsulation, prim count, file size, and override path depth.

    Parameters
    ----------
    sublayer_path : str
        Path to abl_kinase_complex.usda (SubLayer style).
    refstyle_path : str
        Path to abl_kinase_complex_refstyle.usda (Reference style).
    """
    print("=== References vs SubLayers Comparison ===")
    print(f"SubLayer assembly : {sublayer_path}")
    print(f"Reference assembly: {refstyle_path}")
    print()

    stage_sub = Usd.Stage.Open(sublayer_path)
    stage_ref = Usd.Stage.Open(refstyle_path)

    # -------------------------------------------------------------------------
    # FINDING 1: encapsulation
    # Is /_class_/C (root-level element class) visible at the stage root?
    # SubLayer: YES  — element_templates.usda merged at root -> /_class_/C exists
    # Reference: NO  — element_library.usda scoped under /ElementLib
    # -------------------------------------------------------------------------
    sub_root_class_c = stage_sub.GetPrimAtPath("/_class_/C").IsValid()
    ref_root_class_c = stage_ref.GetPrimAtPath("/_class_/C").IsValid()
    print(
        f"FINDING category=encapsulation "
        f"sublayer={sub_root_class_c} "
        f"reference={ref_root_class_c}"
    )

    # -------------------------------------------------------------------------
    # FINDING 2: prim_count
    # Count all prims visible after composition (Traverse respects composition).
    # Reference style has additional /ElementLib hierarchy so count differs.
    # -------------------------------------------------------------------------
    sub_prim_count = sum(1 for _ in stage_sub.Traverse())
    ref_prim_count = sum(1 for _ in stage_ref.Traverse())
    print(
        f"FINDING category=prim_count "
        f"sublayer={sub_prim_count} "
        f"reference={ref_prim_count}"
    )

    # -------------------------------------------------------------------------
    # FINDING 3: file_size_bytes
    # On-disk file size of the root .usda.  Reference style embeds no class
    # prim definitions (they live in element_library.usda); SubLayer style
    # similarly delegates to element_templates.usda.  The difference reflects
    # only the structural delta (inherit paths, /ElementLib prim).
    # -------------------------------------------------------------------------
    sub_size = os.path.getsize(sublayer_path)
    ref_size = os.path.getsize(refstyle_path)
    print(
        f"FINDING category=file_size_bytes "
        f"sublayer={sub_size} "
        f"reference={ref_size}"
    )

    # -------------------------------------------------------------------------
    # FINDING 4: override_path_depth
    # Path component count to reach the carbon element class prim.
    # SubLayer: /_class_/C -> depth 2  (["_class_", "C"])
    # Reference: /ElementLib/_class_/C -> depth 3  (["ElementLib", "_class_", "C"])
    # Shorter SubLayer path = easier to override from any opinion in the stage.
    # Longer Reference path = explicit namespace; override requires knowing /ElementLib.
    # -------------------------------------------------------------------------
    sub_class_c_path = "/_class_/C"
    ref_class_c_path = "/ElementLib/_class_/C"

    # Path depth = number of path elements (components)
    def path_depth(path_str: str) -> int:
        """Count path elements via Sdf.Path.pathElementCount."""
        from pxr import Sdf
        return Sdf.Path(path_str).pathElementCount

    sub_depth = path_depth(sub_class_c_path)
    ref_depth = path_depth(ref_class_c_path)
    print(
        f"FINDING category=override_path_depth "
        f"sublayer={sub_depth} "
        f"reference={ref_depth}"
    )

    # -------------------------------------------------------------------------
    # FINDING 5: atom_count_parity
    # Count prims with bio:element attribute — should be equal in both styles
    # (same PDB source; only composition arc differs).
    # -------------------------------------------------------------------------
    def count_atoms(stage: Usd.Stage) -> int:
        """Count prims that carry a bio:element attribute."""
        return sum(
            1
            for p in stage.Traverse()
            if p.GetAttribute("bio:element").IsValid()
               and p.GetAttribute("bio:element").Get() is not None
        )

    sub_atoms = count_atoms(stage_sub)
    ref_atoms = count_atoms(stage_ref)
    print(
        f"FINDING category=atom_count_parity "
        f"sublayer={sub_atoms} "
        f"reference={ref_atoms}"
    )

    # -------------------------------------------------------------------------
    # Summary narrative
    # -------------------------------------------------------------------------
    print()
    print("--- Interpretation ---")
    print(
        f"encapsulation: SubLayer exposes /_class_/C at root ({sub_root_class_c}); "
        f"Reference hides it behind /ElementLib ({ref_root_class_c})."
    )
    print(
        f"prim_count: {sub_prim_count} (sublayer) vs {ref_prim_count} (reference). "
        f"Delta: {ref_prim_count - sub_prim_count:+d} (from /ElementLib namespace prims)."
    )
    print(
        f"file_size_bytes: {sub_size:,} (sublayer) vs {ref_size:,} (reference). "
        f"Delta: {ref_size - sub_size:+,} bytes."
    )
    print(
        f"override_path_depth: SubLayer class at depth {sub_depth} ({sub_class_c_path}); "
        f"Reference class at depth {ref_depth} ({ref_class_c_path})."
    )
    print(
        f"atom_count_parity: {sub_atoms} == {ref_atoms} -> "
        f"{'MATCH' if sub_atoms == ref_atoms else 'MISMATCH — investigate'}"
    )


if __name__ == "__main__":
    assets_dir = os.path.join(root_dir, "assets", "level4_assemblies")
    sublayer_path = os.path.join(assets_dir, "abl_kinase_complex.usda")
    refstyle_path = os.path.join(assets_dir, "abl_kinase_complex_refstyle.usda")

    for path in [sublayer_path, refstyle_path]:
        if not os.path.exists(path):
            print(f"ERROR: Assembly not found: {path}")
            print("Run the corresponding template script first.")
            sys.exit(1)

    compare_assemblies(sublayer_path, refstyle_path)
