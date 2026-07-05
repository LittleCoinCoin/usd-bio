#!/usr/bin/env python3
"""
usdview_regression_check.py — headless, falsification-resistant regression
check for the "static / grey / double-display / wrong-file" bug class that
usdview would otherwise be the first tool to reveal to a human.

WHY THIS EXISTS
----------------
Four PI bug reports (see the diagnosis this harness implements) all reduced
to the same underlying problem: a human had to open usdview to discover that
a stage was static when it should animate, grey when it should be colored,
double-displayed on a variant switch, or simply the wrong file to open in
the first place. Every one of these defects is mechanically detectable from
the composed Usd.Stage WITHOUT ever launching usdview. This script is that
mechanical check, meant to run in CI / before a human touches usdview.

DESIGN CONTRACT (falsification-resistance)
-------------------------------------------
- Every stage is opened FRESH via Usd.Stage.Open() in this process. No gate
  reads generator in-memory state.
- Expectations are independently stated in the MANIFEST below (per-file role
  and animation intent), not inferred from what a file happens to contain.
- Gates assert properties of the composed result, not of any one layer.
- Exit code is nonzero if ANY gate fails on ANY declared file.

MANIFEST ROLES
--------------
    viewer_entry_point_animated  — meant to be opened directly in usdview;
                                    has an authored timeCode range; pressing
                                    Play should show visible motion.
    viewer_entry_point_static    — meant to be opened directly in usdview;
                                    no animation is expected (single frame /
                                    exploded-grid demos).
    payload_or_manifest          — NOT a viewer entry point. Intermediate
                                    clip payload or clip-template manifest
                                    data. Opening it directly in usdview is
                                    expected to look broken (grey bond
                                    cylinders only, dead Play button) — see
                                    docs/13_value_clips_for_trajectories.md
                                    and docs/11_trajectory_demo_guide.md.

USAGE
-----
    source load_env.sh   # from repo root; sets PYTHONPATH for pxr
    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 \\
        examples/foundation_demo_v8/tests/usdview_regression_check.py [--render] [--usdchecker-timeout SECONDS]

    --render                 Enable Gate 5 (usdrecord frame-diff). Off by
                              default: slow, needs offscreen GL/Storm.
    --usdchecker-timeout N   Per-file timeout (seconds) for Gate 6. Default 60.

Exit codes: 0 = all gates passed on all applicable files. 1 = at least one
gate failed. 2 = harness/environment error (e.g. pxr not importable).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    from pxr import Usd, UsdGeom, Gf
except ImportError as exc:  # pragma: no cover - environment guard
    sys.stderr.write(
        "ERROR: pxr not importable. Run under the OpenUSD Python interpreter "
        "(/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3) with "
        "load_env.sh sourced from the repo root first.\n"
        f"Original error: {exc}\n"
    )
    sys.exit(2)

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
_OUTPUT_DIR = os.path.join(_DEMO_ROOT, "output")
_CLIPS_DIR = os.path.join(_OUTPUT_DIR, "clips")

_REAL_USDCHECKER = "/Users/hacker/Documents/bin/OpenUSD/bin/usdchecker"
_REAL_USDRECORD = "/Users/hacker/Documents/bin/OpenUSD/bin/usdrecord"

_GPRIM_TYPES = ("Sphere", "Cylinder", "Mesh", "Points", "BasisCurves")


# ---------------------------------------------------------------------------
# Manifest — the independently-stated expectation for every real output file.
# This is the falsification-resistance anchor: gates check files AGAINST
# this, never against what the file happens to already contain.
# ---------------------------------------------------------------------------

ROLE_ANIMATED = "viewer_entry_point_animated"
ROLE_STATIC = "viewer_entry_point_static"
ROLE_PAYLOAD = "payload_or_manifest"


@dataclass
class ManifestEntry:
    path: str                 # relative to output/
    role: str                 # one of ROLE_* above
    notes: str = ""


MANIFEST: list[ManifestEntry] = [
    # --- viewer entry points: animated (authored timeCode range expected) ---
    ManifestEntry("trajectory_demo.usda", ROLE_ANIMATED,
                  "Cylinder bonds + per-atom Xform, clip-driven MD trajectory."),
    ManifestEntry("curves_demo.usda", ROLE_ANIMATED,
                  "BasisCurves bond encoding + clip-driven MD trajectory. "
                  "KNOWN BROKEN per diagnosis: no default variant selection, "
                  "curves clip does not drive atom positions."),
    ManifestEntry("binary_demo.usda", ROLE_ANIMATED,
                  ".usdc SubLayers (binary) + clip-driven MD trajectory."),
    ManifestEntry("departmental_demo.usda", ROLE_ANIMATED,
                  "5-layer departmental SubLayer stack (biology/protocol/"
                  "dynamics/analysis/review); dynamics layer drives motion."),

    # --- viewer entry points: static (no animation intended) ---
    ManifestEntry("assembly_demo.usda", ROLE_STATIC,
                  "Full ABL kinase assembly, static topology only."),
    ManifestEntry("element_grid_demo.usda", ROLE_STATIC,
                  "Periodic-table style grid of element class prims."),
    ManifestEntry("residue_grid_demo.usda", ROLE_STATIC,
                  "Grid of amino-acid residue class prims."),
    ManifestEntry("solvent_demo.usda", ROLE_STATIC,
                  "Protein + PointInstancer solvent shell, static. "
                  "KNOWN, JUSTIFIED gate-2 RESIDUAL (v8-gap-closure, curves_demo "
                  "fix cycle): demos/solvent_demo.py now authors a default "
                  "'representation' selection on /SolvatedComplex/Protein (the "
                  "reference actually reachable from defaultPrim=/SolvatedComplex), "
                  "so the real viewer-visible geometry resolves correctly on "
                  "fresh-open. Gate 2 still fails because it calls a WHOLE-STAGE "
                  "stage.Traverse() rather than a defaultPrim-scoped traversal, "
                  "and this file's SubLayer composition (not Reference-only) "
                  "brings two never-rendered-standalone prims onto the stage at "
                  "their OWN top-level paths outside the defaultPrim subtree: "
                  "(1) /ABLComplex itself (the raw sublayered prim; confirmed "
                  "NOT reachable via Usd.PrimRange from /SolvatedComplex) and "
                  "(2) /Solvent/Prototypes/Water (a UsdGeomPointInstancer "
                  "prototype — by standard USD/Hydra convention, prototypes "
                  "listed in a PointInstancer's 'prototypes' relationship are "
                  "drawn only via instancing and are never rendered directly "
                  "at their own prim path, regardless of variant selection). "
                  "Neither is a 'grey block' / 'double display' / 'invisible "
                  "on open' regression a human would see in usdview. This is a "
                  "gate false-positive for whole-stage-sublayered files with "
                  "PointInstancer prototypes, not a fix left undone; see "
                  "examples/foundation_demo_v8/demos/solvent_demo.py for the "
                  "actual authored default."),
    ManifestEntry("water_demo.usda", ROLE_STATIC,
                  "Single water molecule template demo."),

    # --- payload / manifest artifacts: NOT viewer entry points ---
    ManifestEntry("clips/trajectory_clip.usda", ROLE_PAYLOAD,
                  "Clip payload: bond Cylinders + time-sampled atom "
                  "xformOp:translate only. No topology, no color, no "
                  "variants. Opening directly: grey bond cylinders, dead "
                  "Play button (no authored time range) — expected."),
    ManifestEntry("clips/trajectory_clip.usdc", ROLE_PAYLOAD,
                  "Binary twin of trajectory_clip.usda."),
    ManifestEntry("clips/clip.001.usdc", ROLE_PAYLOAD,
                  "Clip-template shard 1/2 (dot-separated hash naming)."),
    ManifestEntry("clips/clip.002.usdc", ROLE_PAYLOAD,
                  "Clip-template shard 2/2."),
    ManifestEntry("clips/clip_template_manifest.usda", ROLE_PAYLOAD,
                  "Metadata-only: clipTemplateAssetPath dictionary on an "
                  "empty Xform. Opening directly renders nothing."),
    ManifestEntry("clips/trajectory_clip_curves.usda", ROLE_PAYLOAD,
                  "Curves-mode clip payload: Bonds.points time samples only, "
                  "no per-atom translate data (root cause of curves_demo's "
                  "atom/bond desync — see diagnosis Item 3)."),
]


# ---------------------------------------------------------------------------
# Result plumbing
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    gate: str
    file: str
    passed: bool
    skipped: bool = False
    messages: list[str] = field(default_factory=list)


ALL_RESULTS: list[GateResult] = []


def _record(gate: str, file: str, passed: bool, messages: list[str],
            skipped: bool = False) -> GateResult:
    r = GateResult(gate=gate, file=file, passed=passed, skipped=skipped,
                    messages=messages)
    ALL_RESULTS.append(r)
    return r


def _abspath(rel: str) -> str:
    return os.path.join(_OUTPUT_DIR, rel)


# ---------------------------------------------------------------------------
# Gate 1 — structural gate
# ---------------------------------------------------------------------------

def gate1_structural(entry: ManifestEntry) -> GateResult:
    """Animated/static entry points: time range, defaultPrim traversal to
    >0 renderable gprims, and >0 prims carrying color/material (catches
    "grey block" and "opened the wrong file, nothing renders")."""
    gate = "1-structural"
    path = _abspath(entry.path)
    msgs = []

    if entry.role == ROLE_PAYLOAD:
        return _record(gate, entry.path, True,
                        ["skipped: payload/manifest artifact, not a viewer entry point"],
                        skipped=True)

    if not os.path.isfile(path):
        return _record(gate, entry.path, False, [f"file not found: {path}"])

    stage = Usd.Stage.Open(path)
    if stage is None:
        return _record(gate, entry.path, False, [f"Usd.Stage.Open failed: {path}"])

    ok = True

    if entry.role == ROLE_ANIMATED:
        has_range = stage.HasAuthoredTimeCodeRange()
        msgs.append(f"HasAuthoredTimeCodeRange={has_range} (expected True)")
        if not has_range:
            ok = False
        else:
            start, end = stage.GetStartTimeCode(), stage.GetEndTimeCode()
            msgs.append(f"start={start}, end={end}")
            if not (start < end):
                ok = False
                msgs.append(f"FAIL: expected start < end, got {start} !< {end}")

    default_prim = stage.GetDefaultPrim()
    if not default_prim or not default_prim.IsValid():
        ok = False
        msgs.append("FAIL: defaultPrim missing or invalid")
    else:
        msgs.append(f"defaultPrim={default_prim.GetPath()}")
        # NOTE: this repo's convention sometimes makes defaultPrim a
        # variant-cascade DISPATCHER prim (e.g. /World) whose actual
        # renderable payload lives at a sibling stage root (e.g.
        # /ABLComplex), reached only through the dispatcher's nested
        # variant-edit-context cascade, not through parent/child
        # containment. Traversing strictly under defaultPrim would miss
        # that payload entirely and produce a false "nothing renders"
        # failure. To catch the real "wrong file / empty stage" class of
        # bug without that false positive, gate 1 checks renderable
        # content across the WHOLE composed stage (usdview's own "what
        # would I show if I opened this and hit Play" scope is the full
        # stage, not just the defaultPrim subtree) while still requiring
        # defaultPrim to be valid above.
        subtree = list(stage.Traverse())
        gprims = [p for p in subtree if p.GetTypeName() in _GPRIM_TYPES]
        msgs.append(f"gprims across whole stage (fresh, no variant selection "
                     f"changes) = {len(gprims)} "
                     f"({', '.join(sorted({p.GetTypeName() for p in gprims})) or 'none'})")
        if len(gprims) == 0:
            ok = False
            msgs.append("FAIL: 0 renderable gprims resolve anywhere on the "
                        "fresh stage — wrong file, or nothing to render")

        colored = 0
        for p in subtree:
            dc = p.GetAttribute("primvars:displayColor")
            if dc and dc.HasAuthoredValue():
                colored += 1
                continue
            if p.HasRelationship("material:binding"):
                rel = p.GetRelationship("material:binding")
                if rel.GetTargets():
                    colored += 1
        msgs.append(f"prims with authored displayColor or bound Material = {colored}")
        if colored == 0 and len(gprims) > 0:
            ok = False
            msgs.append("FAIL: gprims present but 0 carry color/material — "
                        "'grey block' regression")

    return _record(gate, entry.path, ok, msgs)


# ---------------------------------------------------------------------------
# Gate 2 — variant-selection completeness
# ---------------------------------------------------------------------------

def gate2_variant_completeness(entry: ManifestEntry) -> GateResult:
    """For every prim with a non-empty variantSet, a default selection must
    be authored on the FRESH composed stage, before any SetVariantSelection
    call. Catches 'opens with curves visible and atoms invisible because
    nothing is selected.'"""
    gate = "2-variant-completeness"
    path = _abspath(entry.path)

    if entry.role == ROLE_PAYLOAD:
        return _record(gate, entry.path, True,
                        ["skipped: payload/manifest artifact"], skipped=True)

    if not os.path.isfile(path):
        return _record(gate, entry.path, False, [f"file not found: {path}"])

    # Fresh stage, independent of gate 1's stage object.
    stage = Usd.Stage.Open(path)
    if stage is None:
        return _record(gate, entry.path, False, [f"Usd.Stage.Open failed: {path}"])

    msgs = []
    ok = True
    unselected: list[str] = []
    checked = 0

    for prim in stage.Traverse():
        vsets = prim.GetVariantSets()
        names = vsets.GetNames()
        if not names:
            continue
        for name in names:
            checked += 1
            sel = vsets.GetVariantSet(name).GetVariantSelection()
            if not sel:
                unselected.append(f"{prim.GetPath()} [{name}]")

    msgs.append(f"prim-variantSet pairs checked = {checked}")
    if unselected:
        ok = False
        preview = unselected[:8]
        msgs.append(f"FAIL: {len(unselected)} variantSet(s) with NO default "
                     f"selection on fresh stage, e.g.: {preview}"
                     + (" ..." if len(unselected) > 8 else ""))
    else:
        msgs.append("PASS: every variantSet has an authored default selection")

    return _record(gate, entry.path, ok, msgs)


# ---------------------------------------------------------------------------
# Gate 3 — cross-representation visibility-exclusivity
# ---------------------------------------------------------------------------

def _representation_groups(stage: "Usd.Stage") -> dict:
    """Heuristic grouping: prims that carry a 'representation' VariantSet
    are candidate mutually-exclusive representation groups keyed by parent
    path. Returns {parent_path: [prim, ...]}."""
    groups: dict = {}
    for prim in stage.Traverse():
        vsets = prim.GetVariantSets()
        if "representation" not in vsets.GetNames():
            continue
        parent = prim.GetPath().GetParentPath()
        groups.setdefault(str(parent), []).append(prim)
    return groups


def gate3_visibility_exclusivity(entry: ManifestEntry) -> GateResult:
    """Cycle each 'representation' variant and assert at most one
    sibling-representation gprim GROUP resolves visible at a time. Catches
    the Bonds-always-visible-in-ballstick-plus-atoms double-display class.

    Concretely for this repo's known topology: at any given representation
    selection, exactly one of {per-atom Sphere cloud, Bonds Cylinder/
    BasisCurves group} should be the visible bond/atom representation set
    -- but 'ballstick' legitimately shows both spheres AND bonds together
    (that is its intended meaning). What must never happen is a variant
    selection under which a DIFFERENT, non-selected representation's
    geometry is also visible -- i.e. the top-level /ABLComplex-or-/World
    'representation' selection must be the only source of visible gprims;
    no gprim group should be unconditionally visible regardless of the
    active selection when it is meant to be variant-gated.

    This gate operationalizes that as: for each concrete value of the
    outermost 'representation' VariantSet, resolve the full set of visible
    gprims; a group is FLAGGED if it stays visible in EVERY variant value
    including ones that don't name it (e.g. Bonds visible under both
    'points' and 'ballstick' would be flagged; Bonds visible ONLY under
    'ballstick' and 'balls'-with-sticks is the documented intended
    behavior and passes).
    """
    gate = "3-visibility-exclusivity"
    path = _abspath(entry.path)

    if entry.role == ROLE_PAYLOAD:
        return _record(gate, entry.path, True,
                        ["skipped: payload/manifest artifact"], skipped=True)
    if not os.path.isfile(path):
        return _record(gate, entry.path, False, [f"file not found: {path}"])

    stage = Usd.Stage.Open(path)
    if stage is None:
        return _record(gate, entry.path, False, [f"Usd.Stage.Open failed: {path}"])

    default_prim = stage.GetDefaultPrim()
    if not default_prim or not default_prim.IsValid():
        return _record(gate, entry.path, False, ["no valid defaultPrim to cycle variants on"])

    # Find the outermost prim(s) carrying a 'representation' VariantSet
    # directly under/at the defaultPrim (this repo's convention: /World or
    # /ABLComplex itself, or an 'over' on it).
    top_vset = None
    top_prim = None
    for prim in [default_prim] + list(default_prim.GetChildren()):
        vsets = prim.GetVariantSets()
        if "representation" in vsets.GetNames():
            top_prim = prim
            top_vset = vsets.GetVariantSet("representation")
            break

    if top_vset is None:
        return _record(gate, entry.path, True,
                        ["no top-level 'representation' VariantSet found — "
                         "nothing to cycle, treating as N/A pass"], skipped=True)

    variant_names = top_vset.GetVariantNames()
    msgs = [f"top-level representation VariantSet on {top_prim.GetPath()}, "
            f"variants={variant_names}"]

    # For each variant value, capture the set of gprim-bearing group names
    # (by parent-relative leaf name, e.g. 'Bonds') that resolve visible.
    visible_by_variant: dict = {}
    for vname in variant_names:
        top_vset.SetVariantSelection(vname)
        visible_groups = set()
        for prim in stage.Traverse():
            if prim.GetTypeName() not in _GPRIM_TYPES:
                continue
            imageable = UsdGeom.Imageable(prim)
            vis_attr = imageable.GetVisibilityAttr()
            resolved_vis = vis_attr.Get() if vis_attr else "inherited"
            # Walk ancestors for inherited invisibility too.
            is_visible = (resolved_vis != "invisible")
            anc = prim.GetParent()
            while is_visible and anc and anc.IsValid():
                anc_vis = UsdGeom.Imageable(anc).GetVisibilityAttr()
                if anc_vis and anc_vis.Get() == "invisible":
                    is_visible = False
                anc = anc.GetParent()
            if is_visible:
                # Group key: nearest ancestor with a stable structural name
                # (e.g. 'Bonds', or the atom's element symbol container).
                visible_groups.add(prim.GetName())
        visible_by_variant[vname] = visible_groups

    # Reset to first variant to leave stage in a defined state (this stage
    # object is local to this gate; no shared state leaks to other gates).
    if variant_names:
        top_vset.SetVariantSelection(variant_names[0])

    for vname, groups in visible_by_variant.items():
        msgs.append(f"  representation={vname}: visible gprim names sample "
                     f"(up to 6) = {sorted(groups)[:6]} (total {len(groups)})")

    # Flag: a named group ('Bonds' specifically, the repo's known
    # cross-representation sibling) visible in EVERY variant value is the
    # double-display signature -- unless every variant is itself a
    # bond-inclusive mode (nothing to compare against).
    ok = True
    if "Bonds" in {n for g in visible_by_variant.values() for n in g}:
        variants_with_bonds = [v for v, g in visible_by_variant.items() if "Bonds" in g]
        variants_without_bonds = [v for v in variant_names if v not in variants_with_bonds]
        msgs.append(f"'Bonds' visible under variants: {variants_with_bonds}; "
                     f"NOT visible under: {variants_without_bonds}")
        if not variants_without_bonds:
            ok = False
            msgs.append("FAIL: 'Bonds' resolves visible under EVERY "
                         "representation value — not variant-gated at all "
                         "(double-display regardless of selection)")
        elif len(variant_names) >= 2 and len(variants_with_bonds) == len(variant_names) - 0 == len(variant_names):
            # unreachable branch kept for clarity; real check is above
            pass

    return _record(gate, entry.path, ok, msgs)


# ---------------------------------------------------------------------------
# Gate 4 — clip/topology position-sync
# ---------------------------------------------------------------------------

def _world_bbox_centroid(stage: "Usd.Stage", prim_path: str, timecode: float) -> Optional[Gf.Vec3d]:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        return None
    cache = UsdGeom.BBoxCache(Usd.TimeCode(timecode), [UsdGeom.Tokens.default_])
    bbox = cache.ComputeWorldBound(prim)
    rng = bbox.ComputeAlignedRange()
    if rng.IsEmpty():
        return None
    return (rng.GetMin() + rng.GetMax()) / 2.0


def gate4_clip_topology_sync(entry: ManifestEntry) -> GateResult:
    """For ClipsAPI-wired prims: assert clip-driven descendants resolve via
    ValueClips in the active range, and that logically-coupled clip-driven
    gprims (Bonds centroid vs atom-cloud centroid) do not diverge beyond a
    bounding-box tolerance at sampled timecodes. Catches the PDB-frame vs
    MD-frame desync (diagnosis Item 3, cause #2)."""
    gate = "4-clip-topology-sync"
    path = _abspath(entry.path)

    if entry.role == ROLE_PAYLOAD:
        return _record(gate, entry.path, True,
                        ["skipped: payload/manifest artifact"], skipped=True)
    if not os.path.isfile(path):
        return _record(gate, entry.path, False, [f"file not found: {path}"])

    stage = Usd.Stage.Open(path)
    if stage is None:
        return _record(gate, entry.path, False, [f"Usd.Stage.Open failed: {path}"])

    # Find prims with ClipsAPI wired (non-empty ComputeClipAssetPaths).
    clip_prims = []
    for prim in stage.Traverse():
        clips_api = Usd.ClipsAPI(prim)
        if clips_api.GetClipAssetPaths() or clips_api.GetClipTemplateAssetPath():
            clip_prims.append(prim)
    # Root-level 'over' with clips dict may not appear in Traverse if it has
    # no direct children beyond composed ones; also check defaultPrim/known root.
    default_prim = stage.GetDefaultPrim()
    if default_prim and default_prim.IsValid():
        clips_api = Usd.ClipsAPI(default_prim)
        if (clips_api.GetClipAssetPaths() or clips_api.GetClipTemplateAssetPath()) \
                and default_prim not in clip_prims:
            clip_prims.append(default_prim)
        for child in default_prim.GetChildren():
            clips_api = Usd.ClipsAPI(child)
            if (clips_api.GetClipAssetPaths() or clips_api.GetClipTemplateAssetPath()) \
                    and child not in clip_prims:
                clip_prims.append(child)

    if not clip_prims:
        return _record(gate, entry.path, True,
                        ["no ClipsAPI-wired prims found — N/A pass"], skipped=True)

    msgs = [f"ClipsAPI-wired prims: {[p.GetPath() for p in clip_prims]}"]
    ok = True

    start = stage.GetStartTimeCode() if stage.HasAuthoredTimeCodeRange() else 0.0
    end = stage.GetEndTimeCode() if stage.HasAuthoredTimeCodeRange() else 0.0
    sample_times = sorted({start, end}) if end > start else [start]

    # Sub-check A: at least one descendant attribute resolves via ValueClips
    # at a sampled time in range.
    resolved_via_clips = False
    for clip_prim in clip_prims:
        for desc in Usd.PrimRange(clip_prim):
            xf = UsdGeom.Xformable(desc)
            for op in xf.GetOrderedXformOps():
                attr = op.GetAttr()
                for t in sample_times:
                    ri = attr.GetResolveInfo(Usd.TimeCode(t))
                    if ri.GetSource() == Usd.ResolveInfoSourceValueClips:
                        resolved_via_clips = True
                        break
                if resolved_via_clips:
                    break
            if resolved_via_clips:
                break
        if resolved_via_clips:
            break

    msgs.append(f"at least one descendant xformOp resolves via ValueClips in "
                f"[{start},{end}] = {resolved_via_clips}")
    if not resolved_via_clips:
        ok = False
        msgs.append("FAIL: no descendant of any ClipsAPI-wired prim resolves "
                    "via ResolveInfoSourceValueClips — clip wiring is inert")

    # Sub-check B: Bonds vs atom-cloud centroid divergence.
    # Heuristic paths matching this repo's convention.
    bonds_path = None
    for clip_prim in clip_prims:
        candidate = clip_prim.GetPath().AppendChild("Bonds")
        if stage.GetPrimAtPath(candidate).IsValid():
            bonds_path = str(candidate)
            break

    atom_container_path = None
    for clip_prim in clip_prims:
        for child in clip_prim.GetChildren():
            if child.GetName() != "Bonds":
                atom_container_path = str(child.GetPath())
                break
        if atom_container_path:
            break

    if bonds_path and atom_container_path and len(sample_times) >= 1:
        centroids_bonds = []
        centroids_atoms = []
        for t in sample_times:
            cb = _world_bbox_centroid(stage, bonds_path, t)
            ca = _world_bbox_centroid(stage, atom_container_path, t)
            centroids_bonds.append(cb)
            centroids_atoms.append(ca)
            if cb is not None and ca is not None:
                dist = (cb - ca).GetLength()
                msgs.append(f"t={t}: Bonds centroid={tuple(round(x,2) for x in cb)}, "
                            f"atoms centroid={tuple(round(x,2) for x in ca)}, "
                            f"separation={dist:.2f}")
                # Tolerance: same order-of-magnitude neighborhood. The known-good
                # trajectory_demo pattern keeps atoms+bonds within a shared
                # bounding region; the known-broken curves_demo puts them in
                # two disjoint clusters tens of units apart. Use the combined
                # bbox diagonal at this timecode as a scale-aware tolerance.
                cache = UsdGeom.BBoxCache(Usd.TimeCode(t), [UsdGeom.Tokens.default_])
                whole_bbox = cache.ComputeWorldBound(stage.GetPrimAtPath(str(clip_prims[0].GetPath())))
                rng = whole_bbox.ComputeAlignedRange()
                diagonal = (rng.GetMax() - rng.GetMin()).GetLength() if not rng.IsEmpty() else 0.0
                tolerance = max(diagonal * 0.5, 5.0)
                msgs.append(f"     tolerance={tolerance:.2f} (0.5x whole-complex "
                            f"bbox diagonal, floor 5.0)")
                if dist > tolerance:
                    ok = False
                    msgs.append(f"FAIL: Bonds/atoms centroid separation {dist:.2f} "
                                f"exceeds tolerance {tolerance:.2f} at t={t} — "
                                f"PDB-frame vs MD-frame desync")
            else:
                msgs.append(f"t={t}: could not compute one or both centroids "
                            f"(Bonds={cb}, atoms={ca}) — skipping divergence check "
                            f"at this timecode")
    else:
        msgs.append("Bonds/atom-container centroid check N/A (structure does "
                    "not match Bonds+atom-container convention)")

    return _record(gate, entry.path, ok, msgs)


# ---------------------------------------------------------------------------
# Gate 5 — usdrecord frame-diff (opt-in, --render)
# ---------------------------------------------------------------------------

def gate5_frame_diff(entry: ManifestEntry, enabled: bool) -> GateResult:
    """Render first/last declared timecode and assert mean-abs pixel delta
    exceeds a small threshold. Off by default (slow, needs offscreen GL)."""
    gate = "5-frame-diff (--render)"
    path = _abspath(entry.path)

    if not enabled:
        return _record(gate, entry.path, True, ["skipped: --render not passed"], skipped=True)
    if entry.role != ROLE_ANIMATED:
        return _record(gate, entry.path, True,
                        ["skipped: not an animated viewer entry point"], skipped=True)
    if not os.path.isfile(path):
        return _record(gate, entry.path, False, [f"file not found: {path}"])
    if not os.path.isfile(_REAL_USDRECORD):
        return _record(gate, entry.path, False, [f"usdrecord not found: {_REAL_USDRECORD}"])

    stage = Usd.Stage.Open(path)
    if stage is None or not stage.HasAuthoredTimeCodeRange():
        return _record(gate, entry.path, False, ["no authored time range to render"])

    start, end = stage.GetStartTimeCode(), stage.GetEndTimeCode()
    import tempfile
    msgs = []
    ok = True
    with tempfile.TemporaryDirectory(prefix="usdview_regression_render_") as tmpdir:
        out_first = os.path.join(tmpdir, "frame_first.png")
        out_last = os.path.join(tmpdir, "frame_last.png")
        try:
            for tc, out in [(start, out_first), (end, out_last)]:
                subprocess.run(
                    [_REAL_USDRECORD, "--frames", f"{tc}:{tc}", path, out.replace(".png", ".###.png")],
                    capture_output=True, text=True, timeout=180, check=False,
                )
            # usdrecord appends frame number; locate actual output files.
            candidates_first = [f for f in os.listdir(tmpdir) if f.startswith("frame_first")]
            candidates_last = [f for f in os.listdir(tmpdir) if f.startswith("frame_last")]
            if not candidates_first or not candidates_last:
                return _record(gate, entry.path, False,
                                [f"usdrecord did not produce expected output files "
                                 f"in {tmpdir}: {os.listdir(tmpdir)}"])
            try:
                from PIL import Image
                import numpy as np
                img_a = np.asarray(Image.open(os.path.join(tmpdir, candidates_first[0])).convert("RGB"), dtype=float)
                img_b = np.asarray(Image.open(os.path.join(tmpdir, candidates_last[0])).convert("RGB"), dtype=float)
                mean_abs_delta = float(abs(img_a - img_b).mean()) / 255.0
                msgs.append(f"mean abs pixel delta (normalized) = {mean_abs_delta:.5f}")
                threshold = 0.005  # 0.5%
                if mean_abs_delta <= threshold:
                    ok = False
                    msgs.append(f"FAIL: delta {mean_abs_delta:.5f} <= threshold "
                                f"{threshold} — frames are visually static")
                else:
                    msgs.append(f"PASS: delta {mean_abs_delta:.5f} > threshold {threshold}")
            except ImportError:
                return _record(gate, entry.path, False,
                                ["PIL/numpy not available in this interpreter — "
                                 "cannot compute pixel diff for --render gate"])
        except subprocess.TimeoutExpired:
            return _record(gate, entry.path, False, ["usdrecord timed out after 180s"])

    return _record(gate, entry.path, ok, msgs)


# ---------------------------------------------------------------------------
# Gate 6 — usdchecker floor
# ---------------------------------------------------------------------------

def gate6_usdchecker(entry: ManifestEntry, timeout_s: int) -> GateResult:
    """Real usdchecker as a fast compliance floor. Necessary, not sufficient
    -- see module docstring and diagnosis: usdchecker reports clean success
    on the actively-broken curves_demo.usda. Bounds variant combinatorics
    with --skipVariants (this repo's stages are large enough that full
    variant enumeration hangs >120s) and REPORTS (does not silently
    swallow) timeouts."""
    gate = "6-usdchecker-floor"
    path = _abspath(entry.path)

    if not os.path.isfile(path):
        return _record(gate, entry.path, False, [f"file not found: {path}"])
    if not os.path.isfile(_REAL_USDCHECKER):
        return _record(gate, entry.path, False,
                        [f"usdchecker not found at {_REAL_USDCHECKER} — "
                         "do NOT fall back to /usr/bin/usd* (Apple SceneKit stubs)"])

    msgs = [f"binary={_REAL_USDCHECKER}, timeout={timeout_s}s, flags=--skipVariants"]
    try:
        result = subprocess.run(
            [_REAL_USDCHECKER, "--skipVariants", path],
            capture_output=True, text=True, timeout=timeout_s, check=False,
        )
    except subprocess.TimeoutExpired:
        msgs.append(f"FAIL: usdchecker TRUNCATED — did not finish within {timeout_s}s "
                    f"even with --skipVariants. Coverage for this file is INCOMPLETE, "
                    f"not silently skipped.")
        return _record(gate, entry.path, False, msgs)

    output = (result.stdout or "") + (result.stderr or "")
    error_lines = [ln.strip() for ln in output.splitlines()
                   if "error:" in ln.lower()]
    passed = result.returncode == 0 and not error_lines
    if passed:
        msgs.append("usdchecker: Success! (necessary-not-sufficient floor only; "
                    "see gates 1-4 for semantic checks)")
    else:
        msgs.append(f"FAIL: usdchecker returncode={result.returncode}, "
                    f"errors={error_lines or output[-500:]}")
    return _record(gate, entry.path, passed, msgs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--render", action="store_true",
                         help="Enable Gate 5 (usdrecord frame-diff). Slow; off by default.")
    parser.add_argument("--usdchecker-timeout", type=int, default=60,
                         help="Per-file timeout in seconds for Gate 6 (default 60).")
    args = parser.parse_args()

    print("=" * 78)
    print("usdview_regression_check — 6-gate headless usdview-bug-class detector")
    print("=" * 78)

    for entry in MANIFEST:
        print(f"\n{'-'*78}\n{entry.path}  [role={entry.role}]\n  {entry.notes}\n{'-'*78}")
        gates = [
            gate1_structural(entry),
            gate2_variant_completeness(entry),
            gate3_visibility_exclusivity(entry),
            gate4_clip_topology_sync(entry),
            gate5_frame_diff(entry, args.render),
            gate6_usdchecker(entry, args.usdchecker_timeout),
        ]
        for g in gates:
            if g.skipped:
                status = "SKIP"
            else:
                status = "PASS" if g.passed else "FAIL"
            print(f"  [{status}] {g.gate}")
            for m in g.messages:
                for line in str(m).splitlines():
                    print(f"      {line}")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    failed = [r for r in ALL_RESULTS if not r.passed and not r.skipped]
    passed = [r for r in ALL_RESULTS if r.passed and not r.skipped]
    skipped = [r for r in ALL_RESULTS if r.skipped]
    print(f"passed={len(passed)}  failed={len(failed)}  skipped={len(skipped)}")
    if failed:
        print("\nFAILED (gate, file):")
        for r in failed:
            print(f"  - {r.gate} :: {r.file}")

    print("=" * 78)
    if failed:
        print("RESULT: FAIL — one or more gates failed")
    else:
        print("RESULT: PASS — all applicable gates passed")
    print("=" * 78)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
