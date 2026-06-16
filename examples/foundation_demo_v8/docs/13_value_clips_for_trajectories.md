# Value Clips for MD Trajectories

## The Problem

MD simulations produce two fundamentally different kinds of data:

1. **Topology**: which atoms exist, their bonds, types, and hierarchy. Static. Small (~KB).
2. **Trajectory**: 3D positions of every atom at every time step. Dynamic. Massive (~GB).

Loading a full trajectory into memory is impractical. Researchers need to scrub to arbitrary frames without loading the entire dataset. This is the exact problem USD Value Clips solve for animation pipelines.

## The Pattern: Topology/Clip Separation

### Architecture

```
trajectory_demo.usda          # Scene file: timeline + UsdClipsAPI config
  ├─ SubLayers: abl_kinase_complex.usda    # Static topology (hierarchy, colors, variants)
  │    └─ SubLayers: element_templates.usda  # Class prims for elements
  └─ Clips: trajectory_clip.usda           # Time-sampled positions only
```

The topology file defines the prim hierarchy with all metadata, class inheritance, and variant definitions. The clip file contains *only* time-sampled `xformOp:translate` values at matching prim paths. USD's composition engine merges them: the clip's translate values override the topology's static positions at each time code.

### Clip File Structure

Each atom prim in the clip has time-sampled translate ops:

```usda
# Inside trajectory_clip.usda
def Xform "ABLComplex" {
    def Xform "Chain_A" {
        def Xform "ACE_1" {
            def Xform "HH31" {
                double3 xformOp:translate.timeSamples = {
                    0: (-16.265, 8.745, 10.430),
                    1: (-15.891, 9.102, 10.112),
                    2: (-16.504, 8.432, 10.789),
                    ...
                }
                uniform token[] xformOpOrder = ["xformOp:translate"]
            }
        }
    }
}
```

### UsdClipsAPI Setup

```python
clips_api = Usd.ClipsAPI(complex_prim)

# Which files contain clip data
clips_api.SetClipAssetPaths([Sdf.AssetPath("clips/trajectory_clip.usda")])

# Root prim path in clip files (must match topology structure)
clips_api.SetClipPrimPath("/ABLComplex")

# Stage time -> clip time mapping (1:1 in this case)
clip_times = Vt.Vec2dArray(
    [Gf.Vec2d(float(i), float(i)) for i in range(n_frames)]
)
clips_api.SetClipTimes(clip_times)

# Which clip is active at each stage time (clip index 0 from time 0)
clips_api.SetClipActive(Vt.Vec2dArray([Gf.Vec2d(0.0, 0.0)]))
```

### XTC Frame Extraction with mdtraj

```python
import mdtraj as md
import numpy as np

topo = md.load_pdb(pdb_path)
protein_idx = topo.topology.select("protein")
atp_idx = topo.topology.select("resname atp or resname ATP")
combined = np.sort(np.concatenate([protein_idx, atp_idx]))

traj = md.load(xtc_path, top=pdb_path,
               atom_indices=combined, stride=stride)

# mdtraj uses nanometers; USD/PDB uses Angstroms
positions = traj.xyz * 10.0  # shape: (n_frames, n_atoms, 3)
```

## The Gotchas

### 1. Prim path correspondence

The clip file's prim paths must *exactly* match the topology's prim paths. If the assembly creates `/ABLComplex/Chain_A/ACE_1/HH31`, the clip must use the same path. Any mismatch (different sanitization, different hierarchy) silently produces no animation.

**Solution**: Build prim paths from the same PDB parser used for both topology and clips.

### 2. Coordinate system mismatch

mdtraj reports positions in nanometers. PDB files use Angstroms. The topology (from PDB parsing) has Angstrom coordinates. If clip positions are in nm, atoms will appear 10x too close to the origin.

**Solution**: Always multiply mdtraj positions by 10.0 before writing to USD.

### 3. Atom index alignment

mdtraj's `protein` selection returns atoms in PDB file order, but may use different residue naming (HID/HIE/HIP become HIS). The atom *indices* remain aligned with the PDB atom serial order, so the mapping to prim paths works as long as both the topology generator and clip generator iterate atoms in the same order.

**Solution**: Use the same `parse_pdb()` output to build prim paths for both. Don't rely on mdtraj residue names for path construction.

### 4. Anonymous manifest layer warning

USD auto-generates a manifest layer when clips are configured. This produces a harmless warning:

```
Warning: Not saving @anon:...:generated_manifest.usda@ because it is an anonymous layer
```

This is expected and does not affect functionality.

### 5. Per-atom vs. points-array tradeoff

Two approaches for encoding positions:

| Approach | Per-Atom Xform | UsdGeomPoints |
|----------|---------------|---------------|
| Prim count | 4,676 prims | 1 prim |
| Position encoding | `xformOp:translate` per prim | `points` attribute (Vec3f array) |
| Individual selection | Yes | No (select whole cloud) |
| Variant cascade | Yes (per-atom variants) | No (single prim) |
| Metadata per atom | Yes (`bio:atomName`, etc.) | Via primvars only |
| File size (20 frames) | ~95 MB .usda | ~2 MB .usda |
| usdview performance | Acceptable at 5K | Fast at any count |

For this demo (4,676 atoms, prototyping phase), per-atom Xforms are used to preserve the full hierarchy, individual atom selection, and variant cascade. For production systems with >10K atoms or >100 frames, UsdGeomPoints is strongly recommended for the trajectory layer while keeping per-atom Xforms for the static topology.

## Scaling Considerations

| Parameter | Demo | Medium Scale | Production |
|-----------|------|-------------|------------|
| Atoms | 4,676 | 50,000 | 500,000 |
| Frames | 20 | 1,000 | 100,000 |
| Clip format | .usda (text) | .usdc (binary) | .usdc + Crate |
| Position encoding | Per-atom Xform | UsdGeomPoints | UsdGeomPoints |
| Clip file count | 1 | 10-100 | 1,000+ |
| Clip template | No | Yes (template pattern) | Yes |
| Memory model | Load all frames | Lazy per-clip | Lazy + streaming |

### Scaling path for this project

1. **Current**: Per-atom Xforms, single clip file, text format
2. **Next**: Switch clip to `.usdc` binary for 5-10x size reduction
3. **Then**: UsdGeomPoints for trajectory layer (keep Xforms for topology)
4. **Future**: Clip template pattern for multi-file trajectories, one clip per XTC file
5. **Production**: Streaming clips with custom resolver for remote data access
