# Hardware Validation Test Plan

A repeatable bench-test procedure for validating the build before any field deployment. Pair this with
`hardware/Wiring_Guide.md` § 7 "Bring-up order."

## 1. Power-on safety checks

- [ ] All rails (5V, 12V) measure within ±5% of nominal under no load.
- [ ] No component exceeds its rated temperature after 15 minutes idle (touch-test + thermal camera/IR
      thermometer if available — relay modules and the SMPS are the most likely hot spots).
- [ ] Reverse-polarity protection diode verified (briefly reverse the input on a bench supply with
      current limited to <100mA, confirm no damage, confirm zero output).

## 2. Default-safe-state check

- [ ] On boot, before Wi-Fi/MQTT connects, all four lanes show RED (verifies `all_red()` runs before any
      network dependency in `firmware/pico_firmware/main.py`).
- [ ] Disconnect Wi-Fi mid-cycle — confirm the Pico continues its local timer-based FSM rather than
      hanging (this is the "graceful degradation" property claimed in the root README).
- [ ] Kill the MQTT broker mid-emergency — confirm the Pico's `AMBULANCE_GREEN_MIN_S` minimum-hold logic
      still completes locally rather than getting stuck.

## 3. Per-lane signal verification

For each lane (North/East/South/West):
- [ ] GREEN lights only the green LED (no other color in that lane lit simultaneously).
- [ ] YELLOW transition occurs and lasts ~3s (per `config.YELLOW_S`).
- [ ] RED is the default/idle state.
- [ ] OLED for that lane shows the matching phase text and a countdown that decreases monotonically.

## 4. IR occupancy + green extension

- [ ] With no obstruction, a lane's green phase ends at the base duration (`GREEN_BASE_S`).
- [ ] With the IR beam broken during a lane's green phase, that phase extends by
      `GREEN_EXTENSION_S`, and only once per phase (confirm it doesn't re-extend repeatedly).

## 5. Emergency override (the core safety-critical path)

- [ ] Publish a synthetic `traffic/emergency` MQTT message for lane 3 manually (e.g.,
      `mosquitto_pub -t traffic/emergency -m '{"lane":3,"confidence":0.93}'`) and time the interval to
      that lane showing GREEN — target **per the original report: ≤1.3s** detection-to-signal-change;
      note this was measured on the original system's simpler pipeline, re-measure after the YOLOv8
      upgrade.
- [ ] Confirm a brief all-red clearance phase occurs before the ambulance lane turns green (this is the
      safety fix described in `diagrams/Traffic_State_Machine.md` — the original design had no such gap).
- [ ] Confirm all non-emergency lanes show RED for the full duration of `EMERGENCY_MODE`.
- [ ] Confirm the minimum 30s hold (`AMBULANCE_GREEN_MIN_S`) before the system will consider resuming.
- [ ] Confirm the system resumes at `NORTH_GREEN` after the emergency clears (matches the original
      design's deliberate, predictable resume behavior).

## 6. Acoustic alert (ESP8266)

- [ ] Buzzer starts within ~1s of the same `traffic/emergency` message reaching the ESP8266.
- [ ] Buzzer auto-stops after 30s even with no `clear_emergency` message (fail-safe timeout).

## 7. Recovery / fault injection

- [ ] Power-cycle the Pico mid-emergency — on reboot, confirm it returns to all-red, not a stale
      mid-emergency state (there's no persisted state across reboot by design — see
      `firmware/pico_firmware/main.py`'s `finally: controller.all_red()`).
- [ ] Disconnect one OLED mid-run — confirm the other three lanes' displays are unaffected (tests the
      per-channel mux isolation, and the retry-once-then-skip logic in `oled_driver.py`).

## Logging your results

Record pass/fail + measured timings for each checklist item in
`testing/performance_reports/hardware_validation_log.md` (template provided there) rather than only in
this checklist, so there's a dated record you can cite.
