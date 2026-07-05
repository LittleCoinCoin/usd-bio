2026-07-04T07:08:10.092234+00:00
Reporting several broken output files:
- None of the clips in `examples/foundation_demo_v8/output/clips/` can be played in `usdview` --> Play button is not working
- `examples/foundation_demo_v8/output/clips/clip.001.usdc`, `examples/foundation_demo_v8/output/clips/clip.002.usdc`, `examples/foundation_demo_v8/output/clips/trajectory_clip.usda`, and `examples/foundation_demo_v8/output/clips/trajectory_clip.usdc` are all apearing as grey bloc cylinders, not visualizable as all the other variants using balls or sticks in other output files. And ther are also fully statis. So basically these clips are non-functional in `usdview`.

if the above was intended, they this must be documented somewhere so that we know how to run the demos and clips

Additionally, `examples/foundation_demo_v8/output/curves_demo.usda` in `usdview` is bugged. The trajectories are applied to the systems using curves for display, while still keeps the possibility to switch to different variants including balls and sticks. But if we select any of the variants it appears at the wrong location and simultanuously displays both the curved version (with the trajectories properly applied on the curved version when clicking "Play" button in `usdview`)

If these were remnants of prior tests that were wrongly created, we must clean them. Otherwise, we must find out why these demos are broken and document the errors as well as automated debug cycle that LLM-agents can take to check these rather than me discovering these issues at the last minute when starting up `usdview`

