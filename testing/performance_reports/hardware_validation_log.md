# Hardware Validation Log

Dated record of running `testing/hardware_tests/test_plan.md` against a real build. Copy the table below
for each test session — don't overwrite previous entries, so trends (and regressions) are visible.

## Session template

```
### YYYY-MM-DD — Tester name — Build/firmware commit hash

| Checklist item | Result | Measured value | Notes |
|---|---|---|---|
| 1. Power-on safety | PASS/FAIL | | |
| 2. Default-safe-state | PASS/FAIL | | |
| 3. Per-lane signal (N/E/S/W) | PASS/FAIL | | |
| 4. IR occupancy extension | PASS/FAIL | | |
| 5. Emergency override | PASS/FAIL | detection→green: ___s | |
| 6. Acoustic alert | PASS/FAIL | | |
| 7. Recovery / fault injection | PASS/FAIL | | |

**Summary:** (1-2 sentences — what changed since the last session, what to fix next)
```

## Log entries

_No real hardware sessions logged yet in this revision of the repository — this file ships as a template
for you to fill in once you've built the corrected design. An empty log is more honest than a
fabricated one._
