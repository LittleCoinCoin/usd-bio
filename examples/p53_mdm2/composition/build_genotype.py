#!/usr/bin/env python3
"""
build_genotype.py -- Pipeline 2 Step 1: a Genotype (Perturbation) VariantSet
of p53-peptide (chain B) variants.

Generalized from foundation_demo_v8/composition_advanced/perturbation_variantset/
build_genotype.py (R00: generalize -- the geometry-swap-by-Reference mechanism
transfers directly; the T315I/ABL specifics are dropped).

What is carried (the reusable mechanism):
    A ``Genotype`` VariantSet on the complex root prim. For each variant a
    ``Reference`` arc is authored on the mutation-site prim(s), pointing at the
    geometry file that realises that genotype's residue at that site. Because
    each geometry file declares ``defaultPrim`` equal to the site prim name, the
    referenced residue composes onto the site prim. Default selection is the
    wild type.

What is generalized off ABL/T315I specifics:
    - v8 hard-codes ``/ABLKinase``, one site ``Res315``, and the two variants
      WildType/T315I. Here the root path is the ``root_path`` PARAMETER
      (default :data:`p53_env.DEFAULT_ROOT_PATH`, never an ABL literal), and the
      variants are DATA-DRIVEN from ``mutation_specs``: a WildType baseline plus
      one variant per single-point mutant.
    - v8 references pre-authored, hand-coordinated geometry stubs. Here the
      geometry files are generated from the REAL 1YCR coordinates parsed from
      the committed PDB. The alanine-mutant geometry is the wild-type residue
      truncated at C-beta (backbone N/CA/C/O + CB) -- the standard alanine-scan
      geometry, using only real atom coordinates (a SUBSET of the WT atoms),
      never fabricated positions.

Each variant also authors, inside its own edit context, the mutation identity
(``bio:mutation``, ``bio:mutationChain``, ``bio:genotypeLabel``) on the root
prim. Pipeline 2 Step 2 (ddmut_client) reads those off the composed stage to
query DDMut-PPI and write the ddG back into the same variant edit context.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from pxr import Usd, UsdGeom, Sdf, Gf

from p53_mdm2 import p53_env
from p53_mdm2.data import RESIDUES
from p53_mdm2.converters.pdb_parser import parse_pdb, DEFAULT_SOLVENT_IONS

# One-letter -> three-letter for the mutant residue identity written into the
# geometry stub (source-of-truth: the RESIDUES table, not a hard-coded map).
_ONE_TO_THREE = {v["one_letter"]: k for k, v in RESIDUES.items()}
# Atoms retained by an alanine truncation (backbone + C-beta). Real coords only.
_ALA_KEEP = ("N", "CA", "C", "O", "CB")


@dataclass
class MutationSpec:
    """A single-point mutation on the peptide chain.

    Attributes
    ----------
    res_seq:      residue sequence number in the source PDB (e.g. 19).
    mutant_one_letter: the one-letter code of the substituted residue (e.g. "A").
    """
    res_seq: int
    mutant_one_letter: str


# Default variant set for 1YCR: alanine scan of the p53 hydrophobic triad
# Phe19 / Trp23 / Leu26 -- the three residues that insert into the MDM2 cleft.
# The WT residue letter at each position is CONFIRMED against the PDB at build
# time (not hard-coded here), so the mutation codes below are validated, not
# asserted. [source: examples/p53_mdm2/data/structures/1ycr.pdb chain B]
DEFAULT_MUTATION_SPECS: Tuple[MutationSpec, ...] = (
    MutationSpec(19, "A"),   # F19A
    MutationSpec(23, "A"),   # W23A
    MutationSpec(26, "A"),   # L26A
)

WILDTYPE_LABEL = "WildType"


def _site_prim_name(res_name: str, res_seq: int) -> str:
    """USD-safe site prim name, e.g. Site_PHE_19."""
    return f"Site_{res_name}_{res_seq}"


def _geometry_filename(res_name: str, res_seq: int, genotype: str) -> str:
    """Relative geometry filename for a site under a given genotype."""
    return os.path.join("geometries", f"{genotype.lower()}_{res_name.lower()}_{res_seq}.usda")


def _write_residue_geometry(
    abs_path: str,
    site_prim_name: str,
    residue_name: str,
    atoms: List[Tuple[str, str, float, float, float]],
    comment: str,
) -> None:
    """Author a small geometry .usda whose defaultPrim is *site_prim_name*.

    Atoms are ``(name, element, x, y, z)`` in Ångström, all real coordinates.
    Element identity is inlined as ``bio:element`` (self-contained stub, per the
    v8 geometry-stub deviation); the referencing assembly resolves visuals via
    its own /_class_/ inherits when present.
    """
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    if os.path.exists(abs_path):
        os.remove(abs_path)
    stage = Usd.Stage.CreateNew(abs_path)
    stage.SetMetadata("comment", comment)
    stage.SetMetadata("metersPerUnit", p53_env.METERS_PER_UNIT)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    site = UsdGeom.Xform.Define(stage, f"/{site_prim_name}").GetPrim()
    stage.SetDefaultPrim(site)
    site.CreateAttribute("bio:residueName", Sdf.ValueTypeNames.Token).Set(residue_name)
    site.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(len(atoms))

    for name, element, x, y, z in atoms:
        safe = name.replace("'", "p").replace("*", "s")
        atom_xf = UsdGeom.Xform.Define(stage, f"/{site_prim_name}/Atom_{safe}")
        atom_prim = atom_xf.GetPrim()
        atom_prim.CreateAttribute("bio:atomName", Sdf.ValueTypeNames.Token).Set(name)
        atom_prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set(element)
        atom_xf.AddTranslateOp().Set(Gf.Vec3d(x, y, z))
    stage.GetRootLayer().Save()


def _residue_atoms(residue) -> List[Tuple[str, str, float, float, float]]:
    return [(a.name, a.element, a.x, a.y, a.z) for a in residue.atoms]


def _alanine_truncation(residue) -> List[Tuple[str, str, float, float, float]]:
    """Backbone + CB subset of the real residue -- the alanine-scan geometry."""
    keep = {a.name: a for a in residue.atoms if a.name in _ALA_KEEP}
    return [(keep[n].name, keep[n].element, keep[n].x, keep[n].y, keep[n].z)
            for n in _ALA_KEEP if n in keep]


def build_genotype_assembly(
    output_path: str,
    pdb_path: str,
    *,
    chain_id: str = "B",
    mutation_specs: Tuple[MutationSpec, ...] = DEFAULT_MUTATION_SPECS,
    root_path: Optional[str] = None,
    system_name: str = "p53-MDM2 complex (1YCR)",
) -> str:
    """Author a Genotype VariantSet assembly for peptide-chain variants.

    Args:
        output_path: destination .usda for the genotype assembly.
        pdb_path: source PDB (real coordinates for the site geometries).
        chain_id: peptide chain the mutations sit on (default "B", the p53
            peptide in 1YCR).
        mutation_specs: single-point mutations to author as variants (default
            the triad alanine scan). The WT residue letter at each position is
            validated against the PDB.
        root_path: USD root prim path (PARAMETER; default
            :data:`p53_env.DEFAULT_ROOT_PATH`).
        system_name: value for ``bio:systemName``.

    Returns:
        ``output_path``.

    Raises:
        ValueError: if a requested residue is absent from the chain, or if a
            spec would be a no-op mutation (mutant letter == wild-type letter).
    """
    if root_path is None:
        root_path = p53_env.DEFAULT_ROOT_PATH

    structure = parse_pdb(pdb_path, exclude_residues=DEFAULT_SOLVENT_IONS)
    if chain_id not in structure.chains:
        raise ValueError(f"chain {chain_id!r} not in structure {structure.chain_ids}")
    chain = structure.chains[chain_id]

    # Resolve each spec against the real chain: WT residue, mutation code, and
    # the two geometry variants (WT residue + alanine truncation).
    resolved = []
    for spec in mutation_specs:
        residue = chain.residues.get(spec.res_seq)
        if residue is None:
            raise ValueError(
                f"residue {spec.res_seq} not found in chain {chain_id}")
        wt_three = residue.name
        wt_one = RESIDUES.get(wt_three, {}).get("one_letter")
        if wt_one is None:
            raise ValueError(f"no one-letter code for residue {wt_three}")
        if spec.mutant_one_letter == wt_one:
            raise ValueError(
                f"no-op mutation at {spec.res_seq}: {wt_one}->{spec.mutant_one_letter}")
        mutation_code = f"{wt_one}{spec.res_seq}{spec.mutant_one_letter}"
        mut_three = _ONE_TO_THREE.get(spec.mutant_one_letter)
        if mut_three is None:
            raise ValueError(f"unknown mutant residue {spec.mutant_one_letter!r}")
        resolved.append({
            "seq": spec.res_seq,
            "wt_three": wt_three,
            "mut_three": mut_three,
            "code": mutation_code,
            "site_prim": _site_prim_name(wt_three, spec.res_seq),
            "residue": residue,
        })

    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    # --- 1. Emit geometry stubs (WT + alanine truncation) per site ---
    for r in resolved:
        wt_rel = _geometry_filename(r["wt_three"], r["seq"], WILDTYPE_LABEL)
        mut_rel = _geometry_filename(r["wt_three"], r["seq"], r["code"])
        _write_residue_geometry(
            os.path.join(out_dir, wt_rel), r["site_prim"], r["wt_three"],
            _residue_atoms(r["residue"]),
            f"Wild-type {r['wt_three']}{r['seq']} (chain {chain_id}) from "
            f"{os.path.basename(pdb_path)} -- real coordinates.")
        _write_residue_geometry(
            os.path.join(out_dir, mut_rel), r["site_prim"], r["mut_three"],
            _alanine_truncation(r["residue"]),
            f"{r['code']} alanine truncation (backbone+CB subset of real "
            f"{r['wt_three']}{r['seq']} coords) -- no fabricated positions.")
        r["wt_rel"] = wt_rel
        r["mut_rel"] = mut_rel

    # --- 2. Build the assembly stage ---
    if os.path.exists(output_path):
        os.remove(output_path)
    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, p53_env.METERS_PER_UNIT)
    stage.SetMetadata("comment",
                      f"{system_name} -- Genotype (Perturbation) VariantSet "
                      f"on chain {chain_id}")

    complex_prim = UsdGeom.Xform.Define(stage, root_path).GetPrim()
    stage.SetDefaultPrim(complex_prim)
    complex_prim.CreateAttribute("bio:systemName", Sdf.ValueTypeNames.String).Set(system_name)
    complex_prim.CreateAttribute("bio:sourceStructure", Sdf.ValueTypeNames.String).Set(
        os.path.basename(pdb_path))
    complex_prim.CreateAttribute("bio:mutationChain", Sdf.ValueTypeNames.Token).Set(chain_id)

    # Define the site prims (empty; the VariantSet fills them via References).
    for r in resolved:
        UsdGeom.Xform.Define(stage, f"{root_path}/{r['site_prim']}")

    genotype = complex_prim.GetVariantSets().AddVariantSet("Genotype")

    # WildType variant: every site references its WT geometry.
    genotype.AddVariant(WILDTYPE_LABEL)
    genotype.SetVariantSelection(WILDTYPE_LABEL)
    with genotype.GetVariantEditContext():
        complex_prim.CreateAttribute("bio:genotypeLabel", Sdf.ValueTypeNames.String).Set(WILDTYPE_LABEL)
        complex_prim.CreateAttribute("bio:mutation", Sdf.ValueTypeNames.String).Set("none")
        for r in resolved:
            site = stage.GetPrimAtPath(f"{root_path}/{r['site_prim']}")
            site.GetReferences().AddReference(r["wt_rel"])

    # One variant per single-point mutant: the mutated site references the
    # alanine geometry, all other sites stay WT.
    for target in resolved:
        genotype.AddVariant(target["code"])
        genotype.SetVariantSelection(target["code"])
        with genotype.GetVariantEditContext():
            complex_prim.CreateAttribute("bio:genotypeLabel", Sdf.ValueTypeNames.String).Set(target["code"])
            complex_prim.CreateAttribute("bio:mutation", Sdf.ValueTypeNames.String).Set(target["code"])
            for r in resolved:
                site = stage.GetPrimAtPath(f"{root_path}/{r['site_prim']}")
                rel = target["mut_rel"] if r is target else r["wt_rel"]
                site.GetReferences().AddReference(rel)

    genotype.SetVariantSelection(WILDTYPE_LABEL)  # default back to wild type
    stage.GetRootLayer().Save()

    print(f"[build_genotype] Written: {output_path}")
    print(f"  root: {root_path}  chain: {chain_id}")
    print(f"  variants: {[WILDTYPE_LABEL] + [r['code'] for r in resolved]}")
    return output_path


def default_output_path() -> str:
    """Canonical committed location for the genotype assembly artifact."""
    return os.path.join(_HERE, "p53_mdm2_genotype.usda")


if __name__ == "__main__":
    path = build_genotype_assembly(
        default_output_path(),
        p53_env.get_structure_path("1ycr.pdb"),
    )
    print(f"[build_genotype] Done. Inspect with:  usdcat --flatten {path}")
