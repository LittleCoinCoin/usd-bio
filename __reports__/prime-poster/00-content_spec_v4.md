# PRIMe Site-Visit Poster — Content Specification (v4)

**Event:** WPI-PRIMe site visit, 2026-09-03 · **Poster number:** P-14
**Submission:** PDF **and** PPTX to `planning@prime.osaka-u.ac.jp` by **2026-08-21**
**Layout:** adapted portrait Morrison "Better Poster" — claim bar / center / card band
**Status:** v4.1. Rebuilt around the modality-span claim (PI, this session). Folds in a
four-model fact-sampling round and three corrections it surfaced. Every number verified
against the working tree this session (§11).

**Title (fixed by PI):**

> **USD Bio: OpenUSD derived schema as the shared data format for bio-digital twins**

**Conventions.** US spelling (`-ize`, `center`). One term per concept: **bio-digital
twin** never shortens to "twin"; **OpenUSD** is named, never called "the format" on first
use in a block.

---

## 1. The main claim, restated

Previous versions led with how *cheap* integration is — line counts, atom counts, diff
sizes. Those are craft facts. They are true, they are verifiable, and none of them names
a problem a structural biologist, an MD specialist, or a systems-biology modeler actually
suffers from. A delegation asking whether the center is delivering multi-scale
bio-digital twins gets no answer from a line count.

**The claim that does answer them:**

> The case study already spans the kinds of data every other field will bring — structured
> text, numbers with units, three-dimensional geometry, time series, discrete state, and
> visual representation. We have not yet found data OpenUSD could not link.

This is the right claim for four reasons.

1. **It generalizes beyond p53 without overclaiming.** Molecular dynamics and Boolean
   network simulation are not two narrow cases; between them they exercise six modality
   classes. Imaging, omics, and clinical records bring the same six.
2. **It is falsifiable and not yet falsified**, which is a stronger epistemic position
   than a capability list and reads as such to reviewers.
3. **It names its own untested edge.** Nothing here proves audio. Saying so is the
   cheapest credibility purchase on the board — a review delegation grades calibration.
4. **It is a platform claim**, which is the presenter's actual contribution to the center.

### The modality table — the poster's central content

| Kind of data | Where it appears in the case study |
|:--|:--|
| **Structured text** | PDB records from 1YCR; the MaBoSS `.bnd` network definition and `.cfg` parameter file |
| **Numbers with units** | ΔΔG in kcal/mol; atomic masses, van der Waals and covalent radii; stage declared in Ångström (`metersPerUnit = 1e-10`) |
| **Three-dimensional geometry** | 818 atoms, 2 chains, 98 residues, 834 bonds, real coordinates |
| **Time series** | 500 frames of per-node probability on the Analysis layer; MD trajectory frames streamed on demand |
| **Discrete state** | The five-node Boolean network's node states |
| **Visual representation** | Four switchable display modes; CPK colors inherited from shared element templates; renders in standard viewers |

**Not proven: audio.** Print this. It costs one line and it is the sentence that tells a
reviewer the rest of the board was written by someone who distinguishes what they have
shown from what they assume.

---

## 2. The occasion

A JSPS review delegation and senior center staff, assessing delivery against the center's
assigned mission — human bio-digital twins for multi-scale, model-driven research into
disease and diagnosis. Many pass the board mid-conversation.

1. **The claim bar must land unread.** Everything below is for the minority who stop.
2. **The contribution is platform, not biology.** p53–MDM2 is the case study.
3. **Formal, and allowed to shine.** Impact comes from true magnitudes and from an honest
   negative claim, never from evaluative language.

### The alignment worth using

The institute is the Premium Research Institute for **Human Metaverse Medicine**. OpenUSD
is the data standard the metaverse industry converged on. This poster is the institute's
name, implemented.

**Constraint added in v4: no affiliation with the Alliance for OpenUSD may be implied.**
There is no membership. The PI argued the case to the Director eighteen months ago on
recruitment; that is a position held, not an institutional relationship. Every AOUSD
reference in v3 is removed. Standardization may appear only as the presenter's stated
goal, never as a process the center is in.

### Hard format constraints

| Constraint | Value |
|:--|:--|
| Size | A0 portrait, 841 × 1189 mm |
| Top band | **200 mm, white background, black text only** |
| Band contents | P-number, title, authors (○ marks presenter), affiliations, logos |
| Language | English · **Deliverables** PDF **and** PPTX |

**Still open with the organizers:** February's template asked for a flash talk slide; this
one never mentions one.

---

## 3. The super claim

**Recommended:**

> ## Every lab keeps its own tools and file formats. Their results already compose into one bio-digital twin.

The word **already** is new in v4 and it is doing real work: the delegation's question is
whether this has happened yet, and "already" converts an architectural principle into a
delivered state. It is defensible — §11 lists what it cashes out to.

**Supporting line:**

> *We adopted OpenUSD, the data standard the metaverse industry converged on, and extended it for biology.*

**The exposure, and the prepared answer.** Someone may ask *which labs?* The honest answer
is that no center lab has onboarded yet — the demonstration composes four **external
third-party toolchains**, which is a harder test than four internal ones. Do not weaken
the claim to pre-empt this; have the answer ready and volunteer the next-phase framing.

**Alternate, if a modality-led bar is preferred:**

> *Six kinds of scientific data, one representation, no exception found yet.*

Sharper and closer to §1's actual argument. Weaker on the "keeps its own tools" benefit
that a lab head hears as directly relevant to them. Either is defensible; the recommended
one is the more welcoming.

**Rejected:** the problem-led alternate from v2/v3, *"…should not take forty-five
converters."* Two sampling agents independently flagged that 45 is arithmetic (10 choose
2), not a measured fact, and it would be the only unsourced number on a board where every
other figure traces to a committed file. Cut.

### Author block (header band, white only)

```
P-14
USD Bio: OpenUSD derived schema as the shared data format for bio-digital twins

○ Jacopin Eliott¹˒²,  Wu Yichao¹˒³,  Shinobu Ai¹˒³

1  Premium Research Institute for Human Metaverse Medicine (WPI-PRIMe), The University of Osaka, Japan
2  RIKEN, Center for Biosystems Dynamics Research, Japan
3  RIKEN, Center for Computational Science, Japan
```

### The title, and the one thing the body must carry

All four sampling agents flagged that no formal USD schema exists yet — verified: no
`plugInfo.json`, no `generatedSchema.usda`, no `usdGenSchema` output, and the attributes
are `custom`, which in USD means precisely *not declared by a schema*.

**The PI's resolution stands: the title states the purpose of the research, and the body
demonstrates the span.** That is a coherent position and it is not a lie. It carries one
obligation, which this spec now enforces: **card 7 must state without hedging that the
formal schema is the goal and that what exists today is a validated convention layer.**
With that sentence on the board, the title is a statement of direction and the poster
remains the honest document it has been throughout. Without it, the title is the only
unhedged claim on the board.

**Prepared answer if a USD-literate visitor asks to see the schema:** *"The formal schema
is the goal. What exists today is the validated prototype of its conventions — a `bio:`
namespace and shared class templates, tested end to end. The schema is what those
conventions become once they stop changing."*

---

## 4. Space allocation — A0 portrait

```
┌───────────────────────────────────────────────────────────┐
│ HEADER — 841 × 200 mm — WHITE ONLY                        │
├───────────────────────────────────────────────────────────┤
│ SUPER CLAIM — 841 × 170 mm                                │
├───────────────────────────────────────────────────────────┤
│ CENTER — 841 × 500 mm                                     │
│ FIGURE 1 — the modality span, carried by the case study    │
├───────────────────────────────────────────────────────────┤
│ CARD BAND — 841 × 319 mm — 5 across × 2 down = 10 slots   │
│ 8 cards + the diff panel occupying 2 slots (bottom right) │
└───────────────────────────────────────────────────────────┘
```

**Eight-second reading path:** claim bar → the six modality labels running along the
figure → done.

---

## 5. The center — Figure 1

**"Six kinds of data, one representation"**

The figure's organizing principle changes in v4. It is no longer a layer stack with a
result attached; it is the modality table made visual, with the case study as the thing
that demonstrates each row.

### Structure

**Left — four layers, four owners**, as separated planes:

| Layer | Owner tag | Carries |
|:--|:--|:--|
| Biology | structural biology | structure, atoms, bonds |
| Protocol | simulation | simulation setup parameters |
| Perturbation | systems biology | the mutations under test |
| Analysis | analysis | simulation results over time |

**Center — composition.** The planes resolving into one scene: a recognizable p53–MDM2
complex with the three contact residues marked. Visual grammar is **resolution, not
pipeline** — layers converging on one object, not a conveyor belt.

**Right — what came out.** Two probability curves, `31 %` and `86 %` as curve labels.

**Running along the base of the whole figure — the six modality labels**, each with a
one-word pointer to where in the figure it lives. This band is what a walker-past reads.

**The closing line, set apart:**

> **Not proven: audio.**

### Caption — the poster's one sentence of rhetorical force

> One hypothesis selection is the only thing authored by hand. The geometry it brings in
> has nine of tryptophan 23's fourteen atoms removed, the binding-energy change is
> predicted for that same mutation, and 500 frames of p53 response come back onto a layer
> that never touches the structure below it.

### Two precision constraints

1. **Never say the truncated geometry was sent to the predictor.** `converters/ddmut_client.py`
   submits a PDB accession, chain, and mutation *string* against deposited 1YCR. The true
   and stronger statement: the mutation is **declared once**, and both the geometry swap
   and the energy query follow from that declaration.
2. **"p53 response", never "cell fate".** The five-node model outputs `P(p53 up)`; it
   emits no fate.

### Must not

Label anything with USD API vocabulary. Draw a fifth (Review) layer — specified,
unauthored. Show all four curves. Show the conversion equation; its constants are
unfitted.

### Machine-generated elements

Three, and they must not be redrawn: the **molecular structure** (`usdrecord` on
`demos/p53_mdm2_integrated.usda`), the **probability curves**
(`analysis/p53_mdm2_analysis.usda`, `bio:maboss:prob:<node>`, 500 frames), and the **diff
panel** (§6.2).

---

## 6. Card band — 8 cards plus the diff panel

Five across, two down. Body ≤ 28 words. Each card carries at least one number.

### 6.1 The eight

**1 · What USD Bio adds**
> A biology vocabulary inside OpenUSD: elements, residues, molecules, simulation
> parameters. All 818 atoms inherit mass, radius and color from shared templates, and
> every value carries its units and its provenance.

**2 · Four outside tools, none of them modified**
> A crystal structure from the Protein Data Bank, a binding-energy predictor at the
> University of Queensland, a published network model from Institut Curie, and GROMACS.
> Each kept its own format. None was changed.

**3 · One layer per department**
> Structure, protocol, perturbation, and analysis are separate layers with separate
> owners. Opened alone, the structure layer carries none of the annotations the layers
> above it added — asserted by test, not assumed.

**4 · The case study**
> Crystal structure 1YCR — human MDM2 bound to the p53 peptide, the interface targeted by
> a whole class of cancer drugs. Nine atoms removed from tryptophan 23; energy predicted;
> the p53 network simulated.

**5 · How we know it is right**
> Fifty-three automated checks, all passing. Every stored artifact is asserted against the
> source data, never against the code that wrote it, with one independent method per
> stage — including re-running the simulation from scratch.

**6 · Trajectories stream, frame by frame**
> Molecular dynamics frames load on demand instead of all at once — 20 frames sampled
> across a roughly 70,000-frame ABL kinase trajectory from Shinobu Lab, with its 61,273
> water molecules carried as one instanced set.

*Changed in v4.1.* This card previously carried the container's cross-cluster GPU parity
(H100 vs V100, 2.6 parts per million). **That fact is not about the USD framework** — it
is container and HPC engineering, and on a board whose entire argument is *one
representation for six kinds of data*, a card about simulation-engine portability is the
strongest available evidence of lost focus. It also invites the reader to wonder what the
center is funding. It moves to the conversation kit (§9), where it answers a question if
one is asked, and off the board otherwise.

**7 · Where this is going**
> Today USD Bio is a validated convention layer — a `bio:` namespace and shared templates,
> tested end to end. The goal is to make it a formal OpenUSD schema domain for biology,
> the counterpart of the physics standard the format already carries.

**8 · What the center gets**
> Any PRIMe lab contributes to a shared bio-digital twin using the formats it already has.
> Contributions compose instead of colliding, every layer keeps its provenance, and the
> result opens in freely available standard viewers.

**Two QR codes** at the band's edge: the repository and `openusd.org`.

### 6.2 The evidence panel — two slots, bottom right

**Heading:** `Nothing moves that we did not move`

Three commands, in this order. The order is the argument: *untouched → one bounded change
→ and the change can be undone.*

```
$ md5 maboss/reference/p53_Mdm2.bnd maboss/output/p53_Mdm2_W23A.bnd
33ab9a84315bcf2d507692ca9a750d7e
33ab9a84315bcf2d507692ca9a750d7e

$ diff maboss/reference/p53_Mdm2_runcfg.cfg maboss/output/p53_Mdm2_W23A.cfg
8c8
< $KMn_pMC=1;
---
> $KMn_pMC=0.0082602991708;
12c12
< $KMn_pMCD=1;
---
> $KMn_pMCD=0.0082602991708;

$ ddg_from_s(0.0082602991708)
-6.192000
```

**Caption:**
> The network model is Institut Curie's, published and fetched unchanged. Our pipeline
> never writes it — the same checksum goes in and comes out. It sets two parameters and
> nothing else. Read either one back and the binding energy that produced it returns
> exactly, so the crossing from molecule to network loses nothing.

### Why this is the argument, and what it replaces

v4's first draft claimed the pipeline "returns the model byte-identical", which implies a
round trip that does not happen: `maboss/emit_model.py` step 4 copies the reference
topology verbatim, so a matching checksum was never at risk. Stated that way the panel
takes credit for restraint it did not have to exercise, and a reviewer who reads the
source finds that out.

**The honest version is stronger**, and it has two legs, both tested:

1. **The change is bounded.** The network's topology — the biology of the model, the part
   a collaborator owns — is not something this pipeline writes at all. The checksum is
   the proof of that restraint, not proof of a round trip. What it does write is two
   named parameters, and the `diff` is the proof that it wrote nothing else.
   *Source:* `emit_model.py` — "the reference `.cfg` text with ONLY `$KMn_pMCD` and
   `$KMn_pMC` reset to `S` … everything else byte-for-byte unchanged."
2. **The change is reversible.** `dg_correlation.ddg_from_s` is a closed-form inverse, and
   the emitted value carries twelve significant figures specifically so the molecular
   quantity survives. Verified this session: `S = 0.0082602991708 → ΔΔG = −6.192000`,
   against an original of −6.192. `tests/test_maboss_emit.py` asserts this per variant at
   a tolerance of 1e-4, and describes itself as closing the PI's inverse loop.

Together they say what a shared representation has to be able to say: **the system only
ever adds, and what it adds can be taken back out.** Nothing is silently altered, and
nothing is destroyed crossing the scale boundary. That is the property that makes it safe
for a lab to put its work in.

**It pairs with card 3.** Card 3 shows that *layers* do not contaminate each other; this
panel shows that an *external file* survives the same treatment. One claim, two
demonstrations, different scopes.

**Why it earns two slots.** It answers the question a lab head actually has — *what does
joining cost me, and can I get my work back out?* Reproducible live in front of a
reviewer. Set it to read at 1 m; keep the `$` prompts. It is the one element on the board
that visibly did not pass through a designer, and that is its value.

**Third line, presentational note.** `ddg_from_s(...)` is shown bare rather than as a full
`python -c` invocation with an import path. This is the one place the panel departs from
literal transcript, and it is a legibility trade: the real one-liner is long enough to
wrap and would bury the number. If a strict-transcript reading is preferred, the full form
is `python -c "from p53_mdm2.maboss.dg_correlation import ddg_from_s; print(ddg_from_s(0.0082602991708))"`.

### 6.3 The visibility swap

Card 7 as written commits the center to nothing and now carries the schema-status
sentence §3 requires — **do not swap it out.** If the director green-lights a visibility
pitch, swap card 6 or 8 for:

**7b · Interoperability already in place**
> USD Bio output opens in the same tools that drive industrial digital twins, because the
> underlying standard is theirs. Biological models become directly composable with the
> software built around it.

No date, no named partner, no deliverable without the director's agreement. **And no
implication of Alliance membership** (§2).

---

## 7. Honesty ledger

| On the poster | Status | If asked |
|:--|:--|:--|
| Six modalities, no exception found | **Measured** — every row of §1's table traces to a committed artifact | The claim is "not yet falsified", not "proven impossible to falsify" |
| Audio not proven | **True and stated** | Deliberately printed |
| Four outside tools, none modified | **Measured.** PDB 1YCR, DDMut-PPI, Institut Curie model, GROMACS | Response bodies committed verbatim |
| Nine atoms removed | **Measured.** `bio:atomCount` 14 → 5 | Real 1YCR coordinates, truncated; "no fabricated positions" per the files' own doc strings |
| The pipeline never writes the network topology | **Measured.** `emit_model.py` copies the reference `.bnd` verbatim; MD5 identical across all four | **Do not say "returns it byte-identical"** — that implies a round trip. It is never written. The checksum proves restraint, not survival |
| Only two parameters change | **Measured.** `diff` is exactly `8c8` and `12c12` | `emit_model.py`: "everything else byte-for-byte unchanged" |
| The change is reversible | **Measured.** `ddg_from_s(0.0082602991708) = −6.192000` against an original of −6.192; asserted per variant at 1e-4 in `tests/test_maboss_emit.py` | Closed-form logit inverse; the value is written at twelve significant figures for exactly this reason |
| Cross-cluster GPU parity | **Measured** (job 28) — **but off the board.** Not a USD-framework claim | Conversation only. RIKEN hardware, never "the center's" |
| 53 automated checks, all passing | **Measured** this session. **The README's 39 is stale** (2026-07-31; cycle-008 took it to 53) | Re-run the morning of export and print what it says |
| Binding-energy changes | **Real** DDMut-PPI predictions | Predicted, not experimentally measured. Queried by mutation string against deposited 1YCR |
| p53 activity curves | **Real** MaBoSS 2.6.6, seed 100, 50 000 samples, 500 frames | Deterministic, re-runnable |
| The ordering across mutations | **Measured**, asserted three ways | The claim the demonstration makes |
| The *size* of the 31 → 86 gap | **Not protected.** Runs through unfitted constants | Why the percentages are curve labels. Volunteer this before being asked if the reviewer is a modeler |

| Trajectories stream | **Real**, ABL kinase, Shinobu Lab | 4,676-atom complex, 61,273 waters, 20 frames strided from ~70,000 |
| Schema | **Convention layer today; schema is the goal.** Card 7 says so | See §3's prepared answer |
| Review layer | **Specified, not authored** | Do not draw it; do not name it in card 3 |
| Alliance for OpenUSD | **No membership. Nothing may imply one** | A position argued to the Director, not an institutional relationship |

---

## 8. Do not print

Found by the sampling round and verified.

| | Why |
|:--|:--|
| `docs/09_performance_strategies.md` figures | Headed **"Performance Targets"** — design goals, not measurements |
| `docs/13`'s "~95 MB for 20 frames" | Does not match disk; the clip is 19.0 MB |
| 50 000 samples as a data-volume number | It is a Monte-Carlo trajectory count reaching USD as one scalar. What is stored is 10,000 floats in 310 KB — wrong by four orders of magnitude if used as volume |
| Ensemble / `ReplicaID` as a delivered capability | Demonstrated on synthetic clip stubs, not data |
| The `subLayers` block as a second raw-text specimen | It lists three sublayers, not four; Biology is reached transitively, and a reviewer counting departments gets a question |
| `foundation_demo_v8`'s five open gate failures | Real, documented, irrelevant here. Conversation answer only |
| The container-build history | Route A/B, fakeroot, GPU contention, SASS audit. Engineering hygiene; reads as sysadmin work on a board |
| LIVERPS and composition-arc vocabulary | Illegible to this audience, and an architecture diagram is what February already showed |

---

## 9. The conversation kit

1. *"Between molecular dynamics and Boolean network simulation we already cover six kinds of data. We have not found one OpenUSD couldn't hold. Audio, we haven't tested."*
2. *"We never write Curie's model — same checksum in and out. We set two parameters. And you can read either one back and recover the binding energy exactly, so nothing is lost crossing from the molecule to the network."*
3. *"The only thing edited by hand in that whole result is nine atoms."*

**Off the board, for questions only:** *"The same GROMACS container runs on an H100 and a
V100 off one shared filesystem, energies agreeing to two parts per million."* This is
RIKEN hardware, the presenter's own labs — never "the center's". It is not a claim about
the USD framework and it does not go on the poster (§6.1, card 6).

Held in reserve, said **before** being asked if the reviewer is a modeler: *"The
energy-to-parameter conversion is monotone and invertible, which is all the mechanism
needs. Its constants are not fitted, so the ordering across the mutants is the claim, not
the size of the gap."*

---

## 10. Tomorrow, ordered by risk

1. **Re-run the suite and print whatever it says** — it moved 48 → 53 in one cycle:
   ```bash
   . ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" ~/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py
   ```
2. **Render the three machine-generated elements** (§5).
3. **Ask the organizers about the flash talk slide**; confirm portrait in the same message.
4. Pick the super claim from §3.
5. Figure 1 built around the modality band.
6. Export PDF + PPTX as `P14-Eliott_Jacopin-Poster-WPI-PRIMe_Site_Visit_20260903.{pdf,pptx}`.
7. Send to `planning@prime.osaka-u.ac.jp`.

**Separately, not poster work:** `examples/p53_mdm2/cluster/README.md` still carries a
bolded banner saying no dgx1 GPU has run the image. Job 28 and two passing gates
contradict it. Worth fixing before a QR code points anyone at the repository.

---

## 11. Verification log

All run against the working tree this session.

| Claim | Command | Result |
|:--|:--|:--|
| 53 checks passing | `tests/run_tests.py` | `ALL PASS (53/53 checks)` |
| Cross-cluster parity | `cluster/evidence/dgx1_gpu_smoke.txt` | Job 28, 2026-08-12. V100 −4.1673953e+04 vs H100 −4.1674062e+04, `CROSSCLUSTER_ENERGY_REL=2.61554e-06`, gate PASS |
| 14 → 5 atoms | `grep bio:atomCount composition/geometries/*.usda` | wild-type 14, W23A 5 |
| `.bnd` byte-identical | `md5 maboss/reference/*.bnd maboss/output/*.bnd` | `33ab9a84…` × 4 |
| Two-line `.cfg` diff | `diff` against the reference | `8c8`, `12c12`, nothing else |
| Topology never written | read `maboss/emit_model.py` step 4 | Verbatim copy of the reference `.bnd` |
| Change is reversible | `ddg_from_s(0.0082602991708)` | `-6.192000` against an original of `-6.192`; F19A and L26A also recover exactly |
| ABL system size | `solvent_instancer.usda`, `docs/11` | 4,676 complex atoms; 61,273 waters = 183,819 atoms; 20 frames of ~70,000, stride 3500 |
| No schema on disk | searched for `plugInfo.json`, `generatedSchema.usda`, `apiSchemas` | None present; attributes are `custom` |

---

## 12. Sources

- Template and poster numbers: `~/Documents/career/Events/PRIMe_site_visit_20260903/Poster_template_site_visit_2026.pdf`
- February precedent: `~/Documents/career/Events/WPI-PRIMe_4th_Symposium_20260207/`
- Results, testing discipline, correlation-constant caveat: `examples/p53_mdm2/README.md`
- Architecture and departmental layering: `__design__/openusd_for_research_architecture.md`
- Container evidence: `examples/p53_mdm2/cluster/evidence/`
- Trajectory streaming: `examples/foundation_demo_v8/`
- Illustration assets: [`01-illustration_assets_v1.md`](01-illustration_assets_v1.md) — **needs a v2 for the modality band**
