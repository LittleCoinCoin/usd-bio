# Specializes Arc Demonstration

**Goal**: Demonstrate that the Specializes arc makes base-class corrections propagate forcefully over local opinions, and contrast this behaviour with Inherits to make the LIVERPS strength-ordering visible [source: `../../../../__design__/openusd_for_research_architecture.md` §2.1 row S].
**Pre-conditions**:
- [ ] Element templates from `foundation_demo_v8` exist (for `/_class_/` namespace baseline)
- [ ] `pxr` Python environment loadable via `load_env.sh`
- [ ] Execution agent confirms Specializes arc semantics (source-class opinions override instance-local opinions) via context7 `/websites/openusd_release` before authoring — this is the most semantically subtle arc and the API (`UsdSpecializes`) must be read fresh
**Success Gates**:
- ⬜ `examples/composition_advanced/specializes_arc/` contains `build_specializes_demo.py` and `specializes_demo.usda`
- ⬜ `usdcat --flatten specializes_demo.usda` for the Specializes prim shows the corrected base-class value winning over the local opinion on the atom prim
- ⬜ `usdcat --flatten` for the Inherits prim (same demo file) shows the local opinion winning — confirming the contrast
- ⬜ `tests/composition_advanced/test_specializes_arc.py` opens the stage fresh and asserts: (a) Specializes prim resolves to corrected base value, (b) Inherits prim resolves to local value, (c) after updating the base class prim both prims update as expected
- ⬜ No direct `pxr` API call is made from memory — execution agent verifies `UsdSpecializes`, `UsdInherits` signatures via context7
**References**: [R03 §2.1](../../../../__design__/openusd_for_research_architecture.md) — LIVERPS table row S: Specializes as weakest arc, source-class overrides instance; [R03 §7](../../../../__design__/openusd_for_research_architecture.md) — "Specializes = weakest arc, source overrides instance" confirmed claim

## Step 1: Author base class and demo atoms using Inherits and Specializes
**Goal**: Create a single USDA file with (a) a base class prim defining a `bio:vdwRadius`, (b) one atom using `inherits` from that class while also having a local override, and (c) one atom using `specializes` from the same class while also having a local override.
**Implementation Logic**:
1. Define `/_class_/AtomBase` with `bio:vdwRadius = 1.70` (canonical Carbon vdW radius).
2. Define `/Atom_Inherits` as an `Xform` with `prepend inherits = </_class_/AtomBase>` AND a local opinion `bio:vdwRadius = 9.99` (sentinel to show local wins over Inherits).
3. Define `/Atom_Specializes` as an `Xform` with `prepend specializes = </_class_/AtomBase>` AND a local opinion `bio:vdwRadius = 9.99` (same sentinel — but Specializes should let the class override the local).
4. Both atoms should also carry `bio:elementSymbol = "C"` for context.
5. Verify: under LIVERPS, Inherits (I, strength 2) is stronger than Local (L, strength 1) — WAIT. The architecture doc states Local is strength 1 (strongest). Confirm this is correct: Local wins over Inherits, and Specializes (weakest, 7) means the source class wins over the instance. Execution agent MUST verify the exact strength semantics via context7 before assuming the test assertions — this is the key claim [assumption: architecture doc §2.1 states Specializes source overrides instance-local, but execution agent must confirm with official docs before writing assertions].
**Deliverables**: `examples/composition_advanced/specializes_arc/specializes_demo.usda` (prims `/_class_/AtomBase`, `/Atom_Inherits`, `/Atom_Specializes`; all with `bio:vdwRadius` opinions)
**Consistency Checks**: `usdcat examples/composition_advanced/specializes_arc/specializes_demo.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): author base class + Inherits/Specializes atom prims for specializes_arc demo`

## Step 2: Build demo script and verify flattened composed values
**Goal**: Write `build_specializes_demo.py` that programmatically authors the same scene (for reproducibility) and prints the resolved `bio:vdwRadius` for each prim to stdout, demonstrating the arc contrast.
**Implementation Logic**:
1. Use `Usd.Stage.CreateNew(...)` to author the same prim structure as Step 1.
2. For the Specializes prim, use `prim.GetSpecializes().AddSpecialize(Sdf.Path("/_class_/AtomBase"))` — confirm exact API via context7. For Inherits, use `prim.GetInherits().AddInherit(Sdf.Path("/_class_/AtomBase"))`.
3. After saving, open a second stage (fresh) and print `GetAttribute("bio:vdwRadius").Get()` for both prims. Include stdout labels: `"Inherits prim bio:vdwRadius: X (expected: 9.99 local wins)"` and `"Specializes prim bio:vdwRadius: X (expected: 1.70 base wins)"`.
4. This script is a demonstration aid; the read-back test in Step 3 is the authoritative assertion.
**Deliverables**: `examples/composition_advanced/specializes_arc/build_specializes_demo.py` (functions: `build_demo_stage`, `print_resolved_values`); script saves `specializes_demo.usda` to the same directory
**Consistency Checks**: `python examples/composition_advanced/specializes_arc/build_specializes_demo.py` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add build script for specializes_arc demonstration`

## Step 3: Read-back tests asserting Inherits vs Specializes resolved values
**Goal**: Assert the arc contrast from fresh stage open — Inherits prim shows local value winning, Specializes prim shows base-class value winning.
**Implementation Logic**:
1. Open `specializes_demo.usda` fresh with `Usd.Stage.Open(...)`.
2. Assert `/Atom_Inherits.bio:vdwRadius` == 9.99 (local opinion wins over Inherits, as L > I in LIVERPS) — tag assertion as `[source: context7 /websites/openusd_release Specializes/Inherits docs]` in a comment.
3. Assert `/Atom_Specializes.bio:vdwRadius` == 1.70 (base class wins over local, as Specializes source is stronger than instance local) — same source tag.
4. Modify `/_class_/AtomBase.bio:vdwRadius` to `2.00` on the stage, call `stage.Reload()` or equivalent, and assert both prims update: `/Atom_Inherits` still shows 9.99 (local still wins), `/Atom_Specializes` now shows 2.00 (base update propagates).
5. This Step 4 assertion is the most valuable: it proves Specializes propagates base corrections forcefully through composition, not just at authoring time.
**Deliverables**: `tests/composition_advanced/test_specializes_arc.py` (functions: `test_inherits_local_wins`, `test_specializes_base_wins`, `test_specializes_propagates_base_correction`)
**Consistency Checks**: `python tests/composition_advanced/test_specializes_arc.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for specializes_arc LIVERPS contrast`
