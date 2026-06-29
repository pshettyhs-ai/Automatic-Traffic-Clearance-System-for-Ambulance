// mqttBridge.js — subscribes to the broker, persists events to the
// database, and re-emits everything over Socket.IO for the dashboard.
//
// This is the piece that makes MQTT and WebSocket work together rather
// than being two competing real-time mechanisms: edge devices only ever
// need to know about MQTT (lightweight, works on a microcontroller);
// browsers only ever need to know about WebSocket (MQTT clients in the
// browser are awkward and most corporate networks block non-HTTP(S)
// ports anyway). This module is the only place that speaks both.

const mqtt = require("mqtt");
const db = require("../database/db");

const TOPICS = {
  EMERGENCY: "traffic/emergency",
  OVERRIDE: "traffic/override",
  LANE_STATUS: "traffic/lane/status",
  HEALTH: "traffic/health",
  DETECTION_LOG: "traffic/detection_log",
};

function safeJsonParse(buffer) {
  try {
    return JSON.parse(buffer.toString());
  } catch (err) {
    return null;
  }
}

function attachMqttBridge(io, { brokerUrl, username, password } = {}) {
  const client = mqtt.connect(brokerUrl || "mqtt://localhost:1883", {
    username,
    password,
    clientId: `traffic-backend-${Math.random().toString(16).slice(2, 8)}`,
    reconnectPeriod: 2000,
  });

  client.on("connect", () => {
    console.log("[mqttBridge] connected to broker");
    client.subscribe(Object.values(TOPICS), (err) => {
      if (err) console.error("[mqttBridge] subscribe failed:", err.message);
    });
  });

  client.on("reconnect", () => console.log("[mqttBridge] reconnecting..."));
  client.on("error", (err) => console.error("[mqttBridge] error:", err.message));

  client.on("message", (topic, payloadBuf) => {
    const payload = safeJsonParse(payloadBuf);
    if (!payload) {
      console.warn("[mqttBridge] dropped non-JSON message on", topic);
      return;
    }

    switch (topic) {
      case TOPICS.EMERGENCY: {
        const detectedAt = payload.ts || Date.now() / 1000;
        const result = db.emergencyEvents.insert({
          detected_at: detectedAt,
          lane: payload.lane,
          confidence: payload.confidence,
          evidence_path: payload.evidence_id ? `${payload.evidence_id}.jpg` : null,
        });
        io.emit("emergencyEvent", { id: result.lastInsertRowid, ...payload, detected_at: detectedAt });
        break;
      }

      case TOPICS.LANE_STATUS: {
        db.signalCycles.insert({
          started_at: Date.now() / 1000,
          lane: payload.lane,
          phase: payload.phase,
          planned_duration_ms: payload.planned_duration_ms || null,
          actual_duration_ms: payload.actual_duration_ms || null,
          extended_by_ir: payload.extended_by_ir ? 1 : 0,
        });
        io.emit("laneStatus", payload);

        if (payload.phase === "EMERGENCY_CLEARED") {
          io.emit("emergencyCleared", payload);
        }
        break;
      }

      case TOPICS.HEALTH: {
        db.systemHealth.insert({
          ts: Date.now() / 1000,
          node: payload.node || "unknown",
          uptime_s: payload.uptime_s || null,
          cpu_pct: payload.cpu_pct || null,
          mem_pct: payload.mem_pct || null,
          wifi_status: payload.wifi_status || null,
          mqtt_status: "connected",
        });
        io.emit("systemHealth", payload);
        break;
      }

      case TOPICS.DETECTION_LOG: {
        db.detectionLog.insert({
          ts: payload.ts || Date.now() / 1000,
          confidence: payload.confidence,
          passed_validation: payload.passed_validation ? 1 : 0,
          failure_reason: payload.failure_reason || null,
          frame_path: payload.frame_path || null,
          emergency_event_id: payload.emergency_event_id || null,
        });
        // Intentionally not re-emitted to the dashboard — this is a
        // high-frequency stream (every inference pass); the dashboard
        // only needs confirmed emergencyEvent / laneStatus messages live.
        break;
      }

      default:
        console.warn("[mqttBridge] unhandled topic:", topic);
    }
  });

  function publishOverride(action, extra = {}) {
    client.publish(TOPICS.OVERRIDE, JSON.stringify({ action, ...extra }), { qos: 1 });
  }

  return { client, publishOverride, TOPICS };
}

module.exports = { attachMqttBridge, TOPICS };
