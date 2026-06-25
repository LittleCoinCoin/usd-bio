#!/usr/bin/env python3
"""
Convert .usda (ASCII) USD layers to .usdc (binary Crate) format.

Uses Sdf.Layer.FindOrOpen(usda_path).Export(usdc_path) — the Sdf layer
Export method infers Crate format from the .usdc extension.

API confirmed: https://openusd.org/release/api/class_sdf_layer.html
  SdfLayer::Export(filename, comment="", args={}) -> bool

Usage (batch mode, from examples/foundation_demo_v8/):
    source load_env.sh
    python3 converters/usda_to_usdc.py

Output:
    METRIC file=<name> usda_bytes=<N> usdc_bytes=<N> ratio=<float>
    (one METRIC line per converted file)
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Sdf


def convert_layer(usda_path: str, usdc_path: str) -> dict:
    """Convert a single .usda layer to .usdc Crate format.

    Opens the source layer via Sdf.Layer.FindOrOpen and exports it to
    the destination path. The Sdf layer export infers Crate format from
    the .usdc file extension.

    Args:
        usda_path: Absolute path to the source .usda file.
        usdc_path: Absolute path for the output .usdc file.

    Returns:
        dict with keys: usda_bytes (int), usdc_bytes (int), ratio (float).
        ratio = usdc_bytes / usda_bytes (< 1.0 means binary is smaller).

    Raises:
        FileNotFoundError: If usda_path does not exist.
        RuntimeError: If layer open or export fails.
    """
    if not os.path.isfile(usda_path):
        raise FileNotFoundError(f"Source not found: {usda_path}")

    layer = Sdf.Layer.FindOrOpen(usda_path)
    if layer is None:
        raise RuntimeError(f"Sdf.Layer.FindOrOpen failed for: {usda_path}")

    # Ensure destination directory exists
    os.makedirs(os.path.dirname(os.path.abspath(usdc_path)), exist_ok=True)

    # Export to .usdc — extension drives Crate format selection
    ok = layer.Export(usdc_path)
    if not ok:
        raise RuntimeError(f"Layer.Export failed: {usda_path} -> {usdc_path}")

    usda_bytes = os.path.getsize(usda_path)
    usdc_bytes = os.path.getsize(usdc_path)
    ratio = usdc_bytes / usda_bytes if usda_bytes > 0 else float("inf")

    return {
        "usda_bytes": usda_bytes,
        "usdc_bytes": usdc_bytes,
        "ratio": ratio,
    }


def batch_convert(pairs: list) -> list:
    """Convert multiple (usda_path, usdc_path) pairs and print METRIC lines.

    Args:
        pairs: List of (usda_path, usdc_path) tuples.

    Returns:
        List of result dicts, one per converted file.
    """
    results = []
    for usda_path, usdc_path in pairs:
        name = os.path.basename(usda_path)
        print(f"Converting: {name} -> {os.path.basename(usdc_path)}")
        metrics = convert_layer(usda_path, usdc_path)
        print(
            f"METRIC file={name} "
            f"usda_bytes={metrics['usda_bytes']} "
            f"usdc_bytes={metrics['usdc_bytes']} "
            f"ratio={metrics['ratio']:.4f}"
        )
        results.append({"name": name, **metrics})
    return results


if __name__ == "__main__":
    # Default batch: convert the two primary artifacts
    assembly_usda = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )
    assembly_usdc = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usdc"
    )
    clip_usda = os.path.join(root_dir, "output", "clips", "trajectory_clip.usda")
    clip_usdc = os.path.join(root_dir, "output", "clips", "trajectory_clip.usdc")

    pairs = [
        (assembly_usda, assembly_usdc),
        (clip_usda, clip_usdc),
    ]

    print("usda_to_usdc — batch conversion to Crate binary format")
    print("=" * 60)
    results = batch_convert(pairs)
    print("=" * 60)
    print(f"Converted {len(results)} files.")
    for r in results:
        size_reduction = (1.0 - r["ratio"]) * 100
        print(
            f"  {r['name']}: {r['usda_bytes']:,} -> {r['usdc_bytes']:,} bytes "
            f"({size_reduction:.1f}% reduction)"
        )
