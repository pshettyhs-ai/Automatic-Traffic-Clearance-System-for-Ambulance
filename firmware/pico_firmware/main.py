"""
main.py — entry point for the Pico WH traffic controller.

Run this on boot (rename to `main.py` on the device's filesystem, or
leave as `main.py` if copying the whole pico_firmware/ tree directly).

High-level responsibilities (see diagrams/Main_System_Flow.md):
  1. Bring up Wi-Fi + MQTT.
  2. Initialize OLEDs, relays/LEDs, IR sensors.
  3. Run the control loop: poll MQTT, tick the FSM, refresh displays,
     publish heartbeats — and fail safe to all-red on any crash.

This intentionally keeps the same "ambulance flag -> override -> resume"
behavioural contract as the original Firebase-based script, but every
external dependency (Firebase Auth, REST polling) has been replaced
with MQTT pub/sub, and the FSM itself fixes the safety gaps described
in diagrams/Traffic_State_Machine.md.
"""

import time
import ujson as json

import config
import wifi
from mqtt_client import TrafficMQTT
from oled_driver import OledBank
from sensors import IrSensors
from traffic_controller import TrafficController

# ---------------------------------------------------------------------------
# Shared mutable state updated by MQTT callbacks, read by the main loop.
# Kept as a tiny module-level dict rather than globals scattered everywhere.
# ---------------------------------------------------------------------------
_state = {
    "emergency_lane": None,       # set by on_emergency(), cleared once handled
    "ambulance_present": False,   # latest detection status for the active lane
    "manual_override": None,      # set by on_override(), e.g. {"action": "force_red"}
}


def on_emergency(msg_bytes):
    """
    Callback for TOPIC_EMERGENCY. Expected JSON payload from the Pi 4B:
        {"lane": 3, "confidence": 0.93, "evidence_id": "20260625-101501"}
    """
    try:
        payload = json.loads(msg_bytes)
        lane = int(payload["lane"])
        if lane in config.LANE_NAMES:
            _state["emergency_lane"] = lane
            _state["ambulance_present"] = True
            print("Emergency event received: lane", lane, "conf", payload.get("confidence"))
    except (ValueError, KeyError, TypeError) as e:
        print("Bad emergency payload:", e)


def on_override(msg_bytes):
    """
    Callback for TOPIC_OVERRIDE. Expected JSON payload from the dashboard:
        {"action": "force_red"} | {"action": "clear_emergency"}
    """
    try:
        payload = json.loads(msg_bytes)
        _state["manual_override"] = payload
        print("Manual override received:", payload)
    except ValueError as e:
        print("Bad override payload:", e)


def apply_manual_override(controller):
    override = _state.pop("manual_override", None)
    if not override:
        return
    action = override.get("action")
    if action == "clear_emergency":
        _state["ambulance_present"] = False
    elif action == "force_red":
        controller.all_red()


def main():
    oled = OledBank()
    ir = IrSensors()

    mqtt = TrafficMQTT(on_emergency=on_emergency, on_override=on_override)
    controller = TrafficController(oled_bank=oled, ir_sensors=ir, mqtt=mqtt)

    controller.all_red()
    oled.init_all()
    if wifi.connect():
        mqtt.reconnect_if_needed()

    boot_ms = time.ticks_ms()
    controller.start_normal_green(config.LANE_NORTH, time.ticks_ms())

    next_mqtt_poll = time.ticks_ms()
    next_ir_poll = time.ticks_ms()
    next_health_publish = time.ticks_ms()

    try:
        while True:
            now = time.ticks_ms()

            if time.ticks_diff(now, next_mqtt_poll) >= 0:
                mqtt.reconnect_if_needed()
                mqtt.poll()
                next_mqtt_poll = time.ticks_add(now, config.MQTT_POLL_MS)

            apply_manual_override(controller)

            emergency_lane = _state["emergency_lane"]
            ambulance_present = _state["ambulance_present"]
            controller.tick(now, emergency_lane, ambulance_present)

            # Once the controller has *started* handling an emergency lane,
            # clear the request flag so re-ticking doesn't re-trigger entry —
            # ambulance_present remains the source of truth for "still here?"
            if controller.mode == "EMERGENCY":
                _state["emergency_lane"] = None

            if time.ticks_diff(now, next_health_publish) >= 0:
                uptime_s = time.ticks_diff(now, boot_ms) // 1000
                mqtt.publish_health(uptime_s)
                next_health_publish = time.ticks_add(now, config.HEALTH_PUBLISH_MS)

            time.sleep_ms(5)

    except KeyboardInterrupt:
        pass
    finally:
        # Fail-safe: whatever happens above, never leave the intersection
        # in an ambiguous or all-green state.
        controller.all_red()
        print("Controller stopped — all signals RED (fail-safe).")


if __name__ == "__main__":
    main()
