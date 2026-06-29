# Architecture

This document is the prose companion to the diagrams in `/diagrams`. Read it alongside
`diagrams/System_Architecture.svg` and `diagrams/Block_Diagram.svg`.

## Three-tier design

**Tier 1 — Edge (at the intersection).** Two boards, with a strict division of responsibility that the
original report's diagrams didn't clearly draw:

- **Raspberry Pi 4B** does the one job that genuinely needs real compute: camera capture, OpenCV
  preprocessing, and YOLOv8 inference. It has no involvement in driving any GPIO-connected hardware.
- **Raspberry Pi Pico WH** does the one job that genuinely needs hard real-time, low-jitter execution:
  the traffic-light state machine, relay/LED control, OLED updates, and IR sensor polling. It has no
  camera and runs no machine learning.

Splitting these is the single biggest architectural correction in this repository — the original
report's circuit diagram wired a camera directly into the same circuit as the Pico, which isn't
buildable for any vision model heavier than basic color thresholding.

A third, minor device — the **ESP8266** — exists only to drive a buzzer on emergency events, intentionally
decoupled from the Pico so a buzzer fault can't affect signal safety.

**Tier 2 — Communication.** MQTT (Mosquitto) is the backbone for anything time-critical and
fire-and-forget (emergency events, lane status, health heartbeats). REST is kept for what it's
naturally good at: login, history queries, and manual override commands. WebSocket (Socket.IO) exists
purely to give the browser dashboard a live feed, since browsers don't speak MQTT directly. See
`diagrams/Communication_Architecture.md` for the full rationale and a sequence diagram.

**Tier 3 — Cloud/Server.** A Node.js backend bridges MQTT↔WebSocket, persists every event to SQLite
(swappable for PostgreSQL), and serves the REST API. A React dashboard consumes both REST and WebSocket.
Everything in this tier ships in one `docker-compose.yml` for a single-server pilot deployment.

## Why these specific technology swaps from the original report

| Original | This revision | Reasoning |
|---|---|---|
| Unspecified "image processing + color filtering" | YOLOv8n, named and versioned | Reproducible, benchmarkable, and a real skill line for a resume — see `ai_model/README.md` |
| REST-only (Web Dashboard ↔ REST API ↔ Raspberry Pi Wi-Fi/ESP8266) | MQTT for events, REST for config/history, WebSocket for live UI | Removes dashboard polling latency and avoids blocking the microcontroller on HTTP overhead for frequent small messages — see `diagrams/Communication_Architecture.md` |
| No mentioned database (REST API implied stateless) | SQLite (Postgres-ready schema) | Makes the "Data Logging and Analytics" objective in the original report's Chapter 1 actually implementable, with a concrete schema (`diagrams/Database_Design.md`) |
| Single combined "Raspberry Pi Wi-Fi / ESP8266" block | Pi 4B (vision) + Pico WH (control) + ESP8266 (alert) | Resolves an unbuildable ambiguity — see "Three-tier design" above |
| Camera wired into the Pico/relay circuit | Camera → Pi 4B (CSI) only | A Pico cannot run CV inference or accept a CSI feed |
| Two disconnected "Regulated Power Supply" boxes, one backward arrow | One shared, correctly-directed PSU + UPS | Original diagram had power flowing *into* the supply from the OLEDs, which is physically backward |
| GP17 and GP15 each assigned twice across different signal groups | Every Pico GPIO assigned exactly once | The original circuit diagram (Fig 2.3) listed an unbuildable pin conflict; this revision's pin map is taken directly from the validated firmware |
| Servo Motor + dedicated Fig 2.2 diagram in the hardware list | Omitted from the BOM | No figure, connection, or firmware logic anywhere in the original report explains what the servo physically does — see `hardware/README.md` for the full reasoning |
| No all-red clearance gap before emergency override | 1-second mandatory all-red gap added | Switching directly from one green lane to a perpendicular green lane is a real safety hazard |
| Docker / containerized deployment not mentioned | `docker-compose.yml` for broker + backend + dashboard | Standard, portable deployment path for the server-side tier |

## Trust boundaries

- Edge devices only ever make **outbound** MQTT connections (TLS, port 8883 in production) — no inbound
  port is opened on a Pi 4B, Pico, or ESP8266, which keeps the attack surface at the intersection small.
- The only state-changing HTTP endpoint (`POST /api/override`) requires a JWT and is rate-limited
  separately from read endpoints (`backend/api/app.js`).
- Every manual override is written to `audit_trail` with the operator's user id (`backend/database/schema.sql`).

See `docs/Deployment_Guide.md` for the full production security checklist (TLS, broker auth, etc. — left
as "enable before going beyond your own LAN" rather than configured by default, to keep local development
friction-free).
