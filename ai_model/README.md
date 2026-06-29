# ai_model/ — Ambulance Detection Pipeline

Replaces the original report's unspecified "image processing + color filtering" approach with a named,
versioned, reproducible pipeline: **YOLOv8n**, fine-tuned for the `ambulance` class, running on-device
on the Raspberry Pi 4B.

```
ai_model/
├── dataset/        YOLO-format dataset layout + sourcing guidance (no images committed)
├── training/       train.py — fine-tuning entry point
├── inference/       detect.py — the live detection + 4-gate validation pipeline (see diagrams/Emergency_Detection_Flowchart.md)
├── model_weights/  trained checkpoints (not committed — see model_weights/README.md)
└── evaluation/     compute_metrics.py — honest accuracy/precision/recall from logged + human-reviewed data
```

## Why YOLOv8n specifically

- **YOLOv8n** ("nano") is the smallest variant in the YOLOv8 family — it trades some accuracy for
  inference speed, which matters here because the Raspberry Pi 4B has no dedicated accelerator.
  In practice this runs at single-digit-to-low-double-digit FPS on a Pi 4B CPU at 224×224 input, which
  is enough for a fixed traffic camera (vehicles don't move fast across the frame between samples).
- A literature-reported reference point for context: Rajurkar (2024), cited in the original project's
  literature survey, reported an 80.5% mAP50 using YOLOv8 for Indian-traffic vehicle detection generally
  (not ambulance-specific) — a reasonable ballpark for what to expect before any project-specific
  fine-tuning, not a number this repository is claiming to have reproduced.
- If a Pi 4B turns out to be too slow once you've measured it on your own footage, `train.py`'s
  ONNX export step makes it straightforward to try ONNX Runtime or OpenVINO for additional speedup
  without changing the rest of the pipeline.

## Pipeline at a glance

1. `inference/detect.py` grabs frames from the camera, runs YOLOv8 inference, and runs every detected
   `ambulance` box through four validation gates (confidence ≥0.85 → multi-frame confirmation → inside
   the lane's detection zone → plausible bounding-box size) before treating it as real.
2. On a confirmed detection, it saves an annotated evidence frame, publishes `traffic/emergency` over
   MQTT, and logs the raw inference result (passed or not, and why) to `traffic/detection_log` for later
   auditing.
3. `evaluation/compute_metrics.py` turns that log into the accuracy/precision/recall numbers you'd want
   for a report — see that folder's README for why it refuses to compute them without ground truth.

## Status

Architecture, training script, and inference pipeline are implemented and unit-tested
(`testing/software_tests/test_detection_validator.py` covers the four-gate validation logic in
isolation). **No production-trained weights ship in this repository** — see `dataset/README.md` and
`model_weights/README.md` for what's needed to take this from "ready to train" to "field-validated."
