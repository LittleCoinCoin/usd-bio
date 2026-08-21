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
