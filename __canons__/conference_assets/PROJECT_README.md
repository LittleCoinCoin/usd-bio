# Poster & Flash Talk System

A reusable base for **A0 scientific posters** (portrait + landscape) and **1-slide flash talks**, derived from Mike Morrison's #betterposter research, the ScienceUX community around it, and Michael Alley's Assertion-Evidence slide work — then corrected against a four-lens review.

These are **print surfaces**, not React components: two A0 sheets and a 16:9 slide. Their API is CSS custom properties plus `data-*` attributes on a `.sheet` wrapper. Each card here is a self-contained, print-ready page.

## The three surfaces

| Card | Size | Notes |
|:--|:--|:--|
| `poster-a0-portrait` | 841 × 1189 mm | No silent presenter bar; your body occludes the middle while you stand at it |
| `poster-a0-landscape` | 1189 × 841 mm | "Presenter" layout — what the eye-tracking pilot selected |
| `flash-talk` | 338.7 × 190.5 mm | Assertion-Evidence; the better-evidenced half of the system |

## Toggles

All on the `.sheet` element.

| Attribute | Values | Surface |
|:--|:--|:--|
| `data-take` | `qr` · `url` · `contact` · `capture` · `none` | posters |
| `data-take` | `poster` · `qr` · `url` · `contact` | slide |
| `data-evidence` | `hero` · `grid` | posters |
| `data-billboard` | `full` · `compact` | posters |
| `data-stand` | `right` · `left` | landscape |
| `data-proof` | `grey` · `dwell` · `words` (space-separated) | all |

## Theming

Override the **nine role tokens in pairs** — every surface token has an ink token:

```css
:root {
  --paper: #FFFFFF;  --ink: #17171B;  --ink-soft: #55555F;
  --field: #EEF3F6;
  --panel: #1B1033;  --panel-ink: #FFFFFF;   /* pair */
  --accent: #B34700; --accent-ink: #FFFFFF;  /* pair */
  --accent-on-panel: #E69F00;
  --rule: #86929C;   /* 3.18:1 on paper; #C9D2D9 was 1.53:1 and failed the 3:1 floor */
}
```

Setting `--panel` to a pale colour while leaving `--panel-ink` white makes the takeaway invisible. Move them together. Do not override type sizes, spacing, or zone proportions — those are the system.

## The rules in one paragraph

Lead with a single plain-language **claim** — for tools work, the design decision someone thinks is wrong — left-aligned at 120pt, with emphasis carrying colour *and* an underline so it survives greyscale. Support it with one figure whose caption asserts what to see. Then put **methods and limitations back in**, drawn as a diagram: that is where the field studies measure the billboard losing (67% preferred traditional posters for "details and rigor"), and it is risk management rather than an evidenced fix. Push depth into the take-away layer — a QR only if a real public artifact exists — but never anything the reader needs in the room.

## Honest scope

The strongest claim this system supports: **it makes one claim land.** The only independent trial of the poster format was null on overall knowledge transfer. The flash-talk half rests on better ground — Assertion-Evidence has independent replication with delayed-retention gains. Trust the slide rules more than the poster rules.

## Source

Lives in `__canons__/conference_assets/` in the `usd-bio` repository. Rendered to print-ready PDF with `library/render.py`, which verifies page geometry, token attach, component attach, font resolution, headline wrap, and per-surface config validity. Cards here are built by `library/sync.py`.

Full guidelines, token vocabulary, and the graded evidence base are in `guidelines/`.
