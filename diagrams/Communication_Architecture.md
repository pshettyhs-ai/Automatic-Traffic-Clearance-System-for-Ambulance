```mermaid
sequenceDiagram
    autonumber
    participant Cam as PI Camera
    participant Pi4 as Pi 4B (YOLOv8)
    participant MQ as MQTT Broker
    participant Pico as Pico WH
    participant ESP as ESP8266 (buzzer)
    participant BE as Node.js Backend
    participant DB as SQLite/PostgreSQL
    participant WS as Dashboard (WebSocket)

    Cam->>Pi4: raw frame (CSI)
    Pi4->>Pi4: preprocess + YOLOv8 inference
    Pi4->>Pi4: 4-gate validation (conf/multi-frame/position/size)
    Pi4->>MQ: PUBLISH traffic/emergency {lane, confidence, evidence_id}
    par fan-out to subscribers
        MQ->>Pico: traffic/emergency
        MQ->>ESP: traffic/emergency
        MQ->>BE: traffic/emergency
    end
    Pico->>Pico: enter EMERGENCY_MODE FSM
    Pico->>MQ: PUBLISH traffic/lane/status {lane, state}
    ESP->>ESP: sound buzzer pattern
    BE->>DB: INSERT emergency_events
    BE->>WS: emit('emergencyEvent', payload)
    WS->>WS: render alert banner + map pin

    Note over Pico,MQ: Heartbeat every 5s on traffic/health,<br/>even with no emergency — used for uptime/MTBF metrics
    Pico->>MQ: PUBLISH traffic/health {uptime, last_cycle}
    MQ->>BE: traffic/health
    BE->>DB: UPSERT system_health

    rect rgb(245,245,245)
        Note over BE,WS: REST is used for non-real-time paths only
        WS->>BE: GET /api/events?range=24h
        BE->>DB: SELECT FROM emergency_events
        BE->>WS: 200 OK [events]
        WS->>BE: POST /api/override {lane, action}
        BE->>MQ: PUBLISH traffic/override (operator command)
        MQ->>Pico: traffic/override
    end
```

### Why MQTT + REST + WebSocket instead of REST-only

The original report routed every interaction — detection events, signal status, and dashboard
polling — through a single REST API. That works, but it has two costs that matter for a
time-critical system:

- REST is request/response: the dashboard would have had to **poll** for new emergency events, adding
  latency proportional to the poll interval (and wasting bandwidth between events).
- A REST call from a constrained microcontroller (Pico WH) blocks on a TCP handshake + HTTP overhead for
  every message, which is unnecessary cost for a small, frequent payload.

MQTT solves both: it's a persistent, lightweight publish/subscribe session, so the Pi 4B can publish a
detection event once and have it fan out instantly to the Pico, the ESP8266, and the backend with no
polling. REST is kept for what it's actually good at — configuration, history queries, and manual
override commands that are naturally request/response. WebSocket (via Socket.IO) is added purely for the
**dashboard's** live view, since browsers can't subscribe to MQTT directly without an extra bridge —
the backend performs that bridge.
