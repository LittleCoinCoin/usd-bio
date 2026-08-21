# design-sync notes — usd-bio / conference_assets

## This repo is outside the design-sync converter's envelope. Do not run the pipeline.

`/design-sync` converts a **compiled React component library** — it installs with the
repo's package manager, bundles the repo's own `dist/` into `_ds_bundle.js`, and emits
per-component `.d.ts` / `.prompt.md` / `.jsx` so the Claude Design *agent* can build UIs
from real components.

This repository has **no `package.json`, no lockfile, no Storybook, no `*.stories.*`, and
no JavaScript at all** — it is a C++/Python OpenUSD project. `conference_assets` is a
static **print** design system: two A0 sheets and a 16:9 slide, whose entire API surface
is CSS custom properties plus `data-*` attributes on a `.sheet` wrapper.

There are no props, no runtime, and nothing to bundle. The skill's escape hatch for
exotic toolchains still requires `package-validate.mjs` to exit clean against the bundle
layout, which cannot exist here.

**Decision (2026-08-16, with Eliott):** upload the preview HTML directly via the
`DesignSync` tool instead. The Design System pane indexes cards from each preview HTML's
first-line `<!-- @dsCard group="…" -->` marker, which `sync.py` already produces.

## Consequences to remember

- The cards are **browsable previews only**. The design agent cannot compose new designs
  from them, because they are print surfaces rather than React components. This is not a
  limitation to fix — composing UIs out of A0 posters is not a thing anyone wants.
- The surfaces are 841–1189 mm wide, so card thumbnails scale down hard and read as tiny
  posters, not as component swatches.
- There is **no `_ds_sync.json` anchor**, so every sync re-uploads everything. Correct and
  honest: the anchor's hash recipe assumes the bundle shape.

## Re-sync procedure

```bash
python3 __canons__/conference_assets/library/sync.py          # rebuild dist/
python3 __canons__/conference_assets/library/sync.py --check  # exits 1 if stale
```

Then upload `library/dist/` plus the canon docs with the `DesignSync` tool
(`finalize_plan` → `write_files`). Project is pinned in `config.json`.

**Never publish the working templates from `library/` directly** — their relative
`<link href="tokens.css">` tags will 404 in a canvas component and every `var()` will
resolve to nothing, rendering an unstyled skeleton that still passes a geometry check.
Only `dist/` is self-contained.

## Other

- `/design-sync` cannot be invoked via the Skill tool (`disable-model-invocation`);
  Eliott must run it himself. The `DesignSync` *tool* is separately available.

## Design-system projects are read-only in the web UI (confirmed 2026-08-16)

Eliott opened the project in Claude Design and tried to edit the templates there; it
reported it needed write access / was read-only. **This is intended behaviour, not a
misconfiguration** — `get_project` reports `canEdit: true` and
`type: PROJECT_TYPE_DESIGN_SYSTEM`, so nothing is broken.

A design-system project is an **input** that designs are built *with*. It is not an
editable document. The source of truth is the repo.

**Round-trip for any change to the templates:**

1. edit `__canons__/conference_assets/library/{tokens,components}.css` or a template
2. `python3 __canons__/conference_assets/library/render.py --all`   (five gates must pass)
3. `python3 __canons__/conference_assets/library/sync.py`           (rebuild `dist/`)
4. `DesignSync` → `finalize_plan` → `write_files` → re-arm `_ds_needs_recompile`

Step 4 needs a fresh `finalize_plan` in each new session — plan tokens do not survive a
context reset. That is one approval per session, not a fault.

**Never edit online even if a future UI allows it:** the repo would silently diverge, and
the next `sync.py` push would overwrite the web edit with no warning.
