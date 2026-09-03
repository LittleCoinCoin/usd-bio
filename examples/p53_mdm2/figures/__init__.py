"""
p53_mdm2.figures -- poster-figure rendering support.

LAZY imports: ``render_support`` imports ``pxr``, so it is deferred to first
attribute access (PEP 562), same convention as ``p53_mdm2.builders``.
``import p53_mdm2.figures`` alone must not pull ``pxr``.
"""

import importlib
from typing import TYPE_CHECKING

__all__ = ["render_support"]


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # pragma: no cover
    from . import render_support  # noqa: F401
