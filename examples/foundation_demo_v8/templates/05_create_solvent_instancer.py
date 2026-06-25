#!/usr/bin/env python3
"""
Create solvent PointInstancer layer from real PDB solvent coordinates.

Patterns applied:
- 02_inherits_arc.md: Prototype Water inherits from /_class_/Water class prim
- 03_variantsets_arc.md: representation VariantSet on /Solvent for mode switching
- UsdGeomPointInstancer for scalable solvent rendering (61k+ water molecules)

Output: assets/level5_solvent/solvent_instancer.usda
  /Solvent                  -- UsdGeomPointInstancer
    /Prototypes/Water       -- Xform prototype inheriting /_class_/Water
  protoIndices              -- VtIntArray (all zeros; single prototype)
  positions                 -- VtVec3fArray (one per water oxygen, Angstroms)

WHY SubLayer water_template: reuses /_class_/Water so all element class
properties (vdwRadius, CPK color, etc.) resolve via the existing inherit chain
without duplicating any authoring here.

DEVIATION (PDB path): The leaf spec references $USDBIO_DATA_DIR/atp-complex-solv35.pdb
but the real file lives at $USDBIO_DATA_DIR/files/atp-complex-solv35.pdb (files/
subdirectory). We use the real path here and document the deviation.
"""

import os
import sys

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Vt, Gf
from usdbio_env import get_data_dir
# Import parse_solvent directly from the module file, bypassing converters/__init__.py
# which imports xtc_to_clips (requires mdtraj, not available under the pxr interpreter).
import importlib.util as _ilu
import types as _types

_pdb_path = os.path.join(root_dir, "converters", "pdb_parser.py")
_spec = _ilu.spec_from_file_location("converters.pdb_parser", _pdb_path)
_pdb_module = _types.ModuleType("converters.pdb_parser")
_pdb_module.__spec__ = _spec
_pdb_module.__file__ = _pdb_path
_pdb_module.__package__ = "converters"
import sys as _sys
_sys.modules["converters.pdb_parser"] = _pdb_module
_spec.loader.exec_module(_pdb_module)
parse_solvent = _pdb_module.parse_solvent

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]

# DEVIATION: real path includes files/ subdir; leaf spec omits it
DEFAULT_PDB = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")


def create_solvent_instancer(
    output_path: str,
    water_template_path: str,
    solvent_positions: list,
) -> str:
    """Create a UsdGeomPointInstancer stage for solvent water molecules.

    Parameters
    ----------
    output_path : str
        Destination .usda file path.
    water_template_path : str
        Absolute path to water_template.usda (provides /_class_/Water).
    solvent_positions : list of (float, float, float)
        One (x, y, z) tuple per water oxygen atom, in Angstroms.

    Returns
    -------
    str
        output_path (for chaining).
    """
    if not solvent_positions:
        raise ValueError("solvent_positions is empty — parse_solvent returned no data")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # Angstrom = 1e-10 m
    stage.SetMetadata("comment",
        "Solvent PointInstancer — 61k water molecules from ShinobuLab ABL MD")

    # SubLayer water_template.usda to pull in /_class_/Water (and /_class_/ elements)
    # Use absolute path to avoid relpath fragility in sublayer lookups.
    stage.GetRootLayer().subLayerPaths.append(water_template_path)

    # =========================================================================
    # POINT INSTANCER ROOT
    # =========================================================================
    instancer_path = "/Solvent"
    instancer = UsdGeom.PointInstancer.Define(stage, instancer_path)
    instancer_prim = instancer.GetPrim()
    stage.SetDefaultPrim(instancer_prim)

    # Bio metadata
    instancer_prim.CreateAttribute("bio:moleculeType", Sdf.ValueTypeNames.Token).Set(
        "Water")
    instancer_prim.CreateAttribute("bio:instanceCount", Sdf.ValueTypeNames.Int).Set(
        len(solvent_positions))
    instancer_prim.CreateAttribute("bio:source", Sdf.ValueTypeNames.String).Set(
        "ShinobuLab ABL kinase MD simulation — atp-complex-solv35.pdb")

    # =========================================================================
    # PROTOTYPE: /Solvent/Prototypes/Water inheriting /_class_/Water
    # =========================================================================
    proto_parent_path = f"{instancer_path}/Prototypes"
    UsdGeom.Xform.Define(stage, proto_parent_path)

    water_proto_path = f"{proto_parent_path}/Water"
    water_proto_xform = UsdGeom.Xform.Define(stage, water_proto_path)
    water_proto_prim = water_proto_xform.GetPrim()

    # Inherit the Water class template — delivers visual properties + sub-atoms
    water_proto_prim.GetInherits().AddInherit("/_class_/Water")

    # Register the prototype with the instancer
    instancer.CreatePrototypesRel().SetTargets([Sdf.Path(water_proto_path)])

    # =========================================================================
    # POSITIONS AND PROTO INDICES
    # =========================================================================
    n = len(solvent_positions)

    positions_vt = Vt.Vec3fArray(n, [Gf.Vec3f(x, y, z) for x, y, z in solvent_positions])
    instancer.CreatePositionsAttr().Set(positions_vt)

    proto_indices_vt = Vt.IntArray(n, [0] * n)
    instancer.CreateProtoIndicesAttr().Set(proto_indices_vt)

    print(f"  PointInstancer /Solvent: {n} instances, 1 prototype")

    # =========================================================================
    # REPRESENTATION VARIANT SET on /Solvent
    # =========================================================================
    vset = instancer_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        vset.AddVariant(mode)
    # Default to points (fastest for 61k molecules)
    vset.SetVariantSelection("points")

    # =========================================================================
    # SAVE
    # =========================================================================
    stage.Save()
    print(f"Created: {output_path}")
    return output_path


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level5_solvent")
    os.makedirs(output_dir, exist_ok=True)

    water_template_path = os.path.abspath(os.path.join(
        root_dir, "assets", "level2_molecules", "water_template.usda"
    ))

    if not os.path.exists(water_template_path):
        print(f"ERROR: Water template not found: {water_template_path}")
        print("Run templates/02_create_water_template.py first")
        sys.exit(1)

    pdb_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDB
    if not os.path.exists(pdb_path):
        print(f"ERROR: PDB file not found: {pdb_path}")
        print("DEVIATION: leaf spec path omits files/ subdirectory.")
        print(f"  Expected real path: {DEFAULT_PDB}")
        sys.exit(1)

    print(f"Parsing solvent from: {pdb_path}")
    positions = parse_solvent(pdb_path)
    print(f"  Found {len(positions)} solvent oxygen atoms (water molecules)")

    if len(positions) < 61000:
        print(f"WARNING: expected >= 61000 positions, got {len(positions)}")

    output_path = os.path.join(output_dir, "solvent_instancer.usda")
    create_solvent_instancer(output_path, water_template_path, positions)

    # Consistency check: reopen and verify
    from pxr import UsdGeom as _UsdGeom
    s = Usd.Stage.Open(output_path)
    pi = _UsdGeom.PointInstancer(s.GetPrimAtPath("/Solvent"))
    assert pi, "/Solvent is not a valid UsdGeomPointInstancer"
    pos_attr = pi.GetPositionsAttr()
    pos_val = pos_attr.Get()
    assert pos_val is not None, "positions attribute has no value"
    assert len(pos_val) >= 61000, f"Expected >=61000 positions, got {len(pos_val)}"
    print(f"PASS: /Solvent PointInstancer with {len(pos_val)} positions verified")
