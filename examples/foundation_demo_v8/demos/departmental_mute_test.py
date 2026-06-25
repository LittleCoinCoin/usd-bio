"""
departmental_mute_test.py
=========================
Mute-toggle test: verify each of the 5 departmental sublayers is independently
removable without breaking stage composition.

Protocol: for each sublayer — mute it, assert GetCompositionErrors() empty,
unmute it.  One-at-a-time (not cumulative) so each test is isolated.

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    python3 demos/departmental_mute_test.py
"""

import os
import sys

from pxr import Usd, Sdf


def test_mute_toggle(stage_path: str) -> bool:
    """
    Open stage_path, mute+check+unmute each of the 5 sublayers.
    Returns True if all pass.  Raises AssertionError on first failure.
    """
    stage = Usd.Stage.Open(stage_path)
    root_layer = stage.GetRootLayer()

    sublayer_rel_paths = list(root_layer.subLayerPaths)
    assert len(sublayer_rel_paths) == 5, (
        f"Expected 5 sublayers, got {len(sublayer_rel_paths)}: {sublayer_rel_paths}"
    )

    # Resolve relative paths to absolute identifiers (required by MuteLayer)
    sublayer_ids = [
        Sdf.ComputeAssetPathRelativeToLayer(root_layer, rel)
        for rel in sublayer_rel_paths
    ]

    print(f"Testing mute-toggle on: {stage_path}")
    print(f"  {len(sublayer_ids)} sublayers to test")
    print()

    for sid in sublayer_ids:
        layer_name = os.path.basename(sid)

        # Mute the layer
        stage.MuteLayer(sid)
        errors_after_mute = stage.GetCompositionErrors()
        assert errors_after_mute == [], (
            f"Composition errors after muting {layer_name}: {errors_after_mute}"
        )
        print(f"  PASS: muted {layer_name}, stage valid (errors=[])")

        # Unmute and confirm still clean
        stage.UnmuteLayer(sid)
        errors_after_unmute = stage.GetCompositionErrors()
        assert errors_after_unmute == [], (
            f"Composition errors after unmuting {layer_name}: {errors_after_unmute}"
        )

    print()
    print("PASS: all 5 sublayers independently mutable without composition errors")
    return True


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    stage_path = os.path.join(base_dir, "output", "departmental_demo.usda")

    if not os.path.exists(stage_path):
        print(f"ERROR: stage not found at {stage_path}")
        print("Run demos/departmental_demo.py first to generate the stage.")
        sys.exit(1)

    test_mute_toggle(stage_path)
    sys.exit(0)
