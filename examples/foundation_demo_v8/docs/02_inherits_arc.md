# USD Inherits Composition Arc

## LIVRPS Strength Order

Inherits is the **2nd strongest** arc in USD's composition order:

1. **L**ocal opinions (strongest)
2. **I**nherits <-- This document
3. **V**ariants
4. **R**eferences
5. **P**ayloads
6. **S**pecializes (weakest)

## Class Prims as Templates

Use `CreateClassPrim()` to define abstract template prims. By convention, prefix with `_class_`:

```python
stage.CreateClassPrim("/_class_Tree")
```

Class prims are **not rendered** - they exist solely as inheritance sources.

## Core API

```python
# Get the inherits editor for a prim
inherits = prim.GetInherits()

# Add inheritance from a class prim
inherits.AddInherit("/_class_Tree")

# Other methods
inherits.RemoveInherit(path)
inherits.ClearInherits()
inherits.GetAllDirectInherits()
```

## Override Behavior

Local opinions **always win** over inherited values:

| Source | Strength |
|--------|----------|
| Local (direct on prim) | Strongest |
| Inherited | Weaker |

Changes to the class prim propagate to all inheriting prims, unless locally overridden.

## Python Example

```python
from pxr import Usd, UsdGeom

# Create stage
stage = Usd.Stage.CreateNew("inherits_demo.usda")

# 1. Define class template
class_prim = stage.CreateClassPrim("/_class_Tree")
trunk = UsdGeom.Mesh.Define(stage, "/_class_Tree/Trunk")
trunk.CreateDisplayColorAttr([(0.5, 0.3, 0.1)])

leaves = UsdGeom.Mesh.Define(stage, "/_class_Tree/Leaves")
leaves.CreateDisplayColorAttr([(0.0, 0.8, 0.0)])

# 2. Create prims that inherit from class
tree_a = stage.DefinePrim("/TreeA", "Xform")
tree_a.GetInherits().AddInherit("/_class_Tree")

tree_b = stage.DefinePrim("/TreeB", "Xform")
tree_b.GetInherits().AddInherit("/_class_Tree")

# 3. Override locally on TreeB
tree_b_leaves = stage.OverridePrim("/TreeB/Leaves")
UsdGeom.Gprim(tree_b_leaves).CreateDisplayColorAttr([(0.8, 1.0, 0.0)])

stage.Save()
```

**Result**: TreeA has green leaves, TreeB has yellow-green leaves (local override wins).

## USDA Output

```usda
class "_class_Tree" {
    def Mesh "Trunk" {
        color3f[] primvars:displayColor = [(0.5, 0.3, 0.1)]
    }
    def Mesh "Leaves" {
        color3f[] primvars:displayColor = [(0, 0.8, 0)]
    }
}

def "TreeA" (inherits = </_class_Tree>) { }

def "TreeB" (inherits = </_class_Tree>) {
    over "Leaves" {
        color3f[] primvars:displayColor = [(0.8, 1, 0)]
    }
}
```

## Key Points

- Inherits enables **shared defaults** across many prims
- Class changes propagate everywhere (unless overridden)
- Use for consistent asset types (trees, rocks, characters)
- Local > Inherits > Variants > References > Payloads > Specializes
