# Assembly Demo User Guide

## What This Demo Is

This demo displays the **ABL kinase + ATP complex** -- a real protein structure from molecular dynamics simulation data (ShinobuLab). ABL kinase is a tyrosine kinase involved in chronic myeloid leukemia; ATP (adenosine triphosphate) is its substrate. The structure contains:

- **Chain A**: 276 residues (4,426 atoms) -- the kinase domain
- **Chain B**: 14 residues (207 atoms) -- a peptide substrate
- **Chain L**: ATP ligand (43 atoms)
- **Total**: 4,676 atoms with full atomic detail (explicit hydrogens)

Every atom is colored by element using CPK conventions (carbon=dark gray, nitrogen=blue, oxygen=red, sulfur=yellow, phosphorus=orange, hydrogen=white), inherited from class prim templates.

## How to Run

```bash
# From the foundation_demo_v8 directory:
cd examples/foundation_demo_v8

# Set up OpenUSD environment
export PATH="/Users/hacker/Documents/src/AOUSD/forOUSD/bin:$PATH"
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"

# Step 1: Generate element templates (if not already done)
python3 templates/01_create_element_templates.py

# Step 2: Generate assembly from PDB
python3 templates/04_create_assembly.py

# Step 3: Create demo scene
python3 demos/assembly_demo.py

# Step 4: View
usdview output/assembly_demo.usda
```

### Expected Output

```
Created: .../output/assembly_demo.usda
Representations: ['points', 'balls', 'vdw', 'ballstick']
Default: balls
```

## What to Observe

### Prim Hierarchy (Composition Tab)

In the usdview tree browser, expand the hierarchy:

```
/World
  /ABLComplex
    /Chain_A
      /ACE_1        (N-terminal cap)
        /HH31       (hydrogen atom, inherits /_class_/H)
        /CH3        (carbon atom, inherits /_class_/C)
        ...
      /SER_2        (serine residue)
        /N, /H, /CA, /HA, /CB, ...
      ...
    /Chain_B
      /ACE_277 ... /NME_290
    /Chain_L
      /atp_293      (ATP ligand)
        /O1G, /PG, /O2G, ...  (phosphate groups)
        /C8, /N7, /C5, ...    (adenine ring)
```

### Representation Switching

Select `/World` in the prim browser, then change the `representation` variant:

| Mode | What You See | Use Case |
|------|-------------|----------|
| `points` | Tiny dots (0.15x VDW radius) | Overview of full complex |
| `balls` | Medium spheres (0.3x VDW radius) | Default, balanced view |
| `vdw` | Full space-filling (1.0x VDW radius) | Surface contacts, steric clashes |
| `ballstick` | Small spheres (0.25x VDW radius) | Bond visualization (future) |

The variant cascade propagates from `/World` through `/ABLComplex`, each chain, each residue, down to every atom -- switching all 4,676 atoms simultaneously.

### Element Colors

Click any atom and inspect its properties:
- `bio:element` -- the chemical element (C, N, O, H, S, P)
- `bio:atomName` -- PDB atom name (CA, CB, OG, etc.)
- `bio:serial` -- PDB atom serial number

Colors come from the class prim inheritance (`/_class_/C` provides carbon's dark gray, etc.).

## Why It Matters

This demo validates three core claims of the OpenUSD-for-research architecture:

1. **Biological taxonomy maps to class prims.** Just as film production uses class prims for character rigs shared across shots, biological structures use element classes shared across thousands of atoms. Define once in `/_class_/`, inherit everywhere.

2. **PDB hierarchy maps to USD hierarchy.** The Chain -> Residue -> Atom hierarchy of a protein structure is naturally expressed as nested USD prims. Each level carries its own metadata (`bio:` namespace) and can be independently queried, styled, or composed.

3. **VariantSets scale across complex structures.** A single variant selection at the root toggles 4,676 atom representations through a cascade. This is the same mechanism film pipelines use for LOD switching -- applied here to scientific visualization modes.

## USD Patterns in Action

| LIVRPS Arc | How It's Used | Research Equivalent |
|-----------|--------------|---------------------|
| **Local** | Each atom's `xformOp:translate` sets its 3D position | Atomic coordinates from PDB |
| **Inherits** | Every atom inherits geometry + color from `/_class_/ELEMENT` | Biological taxonomy (element properties) |
| **VariantSets** | `representation` variant controls visualization mode | Switching between analysis views |
| **SubLayers** | Assembly sublayers `element_templates.usda` for class definitions | Separating concerns (data vs. display templates) |
