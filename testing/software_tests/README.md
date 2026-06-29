# testing/software_tests/

| File | Covers | Executed in this revision? |
|---|---|---|
| `test_detection_validator.py` | The 4-gate detection validation logic in `ai_model/inference/detect.py` | **Yes** — 8/8 passing, run with a dependency-stubbed harness since `ultralytics`/`paho-mqtt` weren't installable offline in the environment this repo was built in. Re-run for yourself: `python testing/software_tests/test_detection_validator.py` (works standalone, no pytest required — falls back to a plain runner if pytest isn't installed) |
| `test_traffic_controller.py` | The emergency-override + normal-cycle finite state machine in `firmware/pico_firmware/traffic_controller.py` | **Yes** — 7/7 passing, run against a simulated MicroPython `time`/`machine` environment (no real hardware needed). This is the suite that caught the emergency-hold timing bug described in `CHANGELOG.md`. Re-run: `python testing/software_tests/test_traffic_controller.py` |
| `test_backend_api.test.js` | REST endpoints in `backend/api/` (health, events, override auth) | **No** — written and syntax-checked (`node --check`) only; `npm install` had no registry access in that environment. Run yourself: `cd backend && npm install && npm test` |

## Why this distinction matters

It would have been easy to present both files as "passing test suites" without qualification. Two of
them actually are — `test_detection_validator.py` caught a real bug where the multi-frame confirmation
counter could never reach its threshold, and `test_traffic_controller.py` caught a real bug where the
emergency-hold minimum duration could be cut from 30 seconds down to roughly 4 — both documented in
`CHANGELOG.md`. The Jest file is a well-formed test that has only been checked for syntax, not behavior.
Treat that category as "ready to run," not "verified," until you've run it yourself.

## Running everything

```bash
# Python — no extra install needed beyond the stdlib
python testing/software_tests/test_detection_validator.py
python testing/software_tests/test_traffic_controller.py

# Node — requires network access for npm install
cd backend && npm install && npm test
```
