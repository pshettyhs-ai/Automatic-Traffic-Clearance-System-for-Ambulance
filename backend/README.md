# Backend — API, MQTT Bridge, Event Store

Node.js + Express service that bridges MQTT (edge hardware) to WebSocket (browser dashboard), persists
every emergency event and detection pass to SQLite, and exposes a small REST API for history/config/
manual override. See `diagrams/Communication_Architecture.md` for the full message-flow rationale.

## Quick start

```bash
npm install
cp .env.example .env            # edit MQTT_BROKER_URL etc.
node database/seed.js admin "a-strong-password"   # create your first operator login
npm run dev                      # nodemon, auto-restart on change
```

Or via Docker Compose from the repo root (brings up Mosquitto + this backend together):
```bash
docker compose up --build
```

## Layout

```
backend/
├── server.js              entry point: http server + Socket.IO + MQTT bridge + Express app
├── api/
│   ├── app.js              Express app assembly (also imported directly by tests)
│   ├── routes/             auth, events, lanes, override, health
│   └── middleware/         JWT auth, centralized error handling
├── database/
│   ├── schema.sql           plain SQL — see diagrams/Database_Design.md
│   ├── db.js                 all prepared statements live here
│   └── seed.js               create the first operator account
└── mqtt/
    └── mqttBridge.js          subscribes to the broker, writes to SQLite, re-emits over Socket.IO
```

## REST endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/login` | — | Exchange username/password for a JWT |
| GET | `/api/events?hours=24&limit=100` | — | Recent emergency events |
| GET | `/api/events/:id` | — | A single event |
| GET | `/api/lanes/cycles?hours=6` | — | Signal-cycle history |
| GET | `/api/lanes/health` | — | Latest heartbeat per physical node |
| GET | `/api/health` | — | Backend liveness |
| POST | `/api/override` | **Bearer JWT** | `{"action":"force_red"\|"clear_emergency","lane":2}` |

Full request/response examples: `docs/API_Documentation.md`.

## WebSocket events (Socket.IO)

| Event | Payload | Emitted when |
|---|---|---|
| `emergencyEvent` | `{id, lane, confidence, evidence_id, detected_at}` | A validated detection arrives via MQTT |
| `laneStatus` | `{lane, phase, ...}` | The Pico publishes a signal-phase change |
| `emergencyCleared` | `{lane, phase: "EMERGENCY_CLEARED"}` | The Pico resumes normal cycling |
| `systemHealth` | `{node, uptime_s, ...}` | A heartbeat arrives from any node |

## Status / honest limitations

This code was written and **syntax-checked** (`node --check` on every file) in a sandboxed environment
with no package-registry access, so `npm install` and the Jest suite under
`testing/software_tests/test_backend_api.test.js` have **not** been executed end-to-end in this revision.
Run `npm install && npm test` yourself before treating this as production-verified — see
`testing/software_tests/README.md` for the full picture of what has and hasn't been run.
