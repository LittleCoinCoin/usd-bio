# Local Opinions in OpenUSD

## Overview

**Local opinions are the strongest** in USD's LIVRPS composition order. Any value authored directly on a prim overrides all inherited, referenced, or specialized values.

## LIVRPS Strength Order

| Position | Arc Type | Strength |
|----------|----------|----------|
| **L** | **Local** | **Strongest** |
| I | Inherits | |
| V | VariantSets | |
| R | References | |
| P | Payloads | |
| S | Specializes | Weakest |

## Local Overrides Inherited/Referenced Values

When a prim inherits from a class or references another layer, you can override any attribute locally:

```usda
#usda 1.0

class "_class_Atom" {
    float bio:vdwRadius = 1.0
}

def "Carbon" (inherits = </_class_Atom>) {
    float bio:vdwRadius = 1.7  # Local override wins
}
```

The local value `1.7` takes precedence over the inherited `1.0`.

## AddTranslateOp() for Local Transforms

Use `AddTranslateOp()` to set local position on any Xformable prim:

```python
from pxr import Usd, UsdGeom, Gf

stage = Usd.Stage.CreateInMemory()
prim = stage.DefinePrim("/Atom", "Xform")

# Local transform - strongest opinion
xform = UsdGeom.Xformable(prim)
xform.AddTranslateOp().Set(Gf.Vec3d(1.5, 2.0, 3.0))
```

## Python Example: Local Override

```python
from pxr import Usd, Sdf

stage = Usd.Stage.CreateInMemory()

# Create class with default
base = stage.CreateClassPrim("/_class_/Element")
base.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(1.0)

# Instance inherits from class
atom = stage.DefinePrim("/Carbon")
atom.GetInherits().AddInherit("/_class_/Element")

# Inherited value
print(atom.GetAttribute("bio:vdwRadius").Get())  # 1.0

# Local override (strongest in LIVRPS)
atom.GetAttribute("bio:vdwRadius").Set(1.7)
print(atom.GetAttribute("bio:vdwRadius").Get())  # 1.7
```

## Key Points

- Local opinions always win over any composition arc
- Use local overrides for instance-specific values
- Transform ops (`AddTranslateOp`, `AddRotateOp`, `AddScaleOp`) are local opinions
- Clear a local opinion with `attr.Clear()` to fall back to inherited value

## References

- OpenUSD Glossary: https://openusd.org/release/glossary.html
- UsdGeomXformable: https://openusd.org/release/api/class_usd_geom_xformable.html
