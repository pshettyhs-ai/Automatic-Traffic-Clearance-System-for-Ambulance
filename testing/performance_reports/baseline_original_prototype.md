# Performance Baseline — Original Prototype (2025-26 Academic Build)

These figures are reported **as measured by the original project team** on the bench prototype shown in
`images/Prototype_System_Setup.png`, running the original Firebase-polling + simpler detection pipeline
— **not** this repository's MQTT/YOLOv8 upgrade. They're preserved here as the documented starting point,
exactly as they appear in `docs/Project_Report.pdf` (Chapter 4). Where this repository changes the
architecture, the relevant number should be re-measured rather than assumed to carry over — see the
"What needs re-validation" section below.

## Detection performance (original color/shape + manual-trigger pipeline)

| Metric | Value |
|---|---|
| Ambulance detection rate (daylight) | 96.5% |
| Ambulance detection rate (night) | 92.3% |
| False positive rate | 0.8% |
| False negative rate | 3.5% |
| Average detection distance | 50–75 m |

## Response time

| Metric | Value |
|---|---|
| Detection → signal change | 1.3 s average |
| Complete intersection clear time | 8–12 s |
| System recovery time (post-emergency) | 15 s |

## Reliability (30-day bench test)

| Metric | Value |
|---|---|
| System uptime | 99.7% |
| Mean Time Between Failures (MTBF) | 720 hours |
| Mean Time To Repair (MTTR) | 30 minutes |

## Traffic flow improvement (normal operation)

| Metric | Value |
|---|---|
| Average wait time reduction | 18% |
| Intersection throughput increase | 22% |
| Queue length reduction | 25% |

## Emergency response improvement

| Metric | Value |
|---|---|
| Ambulance transit time reduction | 45% average |
| Emergency response time improvement | 2.5 min/incident |

## What needs re-validation after this repository's architecture changes

| Change | Why the old number may not transfer | How to re-measure |
|---|---|---|
| Color/shape detection → YOLOv8 | Different failure modes entirely (YOLOv8 should generalize better across vehicle paint schemes/lighting, but hasn't been measured on this project's footage) | `ai_model/evaluation/compute_metrics.py` against your own labeled validation set |
| Firebase REST polling (700ms) → MQTT pub/sub | Detection-to-signal-change latency should *improve* by removing the polling interval, but the 1.3s figure above already includes that polling delay, so the new number is genuinely unmeasured, not just "probably similar" | Bench test per `testing/hardware_tests/test_plan.md` §5 |
| No all-red clearance gap → 1s mandatory gap added | Complete intersection clear time will increase slightly (by design — this was a safety fix) | Re-time §5 of the hardware test plan |
| Single relay-driven Red/Green → added Yellow GPIOs | New failure mode possible (yellow stuck on/off) not present in the original 2-color system | New checklist item, §3 of the hardware test plan |

Use `hardware_validation_log.md` in this folder to record your own dated measurements once you've built
and tested the corrected design, and update the numbers above (with a date and your name/role) rather
than presenting the original team's figures as this repository's own results indefinitely.
