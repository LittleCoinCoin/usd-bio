# M3.T2: Dev Lessons

## Goal

Technical documents on USD composition tricks learned from this work.

## Creates

- `docs/12_pdb_to_usd_patterns.md`
- `docs/13_value_clips_for_trajectories.md`

## Pre-conditions

- M1 complete (for PDB-to-USD patterns)
- M2 complete (for trajectory patterns)

## Steps

| Step | Commit | Description |
|------|--------|-------------|
| S1 | `docs(dev): add PDB-to-USD composition patterns` | `docs/12_pdb_to_usd_patterns.md` -- PDB hierarchy to USD prims, element inheritance at scale, residue naming edge cases, VariantSet cascade performance |
| S2 | `docs(dev): add Value Clips trajectory patterns` | `docs/13_value_clips_for_trajectories.md` -- topology/clip separation, per-atom vs points-array tradeoffs, UsdClipsAPI setup, XTC frame extraction |

## Each Doc Covers

- The problem: what's hard about mapping scientific data to USD
- The pattern: concrete code showing the solution
- The gotchas: what broke, what's non-obvious, what to watch out for
- Scaling considerations: what changes at 5k atoms vs 50k vs 500k
