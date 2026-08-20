# USD Bio — Hand-Drawn Illustration Asset Library (v0)

**Purpose.** The drawn assets for the PRIMe site-visit poster (P-14), specified so the
Claude Design system can produce them as a coherent, reusable set rather than as
one-off decoration. Content spec: [`00-content_spec_v2.md`](00-content_spec_v2.md).

**Why a library and not just figures.** Everything drawn here recurs: the layer motif
appears in every talk about this project, the department owners appear whenever
departmental separation is explained, and the card spots are reusable on slides. Drawing
them once as named SVGs makes the next poster and the next talk cheap.

---

## 1. The house register

**Recommended: technical ink-line drawing.** One ink weight family, drawn as an
engineer's or a naturalist's hand would draw it — confident single-stroke contours,
sparse hatching for volume, no fills except one accent. The register a good lab notebook
sketch or an old instrument plate sits in.

Why this one, concretely:

- It is **serious**. A JSPS delegation reads ink-line technical drawing as competence.
  Cartoon vignettes read as a school project, and clip-art figures read as a slide deck.
- It **survives A0**. Line drawing scales without the muddiness that flat-fill
  illustration develops at poster size and at two metres.
- It **cannot be mistaken for the evidence**. The molecular render and the probability
  curves are photographic and plotted respectively; drawn assets in a visibly different
  medium never blur that boundary. This matters more than it sounds — see §4.

**Subject-matter through-line worth using.** OpenUSD's layers descend from film
compositing, where independently drawn transparent sheets stack and resolve into one
frame. That is not a metaphor invented to explain the technology; it is where the
technology comes from. Drawing layers as physical registered sheets on a light table is
therefore *accurate*, and it lands the "film pipelines already solved this" argument
without spending a word on it. Keep it as subject matter, in the same ink register as
everything else — never as a separate whimsical style.

**Alternate register, if the above reads too industrial for a biology institute:**
scientific-plate drawing — the Haeckel or Cajal lineage, finer line, more hatching, more
organic contour. Equally serious, biology-native, and slightly warmer. Pick one and hold
it across all assets; the two do not mix.

### Constraints that hold for every asset

| | |
|:--|:--|
| Format | SVG, vector throughout, no embedded raster |
| Ink | One line-weight family (a heavy, a regular, a hairline). No drop shadows, no bevels, no gradients-as-volume |
| Color | Ink + at most one accent, applied only to carry meaning (the thing that moves, the thing that is new). Never applied decoratively |
| Legibility floor | Every asset must read at 200 mm wide, and the card spots at 60 mm |
| Text | None baked in. All labels are live text placed by the layout, so they stay editable and translatable |
| Naming | `usdbio-<tier>-<name>.svg`, e.g. `usdbio-fig-layer-sheet.svg` |

---

## 2. Tier 1 — Figure 1, the hero

Seven assets. The figure does not work without these.

### A01 · `fig-layer-sheet`
**Depicts.** A single registered sheet, seen at a slight angle: a rectangle with two peg
holes on one edge and a barely-visible curl at the free corner, so it reads as a
physical thing that can be lifted off the stack. Drawn once, reused four times with
different content sitting on it.

**Must not.** Be a plain rectangle with a drop shadow. Have a folded page corner (that
reads as "document", and these are not documents). Carry a border so heavy it becomes a
box.

**Reuse.** Every future explanation of layered composition, in any talk.

### A02–A05 · the four department owners
Four small figures, each identifiable by what they are *doing*, never by a lab coat and
a face. Drawn waist-up or as hands-and-instrument vignettes, roughly 80 mm tall in
Figure 1.

| ID | Owner | Depicts | Must not |
|:--|:--|:--|:--|
| **A02** | `fig-owner-structure` | Hands turning a physical ball-and-stick model, with a diffraction pattern pinned behind | Be a generic scientist-with-microscope |
| **A03** | `fig-owner-simulation` | A figure at a terminal, with a compute rack's front panel drawn in outline beside it | Be a laptop with a lightning bolt |
| **A04** | `fig-owner-systems` | A figure at a board, drawing a small node-and-arrow network by hand | Reuse the same pose as A02 |
| **A05** | `fig-owner-analysis` | A figure holding up a plotted curve on a sheet, reading it | Be a bar chart with a magnifying glass |

**The rule that makes these work.** Four *different* postures and four *different*
instruments. If they read as the same person recolored, the departmental-separation claim
is undercut by its own illustration.

**Reuse.** The center's own explanations of who contributes what. This is the most
reusable set in the library.

### A06 · `fig-composition`
**Depicts.** The resolve moment: the four sheets seen from above, registered on a light
table's peg bar, light coming up through them so the four contents read as one image.
The composed result is the only part in accent color.

**Must not.** Be a funnel. Be gears. Be arrows converging on a cloud. Be a database
cylinder. Every one of those says "a process happens here" and none of them says what
this actually is, which is *simultaneous resolution of independently authored sheets*.

**This is the asset that carries the poster's central claim visually.** If only one
Tier-1 asset gets real drawing time, it is this one.

### A07 · `fig-residue-callouts`
**Depicts.** A set of hand-drawn leader lines with small circled anchors, in the ink
register, to be laid over the rendered p53–MDM2 structure to mark Phe19, Trp23 and
Leu26. Drawn as an overlay so it composes with the render rather than replacing it.

**Must not.** Redraw the molecule. The structure comes from `usdrecord` on the real
artifact (§4 below) — this asset annotates it and nothing more.

---

## 3. Tier 2 — the eight card spots

One small drawing per card, ~60 mm, sitting beside the heading. These exist so the card
band is not eight grey rectangles, and they are what makes a passer-by's eye stop on a
card at all.

| ID | Card | Depicts | Must not |
|:--|:--|:--|:--|
| **A08** `spot-many-hands` | 1 · What OpenUSD is | Several hands, from different directions, each laying a sheet onto the same registered stack | Be a group of people around a table |
| **A09** `spot-bio-vocabulary` | 2 · What USD Bio adds | A small specimen-label tag tied to an atom, carrying a blank field where units go | Be a dictionary or a book |
| **A10** `spot-four-sheets` | 3 · One layer per department | The four sheets fanned so all four edges are visible at once, each edge marked differently | Repeat A06's viewpoint — this one is edge-on, A06 is top-down |
| **A11** `spot-grip` | 4 · The case study | The p53 peptide seated in the MDM2 groove, drawn as a schematic contact: a helix lying in a cradle, three contact points marked | Be a lock and key. Be a puzzle piece. Both are wrong about the physics and both are the first thing anyone draws |
| **A12** `spot-two-instruments` | 5 · How we know it is right | The same quantity being read off two visibly different instruments side by side, giving the same reading | Be a checkmark. Be a shield. Be a clipboard |
| **A13** `spot-frame-strip` | 6 · Molecular dynamics | A film strip of four frames in which one drawn molecule shifts slightly between frames, with the strip running off the edge of the spot | Be a play button. Be a progress bar |
| **A14** `spot-standard-mark` | 7 · An open standard for biology | An engraved standards mark or gauge block — the physical vocabulary of a *measurement standard* — with a small helix incised into it | Be a trophy, a flag, a globe, or a handshake |
| **A15** `spot-shared-bench` | 8 · What the center gets | One bench surface with four different instruments set down on it by four different hands, all in use at once | Be a network diagram. Be a cloud |

**The pattern in the "must not" column is deliberate.** Every rejected option is the
first image the phrase suggests, and every one of them is a stock symbol that says
nothing specific. A drawing whose subject you could have guessed from the card heading
alone is doing no work.

---

## 4. What must NOT be hand-drawn

Stated here because it is the easiest boundary to erode once a drawn set exists and looks
good.

| Element | Source | Why it cannot be drawn |
|:--|:--|:--|
| The p53–MDM2 structure in Figure 1 | `usdrecord` on `examples/p53_mdm2/demos/p53_mdm2_integrated.usda` | It is the evidence that the system produces real output. A drawn molecule makes the whole figure an illustration of a claim rather than a display of one |
| The two probability curves | Plotted from `analysis/p53_mdm2_analysis.usda`, `bio:maboss:prob:<node>`, 500 frames | A smooth drawn curve is indistinguishable from an invented one, and this audience contains people who look |
| The `31 % → 86 %` callout | Live text | Typography, not illustration |

The medium difference is itself informative: a reviewer sees drawn assets explaining
structure and rendered assets carrying results, and reads the distinction correctly
without being told.

---

## 5. Tier 3 — conditional

Draw only if the corresponding decision goes that way.

| ID | Condition | Depicts |
|:--|:--|:--|
| **A16** `fig-converter-tangle` | Only if the **problem-led** super claim is chosen (§2 of the content spec) | Two panels: format objects joined by a hand-drawn tangle of cables too dense to trace, beside the same objects each running one line to a single registered stack. The contrast is the whole drawing |
| **A17** `fig-network-p53` | Only if the case-study chain needs the Boolean model shown explicitly | The five-node p53/Mdm2 network drawn as a small hand-inked circuit, nodes labeled by live text |
| **A18** `fig-alanine-shave` | Only if the mutate stage needs its own beat in Figure 1 | One residue drawn twice — intact, then with the side chain cut back to alanine — same viewpoint, the removed part ghosted in hairline |

---

## 6. Production order and the cut line

Fifteen assets in Tiers 1–2 is a real amount of drawing. Ordered so that stopping at any
point still leaves a working poster:

1. **A06** `fig-composition` — the poster's central claim, visually. Nothing substitutes.
2. **A01** `fig-layer-sheet` — reused four times; cheapest quality-per-minute in the set.
3. **A02–A05** the four owners — the departmental claim depends on them being four
   distinguishable people.
4. **A11, A13, A14** — the three card spots doing the most work for a passer-by.
5. **A07** the residue callouts.
6. **A08–A10, A12, A15** — the remaining card spots.
7. **Tier 3**, if its conditions fire.

**The cut line is after item 4.** If time runs out there, the hero figure is complete and
five of eight cards carry a spot; the three bare cards read as deliberate restraint
rather than as unfinished work, provided the bare ones are the three *adjacent* cards and
not scattered. If the band ends up mixed, make the spots run along the top row and leave
the bottom row plain.

---

## 7. Handover note for the design system

- Deliver each asset as its own SVG, named per §1, with no baked text.
- Keep a single shared line-weight scale across all fifteen; the set reading as one hand
  is the point, and it is the first thing to break when assets are drawn in separate
  sessions.
- The accent color is spent on meaning only — the composed result in A06, the moving
  molecule in A13, the removed side chain in A18. If an accent appears anywhere it does
  not mark a change of state, it is decoration and should come out.
- Draw at the size each asset is used at, not scaled down from one large drawing; line
  weight that reads at 200 mm turns to mud at 60 mm.
