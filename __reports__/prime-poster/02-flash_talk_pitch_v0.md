# USD Bio — Flash Talk Spoken Pitch (v0)

**Purpose.** The frozen spoken opening for the P-14 poster walkthrough, delivered live
at the WPI-PRIMe site visit (2026-09-03). This is the words said aloud when a visitor
stops at the poster — distinct from the printed flash-talk slide, which lives outside
this repository at
`~/Documents/career/Events/WPI-PRIMe_site_visit_20260903/p14_flash-talk_EJ_20260822.pdf`
and was not itself drafted here. Content spec for the poster: [`00-content_spec_v4.md`](00-content_spec_v4.md).

---

## The pitch

> Good afternoon.
>
> The work displayed at our poster, P-14, today touches on the challenge of
> heterogeneous data integration that we need to solve to enable multi-scale
> bio-digital twins. We have been working on adapting OpenUSD, which is the standard
> the industrial-digital-twin world already converged on. Our goal is to produce an
> extension of OpenUSD called UsdBio, which would follow in the footsteps of the
> existing UsdPhysics for physics simulations, already adopted as an official part of
> OpenUSD. We use the well-known p53–MDM2 system as a testbed for the kind of data a
> real biology study needs to integrate, and so far we have successfully integrated
> six kinds of data from both the molecular scale and the pathway-model scale. I'd be
> happy to walk you through exactly how that integration works, if you'd like a closer
> look at the poster. Thank you for your attention.

## Notes for reuse

- **"Molecular scale," not "molecular dynamics scale."** The p53–MDM2 demo has no MD
  trajectory — only a crystal structure (`examples/p53_mdm2/README.md`, §honesty
  notes). The pitch deliberately says "molecular scale" to describe what is actually
  integrated, without the trajectory implication. The shipped flash-talk PDF's DEMO
  panel says "molecular dynamics to compartment-level," which is looser; if asked
  directly, the honest answer is "not yet — today it's a crystal structure, the MD
  trajectory is next."
- **"Six kinds of data" deliberately echoes the poster's DEMO panel** ("six kinds of
  data going in and out of UsdBio") so the spoken line and the printed slide
  reinforce each other instead of stating the same fact two different ways.
- **UsdBio / UsdPhysics capitalization** follows OpenUSD's own schema-domain naming
  (`Usd<Domain>`), not `USDBio`/`USDPhysics`.
