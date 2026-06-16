# The References Composition Arc in OpenUSD

## Overview

The **References** arc is a core composition mechanism in USD that brings external or internal scene data into a prim. References are mid-strength in LIVRPS, making them ideal for asset assembly.

## LIVRPS Strength Ordering

USD resolves opinions using the LIVRPS mnemonic (strongest to weakest):

| Position | Arc Type | Strength |
|----------|----------|----------|
| L | **Local** | Strongest |
| I | **Inherits** | |
| V | **VariantSets** | |
| R | **References** | |
| P | **Payloads** | |
| S | **Specializes** | Weakest |

**Key Point:** References are weaker than Variants but stronger than Payloads and Specializes. Local overrides always win.

## Internal vs External References

### External References (Most Common)
Point to prims in other USD files:
```python
prim.GetReferences().AddReference("./asset.usda")           # Uses defaultPrim
prim.GetReferences().AddReference("./asset.usda", "/Geom")  # Explicit prim path
```

### Internal References
Point to prims within the same layer:
```python
prim.GetReferences().AddInternalReference("/SharedDef/BaseMaterial")
```

Internal references are useful for sharing definitions without separate files.

## AddReference() API

### Python API

```python
from pxr import Usd, Sdf

stage = Usd.Stage.CreateInMemory()
prim = stage.DefinePrim("/MyPrim")
refs = prim.GetReferences()

# External reference (file path only - uses defaultPrim)
refs.AddReference("./geometry.usda")

# External reference with explicit prim path
refs.AddReference("./geometry.usda", Sdf.Path("/Geom/Sphere"))

# Internal reference (same layer)
refs.AddInternalReference(Sdf.Path("/SharedDefs/Material"))

# Clear all references
refs.ClearReferences()

# Remove specific reference
refs.RemoveReference(Sdf.Reference("./geometry.usda"))
```

### UsdListPosition Options

Control where new references appear in the list:
```python
refs.AddReference("./new.usda", position=Usd.ListPositionFrontOfPrependList)
refs.AddReference("./new.usda", position=Usd.ListPositionBackOfPrependList)   # Default
refs.AddReference("./new.usda", position=Usd.ListPositionFrontOfAppendList)
refs.AddReference("./new.usda", position=Usd.ListPositionBackOfAppendList)
```

## Local Overrides vs Referenced Values

Local opinions always override referenced values:

```python
from pxr import Usd, UsdGeom, Sdf

# Create referenced file
ref_stage = Usd.Stage.CreateNew("/tmp/sphere.usda")
sphere = UsdGeom.Sphere.Define(ref_stage, "/Sphere")
sphere.CreateRadiusAttr(1.0)  # Referenced value: 1.0
ref_stage.SetDefaultPrim(sphere.GetPrim())
ref_stage.GetRootLayer().Save()

# Create main stage with reference
main_stage = Usd.Stage.CreateNew("/tmp/main.usda")
prim = main_stage.DefinePrim("/MySphere")
prim.GetReferences().AddReference("/tmp/sphere.usda")

# Local override wins
UsdGeom.Sphere(prim).GetRadiusAttr().Set(2.0)  # Overrides to 2.0

# Query composed value
radius = UsdGeom.Sphere(prim).GetRadiusAttr().Get()
print(f"Radius: {radius}")  # Output: 2.0
```

### USDA Result
```usda
#usda 1.0
def "MySphere" (
    prepend references = @/tmp/sphere.usda@
)
{
    double radius = 2.0  # Local override
}
```

## Practical Pattern: Variants with References

The correct way to swap geometry in variants (schema attributes like `radius` require this):

```python
from pxr import Usd, UsdGeom
import tempfile, os

with tempfile.TemporaryDirectory() as tmpdir:
    # Create separate files for each representation
    for mode, radius in [("points", 0.2), ("balls", 0.5), ("vdw", 1.7)]:
        ref_path = os.path.join(tmpdir, f"carbon_{mode}.usda")
        ref_stage = Usd.Stage.CreateNew(ref_path)
        sphere = UsdGeom.Sphere.Define(ref_stage, "/Geom/Sphere")
        sphere.CreateRadiusAttr(radius)
        ref_stage.SetDefaultPrim(ref_stage.GetPrimAtPath("/Geom"))
        ref_stage.GetRootLayer().Save()

    # Create main file with variant references
    main_path = os.path.join(tmpdir, "carbon.usda")
    main_stage = Usd.Stage.CreateNew(main_path)
    prim = main_stage.DefinePrim("/Carbon")

    vset = prim.GetVariantSets().AddVariantSet("representation")
    for mode in ["points", "balls", "vdw"]:
        vset.AddVariant(mode)
        vset.SetVariantSelection(mode)
        with vset.GetVariantEditContext():
            prim.GetReferences().ClearReferences()
            prim.GetReferences().AddReference(
                os.path.join(tmpdir, f"carbon_{mode}.usda")
            )

    vset.SetVariantSelection("balls")  # Set default
    main_stage.GetRootLayer().Save()

    # Test: switch variant and verify radius
    vset.SetVariantSelection("vdw")
    sphere_prim = main_stage.GetPrimAtPath("/Carbon/Geom/Sphere")
    radius = UsdGeom.Sphere(sphere_prim).GetRadiusAttr().Get()
    print(f"VDW radius: {radius}")  # Output: 1.7
```

## Best Practices

| Pattern | Use References | Use Payloads |
|---------|----------------|--------------|
| Asset Assembly | Yes | For heavy assets |
| Variant Swapping | Yes (in variants) | Optional |
| Lazy Loading | No | Yes |
| Deferred Loading | No | Yes |

## Key Differences: References vs Payloads

| Aspect | References | Payloads |
|--------|------------|----------|
| Strength | Stronger (R) | Weaker (P) |
| Loading | Always loaded | Can be unloaded |
| Use Case | Essential data | Optional/heavy data |

## References

- OpenUSD Referencing Layers: https://openusd.org/release/tut_referencing_layers.html
- UsdReferences API: https://openusd.org/release/api/class_usd_references.html
- Composition Arcs: https://openusd.org/release/glossary.html#composition-arcs
