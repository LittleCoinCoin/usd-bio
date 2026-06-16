# Quick Start Reference Card

## Setup (Run in Every Terminal)

```bash
# Set OpenUSD Python path
export PATH="/Users/hacker/Documents/src/AOUSD/forOUSD/bin:$PATH"

# Set OpenUSD Python modules
export PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$PYTHONPATH"
```

## Verify

```bash
which python3
python3 -c "from pxr import Usd; print('OK')"
```

## Convert PDB to USD

```bash
cd /Users/hacker/Documents/src/LittleCoinCoin/usd-bio/examples/foundation_demo
python3 pdb_to_usd.py \
  /Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/files/atp-complex-solv35.pdb \
  atp_complex.usd
```

## Foundation Demo v6

```bash
cd /Users/hacker/Documents/src/LittleCoinCoin/usd-bio/examples/foundation_demo_v6
python3 create_atomic_templates.py
python3 create_residue_templates.py
python3 test_atom_instantiation.py
```

## Data Locations

- **USD-Bio**: `/Users/hacker/Documents/src/LittleCoinCoin/usd-bio/`
- **ShinobuLab**: `/Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/`
- **Main PDB**: `ShinobuLab/files/atp-complex-solv35.pdb`
- **Cluster Centers**: `ShinobuLab/analysis/5_kmeans/kmeans_center/center_*.pdb`

## Key Reports

- `01-project_setup_guide_v0.md` - Complete setup guide
- `02-usd_bio_workflow_brainstorm_v0.md` - Workflow patterns
- `03-usd_bio_LIVRPS_brainstorm_v0.md` - LIVRPS composition
- `05-openusd_workflow_patterns_v0.md` - Departmental layering
- `06-encapsulated_department_architecture_v0.md` - Multi-scale architecture
