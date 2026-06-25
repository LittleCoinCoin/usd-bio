# ROADMAP: foundation_demo_v8 -- Assembly + Trajectory

## Milestone Dependency Graph

```
M1 Assembly from Real Data
  |
  |---> M2 Trajectory Playback    (depends on M1: needs topology USD)
  |
  +---> M3 Documentation          (depends on M1; M3.T2 also depends on M2)
```

M1 is the foundation. M2 and M3 can partially overlap once M1 is complete.

## Milestones

| Milestone | Objective | Status |
|-----------|-----------|--------|
| M1 | Parse ABL kinase PDB and create composed USD assembly | Complete — `output/assembly_demo.usda` |
| M2 | Attach MD trajectory frames via Value Clips | Complete — `output/trajectory_demo.usda` |
| M3 | User guides and dev lesson documentation | Complete — see `examples/foundation_demo_v8/` docs |

## Data Source

> Set `USDBIO_DATA_DIR` to the root of your ShinobuLab data directory before running any script.

ABL kinase + ATP from ShinobuLab (`$USDBIO_DATA_DIR/`):
- PDB: `files/atp-complex-solv35.pdb` -- 188,609 atoms total; 4,676 protein+ligand
- Trajectories: `analysis/0_traj/sort_traj_{1..10}.xtc` -- ~1.2 GB each

## Scope

Protein + ligand only. Solvent (183k atoms) deferred to future PointInstancer work.
