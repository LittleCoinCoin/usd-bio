# PRIMe Site-Visit Poster — Content Specification

**Event:** WPI-PRIMe site visit, 2026-09-03 · **Poster number:** P-14
**Submission:** PDF **and** PPTX to `planning@prime.osaka-u.ac.jp` by **2026-08-21**
**Session:** attended PI session, 2026-08-20. Scope, main claim, figure content briefs, space allocation.
**Status:** v0 — content only. Visual execution belongs to the Claude Design system.

---

## 1. The occasion, and what it does to the content

The audience is a JSPS review delegation and senior center staff, assessing whether
PRIMe is delivering on its assigned mission: human bio-digital twins for multi-scale,
model-driven research into disease and diagnosis. They are scientists, but not
specialists in any one poster's field, and many will pass the board while in
conversation rather than stopping to read it.

Three consequences, and every content decision below follows from them:

1. **The poster must land its claim from two metres away, without being read.**
   The title plus one figure carries the whole message. Everything else is for the
   minority who stop.
2. **The contribution is platform, not biology.** Eliott's role in the center is to
   supply software infrastructure the application labs use. p53–MDM2 is the case
   study that proves the infrastructure works — it is never the subject.
3. **Formal, and allowed to shine.** The occasion tolerates a confident claim. It
   does not tolerate an unearned one, and every number on this poster is measured
   and reproducible from the repository.

### Hard format constraints (from the official template)

| Constraint | Value |
|:--|:--|
| Size | A0. Template writes "1189 mm × 841 mm"; **February's poster was portrait (841 × 1189 mm) under identical wording and was accepted** — hold portrait |
| Top band | **200 mm, white background, black text only.** No colour, no image bleed into this band |
| Band contents | P-number, title, author names (○ marks the presenter), affiliations |
| Below band | Free, colour permitted |
| Language | English |
| Logos | PRIMe logo required (February also carried RIKEN — keep both) |
| Deliverables | PDF **and** PPTX |

**One item to confirm with the organizers:** February's template asked for "poster
**and flash talk slide**". This template asks only for "both PDF and Power Point
files" and never mentions a flash talk. A one-line email settles whether the flash
talk slide is still expected, and it changes tomorrow's workload.

---

## 2. Scope

**In scope.** OpenUSD as a shared data representation for multi-scale biology; the
`bio:` schema work that adapts it; the departmental layering that lets independent
labs contribute without colliding; and one worked case study carried end to end.

**Out of scope.** Composition-arc mechanics (LIVERPS, class prims, variant sets,
value clips) as named concepts. These are the substance of the work and they earn
*at most one line each* in a single technical strip. A reviewer who wants the detail
is directed to the QR code. The February poster's centre panel was an architecture
diagram; this one's must be a result.

**Deliberately not on the poster.** The 39-check test harness design, the container
build route, cluster portability evidence, the anti-chimera gate. All real, none
legible to this audience in the space available. One number from the test suite
survives, in the honesty strip.

---

## 3. Main claim

One sentence, and everything on the board serves it:

> **Every lab in the center keeps its own tools and file formats, and their results
> still compose into a single, inspectable bio-digital twin — because we adopted the
> data format that film and industrial-metaverse pipelines already solved this
> problem with, and extended it for biology.**

### The three supporting claims

Each owns one panel. Each is separately falsifiable.

| # | Claim | Evidence on the poster |
|:--|:--|:--|
| **S1** | The integration problem is real and it is a *format* problem, not a science problem | The heterogeneity figure: five labs, five file formats, no common ground |
| **S2** | OpenUSD solves it, and biology fits into it | The layer-stack figure: five departmental layers composing to one stage; each layer independently authored, versioned, replaceable |
| **S3** | It works end to end on a real disease-relevant system | p53–MDM2: one mutation traced from atomic structure to a cell-fate probability, and the answer moves the right way |

### Title

**Recommended:** *One Scene, Every Scale — OpenUSD as the Shared Data Format for Bio-Digital Twins*

Decodes on one pass, names the technology, states the span, and "scene" is both the
USD term and plain English. Alternatives, if a plainer or a drier register is wanted:

- *A Common Data Format for the Bio-Digital Twin: OpenUSD for Multi-Scale Biology* (plainest; safest with a conservative delegation)
- *From Atoms to Cell Decisions in One File: OpenUSD Infrastructure for Multi-Scale Medicine* (leads on the case study's span; strongest if S3 is the panel people stop at)

February's title — *Open Universal Scene Description for Heterogeneous Data
Integration* — should **not** be reused verbatim. Reviewers who saw it in February
must perceive movement, and the title is where they perceive it first.

### Author block

```
P-14
One Scene, Every Scale — OpenUSD as the Shared Data Format for Bio-Digital Twins

○ Jacopin Eliott¹˒²,  Wu Yichao¹˒³,  Shinobu Ai¹˒³

1  Premium Research Institute for Human Metaverse Medicine (WPI-PRIMe), The University of Osaka, Japan
2  RIKEN, Center for Biosystems Dynamics Research, Japan
3  RIKEN, Center for Computational Science, Japan
```

**Note the affiliation change:** the current template writes **"The University of
Osaka"**. February's poster wrote "Osaka University". Use the new form.

---

## 4. Space allocation — A0 portrait, 841 × 1189 mm

The 200 mm white band is fixed. The remaining 841 × 989 mm splits into four bands.
Percentages are of the free area, and they encode the priority order: the case study
and the mechanism get two thirds of the board between them.

```
┌───────────────────────────────────────────────────────────┐
│ HEADER — 841 × 200 mm — WHITE ONLY                        │
│ P-14 · logos · title · authors · affiliations             │
├───────────────────────────────────────────────────────────┤
│ A. THE PROBLEM                          841 × 190 mm (19%)│
│ one sentence + FIGURE 1 (heterogeneity)                   │
├───────────────────────────────────────────────────────────┤
│ B. THE MECHANISM                        841 × 320 mm (32%)│
│ FIGURE 2 — HERO — the composed stage                      │
├───────────────────────────────────────────────────────────┤
│ C. THE CASE STUDY                       841 × 320 mm (32%)│
│ FIGURE 3 — HERO — p53–MDM2, four hops, one number moving  │
├───────────────────────────────────────────────────────────┤
│ D. STATUS, HONESTY, WHAT IT GIVES PRIMe 841 × 159 mm (16%)│
│ three short columns + QR                                  │
└───────────────────────────────────────────────────────────┘
```

**Reading path if the reviewer gives it eight seconds:** title → Figure 3's arrow and
its two numbers → the one-line D-column headline. Those three must work alone.

---

## 5. Panel content — text as it should appear

Word counts are ceilings. Body text at A0 should not go below ~28 pt; if a panel
will not fit, cut content rather than shrink type.

### Band A — The problem  *(≤ 55 words of body text)*

**Heading:** `Five labs. Five file formats. One patient.`

**Body:**

> A bio-digital twin has to hold molecular simulation, imaging, omics, and clinical
> measurement at once. Today each field stores its results in a format only its own
> tools read, so integration means writing a converter for every pair — and rewriting
> them all whenever one lab changes anything.

**Caption for Figure 1:**

> The cost of integration grows with the *square* of the number of data sources.
> Ten labs is forty-five converters to write and maintain.

### Band B — The mechanism  *(≤ 70 words of body text)*

**Heading:** `Film pipelines solved this. We adapted their solution to biology.`

**Body:**

> OpenUSD is the open standard that lets hundreds of artists edit one virtual scene
> at once without overwriting each other. Each contributor authors an independent
> **layer**; the composition engine resolves them into a single scene on read.
> We map the departments of a research project onto that same mechanism, and add a
> biology vocabulary — elements, residues, molecules, simulation parameters — so
> biological data is a first-class citizen rather than an attachment.

**Caption for Figure 2:**

> Five independent layers, five different owners, one composed stage. Replacing the
> analysis layer does not touch the structure below it — verified, not assumed: the
> structure layer opened alone carries none of the annotations added above it.

**Technical strip** — one line each, small type, bottom edge of band B. This is the
only place composition vocabulary appears:

> `Inherits` — atoms inherit mass, radius and colour from shared element templates ·
> `VariantSets` — competing hypotheses coexist in one file and are switched, not copied ·
> `SubLayers` — one layer per research department ·
> `Value Clips` — MD trajectories stream frame-by-frame on demand ·
> `References` — standard assets reused across projects

### Band C — The case study  *(≤ 80 words of body text)*

**Heading:** `One mutation, traced from atom to cell decision.`

**Body:**

> p53 is mutated in roughly half of all human cancers, and MDM2 is the protein that
> switches it off. We take the crystal structure of the two bound together, mutate
> single amino acids at the contact, and ask a protein-stability predictor how much
> each mutation weakens the grip. That number enters the file, drives a Boolean model
> of the p53 regulatory network, and the simulated result returns to the same file.
> Four independent tools, one representation, no format conversion written by hand.

**Caption for Figure 3:**

> Weakening the p53–MDM2 grip should leave more p53 active, and it does — monotonically,
> across every mutation tested. The ordering is fixed by the input energies alone, so a
> mistake at any of the four stages would break it. Real predictions, a real network
> simulation, and a result that could have come out wrong.

**The numbers strip** *(large type — this is what a passing reviewer reads)*:

| Mutation at the contact | Binding weakened by | p53 left active |
|:--|--:|--:|
| none (wild type) | — | **31 %** |
| L26A | 2.9 kcal/mol | 33 % |
| F19A | 3.9 kcal/mol | 40 % |
| W23A | **6.2 kcal/mol** | **86 %** |

### Band D — Three short columns  *(≤ 40 words each)*

**D1 — What this gives PRIMe**

> Any lab in the center can contribute to a shared twin using the file formats it
> already has. Contributions compose instead of colliding, every layer keeps its
> provenance, and the whole assembly opens in standard, freely available viewers.

**D2 — Where it stands** *(the honesty ledger — see §7)*

> Working today: structure, simulation setup, mutation energetics, network simulation,
> and their integration — 39 automated checks assert every artifact against the source
> data. Molecular dynamics streams into the same representation, demonstrated on ABL
> kinase trajectories from Shinobu Lab.

**D3 — Next**

> A GROMACS container is delivered and running on the center's H100 hardware; the
> p53–MDM2 simulation decks come next. Beyond the prototype, the goal is a formal
> OpenUSD schema for biology — the equivalent of the physics standard the format
> already carries.

**QR codes:** repository, and the OpenUSD standard (`https://openusd.org`). Two only.

---

## 6. Figure content briefs

Content only. Composition, palette, and typography are the design system's call.

### FIGURE 1 — The integration problem *(band A, ~55 % of band width)*

**Must show.** Five source labels arranged around a centre: *molecular simulation
(.xtc / .pdb)*, *microscopy (.tif)*, *omics (.csv)*, *clinical records*, *network
models (.bnd / .cfg)*. Between every pair, a connector — the point is the visual
density of the mesh, not any individual line.

**Reader must conclude in three seconds.** "That is far too many connections."

**Must not.** Name a specific lab or person. Show OpenUSD — it does not appear until
band B. Use more than five sources; the mesh stops reading as a mesh past about six.

**Available asset.** February's poster carried hand-drawn file icons
(`atomfile.svg`, `chemfile.svg`, `omicsfile.svg`, `processfile.svg`) in
`~/Documents/career/Events/WPI-PRIMe_4th_Symposium_20260207/`. Reusing them buys
visual continuity with February at zero cost.

### FIGURE 2 — HERO — The composed stage *(band B, full width)*

**Must show.** Five labelled layers as separated planes, stacked, resolving into one
scene on the right. Layers, weakest to strongest: **Biology** (structure, atoms,
bonds) → **Protocol** (simulation setup) → **Perturbation** (the mutations) →
**Analysis** (simulation results) → **Review** (annotation). Each layer carries a
small owner tag — "structural biology", "simulation", "systems biology", "analysis",
"PI" — because the departmental separation is the claim.

**Reader must conclude.** "Different people own different layers, and the layers add
up without touching each other."

**Must show one concrete detail, or the figure is an abstraction.** The composed
scene on the right must be a recognisable p53–MDM2 complex, rendered from the
project's own USD artifact, not stock molecular art. Source:
`examples/p53_mdm2/demos/p53_mdm2_integrated.usda`, rendered with `usdrecord`.

**Must not.** Label the layers with USD API terms. Show more than five layers.
Include an arrow implying a one-directional pipeline — composition is not a pipeline,
and Figure 3 is where directional flow belongs.

**Honesty constraint.** The Review layer is **specified but not yet authored**. Show
it dimmer than the other four, or omit it and describe four. Do not draw it as
delivered.

### FIGURE 3 — HERO — Atom to cell decision *(band C, full width)*

**Must show.** A left-to-right chain of four stages, each with its real tool named
beneath it:

1. **Structure** — the p53 peptide held in the MDM2 groove, with the three contact
   residues (Phe19, Trp23, Leu26) marked. *Source: crystal structure 1YCR.*
2. **Mutate** — one residue replaced by alanine; the resulting binding-energy change.
   *Tool: DDMut-PPI.*
3. **Translate** — that energy converted into the strength of one interaction in the
   regulatory network.
4. **Simulate** — p53 activity over time, as a curve. *Tool: MaBoSS 2.6.6.*

**The one thing the figure exists to show.** Two curves overlaid at stage 4 — wild
type sitting low, W23A sitting high — with the two percentages called out large:
**31 % → 86 %**. If a reviewer looks at nothing else on the board, this is what they
see.

**Reader must conclude.** "The molecular change produced the cellular change, and the
direction is right."

**Must not.** Show all four variants' curves — two is the contrast, four is a data
dump. Show the logistic equation (its constants are placeholders; see §7). Present
this as a discovery about p53 biology. It is a demonstration that the representation
carries meaning across scales, and the caption must keep that distinction.

**Data source.** Curves are real output. `analysis/p53_mdm2_analysis.usda` carries
`bio:maboss:prob:<node>` time-sampled over 500 frames; regenerate with
`demos/run_end_to_end.py`.

### Optional — trajectory still *(only if band B has room)*

A frame from the ABL kinase trajectory animating in `usdview` via Value Clips
(`foundation_demo_v8/output/trajectory_demo.usda`), captioned: *"MD trajectories
stream frame-by-frame into the same representation — ABL kinase, Shinobu Lab data."*
This is the evidence that the format handles time-varying data at scale, and it is
data contributed by two of the three co-authors. Cut it first if space runs short.

---

## 7. Honesty ledger

The poster claims exactly this much, and no more. Each row states what a reviewer who
asks the obvious follow-up question must be told.

| On the poster | Actual status | If asked |
|:--|:--|:--|
| Four pipelines integrated, one file | **Measured.** Committed `.usda` artifacts, 39 read-back checks, each hop asserted against an independent oracle | Runs from a clean checkout |
| ΔΔG values | **Real** DDMut-PPI predictions, response bodies committed verbatim | Predicted, not experimentally measured |
| p53 activity curves | **Real** MaBoSS 2.6.6 run, fixed seed, 50 000 samples | Deterministic and re-runnable |
| Monotone ordering | **Measured**, asserted against three independent read-outs | The claim the demo exists to make |
| ΔΔG → network-strength conversion | **Placeholder shape.** Monotone and invertible, which is all the mechanism needs; its two constants are not fitted to data | Say so plainly. The point is that the *plumbing* carries meaning across scales, not that the conversion is calibrated |
| MD trajectories in USD | **Real**, on ABL kinase (Shinobu Lab) | No p53–MDM2 trajectory exists yet, on any machine |
| GROMACS on center hardware | **Real.** Container delivered, executed on a banyan H100, GPU-resident | The p53–MDM2 simulation decks are not built |
| Review layer | **Not authored** | Specified in the design document; not yet built |

**The rule for tomorrow's authoring:** if a caption cannot be defended when a reviewer
asks "how do you know?", cut the caption rather than soften it. This audience contains
people who ask.

---

## 8. What tomorrow needs

Ordered by risk. Items 1–3 are the ones that can fail.

1. **Render Figure 2's composed structure and Figure 3's curves from the real
   artifacts.** Needs the forOUSD environment and `usdrecord`. This is the only step
   with a technical dependency, so do it first:
   ```bash
   . ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" ~/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/demos/run_end_to_end.py
   ```
2. **Confirm with the organizers whether a flash talk slide is required.** The
   template does not mention one; February's did.
3. **Confirm poster orientation** if there is any contact at the planning office —
   portrait is the February precedent, but the template's stated dimension order is
   landscape.
4. Title selected from §3.
5. Panel text finalized against §5 and the honesty ledger.
6. PPTX and PDF exported, both named to the February convention:
   `P14-Eliott_Jacopin-Poster-WPI-PRIMe_Site_Visit_20260903.{pdf,pptx}`
7. Sent to `planning@prime.osaka-u.ac.jp`.

---

## 9. Sources

- Template and poster-number list: `~/Documents/career/Events/PRIMe_site_visit_20260903/Poster_template_site_visit_2026.pdf`
- February precedent: `~/Documents/career/Events/WPI-PRIMe_4th_Symposium_20260207/`
- Case-study results, LIVERPS mapping, testing discipline: `examples/p53_mdm2/README.md`
- Architecture and departmental layering: `__design__/openusd_for_research_architecture.md`
- Container status and the MD gate: `examples/p53_mdm2/cluster/README.md` (gated step 4)
- Trajectory streaming: `examples/foundation_demo_v8/README.md`
