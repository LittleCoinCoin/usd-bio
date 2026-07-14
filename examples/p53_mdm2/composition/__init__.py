"""
p53_mdm2.composition -- Pipeline 2 (OpenUSD -> MD ddG) composition layer.

Holds the Genotype (Perturbation) VariantSet builder and the six-field
``bio:`` provenance helper. No eager USD/network imports at package level so
this package is safe to import before ``pxr`` or a network client is loaded.
"""
