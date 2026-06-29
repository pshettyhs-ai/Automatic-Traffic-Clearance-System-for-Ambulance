"""
detect.py — Real-time ambulance detection on the Raspberry Pi 4B.

Replaces the original report's unspecified "image processing techniques
combined with machine learning algorithms... color filtering" pipeline
with a named, reproducible model (YOLOv8n) and an explicit four-gate
validation strategy before anything is treated as a confirmed detection.
See diagrams/Emergency_Detection_Flowchart.md for the corresponding
flowchart this code implements.

Usage:
    python detect.py --source 0 --weights ../model_weights/ambulance_yolov8n.pt

Publishes a JSON message to MQTT topic `traffic/emergency` on a
validated detection, matching the schema expected by
firmware/pico_firmware/main.py::on_emergency().
"""

import argparse
import json
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "ultralytics is required: pip install ultralytics opencv-python paho-mqtt\n"
        f"(original import error: {exc})"
    )

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Tunables — keep in sync with firmware/pico_firmware/config.py
# ---------------------------------------------------------------------------
MIN_CONFIDENCE = 0.85
FRAME_BUFFER_SIZE = 5
MIN_CONFIRMING_FRAMES = 3
INFERENCE_SIZE = 224
MQTT_TOPIC_EMERGENCY = "traffic/emergency"
MQTT_TOPIC_DETECTION_LOG = "traffic/detection_log"
AMBULANCE_CLASS_NAME = "ambulance"

# A detection's bounding box, as a fraction of frame area, must fall in this
# range to be considered "an ambulance actually near the intersection camera"
# rather than a distant vehicle or a false-positive sliver. Calibrate against
# your own camera mount height/angle — see hardware/Wiring_Guide.md.
MIN_BBOX_AREA_FRACTION = 0.015
MAX_BBOX_AREA_FRACTION = 0.65

# A simple polygon (in normalized 0-1 image coordinates) describing the lane
# detection zone. Replace with values calibrated for your camera framing.
DETECTION_ZONE = np.array([[0.05, 0.35], [0.95, 0.35], [0.95, 1.0], [0.05, 1.0]])


def _point_in_polygon(point, polygon) -> bool:
    """Standard ray-casting point-in-polygon test; avoids pulling in a heavier
    geometry library just to check whether a bbox center sits inside a 4-point
    detection zone."""
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


@dataclass
class DetectionRecord:
    timestamp: float
    confidence: float
    bbox_area_fraction: float
    center_xy: tuple
    passed_all_gates: bool
    gate_passed: bool = False  # passed confidence+size+zone, independent of multi-frame confirmation
    failure_reason: str = ""


@dataclass
class FrameValidator:
    """
    Implements the four validation gates from the Emergency Detection
    Flowchart: confidence -> multi-frame confirmation -> position ->
    size. Each gate is checked independently so failures are explainable
    (and logged) rather than collapsing into a single boolean.
    """

    history: deque = field(default_factory=lambda: deque(maxlen=FRAME_BUFFER_SIZE))

    def _in_zone(self, center_xy):
        return _point_in_polygon(center_xy, DETECTION_ZONE)

    def evaluate(self, confidence, bbox_xyxy, frame_shape):
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = bbox_xyxy
        area_fraction = abs((x2 - x1) * (y2 - y1)) / float(w * h)
        center = ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h)

        record = DetectionRecord(
            timestamp=time.time(),
            confidence=confidence,
            bbox_area_fraction=area_fraction,
            center_xy=center,
            passed_all_gates=False,
        )

        if confidence < MIN_CONFIDENCE:
            record.failure_reason = "low_confidence"
            self.history.append(record)
            return record

        if not (MIN_BBOX_AREA_FRACTION <= area_fraction <= MAX_BBOX_AREA_FRACTION):
            record.failure_reason = "size_out_of_range"
            self.history.append(record)
            return record

        in_zone = self._in_zone(center)
        if not in_zone:
            record.failure_reason = "outside_detection_zone"
            self.history.append(record)
            return record

        record.gate_passed = True
        self.history.append(record)
        confirming = sum(1 for r in self.history if r.gate_passed)
        if confirming < MIN_CONFIRMING_FRAMES:
            record.failure_reason = "awaiting_multi_frame_confirmation"
            return record

        record.passed_all_gates = True
        record.failure_reason = ""
        return record


def make_mqtt_client(broker_host, broker_port):
    client = mqtt.Client(client_id="pi4-detector", protocol=mqtt.MQTTv311)
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_start()
    return client


def publish_emergency(client, lane, record: DetectionRecord, evidence_path: str):
    payload = {
        "lane": lane,
        "confidence": round(record.confidence, 3),
        "evidence_id": Path(evidence_path).stem,
        "ts": record.timestamp,
    }
    client.publish(MQTT_TOPIC_EMERGENCY, json.dumps(payload), qos=1)


def publish_detection_log(client, record: DetectionRecord):
    """Every inference pass is logged, not just confirmed emergencies — this is
    what lets evaluation/compute_metrics.py reconstruct false-positive/negative
    rates after the fact instead of only ever seeing confirmed events."""
    payload = {
        "ts": record.timestamp,
        "confidence": round(record.confidence, 3),
        "passed_validation": record.passed_all_gates,
        "failure_reason": record.failure_reason,
        "bbox_area_fraction": round(record.bbox_area_fraction, 4),
    }
    client.publish(MQTT_TOPIC_DETECTION_LOG, json.dumps(payload), qos=0)


def save_evidence(frame, annotated_frame, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = out_dir / f"{time.strftime('%Y%m%d-%H%M%S')}.jpg"
    cv2.imwrite(str(filename), annotated_frame)
    return str(filename)


def run(args):
    model = YOLO(args.weights)
    validator = FrameValidator()
    mqtt_client = None
    if not args.no_mqtt:
        mqtt_client = make_mqtt_client(args.mqtt_host, args.mqtt_port)

    cap = cv2.VideoCapture(args.source if not str(args.source).isdigit() else int(args.source))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video source: {args.source}")

    last_trigger_time = 0.0
    cooldown_s = args.cooldown_s

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Frame grab failed, retrying...")
                time.sleep(0.1)
                continue

            resized = cv2.resize(frame, (INFERENCE_SIZE, INFERENCE_SIZE))
            results = model.predict(resized, verbose=False, conf=0.25)[0]

            best_record = None
            annotated = frame.copy()
            for box in results.boxes:
                cls_name = model.names[int(box.cls[0])]
                if cls_name.lower() != AMBULANCE_CLASS_NAME:
                    continue
                conf = float(box.conf[0])
                # Scale bbox back from the 224x224 inference frame to the original frame
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                sx, sy = frame.shape[1] / INFERENCE_SIZE, frame.shape[0] / INFERENCE_SIZE
                bbox_full = (x1 * sx, y1 * sy, x2 * sx, y2 * sy)

                record = validator.evaluate(conf, bbox_full, frame.shape)
                if mqtt_client:
                    publish_detection_log(mqtt_client, record)

                cv2.rectangle(
                    annotated,
                    (int(bbox_full[0]), int(bbox_full[1])),
                    (int(bbox_full[2]), int(bbox_full[3])),
                    (0, 0, 255) if record.passed_all_gates else (0, 165, 255),
                    2,
                )
                cv2.putText(
                    annotated,
                    f"AMBULANCE {conf:.2f}",
                    (int(bbox_full[0]), max(0, int(bbox_full[1]) - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2,
                )

                if record.passed_all_gates and (not best_record or conf > best_record.confidence):
                    best_record = record

            now = time.time()
            if best_record and (now - last_trigger_time) > cooldown_s:
                evidence_path = save_evidence(frame, annotated, Path(args.evidence_dir))
                if mqtt_client:
                    publish_emergency(mqtt_client, args.lane, best_record, evidence_path)
                print(f"EMERGENCY TRIGGERED lane={args.lane} conf={best_record.confidence:.2f} -> {evidence_path}")
                last_trigger_time = now

            if args.show:
                cv2.imshow("Ambulance Detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    finally:
        cap.release()
        if args.show:
            cv2.destroyAllWindows()
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()


def parse_args():
    p = argparse.ArgumentParser(description="YOLOv8 ambulance detection for the traffic clearance system")
    p.add_argument("--source", default="0", help="Camera index or video file/RTSP URL")
    p.add_argument("--weights", default="../model_weights/ambulance_yolov8n.pt")
    p.add_argument("--lane", type=int, default=1, help="Lane number this camera covers (1-4)")
    p.add_argument("--mqtt-host", default="192.168.1.10")
    p.add_argument("--mqtt-port", type=int, default=1883)
    p.add_argument("--no-mqtt", action="store_true", help="Run without publishing (local testing)")
    p.add_argument("--cooldown-s", type=float, default=5.0, help="Min seconds between repeat triggers")
    p.add_argument("--evidence-dir", default="../evaluation/evidence")
    p.add_argument("--show", action="store_true", help="Show annotated preview window")
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
