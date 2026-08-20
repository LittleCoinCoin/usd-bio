# USD Bio — Hand-Drawn Illustration Asset Library (v1)

**Purpose.** The drawn assets for the PRIMe site-visit poster (P-14), specified so the
Claude Design system can produce them as a coherent, reusable set. Content spec:
[`00-content_spec_v3.md`](00-content_spec_v3.md).

**Changes from v0**, all driven by the v3 impact pass:

1. **A18 promoted out of Tier 3 to second in the production order**, and redesigned. It
   now carries the poster's dominant magnitude claim rather than illustrating a step.
2. **The accent color is narrowed to one meaning** across the entire poster. v0 spread it
   across three unrelated ones, which its own §7 rule prohibits.
3. **A05 redrawn.** It depicted a person reading a plotted curve, twenty centimeters from
   the real plotted curve.
4. **A13 rescoped** — the card it serves is now about delivered simulation infrastructure,
   not trajectories alone.

---

## 1. The house register

**Technical ink-line drawing.** One ink weight family, drawn as an engineer's or a
naturalist's hand would draw it — confident single-stroke contours, sparse hatching for
volume, no fills except the accent.

- It is **serious**. A JSPS delegation reads ink-line technical drawing as competence.
  Cartoon vignettes read as a school project.
- It **survives A0** without the muddiness flat-fill illustration develops at two meters.
- It **cannot be mistaken for the evidence.** The poster now carries three
  machine-generated elements — the molecular render, the probability curves, and the diff
  panel. Drawn assets in a visibly different medium keep that boundary readable without a
  word of explanation.

**Subject-matter through-line.** OpenUSD's layers descend from film compositing, where
independently drawn transparent sheets stack and resolve into one frame. That is where the
technology comes from, not a metaphor invented to explain it, so drawing layers as
physical registered sheets on a light table is accurate. It lands the "film pipelines
already solved this" argument without spending a word. Keep it as subject matter, in the
shared ink register — never as a separate whimsical style.

**Alternate register**, if ink-line reads too industrial for a biology institute:
scientific-plate drawing, the Cajal or Haeckel lineage — finer line, more hatching, more
organic contour. Equally serious, biology-native, slightly warmer. Pick one; they do not mix.

### The accent rule — changed in v1, and this is the highest-return item here

**The accent color marks the nine atoms and their consequence. Nothing else.**

| Where the accent appears | What it marks |
|:--|:--|
| A18, right panel | The nine removed atoms of tryptophan 23 |
| A07 overlay, on the rendered structure | The same nine atoms, in place |
| The probability plot | The W23A curve |

Everywhere else is ink. **A06's composed result reverts to a heavier ink weight**, not
accent. One accent used for one meaning across an A0 sheet gives the eye a thread it can
follow from the structure to the curve without being told to; three accent meanings is
decoration, which §1 already prohibits.

The plot's accent must be applied **at plot time**, not by recoloring afterward — the
curves stay machine-generated.

### Constraints for every asset

| | |
|:--|:--|
| Format | SVG, vector throughout, no embedded raster |
| Ink | One line-weight family (heavy, regular, hairline). No drop shadows, bevels, or gradients-as-volume |
| Legibility floor | Figure assets read at 200 mm; card spots at 45 mm (the band is 5 across in v3, so spots are smaller than v0 assumed) |
| Text | None baked in. All labels are live text placed by the layout |
| Naming | `usdbio-<tier>-<name>.svg` |

---

## 2. Tier 1 — Figure 1

### A18 · `fig-nine-atoms` — **the scale statement**
*Promoted from Tier 3. This is the second most important asset in the library.*

**Depicts.** Two panels, one drawing.

- **Left:** the whole 818-atom complex at true relative scale, in ink, with a hairline
  circle around the tryptophan 23 side chain. **The circle is tiny. That is the drawing.**
- **Right:** that circle enlarged, showing fourteen atoms — the nine removed ones in
  accent, the five kept ones in ink.

**Why it leads.** It makes the multi-scale claim without a word of text, and it is what a
reviewer who stops for eight seconds retains. Every other asset in the library is
schematic and roughly equal in visual weight; this is the only one carrying a magnitude.

**Caption to place beneath it** — free credibility, and it pre-empts the modeling question:
> Real 1YCR coordinates, truncated. Nothing was invented; atoms were only removed.

**Must not.** Add a magnifier lens or a callout box for the enlargement — both are the
stock symbol this library's must-not column keeps rejecting. Keep the right panel in the
same single-stroke ink register, or it tips into looking like a textbook figure.

### A06 · `fig-composition`
**Depicts.** The resolve moment: four sheets seen from above, registered on a light
table's peg bar, light coming up through them so the four contents read as one image. The
composed result is distinguished by **heavier ink**, not by accent (see §1).

**Must not.** Be a funnel, gears, arrows converging on a cloud, or a database cylinder.
Every one of those says "a process happens here"; none says *simultaneous resolution of
independently authored sheets*.

**Still the asset that carries the poster's central claim visually.** If only one gets
real drawing time, it is this one.

### A01 · `fig-layer-sheet`
**Depicts.** A single registered sheet at a slight angle — a rectangle with two peg holes
on one edge and a barely-visible curl at the free corner, so it reads as a physical thing
that can be lifted off the stack. Drawn once, reused four times with different content.

**Must not.** Be a plain rectangle with a drop shadow. Have a folded page corner — that
reads as "document", and these are not documents.

### A02–A05 · the four department owners

Identifiable by what they are *doing*, never by a lab coat and a face. Hands-and-instrument
vignettes.

| ID | Owner | Depicts | Must not |
|:--|:--|:--|:--|
| **A02** | `fig-owner-structure` | Hands turning a physical ball-and-stick model, a diffraction pattern pinned behind | Be a generic scientist-with-microscope |
| **A03** | `fig-owner-simulation` | A figure at a terminal, a compute rack's front panel in outline beside it | Be a laptop with a lightning bolt |
| **A04** | `fig-owner-systems` | A figure at a board, drawing a small node-and-arrow network by hand | Reuse A02's pose |
| **A05** | `fig-owner-analysis` | **Redrawn in v1:** hands over a contact sheet of many small plotted frames, one being marked with a grease pencil | **v0's version drew a person reading a curve, twenty centimeters from the real curve.** Do not draw a readable plot in this asset at all |

**The rule that makes these work.** Four different postures, four different instruments. If
they read as the same person recolored, the departmental-separation claim is undercut by
its own illustration.

### A07 · `fig-residue-callouts`
**Depicts.** Hand-drawn leader lines with small circled anchors, in the ink register, laid
over the rendered structure to mark Phe19, Trp23 and Leu26. **Trp23's anchor carries the
accent** (§1); the other two are ink.

**Must not.** Redraw the molecule. This annotates the `usdrecord` output and nothing more.

---

## 3. Tier 2 — the eight card spots

~45 mm each, beside the heading. These are what stop the band being eight rectangles.
Card numbering follows content spec v3 §6.1.

| ID | Card | Depicts | Must not |
|:--|:--|:--|:--|
| **A09** `spot-bio-vocabulary` | 1 · What USD Bio adds | A specimen-label tag tied to an atom, carrying a blank field where units go | Be a dictionary or a book |
| **A08** `spot-many-hands` | 2 · What OpenUSD is | Several hands from different directions, each laying a sheet onto the same registered stack | Be a group of people around a table |
| **A10** `spot-four-sheets` | 3 · One layer per department | The four sheets fanned edge-on so all four edges show, each marked differently | Repeat A06's top-down viewpoint |
| **A11** `spot-grip` | 4 · The case study | The p53 helix lying in the MDM2 cradle, three contact points marked | **Be a lock and key. Be a puzzle piece.** Both are the first thing anyone draws and both are wrong about the physics |
| **A12** `spot-two-instruments` | 5 · How we know it is right | The same quantity read off two visibly different instruments side by side, giving the same reading | Be a checkmark, a shield, or a clipboard |
| **A13** `spot-frames-and-rack` | 6 · Simulation infrastructure, delivered | **Rescoped in v1:** a film strip of four frames with one molecule shifting between them, the strip running into a drawn rack's front panel | Be a play button or a progress bar. Be a cloud |
| **A14** `spot-standard-mark` | 7 · An open standard for biology | An engraved gauge block — the physical vocabulary of a *measurement standard* — with a small helix incised into it | Be a trophy, flag, globe, or handshake |
| **A15** `spot-shared-bench` | 8 · What the center gets | One bench surface with four different instruments set down by four different hands, all in use | Be a network diagram |

**The pattern in the must-not column is deliberate.** Every rejected option is the first
image the phrase suggests, and every one is a stock symbol saying nothing specific. A
drawing you could have guessed from the heading alone is doing no work.

---

## 4. What must NOT be drawn

| Element | Source |
|:--|:--|
| The p53–MDM2 structure | `usdrecord` on `examples/p53_mdm2/demos/p53_mdm2_integrated.usda` |
| The two probability curves | Plotted from `analysis/p53_mdm2_analysis.usda`, `bio:maboss:prob:<node>`, 500 frames |
| **The diff panel** (new in v1) | Literal terminal output, monospaced, `$` prompts kept. Content spec v3 §6.2 |
| The numeric callouts | Live text |

The diff panel's entire value is that it visibly did not pass through a designer. Styling
it — a rounded frame, a syntax-highlight palette, a removed prompt — destroys the one
thing it is there to do.

---

## 5. Tier 3 — conditional

| ID | Condition | Depicts |
|:--|:--|:--|
| **A16** `fig-converter-tangle` | Only if the **problem-led** super claim is chosen | Two panels: format objects joined by a hand-drawn cable tangle too dense to trace, beside the same objects each running one line to a single registered stack |
| **A17** `fig-network-p53` | Only if the Boolean model needs showing explicitly | The five-node p53/Mdm2 network as a small hand-inked circuit, nodes labeled by live text |

---

## 6. Production order and the cut line

1. **A06** `fig-composition` — the central claim, visually.
2. **A18** `fig-nine-atoms` — the poster's dominant magnitude. *Promoted in v1.*
3. **A01** `fig-layer-sheet` — reused four times; cheapest quality per minute.
4. **A02–A05** the four owners.
5. **A11, A13, A14** — the three card spots doing most for a passer-by.
6. **A07** the residue callouts.
7. **A08–A10, A12, A15** — the remaining card spots.
8. **Tier 3**, if its conditions fire.

**Cut line after item 5.** The hero figure is then complete and three of eight cards carry
a spot. If the band ends up mixed, keep the spots **adjacent** — run them along the top
row and leave the bottom row plain, so the gap reads as restraint rather than as
unfinished work.

---

## 7. Handover note

- One SVG per asset, named per §1, no baked text.
- **A single shared line-weight scale across the whole set.** The set reading as one hand
  is the point, and it is the first thing to break when assets are drawn in separate
  sessions.
- **The accent marks the nine atoms and their consequence, and nothing else** (§1). If an
  accent appears anywhere it does not mark those, it is decoration and comes out.
- Draw at the size each asset is used at, not scaled down from one large drawing. Line
  weight that reads at 200 mm turns to mud at 45 mm.
