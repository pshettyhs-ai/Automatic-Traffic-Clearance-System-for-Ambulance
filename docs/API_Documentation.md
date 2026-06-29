# API Documentation

Base URL (local dev): `http://localhost:4000`. All request/response bodies are JSON.

## Authentication

### `POST /api/auth/login`

```json
// Request
{ "username": "admin", "password": "a-strong-password" }

// Response 200
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "id": 1, "username": "admin", "role": "admin" }
}

// Response 401
{ "error": "Invalid credentials" }
```

Use the returned `token` as `Authorization: Bearer <token>` on `/api/override`.

## Events

### `GET /api/events?hours=24&limit=100`

Recent confirmed emergency events.

```json
// Response 200
{
  "count": 2,
  "since": 1750838400.0,
  "events": [
    {
      "id": 42,
      "detected_at": 1750841213.5,
      "lane": 3,
      "confidence": 0.93,
      "evidence_path": "20260625-101501.jpg",
      "cleared": 1,
      "cleared_at": 1750841244.0,
      "duration_ms": 30500
    }
  ]
}
```

### `GET /api/events/:id`

A single event by id. `404` with `{"error": "Event not found"}` if it doesn't exist.

## Lanes

### `GET /api/lanes/cycles?hours=6`

Signal-cycle history (every phase transition the Pico has reported).

```json
{
  "count": 48,
  "since": 1750819200.0,
  "cycles": [
    { "id": 101, "started_at": 1750841200.0, "lane": 1, "phase": "GREEN",
      "planned_duration_ms": 15000, "actual_duration_ms": 25000, "extended_by_ir": 1 }
  ]
}
```

### `GET /api/lanes/health`

Latest heartbeat per physical node.

```json
[
  { "node": "pico-junction-01", "ts": 1750841500.0, "uptime_s": 86400, "wifi_status": "connected", "mqtt_status": "connected" },
  { "node": "pi4-detector", "ts": 1750841498.0, "uptime_s": 86390, "wifi_status": "connected", "mqtt_status": "connected" }
]
```

## Manual override

### `POST /api/override` — **requires `Authorization: Bearer <token>`**

```json
// Request
{ "action": "force_red" }
// or
{ "action": "clear_emergency" }

// Response 200
{ "status": "sent", "action": "force_red", "lane": null }

// Response 400 — invalid action
{ "error": "action must be one of: force_red, clear_emergency" }

// Response 401 — missing/invalid token
{ "error": "Missing bearer token" }

// Response 503 — MQTT bridge not connected
{ "error": "MQTT bridge is not connected; override cannot be delivered" }
```

Every successful call is recorded in `audit_trail` with the authenticated operator's user id.

## Health

### `GET /api/health`

```json
{ "status": "ok", "uptime_s": 86400, "nodes": [ "...same shape as /api/lanes/health..." ], "timestamp": 1750841500.0 }
```

## WebSocket events (Socket.IO, not REST)

Connect to the same base URL with a Socket.IO client. See `dashboard/src/services/socket.js` for a
working example, and `backend/README.md` for the full event table (`emergencyEvent`, `laneStatus`,
`emergencyCleared`, `systemHealth`).

## MQTT topics (not exposed over HTTP — internal to the system)

| Topic | Publisher | Subscriber(s) | Payload |
|---|---|---|---|
| `traffic/emergency` | Pi 4B | Pico, ESP8266, backend | `{lane, confidence, evidence_id, ts}` |
| `traffic/override` | backend (relaying dashboard action) | Pico, ESP8266 | `{action, lane?}` |
| `traffic/lane/status` | Pico | backend | `{lane, phase, ...}` |
| `traffic/health` | Pico, Pi 4B | backend | `{node, uptime_s, ...}` |
| `traffic/detection_log` | Pi 4B | backend | `{ts, confidence, passed_validation, failure_reason}` |

See `diagrams/Communication_Architecture.md` for the full sequence diagram.
