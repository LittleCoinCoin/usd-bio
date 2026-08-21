# Poster P-14 hero-wheel figures

Six figures, one per data modality, for the wheel at the centre of the WPI-PRIMe site-visit
poster (A0 portrait). Every figure is generated from committed artifacts by
`make_poster_figures.py` — nothing here is drawn, mocked, or hand-edited.

## Canvas contract (measured 2026-08-21, not assumed)

| | value |
|:--|:--|
| slot | **214.94 × 64.48 mm** |
| ratio | **3.3336 : 1** |
| raster | **2560 × 768 px** (302 ppi) |
| type floor | **22 pt** |

**The brief's 216 × 69 mm / 3.13 : 1 is wrong**, and it matters. The tile card is 216 × 96 mm
with `grid-template-rows: auto minmax(0,1fr)`; the `auto` row is the header carrying the live
labels, which measures 29.93 mm. Subtract that, the 1.2 mm card borders and the 0.6 mm rule
above the image area and the slot is 64.48 mm tall, not 69.

Because the slot is `fit="contain"`, authoring at 3.13 : 1 would fit by height and render
201.8 mm wide inside a 214.94 mm slot — a 0.934× downscale that turns authored 20 pt into
**18.7 pt, under the legibility floor**. Authoring at the measured ratio scales 1.0 and keeps
type at face value. The 22 pt floor then tolerates a further ~9 % slot shrink before breaching
20 pt.

### Reproducing the measurement

```bash
python3 -m http.server 8731 --bind 127.0.0.1 --directory "$(git rev-parse --show-toplevel)"
# open http://127.0.0.1:8731/examples/p53_mdm2/figures/slot_geometry.html, then in the console:
#   await document.fonts.ready; SLOTS()
```

`slot_geometry.html` reproduces the tile card markup verbatim from `PRIMe Poster P-14.dc.html`
(only `<image-slot>` → a plain div with the identical inline box) and links the canon's own
`tokens.css` / `components.css` rather than copies, so it cannot drift from the design system.
All six tiles measure identically. Verified robust: the poster's `styles.css` contains nothing
but two `@import`s, and removing `components.css` leaves the slot box unchanged — the header
metrics depend only on `tokens.css` and Lato.

## Getting the figures onto the poster

Set `src="figures/<name>.<ext>"` on each `<image-slot>`. **Do not drag-and-drop them.**
`image-slot.js` refuses SVG on the drop path (`ACCEPT` is PNG/JPEG/WebP/AVIF only) and
re-encodes anything accepted through a canvas to `toDataURL('image/webp', 0.85)` capped at
`MAX_DIM = 1200` px. The `src` attribute bypasses all of that — `_render` assigns it straight
to the `<img>`. One drop silently replaces a vector with a 1200 px WebP, because the sidecar's
`stored.u` shadows `srcAttr`.

## Accent

The poster's live theme is **`slate`** (`data-props` default), not `canon`, so the accent is
**`#0B5F8A`** — not `tokens.css`'s `#B34700`, which `installAttested()` overrides at runtime.
`--theme` selects it; the attested table is committed in `themes.json`, sourced from the
`.dc.html`. **Switching theme or rerolling in the Palette Lab desyncs the accent and the
accent-bearing figures must be regenerated.**

One accent only, marking the nine removed Trp23 atoms and the W23A curve. Two disclosed
exceptions: `fig-composition` neutralises CPK to ink so Trp23 is the only colour there;
`mod-display` keeps CPK because that tile's claim is inherited element colours in an
unmodified viewer.

## Recorded decisions

- **Monospace is DejaVu Sans Mono, not the canon's JetBrains Mono.** JetBrains Mono is not
  installed on this machine and is not among matplotlib's resolvable families; DejaVu ships
  with matplotlib, so the script re-runs anywhere without a font install. Advance widths are
  near-identical (0.602 vs 0.600 em). Revisit by committing the TTF if the mismatch against
  the poster's own live `<pre>` block reads badly in proof.

## mod-state: where the discrete state actually comes from

The brief assumed Boolean node state was stored. It is not. The stage carries only
continuous per-node probabilities (`bio:maboss:prob:<node>`, 500 frames) and
`maboss/output/` holds only `.bnd`/`.cfg`. Thresholding those probabilities would mean
inventing a cut-off, which the job forbids.

MaBoSS itself resolves this. `get_states_probtraj()` returns the occupancy of each
**network state** — and a network state IS a Boolean vector over the five nodes, so it
is discrete by construction with nothing invented. Probed 2026-08-21 on the committed
W23A model: 500 frames × 19 distinct network states.

Taking the modal (most probable) state per frame gives a genuinely stepped trajectory
with **no flicker** — 500 frames resolve into just four segments:

| frames | modal network state |
|--:|:--|
| 11 | `Mdm2N -- Dam` |
| 29 | `Dam` |
| 34 | `p53_h -- p53 -- Mdm2C -- Dam` |
| 426 | `p53_h -- p53 -- Mdm2C` |

Per-node, under the modal state: p53 / p53_h / Mdm2C on for 460 of 500 frames,
Mdm2N for 11, Dam for 74. So the figure is a 5-row × 500-column on/off raster with four
hard vertical transitions — unmistakably discrete, sharing tile 4's time axis without
duplicating its claim. Consistent with the stored W23A time-average P(p53 up) = 0.861.

### Trap

`run_maboss.ensure_backend()` **must** be called before `maboss.load`. Without it the
external MaBoSS binary fails at `dyld: Library not loaded: @rpath/libsbml.5.dylib` and
pyMaBoSS then dies on a missing `res_probtraj.csv`, which looks like a parsing bug
rather than a library-path one. Use the external binary, not `cmaboss`: `run_maboss.py`
records that the compiled backend returns a wrong node set and empty state labels.

## mod-units: where the unit strings come from (correcting an earlier claim)

I asserted, in the plan and in the `mod-units` brief, that **no `bio:` attribute
carries a unit string anywhere in the USD layers**, and that the units are asserted by
`data/element_properties.py`. The implementer pushed back and was right on both counts.
Verified 2026-08-21 against the composed stage:

- **`bio:ddgUnits` exists and is authored**, value `"kcal/mol"`, on three prims —
  `/p53_MDM2_complex/integration/{F19A,L26A,W23A}`. So the ΔΔG row's unit *is* on the
  stage, alongside its value.
- `data/element_properties.py` contains **none** of the strings `amu`, `Å` or `kcal/mol`
  (grep count 0 for each). Those units are domain convention tied to the cited
  literature, plus `README.md` and `CLAUDE.md` — not assertions in that module.

The accurate position: units are **partly** on the stage. `bio:ddgUnits` is stored;
mass/radius units are not stored anywhere in the layers and are convention. A readback
figure should therefore read `bio:ddgUnits` from the stage rather than typing
`"kcal/mol"`, and be explicit that the remaining four unit strings are convention.
Uniform provenance across rows is the weaker goal here — "read it, don't type it" is
the whole point of the tile, so it wins wherever the data actually exists.

## fig-composition: the 3D-geometry tile, orthographic camera, and a float32 trap

The sixth and last tile. Real geometry from `demos/p53_mdm2_integrated.usda`
(818 atoms / 834 bonds, `ballstick` representation — settled by measurement: an
occlusion check found `points` 86% / `ballstick` 78% / `balls` 75% / `vdw` only 22% of
Chain_B survives MDM2 occlusion from this camera, and `vdw` would bury Trp23 along
with the rest of the peptide). One accent, the nine Trp23 sidechain atoms the W23A
mutation removes, derived as TRP's atom list minus `_ALA_KEEP`
(`composition/build_genotype.py:59`) — never hardcoded. Everything else is neutralised
to an achromatic ink ramp (ascending atomic number → ascending luminance, capped below
the theme accent's own luminance) authored on the `/_class_/{C,N,O,S}` class Spheres,
plus every one of the 834 bond Cylinders individually (bonds have no shared class to
override once, unlike atoms — see `render_support.cylinder_prim_paths`).

**Two candidates are rendered and both stay on disk** (`fig-composition-A.png` /
`-B.png`, `figures/output/`, gitignored by convention same as every other tile's
raster/svg output): A is the whole complex, oriented by PCA so the longest principal
axis (measured 41.8 x 29.4 x 25.5 Å over all 818 atoms) runs horizontally — even
perfectly oriented this fills only ~40% of the frame's width, because the object's own
in-plane aspect (1.42:1) is far narrower than the frame's (3.3336:1); this is a shape
ceiling, not a camera defect. B crops to Chain_B's own centroid and PCA axes (Chain_B
alone measures 2.08:1, much closer to the frame), filling ~72-82% depending on padding
and keeping >1 Å clearance around every individual Trp23 sidechain atom. B is
registered as the default.

**Camera: orthographic, not perspective**, via two new `render_support.py` additions —
`compute_principal_frame()` (PCA over real atom-center world positions, never a
world-axis-aligned bbox) and `author_oriented_orthographic_camera()` — kept fully
separate from `author_camera()` (untouched, still what every other render-based figure
in this package would use). A parallel projection has zero perspective distortion by
construction, sidestepping the ~115°-horizontal-FOV wide-lens distortion
`author_camera`'s default 50°-vertical-FOV perspective camera carries (RENDER_NOTES.md
§7(b)) — verified here with a 9-sphere grid spanning ±10 world units off-axis through
this exact camera path: every unclipped sphere renders at width/height = 1.0000 exactly,
regardless of position in frame.

**The float32 aperture trap.** `UsdGeomCamera`'s aperture attributes are schema-typed
`float` (32-bit), so the float64 world-unit math silently downcasts on `Set()`.
`author_camera()` elsewhere in this file avoids ever hitting this because its aperture
is always `some_round_default_mm * aperture_ratio` — binary-friendly inputs that survive
the downcast without incident. The oriented camera's aperture is derived from real,
non-round object extents, and for at least one measured case (candidate B, `padding=1.15`)
that downcast landed the float32 aperture ratio at `2560/ratio32 = 767.99996` — one ulp
under the pixel-exact-768 gate, which `usdrecord`'s TRUNCATING width/height division then
floors to 767, not 768. Fixed with a deliberate, documented 1e-6 relative nudge on the
vertical aperture only (asymmetric on purpose: it can only make the frame very slightly
MORE generous, never tighter, so it cannot introduce a clip) — see
`author_oriented_orthographic_camera`'s `_APERTURE_F32_SAFETY_NUDGE`.

**Bond cylinders needed their own neutralisation pass, not just a hue check.**
`builders/build_assembly.py` already authors an achromatic flat `(0.5, 0.5, 0.5)` on
every bond — no CPK hue, so the no-CPK gate is satisfied without touching them — but
that flat albedo renders, through Storm's own tone-mapping, at a HIGHER on-screen
luminance (measured: sRGB `(204,204,204)` = 0.8 luminance at specular highlights) than
either the element ink ramp or the accent's own displayed luminance (~0.29 authored,
~0.43 mean displayed). Left alone, the 834 bonds — not Trp23 — would be the visually
brightest achromatic thing in frame. Fixed by overriding every bond Cylinder's own
`displayColor` down to the same linear value as the darkest element ink level (Carbon's).
After the fix, median accent luminance exceeds median ink luminance by ~0.16 (0..1
scale); a small tail (~3% of ink pixels, Storm's specular highlights on ink-colored
spheres, not a hue or design defect) still edges above the accent's own median — see the
task's adversarial-verification gate output for the exact numbers. Reported as a known,
weak-but-present overlap rather than glossed over.

## fig-composition, round 2: recentring candidate B, and a real greyscale fix

Adversarial review came back on the merged tile with two findings, both against
candidate B and the accent, not the underlying rendering mechanism (orthographic camera,
accent derivation, no-CPK neutralisation all stood as-is).

**Candidate B's vertical framing was wrong.** Centering the crop on Chain_B's own
centroid put nearly all of Chain_B in frame, but MDM2 (6x more atoms, not centered on
Chain_B along that axis) piled up almost entirely to one side — an empty band across
roughly the top quarter, structure clipped at the bottom. Correct data, bad center: it
read as a slipped render, not a deliberate crop. Fixed in `fig_composition._recentre_vertically`
by keeping the frame's orientation and extents (same zoom, same width fill logic) but
moving the center along its own `up` axis to the midpoint of the FULL 818-atom
structure's projection onto that axis, rather than Chain_B's centroid — a plain,
reproducible criterion (not eyeballed) that splits whatever the fixed frame height
crops as evenly as the real geometry allows, above and below. Measured result: width
fill went UP slightly (72.5% → 76.1%, since recentring exposes a different, more
balanced set of edge atoms at the same padding=1.3), and Trp23's minimum single-atom
clearance from the frame edge improved too (1.42 Å → 2.26 Å).

**The greyscale margin was real and worse than round 1's gate reported.** Round 1's gate
compared MEDIANS (accent 0.47 vs ink 0.31, separation looked fine) and flagged only a
"~3% tail" as a caveat. The coordinator's stricter, more relevant metric — what fraction
of ink pixels exceed the ACCENT's OWN 5th percentile (i.e. could a viewer confuse an
ordinary highlighted carbon atom for Trp23?) — was **52.6%** at the ramp round 1 shipped.
The reason medians looked fine while this didn't: every lit sphere, any color, has both
a dark (shadowed) side and a bright (lit/highlight) side, so the accent's OWN 5th
percentile sits quite low (~0.29-0.30) — close to typical ink's median — even though its
mean/median is high. A median-vs-median comparison doesn't see that.

Root cause, confirmed empirically (not assumed): Storm's default per-Gprim shading (no
material bound, just `displayColor`) boosts DISPLAYED peak luminance far above the
AUTHORED linear albedo — an authored 0.5 grey rendered at a measured 0.8 displayed
luminance; even round 1's darkest ink level (0.09 authored) displayed at up to 0.62. A
2-sphere-row isolated test (one row plain `displayColor`, one row an explicit
`UsdPreviewSurface` with `roughness=1`, `specularColor=(0,0,0)`) showed the "specular"
peak is NOT a specular term that a material override suppresses — it persists (in fact
got slightly brighter) under a zero-specular material, so it is ordinary diffuse
shading under a bright light responding to a curved (sphere) surface, not a fixable
material property. What DOES work, verified by direct measurement on the real scene
(render → sample → adjust, not derived analytically): darkening the AUTHORED albedo
further, since diffuse response is still proportional to albedo even if boosted:

| ceiling scale (× round-1 ramp) | ink median | ink p95 | ink max | overlap (ink > accent p5) |
|---:|---:|---:|---:|---:|
| 1.00 (round 1) | 0.306 | 0.455 | 0.616 | 52.6% |
| 0.327 | 0.184 | 0.329 | 0.463 | 7.8% |
| **0.20 (shipped)** | **0.145** | **0.298** | **0.424** | **5.5%** |
| 0.12 | 0.118 | 0.282 | 0.400 | 4.3% |

0.20 is the value kept: the curve visibly flattens past it (0.12 buys another ~1 point
for a noticeably darker structure), and the ball-and-stick geometry stayed clearly
legible — not muddy — at every scale tested down to 0.12, inspected visually each time,
not assumed from the numbers alone. The accent color itself was never touched (still
exactly `resolve_theme(theme).accent`, unscaled) — only the ink darkened further around
it, per the coordinator's explicit instruction. See `fig_composition._INK_CEILING_SCALE`
for the constant and the same table inline.

Final candidate B, both fixes applied: width fill 76.1%, greyscale overlap 5.5% (down
from 52.6%); candidate A: width fill 39.5% (shape-limited, unchanged), greyscale overlap
3.0%.

## fig-composition, round 3: the PI decides, and a naming-contract fix

The PI reviewed both candidates and **decided: candidate B ships.** They also declined
to add a second (size-based) cue for the accent, accepting the measured 5.5% greyscale
overlap from round 2 as sufficient — no further accent work is planned.

**Naming-contract violation, found and fixed.** The job's six deliverables have exactly
six fixed names — `mod-text`, `mod-units`, `fig-composition`, `fig-curves`, `mod-state`,
`mod-display` — one file per name. Round 2 shipped `fig-composition-A.png` and
`fig-composition-B.png`; there was no `fig-composition.png` at all, which is a contract
violation regardless of which candidate the PI eventually chose. Fixed: the registered
`fig-composition` figure now writes the shipped candidate (B) to exactly
`fig-composition.png` (`fig_composition.FIG_COMPOSITION_FILENAME`), and returns that
path — the only path the harness's `--only fig-composition` run or any downstream
consumer should ever see. Candidate A stays real, buildable work — useful for anyone
revisiting the framing decision — but is written under
`fig-composition-alt-whole-complex.png` (`fig_composition.ALT_FILENAME`), a name that
cannot be mistaken for a deliverable and is documented in-module and here as a
**rejected alternative kept for reference only**, with the one-line reason: it fills
39.5% of the frame width against B's 76.1%, and the PI chose fill and Trp23 prominence
over showing all 818 atoms in one frame.

**Known tension, recorded plainly rather than left for someone to rediscover.** The
tile's own poster header reads "818 atoms, 834 bonds" (`mod-display`'s companion text,
not this module), and the shipped crop (candidate B) puts a substantial share of those
atoms and bonds outside the frame — MDM2 is cropped, not fully shown, by design, to keep
Trp23 legible and the width filled. The PI was offered the option of rewording the
header to match the crop and **declined it**. The figure and its caption are therefore
knowingly in slight tension: an accepted PI trade-off, not an oversight, and not
something this module can (or should) resolve on its own by changing the header text
itself, which belongs to a different tile.

No change to the underlying rendering mechanism in this round: orthographic camera,
PCA-based framing, the two rounds of color fixes (bond neutralisation, `_INK_CEILING_SCALE`),
and the vertical recentring all carry over unchanged — verified by re-running gates 1–7
against the renamed files and getting IDENTICAL numbers to round 2 (5.51% overlap for
the shipped candidate, 2.99% for the alt, Sphere=818/Cylinder=834, both PNGs exactly
2560×768 RGBA with transparent corners, orthographic isotropy unaffected since
`render_support.py` was not touched this round).
