"""
config.py — Central configuration for the Pico WH traffic controller.

All tunables live here so the rest of the firmware never hardcodes a pin
number, timing constant, or network credential. Copy this file to
`config_local.py` (gitignored) with your real Wi-Fi/MQTT credentials and
import from there in production — keeping secrets out of version control.
"""

# ---------------------------------------------------------------------------
# Wi-Fi
# ---------------------------------------------------------------------------
WIFI_SSID = "traffic-iot"
WIFI_PASSWORD = "change-me"
WIFI_CONNECT_TIMEOUT_S = 25

# ---------------------------------------------------------------------------
# MQTT (replaces the original Firebase REST-polling design)
# ---------------------------------------------------------------------------
MQTT_BROKER_HOST = "192.168.1.10"     # backend / broker IP on the local network
MQTT_BROKER_PORT = 1883               # use 8883 + TLS in production
MQTT_CLIENT_ID = "pico-junction-01"
MQTT_KEEPALIVE_S = 30

TOPIC_EMERGENCY = b"traffic/emergency"     # Pi4 -> Pico  (ambulance detected)
TOPIC_OVERRIDE = b"traffic/override"       # Dashboard -> Pico (manual control)
TOPIC_LANE_STATUS = b"traffic/lane/status"  # Pico -> Backend (current FSM state)
TOPIC_HEALTH = b"traffic/health"           # Pico -> Backend (heartbeat)

# ---------------------------------------------------------------------------
# GPIO pin map — validated against the working firmware, every pin unique.
# See diagrams/Circuit_Diagram.svg for the full wiring rationale.
# ---------------------------------------------------------------------------
LANE_NORTH, LANE_EAST, LANE_SOUTH, LANE_WEST = 1, 2, 3, 4
LANE_NAMES = {LANE_NORTH: "NORTH", LANE_EAST: "EAST", LANE_SOUTH: "SOUTH", LANE_WEST: "WEST"}

GREEN_PINS = {LANE_NORTH: 2, LANE_EAST: 3, LANE_SOUTH: 4, LANE_WEST: 5}
RED_PINS = {LANE_NORTH: 10, LANE_EAST: 11, LANE_SOUTH: 12, LANE_WEST: 13}
YELLOW_PINS = {LANE_NORTH: 14, LANE_EAST: 15, LANE_SOUTH: 16, LANE_WEST: 17}
IR_PINS = {LANE_NORTH: 6, LANE_EAST: 7, LANE_SOUTH: 8, LANE_WEST: 9}
IR_ACTIVE_HIGH = True

BUZZER_TRIGGER_PIN = 21

# I2C bus shared by the PCA9548A multiplexer -> 4x SSD1306 OLEDs
I2C_ID = 0
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
I2C_FREQ_HZ = 100_000
MUX_I2C_ADDR = 0x70
OLED_I2C_ADDRS = (0x3C, 0x3D)
OLED_MUX_CHANNELS = {LANE_NORTH: 0, LANE_EAST: 1, LANE_SOUTH: 2, LANE_WEST: 3}
OLED_WIDTH, OLED_HEIGHT = 128, 64
MUX_SETTLE_US = 1000

# ---------------------------------------------------------------------------
# Traffic timing (seconds)
# ---------------------------------------------------------------------------
GREEN_BASE_S = 15
GREEN_EXTENSION_S = 10           # added once per green phase if IR detects occupancy
YELLOW_S = 3
ALL_RED_CLEARANCE_S = 1          # safety gap inserted before EMERGENCY_MODE grants green
AMBULANCE_GREEN_MIN_S = 30       # minimum hold once emergency lane is green
EMERGENCY_RECHECK_S = 2          # how often we recheck "has the ambulance cleared?"

# ---------------------------------------------------------------------------
# Detection validation thresholds (must match ai_model/inference/detect.py)
# ---------------------------------------------------------------------------
MIN_CONFIDENCE = 0.85

# ---------------------------------------------------------------------------
# Loop timing
# ---------------------------------------------------------------------------
OLED_REFRESH_MS = 1000
IR_POLL_MS = 100
MQTT_POLL_MS = 200
HEALTH_PUBLISH_MS = 5000
