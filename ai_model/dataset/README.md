# ai_model/dataset/

## What's actually here

No images are committed to this repository — both because labeled vehicle-image datasets are large
(unsuitable for git) and because the dataset used during development mixed public sources with footage
captured at the team's own bench setup (the toy-ambulance prototype shown in
`images/Dashboard_Screenshot.png`), which isn't republishable as-is.

## Expected structure (YOLO format)

```
dataset/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

`data.yaml`:
```yaml
path: ./dataset
train: images/train
val: images/val
test: images/test
names:
  0: ambulance
  1: fire_truck
  2: police_vehicle
  3: car
  4: bus
  5: truck
```

## Sourcing data for your own deployment

1. **Public datasets** — search for "emergency vehicle detection dataset" on Roboflow Universe and
   Kaggle; several CC-licensed sets of ambulance/fire-truck images with YOLO-format annotations exist.
   Filter for vehicles photographed from a fixed elevated angle if possible, since that's closer to a
   real intersection-camera viewpoint than ground-level photos.
2. **Your own footage** — record at the actual intersection(s) you plan to deploy at, across different
   times of day and weather. This matters more than dataset size: a model trained only on daylight,
   clear-weather footage is exactly the failure mode flagged in the original report's "Disadvantages"
   section (night/weather-dependent accuracy).
3. **Labeling** — [Roboflow](https://roboflow.com) or [Label Studio](https://labelstud.io) both export
   directly to YOLO format compatible with `data.yaml` above.

## Honest status

The performance figures quoted in the root README's "Results" table (96.5% daylight / 92.3% night
detection rate, 0.8% false-positive rate) are **from the original project report's tested system**
(a simpler color/shape heuristic + manual-trigger pipeline, not this repository's YOLOv8 upgrade). They
are reported as the project's baseline, not as YOLOv8 benchmark results — re-run
`ai_model/evaluation/compute_metrics.py` against your own labeled validation set once you've trained a
model on real data, and update the numbers honestly. Treat the architecture in this repo as ready to
train and integrate, not as a model with already-proven field accuracy.
