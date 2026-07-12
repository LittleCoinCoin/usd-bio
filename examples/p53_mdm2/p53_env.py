"""
p53_env -- lightweight configuration + path resolvers for the p53_mdm2 package.

Zero USD imports; safe to import before the OpenUSD environment is loaded
(model: foundation_demo_v8/usdbio_env.py). Everything here is a plain-Python
path/string helper so the config can be threaded through parser -> builder ->
tests without dragging in ``pxr``.

The system root prim path is a PARAMETER, not a hard-coded literal. ``/ABLComplex``
(v8's chimera hazard) must never appear anywhere in this package; downstream
generators default to :data:`DEFAULT_ROOT_PATH` and callers may override it.
"""

import os

# ---------------------------------------------------------------------------
# Package-relative locations
# ---------------------------------------------------------------------------
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def structures_dir() -> str:
    """Directory holding committed input structures (PDB/mmCIF), e.g. 1ycr.pdb."""
    return os.path.join(PACKAGE_DIR, "data", "structures")


def get_structure_path(name: str) -> str:
    """Absolute path to a committed input structure by filename."""
    return os.path.join(structures_dir(), name)


def output_dir() -> str:
    """Directory holding committed .usda artifacts (evidence of 'done')."""
    return os.path.join(PACKAGE_DIR, "output")


# ---------------------------------------------------------------------------
# External MD data root (optional -- parity with v8; not needed for a
# committed crystal structure like 1YCR, but kept for future trajectory work).
# ---------------------------------------------------------------------------
def get_data_dir() -> str:
    """Return the external MD data root from ``USDBIO_DATA_DIR``.

    Fails loudly with an actionable message when unset so every consumer fails
    at this single call-site rather than deep inside a script. Not required for
    the topology-only Pipeline 1 deliverable (1YCR ships committed in-package).
    """
    data_dir = os.environ.get("USDBIO_DATA_DIR")
    if not data_dir:
        raise EnvironmentError(
            "USDBIO_DATA_DIR is not set. "
            "Export the path to your MD data directory before running "
            "scripts that consume external trajectory data.\n"
            "  export USDBIO_DATA_DIR=/path/to/data"
        )
    return data_dir


# ---------------------------------------------------------------------------
# Parameterized defaults threaded through the pipeline
# ---------------------------------------------------------------------------
# The default USD root prim path for the p53-MDM2 complex. PARAMETERIZED --
# callers override via the ``root_path`` argument. Deliberately NOT the v8
# ``/ABLComplex`` literal (the anti-chimera invariant, R00 Contracts).
DEFAULT_ROOT_PATH = "/p53_MDM2_complex"

# The canonical visual-mode VariantSet options (CLAUDE.md convention).
DEFAULT_REPRESENTATIONS = ("points", "balls", "vdw", "ballstick")

# Ångström length unit for USD stages: 1 Å = 1e-10 m (project convention).
METERS_PER_UNIT = 1e-10
