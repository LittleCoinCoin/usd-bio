# Questions

## Q-001 Trajectory-dependent experiments (Exp 2 clip templates, future XTC work) need mdtraj, but mdtraj lives only in miniforge3 py3.12 while pxr lives only in the uv-managed cpython 3.11.14 (USD build's linked interpreter, which is EXTERNALLY-MANAGED/PEP668). No single interpreter currently has both. How should I unblock XTC reads under the USD interpreter? Options: (a) pip install mdtraj into the uv interpreter with --break-system-packages; (b) build a dedicated venv from cpython 3.11.14 with mdtraj installed + OpenUSD on PYTHONPATH; (c) keep them split and derive demo clips from already-committed trajectory data (no fresh XTC). I lean (b) as cleanest but it's a network install on your machine, so I'm not doing it unilaterally. Non-trajectory experiments (PointInstancer solvent, BasisCurves bonds, References, departmental layering) proceed without this.
*asked: cycle-1*
*priority: soft*
*answer:*

