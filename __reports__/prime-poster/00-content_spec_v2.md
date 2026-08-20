# PRIMe Site-Visit Poster — Content Specification (v2, register pass applied)

**Event:** WPI-PRIMe site visit, 2026-09-03 · **Poster number:** P-14
**Submission:** PDF **and** PPTX to `planning@prime.osaka-u.ac.jp` by **2026-08-21**
**Layout:** adapted portrait Morrison "Better Poster" — claim bar / center / card band
**Status:** v2. All authored poster text passed against the universal register rules and
the author-level doctrine at `~/.config/writing-prose/`. Findings and trades in §9.
Content only; visual execution belongs to the Claude Design system.

**Title (fixed by PI):**

> **USD Bio: OpenUSD derived schema as the shared data format for bio-digital twins**

**Conventions fixed this round.** US spelling (`-ize`, `center`), matching the
repository corpus. One term per concept: **bio-digital twin** never shortens to "twin";
**layer** is never called a file or a stage; **OpenUSD** is named, never referred to as
"the format" on first use in any block.

---

## 1. The occasion, and what it does to the content

The audience is a JSPS review delegation and senior center staff, assessing whether
PRIMe is delivering on its assigned mission: human bio-digital twins for multi-scale,
model-driven research into disease and diagnosis. They are scientists but not
specialists, and many will pass the board mid-conversation rather than stop to read.

Three consequences:

1. **The claim bar must land without the poster being read.** Morrison's structure
   exists for exactly this audience. Everything below the bar is for the minority who
   stop, and the card band is for the smaller minority who talk to you.
2. **The contribution is platform, not biology.** p53–MDM2 proves the infrastructure
   works; it is never the subject.
3. **Formal, and allowed to shine.** The occasion tolerates a confident claim, not an
   unearned one. Every number below is measured and reproducible from the repository.

### One alignment worth exploiting

The institute is the Premium Research Institute for **Human Metaverse Medicine**.
OpenUSD is the data standard the metaverse industry converged on, and it is what Pixar,
NVIDIA, Apple and the Alliance for OpenUSD build on. This poster is therefore not
adjacent to the institute's name; it is the institute's name, implemented. The argument
is free, it is true, and a JSPS delegation will hear it. It belongs in the claim bar's
supporting line, not buried in a card.

### Hard format constraints (official template)

| Constraint | Value |
|:--|:--|
| Size | A0 portrait, 841 × 1189 mm. Template writes "1189 mm × 841 mm"; February's poster was portrait under identical wording and was accepted |
| Top band | **200 mm, white background, black text only** |
| Band contents | P-number, title, authors (○ marks presenter), affiliations, logos |
| Below band | Free, color permitted |
| Language | English |
| Deliverables | PDF **and** PPTX |

**Still to confirm with the organizers:** February's template asked for "poster **and
flash talk slide**". This one asks only for "both PDF and Power Point files" and never
mentions a flash talk.

---

## 2. The super claim

The bar carries a finding in plain language, sized to be read across a room. It is not
the title, and it uses no word the delegation would have to look up.

**Recommended:**

> ## Every lab keeps its own tools and file formats. Their results still compose into one bio-digital twin.

**Supporting line, one size down, directly beneath:**

> *We adopted OpenUSD, the data standard the metaverse industry converged on, and extended it for biology.*

**Alternates,** if a different emphasis is wanted:

- **Result-led** — *A single mutation travels from atomic structure to a cell-fate decision inside one file.*
  Sharper and more concrete, and it hands you the case study as the opening line of
  every conversation. Weaker on the platform framing you asked to be understood for.
- **Problem-led** — *Integrating ten labs' data should not take forty-five converters. It takes one shared format.*
  The most arresting of the three and the easiest to remember. Riskier: it leads with a
  number about a problem rather than a claim about your delivery.

**Rejected form.** Anything that states a topic instead of a finding — a bar beginning
"Toward" or "A framework for" gives the delegation no information about whether the
center is delivering, and Morrison's structure fails outright when the bar is a topic.

### Author block (header band, white only)

```
P-14
USD Bio: OpenUSD derived schema as the shared data format for bio-digital twins

○ Jacopin Eliott¹˒²,  Wu Yichao¹˒³,  Shinobu Ai¹˒³

1  Premium Research Institute for Human Metaverse Medicine (WPI-PRIMe), The University of Osaka, Japan
2  RIKEN, Center for Biosystems Dynamics Research, Japan
3  RIKEN, Center for Computational Science, Japan
```

**Affiliation change:** the current template writes **"The University of Osaka"**.
February wrote "Osaka University". Use the new form.

---

## 3. Space allocation — A0 portrait, 841 × 1189 mm

```
┌───────────────────────────────────────────────────────────┐
│ HEADER — 841 × 200 mm — WHITE ONLY                        │
│ P-14 · logos · title · authors · affiliations             │
├───────────────────────────────────────────────────────────┤
│ SUPER CLAIM — 841 × 170 mm                                │
│ the finding, huge · supporting line, one size down        │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ CENTER — 841 × 500 mm                                     │
│ FIGURE 1 — the whole argument, one image                  │
│ (2-column fallback in §4.2)                               │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ CARD BAND — 841 × 319 mm                                  │
│ 8 cards, 4 across × 2 down, ~200 × 150 mm each            │
└───────────────────────────────────────────────────────────┘
```

**Eight-second reading path:** claim bar → the two numbers in the center figure → done.
The cards are never part of that path; they exist so that when someone does stop, you
have something to point at for four minutes.

---

## 4. The center

### 4.1 Recommended — one figure, one argument

Morrison's center is one dominant visual, and this poster has an argument that can be
told as one: independent layers compose into a single scene, and something real travels
across the scales as a result. Splitting that into two columns splits the argument.

**FIGURE 1 — "Atom to cell decision, through one composed file"**

**Left third — contribution.** Four labeled layers drawn as separated planes, each with
an owner tag, because departmental separation is the claim:

| Layer | Owner tag | Carries |
|:--|:--|:--|
| Biology | structural biology | structure, atoms, bonds |
| Protocol | simulation | simulation setup parameters |
| Perturbation | systems biology | the mutations under test |
| Analysis | analysis | simulation results over time |

**Center third — composition.** The planes resolving into one scene: a recognizable
p53–MDM2 complex with the three contact residues marked. The visual grammar must be
resolution rather than pipeline — layers converging on one object, not a conveyor belt.

**Right third — the payoff.** Two probability curves overlaid, wild type low and W23A
high, with the callout large enough to read from the claim bar's distance:

> ### 31 % → 86 %
> *p53 left active, wild type versus the W23A mutation*

**The single thing this figure exists to do.** Make a reviewer who reads nothing else
understand that a molecular change produced a cellular change, through one file, in the
right direction.

**Must not.** Label anything with USD API vocabulary — that lives in the cards. Draw a
fifth (Review) layer; it is specified but unauthored, and drawing it would be a false
claim. Show all four variants' curves — two is a contrast, four is a data dump. Show the
conversion equation; its constants are placeholders (§6).

### 4.2 Fallback — two columns

Use only if Figure 1 becomes too dense to read at 2 m.

| | Left column (≈ 45 %) | Right column (≈ 55 %) |
|:--|:--|:--|
| **Heading** | How independent work composes | What traveled across the scales |
| **Content** | The four-layer stack resolving into one p53–MDM2 scene | The four-stage chain: structure → mutate → translate → simulate, ending in the two curves |
| **Caption** | Four layers with four owners resolve into one scene. Opened on its own, the structure layer carries none of the annotations the layers above it added. | Weakening the p53–MDM2 grip leaves more p53 active, and the more it is weakened the more p53 stays active. The ordering is fixed by the input energies alone, so an error at any stage would break it. |

The right column keeps the `31 % → 86 %` callout. Reading order is deliberate:
mechanism, then proof.

### 4.3 Asset generation — one carve-out worth making

Regenerating the diagrammatic elements in Claude Design is right, and they become a
reusable set. Two elements should **not** be redrawn, and this is a substantive point
rather than a production convenience:

- **The molecular structure** must be rendered from the project's own USD artifact
  (`examples/p53_mdm2/demos/p53_mdm2_integrated.usda`, via `usdrecord`).
- **The probability curves** must be plotted from the real run
  (`analysis/p53_mdm2_analysis.usda`, `bio:maboss:prob:<node>`, 500 frames).

A designed-looking molecule and a designed-looking curve undercut the one claim the
figure is making, that this is real output from a working system. Reviewers at this
level can tell the difference, and a stylized curve invites the question you least want.
Render them, then let the design system place and style everything around them.

---

## 5. Card band — 8 cards

Each card: a heading a passer-by can scan, and ≤ 35 words of body. These are your
conversation handles; you are the one who expands them.

Cards 1–5 are the methodological spine and should stay. Cards 6–8 are the swappable set,
and §5.2 gives the swaps.

### 5.1 The eight

**1 · What OpenUSD is**
> The open standard that lets hundreds of artists edit one virtual scene at once without
> overwriting each other. Each contributor authors an independent layer, and the
> composition engine resolves them all on read.

**2 · What USD Bio adds**
> A biology vocabulary inside that standard: elements, residues, molecules, simulation
> parameters. Biological data then carries its own units and provenance instead of
> riding along as an attachment to something else.

**3 · One layer per department**
> Structure, protocol, perturbation, and analysis are separate layers with separate
> owners. Each is edited, versioned, and loaded on its own. Opened alone, the structure
> layer carries none of the annotations the layers above it added.

**4 · The case study**
> Crystal structure 1YCR: the p53 peptide held in the MDM2 groove. We mutate single
> contact residues, take the binding-energy change from DDMut-PPI, and use it to drive a
> Boolean model of the p53 network, simulated by MaBoSS 2.6.6.

**5 · How we know it is right**
> Thirty-nine automated checks assert every stored artifact against the source data,
> never against the code that wrote it. Each stage is checked by an independent method,
> including re-running the simulation from scratch.

**6 · Molecular dynamics**
> Trajectories stream frame by frame into the same representation, loaded on demand
> rather than held in memory, and demonstrated on ABL kinase simulations from Shinobu
> Lab. The simulation engine that produces them runs containerized on the center's H100
> hardware.

**7 · An open standard for biology**
> The goal is a formal OpenUSD schema domain for biology, the counterpart of the physics
> standard the format already carries. Standardized through the Alliance for OpenUSD, it
> would carry the center's name into international infrastructure.

**8 · What the center gets**
> Any PRIMe lab contributes to a shared bio-digital twin using the formats it already
> has. Contributions compose instead of colliding, every layer keeps its provenance, and
> the result opens in the standard, freely available OpenUSD viewers.

**Plus, occupying no card:** two QR codes at the band's edge — the repository and
`openusd.org`. Two only.

### 5.2 The visibility swap

You have not cleared a visibility pitch with the center director, so the poster must not
commit the center to anything. Card 7 as written above is the safe version: it states
your goal and names the consequence for the center without promising a commitment. Keep
it unless you get a green light.

If you do speak to the director and want more visibility content, swap cards **6 and 8**
out and these in — that takes the band from one visibility card to three, which is the
most this poster can carry before it stops being about the work:

**7b · Interoperability already in place**
> USD Bio output opens in the same tools that drive industrial digital twins, because
> the underlying standard is theirs. Biological models become directly composable with
> the visualization and simulation software built around it.

**7c · An adoption path for the center**
> The schema is designed to be adopted a layer at a time: a lab contributes one layer in
> its own format and gains from every other layer already present. No lab has to change
> tools to participate.

**Handle with care.** Both are true and both are forward-looking. Neither should acquire
a date, a named partner, or a deliverable on this poster without the director's
agreement — a JSPS delegation treats a poster claim as a commitment the center has made,
and that is not a commitment you can make alone. If in doubt, ship the safe set.

---

## 6. Honesty ledger

What the poster claims, and what you say when someone asks the obvious question.

| On the poster | Actual status | If asked |
|:--|:--|:--|
| Four pipelines integrated, one file | **Measured.** Committed artifacts, 39 read-back checks, independent oracle per stage | Runs from a clean checkout |
| Binding-energy changes | **Real** DDMut-PPI predictions, response bodies committed verbatim | Predicted, not experimentally measured |
| p53 activity curves | **Real** MaBoSS 2.6.6 run, fixed seed, 50 000 samples | Deterministic and re-runnable |
| The ordering across mutations | **Measured**, asserted against three independent read-outs | The claim the demonstration exists to make |
| Energy → network-strength conversion | **Placeholder shape.** Monotone and invertible, which is all the mechanism needs; its constants are not fitted | Say so plainly. The point is that the representation carries meaning across scales, not that the conversion is calibrated |
| Molecular dynamics trajectories in USD | **Real**, on ABL kinase (Shinobu Lab) | No p53–MDM2 trajectory exists yet, on any machine |
| GROMACS on center hardware | **Real.** Container delivered, executed on a banyan H100, GPU-resident | The p53–MDM2 simulation decks are not built |
| Review layer | **Specified, not authored** | Named in the design document; not yet built. Do not draw it in Figure 1, and do not name it in card 3 |

**Rule for authoring:** if a caption cannot survive "how do you know?", cut it rather
than soften it. This delegation contains people who ask.

---

## 7. Tomorrow, ordered by risk

1. **Render the two real elements** (§4.3) — the only step with a technical dependency,
   so it goes first:
   ```bash
   . ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" ~/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/demos/run_end_to_end.py
   ```
2. **Ask the organizers about the flash talk slide**, and confirm portrait in the same
   message.
3. Pick the super claim from §2, and settle the two open trades in §9.2.
4. Decide the card-7 question — safe version, or the visibility swap after speaking to
   the director.
5. Center figure built; fall back to two columns only if it will not read at 2 m.
6. Export PDF + PPTX as
   `P14-Eliott_Jacopin-Poster-WPI-PRIMe_Site_Visit_20260903.{pdf,pptx}`.
7. Send to `planning@prime.osaka-u.ac.jp`.

---

## 8. Sources

- Template and poster numbers: `~/Documents/career/Events/PRIMe_site_visit_20260903/Poster_template_site_visit_2026.pdf`
- February precedent: `~/Documents/career/Events/WPI-PRIMe_4th_Symposium_20260207/`
- Case-study results, testing discipline: `examples/p53_mdm2/README.md`
- Architecture and departmental layering: `__design__/openusd_for_research_architecture.md`
- Container status, and why no p53 trajectory exists: `examples/p53_mdm2/cluster/README.md` (gated step 4)
- Trajectory streaming: `examples/foundation_demo_v8/README.md`

---

## 9. Register pass — findings and trades

Universal rules from `~/.claude/skills/writing-prose/references/register.md`;
author-level doctrine from `~/.config/writing-prose/`. No project canon exists at
`__canons__/prose_writing/` in this repository; the pass ran on author-level defaults.
Setting up a project canon is worth a separate session, not this one.

### 9.1 Corrections applied

| # | Rule | Where | Was → is |
|:--|:--|:--|:--|
| 1 | **Accuracy scoping** (non-negotiable) | Card 3 | Named five layers including *review*, which contradicts the honesty ledger and §4.1's instruction not to draw it. Now names the four that exist |
| 2 | Generic description of a named thing (`llm-stench-lexicon`) | Supporting line | "the data standard the metaverse industry already runs on" described OpenUSD without naming it. Now names it |
| 3 | Defensive framing | Fallback caption | "verified, not assumed" defended against an objection nobody on the page had made. Replaced with the evidence stated positively |
| 4 | Fragments for punch | Card 4, result-led alternate | "Simulated by MaBoSS 2.6.6." folded into its sentence; the alternate claim given a main verb |
| 5 | Marketing lexicon | Cards 2, 6, 7b | "first-class citizen", "at scale", "ecosystem" replaced with plain equivalents |
| 6 | One term per concept | Card 8 | "a shared twin" → "a shared bio-digital twin" |
| 7 | Causal locality | Card 6 | The H100 sentence had no link to the two before it. Now attached through the simulation engine that produces the trajectories |
| 8 | Ascending triples | Fallback caption | "Four layers, four owners, one composed scene" was a three-beat carrying rhetoric the content did not need |
| 9 | Jargon before plain language (`jargon-glossary-lever`) | Fallback caption | "monotonically" → "the more it is weakened the more p53 stays active" |
| 10 | Internal consistency | Card 7 heading | "Toward an open standard" used the exact form §2 rejects for the claim bar |
| 11 | Accuracy scoping | Card 8 | "opens in free, standard viewers on any machine" overclaimed. Now "the standard, freely available OpenUSD viewers" |
| 12 | Mechanics — one spelling convention | Throughout | "standardised"/"centre" mixed with "-ize"/"center". Fixed to US, matching the repository corpus |
| 13 | Punctuation as a crutch | Cards 1, 2 | Two semicolon and colon joints spent on ordinary conjunction; one colon kept in card 4 where it introduces a genuine list |

### 9.2 Two trades that are yours, not mine

**T-1 — the em dash in the super claim.** v1 read *"Every lab keeps its own tools and
file formats — and their results still compose into one bio-digital twin."* v2 splits it
into two sentences. The em dash is the more vivid rendering and the tie-break rule says
to keep vivid phrasing and flag it, so this is not an automatic call. I split it on
evidence rather than preference: you stripped em-dash joints out of the KAKENHI
abstracts during the restyle round, which reads as a standing dislike. **Say the word and
the dash goes back** — at claim-bar size it gives the sentence a beat the full stop does
not.

**T-2 — "compose instead of colliding" (card 8).** Alliterative, and the contrast is
real. It is the only vivid move in the entire card band, which is why I kept it: the
band is otherwise deliberately flat, and one charged phrase at the end of it is the
budget being spent where it lands rather than left unspent. If it reads as too pleased
with itself for a JSPS board, "compose rather than collide" or plain "compose without
overwriting each other" both work.

### 9.3 Both poles, reported

**Over-spent: clean.** No section carries inflated rhetoric. The claim bar is the one
place a vivid move is mandatory and it spends exactly one, on the contrast that is the
content.

**Under-spent: two places, deliberately.** The card band runs flat by design — it is
reference material read at arm's length, and charge there competes with the claim bar.
Recording it as a deliberate choice rather than an oversight, per the rule that unspent
budget is a defect unless it is named. The honesty ledger is also flat, and should stay
that way; it is the document's most load-bearing content and reads best plain.

### 9.4 Not applied, and why

The spec's own commentary — this section, §1's reasoning, the "must not" lists — is a
working document rather than signed prose, and it is written to be argued with. It
follows the mechanics rules (one term per concept, one spelling convention, abbreviations
expanded) but not the vividness budget, which governs what goes on the poster.
