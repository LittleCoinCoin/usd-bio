# conference_assets — Consumption Guide

**Layer:** consumption-guide · **Batch:** 01 · **Version:** v1 (revised after panel review) · **Date:** 2026-08-16

How to turn this base into one project's poster or flash talk. Read this first if you are making an asset; read [[01-guidelines_v0]] for the rule behind a decision.

You **supply content** and **override role tokens**. The base is never edited to make an instance. If you find yourself changing a rule to fit content, that is a signal about the content.

---

## Architecture

```
tokens.css        ← atoms. Vocabulary only. Never edited per-project.
components.css    ← shared components + the take switch + the proofs.
  └── <project>.theme.css   ← override role tokens IN PAIRS. Nothing else.
        └── poster-a0-*.html / flash-talk.html   ← layout + your content
              └── render.py   → print-ready PDF, five gates
              └── sync.py     → dist/, self-contained, for Claude Design
```

Toggles live on the `.sheet` wrapper, not `<body>`, so a published Design component survives being wrapped by the platform.

## Step 0 — Run the applicability gate

Read §0 of the guidelines before committing to this format. It is a real gate, not a formality: multi-result work, image-dense evidence, and completeness-judged sessions all fight the billboard, and the honest answer is sometimes "use a traditional poster".

## Step 1 — Write the takeaway before opening a template

**Test:** state it as a sentence someone could disagree with. *"Effect of X on Y"* fails — a topic. *"X halves Y under Z"* passes — a claim.

**For tools, methods, or infrastructure work** — where there is no experimental finding — the billboard states **the design decision someone in the audience thinks is wrong**:

> *"An MD trajectory is an animation clip. Compose it like one."*
> *"Biology data doesn't need another file format. It needs a scene graph."*

An architectural thesis is usually *more* disagreeable than a p-value. The mechanism does not require empiricism; it requires a claim.

Then hand it to someone outside your subfield. Five seconds. If they cannot restate it, no layout will save the poster.

## Step 2 — Start the hero figure the SAME DAY

**This is the schedule risk, and it is larger than anything in the system.**

For an experimental study the hero figure is a chart you already have. For tools or methods work the evidence is an *architecture* — a mechanism diagram, a before/after, an anatomy drawing — and it does not exist yet in poster-grade form. Drawing one is commonly **2–3 days**, and it is the single largest cost in the whole exercise.

You will not get stuck on the templates; they render first try. You will get stuck staring at an empty `hero figure` placeholder on day three.

Start it the same day as the takeaway, not after the layout is done.

## Step 3 — Choose the surface

| Situation | Use |
|:--|:--|
| Landscape permitted | `poster-a0-landscape.html` — the eye-tracking pilot's pick |
| Portrait mandated | `poster-a0-portrait.html` (note: no silent bar, no occlusion mitigation) |
| Judged on completeness | `data-billboard="compact"` + `data-evidence="grid"` |
| Several co-equal results | `data-evidence="grid"` |
| 60-second talk | `flash-talk.html` |

Set `data-stand` to the side you will physically stand on; the silent bar moves opposite.

## Step 4 — Theme it, in pairs

Override role tokens in a separate file, linked **after** the base:

```css
/* usd-bio.theme.css — the nine role tokens, themed in pairs */
:root {
  --paper: #FFFFFF;   --ink: #17171B;   --ink-soft: #55555F;
  --field: #EEF3F6;
  --panel: #1B1033;   --panel-ink: #FFFFFF;      /* ← pair */
  --accent: #B34700;  --accent-ink: #FFFFFF;     /* ← pair */
  --accent-on-panel: #E69F00;                    /* accent for the dark band */
  --rule: #C9D2D9;
}
```

```html
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="components.css">
<link rel="stylesheet" href="usd-bio.theme.css">
```

**Themed in pairs is not advice, it is the contract.** Set `--panel` to a pale institutional blue while leaving `--panel-ink: #FFFFFF` and your takeaway becomes white-on-pale — invisible at any distance. Every surface token has an ink token; move them together.

Do not override type sizes, spacing, or zone proportions. Those are the system; the colours are the skin.

**Mandated logos** go in the `.badges` slot; set `--badge-h` to reveal it. This exists so a required logo does not force a fork.

## Step 5 — Fill the dwell layers in order

Each layer must pay off alone. The tiers correspond to real viewing distances, so a reader who stops further away still gets something.

- **5 s** (3.6 m) — the takeaway. Two lines maximum.
- **1 min** (1.1 m) — why it matters, and the hero figure with an assertion caption.
- **5 min** (0.6 m) — methods **drawn as a diagram**, and the limitation. Not optional: this is exactly where the format is measured to lose.
- **take** — see Step 5b.

## Step 5b — Choose the take-away honestly

The template defaults to `qr`, and that default is wrong for a lot of real work. **A code resolving to a 404, a private repo, or "coming soon" is worse than no code.**

Stop at the first true row:

| Ask | Set |
|:--|:--|
| Preprint, DOI, dataset, docs site, or **public repo**? | `data-take="qr"` |
| Same, but short/memorable, or a scan-hostile venue? | `data-take="url"` |
| Nothing published, but coming in months? | `data-take="capture"` |
| Nothing published, nothing imminent? | `data-take="contact"` |
| Nothing at all, and evidence wants the space? | `data-take="none"` |

Check first for: repo, docs site, hosted demo, registered protocol, OSF project, dataset DOI, lab page, ORCID. **A repository is a perfectly respectable destination** — for software or methods work often better than a paper.

On the **flash talk** the default is `poster` — if a poster session follows, "Poster 42 · Thursday 16:00 · Hall B" beats any link.

Do not manufacture a destination. A placeholder page stood up the week of the conference becomes a dead link that outlives it.

## Step 6 — Align the programme entry

Fewer than 5% of delegates visit any given poster, and many plan from the programme. **The submitted title and abstract are the true 5-second layer for everyone who plans ahead** — make them carry the same claim as the billboard.

## Step 7 — Proof

```bash
python3 library/render.py --all
```

Five gates run automatically: page geometry, token attach, component attach, font resolution, and headline wrap, plus `data-take` validity for that surface. Geometry alone is not sufficient — it passes even when the stylesheet failed to load and the poster is destroyed.

Then, by hand:

1. **Greyscale** — `data-proof="grey"` on `.sheet`. Every distinction must survive. Conservative sufficiency test, and the mono-laser check.
2. **Dwell** — `data-proof="dwell"`. Read only the 5s layer. Does it teach something?
3. **Word budget** (slide) — `data-proof="words"`. Must read `ok`.
4. **The human 5-second test.** The one that matters.

## Step 8 — Print

`render.py` produces true-size A0 with vector text. Ask for **100% scale, no fit-to-page**.

- **Colour:** the tokens are sRGB. Large-format shops run RGB inkjet RIPs and generally prefer sRGB — tell them that. The specific risk is `--panel`: a rich dark purple can crush toward black on cheap conversion, and that band is the poster's face. **Ask for a proof of the dark band.**
- **Bleed:** `--bleed` defaults to 0, which assumes roll printing with no trim. If your shop trims, set it and say so, or full-bleed bands will show white slivers.
- **Fonts:** `render.py` fails the build if the display face did not resolve — fallback shifts metrics and can push a two-line billboard to three. Install Lato, or change `--font-display` deliberately.
- **Accessibility:** on a standard 2.4 m board, keep the QR and limitation in the **0.9–1.6 m band** so seated and wheelchair-using visitors can reach them. A QR at the very bottom of a portrait sheet sits at knee height.
- **Virtual/hybrid:** the billboard format degrades unusually well to a laptop thumbnail. On screen, prefer `url` over `qr` — nobody scans their own monitor.

## Step 9 — Publish to Claude Design

```bash
python3 library/sync.py
```

Writes `dist/` with the CSS inlined, `@dsCard` promoted to the first line, and the doctype dropped. Then run `/design-sync` yourself and point it at `dist/` — it cannot be invoked on your behalf.

Never publish the working templates directly: their relative `<link>` tags will 404 in a canvas component and every `var()` will resolve to nothing.

`sync.py --check` fails if `dist/` is stale.

## Escalation

- **Image-dense evidence** (microscopy): the single-punchline assumption fights you. Use `grid`, or reconsider the format.
- **No claim at all:** say so plainly. A fabricated punchline is worse than an honest topic line.
- **Hostile first reactions** are documented. One sentence, ready: *it is designed so you learn the finding without stopping; the rigor is all still here.*

## Adding to the base

Only when a need recurs across **three or more** projects. Token first, then the rule in [[01-guidelines_v0]], then use it. A token that exists for one poster is not a token.

---

**Related:** [[00-identity_v0]] · [[00-tokens_v0]] · [[01-guidelines_v0]] · [[evidence_base_v0]]
