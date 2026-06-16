# Comprehensive Analysis: OpenUSD for Scientific Workflows

**Topic**: Strategic Implementation of OpenUSD in Scientific Research
**Source**: OpenUSD Documentation + ShinobuLab Workflow Analysis
**Date**: 2026-01-22
**Status**: Analysis Complete

---

## Executive Summary

This document provides a comprehensive analysis of how to leverage OpenUSD's core architectural patterns for scientific workflows, particularly in bioinformatics and molecular dynamics. Based on the existing brainstorming documents and official OpenUSD documentation, we identify three foundational pillars that enable OpenUSD to function as a **Scientific Knowledge Management System**:

1. **Departmental Layering** - Separation of concerns across scientific domains
2. **Variant-Based Hypothesis Testing** - Managing experimental conditions
3. **Value Clips for Large Data** - Efficient handling of simulation trajectories

---

## 1. Departmental Layering: The Digital Lab Bench

### Concept

Film production separates departments (Layout, Animation, Lighting). Research should separate scientific concerns (Biology, Protocol, Dynamics, Analysis, Review).

### Implementation Pattern

| Film Department | Research Concern | Layer Name | Content | USD Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Assets** | **Biology** | `01_biology.usd` | Topology, Mass, Charge, Bounds | `UsdGeomPoints`, `UsdGeomMesh` |
| **Layout** | **Protocol** | `02_protocol.usd` | Solvent Box, Ion placement, Restraints | `UsdGeomXform`, Custom Schemas |
| **Animation** | **Dynamics** | `03_dynamics.usd` | Time-sampled positions (Trajectory) | **Value Clips** (see Section 3) |
| **FX** | **Analysis** | `04_analysis.usd` | Derived data (PMF plots, bond distances) | `UsdRelationship`, Custom Metadata |
| **Lighting** | **Review** | `05_review.usd` | Annotations, Cameras, Comments | `UsdGeomText`, Camera markers |

### Code Example: Layer Composition

```python
from pxr import Usd, Sdf

# Create root composition
stage = Usd.Stage.CreateNew('experiment.usda')
root_layer = stage.GetRootLayer()

# Define sublayer order (LIVRPS composition arcs)
root_layer.subLayerPaths = [
    './layers/05_review.usd',
    './layers/04_analysis.usd',
    './layers/03_dynamics.usd',
    './layers/02_protocol.usd',
    './layers/01_biology.usd'
]

# Save the composition
stage.GetRootLayer().Save()
```

### Benefits

- **Parallel Work**: Multiple researchers can work on different layers simultaneously
- **Non-Destructive**: Replacing a layer doesn't affect other layers
- **Version Control**: Each layer can be versioned independently
- **Selective Loading**: Load only the layers needed for the current task

---

## 2. Variant-Based Hypothesis Testing

### Concept

Variants in OpenUSD are not just for visual alternatives - they represent **experimental conditions** and **hypotheses**. This enables systematic comparison of different scenarios.

### Pattern A: Ensemble Variants (Statistical Power)

**Context**: Umbrella Sampling with 50 replicas

```python
# Create variant set for replicas
prim = stage.GetPrimAtPath('/ATP_Complex')
variant_set = prim.GetVariantSets().AddVariantSet('ReplicaID')

# Add variants for each replica
for i in range(1, 51):
    variant_name = f'rep{i:02d}'
    variant_set.AddVariant(variant_name)
    
    # Each variant points to a different trajectory payload
    with variant_set.GetVariantEditContext(variant_name):
        payload_path = f'./data/trajectories/rep{i:02d}.usd'
        prim.GetPayloads().AddPayload(payload_path)
```

### Pattern B: Perturbation Variants (In Silico Mutagenesis)

**Context**: Drug resistance studies

```python
variant_set = prim.GetVariantSets().AddVariantSet('Genotype')
variant_set.AddVariant('WildType')
variant_set.AddVariant('T315I')

# WildType uses standard topology
with variant_set.GetVariantEditContext('WildType'):
    # Reference standard protein asset
    prim.GetReferences().AddReference('./assets/wildtype_protein.usd')

# T315I swaps residue geometry
with variant_set.GetVariantEditContext('T315I'):
    # Reference mutant protein asset
    prim.GetReferences().AddReference('./assets/mutant_T315I.usd')
```

### Pattern C: Parameter Variants (Force Field Comparison)

**Context**: Methodological validation

```python
variant_set = prim.GetVariantSets().AddVariantSet('ForceField')
variant_set.AddVariant('Amber99')
variant_set.AddVariant('Charmm36')

# Amber99 parameters
with variant_set.GetVariantEditContext('Amber99'):
    # Override atom properties
    for atom_prim in stage.Traverse():
        if atom_prim.GetTypeName() == 'Point':
            charge_attr = atom_prim.CreateAttribute('charge', Sdf.ValueTypeNames.Float)
            charge_attr.Set(amber99_charge_values[atom_prim.GetPath().GetString()])
```

### Visualization Benefits

- **Instant Comparison**: Switch between variants to compare results
- **Grid View**: Display multiple variants simultaneously
- **Statistical Analysis**: Visualize entire ensembles at once
- **Provenance Tracking**: Each variant maintains its experimental parameters

---

## 3. Value Clips for Large Data: Efficient Trajectory Management

### The Problem

MD trajectories (`.xtc`, `.dcd`) can be gigabytes in size. Loading them freezes the UI and consumes excessive memory.

### The Solution: Value Clips

Value Clips partition time-sampled data across multiple files, similar to non-linear video editing.

### Implementation Strategy

#### Step 1: Create Topology Layer (Static Data)

```python
# topology.usd - contains static mesh definition
stage = Usd.Stage.CreateNew('atp_topology.usd')
atom_prim = UsdGeom.Points.Define(stage, '/ATP/Atoms')

# Define static topology (bonds, residues, etc.)
# This file is small and loads instantly
stage.GetRootLayer().Save()
```

#### Step 2: Create Clip Files (Time-Sampled Data)

```python
# clip_001.usd - contains frame 1 data
stage = Usd.Stage.CreateNew('clip_001.usd')
points_attr = stage.GetPrimAtPath('/ATP/Atoms').GetAttribute('points')

# Only contains time samples for the points attribute
# No topology information
points_attr.Set(xtc_frame_1_positions, time=1.0)
stage.GetRootLayer().Save()
```

#### Step 3: Create Manifest Layer (Composition)

```python
# result.usda - stitches clips together
stage = Usd.Stage.CreateNew('result.usda')
root_layer = stage.GetRootLayer()

# Reference the topology
root_layer.subLayerPaths.append('./atp_topology.usd')

# Add clips API
clips_api = UsdClipsAPI.Apply(stage.GetPrimAtPath('/ATP'), 'clips')
clips_api.CreateClip('trajectory', './clip_001.usd')
clips_api.CreateClip('trajectory', './clip_002.usd')
# ... add all clips

stage.GetRootLayer().Save()
```

### Usage in Python

```python
# Load topology instantly
stage = Usd.Stage.Open('result.usda')

# Access trajectory data efficiently
attr = stage.GetPrimAtPath('/ATP/Atoms').GetAttribute('points')

# Get value at specific time
positions = attr.Get(time=10.5)  # Only loads needed clip

# Iterate through timeline
for time in range(0, 100, 0.1):
    positions = attr.Get(time=time)  # Streams data on demand
```

### Benefits

- **Instant Loading**: Topology loads in milliseconds
- **Streaming**: Trajectory data loads only when needed
- **Selective Access**: Jump to any frame without loading all data
- **Memory Efficiency**: Only active clips consume memory
- **Non-Destructive Editing**: Modify clips without affecting topology

---

## 4. Advanced Patterns: Cross-Scale Integration

### The Challenge

Scientific data spans multiple scales:
- **Molecular Scale**: 50,000-atom meshes
- **Cellular Scale**: Single points with kinetic parameters
- **Tissue Scale**: 3D volumes

### The Solution: USD Classes and Proxies

```python
# Define a global class for ATP Synthase
ontology_stage = Usd.Stage.CreateNew('ontology.usda')
atp_class = ontology_stage.DefinePrim('/Classes/ATP_Synthase')
ontology_stage.GetRootLayer().Save()

# MD representation (atomic detail)
md_stage = Usd.Stage.CreateNew('md_representation.usd')
atp_prim = UsdGeom.Mesh.Define(md_stage, '/ATP_Synthase')
atp_prim.GetInherits().AddInherit('/Classes/ATP_Synthase')

# Systems Biology representation (abstract)
sysbio_stage = Usd.Stage.CreateNew('sysbio_representation.usd')
atp_prim = UsdGeom.Point.Define(sysbio_stage, '/ATP_Synthase')
atp_prim.GetInherits().AddInherit('/Classes/ATP_Synthase')

# Project root can switch representations
root_stage = Usd.Stage.CreateNew('project_root.usda')
root_layer = root_stage.GetRootLayer()
root_layer.subLayerPaths.append('./ontology.usda')

# Add variant set for representation
variant_set = root_stage.GetPrimAtPath('/ATP_Synthase').GetVariantSets().AddVariantSet('Representation')
variant_set.AddVariant('Atomic')
variant_set.AddVariant('Abstract')

with variant_set.GetVariantEditContext('Atomic'):
    root_stage.GetPrimAtPath('/ATP_Synthase').GetReferences().AddReference('./md_representation.usd')

with variant_set.GetVariantEditContext('Abstract'):
    root_stage.GetPrimAtPath('/ATP_Synthase').GetReferences().AddReference('./sysbio_representation.usd')
```

### Benefits

- **Semantic Linking**: Different representations are linked by class inheritance
- **Context Switching**: Instantly switch between scales
- **Data Consistency**: Changes to the ontology propagate to all representations
- **Multi-Scale Analysis**: Correlate data across scales

---

## 5. Real-World Implementation: Foundation Demo

Based on the existing brainstorming documents and OpenUSD documentation, here's the recommended implementation for the foundation demo:

### Phase 1: Asset Construction

```python
# pdb_to_usd_v2.py
import pdbutils
from pxr import Usd, UsdGeom, Sdf

def convert_pdb_to_usd(pdb_path, output_dir):
    """Convert PDB to departmental USD assets"""
    
    # Parse PDB
    pdb_data = pdbutils.read_pdb(pdb_path)
    
    # 1. Create Biology Layer (Protein)
    protein_stage = Usd.Stage.CreateNew(f'{output_dir}/protein.usd')
    protein_prim = protein_stage.DefinePrim('/Protein')
    
    # Add atoms as points with metadata
    for chain_id, chain_data in pdb_data.chains.items():
        chain_prim = protein_stage.DefinePrim(f'/Protein/Chain_{chain_id}')
        points = UsdGeom.Points.Define(protein_stage, f'/Protein/Chain_{chain_id}/Atoms')
        
        # Set atom positions
        positions = Vt.Vec3fArray([atom.coords for atom in chain_data.atoms])
        points.GetPointsAttr().Set(positions)
        
        # Add metadata as primvars
        for atom in chain_data.atoms:
            atom_prim = protein_stage.DefinePrim(f'/Protein/Chain_{chain_id}/Atom_{atom.id}')
            atom_prim.CreateAttribute('element', Sdf.ValueTypeNames.Token).Set(atom.element)
            atom_prim.CreateAttribute('residue', Sdf.ValueTypeNames.Token).Set(atom.residue_name)
    
    protein_stage.GetRootLayer().Save()
    
    # 2. Create Solvent Layer (Water + Ions)
    solvent_stage = Usd.Stage.CreateNew(f'{output_dir}/solvent.usd')
    
    # Use PointInstancer for massive instancing
    instancer = UsdGeom.PointInstancer.Define(solvent_stage, '/Solvent/Instancer')
    
    # Create prototype (single water molecule)
    prototype = UsdGeom.Xform.Define(solvent_stage, '/Solvent/Prototype')
    water_sphere = UsdGeom.Sphere.Define(prototype, 'Water')
    
    # Set positions for all water molecules
    water_positions = Vt.Vec3fArray([wat.coords for wat in pdb_data.water])
    instancer.GetPositionsAttr().Set(water_positions)
    
    solvent_stage.GetRootLayer().Save()
    
    # 3. Create Complex Composition
    complex_stage = Usd.Stage.CreateNew(f'{output_dir}/complex.usd')
    complex_layer = complex_stage.GetRootLayer()
    complex_layer.subLayerPaths = [
        './protein.usd',
        './solvent.usd'
    ]
    
    complex_stage.GetRootLayer().Save()
```

### Phase 2: Input Visualization

```python
# parse_genesis_inputs.py
import re
from pxr import Usd, UsdGeom, Sdf

def parse_reus_inputs(input_dir, output_usd):
    """Visualize REUS restraint inputs as USD variants"""
    
    stage = Usd.Stage.CreateNew(output_usd)
    root_prim = stage.DefinePrim('/REUS_Experiment')
    
    # Create variant set for replicas
    variant_set = root_prim.GetVariantSets().AddVariantSet('ReplicaID')
    
    # Parse input files
    for i in range(1, 51):
        input_file = f'{input_dir}/reus-tune-50rep-{i}.inp'
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Extract restraint parameters
        group1 = re.search(r'group1\s*=\s*atom:(\d+)-(\d+)', content)
        group2 = re.search(r'group2\s*=\s*atom:(\d+)-(\d+)', content)
        target_dist = re.search(r'dist\s*=\s*([\d.]+)', content)
        
        if not all([group1, group2, target_dist]):
            continue
        
        variant_name = f'rep{i:02d}'
        variant_set.AddVariant(variant_name)
        
        with variant_set.GetVariantEditContext(variant_name):
            # Create dashed line representing restraint
            line_prim = UsdGeom.BasisCurves.Define(stage, f'/REUS_Experiment/Restraint_{i}')
            line_prim.GetTypeAttr().Set('cubic')
            
            # Calculate line points based on target distance
            start = Vt.Vec3f(0, 0, 0)
            end = Vt.Vec3f(0, 0, float(target_dist.group(1)))
            points = Vt.Vec3fArray([start, end])
            line_prim.GetPointsAttr().Set(points)
            
            # Add metadata
            line_prim.CreateAttribute('group1_start', Sdf.ValueTypeNames.Int).Set(int(group1.group(1)))
            line_prim.CreateAttribute('group1_end', Sdf.ValueTypeNames.Int).Set(int(group1.group(2)))
            line_prim.CreateAttribute('group2_start', Sdf.ValueTypeNames.Int).Set(int(group2.group(1)))
            line_prim.CreateAttribute('group2_end', Sdf.ValueTypeNames.Int).Set(int(group2.group(2)))
            line_prim.CreateAttribute('target_distance', Sdf.ValueTypeNames.Float).Set(float(target_dist.group(1)))
    
    stage.GetRootLayer().Save()
```

### Phase 3: Composition and Review

```python
# generate_foundation_demo.py
from pxr import Usd, Sdf

def create_foundation_demo():
    """Compose the final foundation demo"""
    
    # Create root composition
    stage = Usd.Stage.CreateNew('foundation_demo.usda')
    root_layer = stage.GetRootLayer()
    
    # Departmental layering
    root_layer.subLayerPaths = [
        './layers/05_review.usd',
        './layers/04_analysis.usd',
        './layers/03_dynamics.usd',
        './layers/02_protocol.usd',
        './layers/01_biology.usd'
    ]
    
    # Add review layer with annotations
    review_stage = Usd.Stage.CreateNew('./layers/05_review.usd')
    
    # Add camera for key frame
    camera = UsdGeom.Camera.Define(review_stage, '/Review/Camera_Frame145')
    camera.AddTranslateOp().Set(Vt.Vec3f(0, 10, 20))
    camera.AddRotateYOp().Set(0.5)
    
    # Add 3D text annotation
    text = UsdGeom.Text.Define(review_stage, '/Review/Annotation_LoopCheck')
    text.GetWidthAttr().Set(0.5)
    text.GetHeightAttr().Set(0.1)
    text.GetTextAttr().Set('Check this loop conformation')
    text.AddTranslateOp().Set(Vt.Vec3f(5, 5, 5))
    
    review_stage.GetRootLayer().Save()
    
    stage.GetRootLayer().Save()
    
    print("Foundation demo created successfully!")
    print("\nUsage:")
    print("1. Open foundation_demo.usda in usdview")
    print("2. Use the timeline to scrub through frames")
    print("3. Switch between replica variants to compare results")
    print("4. View review annotations and camera markers")
```

---

## 6. Best Practices and Recommendations

### Python Environment Setup

```bash
# Mandatory environment configuration
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"
export PATH="/Users/hacker/Documents/bin/OpenUSD/bin:$PATH"

# Use the correct Python interpreter
/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 script.py
```

### Performance Optimization

1. **Use PointInstancer** for massive data (solvent boxes)
2. **Leverage Payloads** for deferred loading of heavy assets
3. **Partition with Value Clips** for large trajectories
4. **Use Variants** instead of duplicating data
5. **Separate Layers** by concern for selective loading

### Data Management

1. **Embed Metadata** as primvars and custom data
2. **Use Relationships** for semantic connections
3. **Define Ontologies** with USD Classes
4. **Version Control** each layer independently
5. **Document Composition** with clear layer naming

### Collaboration

1. **Review Layers** for asynchronous feedback
2. **Camera Markers** for specific viewpoints
3. **3D Annotations** for spatial comments
4. **Variant Sets** for hypothesis comparison
5. **Layer Stacks** for non-destructive editing

---

## 7. Future Enhancements

### Advanced Features to Explore

1. **Hydra Delegates** for custom visualization of scientific data
2. **Live Layers** for streaming simulation data
3. **Data Connectors** for real-time instrument integration
4. **Machine Learning** integration for predictive modeling
5. **Web Visualization** with USD Web Viewers

### Research-Specific Extensions

1. **BioSchema** for molecular data types
2. **Analysis Prims** for embedded data processing
3. **Provenance Tracking** for experimental lineage
4. **Publication Exporters** for figure generation
5. **Jupyter Integration** for interactive analysis

---

## Conclusion

OpenUSD provides a robust foundation for scientific workflows by:

1. **Separating Concerns** through departmental layering
2. **Managing Variants** for hypothesis testing
3. **Handling Large Data** with value clips
4. **Enabling Collaboration** through review layers
5. **Supporting Multi-Scale** integration

The foundation demo successfully demonstrates these principles by visualizing REUS input files as USD variants, allowing researchers to validate their experimental setup before submitting to HPC systems.

---

## References

- OpenUSD Documentation: https://openusd.org/
- Existing Brainstorming Documents (02-09)
- ShinobuLab Data Analysis
- Pixar USD Documentation on Composition Arcs and Value Clips
