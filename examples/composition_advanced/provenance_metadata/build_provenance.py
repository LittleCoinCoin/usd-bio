"""build_provenance.py — Step 2 of provenance_metadata experiment.

Builds assembly_with_provenance.usda: a stage whose /ABLComplex root prim
carries the six structured bio: provenance attributes defined in
provenance_schema.py, replacing the legacy flat ``bio:source`` string.

The six lineage fields authored here use representative ShinobuLab values:

  bio:sourcePdb       = "2HYY.pdb"
      ABL kinase crystal structure (representative PDB accession).
      [assumption: 2HYY is an ABL kinase structure used as the starting
       point for MD equilibration; exact accession not confirmed in this
       repo — execution agent may update if ShinobuLab uses a different one]

  bio:forceField      = "AMBER99SB-ILDN"
      Force field for protein + ligand parametrisation.
      [assumption: AMBER99SB-ILDN is a common choice for ABL MD studies;
       ShinobuLab's exact force field is not documented in this repo]

  bio:softwareName    = "GENESIS"
      Molecular dynamics engine used by ShinobuLab.
      [source: CLAUDE.md — "ShinobuLab MD simulations", known GENESIS user]

  bio:softwareVersion = "2.1.0"
      Version string at time of production run.
      [assumption: 2.1.0 is a plausible GENESIS release; actual version
       not confirmed in this repo]

  bio:simSettings     = JSON string with timestep_fs=2.0, temp_K=310,
                        pressure_bar=1.0
      Key production-MD settings representative of ABL+ATP equilibration
      at body temperature.
      [assumption: 2 fs timestep and 310 K / 1 bar NPT are standard;
       ShinobuLab's exact protocol is not fully documented here]

  bio:timestamp       = "2024-03-15T09:00:00+09:00"
      ISO-8601 datetime (JST) representative of ShinobuLab run date.
      [assumption: date is a plausible sentinel; actual run date unknown]

Stage settings:
  metersPerUnit = 1e-10  (Å coordinates)
  upAxis        = Y
  defaultPrim   = /ABLComplex

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 \\
        examples/composition_advanced/provenance_metadata/build_provenance.py
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

# Import provenance_schema from the same directory
sys.path.insert(0, _THIS_DIR)
from provenance_schema import apply_provenance_metadata  # noqa: E402

from pxr import Usd, UsdGeom, Sdf  # noqa: E402

# ---------------------------------------------------------------------------
# Representative ShinobuLab provenance record
# ---------------------------------------------------------------------------
SHINOBULAB_PROVENANCE = {
    "sourcePdb": "2HYY.pdb",
    "forceField": "AMBER99SB-ILDN",
    "softwareName": "GENESIS",
    "softwareVersion": "2.1.0",
    "simSettings": json.dumps(
        {"timestep_fs": 2.0, "temp_K": 310, "pressure_bar": 1.0}
    ),
    "timestamp": "2024-03-15T09:00:00+09:00",
}


def build_provenance_assembly(output_path: str) -> str:
    """Create assembly_with_provenance.usda with six structured bio: lineage fields.

    Parameters
    ----------
    output_path:
        Absolute path where the .usda file will be written.

    Returns
    -------
    str
        The output_path passed in, for caller convenience.

    Notes
    -----
    - /ABLComplex is an Xform prim with bio:systemName mirroring
      the production assembly root from 04_create_assembly.py.
    - All six provenance attributes are written via apply_provenance_metadata.
    - The legacy flat ``bio:source`` attribute is NOT authored here.
    - API: prim.CreateAttribute(name, Sdf.ValueTypeNames.String).Set(value)
      [source: context7 /websites/openusd_release — UsdPrim.CreateAttribute]
    """
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)

    # Stage-level metadata
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # 1 Å = 1e-10 m
    stage.SetMetadata(
        "comment",
        "ABL kinase + ATP assembly — structured provenance metadata demo"
    )

    # /ABLComplex root prim
    complex_xform = UsdGeom.Xform.Define(stage, "/ABLComplex")
    complex_prim = complex_xform.GetPrim()
    stage.SetDefaultPrim(complex_prim)

    # System-level metadata (unchanged from production assembly)
    complex_prim.CreateAttribute(
        "bio:systemName", Sdf.ValueTypeNames.String
    ).Set("ABL kinase + ATP complex")

    # Six structured provenance attributes — replaces flat bio:source
    apply_provenance_metadata(complex_prim, SHINOBULAB_PROVENANCE)

    stage.Save()
    print(f"Written: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    output_path = os.path.join(_THIS_DIR, "assembly_with_provenance.usda")
    build_provenance_assembly(output_path)
    print("Done.")
