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

(Note: the corner-pixel "background" sampled as `[0,0,0]` is the RGB channel
value of an RGBA(0,0,0,0) pixel — i.e. the background is genuinely
**transparent**, not white. `Image.open(...).convert("RGB")` drops the alpha
channel and keeps the underlying (0,0,0) color that sat behind it, which is
why the sampled corner reads black even though the images look white when
viewed or composited over a white page/canvas. The transparency itself is
correct and load-bearing for the poster (it composites over whatever poster
background color surrounds the figure slot), so this is not a defect to fix
— just a wording correction from an earlier draft of these notes, which
wrongly described the clear color as "white." The *fraction* comparison
below is what carries the evidence, not the absolute sampled color, and it
moves in the expected direction: `vdw`'s much larger sphere radii,
`RADIUS_SCALES["vdw"]=1.00` vs. `RADIUS_SCALES["points"]=0.15` in
`data/element_properties.py`, cover ~7x more of the frame.)

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

## 6. Adversarial-verification round: two real defects, fixed

An independent adversarial pass first confirmed the framing itself is
correct — a known-radius sphere rendered through the exact `render()` /
`author_camera()` path came back 674x674px at ratio 1.00000 (no distortion),
and an anisotropic sphere grid showed identical world-unit-to-pixel scale in
X and Y (no clipping) — and confirmed the aperture reconciliation in §3
above, including the truncation claim. It then found two real defects in
`render_support.py`, both fixed on this branch:

**Defect 1 — `camera_representation` was unvalidated and failed silently.**
`representation` (the render mode) already raised `ValueError` against
`DEFAULT_REPRESENTATIONS`; `camera_representation` (which mode's bbox sizes
the camera) did not. Passing garbage let `SetVariantSelection("bogus")`
resolve to nothing, so `author_camera`'s bbox got measured off whatever
geometry survives an UNSELECTED representation cascade — just the 834 bond
Cylinders, not the 818 atoms. The verifier showed this silently shrank the
top margin from 5.9% to 1.6% of frame height with no signal to the caller;
it didn't clip yet, but was one padding change away from doing so. Fixed by
adding the identical guard to `author_camera`, so every path that can reach
it (`author_camera` directly, `build_render_session_layer`, `render`) now
raises `ValueError` immediately instead of quietly under-framing. Gate
(`defect1_gate.py`, run against this branch):

```
PASS (1a): author_camera raised ValueError: Unknown representation 'bogus_mode'; use one of ('points', 'balls', 'vdw', 'ballstick')
PASS (1b): build_render_session_layer raised ValueError: Unknown representation 'bogus_mode'; use one of ('points', 'balls', 'vdw', 'ballstick')
PASS (1c): render() raised ValueError before ever invoking usdrecord: Unknown representation 'bogus_mode'; use one of ('points', 'balls', 'vdw', 'ballstick')
DEFECT 1 GATE: ALL PASS
```

**Defect 2 — the temp session-layer file leaked on error paths.**
`build_render_session_layer()` called `build_representation_session_layer()`
(which unconditionally writes and saves a temp `.usda`) and only then called
`author_camera()` (which can raise: invalid `root_path`, nonexistent
`stage_path`, an empty-bbox `RuntimeError`, or — post-Defect-1 — a bad
`camera_representation`). `render()`'s own `try/finally` cleanup wrapped only
`subprocess.run`, by which point the temp file already existed, so an
exception raised during the *build* step leaked it permanently. The verifier
reproduced this twice and also found two pre-existing leaked files already
sitting in the OS temp dir from earlier real (non-test) usage — one of them
carrying a `ballstick` selection plus a red `Chain_A` `displayColor`
override, i.e. real session-layer content from an actual prior run, not a
test artifact. Those stale files were removed from `/tmp` as part of this
fix; they were not committed (they were never inside the repo).

Fixed with a context manager, `_temp_session_layer_path()`, that owns the
temp file's lifetime across the *whole* build-and-render sequence rather
than just the subprocess call: it allocates (or accepts) the path, yields
it, and on any exception removes the file before re-raising; on a clean
exit it leaves the file alone so ownership transfers to the caller (`render()`
still deletes it after `usdrecord` runs, success or failure, via its
existing `try/finally`). `build_render_session_layer()` now runs both
authoring calls inside that context manager instead of calling them
bare. Gate (`defect2_gate.py`, run against this branch — polled
`glob.glob(os.path.join(tempfile.gettempdir(), "p53_session_*.usda"))`
before/after each forced failure):

```
build_render_session_layer raised as expected: '/This/Prim/Does/Not/Exist' not found on '.../demos/p53_mdm2_integrated.usda'
PASS (2a): no new p53_session_*.usda survived author_camera raising via bad root_path
build_render_session_layer raised as expected (bad camera_representation): Unknown representation 'bogus_mode'; use one of ('points', 'balls', 'vdw', 'ballstick')
PASS (2b): no new p53_session_*.usda survived a bogus camera_representation raise either
PASS (2c): success path still returns a surviving file: /var/folders/.../T/p53_session_pf3gb09c.usda
DEFECT 2 GATE: ALL PASS
```

(2c) exists specifically to prove the fix didn't overcorrect into deleting
the file on the *success* path too — `build_render_session_layer` still
hands back a real, surviving file for `render()` to use and then clean up.

The original gates 1–3 (§2–§4 above) were re-run against this same fixed
file to confirm the context-manager refactor didn't regress the working
path: `Sphere=818 Cylinder=834`, and a fresh `render()` call still produces
an exact `(2560, 768)` PNG.

## 7. Two properties to record, not fix

**(a) Renders are NOT byte-deterministic.** Two back-to-back, otherwise
identical `render()` calls (same stage, same session layer content, same
camera) differed in 2 of 122,880 pixels, max single-channel delta 26/255 —
ordinary GPU anti-aliasing jitter on edge pixels, invisible at print size.
Nothing in this module or these notes claims otherwise, but it's worth
saying explicitly for whoever writes the next gate: **do not assert
byte-identity between two independently-rendered rasters of the same
scene.** A `hash(png_bytes_a) == hash(png_bytes_b)` gate on this renderer
will flake. A perceptual/statistical comparison (mean-abs-diff under a small
threshold, as gate 3 already does in the *other* direction — asserting
substantial difference between genuinely different renders) is the correct
shape; treat "nearly identical, small bounded delta" as the pass condition
for "these should look the same," never bitwise equality.

**(b) `fov_deg=50` (vertical) combined with the 3.333 aperture ratio is an
extreme wide-angle lens — roughly 115° horizontal FOV.** `author_camera`'s
default `fov_deg=50.0` is a *vertical* field of view; at the poster's
`aperture_ratio ≈ 3.333`, the corresponding horizontal FOV works out to
roughly 115°, well into fisheye territory for a "photographic" framing. This
is currently harmless: the complex sits on-axis and centered, on-axis
spheres stay circular regardless of FOV, so the current framing shows no
visible distortion. But it is a **latent constraint on any future framing
change**: the verifier measured an off-axis sphere near the frame edge
stretching to a width/height ratio of 1.59 — genuine perspective distortion,
not a bug, that gets worse toward the frame edges and would become visible
the moment a future figure crops tighter, off-centers the subject, or
otherwise pushes content toward the edges of this very wide frame. If a
later item needs edge content to stay undistorted, lower `fov_deg` (a
longer, more "orthographic-feeling" lens) rather than widening the frame
further at `fov_deg=50`.
