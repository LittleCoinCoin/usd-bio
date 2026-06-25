"""
Layer 3 — programmatic USD read-back tests.

Opens each committed artifact FRESH with Usd.Stage.Open and asserts that
USD's composition engine has resolved values correctly from SOURCE data, not
from the generator's in-memory state.

Three assertion families:
  1. assert_atom_composition  — bio:element resolves via inherit chain;
                                inherit chain reaches /_class_/<symbol>.
  2. assert_variant_cascade   — switching representation variant on assembly_demo
                                produces measurably different Sphere radii across
                                all 4 selections, and the cascade spans ≥4
                                hierarchy levels.
  3. assert_clip_positions_vary — sampling xformOp:translate at two timecodes in
                                trajectory_demo.usda yields non-zero displacement,
                                confirming clip data is live.

DESIGN: every assertion derives from SOURCE data (data/element_properties.py
ELEMENTS dict and known USD timeSamples) — never from generator in-memory state.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# USD import guard
# ---------------------------------------------------------------------------
try:
    from pxr import Usd, Sdf
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

# ---------------------------------------------------------------------------
# Import ELEMENTS from the authoritative source data module — not from any
# generator script. This is the anti-tautology guard: assertions compare
# against the source-of-truth dict, not the generator's local variables.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _DEMO_ROOT)
from data.element_properties import ELEMENTS  # type: ignore[import]

# Known element symbols from source data
_KNOWN_SYMBOLS: frozenset[str] = frozenset(ELEMENTS.keys())

# The four canonical representation variants per CLAUDE.md conventions
_EXPECTED_VARIANTS: tuple[str, ...] = ("points", "balls", "vdw", "ballstick")

# Expected Sphere radius for Hydrogen under each representation variant.
# Values derived from element_templates.usda (committed asset, not generator).
# H vdwRadius = 1.2 Å; ball = 0.3 * vdwRadius scaling used in templates.
# Observed from the committed .usda: balls=0.36, ballstick=0.3, points=0.18, vdw=1.2
_H_EXPECTED_RADII: dict[str, float] = {
    "balls": 0.36,
    "ballstick": 0.30,
    "points": 0.18,
    "vdw": 1.20,
}


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

@dataclass
class ReadbackResult:
    """Result of one read-back assertion function on a single stage."""
    stage_path: str
    check_name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Assertion 1 — atom composition
# ---------------------------------------------------------------------------

def assert_atom_composition(assembly_path: str) -> ReadbackResult:
    """
    Open assembly_demo.usda fresh. Find the first carbon atom prim. Assert:

    1. bio:element resolves to a known element symbol (from ELEMENTS source dict).
    2. The inherit chain contains /_class_/<symbol> (proves composition resolved).
    3. displayColor is accessible via the variant Sphere child (proves inherit
       cascade delivers visual properties).

    [source: examples/foundation_demo_v8/output/assembly_demo.usda]
    [source: examples/foundation_demo_v8/data/element_properties.py ELEMENTS dict]
    """
    errors: list[str] = []
    detail: dict = {}

    stage = Usd.Stage.Open(assembly_path)

    # Find a carbon atom — carbon is the first non-hydrogen atom in ACE residue.
    # /ABLComplex/Chain_A/ACE_1/CH3 is the canonical first carbon.
    carbon_atom = None
    for prim in stage.Traverse():
        elem_attr = prim.GetAttribute("bio:element")
        if not (elem_attr.IsValid() and elem_attr.Get()):
            continue
        if str(elem_attr.Get()) == "C":
            carbon_atom = prim
            break

    if carbon_atom is None:
        errors.append("No carbon atom prim found in stage")
        return ReadbackResult(
            stage_path=assembly_path,
            check_name="assert_atom_composition",
            passed=False,
            errors=errors,
            detail=detail,
        )

    atom_path = str(carbon_atom.GetPath())
    detail["atom_path"] = atom_path

    # 1. bio:element resolves and is a known symbol
    symbol = str(carbon_atom.GetAttribute("bio:element").Get())
    detail["bio:element"] = symbol
    if symbol not in _KNOWN_SYMBOLS:
        errors.append(
            f"{atom_path}: bio:element='{symbol}' not in ELEMENTS source dict "
            f"(anti-tautology: compared against data/element_properties.py)"
        )

    # 2. Inherit chain contains /_class_/<symbol>
    expected_class = f"/_class_/{symbol}"
    direct_inherits = [
        str(p) for p in carbon_atom.GetInherits().GetAllDirectInherits()
    ]
    detail["inherits"] = direct_inherits
    if expected_class not in direct_inherits:
        errors.append(
            f"{atom_path}: inherit chain does not contain {expected_class}; "
            f"actual={direct_inherits}"
        )

    # 3. displayColor accessible via inherit — resolve by getting current Sphere child
    #    The atom inherits a representation VariantSet; the default variant's Sphere
    #    should provide primvars:displayColor.
    sphere_path = atom_path + "/Sphere"
    sphere = stage.GetPrimAtPath(sphere_path)
    detail["sphere_valid"] = sphere.IsValid()
    if not sphere.IsValid():
        errors.append(
            f"{sphere_path}: Sphere child not present under current variant selection "
            "(inherit cascade failed to deliver geometry child)"
        )
    else:
        dc_attr = sphere.GetAttribute("primvars:displayColor")
        dc = dc_attr.Get() if dc_attr.IsValid() else None
        detail["displayColor"] = str(dc) if dc is not None else None
        if dc is None:
            errors.append(
                f"{sphere_path}: primvars:displayColor is None "
                "(inherit did not deliver color from /_class_/C)"
            )
        else:
            # Cross-check against ELEMENTS source: Carbon CPK = (0.2, 0.2, 0.2)
            source_cpk = ELEMENTS["C"]["cpk_color"]  # (0.2, 0.2, 0.2)
            # dc is a VtArray of GfVec3f; compare first element
            actual_color = tuple(dc[0])
            tol = 0.01
            if not all(abs(actual_color[i] - source_cpk[i]) < tol for i in range(3)):
                errors.append(
                    f"{sphere_path}: displayColor={actual_color} does not match "
                    f"ELEMENTS['C']['cpk_color']={source_cpk} "
                    "(anti-tautology: compared against data/element_properties.py)"
                )
            detail["displayColor_match"] = len(errors) == 0

    return ReadbackResult(
        stage_path=assembly_path,
        check_name="assert_atom_composition",
        passed=len(errors) == 0,
        errors=errors,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Assertion 2 — variant cascade
# ---------------------------------------------------------------------------

def assert_variant_cascade(assembly_path: str) -> ReadbackResult:
    """
    Open assembly_demo.usda fresh. Switch 'representation' to each of the
    four canonical variants on the first hydrogen atom prim and assert:

    1. Each variant produces a measurably different Sphere radius.
    2. Expected radii match the committed element_templates.usda values
       (anti-tautology: compared against _H_EXPECTED_RADII, NOT generator state).
    3. The representation VariantSet is present at ≥4 hierarchy levels on the
       path from the root to the atom.

    [source: examples/foundation_demo_v8/assets/level1_elements/element_templates.usda]
    [source: examples/foundation_demo_v8/output/assembly_demo.usda]
    """
    errors: list[str] = []
    findings: list[str] = []
    detail: dict = {}

    stage = Usd.Stage.Open(assembly_path)

    # Find first hydrogen atom (HH31 in ACE_1 — earliest atom in the stage).
    h_atom = None
    for prim in stage.Traverse():
        elem_attr = prim.GetAttribute("bio:element")
        if elem_attr.IsValid() and str(elem_attr.Get()) == "H":
            h_atom = prim
            break

    if h_atom is None:
        errors.append("No hydrogen atom prim found in stage")
        return ReadbackResult(
            stage_path=assembly_path,
            check_name="assert_variant_cascade",
            passed=False,
            errors=errors,
            detail=detail,
        )

    atom_path = str(h_atom.GetPath())
    detail["atom_path"] = atom_path

    # --- Check hierarchy depth of representation VariantSets ---
    path_parts = atom_path.split("/")
    # path_parts = ['', 'ABLComplex', 'Chain_A', 'ACE_1', 'HH31'] => depth 4
    levels_with_vs = 0
    level_paths: list[str] = []
    for depth in range(1, len(path_parts)):
        ancestor = "/" + "/".join(path_parts[1:depth + 1])
        p = stage.GetPrimAtPath(ancestor)
        if p.IsValid() and "representation" in p.GetVariantSets().GetNames():
            levels_with_vs += 1
            level_paths.append(ancestor)

    detail["levels_with_representation_variantset"] = levels_with_vs
    detail["level_paths"] = level_paths

    if levels_with_vs < 4:
        errors.append(
            f"representation VariantSet found at only {levels_with_vs} hierarchy "
            f"levels on path to {atom_path}; expected ≥4. "
            f"Levels found: {level_paths}"
        )

    # --- Switch each variant and measure radius ---
    vs = h_atom.GetVariantSets().GetVariantSet("representation")
    if not vs:
        errors.append(f"{atom_path}: representation VariantSet not found")
        return ReadbackResult(
            stage_path=assembly_path,
            check_name="assert_variant_cascade",
            passed=False,
            errors=errors,
            detail=detail,
        )

    sphere_path = atom_path + "/Sphere"
    observed_radii: dict[str, float] = {}

    for variant in _EXPECTED_VARIANTS:
        vs.SetVariantSelection(variant)
        sphere = stage.GetPrimAtPath(sphere_path)
        if not sphere.IsValid():
            errors.append(
                f"variant='{variant}': Sphere child not present at {sphere_path} "
                "(variant switch failed to deliver Sphere geometry)"
            )
            observed_radii[variant] = float("nan")
            continue
        r_attr = sphere.GetAttribute("radius")
        radius = r_attr.Get() if r_attr.IsValid() else None
        if radius is None:
            errors.append(f"variant='{variant}': radius attribute missing on Sphere")
            observed_radii[variant] = float("nan")
        else:
            observed_radii[variant] = float(radius)

    detail["observed_radii"] = observed_radii

    # Cross-check against _H_EXPECTED_RADII (derived from committed .usda, NOT generator)
    for variant, expected_r in _H_EXPECTED_RADII.items():
        actual_r = observed_radii.get(variant, float("nan"))
        if math.isnan(actual_r):
            continue  # error already recorded above
        if abs(actual_r - expected_r) > 0.001:
            errors.append(
                f"variant='{variant}': radius={actual_r:.4f} does not match "
                f"expected={expected_r:.4f} from element_templates.usda "
                "(anti-tautology: compared against committed asset, not generator)"
            )

    # Assert all four observed radii are distinct (proves cascade actually changes state)
    valid_radii = [r for r in observed_radii.values() if not math.isnan(r)]
    if len(set(valid_radii)) < len(valid_radii):
        errors.append(
            f"Some variant selections produced identical radii: {observed_radii} "
            "(variant cascade is not producing distinct geometry per selection)"
        )

    return ReadbackResult(
        stage_path=assembly_path,
        check_name="assert_variant_cascade",
        passed=len(errors) == 0,
        errors=errors,
        findings=findings,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Assertion 3 — clip positions vary
# ---------------------------------------------------------------------------

def assert_clip_positions_vary(trajectory_path: str) -> ReadbackResult:
    """
    Open trajectory_demo.usda fresh. Sample xformOp:translate at timecodes 0
    and 10. Assert the displacement magnitude is non-zero, proving clip data
    is live and the UsdClipsAPI is wiring the clip file correctly.

    The atom path /ABLComplex/Chain_A/ACE_1/HH31 is the canonical first atom in
    the assembly. Its positions at t=0 and t=10 are known from trajectory_clip.usda:
      t=0:  (53.96, 83.70, 74.53)
      t=10: (39.19, 91.51, 65.30)
    These are SOURCE values from the committed clip file — not generator state.

    [source: examples/foundation_demo_v8/output/clips/trajectory_clip.usda]
    [source: examples/foundation_demo_v8/output/trajectory_demo.usda]
    """
    errors: list[str] = []
    detail: dict = {}

    stage = Usd.Stage.Open(trajectory_path)

    # Canonical first atom path (known from committed asset structure)
    atom_path = "/ABLComplex/Chain_A/ACE_1/HH31"
    atom = stage.GetPrimAtPath(atom_path)
    detail["atom_path"] = atom_path

    if not atom.IsValid():
        errors.append(
            f"Atom prim not found at {atom_path} in {trajectory_path}. "
            "Stage may not have resolved the sublayer correctly."
        )
        return ReadbackResult(
            stage_path=trajectory_path,
            check_name="assert_clip_positions_vary",
            passed=False,
            errors=errors,
            detail=detail,
        )

    translate_attr = atom.GetAttribute("xformOp:translate")
    if not translate_attr.IsValid():
        errors.append(f"{atom_path}: xformOp:translate attribute not found")
        return ReadbackResult(
            stage_path=trajectory_path,
            check_name="assert_clip_positions_vary",
            passed=False,
            errors=errors,
            detail=detail,
        )

    t0_val = translate_attr.Get(Usd.TimeCode(0))
    t10_val = translate_attr.Get(Usd.TimeCode(10))

    detail["t0"] = tuple(t0_val) if t0_val is not None else None
    detail["t10"] = tuple(t10_val) if t10_val is not None else None

    if t0_val is None:
        errors.append(f"{atom_path}: xformOp:translate returned None at timecode 0")
    if t10_val is None:
        errors.append(f"{atom_path}: xformOp:translate returned None at timecode 10")

    if t0_val is None or t10_val is None:
        return ReadbackResult(
            stage_path=trajectory_path,
            check_name="assert_clip_positions_vary",
            passed=False,
            errors=errors,
            detail=detail,
        )

    # Compute displacement
    diff = tuple(float(t10_val[i]) - float(t0_val[i]) for i in range(3))
    displacement = math.sqrt(sum(d * d for d in diff))
    detail["displacement_magnitude"] = displacement
    detail["diff"] = diff

    # Cross-check against SOURCE clip values (from trajectory_clip.usda)
    # t=0:  (53.96, 83.70, 74.53) — known from committed clip file
    # t=10: (39.19, 91.51, 65.30) — known from committed clip file
    _KNOWN_T0 = (53.96, 83.70, 74.53)
    _KNOWN_T10 = (39.19, 91.51, 65.30)
    tol = 0.1  # Å; generous for floating-point round-trips

    for i, (a, e) in enumerate(zip(tuple(t0_val), _KNOWN_T0)):
        if abs(a - e) > tol:
            errors.append(
                f"t=0 position[{i}] = {a:.4f}, expected {e:.4f} "
                f"from trajectory_clip.usda (anti-tautology: SOURCE values)"
            )

    for i, (a, e) in enumerate(zip(tuple(t10_val), _KNOWN_T10)):
        if abs(a - e) > tol:
            errors.append(
                f"t=10 position[{i}] = {a:.4f}, expected {e:.4f} "
                f"from trajectory_clip.usda (anti-tautology: SOURCE values)"
            )

    # Primary assertion: displacement is non-zero (proves clip is live)
    if displacement < 1.0:
        errors.append(
            f"Displacement from t=0 to t=10 is {displacement:.4f} Å — "
            "expected >1.0 Å, indicating clip data is not being read correctly"
        )

    return ReadbackResult(
        stage_path=trajectory_path,
        check_name="assert_clip_positions_vary",
        passed=len(errors) == 0,
        errors=errors,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(output_dir: str) -> list[ReadbackResult]:
    """
    Run all read-back assertions against artifacts in output_dir.

    Parameters
    ----------
    output_dir : str
        Path to the output/ directory containing the committed .usda artifacts.

    Returns
    -------
    list of ReadbackResult
        One result per assertion. Some assertions run against the same artifact.
    """
    assembly_path = os.path.join(output_dir, "assembly_demo.usda")
    trajectory_path = os.path.join(output_dir, "trajectory_demo.usda")

    results: list[ReadbackResult] = []

    # --- Assertion 1: atom composition ---
    if not os.path.isfile(assembly_path):
        results.append(ReadbackResult(
            stage_path=assembly_path,
            check_name="assert_atom_composition",
            passed=False,
            errors=[f"File not found: {assembly_path}"],
        ))
    else:
        results.append(assert_atom_composition(assembly_path))

    # --- Assertion 2: variant cascade ---
    if not os.path.isfile(assembly_path):
        results.append(ReadbackResult(
            stage_path=assembly_path,
            check_name="assert_variant_cascade",
            passed=False,
            errors=[f"File not found: {assembly_path}"],
        ))
    else:
        results.append(assert_variant_cascade(assembly_path))

    # --- Assertion 3: clip positions vary ---
    if not os.path.isfile(trajectory_path):
        results.append(ReadbackResult(
            stage_path=trajectory_path,
            check_name="assert_clip_positions_vary",
            passed=False,
            errors=[f"File not found: {trajectory_path}"],
        ))
    else:
        results.append(assert_clip_positions_vary(trajectory_path))

    return results
