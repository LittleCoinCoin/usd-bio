# M1.T2: Assembly Template

## Goal

Generate ABL kinase + ATP as composed USD stage.

## Creates

`templates/04_create_assembly.py` -> `assets/level4_assemblies/abl_kinase_complex.usda`

## Pre-conditions

- M1.T1 complete (PDB parser)
- `element_templates.usda` exists in `assets/level1_elements/`

## Success Gates

USD file loads in usdview with correct atom positions and colors.

## Steps

| Step | Commit | Description |
|------|--------|-------------|
| S1 | `feat(templates): scaffold assembly template script` | Script structure following 01/02/03 pattern: imports, stage creation, SubLayer element_templates.usda, save. |
| S2 | `feat(templates): create protein chain hierarchy` | Parse PDB via converter, create /ABLComplex/Chain_X/Res_NAME_SEQ/ATOM prims. Each atom inherits from /_class_/ELEMENT. Positions as local translate ops. Bio metadata. |
| S3 | `feat(templates): add representation VariantSet cascade` | VariantSet at complex -> chain -> residue -> atom levels. Same cascade pattern as 03_create_residue_templates.py. |
| S4 | `test(templates): add assembly verification` | Verify function: atom count, sample element inheritance, variant switching, spatial bounds. |
