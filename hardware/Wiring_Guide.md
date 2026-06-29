# Wiring Guide

This guide assumes the corrected architecture in `diagrams/System_Architecture.svg`,
`diagrams/Block_Diagram.svg`, and `diagrams/Circuit_Diagram.svg` — read those first; this document is
the step-by-step build version of what they show.

## 1. Power distribution (do this first, with everything unpowered)

1. Wire the SMPS's 12V rail to both relay modules' COM terminals (these switch the LED arrays).
2. Wire the SMPS's 5V rail to: Raspberry Pi 4B (USB-C), Pico WH (VSYS via diode), ESP8266 (5V/VIN), and
   the OLED/IR/buzzer 5V rails.
3. Tie all grounds (Pi4, Pico, ESP8266, relay modules, OLED mux, IR sensors) to a single common ground
   point — star-ground rather than daisy-chaining, to avoid ground-loop noise on the I2C bus.
4. Wire the 12V 7Ah SLA battery + charger inline with the SMPS output per the charger module's
   instructions, so it floats on the rail and takes over automatically on mains loss.

**Do not** connect the Pi camera to anything in this section — it connects only to the Pi 4B's CSI
port, never to the relay/LED wiring.

## 2. Pico WH → Relay → LED arrays

Follow `diagrams/Circuit_Diagram.svg` for the exact GPIO numbers. In short, for each lane:

| Lane | Green GPIO | Red GPIO | Yellow GPIO | IR GPIO |
|---|---|---|---|---|
| North | GP2 | GP10 | GP14 | GP6 |
| East  | GP3 | GP11 | GP15 | GP7 |
| South | GP4 | GP12 | GP16 | GP8 |
| West  | GP5 | GP13 | GP17 | GP9 |

Each GPIO goes to one relay module input channel; the relay's NO/COM contacts switch 12V to the
corresponding LED color in that lane's signal head, through a 220Ω (red) or 150Ω (yellow/green) current
-limiting resistor as specified in the original hardware spec.

## 3. I2C bus: Pico WH → PCA9548A → 4× OLED

- Pico GP0 (SDA) → mux SDA; GP1 (SCL) → mux SCL.
- Add 4.7kΩ pull-up resistors from SDA and SCL to 3.3V if your mux board doesn't already include them.
- Mux channels 0–3 → one OLED each (all four OLEDs can share the same 0x3C address since the mux
  isolates them onto separate channels).

## 4. IR sensors

Each lane's IR break-beam sensor's digital output goes to that lane's IR GPIO (table above). Power from
the shared 5V rail; most breakout boards include their own onboard regulator/comparator.

## 5. Raspberry Pi 4B + Camera

- Camera ribbon cable → Pi 4B CSI port only.
- Pi 4B connects to the network over its onboard Wi-Fi (or Ethernet, if available at the install site)
  — it does **not** wire to the Pico's circuit at all; the two boards only ever talk over MQTT.

## 6. ESP8266 buzzer node

- Buzzer's positive lead → ESP8266 D1 (GPIO5) through the module's own driver transistor if it's not an
  "active buzzer" module with one built in.
- ESP8266 powered from the shared 5V rail, independent of the Pico.

## 7. Bring-up order

1. Power everything with the Pico's `main.py` *not yet* deployed (or Wi-Fi creds blank) — confirm no
   shorts, nothing overheats, multimeter-check the 5V/12V rails before any board is connected.
2. Flash and boot the Pico WH alone — confirm `all_red()` runs (every lane's red LED lights) as the
   safe default.
3. Bring up the MQTT broker (`docker compose up mosquitto`) and confirm the Pico's heartbeat
   (`traffic/health`) arrives — see `backend/README.md`.
4. Bring up the Pi 4B detection script in `--no-mqtt --show` mode first to visually confirm detection
   before wiring it into the live MQTT topic.
5. Only once 2–4 are confirmed individually, run an end-to-end test: trigger a detection and confirm the
   Pico enters `EMERGENCY_MODE` within the ~1.3s response time discussed in the root README.
