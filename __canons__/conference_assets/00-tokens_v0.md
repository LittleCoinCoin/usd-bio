# conference_assets — Token Vocabulary

**Layer:** token-vocabulary · **Batch:** 00 · **Version:** v0 · **Date:** 2026-08-15

The sanctioned atoms. **`library/tokens.css` is the executable source of truth**; this document explains what each group is for and where its numbers came from. When the two disagree, the CSS wins and this file is stale.

Downstream templates reference tokens. They never redefine them and never hard-code a literal value. Adding a token means editing `tokens.css` first.

---

## Provenance

Numbers tagged `[measured]` were read out of Morrison's own OSF PowerPoint files by parsing the OOXML geometry — not taken from any secondary write-up. Two measurements contradict the commonly published figures:

- His **landscape canvas is 1372 × 914 mm** (US 54 × 36 in), **not A0**. Every percentage grid derived from it silently misfits A0.
- The **"Presenter" layout is ~21% silent bar + ~75% main panel**, not the 25/50/25 three-column split that secondary sources describe.

## 1. Canvas — closed set

`--canvas-a0-portrait-*` (841 × 1189 mm), `--canvas-a0-landscape-*` (1189 × 841 mm), `--canvas-slide-*` (338.7 × 190.5 mm). No fourth surface. `render.py` enforces this.

`--margin-poster: 48mm` ≈ the 5.7–5.9% inset measured in Morrison's portrait template `[measured]`. Full-bleed bands intentionally run past it to the trim edge.

## 2. Type — absolute, closed set

Seven poster steps (`--type-takeaway` 120pt → `--type-micro` 14pt) and three slide steps (`--type-ae-assertion` 28pt, `--type-ae-body` 22pt, `--type-ae-ref` 13pt).

**Absolute, not proportional — this is the load-bearing decision of the whole system.** Reading distance does not change when a sheet is rotated, so glyph height must not either. Measured anchors: portrait 114/76/62/42/36/17 pt; landscape 125–138/66–80/60/48/20–24 pt `[measured]`. Slide steps are Alley's checklist verbatim `[ae]`.

Two separate scales exist because a projected slide and a printed sheet are read at different distances. Do not mix them.

## 3. Typefaces

`--font-display` (900 weight) / `--font-prose` / `--font-mono`. Morrison used Segoe UI Black + Segoe UI Light (portrait) and Lato Black (landscape) `[measured]`.

The **weight contrast** carries the hierarchy and is load-bearing. The *choice of sans* is voice only — the legibility literature finds no consistent sans-over-serif advantage at distance, so never defend it on legibility grounds.

## 4. Colour — closed set

**Six semantic roles:** `--ink`, `--ink-soft`, `--paper`, `--field`, `--panel` / `--panel-ink`, `--accent` / `--accent-ink`, `--rule`. Re-skinning a poster means overriding these six and nothing else.

**One accent.** A second accent means neither is one.

**Eight categorical values** `--cat-1..8`: the Okabe-Ito colour-vision-deficiency-safe qualitative palette. Use in order; do not add a ninth. Morrison's shipped palette (`#31092D` aubergine, `#E1F1F4` field, `#F68B1F`, `#662D91`) is recorded in `tokens.css` for reference but is **not CVD-safe** and is not the default here — the community forks made CVD-safety and greyscale survival explicit requirements, and we follow them.

Hue is always redundant with position, shape, or label.

## 5. Space

One geometric ladder, `--space-1` (6mm) → `--space-6` (84mm). Every gap on a poster is a rung on it. `[house]`

`--measure-prose: 34ch` — over-long lines are the commonest silent-bar failure.

## 6. Zone proportions

`--zone-silentbar: 21%`, `--zone-main: 74.6%`, `--zone-takeaway-band: 37.7%` `[measured]`.

These are the only proportional tokens in the system, because they describe *layout regions*, which do scale with the sheet — unlike type, which does not.

## 7. QR

`--qr-size: 158mm` default, `--qr-size-min: 102mm` floor. 158 mm is Morrison's own portrait figure `[measured]`, well above the 4-inch minimum usually quoted; scan range scales with module size.

## 8. Proof utilities

Not decoration — these are the test suite.

- `.proof-grey` — desaturates the surface. Catches meaning encoded in hue alone, and simulates the department mono laser.
- `.proof-dwell` — outlines each `data-dwell` layer so you can verify the 5-second layer reads on its own.
- `data-proof="words"` (slide only) — live count against the ~20-words-per-minute reading budget `[ae]`.

---

**Related:** [[00-identity_v0]] · [[01-guidelines_v0]] · [[01-consumption_v0]] · [[evidence_base_v0]]
