# Questions

## Q-001 p53-MDM2 input data: where do the topology/trajectory files live, and what format? USDBIO_DATA_DIR was unset in the agent shell. Pipeline 1 extraction assumes a PDB+XTC shape like v8's; if the system ships mmCIF or a non-mdtraj trajectory, pdb_parser/xtc_to_clips need more than parameterization. If no p53-MDM2 MD data exists yet, should cycle-001 start from the 1YCR crystal structure alone (topology-only USD) until a trajectory is available?
*asked: cycle-0*
*priority: soft*
*answer:*

## Q-002 dG binarization threshold (Pipeline 3): what ddG (kcal/mol) cutoff flips the p53-MDM2 complex from bound to unbound, and should a destabilizing variant flip Mdm2N.istate=FALSE only, or also force the node OFF? Pipeline 3 will take the threshold as a parameter regardless, but the demo needs a defensible default.
*asked: cycle-0*
*priority: soft*
*answer:*

