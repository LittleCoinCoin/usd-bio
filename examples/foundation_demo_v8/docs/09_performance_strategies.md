# Performance Strategies for Large Molecular Scenes in OpenUSD

## Overview

This document summarizes strategies for rendering large molecular systems (1000+ atoms) with interactive representation switching.

## Strategy Comparison

| Approach | Atom Count | Mode Switch | Memory | Selection | Best For |
|----------|------------|-------------|--------|-----------|----------|
| **Individual prims** | <500 | Slow (cascade) | High | Native | Educational, editing |
| **PointInstancer** | 1K-1M | Fast (array) | Low | Promotion | Production, bulk |
| **UsdGeom.Points** | 10K+ | N/A | Minimal | Custom | Trajectories, overview |
| **Hybrid** | Any | Fast | Medium | Both | Interactive apps |

---

## 1. Individual Prims (Current v8 Approach)

**Structure:**
```
/_class_/H          <- Class template with VariantSet
/_class_/O
/World/Water
    /O (inherits /_class_/O, local position)
    /H1 (inherits /_class_/H, local position)
    /H2 (inherits /_class_/H, local position)
```

**Pros:**
- Full USD composition (LIVRPS)
- Per-atom selection and editing
- Clean variant cascade

**Cons:**
- Slow for 1000+ atoms
- High memory overhead
- Many draw calls

**Use when:** <500 atoms, need editing, educational purposes

---

## 2. PointInstancer

**Structure:**
```
/Solvent/Waters (PointInstancer)
    /Prototypes
        /H (inherits /_class_/H, variants={representation=balls})
        /O (inherits /_class_/O, variants={representation=balls})
    positions = [3000 Vec3f]     # 1000 waters × 3 atoms
    protoIndices = [0,0,1,...]   # H,H,O pattern
    scales = [3000 Vec3f]        # For mode switching
```

**Key Findings:**
- Prototypes CAN use VariantSets
- Prototypes CAN inherit from class prims
- All instances of a prototype share the same variant selection
- Changing prototype variant = ALL instances update

**Mode Switching Options:**

### Option A: Variant on Prototype
```python
proto = stage.GetPrimAtPath("/Instancer/Prototypes/H")
vset = proto.GetVariantSets().GetVariantSet("representation")
vset.SetVariantSelection("vdw")  # All H instances switch
```

### Option B: Scales Array (Faster)
```python
SCALE_MAP = {"points": 0.1, "balls": 0.4, "vdw": 1.0}

def switch_mode(instancer, mode):
    n = len(instancer.GetPositionsAttr().Get())
    new_scales = [Gf.Vec3f(SCALE_MAP[mode])] * n
    instancer.GetScalesAttr().Set(Vt.Vec3fArray(new_scales))
```

**Pros:**
- Excellent performance (2-10 draw calls for 10K atoms)
- Low memory
- Fast mode switching

**Cons:**
- No per-instance variant overrides
- Array-based (modify all or nothing)
- Selection requires "promotion"

**Use when:** 1000+ identical molecules (solvent, bulk)

---

## 3. UsdGeom.Points (Point Cloud)

**Structure:**
```python
points_prim = UsdGeom.Points.Define(stage, "/Molecule/PointCloud")
points_prim.CreatePointsAttr(Vt.Vec3fArray(positions))
points_prim.CreateWidthsAttr(Vt.FloatArray(widths))

# Per-point colors
color_pv = points_prim.CreateDisplayColorPrimvar(UsdGeom.Tokens.vertex)
color_pv.Set(Vt.Vec3fArray(colors))
```

**Pros:**
- Single prim, single draw call
- 100-1000x faster than spheres
- Minimal memory

**Cons:**
- Points only (no sphere geometry)
- Limited rendering options
- No bonds

**Use when:** Trajectory playback, overview mode, 10K+ atoms

---

## 4. Hybrid Approach

**Concept:** Use different strategies for different scene components based on interaction needs.

### Scene Structure
```
/Simulation
    /Protein          <- Individual prims (need selection)
    /Ligand           <- Individual prims (need editing)
    /Solvent          <- PointInstancer (bulk display)
    /Selection        <- Promoted prims (from instancer)
```

### Component Strategy

| Component | Strategy | Reason |
|-----------|----------|--------|
| Protein (500-5000 atoms) | Individual prims | Per-residue coloring, selection |
| Ligand (<100 atoms) | Individual prims | Bond editing, detailed view |
| Solvent (10K+ atoms) | PointInstancer | Bulk, no interaction |
| Focus area | Individual prims | Detailed interaction |

### Promotion Pattern

When user selects atoms from PointInstancer:

```python
def promote_selection(instancer, selected_indices, stage):
    """Convert selected instances to individual prims for editing."""
    positions = instancer.GetPositionsAttr().Get()
    proto_indices = instancer.GetProtoIndicesAttr().Get()

    # Create individual prims
    for idx in selected_indices:
        atom = UsdGeom.Sphere.Define(stage, f"/Selection/Atom_{idx}")
        xform = UsdGeom.Xformable(atom)
        xform.AddTranslateOp().Set(Gf.Vec3d(positions[idx]))
        # Copy radius, color from prototype...

    # Hide in instancer
    instancer.GetInvisibleIdsAttr().Set(Vt.Int64Array(selected_indices))

def demote_selection(instancer, selected_indices, stage):
    """Return promoted prims back to instancer."""
    # Remove individual prims
    for idx in selected_indices:
        stage.RemovePrim(f"/Selection/Atom_{idx}")

    # Show in instancer again
    instancer.GetInvisibleIdsAttr().Clear()
```

### Interaction State Machine

| User Action | Active Strategy |
|-------------|-----------------|
| Scene load | PointInstancer for solvent |
| Navigate (rotate/zoom) | All strategies active |
| Select atoms | Promote to individual prims |
| Edit bonds | Individual prims |
| Play trajectory | Switch to UsdGeom.Points |
| Export | Appropriate for target |

---

## 5. Metadata Storage

### Individual Prims: Per-prim attributes
```python
atom_prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set("C")
atom_prim.CreateAttribute("bio:residueId", Sdf.ValueTypeNames.Int).Set(42)
```

### PointInstancer: Array attributes
```python
prim = instancer.GetPrim()
prim.CreateAttribute("bio:elements", Sdf.ValueTypeNames.TokenArray).Set(elements)
prim.CreateAttribute("bio:residueIds", Sdf.ValueTypeNames.IntArray).Set(residue_ids)
prim.CreateAttribute("bio:atomNames", Sdf.ValueTypeNames.StringArray).Set(names)
```

---

## 6. Recommended Representation Modes

| Mode | Geometry | Implementation | Use Case |
|------|----------|----------------|----------|
| `pointcloud` | UsdGeom.Points | Single prim | Fast overview, trajectories |
| `points` | Small spheres | 0.15× VDW | Overview with depth |
| `balls` | Medium spheres | 0.30× VDW | Default visualization |
| `vdw` | Full spheres | 1.0× VDW | Space-filling |
| `ballstick` | Spheres + cylinders | 0.25× VDW + bonds | Bond visualization |

---

## 7. Performance Targets

| Metric | Individual Prims | PointInstancer | Target |
|--------|------------------|----------------|--------|
| Stage load (10K atoms) | 2-5 sec | <200ms | <500ms |
| Mode switch | 500ms-2s | <50ms | <100ms |
| Memory (10K atoms) | ~15MB | ~2MB | <5MB |
| Draw calls | 10,000+ | 2-10 | <50 |

---

## References

- OpenUSD PointInstancer: https://openusd.org/release/api/class_usd_geom_point_instancer.html
- OpenUSD Points: https://openusd.org/release/api/class_usd_geom_points.html
- NVIDIA Instancing Guide: https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/independent/modularity-guide/instancing.html
