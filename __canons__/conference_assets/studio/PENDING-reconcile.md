# Reconciliation ledger — studio ↔ library

**Opened 2026-08-21.**

## Direction of authority — read this first

**The online project is GROUND TRUTH for the studio layer.** Eliott authored it there
deliberately; it is the current state of the design system, not a proposal against `library/`.
Where the two disagree, `library/` is the side that is **stale**, and this file lists what local
must do to catch up — not decisions to be relitigated.

From now on the flow reverses permanently: **every future change is made in this repo first,
then pushed.** The online copy stops being an authoring surface and becomes a published mirror.
That is why the whole studio layer is being brought down: so there is something local to edit.

This file therefore has two kinds of entry:

- **CATCH-UP** — local differs from online; local changes to match. No decision required.
- **LOCAL EDIT** — something *I* changed during import that online does not have. Each is listed
  so it can be kept or reverted before the push. These are the only entries that need a look.

Verified working: `_smoke.html` loads all six modules (`palette-engine`, `chart-kit`,
`methods-kit`, `pictogram-kit`, `diagram-grammars`, `specimen`) plus `plate.css`, and runs
**46 assertions — all passing**. Run it with:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --allow-file-access-from-files --virtual-time-budget=6000 \
  --dump-dom "file://$PWD/_smoke.html"
```

---

## 0. LOCAL EDIT manifest — the only places local differs from online

`_pull.py --diff` is the authority; this is its reading as of 2026-08-21. Everything not listed
is byte-identical to the online project.

| File | Local edit | Origin |
|:--|:--|:--|
| `studio/chart-kit.js` | v2 → **v3** (recovered from `templates/goldilocks-ink/`), plus safety-ordered `catPick()` and themeable font | your decisions 1 & 3 |
| `studio/methods-kit.js` | v2 → **v3**, plus hairline comment corrected and themeable font | your decisions 2 & 3 |
| `studio/diagram-grammars.js` | hairline comment + themeable font | your decisions 2 & 3 |
| `studio/plate.css` | added the missing `.compare` grid rule; note on `--u` | fixes the unbalanced plate 03 you reported |
| `studio/palette-engine.js` | **added `['rule','field',3]` to `CHECKS`** + a note comment | ⚠️ **my unilateral change** |

Note `studio/methods-kit.js` shows no drift row because the online **v2** was never downloaded —
only the v3 from `templates/`. The local file is v3; online is still v2. That gap is real and
invisible to `--diff`.

**All five edits are cleared.** An earlier draft of this ledger flagged the `palette-engine.js`
check as needing a decision because "6/6 attested themes fail it". That framing was wrong — see
§11 for the correction. Measured: every attested wheel state and 200/200 rolled palettes pass
the full 8-check contract. Nothing is blocking the push.

## 1. Categorical scale order — RESOLVED (your decision: safety ordering)

| Side | Order | `--cat-1` / `OKABE[0]` |
|:--|:--|:--|
| `library/tokens.css` | reordered by contrast-on-paper, safe values first | `#0072B2` |
| `studio/palette-engine.js` | the published Okabe-Ito order | `#000000` |

`chart-kit.js` cycles `PE.OKABE` in **its** order, so a figure's third series and CSS `--cat-3`
are different colours. Confirmed by smoke test.

Both orders encode something real: the CSS order is a **safety ranking** (cat-6..8 are fill-only
because they fail the 3:1 floor on white); the JS order is the **published palette** everyone
recognises. Options:

- **(a)** reorder `PE.OKABE` to match the CSS, and drop the safety note from the CSS since
  position now carries it. One source of truth; loses the recognisable published order.
- **(b)** keep both, and have `catPick()` sort by `catSafety()` before assigning, so *safety*
  drives assignment while the array stays canonical. Costs one sort; keeps both meanings.
- **(c)** declare the CSS scale display-only and the JS scale chart-only. Cheapest, but leaves
  two things called `cat-3` that differ — the exact defect this ledger exists to kill.

**Resolved:** (b) applied — `catPick()` sorts by `catSafety()`; `PE.OKABE` untouched. Verified in `_smoke.html`.

## 2. Hairline weight — RESOLVED (your decision: keep both, document)

`library/tokens.css` sets `--rule-weight: 0.6mm`. Both kits set `STROKE.hair = 0.35` and their
comments assert *"hairline == --rule-weight"*, which is false. `STROKE.data = 1.4` is then
derived as "4× the hairline", so the error propagates into every data stroke.

Options: raise the kit hairline to 0.6 and rescale data/strong to 2.4/3.6; or keep 0.35 as a
deliberately finer **chart-internal** hairline and fix the comment. The second is probably right
— a gridline inside a figure and a rule dividing the sheet are different jobs — but it must be
*stated*, and `--rule-weight` should stop being cited as its source.

**Resolved:** both kept. 0.35mm is the chart-internal hairline, 0.6mm the sheet rule; the false 'they are equal' comment is gone from all three kits and the distinction is stated in `tokens.css`.

## 3. Figure typeface — RESOLVED (your steer: scalability + customizability)

Both kits hardcode `font-family="Archivo, sans-serif"` into every SVG they emit. The poster
type stack is `--font-display` / `--font-prose` = Lato / Segoe UI. So **every figure renders in a
different typeface from the sheet it sits on**, and neither kit reads the token.

**Resolved:** default `inherit`, so a figure adopts whatever surface it sits on — `--font-prose`
on a sheet, Archivo inside a plate — with no coordination. Two escape hatches for exceptions:
`CK.setFont()` / `MK.setFont()` / `DG.setFont()` project-wide, and `{font:'…'}` per call.
No kit hardcodes Archivo any more.

## 4. Greyscale safety of the categorical scale — EVIDENCE, guidelines need updating

Empirically confirmed, not asserted: the eight-value scale's **worst pair separates by 1.02:1**
in greyscale. `greyDiagnostic()` returns `separates: false` for the full set.

Consequence the guidelines do not state: **more than about three categorical series is a
structural problem, not an ink one.** Past three, no redundant encoding rescues it — the answer
is fewer series or small multiples. Add to §6.

## 5. The three guideline edits plate 03b asked for — APPLIED

1. **§7.2** — replace *"aim for a middle data-ink ratio"* with the **three-dose procedure**
   (render lean/mid/rich, compare, choose). `CK.goldilocks()` makes it runnable.
2. **§7** — add a **familiarity rule**: prefer the conventional form unless the unconventional
   one is demonstrably clearer.
3. **Proof table, greyscale row** — gains its **second reading** as a data-ink diagnostic
   alongside the existing CVD/mono-laser sufficiency test.

Explicitly not needed: pictogram kit and diagram grammars — the commentary governs data
graphics, and pictograms are non-data ink by definition.

## 6. New concepts the guidelines do not cover at all

- **Ink budget.** `PE.estimateInk()` + `COV_MAX = 0.30` (total coverage ceiling). Nothing in the
  guidelines mentions an ink ceiling. It is a `[house]` number, and the plates flag it as
  unverified against a real print.
- **`PLATE_MAX = 0.22` is a plate-share ceiling.** (Corrected 2026-08-21: an earlier draft of
  this ledger called it a dead constant. That was wrong — it looked unused because only
  `palette-engine.js` had been read. `specimen.js`'s `meter()` uses it for the plate budget
  readout.) It is still not enforced anywhere — `PE.build` warns on `COV_MAX` but never on
  plate share — so a poster can exceed it silently while the meter shows it in red.
- **`ppiCheck()` raster floors** — 150 ppi hero / 300 ppi detail crop. Textbook numbers, flagged
  by plate 03 itself as unverified against an actual printer. Should be checked on the same test
  print as the ink ceiling.
- **CVD simulation** (Machado 2009, ΔE ≥ 10) — a stronger check than the canon's greyscale proof,
  and currently only reachable from the palette engine.

## 11. `--rule` was below its own floor — FIXED, with a follow-on decision

**The defect.** `library/tokens.css` shipped `--rule: #C9D2D9`, which is **1.53:1** against
white. The guidelines demand **≥3:1** for graphics. Every hairline, figure frame and title rule
on every poster rendered so far was at less than half the required contrast. The studio had
already found and fixed this independently (`#86929C`, 3.18:1); the library never checked.

**Fixed on import:** `--rule` is now `#86929C`, matching the studio's validated value, which
also removes a library↔studio divergence.

**The follow-on, which neither side had caught.** Figure frames are drawn on `--field`, not on
`--paper`, and `PE.CHECKS` only ever tested against paper. Adding `['rule','field',3]` reveals:

| theme | rule on field | verdict |
|:--|--:|:--|
| canon | 2.84:1 | fail |
| slate | 2.84:1 | fail |
| bone | 2.91:1 | fail |
| moss | 2.86:1 | fail |
| ash | 2.80:1 | fail |
| vermilion | 2.79:1 | fail |

### CORRECTION 2026-08-21 — the "6/6 fail" framing was wrong

An earlier draft of this section presented the six failures as evidence that the *check* was
mis-scoped, and proposed weakening it. Eliott pointed out that the online generator worked well
in practice, which is the correct signal. Measuring settled it:

| what was measured | rule/paper | rule/field | verdict |
|:--|--:|--:|:--|
| six **attested wheel states**, via `PE.build()` | 3.59–3.67:1 | **3.20–3.31:1** | all 8 checks pass |
| **200 randomly rolled** palettes | — | — | **200/200 pass** |

The six failures were never the generator. They were Plate 01's **hardcoded `[data-theme]` CSS
blocks** — hand-tuned constants that Plate 02 explicitly withdrew as definitions, keeping the six
only as *attested instances* (named wheel states). Run through the generator, those same six
clear the new check comfortably.

**Resolution: keep the check.** It costs the generator nothing — the repair pass moves lightness
until it passes — and it closes a blind spot that had let a 1.53:1 `--rule` ship in
`library/tokens.css` unnoticed.

**Optional follow-up, not done:** Plate 01's hardcoded `[data-theme]` blocks still carry the old
paper-only-tuned values and are now the only place in the system below the floor. Plate 02 §04
already argues the fitted values are correct — *"Where a fitted theme differs from its Plate 01
twin, the fitted one is the correct value."* Regenerating those six CSS blocks from their wheel
states would align Plate 01 with its own successor. That is an edit to ground truth, so it is
proposed rather than applied.

## 12. Plate 01 proposes a layout change the library has not adopted

`studio/01-theme-layer.html` (Plate 01) argues for a **contained plate** — the dark takeaway
region as an object with paper margin on all four sides — replacing the full-bleed band the
library currently renders (`.billboard` spans full width). Its case: less ink, and it gains a
silhouette recognisable at 20 m, so the system acquires a signature instead of looking like the
default #betterposter template.

This is load-bearing: adopting it means re-cutting both posters and the slide. **Not adopted.**

It also introduces three tokens the library does not have — `--ink-plate-max: 22%`,
`--ink-coverage-max: 0.30`, `--ink-accent-events: 1` — and six named `[data-theme]` blocks
applied by a single attribute, which is a far better answer to "how do I re-skin this" than the
consumption guide's hand-written `<project>.theme.css`.

Note Plate 01's own decision 3 (the closed set of six) is **explicitly withdrawn by Plate 02**,
which replaces it with the generator: *any palette may be generated, only generated palettes may
be installed.* The six survive as attested defaults.

## 7. Resolved on import — no action

- **`.compare` grid rule was missing** from `plate.css`, so plate 03's three DO/DON'T pairs
  stacked as six full-width boxes in one column. That was the "unbalanced kit". **Fixed**, in
  both the grid rule and the mobile collapse.
- **`--u: 1cqw` / `1.414cqw`** in the specimen blocks is **not** a rival unit doctrine. Specimens
  are scaled thumbnails inside a review document; container units are correct there, and
  1.414 = √2 is the A-series ratio so one system serves both orientations. The absolute-for-print
  doctrine is untouched. Noted in `plate.css`.
- **`templates/goldilocks-ink/` was never a template.** It held the v3 kits and plate 03b,
  exiled there because the read-only project refused writes to `studio/`. All unique content is
  now on disk. `ds-base.js` (12-line loader) and `support.js` (70KB generated `dc-runtime`) are
  platform scaffolding, discarded.

## 8. Conversion debt

`03b-kit-refactor.dc.html` is a canvas component: React via `DCLogic`, `{{ }}` interpolation,
`<sc-for>`. It **cannot render standalone** — the `{{ }}` tokens show literally without the
platform runtime. Plates 01–06 are vanilla HTML + inline script and do render. Converting 03b to
plate form is outstanding; `PENDING-03b.md` records its decisions meanwhile.

## 9. Import status

**Done:** `palette-engine.js`, `chart-kit.js` (v3), `methods-kit.js` (v3), `pictogram-kit.js`,
`diagram-grammars.js`, `specimen.js`, `plate.css` (+ `.compare` fix), `03b-kit-refactor.dc.html`.

**Still to import:** plates `01`–`06` HTML, the project `README.md`,
`_adherence.oxlintrc.json`. Not needed: `_ds_bundle.js` (compiled output), `.thumbnail`.

## 10. The ink instrument validates itself — no action, worth knowing

Two independent measurements of the same specimen agree:

| Method | Coverage C | Plate share |
|:--|:--|:--|
| `PE.estimateInk()` — the `SCHEDULE` approximation | 17.8% | 13.1% (constant) |
| `SP.coverage()` — measured off the live DOM | 17.0% | 13.1% (measured) |

`PLATE_SHARE = 0.131` is exactly the measured plate share, so the schedule was calibrated
against this specimen rather than guessed. The approximation holds to under one point, which
means `PE.estimateInk()` is safe to use where measuring the DOM is impractical — as its own
comment claims. That claim is now checked rather than asserted.

Once imported, `studio/` should be pushed back so the online copy tracks disk — and from then on
the repo is the only place either side is edited.
