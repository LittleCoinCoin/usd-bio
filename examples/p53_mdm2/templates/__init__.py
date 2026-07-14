"""
examples/p53_mdm2/templates -- reusable USDBio parameter-representation templates.

Currently holds the MD-setup-parameter representation (``bio:md:`` namespace,
:mod:`p53_mdm2.templates.md_parameters`), the greenfield USDBio concern promoted
to the critical path by the PI in Q-003 (the project runs its own p53-MDM2 MD).

LAZY imports only (same discipline as the package root): ``import
p53_mdm2.templates`` must not pull ``pxr`` until a consumer touches a submodule.
"""

import importlib
from typing import TYPE_CHECKING

__all__ = ["md_parameters"]


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:  # pragma: no cover
    from . import md_parameters  # noqa: F401
