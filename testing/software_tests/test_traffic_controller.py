"""
test_traffic_controller.py — unit tests for the Pico WH's traffic-light
finite state machine (firmware/pico_firmware/traffic_controller.py).

traffic_controller.py is MicroPython code: it imports `machine.Pin` and
uses MicroPython-specific `time.ticks_ms/ticks_add/ticks_diff` functions
that don't exist in CPython's `time` module. This test file stubs both
with a small fake clock we control directly, so the FSM logic can be
exercised deterministically on a normal machine with no hardware and no
real wall-clock waiting.

Run from the repo root:
    python testing/software_tests/test_traffic_controller.py
(works standalone; falls back to a plain runner if pytest isn't
installed -- see the __main__ block.)
"""

import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIRMWARE_DIR = REPO_ROOT / "firmware" / "pico_firmware"
sys.path.insert(0, str(FIRMWARE_DIR))


class _FakePin:
    OUT = "OUT"
    IN = "IN"

    def __init__(self, pin, mode=None, value=0):
        self.pin = pin
        self._value = value

    def value(self, v=None):
        if v is None:
            return self._value
        self._value = v


class _FakeClock:
    """Stands in for MicroPython's `time` module. `now` is advanced
    explicitly by the test, not by real wall-clock time."""

    def __init__(self):
        self.now = 0

    def ticks_ms(self):
        return self.now

    def ticks_add(self, a, b):
        return a + b

    def ticks_diff(self, a, b):
        return a - b

    def sleep_ms(self, _ms):
        pass


def _install_stubs(clock):
    machine_module = types.ModuleType("machine")
    machine_module.Pin = _FakePin
    sys.modules["machine"] = machine_module
    sys.modules["time"] = clock


_clock = _FakeClock()
_install_stubs(_clock)

import config  # noqa: E402
import traffic_controller  # noqa: E402


class _FakeOled:
    def show_normal_cycle(self, *a, **k):
        pass

    def show_emergency(self, *a, **k):
        pass

    def show_lines(self, *a, **k):
        pass


class _FakeIr:
    def __init__(self):
        self.occupied_lanes = set()

    def is_occupied(self, lane):
        return lane in self.occupied_lanes


class _FakeMqtt:
    def __init__(self):
        self.published = []

    def publish_status(self, lane, phase):
        self.published.append((lane, phase))


def _make_controller():
    _clock.now = 0
    return traffic_controller.TrafficController(_FakeOled(), _FakeIr(), _FakeMqtt())


def test_boot_default_is_all_red_safe_state():
    ctrl = _make_controller()
    ctrl.all_red()
    assert all(p.value() == 1 for p in ctrl._red.values())
    assert all(p.value() == 0 for p in ctrl._green.values())
    assert all(p.value() == 0 for p in ctrl._yellow.values())


def test_normal_cycle_advances_through_all_four_lanes_with_yellow():
    ctrl = _make_controller()
    ctrl.start_normal_green(config.LANE_NORTH, _clock.now)
    seen_lanes = [ctrl.current_lane]

    # Run for well over a full 4-lane cycle's worth of time.
    full_cycle_ms = (config.GREEN_BASE_S + config.YELLOW_S) * 4 * 1000
    for step in range(0, full_cycle_ms + 5000, 100):
        _clock.now = step
        ctrl.tick(_clock.now, None, False)
        if ctrl.current_lane != seen_lanes[-1]:
            seen_lanes.append(ctrl.current_lane)

    # Should visit North -> East -> South -> West -> North in order.
    assert seen_lanes[:5] == [config.LANE_NORTH, config.LANE_EAST, config.LANE_SOUTH, config.LANE_WEST, config.LANE_NORTH]


def test_emergency_inserts_all_red_clearance_before_green():
    """Regression test for the original report's missing safety interlock:
    the ambulance lane must never go directly from another lane's GREEN to
    its own GREEN with no clearance gap."""
    ctrl = _make_controller()
    ctrl.start_normal_green(config.LANE_NORTH, _clock.now)
    ctrl.tick(_clock.now, emergency_requested_lane=3, ambulance_still_present=True)

    assert ctrl.phase == "ALL_RED_CLEARANCE"
    assert ctrl._green[3].value() == 0, "ambulance lane must not be green during the clearance gap"
    assert all(r.value() == 1 for r in ctrl._red.values()), "every lane must be red during clearance"

    # After the clearance interval elapses, lane 3 should go green.
    _clock.now = config.ALL_RED_CLEARANCE_S * 1000 + 1
    ctrl.tick(_clock.now, None, True)
    assert ctrl.phase == "HOLD"
    assert ctrl._green[3].value() == 1
    assert ctrl._red[3].value() == 0


def test_emergency_hold_respects_mandatory_minimum_even_if_ambulance_leaves_early():
    """Regression test for a real bug found during review: the original
    version of tick_emergency() re-armed phase_end_ms to "now + RECHECK_S"
    on every recheck tick, which could let the system exit emergency mode
    only a few seconds in -- nowhere near AMBULANCE_GREEN_MIN_S (30s) --
    if the ambulance was detected as "gone" right after an early recheck."""
    ctrl = _make_controller()
    ctrl.start_normal_green(config.LANE_NORTH, _clock.now)
    ctrl.tick(_clock.now, emergency_requested_lane=3, ambulance_still_present=True)

    hold_entered_at = None
    exited_at = None
    orig_exit = ctrl.exit_emergency

    def spy_exit(now):
        nonlocal exited_at
        exited_at = now
        orig_exit(now)

    ctrl.exit_emergency = spy_exit

    for step in range(0, 40_000, 50):
        _clock.now = step
        # Ambulance is "seen" for only the first 3 seconds of the HOLD phase.
        ambulance_present = hold_entered_at is None or (step - hold_entered_at) <= 3000
        ctrl.tick(_clock.now, None, ambulance_present)
        if ctrl.phase == "HOLD" and hold_entered_at is None:
            # Capture this *after* tick() so it lines up with the same
            # `now` the controller used internally to set phase_end_ms --
            # capturing it before the call (i.e. one iteration later) would
            # make this test's own measurement lag the controller's actual
            # reference point by one polling interval.
            hold_entered_at = step
        if exited_at is not None:
            break

    assert hold_entered_at is not None, "should have entered HOLD phase"
    assert exited_at is not None, "should eventually exit once the minimum elapses"

    actual_hold_ms = exited_at - hold_entered_at
    minimum_required_ms = config.AMBULANCE_GREEN_MIN_S * 1000
    assert actual_hold_ms >= minimum_required_ms, (
        f"held for only {actual_hold_ms}ms, less than the {minimum_required_ms}ms minimum -- "
        "the early-exit bug has regressed"
    )


def test_emergency_hold_extends_while_ambulance_remains_present_past_minimum():
    ctrl = _make_controller()
    ctrl.start_normal_green(config.LANE_NORTH, _clock.now)
    ctrl.tick(_clock.now, emergency_requested_lane=2, ambulance_still_present=True)

    # Run well past the minimum hold with the ambulance continuously present.
    exited = False
    for step in range(0, config.AMBULANCE_GREEN_MIN_S * 1000 + 20_000, 100):
        _clock.now = step
        ctrl.tick(_clock.now, None, True)
        if ctrl.mode == "NORMAL":
            exited = True
            break

    assert not exited, "must not exit emergency mode while the ambulance is still continuously present"


def test_exit_emergency_always_resumes_at_north():
    ctrl = _make_controller()
    ctrl.start_normal_green(config.LANE_WEST, _clock.now)  # start mid-sequence
    ctrl.tick(_clock.now, emergency_requested_lane=4, ambulance_still_present=True)
    _clock.now = config.ALL_RED_CLEARANCE_S * 1000 + 1
    ctrl.tick(_clock.now, None, False)  # enter HOLD, ambulance already gone
    _clock.now += config.AMBULANCE_GREEN_MIN_S * 1000 + 1
    ctrl.tick(_clock.now, None, False)  # minimum elapsed, ambulance gone -> should exit

    assert ctrl.mode == "NORMAL"
    assert ctrl.current_lane == config.LANE_NORTH


def test_green_extends_at_most_once_per_phase_when_ir_occupied():
    ctrl = _make_controller()
    ctrl.ir.occupied_lanes.add(config.LANE_NORTH)
    ctrl.start_normal_green(config.LANE_NORTH, _clock.now)
    base_end = ctrl.phase_end_ms

    ctrl.tick(100, None, False)
    extended_end = ctrl.phase_end_ms
    assert extended_end == base_end + config.GREEN_EXTENSION_S * 1000

    # A second tick while still occupied must not extend it again.
    ctrl.tick(200, None, False)
    assert ctrl.phase_end_ms == extended_end


if __name__ == "__main__":
    import inspect

    test_fns = [
        obj for name, obj in list(globals().items())
        if name.startswith("test_") and inspect.isfunction(obj)
    ]
    passed = 0
    for fn in test_fns:
        _install_stubs(_FakeClock())  # fresh-ish state per test isn't strictly required here,
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__} -> {e}")
    print(f"\n{passed}/{len(test_fns)} passed")
    sys.exit(0 if passed == len(test_fns) else 1)
