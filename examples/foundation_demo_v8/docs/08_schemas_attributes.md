# OpenUSD Schemas and Attributes

## 1. UsdGeom Schemas

USD provides typed schemas for common geometry. Key schemas:

| Schema | Purpose | Key Attributes |
|--------|---------|----------------|
| `UsdGeom.Xform` | Transform container | xformOps (translate, rotate, scale) |
| `UsdGeom.Sphere` | Sphere primitive | radius, extent |
| `UsdGeom.Mesh` | Polygon mesh | points, faceVertexCounts, faceVertexIndices |
| `UsdGeom.Cylinder` | Cylinder primitive | radius, height, axis |
| `UsdGeom.Scope` | Grouping (no transform) | N/A |

## 2. CreateAttribute vs Schema Methods

**Schema methods** (preferred for schema-defined attributes):
```python
sphere = UsdGeom.Sphere.Define(stage, "/path")
sphere.CreateRadiusAttr(2.0)      # Schema knows type (double)
sphere.GetRadiusAttr().Set(3.0)   # Get existing, then set
```

**CreateAttribute** (for custom attributes):
```python
prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set("C")
prim.CreateAttribute("custom:mass", Sdf.ValueTypeNames.Float).Set(12.01)
```

**Rule**: Use schema methods when available; use `CreateAttribute` for custom data.

## 3. Primvars vs Regular Attributes

| Feature | Regular Attributes | Primvars |
|---------|-------------------|----------|
| Prefix | None | `primvars:` |
| Interpolation | No | Yes (constant, vertex, faceVarying) |
| Use case | General data | Renderable data (color, UVs) |

```python
# Regular attribute
prim.CreateAttribute("radius", Sdf.ValueTypeNames.Double)

# Primvar (with interpolation)
primvar = mesh.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray,
                             UsdGeom.Tokens.faceVarying)

# Display color primvar (shortcut)
sphere.CreateDisplayColorAttr([(1, 0, 0)])  # Red
```

## 4. Sdf.ValueTypeNames Reference

Common types for `CreateAttribute`:

| Type Name | Python Value | USD Type |
|-----------|--------------|----------|
| `Bool` | `True/False` | bool |
| `Int` | `42` | int |
| `Float` | `3.14` | float |
| `Double` | `3.14159` | double |
| `String` | `"text"` | string |
| `Token` | `"enumValue"` | token |
| `Vec3f` | `Gf.Vec3f(1,2,3)` | float3 |
| `Vec3d` | `Gf.Vec3d(1,2,3)` | double3 |
| `Color3f` | `Gf.Vec3f(1,0,0)` | color3f |
| `Float3Array` | `[(1,2,3), (4,5,6)]` | float3[] |
| `IntArray` | `[1, 2, 3]` | int[] |
| `TexCoord2fArray` | `[(0,0), (1,1)]` | texCoord2f[] |

## 5. Complete Python Example

```python
from pxr import Usd, UsdGeom, Sdf, Gf

# Create stage
stage = Usd.Stage.CreateNew("example.usda")

# Define Xform with transform
xform = UsdGeom.Xform.Define(stage, "/World/Atom")
xform.AddTranslateOp().Set(Gf.Vec3d(1, 2, 3))

# Define Sphere with schema attributes
sphere = UsdGeom.Sphere.Define(stage, "/World/Atom/Sphere")
sphere.CreateRadiusAttr(1.5)
sphere.CreateDisplayColorAttr([Gf.Vec3f(0, 1, 0)])  # Green

# Custom attributes with bio: namespace
prim = sphere.GetPrim()
prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set("C")
prim.CreateAttribute("bio:atomicNumber", Sdf.ValueTypeNames.Int).Set(6)
prim.CreateAttribute("bio:mass", Sdf.ValueTypeNames.Float).Set(12.01)

# Primvar for texture coordinates on a mesh
mesh = UsdGeom.Mesh.Define(stage, "/World/Surface")
mesh.CreatePointsAttr([(-1,0,-1), (1,0,-1), (1,0,1), (-1,0,1)])
mesh.CreateFaceVertexCountsAttr([4])
mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])

uvs = mesh.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray,
                         UsdGeom.Tokens.faceVarying)
uvs.Set([(0,0), (1,0), (1,1), (0,1)])

stage.GetRootLayer().Save()
```

## Key Takeaways

1. **Use schema methods** (`CreateRadiusAttr`) for built-in attributes
2. **Use CreateAttribute** with `Sdf.ValueTypeNames` for custom data
3. **Primvars** = renderable attributes with interpolation (prefix: `primvars:`)
4. **Namespace custom attributes** (e.g., `bio:element`) for organization
5. **Gf module** provides vector/matrix types (`Gf.Vec3f`, `Gf.Vec3d`)
