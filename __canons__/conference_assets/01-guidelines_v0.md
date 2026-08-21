# conference_assets — Actionable Guidelines

**Layer:** actionable-guidelines · **Batch:** 01 · **Version:** v1 (revised after panel review) · **Date:** 2026-08-16

Prescriptive production rules. Every rule carries its warrant so you know what you can defend and what is merely this canon's convention.

## Warrants

| Tag | Means | Weight |
|:--|:--|:--|
| `[geometry]` | parsed from Morrison's own PPTX | a measurement of an artifact — tells you what he *did*, not that it is good |
| `[morrison]` | Morrison asserts it (slide, guide, FAQ) | **authority, not evidence.** Ranks equal to `[house]` |
| `[field]` | Oronje et al. 2022 (n=59, n=95) | *preference* data, not learning outcomes |
| `[rct]` | Lewis et al. 2025 (n=94) | randomised **whole posters** — warrants the format as a bundle, never a single rule |
| `[ae]` | Alley Assertion-Evidence | the best-evidenced material here; independently replicated |
| `[optics]` | visual-angle arithmetic | physical and checkable — recompute and disagree |
| `[house]` | our choice | no external warrant. Override freely |

**Two corrections to how this canon used to tag itself.** `[measured]` previously covered both real geometry and Morrison's opinions, which let "he did it this way" silently outrank "we chose this" — imitation laundered as measurement. And no individual rule can carry `[rct]`: the trial randomised complete posters, so type size, layout, content reduction and the assertion sentence are confounded together.

**Independence asymmetry — let this change your confidence.** Morrison co-authors the field study, the eye-tracking pilot (in his own outlet), and the dataviz commentary. The only two *independent* studies are Lewis 2025 (posters — essentially null on overall knowledge transfer) and Sripradith 2023 (AE slides — positive, replicated). **Trust §10 more than §§1–9.**

---

## 0. Applicability gate — run this before anything else

A canon of closed sets that leaves its own applicability open is inconsistent. Answer these first. `[house]`

| Condition | Action |
|:--|:--|
| The work has **one** claim a stranger could disagree with | proceed |
| Several co-equal results | `data-evidence="grid"`, and expect friction |
| Evidence is inherently a wall of images (microscopy, histology) | this format fights you — consider not using it |
| Session is **judged on methodological completeness** | `data-billboard="compact"` + `data-evidence="grid"`, or use a traditional poster |
| No claim exists at all (pure catalogue, null methods work) | say so plainly in the billboard — **do not manufacture a punchline** |

A fabricated punchline is worse than an honest topic line.

## 1. Surfaces — closed set

A0 portrait (841×1189), A0 landscape (1189×841), 16:9 slide (338.7×190.5). `render.py` refuses anything else. `[house]`

**Prefer landscape** where permitted: it is what the eye-tracking pilot selected, and its top-left gaze entry matches western reading order. `[optics]` Weigh it as a tiebreaker — n=13, and its own authors call it flawed.

**Portrait has no silent presenter bar.** The single-column narrative means your body occludes the middle while you stand there, and `data-stand` does not apply. Portrait forfeits the stand-alone-read guarantee. `[house]`

## 2. The takeaway line

1. **One sentence, one claim.** Needs an "and"? That's two posters, or a `grid`. `[house]`
2. **A claim, not a topic.** *"Effect of X on Y"* is a label; *"X halves Y under Z"* is a claim. The claim-vs-topic mechanism is what the bundle-level trial actually improved. `[rct, bundle-level]`
3. **Plain language, including for experts.** `[morrison]`
4. **Left-align. Never centre.** `[morrison]` — one of the few places his stated reason matches the reading literature.
5. **Emphasise with `<em>`**, which carries colour **and an underline**. Hue alone violates §6 and inverts on the dark panel, where the accent sits at 4.65:1 against white at 17.97:1 — the emphasised word becomes the dimmest. `[optics]`
6. **120pt default, 100–140pt sanctioned.** `[optics]`
7. **Two lines maximum.** Three means cut words, not shrink type. `render.py` fails the build if it wraps past two. `[house]`

### For tools, methods, and infrastructure work

The format assumes a finding. It does not require one — it requires a **claim**, and an architectural thesis is often *more* disagreeable than a p-value. `[house]`

**The billboard states the design decision someone in the audience thinks is wrong.**

> *"An MD trajectory is an animation clip. Compose it like one."*
> *"Biology data doesn't need another file format. It needs a scene graph."*

Both are 10–12 words, fit two lines at 120pt, and invite argument. That is the mechanism working exactly as intended.

## 3. Zone content

**The silent bar holds ~200 words — a 50–60 second stand-alone read.** `[optics]` Morrison's "1–4 minutes" describes bar + method chips + captions read carefully together. `[morrison]` If your stand-alone story needs more, the format is fighting you; see §0.

Morrison's cut rule: if it does not fit, you have too much — move it behind the take-away, then cut. **Never shrink the type**, which trades a solvable content problem for an unsolvable legibility one. `[morrison]`

**Put the silent bar on the side you do NOT stand on** (`data-stand`), mitigating documented occlusion. `[house]`

**Never split one result across two zones.** Chandler & Sweller's split-attention effect and the documented "dance back and forth" criticism both point here: related content stays together, even at the cost of white space. `[house, from cited premises]`

**Cut from the sheet:** full references, extended methods, supplementary figures, the abstract.
**Never cut:** methods and the limitation — see §4.

## 4. Methods and limitations are mandatory

The field studies found IMRAD preferred **67%** for "communicating details and rigor". `[field]`

**Be precise about what that licenses.** It is a *preference* measure: respondents rated which format *seemed* rigorous. Dense text may signal rigor without transferring it, and the trial that measured actual transfer found no overall advantage either way. The remedy was never tested — "billboard + methods diagram" is a third condition that exists in no study.

So the rule stands on **risk management, not evidence**: the deficit is the format's best-documented weakness, the cost of a methods diagram and a limitation line is small, and the downside of omitting them in judged or sceptical settings is real. Min-max under uncertainty favours inclusion. `[field] documents the deficit; this repair is [house] and untested.`

**Methods are drawn, not written** — boxes for arms, conditions, analysis steps. Each box is one decision a reviewer would challenge. `[morrison]`

**The limitation line** may be titled **"Status"** or **"Scope"** for early-phase work — for prototyping-stage infrastructure it reads as status, not confession, and pre-empts the obvious question. It must never sit inside the 5-second layer. `[house]`

## 5. Type — absolute, never proportional

| Token | Size | Cap height | Comfortable at |
|:--|:--|:--|:--|
| `--type-takeaway` | 120pt | 30.3mm | 3.6 m |
| `--type-section` | 72pt | 18.2mm | 2.2 m |
| `--type-title` | 60pt | 15.2mm | 1.8 m |
| `--type-body` | 36pt | 9.1mm | 1.1 m |
| `--type-caption` | 28pt | 7.1mm | 0.85 m |
| `--type-detail` | 20pt | 5.1mm | 0.6 m |

Legibility is visual angle: the hall sets the distance, not the paper. Percentage grids copied from Morrison break silently because his canvas is 1372×914mm, not A0. `[optics]`

**These distances are the dwell ladder's actual justification** — the tiers coincide with a reader's physical approach. The ladder is *not* licensed by information-foraging theory, which models a continuous patch-leaving process with no discrete rungs.

**Sans-serif here is voice, not legibility** — the literature finds no consistent advantage at distance. What is load-bearing is **weight contrast**, which survives font fallback. `[house]`

**Proportion and point size are a matched pair.** Morrison's 37.7% band was calibrated to 125–138pt on a 914mm canvas; porting the proportion while correctly shrinking type stranded ~80mm of empty panel. The band is now content-sized with a floor. `[optics]`

## 6. Colour — closed set

**Nine role tokens, themed in PAIRS.** Every surface has an ink. Overriding `--panel` without `--panel-ink` is the commonest way to produce an invisible takeaway. `[house]`

1. **One accent.** `--accent` on paper, `--accent-on-panel` on the dark band. `[optics]`
2. **Hue is always redundant** with position, shape, or label.
3. **Categorical scale is Okabe-Ito.** `--cat-1..5` are safe as lines, points, or text. **`--cat-6..8` are fill-only and must be outlined** — on white they are 2.25:1, 2.31:1 and 1.32:1, all below the 3:1 graphics floor. `[optics]`

   The CSS scale is ordered by contrast-on-paper; `studio/palette-engine.js` keeps `PE.OKABE` in the *published* Okabe-Ito order so it stays recognisable. These no longer disagree in practice: `chart-kit.js`'s `catPick()` assigns in **safety order** regardless of array position, so the Nth series always gets the Nth-safest entry. Verified in `studio/_smoke.html`. `[house]`

4. **More than about three categorical series is a structural problem, not an ink one.** Measured, not asserted: the full eight-value scale's worst pair separates by **1.02:1** in greyscale — indistinguishable. Okabe-Ito is colour-vision-deficiency-safe, *not* greyscale-safe. Past roughly three series no amount of redundant encoding rescues it; the answer is fewer series, small multiples, or direct labels carrying the identity. Run `CK.greyDiagnostic()` to check a specific figure. `[optics]`
5. Contrast ≥ 4.5:1 prose, ≥ 3:1 graphics.

## 7. Figures — Goldilocks, not minimal

1. **Caption above, as an assertion sentence saying what to see.** Sanctioned *only* when it makes a claim — a bare label above a figure is worse than one below. `[morrison]` + `[house]`

2. **Run the three-dose comparison; do not aim at a number.** The earlier wording — *"aim for a middle data-ink ratio"* — was a target masquerading as a method. The source licenses a **procedure**: render the same figure lean, mid and rich, put them side by side, and choose. It cannot warrant a numeric default, so the doses themselves are `[house]`.

   ```js
   CK.goldilocks('series', {roles, ...data})   // → [{ink:'lean',svg},{ink:'mid',svg},{ink:'rich',svg}]
   ```

   Doses derive from the dwell layer when you don't want to choose: `dwell:'5s'` → rich (memorability, and it must survive a glance), `'1min'` → mid, `'5min'` → lean-but-fully-labelled (accuracy over engagement). **The methods kit inverts this deliberately** — a protocol figure earns *more* labelling the longer someone studies it.

3. **Prefer the conventional form unless the unconventional one is demonstrably clearer.** Familiarity is a real axis and the canon was not modelling it. A reader who must first work out *what they are looking at* has not yet started looking at it. This is why `distribution()` defaults to a box rather than the higher-data-ink strip: less ink, less familiar, slower to read is a bad trade. `strip` and `both` remain available for the case where raw spread is the point. `[house]`

4. **Label series directly**, not in a detached legend.

5. **One hero figure by default.**

6. **Raster figures carry a resolution floor** — 150 ppi for a hero, 300 ppi for a detail crop meant to be examined closely. `CK.ppiCheck()` computes it. Both numbers are printing-industry convention, **unverified against your printer**, and should be checked on the same test print as the ink ceiling. `[house]`

## 8. The take-away layer

**The zone's job is continuity past the room — not "a QR code".** Never print a code resolving to a 404, a private repo, or "coming soon". `[house]`

| `data-take` | Use when |
|:--|:--|
| `qr` | a real, public, permanent artifact exists |
| `url` | durable, but a code is overkill — one short typeset URL |
| `contact` | no output yet; the work is still the person |
| `capture` | nothing **yet**, but it's coming — ask for *their* address |
| `none` | nothing exists; reclaim the space for evidence |

`qr` at 158mm default `[geometry]`, 102mm floor. **Test the printed proof with a phone at two metres** — screen tests prove nothing about ink.

**Before defaulting to `contact` or `none`,** check for a repo, docs site, demo, protocol, OSF project, dataset DOI, or ORCID. **A repository is a perfectly respectable thing to point at** — for software work often better than a paper.

`none` is explicitly sanctioned by Morrison's own FAQ, which trades the QR away for a figure. `[morrison]`

**Nothing the reader needs in the room may live only here.** `[house]`

## 9. The discovery layer — before the poster exists

Fewer than 5% of delegates visit any given poster, and many plan their route from the programme rather than wandering. **The abstract-book title is the true 5-second layer** — for most readers it is first contact. `[house, from cited premises]`

So: **the submitted title and abstract must carry the same claim as the billboard.** A poster whose takeaway contradicts, or merely fails to echo, its programme entry is invisible to everyone who planned their visit.

## 10. Flash-talk slide — Assertion-Evidence

The best-evidenced part of this system. Do not apply poster rules. `[ae]`

1. **Sentence assertion headline**, left, **max 2 lines**, 28pt.
2. **Visual evidence. No bullet lists** — a list hides the relationships among the listed items.
3. Body 18–24pt; references 12–14pt, never bold.
4. **≥13mm white space below the headline.**
5. **~20 words per minute of slide time** — a 60-second talk affords ~20 on-screen words total. `data-proof="words"` counts them.
6. **Speak extemporaneously.** The slide is not the script.
7. No all-caps, italics, or underline.
8. **Take-away is usually `poster`**, not `qr`: "Poster 42 · Thursday 16:00 · Hall B" is more actionable than a link, and a projected code is scannable only while the slide is up.

**60-second beat sheet** (~140–150 spoken words): claim 10s → point at the visual and say what to see 25s → the one number or mechanism 15s → "come argue with me at Poster 42" 10s.

**Venue warning:** flash sessions usually collect slides in advance, often PPTX-only, sometimes in a mandated template. These content rules survive transplantation; the rendered PDF may not be accepted. Check the CFP.

## 11. Mandatory proofs

```bash
python3 library/render.py --all      # geometry + tokens + components + font + wrap
```

| Proof | How | Passes when |
|:--|:--|:--|
| Geometry | `render.py` | a sanctioned canvas |
| Token attach | `render.py` | CSS actually applied — geometry alone passes even when the poster is destroyed |
| Font | `render.py` | display face resolved; fallback shifts metrics and can reflow the billboard |
| Headline wrap | `render.py` | ≤ 2 lines |
| Config validity | `render.py` | `data-take` legal **for that surface** |
| Greyscale | `data-proof="grey"` | every distinction survives — **read it twice**, see below |
| Dwell | `data-proof="dwell"` | the 5s layer reads alone |
| Word budget | `data-proof="words"` | ≤ 20 words |

**The greyscale pass answers two different questions from one conversion.**

1. *Sufficiency* — does every distinction survive without hue? This is a **conservative** test, stricter than deutan/protan vision, and it doubles as the mono-laser check. A failure here is a defect.
2. *Data-ink diagnostic* — if every distinction survives, the colour was **decorative ink**: legitimate, and yours to spend or cut. If one dies, hue is **load-bearing**, and no amount of ink spent elsewhere fixes it. `CK.greyDiagnostic()` returns `decorative` or `load-bearing` with the worst pair.

The second reading is what makes the proof useful for figure design rather than only for accessibility compliance.

For a stronger check than greyscale, `PE.build()` runs a **Machado-2009 CVD simulation** (protan/deutan/tritan, ΔE ≥ 10) across the accent/ink/panel/field pairs. It is currently reachable only from the palette engine, not from the proof toggles.

**The 5-second test** remains the one that matters: show it to someone outside your subfield for five seconds, take it away, ask what the finding was.

---

**Related:** [[00-identity_v0]] · [[00-tokens_v0]] · [[01-consumption_v0]] · [[evidence_base_v0]]
