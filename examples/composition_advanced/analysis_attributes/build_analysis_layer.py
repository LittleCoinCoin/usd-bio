"""build_analysis_layer.py — Steps 1 and 2 of analysis_attributes experiment.

Builds analysis_layer.usda: a stage that carries time-sampled bio: analysis
attributes on appropriate prims, proving that derived analysis data (PMF, RMSD,
contact counts) can be first-class citizens in a usd-bio stage.

Attribute placement strategy (Step 1 — design_schema):
  - bio:rmsd (float, Å): time-sampled on /ABLComplex root.
    RMSD is a whole-system scalar sampled at each production-MD frame.
    Time axis: frame index 0..9 (10 sentinel frames).
    Value range: 1.2..3.8 Å linear ramp (representative of ABL equilibration).
    [assumption: RMSD range 1–5 Å is representative of ABL+ATP production-phase
     data from ShinobuLab REUS; exact values are synthetic sentinels]

  - bio:pmf (float, kcal/mol): time-sampled on /ABLComplex/Analysis/PMFProfile.
    PMF is a profile over the COM-distance reaction coordinate.
    Time axis: bin index 0..20 (21 sentinel bins for a ~5 Å span at 0.25 Å/bin).
    Value range: ~0 (well minimum at bin 10) to ~8 kcal/mol (flanks at bin 0/20).
    [assumption: PMF well depth ~8 kcal/mol and Gaussian shape are plausible
     sentinel for ABL+ATP; actual values require REUS analysis not done here]

  - bio:contactCount (int): time-sampled on /ABLComplex/Chain_A/Lig_ATP.
    Ligand-protein contact count per frame (cutoff ~4 Å, all heavy atoms).
    Time axis: frame index 0..9 (same as RMSD).
    Values: 12, 11, 13, 10, 14, 11, 12, 9, 13, 12 (integer time series).
    [assumption: 5-20 contact range is representative of ATP in ABL active site]

Sdf.ValueTypeNames.Float and Sdf.ValueTypeNames.Int confirmed for the above
attribute types via context7 /websites/openusd_release.

API confirmed via context7 /websites/openusd_release:
  - prim.CreateAttribute(name, Sdf.ValueTypeNames.Float, custom=True)
  - attr.Set(value, Usd.TimeCode(t))   — sets one time sample
  - attr.GetTimeSamples()              — returns list of authored time codes
  - Held interpolation (UsdInterpolationTypeHeld): values held constant between
    samples; sampling beyond the last authored time returns the last value.

Stage settings:
  metersPerUnit = 1e-10  (Å scale for atomic coordinates)
  upAxis = Y
  defaultPrim = /ABLComplex
  startTimeCode = 0
  endTimeCode = 20   (covers both RMSD/contact [0..9] and PMF [0..20])

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 \\
        examples/composition_advanced/analysis_attributes/build_analysis_layer.py
"""

import math
import os
import sys

from pxr import Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTPUT = os.path.join(_THIS_DIR, "analysis_layer.usda")


# ---------------------------------------------------------------------------
# Step 1: design_schema — attribute specifications
# ---------------------------------------------------------------------------

def design_schema() -> dict:
    """Return the attribute placement specification as a dict.

    Each key is a prim path string; each value is a dict describing the
    attribute name, Sdf type, time axis, and value series.

    This function is pure Python (no pxr calls) and serves as the
    authoritative design document for the experiment.
    """
    # PMF values: Gaussian well centred at bin 10, peak=0, flanks ~8 kcal/mol
    # f(bin) = 8 * ((bin - 10) / 10)^2 clamped to [0, 8]
    pmf_values = []
    for b in range(21):
        val = 8.0 * ((b - 10) / 10.0) ** 2
        pmf_values.append(round(val, 4))

    # RMSD values: linear ramp 1.2 → 3.8 over 10 frames (0..9)
    rmsd_values = [round(1.2 + (3.8 - 1.2) * i / 9.0, 4) for i in range(10)]

    # Contact count values: integer time series (frames 0..9)
    contact_values = [12, 11, 13, 10, 14, 11, 12, 9, 13, 12]

    return {
        "/ABLComplex": {
            "attr_name": "bio:rmsd",
            "sdf_type": "Float",
            "time_axis": list(range(10)),
            "values": rmsd_values,
            "unit": "Å",
            "description": "Whole-system backbone RMSD from reference frame",
        },
        "/ABLComplex/Analysis/PMFProfile": {
            "attr_name": "bio:pmf",
            "sdf_type": "Float",
            "time_axis": list(range(21)),
            "values": pmf_values,
            "unit": "kcal/mol",
            "description": "Potential of mean force vs COM-distance bin index",
        },
        "/ABLComplex/Chain_A/Lig_ATP": {
            "attr_name": "bio:contactCount",
            "sdf_type": "Int",
            "time_axis": list(range(10)),
            "values": contact_values,
            "unit": "count",
            "description": "Ligand-protein heavy-atom contacts within 4 Å per frame",
        },
    }


# ---------------------------------------------------------------------------
# Step 2: build_analysis_layer — author time-sampled attributes
# ---------------------------------------------------------------------------

def build_analysis_layer(output_path: str = _OUTPUT) -> str:
    """Author analysis_layer.usda with time-sampled bio: analysis attributes.

    Creates prims:
      /ABLComplex              (Xform) — carries bio:rmsd
      /ABLComplex/Analysis     (Xform) — analysis scope
      /ABLComplex/Analysis/PMFProfile  (Xform) — carries bio:pmf
      /ABLComplex/Chain_A      (Xform) — chain scope
      /ABLComplex/Chain_A/Lig_ATP      (Xform) — carries bio:contactCount

    Returns the path to the written file.
    """
    schema = design_schema()

    stage = Usd.Stage.CreateNew(output_path)

    # Stage metadata
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # Å scale
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetDefaultPrim(stage.DefinePrim("/ABLComplex"))
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(20)  # covers both RMSD/contact [0..9] and PMF [0..20]

    # Define hierarchy prims (all Xform for geometric compatibility)
    abl_complex = UsdGeom.Xform.Define(stage, "/ABLComplex")
    analysis_scope = UsdGeom.Xform.Define(stage, "/ABLComplex/Analysis")
    pmf_profile = UsdGeom.Xform.Define(stage, "/ABLComplex/Analysis/PMFProfile")
    chain_a = UsdGeom.Xform.Define(stage, "/ABLComplex/Chain_A")
    lig_atp = UsdGeom.Xform.Define(stage, "/ABLComplex/Chain_A/Lig_ATP")

    # Map prim path -> UsdPrim object
    prim_map = {
        "/ABLComplex": abl_complex.GetPrim(),
        "/ABLComplex/Analysis/PMFProfile": pmf_profile.GetPrim(),
        "/ABLComplex/Chain_A/Lig_ATP": lig_atp.GetPrim(),
    }

    # Author time-sampled attributes
    for prim_path, spec in schema.items():
        prim = prim_map[prim_path]
        attr_name = spec["attr_name"]
        sdf_type_name = spec["sdf_type"]

        # Resolve Sdf type
        if sdf_type_name == "Float":
            sdf_type = Sdf.ValueTypeNames.Float
        elif sdf_type_name == "Int":
            sdf_type = Sdf.ValueTypeNames.Int
        else:
            raise ValueError(f"Unknown sdf_type: {sdf_type_name}")

        attr = prim.CreateAttribute(attr_name, sdf_type, custom=True)

        # Set one time sample per entry in the time axis
        for t, val in zip(spec["time_axis"], spec["values"]):
            attr.Set(val, Usd.TimeCode(t))

        # Verify round-trip: GetTimeSamples must match authored times
        authored_times = attr.GetTimeSamples()
        expected_times = [float(t) for t in spec["time_axis"]]
        assert authored_times == expected_times, (
            f"[{prim_path}] GetTimeSamples() mismatch: "
            f"expected {expected_times}, got {authored_times}"
        )

    stage.Save()
    return output_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out = build_analysis_layer()
    print(f"Wrote: {out}")
    schema = design_schema()
    print(f"\nAuthored attributes:")
    for prim_path, spec in schema.items():
        print(f"  {prim_path}.{spec['attr_name']} "
              f"({spec['sdf_type']}, {len(spec['time_axis'])} samples, "
              f"unit={spec['unit']})")
