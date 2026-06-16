# M2.T2: Trajectory Demo

## Goal

Compose topology + clips into a playable scene.

## Creates

`demos/trajectory_demo.py` -> `output/trajectory_demo.usda` + `output/clips/`

## Pre-conditions

M2.T1 complete (clip files exist).

## Success Gates

usdview timeline shows protein moving across frames.

## Steps

| Step | Commit | Description |
|------|--------|-------------|
| S1 | `feat(demos): add trajectory demo with UsdClipsAPI` | Set up UsdClipsAPI on assembly root: clipAssetPaths, clipPrimPath, clipActive, clipTimes. Reference topology. |
| S2 | `test(demos): verify trajectory playback` | Verify frame count, position change between frames, topology integrity. |
