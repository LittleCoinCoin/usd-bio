# PDB-to-USD Composition Patterns

## The Problem

PDB files encode a flat list of atoms with implicit hierarchy (chain → residue → atom). USD needs an explicit prim hierarchy with typed relationships. The mapping seems straightforward, but several non-obvious issues arise at scale.

## Pattern 1: Inferring Structure from AMBER PDB

AMBER-format PDB files lack two fields present in standard PDB: the chain ID column (column 22) and the element column (columns 77-78). Both must be reconstructed.

### Chain detection via TER records

```python
# TER records separate chains. Track segments between TERs.
segments = []
current_segment = []

for line in pdb_file:
    if line.startswith(("ATOM", "HETATM")):
        current_segment.append(parse_atom(line))
    elif line.startswith("TER"):
        if current_segment:
            segments.append(current_segment)
            current_segment = []
```

Each segment gets a chain label (A, B, C... for protein, L for ligand). The first residue name in a segment distinguishes protein from ligand.

### Element inference from atom names

```python
def infer_element(atom_name: str) -> str:
    stripped = atom_name.strip()
    for char in stripped:
        if char.isalpha():
            return char.upper()
    return "X"
```

This works for single-letter elements (H, C, N, O, S, P) which cover all atoms in standard protein + ATP systems. For multi-letter elements (Fe, Zn, Mg), check the full element column if available, or use a two-character lookup table.

## Pattern 2: Prim Name Sanitization

PDB atom names contain characters illegal in USD prim names:

| PDB Name | Problem | USD Name |
|----------|---------|----------|
| `O3'` | Apostrophe | `O3p` |
| `C5*` | Asterisk | `C5s` |
| `Na+` | Plus sign | `Naplus` |
| `Cl-` | Minus sign | `Clminus` |
| `1HG` | Starts with digit | `_1HG` |

```python
def sanitize_name(name: str) -> str:
    result = name.replace("+", "plus").replace("-", "minus")
    result = result.replace("*", "s").replace("'", "p")
    if result and result[0].isdigit():
        result = "_" + result
    return result
```

## Pattern 3: Element Inheritance at Scale

Every atom inherits from a class prim (`/_class_/C`, `/_class_/N`, etc.). With 4,676 atoms, this means 4,676 inherit arcs. The key insight: this is *cheap* in USD because inherits are resolved lazily during composition.

```python
# Class prims defined once in element_templates.usda (sublayered)
# Each atom gets a single inherit arc
atom_prim.GetInherits().AddInherit(f"/_class_/{element}")
```

The class prim provides:
- Sphere geometry (with radius varying by representation variant)
- CPK display color
- Scientific metadata (VDW radius, atomic mass, etc.)

The atom prim provides only:
- `xformOp:translate` (position -- LOCAL opinion, strongest in LIVRPS)
- `bio:atomName`, `bio:serial` (instance-specific metadata)

This separation means changing an element's color updates *all* atoms of that element instantly.

## Pattern 4: VariantSet Cascade Architecture

The representation VariantSet cascades through four levels:

```
/ABLComplex (complex)
  → representation: sets chain variant selections
    /Chain_A (chain)
      → representation: sets residue variant selections
        /SER_2 (residue)
          → representation: sets atom variant selections
            /CA (atom)
              → representation: selects inherited class geometry
```

Each level's variant edit context sets the selection on its children:

```python
# Residue cascade -> atoms
for mode in REPRESENTATIONS:
    res_vset.SetVariantSelection(mode)
    with res_vset.GetVariantEditContext():
        for atom_prim in res_atom_prims:
            atom_prim.GetVariantSets().GetVariantSet(
                "representation").SetVariantSelection(mode)
```

### Gotcha: Build bottom-up, cascade top-down

Atom VariantSets must be created *before* the residue cascade writes variant selections into them. The residue cascade must complete before the chain cascade references it.

## Pattern 5: AMBER Residue Naming Edge Cases

| Residue | Issue | Handling |
|---------|-------|----------|
| HID, HIE, HIP | Histidine protonation variants | Preserve as-is (different atom counts) |
| ACE, NME | Terminal caps | Include as regular residues |
| atp | Lowercase in AMBER | Preserve case, assign to ligand chain |
| MG | Magnesium cofactor ion | Exclude (not protein/ligand) |
| WAT, Na+, Cl- | Solvent/ions | Exclude |

## Scaling Considerations

| Atom Count | File Size | Generation Time | usdview Load |
|-----------|-----------|----------------|-------------|
| ~5K (protein+ligand) | 7.6 MB .usda | ~30s | Smooth |
| ~50K (+ some solvent) | ~75 MB .usda | ~5 min | Sluggish |
| ~189K (full solvated) | ~300 MB .usda | Impractical | Impractical |

For systems beyond ~10K atoms, consider:
- **UsdGeomPoints** instead of individual Xform prims (single prim with position array)
- **PointInstancer** for identical molecules (e.g., 61K water molecules)
- **Binary .usdc** format instead of text .usda (5-10x smaller, faster I/O)
- **Payloads** for deferred loading of heavy components (solvent shell)

The per-atom Xform approach used here is ideal for small-to-medium structures where individual atom selection, metadata, and variant switching are important. For large systems, a hybrid approach (Xforms for protein, PointInstancer for solvent) provides the best balance of interactivity and functionality.
