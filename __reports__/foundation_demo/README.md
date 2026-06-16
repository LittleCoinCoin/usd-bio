# Foundation Demo: Evolutionary Log

This directory tracks the development of the USD-Bio Foundation Demo, showcasing the transition from simple data conversion to a sophisticated, object-oriented biological data architecture.

## Version History

### Version 5 (Current) - "Biological Object Model"
*   **Focus**: Hierarchical composition and visualization variants.
*   **Architecture**: 
    *   Level 1: Atomic Blueprints (`atomic_templates.usd`).
    *   Level 2: Residue Blueprints (`residue_templates.usd`).
    *   Level 3: Data-driven Assembly (`complex_v5.usd`).
*   **Features**: 
    *   Atoms as first-class objects inheriting from element classes.
    *   Residues inheriting from amino-acid classes.
    *   `representation` VariantSet at every level (Atom, Residue, Molecule).
    *   Visual modes: `points`, `balls` (ball-and-stick), `vdw` (space-filling).
    *   Bonds as `UsdGeomBasisCurves` with `thread` and `cylinder` modes.

### Version 4 (Internal Iteration)
*   **Focus**: Departmental separation.
*   **Outcome**: Successfully separated Protein, Ligand, and Solvent into individual layers. PointInstancer implemented for solvent.

### Version 1-3 (Legacy)
*   **Focus**: Basic PDB to USD conversion.
*   **Outcome**: Proof of concept for reading ASCII PDB data and visualizing in `usdview`.

## Active Implementation
*   `examples/foundation_demo_v5/create_atomic_templates.py`
*   `examples/foundation_demo_v5/create_residue_templates.py`
*   `examples/foundation_demo_v5/pdb_to_usd_v5.py`
