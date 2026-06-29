"""
traffic_controller.py — the traffic-light finite state machine.

This implements the corrected state machine from
diagrams/Traffic_State_Machine.md: a full GREEN -> YELLOW -> next-lane
rotation for all four lanes (the original report's diagram only drew
yellow transitions for two of the four lanes), an all-red clearance
interval before EMERGENCY_MODE grants a lane green (missing from the
original), and a minimum hold + re-check loop once the ambulance lane
is green.

The controller always fails safe: any unhandled exception in the main
loop should result in all_red() being called (see main.py's try/finally).
"""

import time
from machine import Pin

import config

NORMAL_SEQUENCE = [config.LANE_NORTH, config.LANE_EAST, config.LANE_SOUTH, config.LANE_WEST]


def now_ms():
    return time.ticks_ms()


class TrafficController:
    def __init__(self, oled_bank, ir_sensors, mqtt):
        self.oled = oled_bank
        self.ir = ir_sensors
        self.mqtt = mqtt

        self._green = {lane: Pin(p, Pin.OUT, value=0) for lane, p in config.GREEN_PINS.items()}
        self._yellow = {lane: Pin(p, Pin.OUT, value=0) for lane, p in config.YELLOW_PINS.items()}
        self._red = {lane: Pin(p, Pin.OUT, value=1) for lane, p in config.RED_PINS.items()}
        self._buzzer = Pin(config.BUZZER_TRIGGER_PIN, Pin.OUT, value=0)

        self.mode = "NORMAL"          # NORMAL | EMERGENCY
        self.phase = "GREEN"          # GREEN | YELLOW | ALL_RED_CLEARANCE | HOLD
        self.current_lane = config.LANE_NORTH
        self.sequence_index = 0
        self.phase_end_ms = 0
        self.extended_this_phase = False

        self.emergency_lane = None
        self.emergency_recheck_ms = 0

    # ------------------------------------------------------------------ #
    # Low-level signal control
    # ------------------------------------------------------------------ #
    def all_red(self):
        for lane in self._green:
            self._green[lane].value(0)
            self._yellow[lane].value(0)
            self._red[lane].value(1)

    def _set_phase_lights(self, lane, phase):
        for l in self._green:
            self._green[l].value(1 if (l == lane and phase == "GREEN") else 0)
            self._yellow[l].value(1 if (l == lane and phase == "YELLOW") else 0)
            self._red[l].value(0 if l == lane and phase in ("GREEN", "YELLOW") else 1)

    # ------------------------------------------------------------------ #
    # Normal cycle
    # ------------------------------------------------------------------ #
    def start_normal_green(self, lane, now):
        self.mode = "NORMAL"
        self.phase = "GREEN"
        self.current_lane = lane
        self.extended_this_phase = False
        self._set_phase_lights(lane, "GREEN")
        self.phase_end_ms = time.ticks_add(now, config.GREEN_BASE_S * 1000)
        self.oled.show_normal_cycle(lane, config.GREEN_BASE_S, "GREEN")
        self.mqtt.publish_status(lane, "GREEN")

    def start_yellow(self, now):
        self.phase = "YELLOW"
        self._set_phase_lights(self.current_lane, "YELLOW")
        self.phase_end_ms = time.ticks_add(now, config.YELLOW_S * 1000)
        self.mqtt.publish_status(self.current_lane, "YELLOW")

    def advance_to_next_lane(self, now):
        self.sequence_index = (self.sequence_index + 1) % len(NORMAL_SEQUENCE)
        self.start_normal_green(NORMAL_SEQUENCE[self.sequence_index], now)

    def maybe_extend_green(self, now):
        if self.phase != "GREEN" or self.extended_this_phase:
            return
        if self.ir.is_occupied(self.current_lane):
            self.phase_end_ms = time.ticks_add(self.phase_end_ms, config.GREEN_EXTENSION_S * 1000)
            self.extended_this_phase = True
            print("Lane", self.current_lane, "green extended by", config.GREEN_EXTENSION_S, "s")

    def tick_normal(self, now):
        self.maybe_extend_green(now)
        if time.ticks_diff(now, self.phase_end_ms) < 0:
            if self.phase == "GREEN":
                remaining = max(0, time.ticks_diff(self.phase_end_ms, now) // 1000)
                self.oled.show_normal_cycle(self.current_lane, remaining, "GREEN")
            return
        if self.phase == "GREEN":
            self.start_yellow(now)
        else:  # YELLOW expired -> move on
            self.advance_to_next_lane(now)

    # ------------------------------------------------------------------ #
    # Emergency override
    # ------------------------------------------------------------------ #
    def enter_emergency(self, lane, now):
        print("EMERGENCY: overriding for lane", lane)
        self.mode = "EMERGENCY"
        self.phase = "ALL_RED_CLEARANCE"
        self.emergency_lane = lane
        self.all_red()
        self._buzzer.value(1)
        self.phase_end_ms = time.ticks_add(now, config.ALL_RED_CLEARANCE_S * 1000)
        for l in config.LANE_NAMES:
            self.oled.show_lines(l, "EMERGENCY", "Clearing", "intersection...")
        self.mqtt.publish_status(lane, "ALL_RED_CLEARANCE")

    def tick_emergency(self, now, ambulance_still_present):
        if self.phase == "ALL_RED_CLEARANCE":
            if time.ticks_diff(now, self.phase_end_ms) >= 0:
                self.phase = "HOLD"
                self._set_phase_lights(self.emergency_lane, "GREEN")
                self.phase_end_ms = time.ticks_add(now, config.AMBULANCE_GREEN_MIN_S * 1000)
                self.emergency_recheck_ms = time.ticks_add(now, config.EMERGENCY_RECHECK_S * 1000)
            return

        # phase == HOLD
        remaining = max(0, time.ticks_diff(self.phase_end_ms, now) // 1000)
        self.oled.show_emergency(self.emergency_lane, remaining)

        minimum_elapsed = time.ticks_diff(now, self.phase_end_ms) >= 0
        if not minimum_elapsed:
            # Still inside the mandatory AMBULANCE_GREEN_MIN_S window -- never
            # exit, and never shrink phase_end_ms, regardless of detection
            # status. (A prior version of this method re-armed phase_end_ms
            # to "now + EMERGENCY_RECHECK_S" on every recheck tick even
            # during this window, which could cut the minimum hold down to
            # just a few seconds -- see CHANGELOG.md for the writeup.)
            return

        if ambulance_still_present:
            # Minimum has elapsed but the ambulance is still in view: keep
            # rolling the deadline forward in small increments rather than
            # cutting priority the instant the minimum is reached.
            if time.ticks_diff(now, self.emergency_recheck_ms) >= 0:
                self.phase_end_ms = time.ticks_add(now, config.EMERGENCY_RECHECK_S * 1000)
                self.emergency_recheck_ms = time.ticks_add(now, config.EMERGENCY_RECHECK_S * 1000)
            return

        self.exit_emergency(now)

    def exit_emergency(self, now):
        print("EMERGENCY: cleared, resuming normal cycle")
        self._buzzer.value(0)
        self.mode = "NORMAL"
        self.mqtt.publish_status(self.emergency_lane, "EMERGENCY_CLEARED")
        self.emergency_lane = None
        # Always resume at NORTH for a predictable, auditable post-emergency state
        self.sequence_index = 0
        self.start_normal_green(config.LANE_NORTH, now)

    # ------------------------------------------------------------------ #
    # Top-level tick — call once per main-loop iteration
    # ------------------------------------------------------------------ #
    def tick(self, now, emergency_requested_lane, ambulance_still_present):
        if self.mode == "NORMAL" and emergency_requested_lane is not None:
            self.enter_emergency(emergency_requested_lane, now)
            return
        if self.mode == "EMERGENCY":
            self.tick_emergency(now, ambulance_still_present)
            return
        self.tick_normal(now)
