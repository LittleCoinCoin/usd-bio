# Render spike notes (W3)

Findings from getting `usdrecord` to actually rasterize
`examples/p53_mdm2/demos/p53_mdm2_integrated.usda`, on this machine
(macOS Darwin 25.5.0, Apple M3 Pro, local console session, DELL U4323QE +
built-in display attached). All numbers below are real measured output from
this session, not projections.

## 1. Offscreen Storm/GL rendering WORKS here, unmodified, in a real console session

No workaround was needed. The absolute-path binary renders successfully with
the GPU (default path):

```bash
PYTHONPATH=/Users/hacker/Documents/bin/OpenUSD/lib/python \
  /Users/hacker/Documents/bin/OpenUSD/bin/usdrecord \
  --renderer Storm \
  --sessionLayer /tmp/p53_session_XXXX.usda \
  --camera /RenderCamera \
  --imageWidth 2560 \
  --complexity high \
  examples/p53_mdm2/demos/p53_mdm2_integrated.usda \
  out.png
```

where the session layer carries an `over "/p53_MDM2_complex"` with a
`representation` variant selection plus the authored `/RenderCamera`. This
is exactly what `render_support.render()` in this directory constructs and
runs. Verified end to end via `render_support.render(...)` for
`representation` in `{"points", "vdw", "ballstick"}` at width 2560 (and 640
for a quick smoke test) — every run exited 0 and produced a correctly-sized
PNG.

**`--disableGpu` is NOT needed and, on this build, actively breaks rendering:**

```
$ usdrecord --renderer Storm --disableGpu ... 
Error in 'UsdImagingGLEngine::SetRendererPlugin' ... 'Invalid plugin id '
Error in 'UsdImagingGLEngine' ... 'No renderer plugins found!'
```

This build of OpenUSD 0.25.11 only has the Storm/GL Hydra plugin registered
— there is no CPU-only (e.g. Embree) renderer plugin available, so
`--disableGpu` leaves zero usable renderer plugins and usdrecord fails
immediately (exit 1, ~0.5s). The working path is GPU-backed Storm, which
means **this specific result is conditioned on the console session having
real GPU/display access** (Apple M3 Pro, an attached display). Whether
offscreen Storm rendering also works over SSH / in a headless CI runner on
this same machine was NOT tested here and should not be assumed from this
result — the module raises a clear `RenderError` (subprocess stderr
included) rather than hanging or silently producing nothing if that
assumption turns out to be wrong in a different environment.

## 2. Gate 1 — representation-variant selection: confirmed cascade defect + fix

Naive open, no session layer:

```
Sphere count: 0
Cylinder count: 834
```

Same file, `Usd.Stage.Open(rootLayer, sessionLayer)` where the session layer
is `render_support.build_representation_session_layer("ballstick")`:

```
Sphere count: 818
Cylinder count: 834
```

Confirms obstacle 1 from the brief exactly: zero atoms render by default; a
single `over` on `/p53_MDM2_complex` selecting a `representation` variant is
sufficient (the cascade authored in `builders/build_assembly.py` already
propagates the selection down through chain -> residue -> atom/bond via each
level's own `VariantEditContext`, so no per-atom session-layer opinion is
needed — one `over` at the root does it).

## 3. Gate 2 — exact pixel size, and an aperture-ratio reconciliation

`render_support.render(..., width=2560, representation="vdw")` (default
aperture ratio) produces a PNG measured by PIL at exactly **(2560, 768)**.

This took one round of correction. The brief's aperture ratio (3.3336,
quoted from `214.94 / 64.48` mm) and its pixel target (2560 x 768) are not
bit-exact reciprocals of each other:

```
214.94 / 64.48        = 3.33344 (quoted as 3.3336)
2560 / 3.3336          = 767.945
```

`usdrecord` derives image height from `imageWidth / camera aspect ratio` by
**truncation, not rounding** — empirically confirmed: a camera built with
`horizontalAperture/verticalAperture = 3.3336` renders **767px tall**, one
pixel short:

```
using ratio 3.3336...  -> size=(2560, 767)
using ratio 2560/768   -> size=(2560, 768)
```

The two given numbers agree to 4 significant figures (~0.03% difference,
invisible at poster print size), so `render_support.POSTER_APERTURE_RATIO`
is defined as `2560 / 768` exactly (the pixel-exact form) rather than the
quoted `3.3336`, with the originally-quoted ratio kept alongside as
`POSTER_APERTURE_RATIO_MEASURED` for provenance. This is the one spec
imprecision worth flagging explicitly: **the two "given" numbers are only
approximately consistent, not exact reciprocals**, and hitting an
exact-pixel gate with an integer-truncating renderer requires picking the
pixel-derived ratio, not the mm-derived one.

## 4. Gate 3 — atoms are actually in the framebuffer, not just on the stage

Same camera, same session-layer machinery, two representations:

```
mean abs pixel diff (0-255 scale) = 15.4877
corner bg (points): [0. 0. 0.]   corner bg (vdw): [0. 0. 0.]
non-background pixel fraction: points=2.1152%   vdw=14.8469%
```

(Note: the corner-pixel "background" sampled as `[0,0,0]` is a min-alpha
artifact of the naive corner-pixel sampling against the actual white Storm
clear color visible in the images below — see the two committed/verified
renders — the *fraction* comparison is what carries the evidence, not the
absolute color value, and it moves in the expected direction: `vdw`'s
much larger sphere radii, `RADIUS_SCALES["vdw"]=1.00` vs.
`RADIUS_SCALES["points"]=0.15` in `data/element_properties.py`, cover ~7x
more of the frame.)

Both PNGs were also inspected visually (not just diffed numerically):
`points` shows ~818 small individually-separated CPK-colored dots (grey C,
blue N, red O, yellow S) in the complex's silhouette; `vdw` shows a dense,
correctly colored space-filling blob, same silhouette, same camera. This is
real rendered geometry, not an empty frame or a stage-only illusion.

Full-resolution probes were written to a scratch temp directory during this
spike and were NOT committed (see the "commit hygiene" note in the module
docstring / task brief). One downscaled (512x154) proof image is committed
here: `render_probe_vdw_thumb.png`.

## 5. Summary of what a caller of `render_support.py` gets

- `build_representation_session_layer(representation, ...)` — an `over` with
  a `representation` variant selection (+ optional `displayColor` overrides,
  for a later item's accent-highlight need), written to a temp `.usda`.
- `author_camera(stage_path, session_layer_path, aperture_ratio, ...)` —
  adds a `UsdGeomCamera` to that (or any) session layer, framed from the
  REAL composed bbox via `UsdGeom.BBoxCache` (measured against the `vdw`
  mode's geometry by default, since it is the largest — a camera fit to
  `points` would clip `vdw`'s bigger spheres).
- `build_render_session_layer(...)` — combines the two into one file (only
  one `--sessionLayer` argument is accepted by `usdrecord`).
- `render(stage_path, out_png, width, representation, ...)` — runs the
  absolute-path `usdrecord` with `--renderer Storm` and that merged session
  layer; raises `RenderError` (with the full command line and captured
  stdout/stderr) if the process exits non-zero OR the output file is
  missing afterward.
- `count_prims_of_type(stage, type_name)` / `open_stage_with_representation`
  — the gate-1-style helpers used above.

No `usdview`-screenshot fallback recipe is needed for this item: offscreen
rendering worked directly.
