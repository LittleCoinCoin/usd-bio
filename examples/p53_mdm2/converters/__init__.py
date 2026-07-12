"""
p53_mdm2.converters -- source-format parsers (PDB -> structured Python).

LAZY imports. v8's converters/__init__ eager-imported an mdtraj-dependent
module, which broke pxr-only interpreters (R00 leave-behind). Here submodules
load on first attribute access. ``pdb_parser`` itself has no heavy deps (pure
Python), but the lazy pattern is preserved so future mdtraj-backed converters
(e.g. trajectory clips) never load at package-import time.
"""

import importlib
from typing import TYPE_CHECKING

__all__ = ["pdb_parser"]


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # pragma: no cover
    from . import pdb_parser  # noqa: F401
