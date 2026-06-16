# The Payloads Composition Arc in OpenUSD

## Overview

**Payloads** behave like references but support **deferred loading**, ideal for large assets that don't need immediate loading.

## LIVRPS Strength Ordering

| Position | Arc Type | Strength |
|----------|----------|----------|
| L | **Local** | Strongest |
| I | **Inherits** | |
| V | **VariantSets** | |
| R | **References** | |
| P | **Payloads** | Weaker than References |
| S | **Specializes** | Weakest |

**Key Point:** Payloads are weaker than references. Referenced opinions win over payloaded opinions.

## Payloads vs References

| Aspect | References | Payloads |
|--------|------------|----------|
| Loading | Always loaded | Optionally loaded (deferred) |
| Strength | Stronger (R) | Weaker (P) |
| Use case | Essential scene data | Heavy/optional assets |

The critical difference: **payloads can be unloaded** to reduce memory and improve load times.

## Python API

### Adding Payloads

```python
from pxr import Usd, Sdf

stage = Usd.Stage.CreateInMemory()
prim = stage.DefinePrim("/HeavyAsset", "Xform")
payloads = prim.GetPayloads()

# Add a payload (external file)
payloads.AddPayload("./HeavyModel.usd", Sdf.Path("/Model"))

# Set explicit payload list (replaces existing)
payloads.SetPayloads([
    Sdf.Payload("./Asset1.usd", "/Root"),
    Sdf.Payload("./Asset2.usd", "/Root")
])

payloads.ClearPayloads()  # Clear all
payloads.RemovePayload(Sdf.Payload("./Asset1.usd", "/Root"))  # Remove one
```

### Load/Unload Control

```python
from pxr import Usd

# Open stage with payloads initially unloaded
stage = Usd.Stage.Open("scene.usd", Usd.Stage.LoadNone)

stage.Load("/HeavyAsset")  # Load specific prim's payload

prim = stage.GetPrimAtPath("/HeavyAsset")
prim.Load(Usd.LoadWithDescendants)  # Load with children
prim.Unload()  # Unload to free memory

# Check payload status
has_payload = prim.HasPayload()
has_authored = prim.HasAuthoredPayloads()
```

### Stage Load Policies

```python
stage = Usd.Stage.Open("scene.usd", Usd.Stage.LoadAll)   # Load all (default)
stage = Usd.Stage.Open("scene.usd", Usd.Stage.LoadNone)  # Load none (faster)
stage.Load("/ImportantAsset")  # Selective loading
```

## When to Use Payloads

**Use payloads for:**
- Large geometry (high-poly meshes, complex assemblies)
- Assets that may not always be needed
- Background/distant objects in large scenes

**Use references for:**
- Essential scene structure
- Lightweight assets that must always be present

## USDA Syntax

```usda
#usda 1.0

def Xform "Scene" {
    def "Hero" (
        references = @./hero.usd@</Model>  # Always loaded
    ) {}

    def "Background" (
        payload = @./city.usd@</City>  # Deferred loading
    ) {}
}
```

## Best Practices

1. **Large assets:** Always use payloads for heavy geometry
2. **Scene root:** Use references for core structure, payloads for details
3. **Memory management:** Open with `LoadNone`, load selectively

## References

- UsdPayloads API: https://openusd.org/release/api/class_usd_payloads.html
- USD Glossary: https://openusd.org/release/glossary.html
