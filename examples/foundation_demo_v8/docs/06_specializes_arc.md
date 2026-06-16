# The Specializes Composition Arc in OpenUSD

## Overview

The **Specializes** arc is the weakest composition arc in USD's LIVRPS ordering system. It provides a mechanism for creating specialized versions of prims that can still receive updates from their base definitions while allowing local overrides to take precedence.

## LIVRPS Strength Ordering

USD resolves opinions using the LIVRPS mnemonic, ordered from strongest to weakest:

| Position | Arc Type | Strength |
|----------|----------|----------|
| L | **Local** | Strongest |
| I | **Inherits** | |
| V | **VariantSets** | |
| R | **References** | |
| P | **Payloads** | |
| S | **Specializes** | Weakest |

**Key Point:** Specializes is intentionally the weakest arc. This means opinions from specialized prims can be overridden by almost any other composition mechanism.

## PcpArcType Enumeration

In USD's Prim Composition (Pcp) layer, arc types are defined in strength order:

```cpp
enum PcpArcType {
    PcpArcTypeRoot,        // Special root node
    PcpArcTypeInherit,     // Strongest regular arc
    PcpArcTypeVariant,
    PcpArcTypeRelocate,
    PcpArcTypeReference,
    PcpArcTypePayload,
    PcpArcTypeSpecialize,  // Weakest arc
    PcpNumArcTypes
};
```

Both Inherits and Specializes are "class-based arcs":

```cpp
inline bool PcpIsClassBasedArc(PcpArcType arcType) {
    return PcpIsInheritArc(arcType) || PcpIsSpecializeArc(arcType);
}
```

## Specializes vs Inherits: Key Differences

### Inherits (Stronger)
- Opinions from the inherited class are **stronger** than opinions from references/payloads
- Changes to the base class affect instances **unless** the instance has a local override
- Best for: Shared defaults that instances commonly override

### Specializes (Weaker)
- Opinions from the specialized class are **weaker** than opinions from references/payloads
- Changes to the base class **propagate through** to specialized prims
- Specialized prim's direct opinions override the base
- Best for: Refinements where base changes should flow through

### Visual Comparison

```
INHERITS (Strong):
    Local Override > Inherited Value > Referenced Value

SPECIALIZES (Weak):
    Local Override > Referenced Value > Specialized Base Value
```

## When to Use Specializes

### Use Case 1: Material Variants

```usda
#usda 1.0

def "Robot" {
    def "Materials" {
        def Material "Metal" {
            float inputs:diffuseGain = 0
            float inputs:specularRoughness = 0

            def Shader "Surface" {
                asset info:id = @PxrSurface@
            }
        }

        def Material "CorrodedMetal" (
            specializes = </Robot/Materials/Metal>
        ) {
            float inputs:specularRoughness = 0.2

            def Shader "Corrosion" {
                asset info:id = @PxrOSL@
            }
        }
    }
}
```

### Use Case 2: Asset Refinement

```usda
#usda 1.0

def "World" {
    def "Rosie" (
        references = @./Robot.usd@</Robot>
    ) {
        over "Materials" {
            over "Metal" {
                # This override affects CorrodedMetal too
                # because specializes is weaker than references
                float inputs:diffuseGain = 0.3
            }
        }
    }
}
```

## Python API: UsdSpecializes

### Basic Usage

```python
from pxr import Usd, Sdf

stage = Usd.Stage.CreateInMemory()

# Create base prim
base_prim = stage.DefinePrim("/Base", "Xform")
base_prim.CreateAttribute("baseValue", Sdf.ValueTypeNames.Float).Set(1.0)

# Create specialized prim
specialized_prim = stage.DefinePrim("/Specialized", "Xform")

# Add specialization
specializes = specialized_prim.GetSpecializes()
specializes.AddSpecialize("/Base")

print(stage.GetRootLayer().ExportToString())
```

### UsdSpecializes Class Methods

```python
# Get the specializes proxy
specializes = prim.GetSpecializes()

# Add a specialization (returns bool)
success = specializes.AddSpecialize(Sdf.Path("/BasePrim"))

# Remove a specific specialization
success = specializes.RemoveSpecialize(Sdf.Path("/BasePrim"))

# Clear all specializations
success = specializes.ClearSpecializes()

# Set explicit list of specializations
success = specializes.SetSpecializes([Sdf.Path("/Base1"), Sdf.Path("/Base2")])

# Check if authored
has_specializes = prim.HasAuthoredSpecializes()
```

## LIVRPS Evaluation Details

During composition:
- **For most arcs (LIVRP):** Recursively applies LIVERP evaluation (excluding S)
- **For Specializes (S):** Recursively applies full LIVERPS evaluation

This means specializes can compose with other specializes (nested), and the weakest position ensures base changes flow through.

## Best Practices

| When to Use | Specializes | Inherits |
|-------------|-------------|----------|
| Use Case | Refinements | Class defaults |
| Base Updates | Flow through refs | Blocked by refs |
| Strength | Weak (last) | Strong (2nd) |

## References

- OpenUSD Glossary: https://openusd.org/release/glossary.html
- UsdSpecializes API: https://openusd.org/release/api/class_usd_specializes.html
- PcpArcType: https://openusd.org/release/api/pcp_2types_8h.html
