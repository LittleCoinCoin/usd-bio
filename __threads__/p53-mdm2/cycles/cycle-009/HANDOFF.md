---
cycle: 9
topic: p53-mdm2
artifacts:
- __reports__/p53-mdm2/17-cycle009_findings_v0.md examples/p53_mdm2/output/p53_mdm2_md_setup_gromacs.usda examples/p53_mdm2/cluster/p53_md/p53_md_submit.sbatch examples/p53_mdm2/templates/gromacs_deck.py
roadmap_refs: []
next_decision: 'FIRST p53-MDM2 MD RUN IS BUILT BUT NOT RUN. Deck (amber99sb-ildn/TIP3P, 0.15 M NaCl, EM -> NVT 100 ps -> NPT 100 ps -> 100 ps NPT prod on 1 dgx1 V100) is emitted from the USD stage output/p53_mdm2_md_setup_gromacs.usda, with job scripts in examples/p53_mdm2/cluster/p53_md/. Suite 63/63. The classifier refused the first cluster write (staging), so nothing was submitted. PI: (Q-016) run it attended with the 3 commands in Q-016 and drop the out files into cluster/evidence/ as .txt, or add a permission rule for unattended staging/submit; (Q-017) accept amber99sb-ildn, add a vetted ff19SB/ff14SB, or treat this run as plumbing only. Then umbod ack.'
outcome: open
---
# Cycle 009 HANDOFF

Outcome: **open**

Next decision: FIRST p53-MDM2 MD RUN IS BUILT BUT NOT RUN. Deck (amber99sb-ildn/TIP3P, 0.15 M NaCl, EM -> NVT 100 ps -> NPT 100 ps -> 100 ps NPT prod on 1 dgx1 V100) is emitted from the USD stage output/p53_mdm2_md_setup_gromacs.usda, with job scripts in examples/p53_mdm2/cluster/p53_md/. Suite 63/63. The classifier refused the first cluster write (staging), so nothing was submitted. PI: (Q-016) run it attended with the 3 commands in Q-016 and drop the out files into cluster/evidence/ as .txt, or add a permission rule for unattended staging/submit; (Q-017) accept amber99sb-ildn, add a vetted ff19SB/ff14SB, or treat this run as plumbing only. Then umbod ack.
