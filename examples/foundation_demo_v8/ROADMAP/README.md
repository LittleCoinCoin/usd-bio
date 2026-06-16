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
| M1 | Parse ABL kinase PDB and create composed USD assembly | In Progress |
| M2 | Attach MD trajectory frames via Value Clips | Blocked on M1 |
| M3 | User guides and dev lesson documentation | Blocked on M1+M2 |

## Data Source

ABL kinase + ATP from ShinobuLab (`/Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/`):
- PDB: `files/atp-complex-solv35.pdb` -- 188,609 atoms total; 4,676 protein+ligand
- Trajectories: `analysis/0_traj/sort_traj_{1..10}.xtc` -- ~1.2 GB each

## Scope

Protein + ligand only. Solvent (183k atoms) deferred to future PointInstancer work.
