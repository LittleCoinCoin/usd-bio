# PRIMe Site-Visit Poster — Content Specification (v3, impact pass)

**Event:** WPI-PRIMe site visit, 2026-09-03 · **Poster number:** P-14
**Submission:** PDF **and** PPTX to `planning@prime.osaka-u.ac.jp` by **2026-08-21**
**Layout:** adapted portrait Morrison "Better Poster" — claim bar / center / card band
**Status:** v3. Spends the vividness budget v2 left unspent, and corrects one accuracy
defect v2 introduced. Every number below verified against the artifacts this session
(§10). Content only; visual execution belongs to the Claude Design system.

**Title (fixed by PI):**

> **USD Bio: OpenUSD derived schema as the shared data format for bio-digital twins**

**Conventions.** US spelling (`-ize`, `center`). One term per concept: **bio-digital
twin** never shortens to "twin"; **OpenUSD** is named, never called "the format" on
first use in a block.

---

## 1. What changed from v2, and why

v2's register review recorded the card band as "deliberately flat" and called it a
choice. That entry was wrong, and while it stood it would have protected the flatness
through every future pass. The register rules are explicit that an unspent vividness
budget is a failure reported the same way as an over-spent one. This version spends it.

**Where the budget was actually sitting.** Not in adjectives — in numbers the
repository already holds and the poster was not using:

| Fact | Verified value | Exposure to the honesty ledger |
|:--|:--|:--|
| The size of the edit | Tryptophan 23 carries **14** atoms; the W23A geometry carries **5**. Nine atoms, out of 818 in the structure | **None.** Two integers in two committed files |
| The published model is untouched | All four `.bnd` files, reference and three mutants, share MD5 `33ab9a84…`. The `.cfg` differs by **exactly two lines** | **None.** Reproducible with `diff` in front of the reviewer |
| Composition costs almost nothing | The composed file is **82 lines**; the four layers beneath it total **119,123** | **None.** `wc -l` |

**One accuracy defect corrected.** v2 wrote "cell-fate decision" in the figure title and
in an alternate claim. The five-node p53/Mdm2 oscillator outputs `P(p53 up)`; it does not
emit a fate. Every occurrence is now **"p53 response"** or **"the p53 damage-response
network"**. This was the single most likely specialist objection on the board and it cost
nothing to remove.

**One thing deliberately *not* changed.** The super claim stays a platform claim. An
advisory pass proposed moving "nine atoms" up into the claim bar; that would revert the
poster to the result-led framing rejected at the start of this work, where the PI's
contribution to the center is software infrastructure and p53–MDM2 is the case study. The
nine atoms become the center figure's dominant number instead, which is where they do
their work without displacing the framing.

---

## 2. The occasion

The audience is a JSPS review delegation and senior center staff, assessing whether
PRIMe is delivering on its assigned mission: human bio-digital twins for multi-scale,
model-driven research into disease and diagnosis. Many will pass the board mid-conversation
rather than stop.

1. **The claim bar must land without the poster being read.** Everything below is for the
   minority who stop; the card band is for the smaller minority who talk to you.
2. **The contribution is platform, not biology.** p53–MDM2 proves the infrastructure
   works; it is never the subject.
3. **Formal, and allowed to shine.** The impact here comes from true magnitudes placed
   where they land, never from evaluative language. A JSPS delegation must not read this
   as a sales pitch, and nothing in §4–§6 is an adjective doing a number's job.

### The alignment worth exploiting

The institute is the Premium Research Institute for **Human Metaverse Medicine**. OpenUSD
is the data standard the metaverse industry converged on, and it is what Pixar, NVIDIA,
Apple and the Alliance for OpenUSD build on. This poster is not adjacent to the
institute's name; it is the institute's name, implemented. Free, true, and it belongs in
the claim bar's supporting line.

### Hard format constraints

| Constraint | Value |
|:--|:--|
| Size | A0 portrait, 841 × 1189 mm. February's poster was portrait under identical template wording and was accepted |
| Top band | **200 mm, white background, black text only** |
| Band contents | P-number, title, authors (○ marks presenter), affiliations, logos |
| Language | English · **Deliverables** PDF **and** PPTX |

**Still to confirm with the organizers:** February's template asked for "poster **and
flash talk slide**". This one never mentions a flash talk.

---

## 3. The super claim

**Recommended, unchanged from v2:**

> ## Every lab keeps its own tools and file formats. Their results still compose into one bio-digital twin.

**Supporting line:**

> *We adopted OpenUSD, the data standard the metaverse industry converged on, and extended it for biology.*

**Alternates:**

- **Result-led** — *A nine-atom edit to a protein structure reaches a cell-level p53 response, and every step in between is stored in one composed file.*
  Now much stronger than v2's version, because "nine atoms" is verifiable and vivid at
  once. Take it only if you want to be read as the p53 person rather than the platform
  person.
- **Problem-led** — *Integrating ten labs' data should not take forty-five converters. It takes one shared format.*

**Rejected form.** A bar that states a topic instead of a finding. Morrison's structure
fails outright when the bar is a topic, and a delegation reading a topic learns nothing
about whether the center is delivering.

### Author block (header band, white only)

```
P-14
USD Bio: OpenUSD derived schema as the shared data format for bio-digital twins

○ Jacopin Eliott¹˒²,  Wu Yichao¹˒³,  Shinobu Ai¹˒³

1  Premium Research Institute for Human Metaverse Medicine (WPI-PRIMe), The University of Osaka, Japan
2  RIKEN, Center for Biosystems Dynamics Research, Japan
3  RIKEN, Center for Computational Science, Japan
```

Note the affiliation change: **"The University of Osaka"**, not February's "Osaka University".

---

## 4. Space allocation — A0 portrait, 841 × 1189 mm

```
┌───────────────────────────────────────────────────────────┐
│ HEADER — 841 × 200 mm — WHITE ONLY                        │
├───────────────────────────────────────────────────────────┤
│ SUPER CLAIM — 841 × 170 mm                                │
├───────────────────────────────────────────────────────────┤
│ CENTER — 841 × 500 mm                                     │
│ FIGURE 1 — the whole argument, one image                  │
├───────────────────────────────────────────────────────────┤
│ CARD BAND — 841 × 319 mm — 5 across × 2 down = 10 slots   │
│ 8 cards + the diff panel occupying 2 slots (bottom right) │
└───────────────────────────────────────────────────────────┘
```

**Eight-second reading path:** claim bar → the center figure's two magnitudes → done.

---

## 5. The center — Figure 1

**"Nine atoms, and everything that follows"**

### Left third — contribution

Four labeled layers as separated planes, each with an owner tag:

| Layer | Owner tag | Carries |
|:--|:--|:--|
| Biology | structural biology | structure, atoms, bonds |
| Protocol | simulation | simulation setup parameters |
| Perturbation | systems biology | the mutations under test |
| Analysis | analysis | simulation results over time |

**Live text at the point where the planes converge — this is new in v3:**

> **82 lines** — the composed file, carrying no data of its own
> **119,123 lines** — in the four layers it composes

**Caption, which must be present or the number reads as "there is not much here":**
> Those 82 lines are a list of the four layers, four items of stage metadata, one
> hypothesis selection, and the cross-pipeline join. Opened alone, the structure layer
> carries none of the annotations the layers above it added.

### Center third — composition

The planes resolving into one scene: a recognizable p53–MDM2 complex with the three
contact residues marked. Visual grammar is **resolution, not pipeline** — layers
converging on one object, not a conveyor belt.

### Right third — the payoff

**The dominant callout, replacing v2's percentage pair in that role:**

> ### 9 atoms
> *removed from tryptophan 23 — the only edit made by hand*
> ### ↓
> ### 500 frames
> *of p53 damage-response network activity*

Beneath it, the two probability curves, with `31 %` and `86 %` as **curve labels** rather
than as the headline. The demotion is deliberate and it is an honesty move: the *ordering*
across mutations is measured and asserted three ways, but the *size of the gap* runs
through a logistic whose two constants the README calls explicitly ad-hoc placeholders.
The ledger protects the ordering, not the magnitude, and v2 was putting the magnitude in
the largest type on the board.

**Caption — the poster's one sentence of rhetorical force, placed at the second and last
stop on the eight-second path:**

> One hypothesis selection is the only thing authored by hand. The geometry it brings in
> has nine of tryptophan 23's fourteen atoms removed, the binding-energy change is
> predicted for that same mutation, and 500 frames of p53 probability come back onto a
> layer that never touches the structure below it.

*Shorter, if the slot is tight:* One hypothesis selection is the only thing authored by
hand; everything after it is computed and written back into the same composed file.

### Two precision constraints — read before drafting any caption

1. **Never say the nine-atom geometry was sent to the predictor.** `converters/ddmut_client.py`
   submits a PDB accession, a chain, and a mutation *string* against deposited 1YCR — not
   the truncated coordinates. The true and stronger statement is that the mutation is
   declared once and both the referenced geometry and the energy query follow from that
   one declaration.
2. **"p53 response", never "cell fate".** See §1.

### Must not

Label anything with USD API vocabulary — that lives in the cards. Draw a fifth (Review)
layer; it is specified but unauthored. Show all four variants' curves — two is a contrast,
four is a data dump. Show the conversion equation; its constants are placeholders.

### Asset generation carve-out

Regenerating diagrammatic elements in Claude Design is right. Three elements must stay
machine-generated: **the molecular structure** (`usdrecord` on
`demos/p53_mdm2_integrated.usda`), **the probability curves** (`analysis/p53_mdm2_analysis.usda`,
`bio:maboss:prob:<node>`, 500 frames), and **the diff panel** (§6.2). A designed-looking
molecule and a smooth designed curve undercut the one claim the figure makes.

---

## 6. Card band — 8 cards plus the diff panel

Five across, two down. Body text ≤ 28 words. Each card carries **at least one number** —
that, not adjectives, is where the band's vividness budget gets spent.

### 6.1 The eight

**1 · What USD Bio adds**
> A biology vocabulary inside OpenUSD: elements, residues, molecules, simulation
> parameters. All 818 atoms inherit mass, radius and color from shared element templates,
> and every value carries its own units and provenance.

**2 · What OpenUSD is**
> The open standard that lets hundreds of artists edit one virtual scene at once without
> overwriting each other. Each contributor authors an independent layer; the composition
> engine resolves them all on read.

**3 · One layer per department**
> Structure, protocol, perturbation, and analysis are separate layers with separate
> owners. The file that composes them is 82 lines and holds no data of its own.

**4 · The case study**
> Crystal structure 1YCR: the p53 peptide held in the MDM2 groove. Nine atoms removed
> from tryptophan 23; the binding-energy change predicted by DDMut-PPI; a Boolean model
> of the p53 network run by MaBoSS 2.6.6.

**5 · How we know it is right**
> Thirty-nine automated checks assert every stored artifact against the source data,
> never against the code that wrote it. One independent method per stage, including
> re-running the simulation from scratch.

**6 · Simulation infrastructure, delivered**
> Trajectories stream frame by frame into the same representation, loaded on demand —
> demonstrated on ABL kinase simulations from Shinobu Lab. The engine that produces them
> runs containerized on the center's H100 hardware, matching its reference build to
> 1.4 parts per million.

**7 · An open standard for biology**
> The goal is a formal OpenUSD schema domain for biology, the counterpart of the physics
> standard the format already carries. Standardized through the Alliance for OpenUSD, it
> would carry the center's name into international infrastructure.

**8 · What the center gets**
> Any PRIMe lab contributes to a shared bio-digital twin using the formats it already
> has. Contributions compose instead of colliding, every layer keeps its provenance, and
> the result opens in the standard, freely available OpenUSD viewers.

**Ordering note.** Card 1 is "What USD Bio adds", not "What OpenUSD is". The band's
most-read slot should carry what the presenter built, not somebody else's technology —
and by the time a reader reaches the cards, OpenUSD has been named twice above.

**Two QR codes** at the band's edge: the repository, and `openusd.org`. Two only.

### 6.2 The diff panel — two slots, bottom right

Machine-generated, monospaced, reproduced as literal terminal output:

```
$ diff maboss/reference/p53_Mdm2_runcfg.cfg maboss/output/p53_Mdm2_W23A.cfg
8c8
< $KMn_pMC=1;
---
> $KMn_pMC=0.0082602991708;
12c12
< $KMn_pMCD=1;
---
> $KMn_pMCD=0.0082602991708;

$ md5 maboss/reference/p53_Mdm2.bnd maboss/output/p53_Mdm2_W23A.bnd
33ab9a84315bcf2d507692ca9a750d7e
33ab9a84315bcf2d507692ca9a750d7e
```

**Caption:**
> The Boolean model is the published one from Institut Curie, fetched verbatim. Our
> pipeline returns it byte-identical — same checksum — and writes the entire molecular
> result into two numbers in its configuration.

**Why this earns two slots.** It is the poster's most memorable element and it makes an
argument no diagram can. To a delegation assessing whether an institute can get
heterogeneous labs to interoperate, *we did not fork their model, we parameterized it* is
the most credible interoperability claim available — demonstrated rather than asserted.
It also answers the question every reviewer has about integration platforms, which is
what adopting one costs the labs already doing the science. Answer: two lines.

**Set it to read at 1 m, not 2 m.** It is a stop-and-look element. Keep the `$` prompts so
it reads as a transcript rather than as a designed panel — it is the one thing on the
board that visibly did not pass through a designer, and that is its whole value.

### 6.3 The visibility swap

You have not cleared a visibility pitch with the center director, so the poster commits
the center to nothing. Card 7 as written states *your* goal and names the consequence
without promising a commitment. Keep it unless you get a green light. If you do, swap
cards 6 and 8 out for:

**7b · Interoperability already in place**
> USD Bio output opens in the same tools that drive industrial digital twins, because the
> underlying standard is theirs. Biological models become directly composable with the
> visualization and simulation software built around it.

**7c · An adoption path for the center**
> The schema is designed to be adopted a layer at a time: a lab contributes one layer in
> its own format and gains from every other layer already present. No lab changes tools
> to participate.

**Handle with care.** Neither should acquire a date, a named partner, or a deliverable
without the director's agreement — a JSPS delegation treats a poster claim as a
commitment the center has made, and that is not one you can make alone.

---

## 7. Honesty ledger

| On the poster | Actual status | If asked |
|:--|:--|:--|
| Nine atoms removed from tryptophan 23 | **Measured.** `bio:atomCount` 14 → 5 in two committed geometry files | Real 1YCR coordinates, truncated. The files' own doc strings say "no fabricated positions" |
| 82 lines vs 119,123 | **Measured.** `wc -l` this session | Reproducible in front of the reviewer |
| The `.bnd` checksums and the two-line diff | **Measured** this session | Reproducible in front of the reviewer |
| Four pipelines integrated, one file | **Measured.** 39 read-back checks, independent oracle per stage | Runs from a clean checkout |
| Binding-energy changes | **Real** DDMut-PPI predictions, response bodies committed verbatim | Predicted, not experimentally measured. Queried by mutation string against deposited 1YCR |
| p53 activity curves | **Real** MaBoSS 2.6.6 run, fixed seed, 50 000 samples | Deterministic and re-runnable |
| The ordering across mutations | **Measured**, asserted against three independent read-outs | The claim the demonstration makes |
| The *size* of the 31 → 86 gap | **Not protected.** Runs through a logistic whose constants are unfitted placeholders | This is why the percentages are curve labels and not the headline. Say it before being asked if the reviewer is a modeler |
| Trajectories in USD | **Real**, on ABL kinase (Shinobu Lab) | No p53–MDM2 trajectory exists yet, on any machine |
| GROMACS on center hardware | **Real.** Container delivered, executed on a banyan H100, parity 1.39e-06 | A smoke-test system ran. The p53–MDM2 simulation decks are not built |
| Review layer | **Specified, not authored** | Do not draw it in Figure 1, and do not name it in card 3 |

---

## 8. The conversation kit

Three lines, all traceable, in the order to reach for them:

1. *"The only thing edited by hand in that whole result is nine atoms."*
2. *"The published Curie model comes through our pipeline byte-identical. What changed is two numbers in a config file."*
3. *"The file carrying the integrated result is eighty-two lines and contains no data of its own."*

And the one held in reserve, said **before** being asked if the reviewer is a modeler:
*"The energy-to-parameter conversion is monotone and invertible, which is all the
mechanism needs. Its constants are not fitted to anything, so the ordering across the
mutants is the claim, not the size of the gap."* It converts the one soft spot into a
display of calibration.

---

## 9. Tomorrow, ordered by risk

1. **Render the three machine-generated elements** (§5) — the only step with a technical
   dependency:
   ```bash
   . ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" ~/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/demos/run_end_to_end.py
   ```
2. **Ask the organizers about the flash talk slide**, and confirm portrait in the same message.
3. Pick the super claim from §3.
4. Decide the card-7 question.
5. Figure 1 built.
6. Export PDF + PPTX as `P14-Eliott_Jacopin-Poster-WPI-PRIMe_Site_Visit_20260903.{pdf,pptx}`.
7. Send to `planning@prime.osaka-u.ac.jp`.

---

## 10. Verification log

Run this session against the working tree; all values above are from these commands.

| Claim | Command | Result |
|:--|:--|:--|
| 14 → 5 atoms | `grep bio:atomCount composition/geometries/*.usda` | `wildtype_trp_23` 14, `w23a_trp_23` 5 |
| `.bnd` byte-identical | `md5 maboss/reference/*.bnd maboss/output/*.bnd` | `33ab9a84315bcf2d507692ca9a750d7e` × 4 |
| Two-line `.cfg` diff | `diff maboss/reference/p53_Mdm2_runcfg.cfg maboss/output/p53_Mdm2_W23A.cfg` | `8c8` and `12c12`, nothing else |
| 82 vs 119,123 lines | `wc -l` on the root layer and the four sublayers | 82; 108,667 + 10,114 + 189 + 153 = 119,123 |

**One thing checked and rejected.** An advisory pass proposed reproducing the composed
file's `subLayers` block as a second raw-text specimen. The block lists **three**
sublayers, not four — the Biology layer is reached transitively through the genotype
layer, exactly as the README describes. A reviewer counting four departments and finding
three entries gets a question mid-assessment, and two raw-text specimens is one more than
the band can carry. The diff makes the stronger argument; it stays, this does not.

---

## 11. Sources

- Template and poster numbers: `~/Documents/career/Events/PRIMe_site_visit_20260903/Poster_template_site_visit_2026.pdf`
- February precedent: `~/Documents/career/Events/WPI-PRIMe_4th_Symposium_20260207/`
- Results, testing discipline, correlation-constant caveat: `examples/p53_mdm2/README.md`
- Architecture and departmental layering: `__design__/openusd_for_research_architecture.md`
- Container status, and why no p53 trajectory exists: `examples/p53_mdm2/cluster/README.md` (gated step 4)
- Trajectory streaming: `examples/foundation_demo_v8/README.md`
- Illustration assets: [`01-illustration_assets_v1.md`](01-illustration_assets_v1.md)
