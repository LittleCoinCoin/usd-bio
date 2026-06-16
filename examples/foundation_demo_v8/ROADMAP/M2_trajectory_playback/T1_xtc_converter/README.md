# M2.T1: XTC-to-Clips Converter

## Goal

Convert XTC trajectory frames into USD clip files.

## Creates

`converters/xtc_to_clips.py`

## Pre-conditions

- M1.T2 complete (assembly topology exists)
- mdtraj available in Python environment

## Success Gates

Clip .usda files contain time-sampled translate ops for all 4,676 atoms.

## Steps

| Step | Commit | Description |
|------|--------|-------------|
| S1 | `feat(converters): add XTC frame reader` | Use mdtraj to load XTC + PDB topology, select protein+ligand atoms, extract positions per frame. |
| S2 | `feat(converters): generate USD clip files from frames` | For a subset of frames (10-50), write clip .usda files containing only xformOp:translate time samples matching the assembly prim paths. |
| S3 | `test(converters): verify clip file structure` | Check clip files have correct prim paths, time samples, and position values. |

## Notes

- mdtraj must be installed: `pip install mdtraj`
- XTC files are ~1.2 GB each; only a subset of frames is extracted
- Per-atom translate ops may have perf implications at 4,676 atoms; monitor
