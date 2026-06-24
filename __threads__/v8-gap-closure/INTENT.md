---
topic: v8-gap-closure
created: 2026-06-24
---

# Brief

## Goal — bring foundation_demo_v8 to architecture-doc parity

`examples/foundation_demo_v8/` is the project keystone, but it demonstrates a
deliberate *subset* of `__design__/openusd_for_research_architecture.md` —
protein+ligand, single-phase, single-layer. The goal of this topic is parity: every
pattern the architecture doc specifies is demonstrated in v8, in Python. This is a
large, multi-cycle chunk of work; C++/schema is deferred indefinitely (per the
`restart` decisions), and the p53-mdm2 application is the *next* topic, not this one.

## How to approach this (guidance, not a deliverables checklist)

The cycle agent owns the concrete plan; this section is direction on *how* to tackle
something this big with rigor.

- **Start from the existing gap analysis — do not re-derive it.** The explicit gap
  report already exists:
  `__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md`
  (2026-02-15). Its **§3 Gap Analysis** (scale/solvent/file-format/bonds, §3.3
  composition arcs not yet exercised, §3.4 provenance) and **§5 Prototyping
  Experiments Still Needed** (six prioritized experiments, each with an explicit
  deliverable) are the authoritative backlog for this topic. The audit's job is to
  **validate and refresh** that report against current code — it is ~4 months old, so
  confirm each gap still holds and nothing has been closed since — not to invent a new
  inventory. A useful lens while refreshing: deferred-by-design architectural work (the
  bulk — §3.3 arcs and the §5 experiments) vs genuine defects (portability paths, thin
  tests). Note that the report's schema/GUI/pipeline material (§2, §6, §7, and §8
  Phases 1–5) is **out of scope** here — C++/schema is deferred; the in-scope work is
  §3 and §5.
- **Drive it with a roadmap.** Use `/managing-roadmaps` to turn the audit into a
  dependency-ordered graph and execute it BFS across cycles. The roadmap — not this
  brief — defines the per-leaf deliverables and success gates, ordered so foundational
  work (e.g. a test harness, departmental layering) precedes what builds on it.
- **Work as a team.** Delegate per-gap deep analysis and per-leaf implementation to
  sub-agents. Use **Claude Sonnet 4.6** for implementor and verifier sub-agents; keep
  the orchestrator (Opus) for synthesis, sequencing, and adjudication.
- **Verify, and be the tie-breaker.** Every implemented leaf is checked by a verifier
  sub-agent. On any discrepancy between implementor and verifier, the orchestrator
  rules — the sentinel of rigor and high work-ethic, prioritizing honest, evidenced
  outcomes over apparent progress.
- **Lean on cheap docs.** Use the `context7` MCP tools for OpenUSD reference
  (resolve-library-id → query-docs, prefer `/websites/openusd_release`) rather than
  re-deriving USD concepts; fall back to in-repo `docs/` if context7 is unavailable in
  a headless run.
- **Evidence over prose.** Runnable demos + committed `.usda` outputs + passing tests
  are the unit of "done"; build in the established v8 idiom (`/_class_/` templates,
  `bio:` namespace, CPK colors, `representation` VariantSet) and honor the honesty
  contract.

## Testing must be falsification-resistant (mandatory, build it early)

There is **no Playwright/MCP-style harness** here that lets an agent independently
exercise its own USD output, so the agent can otherwise "pass" tests that merely
re-assert what its generator just wrote — tautological tests that catch nothing. A
test is only useful if it **reads the artifact back as a downstream consumer would**
and checks it against *independently stated* expectations. Tests must cover two
distinct dimensions:

- **Integrity** — the artifact is valid, well-formed USD.
- **Intent-conformance** — the artifact is *what was expected* (right hierarchy,
  right `bio:` values, variants resolve, trajectory samples populate).

The `usd` CLI is a good start but far from enough on its own. Layer the tooling
(confirm exact APIs via `context7` at build time):

1. **`usdchecker`** — baseline compliance/integrity gate on every produced
   `.usda`/`.usdc`. Necessary, not sufficient.
2. **Custom validators via the `UsdValidation` framework** — register Python
   prim/stage/layer validators (`UsdValidation.ValidationRegistry().RegisterPrimValidator(...)`)
   that encode domain invariants: e.g. every atom prim carries `bio:element` and
   inherits from a `/_class_/` element class; residue atom counts match topology; the
   `representation` variant cascade resolves at every level; clip-backed positions are
   populated across the time range. This domain layer is what makes "integrity" mean
   something biological, not just "parses".
3. **Programmatic read-back (the core)** — open the produced file *fresh* with
   `Usd.Stage.Open`, traverse the hierarchy, resolve *composed/inherited* values via
   `prim.GetAttribute(...).Get()`, switch variant selections, and sample time-varying
   data — then assert the observed structure and values against expectations derived
   from the source data (PDB/XTC), **not** from the generator's own in-memory state.
   This is the user-like behavior simulation that makes a test non-falsifiable.
4. **Golden/baseline diffing** — `usddiff` (and `usdcat`/`usdtree` for inspection)
   against small committed reference `.usda` files for regression on representative
   fixtures.

Stand this harness up **early** in the roadmap (it is foundational — every later gap
closure relies on it as its regression net), and apply it to the *existing* v8
artifacts first so the baseline is trustworthy before new work lands. A verifier
sub-agent's sign-off should require these read-back assertions to exist and pass, not
just that a demo ran.

## The authoritative gap source

`__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md` is the
explicit gap analysis. Anchor the audit and roadmap on it rather than re-deriving from
the architecture doc. Its in-scope backlog, in brief:

- **§3.1 Scale:** solvent excluded (183K atoms → PointInstancer); `.usda` → `.usdc`
  binary; 20 frames → lazy-loaded clip-template pattern across all XTC files.
- **§3.2 Bonds at scale:** per-bond cylinder prims are too heavy; evaluate
  BasisCurves / implicit / shader bonds.
- **§3.3 Composition arcs not yet exercised:** References (asset libraries), Payloads
  (deferred loading), Ensemble (`ReplicaID`) / Perturbation (`Genotype`) / Parameter
  (`ForceField`) VariantSets, Specializes, departmental layering
  (Biology/Protocol/Dynamics/Analysis/Review), analysis data as USD attributes.
- **§3.4 Provenance:** structured lineage metadata.
- **§5 Experiments (prioritized, with deliverables):** (1) PointInstancer for solvent,
  (2) binary format + clip templates, (3) departmental layering with a real workflow,
  (4) Ensemble VariantSet with Payload swapping, (5) BasisCurves for bonds,
  (6) References vs SubLayers.

Also fold in the genuine defects surfaced during `restart` (re-verify): hard-coded
ShinobuLab paths in the converters; near-zero test coverage. The §5 priority ordering
is a strong starting hint for roadmap sequencing, but the refreshed audit owns the
final ordering.

## Scope boundaries

- **In scope:** Python prototype only — audit, roadmap, demos, `.usda` outputs,
  portability fixes, tests, correcting stale v8 `ROADMAP/` statuses.
- **Out of scope:** C++/schema authoring, CMake/CI/vcpkg revival; the p53-mdm2
  application (the next topic); rewriting the architecture doc's decisions (implement
  them, don't alter them).

## Done definition

Architecture-doc parity, operationalized as the in-scope backlog of
`01_v8_to_production_perspective.md` (§3 gaps + §5 experiments) closed: each with a
runnable demo + committed `.usda` (or equivalent evidence), defects fixed, and v8
`ROADMAP/` statuses truthful. The roadmap defines the path; the topic finishes
`proposed-resolution` for PI review when that backlog is closed.
