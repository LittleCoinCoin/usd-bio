# Project Setup Guide: USD-Bio for ShinobuLab Research

**Topic**: Complete setup guide for running OpenUSD with USD-Bio and ShinobuLab data
**Source**: Project documentation and environment setup
**Date**: 2026-01-22
**Status**: Draft

---

## Executive Summary

This document provides a comprehensive guide to setting up the USD-Bio project for working with ShinobuLab's computational biology data. It covers:
1. OpenUSD environment configuration (manual setup per terminal session)
2. Project structure and key directories
3. ShinobuLab data location and organization
4. Running the foundation demos
5. Understanding the research workflow patterns

**IMPORTANT**: This project requires manual environment setup. You must export the correct paths in your terminal before running any commands.

---

## 1. OpenUSD Environment Setup

### Prerequisites

To work with USD-Bio, you need to configure your environment to use the correct Python and OpenUSD installation for each terminal session.

### Manual Setup (Required for Each Terminal)

Before running any USD-Bio commands, export these paths:

```bash
# Set the Python path for OpenUSD
export PATH="/Users/hacker/Documents/src/AOUSD/forOUSD/bin:$PATH"

# Set the PYTHONPATH for OpenUSD modules
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"
```

### Verification

After setting up the environment, verify it works:

```bash
which python3
# Should output: /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3

python3 -c "from pxr import Usd; print('OpenUSD imported successfully')"
# Should output: OpenUSD imported successfully
```

### Remember

**You must run these export commands in every new terminal session before working with USD-Bio.**

---

## 2. Project Structure

### USD-Bio Repository

```
usd-bio/
├── src/                    # C++ extension library
├── tests/                  # Test suite
├── examples/               # Example programs and demos
│   ├── foundation_demo/    # Basic PDB to USD conversion
│   ├── foundation_demo_v2/ # Version 2 of foundation demo
│   ├── foundation_demo_v3/ # Version 3 with templates
│   ├── foundation_demo_v4/ # Version 4 improvements
│   ├── foundation_demo_v5/ # Version 5 with variants
│   └── foundation_demo_v6/ # Version 6 - Current development
├── docs/                   # Documentation (Sphinx + Doxygen)
├── __design__/             # Design documents and roadmap
└── __reports__/            # Work reports and analysis
    └── foundation_demo/setup/  # Setup and configuration guides
```

### Key Directories

- **`examples/foundation_demo_v6/`**: Current development focus with atomic and residue templates
- **`__reports__/foundation_demo/analysis/`**: Analysis documents describing LIVRPS patterns
- **`assets/`**: Shared USD assets and templates

---

## 3. ShinobuLab Data Location

### Main Data Repository

```
/Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/
├── files/                  # System setup files
│   ├── atp-complex-solv35.pdb      # Main PDB file (21MB)
│   ├── atp-complex-solv35.prmtop  # Amber topology
│   └── atp-complex-solv35.inpcrd  # Initial coordinates
├── equilibration/          # Equilibration protocol
├── md-simulations/         # Production MD runs (350 runs)
├── pull/                   # REUS (Replica Exchange Umbrella Sampling)
│   ├── rep01/              # Replica 1 data
│   ├── rep02/              # Replica 2 data
│   └── ...                # 50 replicas total
└── analysis/              # Analysis pipeline
    ├── 0_traj/             # Trajectory processing
    ├── 1_comdist/          # COM distance calculations
    ├── 2_angle/            # Angular distributions
    ├── 3_mbar/             # MBAR free energy calculation
    ├── 4_pmf/              # PMF generation
    └── 5_kmeans/           # Clustering analysis
        └── kmeans_center/  # Cluster center PDB files
            ├── center_0.pdb
            ├── center_1.pdb
            └── ...          # 16 cluster centers
```

### Data Overview

- **PDB File**: `atp-complex-solv35.pdb` - ATP complex with solvent (35,000+ atoms)
- **Replicas**: 50 replicas in the `pull/` directory for REUS analysis
- **Cluster Centers**: 16 representative structures from k-means clustering
- **Analysis Results**: PMF profiles, COM distances, angular distributions

---

## 4. Running the Foundation Demos

### Setup First

**Remember**: Export the paths first:

```bash
export PATH="/Users/hacker/Documents/src/AOUSD/forOUSD/bin:$PATH"
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"
```

### Basic Usage

Convert a PDB file to USD:

```bash
# Navigate to foundation demo
cd /Users/hacker/Documents/src/LittleCoinCoin/usd-bio/examples/foundation_demo

# Run the converter
python3 pdb_to_usd.py input.pdb output.usd
```

### Using ShinobuLab Data

```bash
# Convert the main ATP complex
python3 pdb_to_usd.py \
  /Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/files/atp-complex-solv35.pdb \
  atp_complex.usd

# Convert a cluster center
python3 pdb_to_usd.py \
  /Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/analysis/5_kmeans/kmeans_center/center_0.pdb \
  cluster_0.usd
```

### Foundation Demo v6 (Current)

The v6 demo implements the LIVRPS composition patterns:

```bash
cd /Users/hacker/Documents/src/LittleCoinCoin/usd-bio/examples/foundation_demo_v6

# Create atomic templates
python3 create_atomic_templates.py

# Create residue templates (uses atomic templates)
python3 create_residue_templates.py

# Test instantiation
python3 test_atom_instantiation.py
```

---

## 5. Understanding the Research Workflow Patterns

### LIVRPS Composition Principle

OpenUSD resolves data conflicts using the LIVRPS strength ordering:

| Strength | Arc Type | Research Equivalent | Usage in USD-Bio |
|----------|----------|---------------------|------------------|
| 1 (Strongest) | Local | The Lab Notebook | Active experiment, SubLayers |
| 2 | Inherits | The Taxonomy | Semantic classification (e.g., `_Tyrosine_`) |
| 3 | VariantSets | The Hypothesis | Force fields, mutations, replicas |
| 4 | References | The Literature | Standard assets (amino acids, solvents) |
| 5 | Payloads | The Raw Data | Trajectories loaded on demand |
| 6 (Weakest) | Specialize | Rarely Used | Specialized refinements |

### Departmental Layering

The research workflow follows a film production analogy:

```
Project Root (PI View)
├── 05_review.usd          # Global comments and annotations
├── 04_analysis.usd        # Cross-scale correlation
├── 03_microscopy.usd      # Tissue scale
├── 02_systems_bio.usd    # Cell scale
└── 01_md_simulations.usd  # Molecular scale

Department Layer (PhD Student View)
├── Sequence organization
├── 50 Replicas (Shots)
└── Scientific Variant Sets

Asset Layer (Algorithm View)
├── Value Clips
├── Topology + Trajectory
└── On-demand data loading
```

### Scientific Variant Sets

Three key patterns:

1. **Ensemble Variant (ReplicaID)**: 
   - 50 replicas (rep_00 ... rep_50)
   - Swaps Payload pointers to different `.xtc` files
   - Instantly browse statistical distribution

2. **Perturbation Variant (Genotype)**:
   - WildType vs. T315I mutation
   - Swaps residue geometry
   - Visual A/B testing of steric clashes

3. **Parameter Variant (ForceField)**:
   - Amber99 vs. Charmm36
   - Overrides `primvars:charge` and `primvars:mass`
   - Verify parameterization effects

---

## 6. Project Purpose

### Goal

USD-Bio aims to transform computational biology workflows by:

1. **Standardizing Data Representation**: Using OpenUSD as a universal format for biological data
2. **Enabling Collaboration**: Shared scene descriptions for multi-disciplinary teams
3. **Facilitating Visualization**: Industry-standard tools for 3D biological data
4. **Supporting Complex Workflows**: Multi-scale, multi-replica research with proper composition

### Research Questions

- Can OpenUSD's composition engine handle the complexity of multi-scale biology research?
- Can LIVRPS patterns effectively organize scientific workflows?
- Can USD classes provide semantic ontologies for biological data?
- Can VariantSets enable efficient hypothesis testing?

### Expected Outcomes

1. A production-ready USD-Bio schema for biological data
2. Demonstrated workflow patterns for MD simulations, systems biology, and microscopy
3. Integration with existing biology tools (GENESIS, Amber, MDTraj, PyMBAR)
4. Documentation and examples for the research community

---

## 7. Next Steps

### Immediate Tasks

1. ✅ Document environment setup
2. ✅ Document data locations
3. ✅ Document project structure
4. ⏳ Create comprehensive research workflow demo
5. ⏳ Implement Layer Stack with Departmental Organization
6. ⏳ Implement Variant Sets for Hypothesis Testing
7. ⏳ Implement Contextual Review with 3D Annotations

### Long-term Goals

1. Develop USD-Bio C++ extension with biology-specific schemas
2. Create import/export pipelines for PDB, PRMTOP, XTC, etc.
3. Integrate with visualization tools (Hydra, usdview, NVIDIA Omniverse)
4. Establish best practices for scientific USD workflows
5. Publish case studies and documentation

---

## 8. References

- [OpenUSD Documentation](https://openusd.org/docs/)
- [ShinobuLab MD Workflow README](https://github.com/ShinobuLab/md-workflow)
- [LIVRPS Composition](https://openusd.org/release/api/class_usd_stage.html)
- [USD Classes](https://openusd.org/docs/USD-Classes.html)
- [USD VariantSets](https://openusd.org/docs/USD-Variant-Sets.html)

---

## 9. Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'pxr'`

**Solution**: You forgot to export PYTHONPATH. Run:
```bash
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"
```

**Problem**: `python3` not found or wrong version

**Solution**: You forgot to export PATH. Run:
```bash
export PATH="/Users/hacker/Documents/src/AOUSD/forOUSD/bin:$PATH"
```

**Problem**: Large PDB files cause memory issues

**Solution**: Use the PointInstancer for solvent and limit atom count:
```python
# In pdb_to_usd.py, filter out hydrogens or use instancing
```

**Problem**: USD files don't render correctly

**Solution**: Check the upAxis setting:
```python
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
```

---

## 10. Contact

For questions or issues:
- **Eliott Jacopin** - Primary maintainer
- **Ai Shinobu** - Research lead
- **GitHub Issues**: https://github.com/LittleCoinCoin/usd-bio/issues

---

**Last Updated**: 2026-01-22
**Status**: Draft - Awaiting review and testing
