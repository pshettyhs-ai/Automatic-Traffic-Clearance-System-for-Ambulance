# ESP8266 Firmware — Acoustic Alert Node

## Why this board exists at all

The original report's block diagram showed "Raspberry Pi Wi-Fi / ESP8266" as one ambiguous combined box,
and the hardware list included both an ESP8266 *and* a Pico WH (which already has its own Wi-Fi radio).
Running two independent Wi-Fi stacks to do the same control job is redundant and is one of the
inconsistencies this repository's redesign resolves (see the root README's "Architecture Corrections"
section).

Rather than deleting the ESP8266 from the BOM, it's repurposed here as a **single-purpose acoustic alert
node**: it subscribes to the same `traffic/emergency` MQTT topic as the Pico and independently drives a
buzzer. The benefit of keeping it as a separate board rather than wiring the buzzer straight to the Pico:
a brownout, crash, or reflash of the buzzer logic can never interfere with the safety-critical signal
control firmware running on the Pico.

## Build

Arduino IDE / arduino-cli, board package `esp8266` by ESP8266 Community.

Library dependencies (Library Manager):
- `PubSubClient` by Nick O'Leary
- `ArduinoJson` by Benoit Blanchon (v6.x)

```bash
arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 buzzer_node.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp8266:esp8266:nodemcuv2 buzzer_node.ino
```

## Behavior

- Subscribes to `traffic/emergency` → starts an audible on/off beep pattern.
- Subscribes to `traffic/override` → stops the alert early if the dashboard issues
  `{"action":"clear_emergency"}` or `{"action":"force_red"}`.
- Auto-clears after 30 seconds regardless (matching the Pico's `AMBULANCE_GREEN_MIN_S`), so a dropped
  MQTT message can never leave the buzzer stuck on.

## Status

Compiled against `esp8266` core 3.x locally; **not yet bench-tested against a live broker** in this
revision — validate the MQTT broker reachability and credentials against your own network before
relying on it in a demo.
