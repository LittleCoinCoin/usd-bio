# Questions

## Q-001 Trajectory-dependent experiments (Exp 2 clip templates, future XTC work) need mdtraj, but mdtraj lives only in miniforge3 py3.12 while pxr lives only in the uv-managed cpython 3.11.14 (USD build's linked interpreter, which is EXTERNALLY-MANAGED/PEP668). No single interpreter currently has both. How should I unblock XTC reads under the USD interpreter? Options: (a) pip install mdtraj into the uv interpreter with --break-system-packages; (b) build a dedicated venv from cpython 3.11.14 with mdtraj installed + OpenUSD on PYTHONPATH; (c) keep them split and derive demo clips from already-committed trajectory data (no fresh XTC). I lean (b) as cleanest but it's a network install on your machine, so I'm not doing it unilaterally. Non-trajectory experiments (PointInstancer solvent, BasisCurves bonds, References, departmental layering) proceed without this.
*asked: cycle-1*
*priority: soft*
*answer:* Already solved — use the existing forOUSD venv (~/Documents/src/AOUSD/forOUSD/bin/python3, Python 3.11.14) with PYTHONPATH from load_env.sh; it already has both pxr and mdtraj. — PI, 2026-07-03

## Q-002 In-scope backlog is complete and cycle-003 independently re-verified it (67/67 tests green, statuses truthful). Before close, one PI-approval-needing item remains: the architecture doc R03 __design__/openusd_for_research_architecture.md §2.1 (row S) / §7 claims the Specializes source overrides the instance, but this is empirically BACKWARDS (real USD: a Specializes base is always weaker than instance opinions; demonstrated + tested in specializes_arc). Correcting __design__/ is currently OUT of INTENT scope ('do not alter the architecture doc's decisions'). Do you want to (a) confirm-and-close as-is and fix the doc under a separate topic, or (b) expand this topic's scope to include the one-line doc correction before close? Separately, provenance_metadata uses representative sentinel values (2HYY.pdb / AMBER99SB-ILDN / GENESIS 2.1.0), not real ShinobuLab run metadata — acceptable for the prototype unless you want real lineage wired in.
*asked: cycle-3*
*priority: soft*
*answer:* 
- Confirming direction (b): Let's go through one more confirmation. Is the empirical observation in line with the documentation available via the `context7` MCP tools about `openusd`. If yes, then I authorize correcting our local documentation.
- I would prefer having runnable demo using Shinobu Lab's data so that we can discuss about these results live during meetings. — PI, 2026-07-04
I checked the content of the `output/` directory in the foundational example v8 and I think the usda trajectories are already using Shinobu Lab's trajectory data. But not necessarily the usdc? Elaborate about the flag you raised about the `provenance_metadata`. — PI, 2026-07-04
