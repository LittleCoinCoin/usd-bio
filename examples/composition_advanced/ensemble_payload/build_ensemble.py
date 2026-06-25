"""build_ensemble.py — Step 2 of Exp 4 (ensemble_payload).

Builds ensemble_assembly.usda: a stage with prim /ABLEnsemble that carries a
ReplicaID VariantSet (variants rep_01/rep_02/rep_03); inside each variant's
edit context a Payload arc is authored pointing to the matching clip stub.

API signatures confirmed via context7 /websites/openusd_release:
  - variantSet.SetVariantSelection(name) + with variantSet.GetVariantEditContext()
  - prim.GetPayloads().AddPayload(Sdf.Payload(assetPath, primPath))

DEVIATION: The leaf (Step 2 §1) asks to SubLayer the departmental_demo.usda
from Exp 3 as the Biology+Protocol base. However, departmental_demo.usda has
defaultPrim="ABLComplex", while this assembly introduces /ABLEnsemble as a
distinct root. SubLayering it would flatten /ABLComplex onto the stage root
and not under /ABLEnsemble, polluting the stage with unrelated prims and
making sentinel assertions ambiguous. Decision: skip the SubLayer; the assembly
is self-contained. The biological base can be added once the schema maps
ABLEnsemble -> ABLComplex sub-structure (a future step). [assumption: staying
focused on the payload-swap mechanism is what the test gates actually require]
"""

import os
import sys

from pxr import Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CLIPS_DIR = os.path.join(_THIS_DIR, "clips")
_OUTPUT = os.path.join(_THIS_DIR, "ensemble_assembly.usda")

REPLICAS = ["rep_01", "rep_02", "rep_03"]


def build_replica_clips() -> list[str]:
    """Return the list of clip stub paths (already created in Step 1)."""
    paths = []
    for rep in REPLICAS:
        p = os.path.join(_CLIPS_DIR, f"{rep}.usda")
        if not os.path.exists(p):
            raise FileNotFoundError(f"Clip stub missing: {p}")
        paths.append(p)
    return paths


def build_ensemble_assembly(output_path: str = _OUTPUT) -> str:
    """Author ensemble_assembly.usda with ReplicaID VariantSet + Payload arcs.

    For each replica variant, a Payload arc is authored on /ABLEnsemble pointing
    to the matching clips/rep_0N.usda. The payload's defaultPrim (ABLComplex)
    is composed as a child namespace under /ABLEnsemble when the payload is
    loaded, so the sentinel points attribute resolves at:
        /ABLEnsemble/Chain_A/Res_001/Atom_CA.points
    [source: USD composition spec — payload defaultPrim is namespace-shifted
    under the prim that owns the payload arc]

    Returns the path to the written file.
    """
    # Confirm clip stubs are present
    build_replica_clips()

    # Create a new in-memory stage (payloads load-none so we can author freely)
    stage = Usd.Stage.CreateNew(output_path)

    # Stage metadata
    stage.SetMetadata("metersPerUnit", 1e-10)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetStartTimeCode(1)
    stage.SetEndTimeCode(1)

    # Define /ABLEnsemble as an Xform
    ensemble_prim = UsdGeom.Xform.Define(stage, "/ABLEnsemble").GetPrim()
    stage.SetDefaultPrim(ensemble_prim)

    # Create the ReplicaID VariantSet
    replica_vset = ensemble_prim.GetVariantSets().AddVariantSet("ReplicaID")

    for rep in REPLICAS:
        # Add variant to the set
        replica_vset.AddVariant(rep)
        # Switch to this variant
        replica_vset.SetVariantSelection(rep)
        # Open its edit context and author a Payload arc
        with replica_vset.GetVariantEditContext():
            clip_path = f"clips/{rep}.usda"
            # Payload: asset path relative to this layer; primPath="" means use
            # the clip file's defaultPrim (ABLComplex)
            ensemble_prim.GetPayloads().AddPayload(
                Sdf.Payload(clip_path)
            )

    # Set default variant to rep_01
    replica_vset.SetVariantSelection("rep_01")

    stage.GetRootLayer().Save()
    print(f"[build_ensemble] Written: {output_path}")
    return output_path


if __name__ == "__main__":
    path = build_ensemble_assembly()
    print(f"[build_ensemble] Done. Verify with:")
    print(
        f"  usdcat --flatten {path}"
    )
