# conference_assets — Identity

**Layer:** identity · **Batch:** 00 · **Version:** v0 · **Date:** 2026-08-15

---

## What this system is

A reusable base for **A0 posters (portrait and landscape) and 1-slide flash talks**, derived from Mike Morrison's #betterposter work, the ScienceUX community around it, and Michael Alley's Assertion-Evidence slide research.

It is an *abstract base*. It carries no project's content and no lab's branding. Instantiating it for a specific piece of work means supplying content and overriding role tokens — never editing the rules.

## The governing sentence

Morrison states the design philosophy himself, on the last slide of his own template deck:

> Design isn't about making things look pretty. It's about directing attention.

That is this canon's controlling heuristic. Every rule below exists to answer one question: **does this direct a stranger's attention to the finding faster?** Aesthetics are downstream of that, not alongside it.

Its corollary, also his: *"UX designers feel a surge of happiness when they get to delete something."* When a decision is genuinely balanced, delete.

## The architecture is dwell time, not typography

The popular reading of #betterposter is "put your finding in a giant font." That is the visible symptom, not the design. The actual architecture is a **ladder of engagement layers**, each of which must pay off on its own:

| Layer | Reader is | Must deliver |
|:--|:--|:--|
| **5 s** | walking past, not stopping | one plain-language finding, legible at 3 m |
| **1 min** | paused in front of it | why it matters, and the evidence for the claim |
| **5 min** | reading properly, or talking to you | methods, rigor, the honest limitation |
| **take** | gone | continuity past the room — a pointer to depth, or a way to reach you |

A reader who leaves at any rung should still have gained something.

**What licenses this ladder is optics, not foraging theory.** The tiers correspond to real viewing distances: the 5-second layer at 120pt is comfortable at 3.6 m, the 1-minute layer at 36pt at 1.1 m, the 5-minute layer at 20pt at 0.6 m. The information tiers coincide with a reader's physical approach, and you can recompute the arithmetic and disagree with it.

This canon previously claimed the layering "is why the format works", citing information foraging (Pirolli & Card). That claim was borrowed from Morrison and does not survive scrutiny: foraging models a *continuous* patch-leaving process, and supplies no discrete rungs at 5 s / 1 min / 5 min. No study in the corpus measures dwell time at a real poster session. Treat the rungs as **testable design targets** — each layer must pay off alone — not as a mechanism explaining the format's success.

Every template in `library/` marks these layers with `data-dwell` so they can be proofed rather than assumed.

## The tension this system must hold

The evidence is genuinely mixed, and the canon is built around the mixture rather than around the marketing.

**What the billboard format demonstrably does well.** Across two field studies (Oronje et al. 2022; n=59 and n=95) it beat traditional IMRAD posters on visual appeal, approachability, perceived learning, promoting discovery, and — most strongly — **understanding the main message (82%)**. The Vienna eye-tracking pilot found the v2 layouts were the *only* stimuli where every participant looked at every area of interest; on traditional posters, whole regions went unread even with 20 seconds of undisturbed viewing.

**What it demonstrably does badly.** In the same field study, the traditional poster won on **communicating the details and rigor of the study (67%)**. The authors' own conclusion is that future billboard designs must put methods and rigor back in. And the one genuine randomised controlled trial (Lewis et al. 2025, PRiMER, n=94) found **no significant effect on overall knowledge transfer** — only on the narrow two-item measure of the stated conclusion.

So the honest claim is narrow and worth stating plainly: **this format makes one finding land. It does not, on current evidence, make people learn more overall.**

The design consequence is the thing that most distinguishes this canon from a naive #betterposter template: **the 5-minute layer is not optional decoration.** Methods and limitations are load-bearing structure, because they are precisely where the format is measured to lose. A poster built here that drops them is not a lean poster; it is a poster with a known defect.

## Voice

**Plain language, stated as a claim.** Morrison's own cited ammunition is four Nielsen Norman Group articles, and two of them are about plain language being interpreted faster — *including by experts*. Jargon is not rigor. A finding written so a neighbouring field can read it has not been dumbed down; it has been made foragable.

**Assertions, not topics.** "Effect of X on Y" is a label. "X halves Y under Z" is a claim. Labels can only be filed; claims can be agreed with, disagreed with, and remembered. This is the single rule shared by the poster billboard and the Assertion-Evidence slide headline, and it is the highest-leverage sentence-level habit in the system.

**Honest about limits.** The limitation line is part of the voice, not a compliance gesture. It is what buys the billboard its credibility with the audience that the format otherwise loses.

## Material grounding

The system behaves like **printed signage read at walking pace**, not like a document reduced to fit a wall. Concretely:

- Type sizes are **absolute**, never proportional to the sheet. A poster is read from 1–3 m whether it is turned portrait or landscape, so glyph height cannot change with orientation. Morrison's own templates are anchored to a 1372×914 mm US canvas; every percentage-based reconstruction of them breaks silently when moved to A0. This canon re-anchors to absolute millimetres for that reason.
- Colour must survive **greyscale and colour-vision deficiency**. Meaning is never carried by hue alone; hue is always redundant with position, shape, or label. The community forks of the template made this an explicit requirement, and Morrison's own palette does not meet it.
- Figures aim for a **Goldilocks** data-ink ratio, not maximum minimalism (Lai & Morrison 2025). Stripping a chart to Tufte-minimal can cost the visual cues that make it readable at a glance.

## What this system deliberately refuses

- **Centred billboard text.** Morrison's own template carries this as an explicit rule: centred text is slower to read than left-aligned.
- **Bullet lists as evidence on a slide.** A list conceals the relationships between the listed items, which is the part worth showing.
- **Meaning encoded in hue alone.**
- **Shrinking type to fit content.** If it does not fit, there is too much of it. Cut it, or move it behind the QR code.
- **Template literalism.** The MIT #evenbetterposter critique is fair: authors who assume that using the template makes the poster good end up cramming jargon-dense sentences into small side bars, which defeats the whole design. The rules here are a floor, not a substitute for judgement.

## Known failure modes, carried openly

These are real, documented, and unresolved. A consumer of this canon should know them before choosing the format.

- **Occlusion.** In a real session, the presenter's body and a cluster of attendees block the centre of the poster. Morrison's demo footage is filmed in an empty room. Mitigation: the silent bar goes on the side you do *not* stand on (`data-stand`).
- **QR codes are scanned less than they are printed.** Never let the take-away layer carry anything the reader needs in the room. And a QR is not a requirement of the format — when no preprint or public artifact exists, a typeset URL, your contact details, an invitation to leave *their* address, or simply deleting the zone are all better than a code pointing at nothing. Morrison's own layout FAQ already treats the QR as demotable when the space is worth more to a figure.
- **Poor fit for multi-result and image-dense work.** The format assumes one punchline. Studies with several co-equal findings, or evidence that is inherently a wall of microscopy, fight it. Use the `evidence` / `grid` variants, or reconsider the format.
- **Judged sessions.** Where posters are scored on methodological completeness, the billboard's measured weakness on "details and rigor" is a direct scoring risk. Use the evidence-weighted variant.
- **Initial hostility.** Some viewers react negatively to the format on sight, before reading. That reaction is real and worth anticipating in how you open a conversation.

---

**Related:** [[00-tokens_v0]] · [[01-guidelines_v0]] · [[01-consumption_v0]] · [[evidence_base_v0]]
