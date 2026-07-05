# Trajectory Demo User Guide

## What This Demo Is

This demo plays back a **molecular dynamics trajectory** of the ABL kinase + ATP complex. The 20 frames are extracted from a production MD simulation (ShinobuLab, ~70,000 frames total in the first trajectory file alone). Scrubbing the usdview timeline shows the protein moving as it would during the simulation.

The key principle: **topology is static, positions are dynamic** -- exactly the same separation USD uses for animated characters in film production. The protein's hierarchy, element colors, metadata, and variant definitions don't change between frames. Only the 3D positions of the 4,676 atoms change over time.

## How to Run

```bash
# From the foundation_demo_v8 directory:
cd examples/foundation_demo_v8

# Set up OpenUSD environment
export PATH="/Users/hacker/Documents/src/AOUSD/forOUSD/bin:$PATH"
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"

# Prerequisites: assembly must exist first
python3 templates/01_create_element_templates.py  # if not done
python3 templates/04_create_assembly.py           # if not done

# Step 1: Generate clip file from XTC trajectory
python3 converters/xtc_to_clips.py
# This reads sort_traj_1.xtc (~1.2 GB), extracts 20 frames for protein+ligand

# Step 2: Create trajectory demo scene
python3 demos/trajectory_demo.py

# Step 3: View
usdview output/trajectory_demo.usda
```

### Expected Output

```
PDB: .../atp-complex-solv35.pdb
XTC: .../sort_traj_1.xtc
Parsing PDB for prim paths... 4676 atom prim paths
Extracting trajectory frames...
  Estimated total frames: ~70000, using stride=3500
  Loaded 20 frames, 4676 atoms
Writing clip file... Created clip: .../output/clips/trajectory_clip.usda

Created: .../output/trajectory_demo.usda
  Timeline: 0-19 (20 frames at 10 fps)
```

## What to Observe

### Timeline Scrubbing

The usdview timeline shows frames 0-19 at 10 fps (2 seconds total). Use the timeline slider or press Play to watch the protein move. You should see:

- **Global translation/rotation** of the complex (whole-body motion from simulation)
- **Local conformational changes** in side chains and loops
- **ATP movement** relative to the protein binding pocket

### Representation Switching During Playback

You can change the `representation` variant on `/World` while the trajectory plays:
- `points` mode is fastest for playback (smallest geometry per atom)
- `balls` mode gives a clearer sense of the molecular surface
- `vdw` mode shows space-filling contacts (slower with 4,676 full-size spheres)

### File Structure

```
output/
  trajectory_demo.usda        # Scene: /World + UsdClipsAPI metadata
  clips/
    trajectory_clip.usda       # Time-sampled positions only
```

The trajectory demo file is small (a few KB of clip configuration). The clip file contains all 20 x 4,676 position values. The assembly topology is sublayered from `assets/level4_assemblies/`.

> **Do not open `output/clips/trajectory_clip.usda` (or its `.usdc`/`clip.NNN.usdc` siblings) directly in usdview.** They carry only bond `Cylinder` geometry and time-sampled `xformOp:translate` values -- no topology hierarchy, no `displayColor`, no `representation` variants, and no authored stage time range. Opened standalone you will see a static mass of grey bond cylinders and a Play button that does nothing (there is no `startTimeCode`/`endTimeCode` to scrub). This is expected: always open `output/trajectory_demo.usda`, which sublayers the topology and wires the clip via `UsdClipsAPI`. See `docs/13_value_clips_for_trajectories.md` for the full topology/clip separation this implements, and `examples/foundation_demo_v8/README.md` for a complete entry-point-vs-payload file table.

## Why It Matters

### MD Trajectories Are Animation Clips

An MD simulation produces the same data structure as character animation:
- **Topology** (which atoms exist, how they're bonded) = character rig
- **Trajectory** (positions over time) = animation keyframes
- **Analysis overlays** (RMSD, contacts, energies) = post-production effects

USD Value Clips were designed for exactly this pattern: a static topology composed with time-varying data loaded on demand.

### Scalability Path

This demo extracts 20 frames from one of 10 trajectory files. The full dataset has ~700,000 frames across all files. USD's clip architecture supports:
- **Lazy loading**: only the visible frame is loaded into memory
- **Multiple clip files**: each XTC file becomes a separate clip
- **Clip sets**: different trajectories (replicas, perturbations) as named clip sets
- **Stage-time mapping**: non-linear time mapping for analysis (e.g., skip to interesting events)

## USD Patterns in Action

| LIVRPS Arc | How It's Used | Research Equivalent |
|-----------|--------------|---------------------|
| **Local** | Clip translate ops override topology positions at each time code | Frame-specific atomic coordinates |
| **Inherits** | Topology atoms still inherit colors/radii from `/_class_/` | Element properties persist across trajectory |
| **VariantSets** | Representation switching works during playback | Switching visualization modes during analysis |
| **SubLayers** | Topology sublayered for hierarchy; clips composed via API | Separating static structure from dynamic data |
| **Value Clips** | `UsdClipsAPI` maps trajectory frames to stage timeline | MD frames as animation clips |
