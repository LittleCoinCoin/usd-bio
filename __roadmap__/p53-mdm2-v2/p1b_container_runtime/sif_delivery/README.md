# SIF Delivery

## Context
This node exists at this depth for one reason: the `.sif` **does not exist yet**. Everything above it operates on a Docker image; everything here operates on a Singularity image built from that Docker image, and no work at this level can begin until conversion has produced the artifact. It consumes the three verified depth-1 leaves and produces the delivered `gromacs.sif` on the shared NFS home plus the evidence that it behaves identically to the Docker original.

## Goal
Convert the verified Docker image into `gromacs.sif` on the shared home, prove the conversion changed nothing observable, and reclaim the build scratch from the shared node.

## Pre-conditions
- [ ] `sass_portability_audit` green — converting an image whose SASS targets are wrong is wasted work
- [ ] `docker_gpu_smoke` green, or explicitly `blocked` with a recorded reason — so that a red `.sif` result is attributable to conversion rather than ambiguous
- [ ] `recipe_evidence_corrections` landed, since the rebuild consumes the corrected recipe
- [ ] `df -h /home` shows ≥ 30 G free, and `SINGULARITY_TMPDIR` / `SINGULARITY_CACHEDIR` / `TMPDIR` all redirected under `/home/eliott/p53mdm2/` so no build scratch lands on `/`

## Success Gates
- ⬜ `[run]` `gromacs.sif` present on `ts2:/export/home`, with the sha256 of both the intermediate tar and the `.sif` recorded
- ⬜ `[run]` `singularity inspect` reports `GromacsVer 2025.3` and `TargetSM 70;90`, and **no** `BuildStatus` key survives into the delivered artifact
- ⬜ `[run]` the rebuilt image's SASS summary and `gmx --version` block are byte-identical to the pre-correction capture — a build-reproducibility datum this campaign otherwise has none of
- ⬜ `[run]` `.sif` and Docker agree on GROMACS version, SIMD, CUDA runtime and GPU-support lines, and on minimisation `Potential Energy` to ≤ 1e-3 relative
- ⬜ `[run]` no `gromacs.tar`, no `gromacs-p53mdm2` image, and `/` free space recorded before and after

## Gotchas
- **This is why Route B works at all:** converting a `docker-archive://` has no `%post` to execute, so it needs no root and no `--fakeroot`. The absence of a subuid mapping — which killed the native `singularity build` — is irrelevant here.
- **Cleanup is destructive and comes last.** Deleting the tar and pruning the image removes the ability to re-run any earlier step in `convert_verify_cleanup`. Never reorder it earlier for tidiness.
- **The `.sif` must be written straight to shared home**, not built on `/` and moved: `/` is a 900 G filesystem carrying 213 G of other users' Docker layers, while the shared home has ~13 T free.

## Status
```mermaid
graph TD
    convert_verify_cleanup[Convert, Verify, Cleanup]:::inprogress
    crosscluster_readonly[Cross-Cluster Read-Only Checks]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `convert_verify_cleanup.md` | 📄 Leaf Task | 🔄 In Progress |
| `crosscluster_readonly/` | 📁 Directory | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `convert_verify_cleanup.md` | task/p53-mdm2-container-runtime | 1 | `2a1ffcf` convert+verify script; job 33 exit 0 in 17 min. Steps 1,2,3,5 done. **`gromacs.sif` delivered** on shared home, sha256 `1fc04f8b…81ac`, 5.4 GiB, labels truthful (no `BuildStatus`). Docker↔sif parity 1.39e-06. Cleanup reclaimed the 9.9 GB tar and deleted the image; `/` did not drop because releasing dangling layers needs a prune that would touch other users' images. Step 4 (parity assertions in `run_tests.py`) still open. Caveat: build equivalence was measured against a CACHED compile layer, so it shows the label removal changed no compiled content — NOT a cold-cache reproduction. |
