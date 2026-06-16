# M2: Trajectory Playback

## Objective

Attach MD trajectory frames to the assembly topology via Value Clips, enabling time-scrubbing in usdview.

## Success Gates

- Clip files generated from XTC data
- `usdview` timeline scrub shows protein motion
- Topology (bonds, metadata, colors) remains static; only positions change

## Task DAG

```
T1 XTC Converter ----> T2 Trajectory Demo
(converters/)          (demos/)
```

## Dependencies

M1 must be complete (assembly topology USD needed as reference).
