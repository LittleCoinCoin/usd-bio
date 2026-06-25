#!/usr/bin/env python3
"""
Compose solvated assembly demo: protein (per-atom Xforms) + solvent (PointInstancer).

Creates output/solvent_demo.usda with:
  /SolvatedComplex             -- root Xform; defaultPrim
    /SolvatedComplex/Protein  -- references /ABLComplex (per-atom hierarchy)
    /SolvatedComplex/Solvent  -- references /Solvent (UsdGeomPointInstancer, 61k waters)

WHY references not SubLayers: isolates namespaces so protein (/ABLComplex) and
solvent (/Solvent) do not collide at the root level.

Prints METRIC lines for load time and memory RSS.

DEVIATION (PDB path): The leaf spec references $USDBIO_DATA_DIR/atp-complex-solv35.pdb
but the real file lives at $USDBIO_DATA_DIR/files/atp-complex-solv35.pdb.
"""

import os
import sys
import time
import resource

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_solvent_demo(
    output_path: str,
    assembly_path: str,
    solvent_path: str,
) -> str:
    """Compose protein assembly + solvent instancer into a single stage.

    Parameters
    ----------
    output_path : str
        Destination .usda file (e.g. output/solvent_demo.usda).
    assembly_path : str
        Absolute path to abl_kinase_complex.usda (provides /ABLComplex).
    solvent_path : str
        Absolute path to solvent_instancer.usda (provides /Solvent).

    Returns
    -------
    str
        output_path (for chaining).
    """
    if os.path.exists(output_path):
        os.remove(output_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # Angstrom = 1e-10 m
    stage.SetMetadata("comment",
        "Solvated ABL kinase complex — protein per-atom Xforms + solvent PointInstancer")

    # SubLayer both assets so their class prims and definitions are accessible.
    # References below draw from these sublayers by path.
    stage.GetRootLayer().subLayerPaths.append(assembly_path)
    stage.GetRootLayer().subLayerPaths.append(solvent_path)

    # =========================================================================
    # ROOT: /SolvatedComplex
    # =========================================================================
    root_path = "/SolvatedComplex"
    root_xform = UsdGeom.Xform.Define(stage, root_path)
    root_prim = root_xform.GetPrim()
    stage.SetDefaultPrim(root_prim)

    root_prim.CreateAttribute("bio:systemName", Sdf.ValueTypeNames.String).Set(
        "ABL kinase + ATP + explicit solvent")
    root_prim.CreateAttribute("bio:source", Sdf.ValueTypeNames.String).Set(
        "ShinobuLab ABL MD simulation — atp-complex-solv35.pdb")

    # =========================================================================
    # PROTEIN: /SolvatedComplex/Protein -> references /ABLComplex
    # WHY reference: keeps protein namespace isolated; /ABLComplex stays intact
    # Use stage.OverridePrim to avoid pre-typing the prim, letting the reference
    # deliver the full type (Xform for protein).
    # =========================================================================
    protein_path = f"{root_path}/Protein"
    protein_prim = stage.OverridePrim(protein_path)
    protein_prim.GetReferences().AddReference(
        assetPath="",  # in-stage reference (from sublayer)
        primPath=Sdf.Path("/ABLComplex"),
    )

    # =========================================================================
    # SOLVENT: /SolvatedComplex/Solvent -> references /Solvent
    # WHY reference: keeps instancer namespace isolated from protein root.
    # Use stage.OverridePrim (not Define) so the reference delivers the
    # PointInstancer type from the sublayer without Xform overriding it.
    # =========================================================================
    solvent_scene_path = f"{root_path}/Solvent"
    solvent_prim = stage.OverridePrim(solvent_scene_path)
    solvent_prim.GetReferences().AddReference(
        assetPath="",  # in-stage reference (from sublayer)
        primPath=Sdf.Path("/Solvent"),
    )

    stage.Save()

    print(f"Created: {output_path}")
    print(f"  SubLayers: {os.path.basename(assembly_path)}, {os.path.basename(solvent_path)}")
    print(f"  /SolvatedComplex/Protein -> /ABLComplex")
    print(f"  /SolvatedComplex/Solvent -> /Solvent (PointInstancer)")

    return output_path


def benchmark_stage(output_path: str) -> dict:
    """Open the composed stage and measure load time, memory, and variant latency.

    Prints METRIC lines for load_time_s and mem_rss_mb (required by leaf spec).

    Parameters
    ----------
    output_path : str
        Path to the .usda stage to benchmark.

    Returns
    -------
    dict
        Benchmark results keyed by metric name.
    """
    # --- Load time ---
    t0 = time.perf_counter()
    stage = Usd.Stage.Open(output_path)
    load_time_s = time.perf_counter() - t0

    # --- Memory (RSS) ---
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in bytes on macOS, kilobytes on Linux
    if sys.platform == "darwin":
        mem_rss_mb = usage.ru_maxrss / (1024 * 1024)
    else:
        mem_rss_mb = usage.ru_maxrss / 1024

    print(f"METRIC load_time_s={load_time_s:.4f}")
    print(f"METRIC mem_rss_mb={mem_rss_mb:.1f}")

    # --- Confirm key structure ---
    solvent_prim = stage.GetPrimAtPath("/SolvatedComplex/Solvent")
    instancer = UsdGeom.PointInstancer(solvent_prim)
    pos_val = instancer.GetPositionsAttr().Get() if instancer else None
    water_count = len(pos_val) if pos_val is not None else 0
    print(f"  Water instances: {water_count}")

    protein_chain_a = stage.GetPrimAtPath("/SolvatedComplex/Protein/Chain_A")
    print(f"  Protein Chain_A exists: {protein_chain_a.IsValid()}")

    # --- Mode-switch latency ---
    vset = solvent_prim.GetVariantSets().GetVariantSet("representation") \
        if solvent_prim.IsValid() else None

    if vset:
        print("  Mode-switch latency:")
        for mode in REPRESENTATIONS:
            t_mode = time.perf_counter()
            vset.SetVariantSelection(mode)
            latency_ms = (time.perf_counter() - t_mode) * 1000
            print(f"    {mode}: {latency_ms:.3f} ms")

    return {
        "load_time_s": load_time_s,
        "mem_rss_mb": mem_rss_mb,
        "water_count": water_count,
    }


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    assembly_path = os.path.abspath(os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    ))
    solvent_path = os.path.abspath(os.path.join(
        root_dir, "assets", "level5_solvent", "solvent_instancer.usda"
    ))
    output_path = os.path.join(output_dir, "solvent_demo.usda")

    for label, path in [("Assembly", assembly_path), ("Solvent instancer", solvent_path)]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    create_solvent_demo(output_path, assembly_path, solvent_path)
    benchmark_stage(output_path)
