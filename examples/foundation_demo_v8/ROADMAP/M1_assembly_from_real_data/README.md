# M1: Assembly from Real Data

## Objective

Parse ABL kinase PDB and create a composed USD assembly in `assets/level4_assemblies/`, viewable in usdview with representation switching.

## Success Gates

- `assets/level4_assemblies/abl_kinase_complex.usda` loads in usdview
- 4,676 atom prims visible, colored via class prim inheritance
- `representation` VariantSet toggles points/balls/vdw/ballstick across entire complex

## Task DAG

```
T1 PDB Parser ----> T2 Assembly Template ----> T3 Assembly Demo
(converters/)       (templates/)                (demos/)
```

## System Info

The PDB file is AMBER-format: no chain ID column, no element column. Two protein chains are separated by TER records (residues 1-276, 277-290), plus ATP ligand (residue 293). Elements are inferred from atom names.
