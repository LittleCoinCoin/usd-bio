# PointInstancer: Efficient Many-Instance Rendering

## When to Use PointInstancer

Use `UsdGeomPointInstancer` when rendering **1000+ identical or similar objects**:
- Particle systems (rain, snow, debris)
- Crowds and vegetation (trees, grass, rocks)
- Scattered objects (bolts, bricks, molecules)

**Performance**: PointInstancer is GPU-optimized. Drawing 10,000 spheres individually = slow. Drawing 10,000 instances of one sphere prototype = fast.

## Core Concepts

| Attribute | Type | Description |
|-----------|------|-------------|
| `prototypes` | relationship | Points to prototype geometry (what to instance) |
| `protoIndices` | int[] | Which prototype each instance uses (0-indexed) |
| `positions` | point3f[] | World-space position per instance |
| `orientations` | quath[] | Rotation per instance (quaternion) |
| `scales` | float3[] | Scale per instance |

## Python Example: Complete PointInstancer

```python
from pxr import Usd, UsdGeom, Gf, Vt, Sdf

# Create stage
stage = Usd.Stage.CreateNew("point_instancer.usda")
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

# 1. Create the PointInstancer
instancer = UsdGeom.PointInstancer.Define(stage, "/Instancer")

# 2. Create prototypes under the instancer
proto_scope = stage.DefinePrim("/Instancer/Prototypes", "Scope")
sphere = UsdGeom.Sphere.Define(stage, "/Instancer/Prototypes/Sphere")
sphere.GetRadiusAttr().Set(0.5)
cube = UsdGeom.Cube.Define(stage, "/Instancer/Prototypes/Cube")
cube.GetSizeAttr().Set(1.0)

# 3. Set up prototype relationship (ORDER MATTERS - defines indices)
prototypes_rel = instancer.GetPrototypesRel()
prototypes_rel.AddTarget("/Instancer/Prototypes/Sphere")  # index 0
prototypes_rel.AddTarget("/Instancer/Prototypes/Cube")    # index 1

# 4. Define instances
num_instances = 5000
positions = []
proto_indices = []
orientations = []
scales = []

import random
for i in range(num_instances):
    x = (i % 50) * 2.0
    z = (i // 50) * 2.0
    y = random.uniform(0, 1)
    positions.append(Gf.Vec3f(x, y, z))
    proto_indices.append(i % 2)
    orientations.append(Gf.Quath(1, 0, 0, 0))
    s = random.uniform(0.5, 1.5)
    scales.append(Gf.Vec3f(s, s, s))

# 5. Set instance attributes
instancer.GetPositionsAttr().Set(Vt.Vec3fArray(positions))
instancer.GetProtoIndicesAttr().Set(Vt.IntArray(proto_indices))
instancer.GetOrientationsAttr().Set(Vt.QuathArray(orientations))
instancer.GetScalesAttr().Set(Vt.Vec3fArray(scales))

stage.Save()
```

## Per-Instance Colors with Primvars

```python
from pxr import UsdGeom, Gf, Vt

primvars_api = UsdGeom.PrimvarsAPI(instancer)
color_primvar = primvars_api.CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.varying
)

colors = [Gf.Vec3f((i%10)/10.0, ((i//10)%10)/10.0, 0.5) for i in range(num_instances)]
color_primvar.Set(Vt.Vec3fArray(colors))
```

## Minimal Working Example

```python
from pxr import Usd, UsdGeom, Gf, Vt

stage = Usd.Stage.CreateInMemory()
instancer = UsdGeom.PointInstancer.Define(stage, "/Points")

sphere = UsdGeom.Sphere.Define(stage, "/Points/Proto/S")
instancer.GetPrototypesRel().AddTarget("/Points/Proto/S")

instancer.GetPositionsAttr().Set([(0,0,0), (2,0,0), (4,0,0)])
instancer.GetProtoIndicesAttr().Set([0, 0, 0])

print(stage.GetRootLayer().ExportToString())
```

## Key Points

1. **Prototypes must be children** of the instancer (or referenced into it)
2. **protoIndices** array length must equal **positions** array length
3. **Prototype order** in the relationship defines the index mapping
4. For animation, set time-sampled positions/orientations/scales
5. Use `ComputeInstanceTransformsAtTime()` to query final transforms

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| No instances visible | Missing protoIndices | Set protoIndices array |
| Wrong prototype used | Index mismatch | Check AddTarget order matches indices |
| Colors not showing | Wrong interpolation | Use `varying` or check renderer support |
