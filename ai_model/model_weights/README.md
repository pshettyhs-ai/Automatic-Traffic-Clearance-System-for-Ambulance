# ai_model/model_weights/

Trained model checkpoints are not committed to this repository (binary weight files don't belong in
git history — use [Git LFS](https://git-lfs.com) or a release artifact if you need to version them).

## Expected files after training

Running `ai_model/training/train.py` will populate this folder with:

```
model_weights/
├── runs/
│   └── ambulance_yolov8n/
│       ├── weights/
│       │   ├── best.pt       <- use this one for inference
│       │   └── last.pt
│       └── results.png       <- training curves (loss, mAP) for the README
└── ambulance_yolov8n.pt      <- copy of best.pt, the path detect.py expects by default
```

## Publishing a checkpoint with a GitHub Release

Rather than committing large binaries:

```bash
gh release create v1.0-weights ai_model/model_weights/ambulance_yolov8n.pt \
  --title "Ambulance YOLOv8n weights v1.0" \
  --notes "Trained on <dataset version>, mAP50=<value> — see ai_model/evaluation/"
```

Then link the release asset from the root README instead of bloating the repository.

## Status

No checkpoint has been published yet from this revision of the repository — `ambulance_yolov8n.pt` is
the path the code expects, not a claim that a trained file exists here. Train against your own dataset
(see `ai_model/dataset/README.md`) before relying on `ai_model/inference/detect.py` for anything beyond
a code review / architecture demo.
