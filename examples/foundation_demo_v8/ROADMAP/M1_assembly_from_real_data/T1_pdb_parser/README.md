# M1.T1: PDB Parser

## Goal

Parse `atp-complex-solv35.pdb` into structured Python data.

## Creates

`converters/pdb_parser.py`

## Pre-conditions

PDB file accessible at ShinobuLab path.

## Success Gates

Extracts 4,676 protein+ligand atoms grouped by chain/residue.

## Steps

| Step | Commit | Description |
|------|--------|-------------|
| S1 | `feat(converters): add PDB ATOM record parser` | Parse ATOM lines: atom name, residue name, chain ID, seq number, x/y/z, element. Filter out WAT/Na+/Cl-/MG. |
| S2 | `feat(converters): add chain/residue grouping` | Group atoms into chain -> residue -> atom hierarchy. Handle HID/HIE/HIP, ACE/NME, atp. |
| S3 | `test(converters): add PDB parser verification` | Standalone verify function: atom count, element coverage, residue count, chain IDs. |

## Notes

- AMBER PDB format: no chain ID column (col 21 is blank), no element column (lines are ~67 chars)
- Chain boundaries detected via TER records
- Element inferred from first alphabetic character of atom name
- MG ions at residues 291-292 are excluded (ions, not protein/ligand)
