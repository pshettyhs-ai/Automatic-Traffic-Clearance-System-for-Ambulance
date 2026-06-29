# Wokwi Simulation — Pico WH Signal Controller

A browser-runnable simulation of the **signal-control side only** (`firmware/pico_firmware`) — Wokwi has
no camera/CV simulation capability, so the YOLOv8 detection pipeline isn't part of this sim. Use it to
exercise the traffic-light state machine and OLED displays without any physical hardware.

## Running it

1. Go to [wokwi.com](https://wokwi.com/), create a new "Raspberry Pi Pico W" MicroPython project.
2. Copy `diagram.json` from this folder into the Wokwi project (or open this repo in VS Code with the
   [Wokwi extension](https://marketplace.visualstudio.com/items?itemName=wokwi.wokwi-vscode), which
   reads `wokwi.toml` directly).
3. Copy the contents of `firmware/pico_firmware/` into the simulated filesystem.
4. Since Wokwi has no real network, **comment out the `wifi.connect()` / MQTT calls in `main.py`** for
   simulation purposes, or stub `mqtt_client.py`'s `connect()` to always return `False` — the controller
   is designed to keep running its local timer-based FSM even without a network connection
   (see `traffic_controller.py`), so the simulation still demonstrates the full normal-cycle and (via the
   pushbuttons wired as IR-sensor stand-ins) green-extension behavior.
5. To simulate an emergency override without MQTT, call
   `controller.tick(now, emergency_lane=3, ambulance_present=True)` directly from a temporary test loop
   in `main.py`, or trigger it from the Wokwi serial console.

## What this simulation does and doesn't prove

**Does:** validates the GPIO pin map, the LED on/off logic per phase, the OLED text rendering, and the
core state machine transitions (including the corrected all-red clearance gap — watch for the brief
moment all 12 LEDs are off-then-red before the ambulance lane goes green).

**Doesn't:** validate I2C timing against real SSD1306 hardware (Wokwi's `wokwi-ssd1306` part is a
behavioral model, not a timing-accurate one), validate MQTT round-trip behavior, or involve the YOLOv8
detection pipeline at all.

## Proteus

`simulations/proteus/` is an intentionally empty placeholder — no `.pdsprj` file is included in this
revision. Proteus's MCU simulation for RP2040 is limited compared to Wokwi's, so Wokwi was used here
instead; a Proteus project mainly adds value if you need SPICE-accurate analog simulation of the
LED-driver/relay section, which hasn't been built out yet.
