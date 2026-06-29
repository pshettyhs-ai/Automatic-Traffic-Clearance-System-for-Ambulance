# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] - 2026-06-25 - Industry-grade repository rebuild

### Fixed
- **Emergency-hold minimum-duration bug** in `firmware/pico_firmware/traffic_controller.py`: the
  recheck logic in `tick_emergency()` re-armed `phase_end_ms` to `now + EMERGENCY_RECHECK_S` on every
  2-second recheck tick, which could let the system exit emergency mode (resuming normal cycling) only
  a few seconds after entering it if the ambulance was detected as "no longer present" shortly after an
  early recheck point -- nowhere near the intended `AMBULANCE_GREEN_MIN_S` (30s) minimum hold. Found via
  a simulation-based test (`testing/software_tests/test_traffic_controller.py`) that stepped a fake clock
  through the FSM with the ambulance disappearing 3 seconds into the hold; the original logic exited
  after ~4 seconds instead of 30. Fixed by gating the entire recheck/exit branch behind an explicit
  "has the mandatory minimum actually elapsed" check, so `phase_end_ms` can only ever be pushed later by
  the recheck logic, never earlier. Regression test included.
- **Detection-validator multi-frame confirmation counter** in `ai_model/inference/detect.py`: the
  original counting approach mutated each frame's `failure_reason` immediately after counting it, which
  meant the "how many of the last N frames passed?" count could never exceed 1 across calls. Fixed by
  tracking gate-passage on a dedicated `gate_passed` field set once and never overwritten, decoupled
  from the multi-frame confirmation outcome. Caught and fixed via
  `testing/software_tests/test_detection_validator.py` during initial development.

### Added
- MQTT-based event architecture (`traffic/emergency`, `traffic/lane/status`, `traffic/health`,
  `traffic/detection_log`) alongside REST and WebSocket - see `diagrams/Communication_Architecture.md`.
- Named, versioned ML pipeline: YOLOv8n ambulance detection with a four-gate validation strategy
  (`ai_model/inference/detect.py`), replacing the original unspecified "image processing" approach.
- SQLite event store with a Postgres-portable schema (`backend/database/schema.sql`) and a Node.js /
  Express / Socket.IO backend bridging MQTT to the dashboard.
- React + Redux Toolkit + Tailwind operator dashboard with live signal status, emergency timeline,
  analytics, and an authenticated manual-override panel.
- Yellow-phase GPIO control on the Pico WH firmware (the original sample firmware only drove
  red/green, despite 3-color signal heads in the BOM).
- A mandatory all-red clearance phase before granting the ambulance lane green (closes a real safety
  gap in the original state machine - see `diagrams/Traffic_State_Machine.md`).
- Docker Compose deployment for the broker, backend, and dashboard.
- Unit tests for the detection-validation logic (`testing/software_tests/test_detection_validator.py`,
  executed and passing - see that file and `testing/software_tests/README.md`).
- Full documentation set: architecture, design rationale, API reference, user manual, deployment guide,
  hardware BOM, wiring guide, and a hardware validation checklist.

### Changed
- Split the original ambiguous "Raspberry Pi Wi-Fi / ESP8266" block into three clearly-scoped devices:
  Pi 4B (vision), Pico WH (real-time control), ESP8266 (acoustic alert only).
- Replaced Firebase Realtime Database REST polling (`fb_get_bool`, 700ms poll loop) with persistent
  MQTT pub/sub in the Pico firmware.
- Corrected the GPIO pin map: the original circuit diagram (Fig 2.3) assigned GP17 and GP15 twice each
  across different signal groups; the corrected map (derived from the original working firmware) assigns
  every pin exactly once.
- Moved the camera from the Pico's circuit (as drawn in the original Fig 2.3) to the Pi 4B's CSI port,
  since a Pico cannot run CV inference or accept a CSI feed.
- Replaced the original report's two disconnected, backward-wired "Regulated Power Supply" blocks with
  one shared, correctly-directed PSU and UPS in the corrected block diagram.

### Documentation honesty notes
- Performance figures (detection accuracy, response time, uptime, etc.) quoted from the original report
  are explicitly labeled as measurements of the original color/shape-detection and Firebase-polling
  system, not as results for this revision's YOLOv8/MQTT upgrade - see
  `testing/performance_reports/baseline_original_prototype.md` for exactly what needs re-validation and
  how.
- Backend and dashboard code was syntax-checked but not executed end-to-end in the environment this
  revision was built in (no package-registry network access there) - see `backend/README.md` and
  `dashboard/README.md`.

## [1.0.0] - 2025-26 - Original academic submission

- Initial four-way intersection prototype: timer-based signal control, Firebase-based ambulance flag
  polling, OLED status displays, web dashboard. Submitted as the major project report for B.E. ECE,
  Adichunchanagiri Institute of Technology (VTU). See `docs/Project_Report.pdf`.
