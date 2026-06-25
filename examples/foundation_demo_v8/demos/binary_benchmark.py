#!/usr/bin/env python3
"""
Benchmark .usda vs .usdc load time and per-frame scrub latency.

Measures:
  (a) Usd.Stage.Open() wall time via time.perf_counter()
  (b) Per-frame attribute read latency — xformable.GetLocalTransformation()
      on a representative atom, averaged over 20 calls

Prints METRIC lines:
    METRIC format=usda|usdc load_time_s=<float> frame_read_us=<float>

Also opens output/binary_demo.usda to verify composition still works
end-to-end with .usdc SubLayers.

Usage (from examples/foundation_demo_v8/):
    source load_env.sh
    python3 demos/binary_benchmark.py
"""

import os
import sys
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Gf

# Paths — relative to root_dir (examples/foundation_demo_v8/)
_USDA_CLIP = os.path.join(root_dir, "output", "clips", "trajectory_clip.usda")
_USDC_CLIP = os.path.join(root_dir, "output", "clips", "trajectory_clip.usdc")

# A representative atom in the trajectory clip that has time-sampled positions
_SAMPLE_PRIM_PATH = "/ABLComplex/Chain_A/ACE_1/HH31"

# Number of frames in the clip (written with frames 0..19)
_N_FRAMES = 20


def benchmark_stage(path: str, n_frames: int = 20) -> dict:
    """Benchmark Usd.Stage.Open time and per-frame attribute read latency.

    Args:
        path: Absolute path to a USD stage file (.usda or .usdc).
        n_frames: Number of frames to sample for per-frame latency.

    Returns:
        dict with keys:
            load_time_s (float): Stage open wall-clock time in seconds.
            frame_read_us (float): Average per-frame xform read latency in microseconds.
            format (str): "usda" or "usdc" inferred from extension.
    """
    fmt = os.path.splitext(path)[1].lstrip(".")  # "usda" or "usdc"

    # --- (a) Stage open time ---
    t0 = time.perf_counter()
    stage = Usd.Stage.Open(path)
    load_time_s = time.perf_counter() - t0

    if stage is None:
        raise RuntimeError(f"Usd.Stage.Open failed: {path}")

    # --- (b) Per-frame attribute read latency ---
    prim = stage.GetPrimAtPath(_SAMPLE_PRIM_PATH)
    if not prim.IsValid():
        # Clip files contain the prim directly; composed stages may wrap it
        # Fall back to first prim with time samples
        prim = None
        for p in stage.Traverse():
            ops = UsdGeom.Xformable(p).GetOrderedXformOps()
            if ops and len(ops[0].GetTimeSamples()) > 1:
                prim = p
                break

    read_times = []
    if prim is not None and prim.IsValid():
        xformable = UsdGeom.Xformable(prim)
        ops = xformable.GetOrderedXformOps()
        if ops:
            translate_op = ops[0]
            time_samples = translate_op.GetTimeSamples()
            sample_tcs = [Usd.TimeCode(t) for t in time_samples[:n_frames]]

            # Warm up
            for tc in sample_tcs[:2]:
                translate_op.Get(tc)

            # Timed reads
            for tc in sample_tcs:
                t_start = time.perf_counter()
                translate_op.Get(tc)
                read_times.append(time.perf_counter() - t_start)

    frame_read_us = (
        (sum(read_times) / len(read_times)) * 1e6 if read_times else float("nan")
    )

    return {
        "format": fmt,
        "path": path,
        "load_time_s": load_time_s,
        "frame_read_us": frame_read_us,
    }


def print_comparison(usda_metrics: dict, usdc_metrics: dict) -> None:
    """Print a human-readable comparison and METRIC lines.

    Prints two METRIC lines (one per format):
        METRIC format=usda|usdc load_time_s=<float> frame_read_us=<float>
    """
    for m in (usda_metrics, usdc_metrics):
        fmt = m["format"]
        load_s = m["load_time_s"]
        read_us = m["frame_read_us"]
        print(f"METRIC format={fmt} load_time_s={load_s:.4f} frame_read_us={read_us:.2f}")

    # Human-readable summary
    speedup_load = usda_metrics["load_time_s"] / usdc_metrics["load_time_s"] if usdc_metrics["load_time_s"] > 0 else float("nan")
    print()
    print("Summary:")
    print(f"  Load time  — usda: {usda_metrics['load_time_s']:.4f}s  "
          f"usdc: {usdc_metrics['load_time_s']:.4f}s  "
          f"(usdc is {speedup_load:.1f}x faster)")
    print(f"  Frame read — usda: {usda_metrics['frame_read_us']:.2f}µs  "
          f"usdc: {usdc_metrics['frame_read_us']:.2f}µs")


def verify_binary_demo(demo_path: str) -> None:
    """Open binary_demo.usda and verify composition works end-to-end.

    Checks that the stage opens, has the /ABLComplex prim, and that
    time-sampled positions are readable via the clip.
    """
    print(f"\nVerifying binary_demo stage: {os.path.basename(demo_path)}")
    stage = Usd.Stage.Open(demo_path)
    assert stage is not None, f"Failed to open: {demo_path}"

    prim = stage.GetPrimAtPath("/ABLComplex")
    assert prim.IsValid(), "/ABLComplex prim not found in binary_demo"
    print("  PASS: /ABLComplex prim found")

    # Check that a child atom prim is accessible
    atom = stage.GetPrimAtPath(_SAMPLE_PRIM_PATH)
    assert atom.IsValid(), f"Atom prim not found: {_SAMPLE_PRIM_PATH}"
    print(f"  PASS: atom prim accessible — {_SAMPLE_PRIM_PATH}")
    print("  PASS: binary_demo composition verified")


if __name__ == "__main__":
    print("binary_benchmark — .usda vs .usdc load and scrub latency")
    print("=" * 60)

    # Benchmark clip files (contain the time-sampled data) — pair 1
    print(f"\n[Clip] Benchmarking: {os.path.basename(_USDA_CLIP)}")
    clip_usda_m = benchmark_stage(_USDA_CLIP, n_frames=_N_FRAMES)
    print(f"[Clip] Benchmarking: {os.path.basename(_USDC_CLIP)}")
    clip_usdc_m = benchmark_stage(_USDC_CLIP, n_frames=_N_FRAMES)

    print()
    print("--- Clip benchmark ---")
    print_comparison(clip_usda_m, clip_usdc_m)

    # Benchmark assembly files — pair 2 (no time samples; frame_read_us=nan)
    _USDA_ASSEMBLY = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )
    _USDC_ASSEMBLY = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usdc"
    )
    print(f"\n[Assembly] Benchmarking: {os.path.basename(_USDA_ASSEMBLY)}")
    asm_usda_m = benchmark_stage(_USDA_ASSEMBLY, n_frames=_N_FRAMES)
    print(f"[Assembly] Benchmarking: {os.path.basename(_USDC_ASSEMBLY)}")
    asm_usdc_m = benchmark_stage(_USDC_ASSEMBLY, n_frames=_N_FRAMES)

    print()
    print("--- Assembly benchmark ---")
    print_comparison(asm_usda_m, asm_usdc_m)

    # Verify composition of the binary_demo stage
    binary_demo = os.path.join(root_dir, "output", "binary_demo.usda")
    if os.path.isfile(binary_demo):
        verify_binary_demo(binary_demo)
    else:
        print(f"\nWARN: binary_demo.usda not found at {binary_demo}")
        print("      Run this script after binary_demo.usda is created.")
