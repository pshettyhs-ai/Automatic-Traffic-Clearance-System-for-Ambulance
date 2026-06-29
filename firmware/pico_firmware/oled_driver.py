"""
oled_driver.py — PCA9548A multiplexer + SSD1306 OLED management.

Refactored from the original project's monolithic script. The original
init logic is preserved (probe each mux channel, try SSD1306 then fall
back to SH1106, retry once on OSError) because it was already a sound,
field-tested approach -- it's just been pulled out of the main loop and
given a clean class interface.
"""

import time
from machine import Pin, I2C

import config


class OledBank:
    """Manages up to 4 OLED displays behind a PCA9548A I2C multiplexer."""

    def __init__(self):
        self.i2c = I2C(
            config.I2C_ID,
            sda=Pin(config.I2C_SDA_PIN),
            scl=Pin(config.I2C_SCL_PIN),
            freq=config.I2C_FREQ_HZ,
        )
        self.displays = {}  # lane -> driver instance
        self._ssd1306_ok = True
        self._sh1106_ok = True
        try:
            import ssd1306  # noqa: F401
        except ImportError:
            self._ssd1306_ok = False
        try:
            import sh1106_i2c  # noqa: F401
        except ImportError:
            self._sh1106_ok = False

    # -- low level mux control -------------------------------------------------
    def _select(self, channel):
        self.i2c.writeto(config.MUX_I2C_ADDR, bytes([1 << channel]))
        time.sleep_us(config.MUX_SETTLE_US)

    def _disable_all(self):
        self.i2c.writeto(config.MUX_I2C_ADDR, b"\x00")
        time.sleep_us(50)

    def _make_display(self, channel, addr):
        import ssd1306
        import sh1106_i2c

        for width, height in ((config.OLED_WIDTH, config.OLED_HEIGHT), (128, 32)):
            if self._ssd1306_ok:
                try:
                    self._select(channel)
                    d = ssd1306.SSD1306_I2C(width, height, self.i2c, addr=addr)
                    d.fill(0)
                    d.text("READY", 0, 0)
                    d.show()
                    return d
                except OSError:
                    pass
            if self._sh1106_ok:
                try:
                    self._select(channel)
                    d = sh1106_i2c.SH1106_I2C(width, height, self.i2c, addr=addr)
                    d.fill(0)
                    d.text("READY", 0, 0)
                    d.show()
                    return d
                except OSError:
                    pass
        return None

    def init_all(self):
        self._disable_all()
        for lane, channel in config.OLED_MUX_CHANNELS.items():
            self._select(channel)
            present = self.i2c.scan()
            target_addr = next((a for a in config.OLED_I2C_ADDRS if a in present), None)
            if target_addr is None:
                print("WARN: no OLED found on lane", lane, "(channel", channel, ")")
                continue
            d = self._make_display(channel, target_addr)
            if d:
                self.displays[lane] = d
            else:
                print("WARN: OLED present but driver init failed on lane", lane)
            self._disable_all()

    # -- drawing -----------------------------------------------------------
    def _draw(self, lane, draw_fn):
        d = self.displays.get(lane)
        if not d:
            return
        channel = config.OLED_MUX_CHANNELS[lane]
        for attempt in range(2):
            try:
                self._select(channel)
                draw_fn(d)
                d.show()
                self._disable_all()
                return
            except OSError:
                time.sleep_ms(2)
                self.init_all()
                d = self.displays.get(lane)
                if not d:
                    return

    def show_lines(self, lane, line1="", line2="", line3="", line4=""):
        def _draw(d):
            d.fill(0)
            if line1:
                d.text(line1, 0, 0)
            if line2:
                d.text(line2, 0, 16)
            if line3:
                d.text(line3, 0, 32)
            if line4:
                d.text(line4, 0, 48)

        self._draw(lane, _draw)

    def show_normal_cycle(self, current_lane, remaining_s, phase):
        for lane in config.LANE_NAMES:
            name = config.LANE_NAMES[lane]
            if lane == current_lane:
                self.show_lines(lane, f"Lane {lane}: {phase}", f"T: {int(remaining_s):>3}s")
            else:
                self.show_lines(lane, f"Lane {lane}: RED", "Waiting...")

    def show_emergency(self, ambulance_lane, remaining_s):
        for lane in config.LANE_NAMES:
            if lane == ambulance_lane:
                self.show_lines(lane, "EMERGENCY", f"Lane {lane} GREEN", f"T: {int(remaining_s):>3}s")
            else:
                self.show_lines(lane, "EMERGENCY", "Hold - RED", "Clearing path")
