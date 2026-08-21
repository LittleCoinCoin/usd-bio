#!/usr/bin/env python3
"""
fig_mod_units.py -- poster tile "mod-units": numbers with units.

Registers ``mod-units`` (see ``make_poster_figures.py`` for the harness this
plugs into). The claim of this tile is that the stage carries numbers WITH
their units -- so every value drawn here is read from the composed USD
stage at run time via the ``pxr`` API, never typed as a literal in the
drawing code. The one exception is the gate block at the bottom of this
file, which holds the literal expected values purely to assert the stage
still agrees with them; if it ever disagrees, this module raises rather
than silently drawing the (wrong) authored number.

Units are a separate story. No ``bio:`` attribute on the class-template
prims carries a unit string -- ``bio:atomicMass``, ``bio:vdwRadius`` and
``bio:covalentRadius`` are bare floats (see ``builders/element_templates.py``
and ``data/element_properties.py``) and ``metersPerUnit`` is stage metadata,
not a bio: attribute at all. For those four rows the unit string is asserted
by convention/documentation, not read from the stage, and this module cites
the documentation file it came from rather than a USD attribute.

FINDING (see this module's provenance notes and the delivery report): the
task brief for this tile states "No bio: attribute carries a unit string
anywhere in the USD layers." That is false for the fifth row.
``/p53_MDM2_complex/integration/W23A`` also carries a sibling
``bio:ddgUnits`` token attribute set to the literal string ``"kcal/mol"``
(authored in ``converters/ddmut_client.py`` and ``demos/run_end_to_end.py``,
and visible composed into ``demos/p53_mdm2_integrated.usda``). This module
still sources the ddG unit string from ``README.md`` rather than from that
stage token, to keep all five rows' unit provenance uniform ("value from
stage, unit from documentation") and because the brief was explicit that a
figure must not imply the stage stores units -- but the existence of
``bio:ddgUnits`` on the composed stage means that instruction's stated
justification is not accurate for this attribute, and a reviewer should not
take "units are never on this stage" as a verified fact from this file.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
from pxr import Usd, UsdGeom

from make_poster_figures import (
    MONO_FONT,
    Theme,
    figure,
    make_figure,
    prov,
    save_figure,
    type_pt,
    usd_source,
)

# ---------------------------------------------------------------------------
# Stage / prim locations (paths only -- no scientific values live here).
# ---------------------------------------------------------------------------
_FIGURES_DIR = os.path.dirname(os.path.abspath(__file__))
_P53_MDM2_DIR = os.path.dirname(_FIGURES_DIR)  # .../examples/p53_mdm2

# Relative-to-examples/p53_mdm2 form, matching the usd_source() examples in
# make_poster_figures.py's own docstring (e.g. "output/p53_mdm2_topology.usda").
STAGE_REL_PATH = "demos/p53_mdm2_integrated.usda"
STAGE_ABS_PATH = os.path.join(_P53_MDM2_DIR, "demos", "p53_mdm2_integrated.usda")

CARBON_CLASS_PATH = "/_class_/C"
# The ddG readout has two homes in the composed stage (see module docstring
# in the brief): authored inside the Genotype VariantSet's W23A variant, and
# flattened onto this concrete Scope. This module reads the flattened Scope
# because it is reachable on the stage exactly as delivered -- the demo's
# own "over" block only ever selects Genotype="WildType" (see the root
# layer's variants block), so reading the W23A number without first calling
# SetVariantSelection("W23A") means reading a path that does not depend on
# this script mutating variant state to get there.
DDG_SCOPE_PATH = "/p53_MDM2_complex/integration/W23A"

# Where the unit STRINGS come from -- documentation/convention, not bio:
# attributes (see FINDING in the module docstring for the one exception).
_ELEMENT_PROPS_DOC = "data/element_properties.py"
_CLAUDE_MD_DOC = "../../CLAUDE.md"
_EXAMPLE_README_DOC = "README.md"


# ---------------------------------------------------------------------------
# Value formatting -- turns a stage-read float into the display string.
# None of these format specs are the expected-value literals; they are
# rounding/notation rules applied to whatever the stage actually returned.
# ---------------------------------------------------------------------------
def _fmt_fixed(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}"


def _fmt_sci_int_exponent(value: float) -> str:
    """Format e.g. 1e-10 as '1e-10' (no leading zero / plus sign on exponent)."""
    text = f"{value:.0e}"  # "1e-10"
    mantissa, exponent = text.split("e")
    exponent = exponent.replace("+", "")
    exponent = exponent[0] + exponent[1:].lstrip("0").rjust(1, "0")
    return f"{mantissa}e{exponent}"


def _fmt_signed(value: float, decimals: int) -> str:
    """Fixed-point, using a true Unicode minus sign instead of a hyphen."""
    text = f"{value:.{decimals}f}"
    return text.replace("-", "−")


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
@figure("mod-units", ext="svg")
def build_mod_units(theme: Theme, out_dir: str) -> str:
    stage = Usd.Stage.Open(STAGE_ABS_PATH)
    if stage is None:
        raise RuntimeError(f"could not open stage: {STAGE_ABS_PATH!r}")

    carbon = stage.GetPrimAtPath(CARBON_CLASS_PATH)
    if not carbon.IsValid():
        raise RuntimeError(f"{CARBON_CLASS_PATH!r} not found on composed stage")

    atomic_mass = prov(
        carbon.GetAttribute("bio:atomicMass").Get(),
        usd_source(STAGE_REL_PATH, CARBON_CLASS_PATH, "bio:atomicMass"),
        note="carbon element class prim, reached through the sublayer chain",
    )
    vdw_radius = prov(
        carbon.GetAttribute("bio:vdwRadius").Get(),
        usd_source(STAGE_REL_PATH, CARBON_CLASS_PATH, "bio:vdwRadius"),
        note="carbon element class prim, reached through the sublayer chain",
    )
    covalent_radius = prov(
        carbon.GetAttribute("bio:covalentRadius").Get(),
        usd_source(STAGE_REL_PATH, CARBON_CLASS_PATH, "bio:covalentRadius"),
        note="carbon element class prim, reached through the sublayer chain",
    )
    meters_per_unit = prov(
        UsdGeom.GetStageMetersPerUnit(stage),
        f"{STAGE_REL_PATH} (root layer stage metadata: metersPerUnit)",
        note="UsdGeom.GetStageMetersPerUnit(); metersPerUnit is not inherited "
        "from sublayers, so this must be read off the root layer",
    )

    ddg_scope = stage.GetPrimAtPath(DDG_SCOPE_PATH)
    if not ddg_scope.IsValid():
        raise RuntimeError(f"{DDG_SCOPE_PATH!r} not found on composed stage")
    ddg = prov(
        ddg_scope.GetAttribute("bio:ddgKcalPerMol").Get(),
        usd_source(STAGE_REL_PATH, DDG_SCOPE_PATH, "bio:ddgKcalPerMol"),
        note="flattened Scope readout, not the Genotype VariantSet's W23A "
        "variant opinion -- reachable without switching the stage's "
        "variant selection away from the demo's own WildType default",
    )

    # ---- unit strings: convention/documentation, never a stage read ----
    unit_amu = prov(
        "amu",
        _ELEMENT_PROPS_DOC,
        note="IUPAC Standard Atomic Weights convention cited in this file's "
        "module docstring; the string 'amu' is not itself stored as a "
        "bio: attribute anywhere on the stage",
    )
    unit_ang_vdw = prov(
        "Å",
        _ELEMENT_PROPS_DOC,
        note="Bondi (1964) van der Waals radii convention cited in this "
        "file's module docstring; not a stage attribute",
    )
    unit_ang_cov = prov(
        "Å",
        _ELEMENT_PROPS_DOC,
        note="Cordero et al. (2008) covalent radii convention cited in "
        "this file's module docstring; not a stage attribute",
    )
    unit_mpu = prov(
        "(Å as metres)",
        _CLAUDE_MD_DOC,
        note="project convention 'Angstrom as the length unit -- stage "
        "metersPerUnit = 1e-10'; metersPerUnit itself is a dimensionless "
        "ratio with no unit string attached on the stage",
    )
    unit_ddg = prov(
        "kcal/mol",
        _EXAMPLE_README_DOC,
        note="'DeltaDeltaG in kcal/mol' convention documented in the "
        "example README; see this module's docstring FINDING -- a "
        "bio:ddgUnits token with this same string also exists on the "
        "composed stage at this Scope, which this figure deliberately "
        "does not cite so all five rows read units the same way",
    )

    # ---- gate: the stage must agree with the poster's claimed numbers ----
    _assert_matches_expected(
        atomic_mass=atomic_mass,
        vdw_radius=vdw_radius,
        covalent_radius=covalent_radius,
        meters_per_unit=meters_per_unit,
        ddg=ddg,
    )

    rows = [
        ("bio:atomicMass", _fmt_fixed(atomic_mass, 3), unit_amu),
        ("bio:vdwRadius", _fmt_fixed(vdw_radius, 1), unit_ang_vdw),
        ("bio:covalentRadius", _fmt_fixed(covalent_radius, 2), unit_ang_cov),
        ("metersPerUnit", _fmt_sci_int_exponent(meters_per_unit), unit_mpu),
        ("bio:ddgKcalPerMol", _fmt_signed(ddg, 3), unit_ddg),
    ]

    fig, ax = make_figure()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    name_w, val_w, gap_w = 20, 8, 2
    left_margin = 0.02
    top_margin, bottom_margin = 0.07, 0.07
    band_h = (1.0 - top_margin - bottom_margin) / len(rows)
    size = type_pt(22)

    for i, (name, value_str, unit_str) in enumerate(rows):
        line = f"{name:<{name_w}}{value_str:>{val_w}}{'':<{gap_w}}{unit_str}"
        y = 1.0 - top_margin - band_h * (i + 0.5)
        ax.text(
            left_margin,
            y,
            line,
            fontsize=size,
            fontfamily=MONO_FONT,
            color=theme.ink,
            ha="left",
            va="center",
        )

    out_path = os.path.join(out_dir, "mod-units.svg")
    save_figure(fig, out_path, ext="svg")
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Gate: stage-vs-expected agreement.
#
# These five literals are the ONLY place the poster's claimed numbers exist
# as literals in this file. Drawing code above formats whatever the stage
# actually returned; it never touches these constants. If the stage
# disagrees, this raises instead of letting the figure silently draw a
# number the brief did not sign off on.
# ---------------------------------------------------------------------------
_EXPECTED_ATOMIC_MASS_C = 12.011
_EXPECTED_VDW_RADIUS_C = 1.7
_EXPECTED_COVALENT_RADIUS_C = 0.76
_EXPECTED_METERS_PER_UNIT = 1e-10
_EXPECTED_DDG_W23A = -6.192
_TOL = 1e-4


def _assert_matches_expected(
    *, atomic_mass, vdw_radius, covalent_radius, meters_per_unit, ddg
):
    checks = [
        ("bio:atomicMass (carbon)", atomic_mass, _EXPECTED_ATOMIC_MASS_C),
        ("bio:vdwRadius (carbon)", vdw_radius, _EXPECTED_VDW_RADIUS_C),
        ("bio:covalentRadius (carbon)", covalent_radius, _EXPECTED_COVALENT_RADIUS_C),
        ("metersPerUnit", meters_per_unit, _EXPECTED_METERS_PER_UNIT),
        ("bio:ddgKcalPerMol (W23A)", ddg, _EXPECTED_DDG_W23A),
    ]
    disagreements = [
        f"  {label}: stage={value!r} expected={expected!r} "
        f"diff={abs(value - expected):.3g}"
        for label, value, expected in checks
        if abs(value - expected) > _TOL
    ]
    if disagreements:
        raise AssertionError(
            "fig_mod_units: stage disagrees with the poster's claimed "
            "numbers -- halting rather than drawing a figure that "
            "contradicts the stage:\n" + "\n".join(disagreements)
        )
