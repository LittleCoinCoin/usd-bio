# studio/03b — kit refactor (v3) — PENDING CONVERSION

## What this is

`templates/goldilocks-ink/GoldilocksInk.dc.html` in the online project was **not a template**.
Its own masthead reads *"Studio plate 03b · kit refactor · v3"*. It is the review plate
arguing for the v3 kits — forced into `templates/` because the read-only design-system
project would not accept a new file under `studio/`.

The two kits it shipped beside itself are already salvaged into this directory as
`chart-kit.js` and `methods-kit.js` (both v3). Its `ds-base.js` (12-line loader) and
`support.js` (70KB generated `dc-runtime`) are platform scaffolding — discarded.

## Its own "to land in the repo" list — three guideline edits, not yet applied

1. **§7.2** — replace the phrase *"aim for a middle data-ink ratio"* with the **three-dose
   procedure**: render lean / mid / rich and compare. The method is comparison, so the
   guideline should prescribe the comparison, not a vague target.
2. **§7** — add a **familiarity rule**: prefer the conventional form unless the
   unconventional one is demonstrably clearer. (This is why v3's `distribution()` defaults
   back to a box: v2's strip-with-mean-bar was Tufte-minimal *and* less legible.)
3. **Proof table, greyscale row** — gains a **second reading**. Greyscale is both a
   sufficiency test (CVD + mono laser) *and* a data-ink diagnostic: if every distinction
   survives desaturation, the colour was decorative and is free to spend or cut; if one
   dies, hue is carrying data alone.

Explicitly **not** needed: pictogram kit and diagram grammars. The commentary is about data
graphics; pictograms are non-data ink by definition, which it grants rather than governs.

## A canon-level finding this plate surfaced

Running `greyDiagnostic()` over the whole categorical scale shows **the eight-value
Okabe-Ito set does NOT survive desaturation**. It is a colour-vision-deficiency-safe
palette, not a greyscale-safe one.

Consequence the guidelines do not currently state: **more than about three categorical
series is a structural problem, not an ink one.** Beyond that, no amount of redundant
encoding rescues it — the answer is fewer series, or small multiples.

## Tweak panel it exposed

`theme` (canon | slate | bone | moss | vermilion), `distributionForm` (box | strip | both),
`greyscale` (boolean). Worth reproducing as controls when this becomes a plate.

## Conversion status

The original is a `.dc.html` canvas component: React via `DCLogic`, `{{ }}` interpolation,
`<sc-for>` iteration. The other studio plates are vanilla HTML + inline `<script>`.
Converting it to plate form is real work and is NOT done. Until then this file records the
decisions so nothing is lost. The raw canvas source is the real one, recovered byte-exactly by `_pull.py` and kept beside
this file as `03b-kit-refactor.dc.html` — an earlier hand-typed copy
at `03b-kit-refactor.dc.html` was deleted as redundant (and was not byte-exact: manual copying
had converted JS unicode escapes to literal characters).
