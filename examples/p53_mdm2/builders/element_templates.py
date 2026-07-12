#!/usr/bin/env python3
"""
Element class-template builder -- the /_class_/<symbol> biological taxonomy.

Generalized (reuse-as-is core) from foundation_demo_v8/templates/
01_create_element_templates.py. Authors abstract ``class`` prims under
``/_class_`` carrying authoritative bio: metadata (Bondi vdW radius, CPK
color, atomic number/mass, electronegativity) plus a ``representation``
VariantSet whose per-mode Sphere geometry uses scientifically-scaled radii.

Concrete atoms later ``inherits`` these class prims (USD Inherits arc =
biological taxonomy, CLAUDE.md Key Concept #2).

Two entry points:
- :func:`build_element_classes` authors classes into a caller-supplied stage
  (so the assembly builder can emit a single self-contained artifact).
- :func:`create_element_templates` writes a standalone templates .usda.

Patterns applied (from usd-bio docs):
- 02_inherits_arc.md: CreateClassPrim() for templates
- 03_variantsets_arc.md: SetVariantSelection() BEFORE GetVariantEditContext()
- 08_schemas_attributes.md: custom bio: namespace for scientific metadata
"""

import os
import sys

# Make the package importable when run as a script (python builders/...py).
_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from pxr import Usd, UsdGeom, Sdf, Gf

from p53_mdm2.data import ELEMENTS, get_scaled_radius
from p53_mdm2 import p53_env

REPRESENTATIONS = list(p53_env.DEFAULT_REPRESENTATIONS)


def build_element_classes(stage, symbols=None, representations=None):
    """Author /_class_ scope + /_class_/<symbol> class prims into ``stage``.

    Args:
        stage: an open ``Usd.Stage`` to author into.
        symbols: iterable of element symbols to build (e.g. {"C","N","O","S"}).
            ``None`` builds every element in the :data:`ELEMENTS` table. Passing
            only the elements a structure actually uses keeps artifacts lean.
        representations: visual-mode variant names; defaults to the project's
            four canonical modes.

    Returns:
        list of the class-prim paths authored, in build order.
    """
    if representations is None:
        representations = REPRESENTATIONS
    if symbols is None:
        symbols = list(ELEMENTS.keys())

    # Create the class scope (abstract container for templates).
    stage.CreateClassPrim("/_class_")

    authored = []
    for symbol in symbols:
        if symbol not in ELEMENTS:
            raise ValueError(f"Unknown element symbol: {symbol!r}")
        data = ELEMENTS[symbol]
        class_path = f"/_class_/{symbol}"
        class_prim = stage.CreateClassPrim(class_path)

        # --- scientific metadata (bio: namespace) ---
        class_prim.CreateAttribute("bio:symbol", Sdf.ValueTypeNames.Token).Set(symbol)
        class_prim.CreateAttribute("bio:name", Sdf.ValueTypeNames.String).Set(data["name"])
        class_prim.CreateAttribute("bio:atomicNumber", Sdf.ValueTypeNames.Int).Set(data["atomic_number"])
        class_prim.CreateAttribute("bio:atomicMass", Sdf.ValueTypeNames.Float).Set(data["atomic_mass"])
        class_prim.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(data["vdw_radius"])
        class_prim.CreateAttribute("bio:covalentRadius", Sdf.ValueTypeNames.Float).Set(data["covalent_radius"])
        class_prim.CreateAttribute("bio:electronegativity", Sdf.ValueTypeNames.Float).Set(data["electronegativity"])
        class_prim.CreateAttribute("bio:notes", Sdf.ValueTypeNames.String).Set(data["bio_notes"])
        cpk = Gf.Vec3f(*data["cpk_color"])
        class_prim.CreateAttribute("bio:cpkColor", Sdf.ValueTypeNames.Color3f).Set(cpk)

        # --- representation VariantSet (per-mode Sphere geometry) ---
        vset = class_prim.GetVariantSets().AddVariantSet("representation")
        for mode in representations:
            vset.AddVariant(mode)
        for mode in representations:
            # SetVariantSelection BEFORE GetVariantEditContext (03_variantsets_arc).
            vset.SetVariantSelection(mode)
            with vset.GetVariantEditContext():
                sphere = UsdGeom.Sphere.Define(stage, f"{class_path}/Sphere")
                radius = get_scaled_radius(symbol, mode)
                sphere.CreateRadiusAttr(radius)
                sphere.CreateDisplayColorAttr([cpk])
                sphere.CreateExtentAttr(
                    [(-radius, -radius, -radius), (radius, radius, radius)]
                )
        vset.ClearVariantSelection()
        authored.append(class_path)

    return authored


def create_element_templates(output_path, symbols=None, representations=None):
    """Write a standalone element-templates .usda (fresh stage)."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, p53_env.METERS_PER_UNIT)  # Ångström
    stage.SetMetadata("comment", "Element class templates with scientific metadata")

    authored = build_element_classes(stage, symbols=symbols, representations=representations)
    stage.Save()

    print(f"Created: {output_path}")
    print(f"  Element classes: {len(authored)} -> {[p.split('/')[-1] for p in authored]}")
    return output_path


if __name__ == "__main__":
    out_dir = p53_env.output_dir()
    os.makedirs(out_dir, exist_ok=True)
    create_element_templates(os.path.join(out_dir, "element_templates.usda"))
