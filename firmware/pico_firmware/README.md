# Pico WH Firmware — Real-Time Traffic Signal Controller

MicroPython firmware for the **Raspberry Pi Pico WH**, responsible for everything that must happen
deterministically and on-device: the traffic light state machine, OLED status displays, IR-based green
extension, and the emergency override. It deliberately does **not** run any computer vision — that runs
on the Raspberry Pi 4B (see `ai_model/inference/`) and reaches this board only as a small MQTT message.

## Why this board does *not* run YOLOv8

A RP2040 has no camera interface fast enough for real-time video and nowhere near the compute budget for
a CNN inference pass. The original report's circuit diagram wired a camera module into the same circuit
as the Pico — this firmware (and `diagrams/Circuit_Diagram.svg`) corrects that: the Pico only ever
receives a small JSON message over MQTT once a detection has already been validated elsewhere.

## File overview

| File | Responsibility |
|---|---|
| `main.py` | Boot sequence + main control loop; the only file you flash as `main.py` |
| `config.py` | All pins, timings, topics, and thresholds — copy to `config_local.py` for real secrets |
| `wifi.py` | Wi-Fi association via the onboard `cyw43` radio |
| `mqtt_client.py` | Persistent pub/sub session (replaces the original Firebase polling) |
| `oled_driver.py` | PCA9548A mux + SSD1306/SH1106 OLED management for 4 lanes |
| `sensors.py` | IR break-beam occupancy sensors |
| `traffic_controller.py` | The corrected finite state machine (see `diagrams/Traffic_State_Machine.md`) |

## Flashing

1. Flash the latest **Pico W/WH MicroPython UF2** from [micropython.org/download/RPI_PICO_W](https://micropython.org/download/RPI_PICO_W/).
2. Copy `firmware/libraries/umqtt/` onto the board's `/lib` folder (bundled here because the board has no
   internet access to `mip install` until Wi-Fi is already configured — a bootstrapping problem).
3. Copy every `.py` file in this folder to the board's root.
4. Edit `config.py` (or add a `config_local.py` and adjust the `import config` lines) with your Wi-Fi
   SSID/password and your MQTT broker's address — see `backend/mqtt/` for bringing up a broker locally.
5. Reset the board. `main.py` runs automatically on boot.

## Validated GPIO map

See `diagrams/Circuit_Diagram.svg` for the full wiring diagram and rationale. Summary:

| Signal | Lane 1 (N) | Lane 2 (E) | Lane 3 (S) | Lane 4 (W) |
|---|---|---|---|---|
| Green  | GP2  | GP3  | GP4  | GP5  |
| Red    | GP10 | GP11 | GP12 | GP13 |
| Yellow | GP14 | GP15 | GP16 | GP17 |
| IR sensor | GP6 | GP7 | GP8 | GP9 |

I2C0 (`GP0`=SDA, `GP1`=SCL) drives the PCA9548A multiplexer (`0x70`) → 4× SSD1306 OLED (`0x3C`).
`GP21` triggers the ESP8266 buzzer node.

## State machine logic is unit-tested against a simulated clock

`traffic_controller.py`'s FSM logic (normal cycling, the all-red clearance gap, and the emergency hold)
is exercised by `testing/software_tests/test_traffic_controller.py`, which stubs `machine.Pin` and
MicroPython's `time.ticks_*` functions so the whole state machine can be driven through a simulated
clock with no real hardware or wall-clock waiting. That suite is what caught a real bug during
development — the emergency-hold minimum duration could be cut from the intended 30 seconds down to
roughly 4 — see `CHANGELOG.md` for the full writeup. Run it yourself:

```bash
python testing/software_tests/test_traffic_controller.py
```

## Known limitations / honest status

- This firmware has been exercised against the bench prototype shown in `images/Prototype_System_Setup.png`
  using a manually-triggered MQTT message standing in for a real Pi 4B detection event — **not yet against
  a live YOLOv8 pipeline end-to-end**. Treat the MQTT contract (topic names + JSON schema in `config.py`)
  as the integration point to validate first when wiring up the real detector.
- `umqtt.simple` does not support TLS on all MicroPython ports; for a production rollout, confirm TLS
  support on your specific Pico W firmware build or terminate TLS at a local broker on the same LAN
  segment instead of exposing MQTT over the public internet in plaintext.
