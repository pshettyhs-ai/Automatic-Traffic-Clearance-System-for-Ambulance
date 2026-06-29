/*
 * ESP8266 Acoustic Alert Node
 * ---------------------------
 * Repurposes the ESP8266 originally listed alongside the Pico WH in the
 * report's block diagram. Since the Pico WH already has its own Wi-Fi
 * radio, having a second board *also* speak Wi-Fi to do the same job was
 * redundant. Instead, this board has exactly one job: subscribe to the
 * emergency MQTT topic and drive a buzzer with a distinct audible pattern,
 * independently of the Pico — so a buzzer fault or reflash can never
 * block the safety-critical signal control logic on the Pico.
 *
 * Board: any ESP8266 dev board (NodeMCU / Wemos D1 mini tested form factor)
 * Library deps (Arduino IDE Library Manager):
 *   - PubSubClient (Nick O'Leary)
 *   - ESP8266WiFi (bundled with the ESP8266 Arduino core)
 *   - ArduinoJson (for parsing the emergency payload)
 */

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ---------------------------------------------------------------------------
// Configuration — mirror firmware/pico_firmware/config.py topic names exactly
// ---------------------------------------------------------------------------
const char *WIFI_SSID = "traffic-iot";
const char *WIFI_PASSWORD = "change-me";

const char *MQTT_BROKER_HOST = "192.168.1.10";
const uint16_t MQTT_BROKER_PORT = 1883;
const char *MQTT_CLIENT_ID = "esp8266-buzzer-01";

const char *TOPIC_EMERGENCY = "traffic/emergency";
const char *TOPIC_OVERRIDE = "traffic/override";

const uint8_t BUZZER_PIN = D1;          // GPIO5 on most ESP8266 boards
const unsigned long ALERT_DURATION_MS = 30000;  // matches AMBULANCE_GREEN_MIN_S minimum
const unsigned long BEEP_ON_MS = 250;
const unsigned long BEEP_OFF_MS = 250;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

bool alertActive = false;
unsigned long alertStartedAt = 0;
unsigned long lastBeepToggleAt = 0;
bool beepState = false;

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Wi-Fi: connecting");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 25000) {
    delay(250);
    Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " connected" : " FAILED");
}

void startAlert() {
  alertActive = true;
  alertStartedAt = millis();
  lastBeepToggleAt = 0;
  Serial.println("Buzzer: emergency alert started");
}

void stopAlert() {
  alertActive = false;
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("Buzzer: alert stopped");
}

void onMqttMessage(char *topic, byte *payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.print("JSON parse failed: ");
    Serial.println(err.c_str());
    return;
  }

  if (strcmp(topic, TOPIC_EMERGENCY) == 0) {
    startAlert();
  } else if (strcmp(topic, TOPIC_OVERRIDE) == 0) {
    const char *action = doc["action"] | "";
    if (strcmp(action, "clear_emergency") == 0 || strcmp(action, "force_red") == 0) {
      stopAlert();
    }
  }
}

void reconnectMqtt() {
  while (!mqttClient.connected()) {
    Serial.print("MQTT: connecting...");
    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println(" connected");
      mqttClient.subscribe(TOPIC_EMERGENCY);
      mqttClient.subscribe(TOPIC_OVERRIDE);
    } else {
      Serial.print(" failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 2s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  connectWifi();
  mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
  mqttClient.setCallback(onMqttMessage);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
  }
  if (!mqttClient.connected()) {
    reconnectMqtt();
  }
  mqttClient.loop();

  if (alertActive) {
    // Auto-clear as a fail-safe even if the "cleared" MQTT message is lost,
    // so the buzzer can never get stuck on indefinitely.
    if (millis() - alertStartedAt > ALERT_DURATION_MS) {
      stopAlert();
    } else {
      unsigned long now = millis();
      unsigned long interval = beepState ? BEEP_ON_MS : BEEP_OFF_MS;
      if (now - lastBeepToggleAt >= interval) {
        beepState = !beepState;
        digitalWrite(BUZZER_PIN, beepState ? HIGH : LOW);
        lastBeepToggleAt = now;
      }
    }
  }
}
