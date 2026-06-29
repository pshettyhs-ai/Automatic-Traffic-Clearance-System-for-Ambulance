# Contributing

This started as a four-person final-year ECE project (Pavan Shetty H S, Pratham J S, Sachin N,
Thejomurthi A — Adichunchanagiri Institute of Technology, 2025-26) and is maintained here as a portfolio
/reference implementation. Contributions, issues, and forks are welcome.

## Reporting issues

Open a GitHub issue with:
- Which module (`firmware/`, `ai_model/`, `backend/`, `dashboard/`, hardware) it concerns.
- For firmware/hardware issues: which board revision and a photo/scope capture if it's a timing issue.
- For software issues: steps to reproduce, and whether it's a logic bug vs. a "haven't been able to
  run this yet" environment issue — see each module's README for what has and hasn't actually been
  execution-tested (e.g. `testing/software_tests/README.md`, `backend/README.md`, `dashboard/README.md`).

## Development setup

Each module is independently runnable — see its own README:
- `firmware/pico_firmware/README.md` / `firmware/esp8266_firmware/README.md`
- `ai_model/README.md`
- `backend/README.md`
- `dashboard/README.md`

## Pull requests

1. Fork, branch from `main`.
2. Keep changes scoped to one module where possible — this makes review tractable across such a wide
   hardware+software stack.
3. If you're changing firmware GPIO assignments, update both `firmware/pico_firmware/config.py` and
   `diagrams/Circuit_Diagram.svg` / `hardware/Wiring_Guide.md` in the same PR — a repeat of the original
   report's diagram/firmware mismatch is exactly the failure mode this repository was rebuilt to fix.
4. If you're changing a metric or performance claim in the README, link to the test or log entry that
   justifies it (`testing/performance_reports/`) rather than editing the number in isolation.
5. Run what test coverage exists for the module you touched before opening the PR:
   - Python: `python testing/software_tests/test_detection_validator.py`
   - Node: `cd backend && npm test`

## Code style

- Python: PEP 8, type hints where they add clarity (not required everywhere — this isn't a strictly
  typed codebase).
- JavaScript: no enforced style guide is configured yet; match the existing formatting in the file
  you're editing.
- Commit messages: present tense, scoped prefix helps (e.g. "firmware: fix yellow GPIO off-by-one",
  "dashboard: add lane health panel").

## Safety-critical changes

Anything touching `firmware/pico_firmware/traffic_controller.py`'s state machine should be checked
against `testing/hardware_tests/test_plan.md` Section 5 (emergency override) on real or simulated
(`simulations/wokwi/`) hardware before merging — this is the one module where a regression has real-world
safety implications, not just a broken feature.
