# Design Document

## Scope

A single 4-way intersection pilot: emergency vehicle detection, automated signal control with emergency
override, local visual feedback (OLED), acoustic alert, and a remote monitoring/override dashboard. This
matches the original academic project's stated scope (`docs/Project_Report.pdf`, Chapter 1) — this
repository does not expand the deployment scope, only the implementation quality and architectural
correctness of that same scope.

## Design goals, in priority order

1. **Safety first.** The signal controller must never present an ambiguous or actively unsafe state
   (e.g., two perpendicular greens). Every state transition in `traffic_controller.py` either holds the
   previous safe state or moves through an explicit all-red clearance step.
2. **Graceful degradation over hard dependency.** Losing Wi-Fi, the MQTT broker, or the backend should
   degrade the system to "dumb but safe timer-based signal control," not stop it entirely. This is why
   the Pico's FSM never blocks waiting on a network call.
3. **Auditability.** Every emergency trigger, every detection pass (not just confirmed ones), every
   signal-phase change, and every manual override is logged with a timestamp — see
   `diagrams/Database_Design.md`.
4. **Replaceability of any single component.** SQLite↔Postgres, Mosquitto↔managed broker, YOLOv8n↔a
   larger model — none of these swaps should require touching more than one layer.

## Key design decisions and the alternatives considered

### Why MQTT over a heavier message broker (Kafka, RabbitMQ)

A 4-way intersection produces a low volume of small, infrequent messages (emergency events, lane status,
heartbeats every few seconds) — nowhere near the throughput Kafka/RabbitMQ are built for. MQTT's minimal
client footprint matters more here, since one of the publishers is a microcontroller with limited RAM.

### Why YOLOv8n over a larger YOLOv8 variant or a two-stage detector

The Pi 4B has no hardware accelerator. YOLOv8n is the smallest variant in the family specifically to fit
a CPU-only edge budget; a larger variant (s/m/l/x) would need to be justified by a measured accuracy gap
on this project's own footage, which hasn't been done — start small, measure, and upgrade only if the
metrics in `ai_model/evaluation/` show it's needed.

### Why SQLite for the pilot instead of Postgres from day one

A single-intersection pilot has one writer (the backend process) and modest write volume. SQLite removes
an entire service (and its ops burden) for that scale. The schema is plain SQL specifically so this
decision is reversible — see `backend/README.md`.

### Why the all-red clearance gap is fixed at 1 second, not configurable per-deployment

This is a deliberate simplification for the pilot scope: a real city deployment would calibrate this per
intersection (lane width, typical vehicle speed). It's called out explicitly in
`firmware/pico_firmware/config.py` as `ALL_RED_CLEARANCE_S` precisely so it's a one-line change, not
hardcoded inline in the FSM logic.

### Why manual override requires login but live viewing doesn't

The dashboard's read-only live view (signal status, detection feed, history) has no safety implication if
seen by an unauthenticated viewer on the local network; the override endpoint can change real-world
traffic signal behavior, so it's the one endpoint gated behind auth — see `backend/api/middleware/auth.js`.

## Out of scope for this revision (see root README § Future Enhancements for the longer list)

- Multi-intersection coordination / "green corridor" sequencing (mentioned in the original report's
  abstract as a goal; not implemented at the pilot scope here).
- Multiple simultaneous emergency vehicles from different lanes.
- Pedestrian-crossing awareness during an override.
- Authenticated, encrypted MQTT by default (documented as a pre-production step, not shipped as the
  default local-dev config — see `docs/Deployment_Guide.md`).
