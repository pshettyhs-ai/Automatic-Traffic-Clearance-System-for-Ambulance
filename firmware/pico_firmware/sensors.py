"""
sensors.py — IR break-beam occupancy sensors, one per lane.
"""

from machine import Pin

import config


class IrSensors:
    def __init__(self):
        self._pins = {lane: Pin(pin, Pin.IN) for lane, pin in config.IR_PINS.items()}

    def is_occupied(self, lane):
        value = self._pins[lane].value()
        return (value == 1) if config.IR_ACTIVE_HIGH else (value == 0)
