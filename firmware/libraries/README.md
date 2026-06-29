# firmware/libraries/

External MicroPython libraries needed on the Pico WH that aren't part of the standard firmware build.

## umqtt.simple

The Pico firmware (`firmware/pico_firmware/mqtt_client.py`) depends on `umqtt.simple`, the standard
lightweight MQTT client from [micropython-lib](https://github.com/micropython/micropython-lib).

This repository does **not** vendor a copy of the library source here, to avoid shipping a stale or
subtly-modified fork under this project's license. Install it one of these ways:

**Option A — over-the-air (once Wi-Fi is already configured on the board):**
```python
import mip
mip.install("umqtt.simple")
```

**Option B — offline, via `mpremote` from a dev machine with internet access:**
```bash
mpremote mip install umqtt.simple
mpremote cp -r ~/.micropython/lib/umqtt :lib/umqtt
```

**Option C — manual download:** grab `umqtt/simple.py` directly from the
[micropython-lib GitHub repository](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple)
and copy it to `/lib/umqtt/simple.py` on the board's filesystem.

## ssd1306 / sh1106_i2c

`oled_driver.py` tries `ssd1306` first and falls back to `sh1106_i2c`. The former ships with most Pico W
MicroPython builds already; the latter (for SH1106-controller OLEDs sometimes substituted in by
suppliers) can be installed the same way as above, substituting the package name.
