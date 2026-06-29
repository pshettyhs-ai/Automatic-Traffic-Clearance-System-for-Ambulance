"""
compute_metrics.py — Turn the raw detection log into the metrics quoted in
the root README's "Performance Metrics" table: detection accuracy, false
positive/negative rate, and response time.

Reads from the same `detection_log` table the backend populates from the
`traffic/detection_log` MQTT topic (see backend/database/schema.sql) so
metrics are computed from real logged inference passes, not estimated.

Usage:
    python compute_metrics.py --db ../../backend/database/traffic.db --hours 24
"""

import argparse
import sqlite3
from datetime import datetime, timedelta


def load_detection_log(db_path: str, since: datetime):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT * FROM detection_log WHERE ts >= ? ORDER BY ts ASC",
        (since.timestamp(),),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def load_confirmed_events(db_path: str, since: datetime):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT * FROM emergency_events WHERE detected_at >= ? ORDER BY detected_at ASC",
        (since.timestamp(),),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def summarize(detection_log, confirmed_events, ground_truth_event_ids: set):
    """
    `ground_truth_event_ids` is the set of emergency_events.id values that a
    human reviewer has confirmed were *actually* an emergency vehicle
    (cross-checked against the saved evidence image). Without ground truth,
    this script can only report operational stats (trigger count, response
    time) — it cannot honestly report accuracy/false-positive rate. This is
    intentional: a script that invented those numbers from unlabeled data
    would be more misleading than a script that says "needs review".
    """
    total_passes = len(detection_log)
    confirmed = [e for e in confirmed_events]
    total_confirmed = len(confirmed)

    print(f"Total inference passes logged: {total_passes}")
    print(f"Total confirmed emergency triggers: {total_confirmed}")

    if total_confirmed and detection_log:
        avg_conf = sum(d["confidence"] for d in detection_log) / total_passes
        print(f"Mean confidence across all passes: {avg_conf:.3f}")

    if not ground_truth_event_ids:
        print(
            "\nNo human-reviewed ground truth provided (--ground-truth-ids). "
            "Skipping accuracy / false-positive / false-negative computation — "
            "label a sample of emergency_events against the saved evidence "
            "images first (see evaluation/README.md), then re-run with "
            "--ground-truth-ids."
        )
        return

    true_positive_ids = {e["id"] for e in confirmed} & ground_truth_event_ids
    false_positive_ids = {e["id"] for e in confirmed} - ground_truth_event_ids
    false_negative_count = len(ground_truth_event_ids - {e["id"] for e in confirmed})

    tp, fp, fn = len(true_positive_ids), len(false_positive_ids), false_negative_count
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")

    print(f"\nTrue positives:  {tp}")
    print(f"False positives: {fp}  ({fp / total_confirmed:.1%} of triggers)" if total_confirmed else "")
    print(f"False negatives: {fn}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")


def parse_args():
    p = argparse.ArgumentParser(description="Compute detection performance metrics from logged events")
    p.add_argument("--db", default="../../backend/database/traffic.db")
    p.add_argument("--hours", type=int, default=24, help="Look-back window")
    p.add_argument(
        "--ground-truth-ids",
        default="",
        help="Comma-separated emergency_events.id values manually confirmed as true ambulances",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    since = datetime.now() - timedelta(hours=args.hours)
    log = load_detection_log(args.db, since)
    events = load_confirmed_events(args.db, since)
    gt_ids = {int(x) for x in args.ground_truth_ids.split(",") if x.strip()}
    summarize(log, events, gt_ids)
