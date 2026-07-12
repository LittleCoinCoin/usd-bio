"""
examples/p53_mdm2 -- multi-scale p53-MDM2 OpenUSD demonstration package.

Extracted and generalized from foundation_demo_v8 per the R00 reuse map
(__reports__/p53-mdm2/00-architecture_v0.md). Every module here is
root-path-parameterized: the ABL-specific ``/ABLComplex`` root and dataset
atom counts must never appear in this tree.

LAZY imports only.  v8's ``converters/__init__.py`` eager-imported
``xtc_to_clips`` (and therefore ``mdtraj``), which broke interpreters that
carried ``pxr`` but not ``mdtraj``.  We expose submodules lazily via
``__getattr__`` so that ``import p53_mdm2`` (and ``import p53_mdm2.p53_env``)
never pulls ``pxr`` or ``mdtraj`` until a consumer actually needs them.
"""

import importlib
from typing import TYPE_CHECKING

__all__ = ["p53_env", "data", "converters", "builders"]


def __getattr__(name: str):
    """PEP 562 lazy submodule access -- import on first attribute lookup."""
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # pragma: no cover -- static analysis only, never executed
    from . import p53_env, data, converters, builders  # noqa: F401
