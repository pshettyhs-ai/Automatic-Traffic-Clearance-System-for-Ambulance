"""
wifi.py — Wi-Fi connection helper for the Pico WH (cyw43 radio).
"""

import time
import network

import config


def connect():
    sta = network.WLAN(network.STA_IF)
    if not sta.active():
        sta.active(True)
    if not sta.isconnected():
        print("Wi-Fi: connecting to", config.WIFI_SSID)
        sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        deadline = time.time() + config.WIFI_CONNECT_TIMEOUT_S
        while not sta.isconnected() and time.time() < deadline:
            time.sleep(0.25)
    ok = sta.isconnected()
    print("Wi-Fi:", "connected, ip=" + sta.ifconfig()[0] if ok else "FAILED to connect")
    return ok
