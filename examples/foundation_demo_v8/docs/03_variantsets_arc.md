# The VariantSets Composition Arc in OpenUSD

## Overview

**VariantSets** package multiple variations into a single USD file. They are "V" in LIVRPS - stronger than references/payloads, weaker than inherits/local.

| Position | Arc Type | Strength |
|----------|----------|----------|
| L | Local | Strongest |
| I | Inherits | |
| **V** | **VariantSets** | |
| R | References | |
| P | Payloads | |
| S | Specializes | Weakest |

## Creating VariantSets

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateInMemory()
prim = stage.DefinePrim("/Asset", "Xform")

# Create VariantSet and add variants
vset = prim.GetVariantSets().AddVariantSet("colorVariant")
vset.AddVariant("red")
vset.AddVariant("blue")
```

## CRITICAL: SetVariantSelection BEFORE GetVariantEditContext

```python
# CORRECT - Select THEN edit
vset.SetVariantSelection("red")      # 1. SELECT first
with vset.GetVariantEditContext():   # 2. THEN enter context
    colorAttr.Set([(1, 0, 0)])

# WRONG - Edits go to wrong place!
with vset.GetVariantEditContext():   # BUG: No selection!
    vset.SetVariantSelection("red")  # Too late
    colorAttr.Set([(1, 0, 0)])
```

### Complete Example

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("Asset.usda")
rootPrim = stage.GetPrimAtPath("/Asset")
colorAttr = UsdGeom.Gprim.Get(stage, "/Asset/Sphere").GetDisplayColorAttr()
colorAttr.Clear()  # Clear local opinion first!

vset = rootPrim.GetVariantSets().AddVariantSet("shadingVariant")
vset.AddVariant("red")
vset.AddVariant("blue")

# Author variants - ALWAYS: Select, then edit
vset.SetVariantSelection("red")
with vset.GetVariantEditContext():
    colorAttr.Set([(1, 0, 0)])

vset.SetVariantSelection("blue")
with vset.GetVariantEditContext():
    colorAttr.Set([(0, 0, 1)])

vset.SetVariantSelection("red")  # Set default
stage.GetRootLayer().Save()
```

## Variant Cascade with "overs"

Override selections from stronger layers using `over`:

### USDA

```usda
#usda 1.0
over "MyAsset" (
    variants = {
        string shadingVariant = "blue"
    }
)
{
}
```

### Python

```python
scene_stage = Usd.Stage.Open("Scene.usda")
asset_prim = scene_stage.GetPrimAtPath("/MyAsset")
asset_prim.GetVariantSet("shadingVariant").SetVariantSelection("blue")
```

### Nested VariantSets

```python
from pxr import Sdf, Usd

stage = Usd.Stage.CreateNew("nested.usd")
prim = stage.DefinePrim("/Char")
title = prim.CreateAttribute("title", Sdf.ValueTypeNames.String)

classVS = prim.GetVariantSets().AddVariantSet("classVariant")
for cls in ["Warrior", "Mage"]:
    classVS.AddVariant(cls)
    classVS.SetVariantSelection(cls)
    with classVS.GetVariantEditContext():
        weaponVS = prim.GetVariantSets().AddVariantSet("weaponVariant")
        weapons = ["Sword", "Axe"] if cls == "Warrior" else ["Staff", "Wand"]
        for w in weapons:
            weaponVS.AddVariant(w)
            weaponVS.SetVariantSelection(w)
            with weaponVS.GetVariantEditContext():
                title.Set(f"{cls} with {w}")
```

## Common Mistakes

### 1. Editing Before Selection
```python
# WRONG                              # CORRECT
with vset.GetVariantEditContext():   vset.SetVariantSelection("red")
    vset.SetVariantSelection("red")  with vset.GetVariantEditContext():
    attr.Set(value)                      attr.Set(value)
```

### 2. Not Clearing Local Opinions
```python
attr.Set([(0.5, 0.5, 0.5)])  # Local opinion BLOCKS variants!
attr.Clear()                  # Fix: clear it first
```

### 3. Forgetting Default Selection
```python
# After authoring all variants...
vset.SetVariantSelection("red")  # Don't forget default!
```

### 4. Using GetVariantSet on Non-Existent Set
```python
# Safe - creates if missing
vset = prim.GetVariantSets().AddVariantSet("myVariant")

# Unsafe - may be invalid
vset = prim.GetVariantSets().GetVariantSet("nonExistent")
```

## API Reference

```python
# UsdVariantSets (collection on prim)
vsets = prim.GetVariantSets()
vsets.AddVariantSet("name")           # Create/get
vsets.GetNames()                      # List names
vsets.HasVariantSet("name")           # Check exists
vsets.SetSelection("name", "var")     # Shortcut

# UsdVariantSet (single set)
vset.AddVariant("variantName")
vset.GetVariantNames()
vset.SetVariantSelection("name")      # CALL FIRST!
vset.GetVariantEditContext()          # CALL SECOND!
```

## Golden Rule

```
SetVariantSelection()  -->  GetVariantEditContext()
      FIRST                       SECOND
```

## References

- https://openusd.org/release/glossary.html
- https://openusd.org/release/api/class_usd_variant_set.html
