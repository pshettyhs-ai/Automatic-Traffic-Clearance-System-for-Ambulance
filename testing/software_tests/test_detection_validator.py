"""
test_detection_validator.py — unit tests for the four-gate detection
validation logic in ai_model/inference/detect.py.

These tests stub out the heavy runtime dependencies (ultralytics, paho-mqtt)
since this test only exercises pure validation logic and shouldn't require
a GPU, a camera, or a broker to run in CI.

Run from the repo root:
    pytest testing/software_tests/test_detection_validator.py -v
"""

import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFERENCE_DIR = REPO_ROOT / "ai_model" / "inference"
sys.path.insert(0, str(INFERENCE_DIR))

# Stub heavy/optional deps so `import detect` succeeds in a plain test env.
sys.modules.setdefault("ultralytics", types.SimpleNamespace(YOLO=lambda *a, **k: None))
_paho = types.ModuleType("paho")
_paho_mqtt = types.ModuleType("paho.mqtt")
_paho_mqtt_client = types.SimpleNamespace(Client=lambda *a, **k: None, MQTTv311=4)
sys.modules.setdefault("paho", _paho)
sys.modules.setdefault("paho.mqtt", _paho_mqtt)
sys.modules.setdefault("paho.mqtt.client", _paho_mqtt_client)

import detect  # noqa: E402

FRAME_SHAPE = (480, 640, 3)
GOOD_BOX = (250, 250, 350, 350)  # 100x100 = 10,000px^2 -> ~0.0326 of 307,200px frame, inside the zone


def test_low_confidence_rejected():
    fv = detect.FrameValidator()
    record = fv.evaluate(0.5, GOOD_BOX, FRAME_SHAPE)
    assert record.failure_reason == "low_confidence"
    assert record.passed_all_gates is False


def test_bbox_too_small_rejected():
    fv = detect.FrameValidator()
    record = fv.evaluate(0.95, (300, 300, 302, 302), FRAME_SHAPE)
    assert record.failure_reason == "size_out_of_range"


def test_bbox_too_large_rejected():
    fv = detect.FrameValidator()
    record = fv.evaluate(0.95, (0, 0, 640, 480), FRAME_SHAPE)
    assert record.failure_reason == "size_out_of_range"


def test_outside_detection_zone_rejected():
    fv = detect.FrameValidator()
    # Properly sized box, but positioned above the zone (zone y_min = 0.35 * 480 = 168px)
    record = fv.evaluate(0.95, (250, 5, 360, 60), FRAME_SHAPE)
    assert record.failure_reason == "outside_detection_zone"


def test_single_good_frame_awaits_confirmation():
    fv = detect.FrameValidator()
    record = fv.evaluate(0.9, GOOD_BOX, FRAME_SHAPE)
    assert record.failure_reason == "awaiting_multi_frame_confirmation"
    assert record.passed_all_gates is False


def test_third_consecutive_good_frame_confirms():
    fv = detect.FrameValidator()
    records = [fv.evaluate(0.9, GOOD_BOX, FRAME_SHAPE) for _ in range(3)]
    assert records[0].failure_reason == "awaiting_multi_frame_confirmation"
    assert records[1].failure_reason == "awaiting_multi_frame_confirmation"
    assert records[2].passed_all_gates is True
    assert records[2].failure_reason == ""


def test_confirmation_does_not_carry_across_unrelated_frames():
    """Two good frames followed by three bad ones should never reach
    confirmation — the rolling window should not let stale good frames
    confirm a much later, unrelated detection."""
    fv = detect.FrameValidator()
    fv.evaluate(0.9, GOOD_BOX, FRAME_SHAPE)
    fv.evaluate(0.9, GOOD_BOX, FRAME_SHAPE)
    for _ in range(3):
        record = fv.evaluate(0.5, GOOD_BOX, FRAME_SHAPE)  # low confidence
    assert record.failure_reason == "low_confidence"

    # A new good frame right after should again need fresh confirmations,
    # not instantly pass on the strength of the old (now-evicted) frames.
    record = fv.evaluate(0.9, GOOD_BOX, FRAME_SHAPE)
    assert record.passed_all_gates is False


def test_point_in_polygon_helper():
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert detect._point_in_polygon((0.5, 0.5), square) is True
    assert detect._point_in_polygon((1.5, 0.5), square) is False


if __name__ == "__main__":
    try:
        import pytest

        sys.exit(pytest.main([__file__, "-v"]))
    except ImportError:
        # No pytest in this environment -- fall back to a plain runner so
        # this file is still directly executable with `python this_file.py`.
        import inspect

        test_fns = [
            obj for name, obj in list(globals().items())
            if name.startswith("test_") and inspect.isfunction(obj)
        ]
        passed = 0
        for fn in test_fns:
            try:
                fn()
                print(f"PASS: {fn.__name__}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL: {fn.__name__} -> {e}")
        print(f"\n{passed}/{len(test_fns)} passed")
        sys.exit(0 if passed == len(test_fns) else 1)
