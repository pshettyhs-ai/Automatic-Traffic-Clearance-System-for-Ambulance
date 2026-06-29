# ai_model/evaluation/

## Files

- `compute_metrics.py` — computes detection performance metrics from the backend's `detection_log` and
  `emergency_events` tables (see `backend/database/schema.sql`).
- `evidence/` — annotated frame snapshots saved by `ai_model/inference/detect.py` on every confirmed
  trigger (gitignored; these are runtime artifacts, not repository content).

## How to actually evaluate detection accuracy honestly

`compute_metrics.py` deliberately **will not** report a detection accuracy, false-positive rate, or
false-negative rate unless you supply human-reviewed ground truth via `--ground-truth-ids`. Computing
those numbers from the system's own confirmed triggers, with no independent check, would just measure
"how often did the system agree with itself" — not real accuracy.

To produce a defensible number for a resume bullet or report:

1. Let the system run and log detections for a period (`detection_log` table fills automatically).
2. Open `evaluation/evidence/` and manually review each saved snapshot for confirmed triggers
   (`emergency_events`). Note the `id` of every event that's actually an ambulance.
3. Separately review a sample of footage from when no trigger fired, to estimate missed detections
   (false negatives) — this is the part most homegrown evaluations skip, and it's the harder half of
   the number.
4. Run:
   ```bash
   python compute_metrics.py --db ../../backend/database/traffic.db --hours 24 \
       --ground-truth-ids 14,15,19,22
   ```

## Why this matters for an interview

A specific, reproducible "here's the script, here's how I labeled ground truth, here's the resulting
precision/recall" answer is far stronger than quoting a single percentage with no methodology behind
it — and it's something an interviewer can ask follow-up questions about without the answer falling
apart.
