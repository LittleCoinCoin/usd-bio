"""
p53_mdm2.builders -- USD stage generators (element-class templates, assembly).

LAZY imports: these modules import ``pxr``, so we defer the import to first
attribute access (PEP 562). ``import p53_mdm2.builders`` alone must not pull
``pxr`` -- consumers that only need the config or data must not be forced into
the OpenUSD runtime.
"""

import importlib
from typing import TYPE_CHECKING

__all__ = ["element_templates", "build_assembly"]


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # pragma: no cover
    from . import element_templates, build_assembly  # noqa: F401
