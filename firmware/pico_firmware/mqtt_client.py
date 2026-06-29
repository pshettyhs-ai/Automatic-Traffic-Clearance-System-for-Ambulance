"""
mqtt_client.py — thin wrapper around umqtt.simple for the Pico WH.

Replaces the original project's Firebase REST-polling approach
(`fb_get_bool`, `fb_login`, etc.) with a persistent publish/subscribe
session. This removes the original's ~700ms polling latency for the
emergency flag and removes the need to embed a Firebase email/password
pair in firmware source.

Dependency: `umqtt.simple` (bundle it under firmware/libraries/, or
`mip install umqtt.simple` if the board has network access during
provisioning).
"""

import time

from umqtt.simple import MQTTClient

import config


class TrafficMQTT:
    def __init__(self, on_emergency, on_override):
        self._client = None
        self._on_emergency = on_emergency
        self._on_override = on_override
        self.connected = False

    def connect(self):
        self._client = MQTTClient(
            config.MQTT_CLIENT_ID,
            config.MQTT_BROKER_HOST,
            port=config.MQTT_BROKER_PORT,
            keepalive=config.MQTT_KEEPALIVE_S,
        )
        self._client.set_callback(self._dispatch)
        self._client.connect()
        self._client.subscribe(config.TOPIC_EMERGENCY)
        self._client.subscribe(config.TOPIC_OVERRIDE)
        self.connected = True
        print("MQTT: connected and subscribed")

    def _dispatch(self, topic, msg):
        try:
            if topic == config.TOPIC_EMERGENCY:
                self._on_emergency(msg)
            elif topic == config.TOPIC_OVERRIDE:
                self._on_override(msg)
        except Exception as exc:  # noqa: BLE001 - never let a bad payload crash the FSM
            print("MQTT: callback error", exc)

    def poll(self):
        """Non-blocking check for incoming messages. Call frequently from the main loop."""
        if not self.connected:
            return
        try:
            self._client.check_msg()
        except OSError as exc:
            print("MQTT: connection lost", exc)
            self.connected = False

    def publish_status(self, lane, phase):
        self._safe_publish(config.TOPIC_LANE_STATUS, '{"lane":%d,"phase":"%s"}' % (lane, phase))

    def publish_health(self, uptime_s):
        self._safe_publish(
            config.TOPIC_HEALTH, '{"node":"%s","uptime_s":%d}' % (config.MQTT_CLIENT_ID, uptime_s)
        )

    def _safe_publish(self, topic, payload):
        if not self.connected:
            return
        try:
            self._client.publish(topic, payload)
        except OSError as exc:
            print("MQTT: publish failed", exc)
            self.connected = False

    def reconnect_if_needed(self):
        if self.connected:
            return
        try:
            self.connect()
        except OSError as exc:
            print("MQTT: reconnect failed", exc)
            time.sleep_ms(500)
