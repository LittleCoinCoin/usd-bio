"""
Layer 3 -- programmatic USD read-back tests (falsification-resistant).

Opens the committed topology artifact FRESH with Usd.Stage.Open and asserts
that USD's composition engine resolved values that match expectations
INDEPENDENTLY re-derived from the 1YCR PDB file (via
``independent_pdb.raw_pdb_expectations`` -- a different code path from the
production parser) and from the source-of-truth ``p53_mdm2.data`` tables.
Never compared against the generator's in-memory state (R00 anti-tautology).

Per-run 1YCR fixtures (dataset counts live here, NEVER in library code):
    total atoms 818, chain A (MDM2) 705, chain B (p53 peptide) 113, elements
    {C,N,O,S}, hydrophobic triad Phe19/Trp23/Leu26 on chain B.
These anchors are cross-checked against the runtime re-derivation so a shared
bug in both parse paths cannot pass silently.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
for _p in (_HERE, _PKG_PARENT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p53_mdm2.data import ELEMENTS, get_scaled_radius
from p53_mdm2 import p53_env
from p53_mdm2.converters.pdb_parser import DEFAULT_SOLVENT_IONS
from independent_pdb import raw_pdb_expectations  # sibling module (bare import)

# --- per-run 1YCR fixtures (test-side; deliberately NOT in library code) ---
FIX_TOTAL_ATOMS = 818
FIX_CHAIN_ATOMS = {"A": 705, "B": 113}
FIX_ELEMENTS = {"C", "N", "O", "S"}
FIX_TRIAD = {19: "PHE", 23: "TRP", 26: "LEU"}  # chain B hydrophobic triad
_EXPECTED_VARIANTS = tuple(p53_env.DEFAULT_REPRESENTATIONS)


@dataclass
class ReadbackResult:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _atom_prims(stage):
    for prim in stage.Traverse():
        a = prim.GetAttribute("bio:element")
        if a.IsValid() and a.Get():
            yield prim


def assert_counts_match_independent_pdb(stage_path, pdb_path) -> ReadbackResult:
    """USD atom/chain counts + elements == independent PDB re-derivation."""
    errors, detail = [], {}
    exp = raw_pdb_expectations(pdb_path, exclude_residues=DEFAULT_SOLVENT_IONS)

    # Anchor the independent derivation against the stated fixtures first, so a
    # shared parse bug cannot make USD and re-derivation agree on a wrong value.
    if exp.total_atoms != FIX_TOTAL_ATOMS:
        errors.append(
            f"independent PDB re-derivation total_atoms={exp.total_atoms} != "
            f"fixture {FIX_TOTAL_ATOMS} (1YCR changed or parse drifted)")
    if exp.chain_atom_counts != FIX_CHAIN_ATOMS:
        errors.append(
            f"independent chain counts {exp.chain_atom_counts} != {FIX_CHAIN_ATOMS}")
    if exp.elements != FIX_ELEMENTS:
        errors.append(f"independent elements {exp.elements} != {FIX_ELEMENTS}")

    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    detail["root"] = str(root.GetPath())

    # bio:atomCount metadata vs. independent total
    meta_count = root.GetAttribute("bio:atomCount").Get()
    detail["bio:atomCount"] = meta_count
    if meta_count != exp.total_atoms:
        errors.append(
            f"root bio:atomCount={meta_count} != independent {exp.total_atoms}")

    # actual atom-prim count vs. independent total
    usd_atoms = list(_atom_prims(stage))
    detail["usd_atom_prims"] = len(usd_atoms)
    if len(usd_atoms) != exp.total_atoms:
        errors.append(
            f"USD atom-prim count={len(usd_atoms)} != independent {exp.total_atoms}")

    # chain count + per-chain atom counts
    chain_prims = [p for p in stage.Traverse()
                   if p.GetAttribute("bio:chainID").IsValid()
                   and p.GetAttribute("bio:chainID").Get() is not None]
    usd_chain_atoms = {}
    for cp in chain_prims:
        cid = str(cp.GetAttribute("bio:chainID").Get())
        usd_chain_atoms[cid] = cp.GetAttribute("bio:atomCount").Get()
    detail["usd_chain_atoms"] = usd_chain_atoms
    if usd_chain_atoms != exp.chain_atom_counts:
        errors.append(
            f"USD per-chain atom counts {usd_chain_atoms} != "
            f"independent {exp.chain_atom_counts}")

    # element set present in USD atoms vs. independent
    usd_elems = {str(p.GetAttribute("bio:element").Get()) for p in usd_atoms}
    detail["usd_elements"] = sorted(usd_elems)
    if usd_elems != exp.elements:
        errors.append(f"USD elements {usd_elems} != independent {exp.elements}")

    return ReadbackResult(
        "counts_match_independent_pdb", not errors, errors, detail)


def assert_element_assignment_and_inherits(stage_path, pdb_path) -> ReadbackResult:
    """Each atom's bio:element matches the independent PDB element, and every
    atom inherits /_class_/<that element> (composition resolved from source)."""
    errors, detail = [], {}
    exp = raw_pdb_expectations(pdb_path, exclude_residues=DEFAULT_SOLVENT_IONS)
    stage = Usd.Stage.Open(stage_path)

    mismatches, inherit_fail, checked = 0, 0, 0
    for prim in _atom_prims(stage):
        checked += 1
        symbol = str(prim.GetAttribute("bio:element").Get())
        atom_name = str(prim.GetAttribute("bio:atomName").Get())
        # residue seq lives on the parent residue prim
        rseq_prim = prim.GetParent().GetAttribute("bio:residueSeq")
        rseq = rseq_prim.Get() if rseq_prim.IsValid() else None
        # chain id: walk up to the ancestor carrying bio:chainID
        chain_id = None
        anc = prim.GetParent()
        while anc.IsValid():
            ca = anc.GetAttribute("bio:chainID")
            if ca.IsValid() and ca.Get() is not None:
                chain_id = str(ca.Get())
                break
            anc = anc.GetParent()

        key = (chain_id, rseq, atom_name)
        indep_elem = exp.atom_elements.get(key)
        if indep_elem is not None and indep_elem != symbol:
            mismatches += 1
            if mismatches <= 5:
                errors.append(
                    f"{prim.GetPath()}: bio:element={symbol} != independent "
                    f"{indep_elem} for {key}")
        if symbol not in ELEMENTS:
            errors.append(f"{prim.GetPath()}: element {symbol} not in ELEMENTS")
        inh = [str(p) for p in prim.GetInherits().GetAllDirectInherits()]
        if f"/_class_/{symbol}" not in inh:
            inherit_fail += 1
            if inherit_fail <= 5:
                errors.append(f"{prim.GetPath()}: missing inherit /_class_/{symbol}")

    detail.update(atoms_checked=checked, element_mismatches=mismatches,
                  inherit_failures=inherit_fail)
    return ReadbackResult(
        "element_assignment_and_inherits", not errors, errors, detail)


def assert_triad_present(stage_path) -> ReadbackResult:
    """The p53 hydrophobic triad Phe19/Trp23/Leu26 resolves on chain B."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    found = {}
    for prim in stage.Traverse():
        rn = prim.GetAttribute("bio:residueName")
        rs = prim.GetAttribute("bio:residueSeq")
        if not (rn.IsValid() and rs.IsValid() and rs.Get() is not None):
            continue
        seq = rs.Get()
        if seq in FIX_TRIAD:
            # confirm it is under chain B
            anc = prim.GetParent()
            cid = None
            while anc.IsValid():
                ca = anc.GetAttribute("bio:chainID")
                if ca.IsValid() and ca.Get() is not None:
                    cid = str(ca.Get()); break
                anc = anc.GetParent()
            if cid == "B":
                found[seq] = str(rn.Get())
    detail["found"] = found
    for seq, name in FIX_TRIAD.items():
        if found.get(seq) != name:
            errors.append(f"triad residue {name}{seq} not found on chain B (got {found.get(seq)})")
    return ReadbackResult("triad_present", not errors, errors, detail)


def assert_variant_cascade(stage_path) -> ReadbackResult:
    """Switching representation on a sample atom yields the 4 scientifically
    scaled radii from the source ELEMENTS table (composition resolved via the
    inherited element class)."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    sample = None
    for prim in _atom_prims(stage):
        if str(prim.GetAttribute("bio:element").Get()) == "C":
            sample = prim
            break
    if sample is None:
        return ReadbackResult("variant_cascade", False, ["no carbon atom found"])
    detail["sample"] = str(sample.GetPath())
    vs = sample.GetVariantSets().GetVariantSet("representation")
    observed = {}
    for mode in _EXPECTED_VARIANTS:
        vs.SetVariantSelection(mode)
        sph = stage.GetPrimAtPath(str(sample.GetPath()) + "/Sphere")
        if not sph.IsValid():
            errors.append(f"variant '{mode}': inherited Sphere did not compose")
            continue
        r = sph.GetAttribute("radius").Get()
        observed[mode] = r
        expected = get_scaled_radius("C", mode)  # source-of-truth
        if r is None or abs(r - expected) > 1e-3:
            errors.append(f"variant '{mode}': radius {r} != source {expected}")
    detail["observed_radii"] = observed
    if len(set(observed.values())) < len(observed):
        errors.append(f"variant radii not all distinct: {observed}")
    return ReadbackResult("variant_cascade", not errors, errors, detail)


def run(stage_path: str, pdb_path: str) -> list:
    if not os.path.isfile(stage_path):
        return [ReadbackResult("stage_exists", False, [f"Not found: {stage_path}"])]
    return [
        assert_counts_match_independent_pdb(stage_path, pdb_path),
        assert_element_assignment_and_inherits(stage_path, pdb_path),
        assert_triad_present(stage_path),
        assert_variant_cascade(stage_path),
    ]
