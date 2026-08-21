# conference_assets

A reusable base for **A0 posters (portrait + landscape)** and **1-slide flash talks**, derived from Mike Morrison's #betterposter work, the ScienceUX community around it, and Michael Alley's Assertion-Evidence slide research — then corrected against a four-lens review (methodology, typography, practitioner, systems).

This is the abstract base. It carries no project's content and no lab's branding. Instantiating it means supplying content and overriding role tokens — not editing rules.

## Documents

| Doc | Layer | Read it when |
|:--|:--|:--|
| [00-identity_v0.md](00-identity_v0.md) | identity | the why, the dwell architecture, the known failure modes |
| [00-tokens_v0.md](00-tokens_v0.md) | token-vocabulary | what an atom means and where its number came from |
| [01-guidelines_v0.md](01-guidelines_v0.md) | actionable-guidelines | you are making an asset and need the rule |
| [01-consumption_v0.md](01-consumption_v0.md) | consumption-guide | **start here** for a new poster or talk |
| [evidence_base_v0.md](evidence_base_v0.md) | supporting | you must defend a choice to a reviewer |

## Library

| File | What |
|:--|:--|
| `library/tokens.css` | the atoms — vocabulary only |
| `library/components.css` | shared components, the take switch, the proofs |
| `library/poster-a0-portrait.html` | 841 × 1189 mm |
| `library/poster-a0-landscape.html` | 1189 × 841 mm — "Presenter" layout |
| `library/flash-talk.html` | 338.7 × 190.5 mm, Assertion-Evidence |
| `library/render.py` | renderer + five verification gates |
| `library/sync.py` | builds `dist/` for Claude Design |

## Use

```bash
python3 __canons__/conference_assets/library/render.py --all
```

```bash
python3 __canons__/conference_assets/library/sync.py
```

Then run `/design-sync` yourself against `library/dist/` — it cannot be invoked on your behalf.

> **Why a renderer instead of `chrome --print-to-pdf`:** that flag silently ignores `@page { size }` and emits US Letter, so an A0 poster arrives at the print shop at quarter scale. `render.py` drives Chrome over the DevTools protocol with `preferCSSPageSize`, then verifies the result.
>
> **Why geometry is not enough:** the page size comes from a hard-coded `@page` literal, so a poster whose stylesheet failed to load still reports a perfect A0 while being visually destroyed. The gates also check that tokens and components actually applied, that the display font resolved (fallback shifts metrics), that the headline did not wrap past two lines, and that `data-take` is valid *for that surface*.
>
> **Why `dist/`:** a Claude Design component is one self-contained file. Publishing the working templates would 404 their relative `<link>` tags and render an unstyled skeleton. `sync.py` inlines the CSS, hashes it, and promotes `@dsCard` to the first line.

## The one-paragraph version

Lead with a single plain-language **claim** — for tools work, the design decision someone thinks is wrong — left-aligned at 120pt, emphasis carrying both colour *and* an underline so it survives greyscale. Support it with one figure whose caption asserts what to see. Then **put methods and limitations back in**, drawn as a diagram: that is where the field studies measure the billboard losing (67% preferred IMRAD for "details and rigor"), and it is a risk-management decision rather than an evidenced one. Push depth into the take-away layer — a QR only if a real public artifact exists, otherwise a typeset URL, your contact, an invitation to leave *their* address, or nothing — but never anything the reader needs in the room. Make the programme title carry the same claim, since most planners never wander. Proof it in greyscale before printing.

## Honest scope

The strongest claim this system supports: **it makes one claim land.** The only independent trial of the poster format was null on overall knowledge transfer; the format's measured win is on the stated conclusion, and its measured loss is on perceived rigor. The flash-talk half rests on better ground — Assertion-Evidence has independent replication with delayed-retention gains. Trust the slide rules more than the poster rules, and see [evidence_base_v0.md](evidence_base_v0.md) before defending either.

## Provenance

Geometry was measured by parsing Morrison's own OSF PowerPoint files, not taken from secondary write-ups. Two corrections that matter: his landscape canvas is **1372 × 914 mm (US 54 × 36 in), not A0**, so published percentage grids do not transfer; and the current "Presenter" layout is a **~21% silent bar + ~75% main panel**, not the 25/50/25 split described elsewhere.
