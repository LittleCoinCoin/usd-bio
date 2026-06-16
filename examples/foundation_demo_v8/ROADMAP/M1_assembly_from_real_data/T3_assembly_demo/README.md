# M1.T3: Assembly Demo

## Goal

Minimal demo scene loading the assembly.

## Creates

`demos/assembly_demo.py` -> `output/assembly_demo.usda`

## Pre-conditions

M1.T2 complete (assembly USD exists).

## Success Gates

`usdview output/assembly_demo.usda` displays ABL kinase with variant switching.

## Steps

| Step | Commit | Description |
|------|--------|-------------|
| S1 | `feat(demos): add assembly demo with world-level variant cascade` | SubLayer assembly, define /World with representation VariantSet, default to "balls". Same pattern as residue_grid_demo.py. |
