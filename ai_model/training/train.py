"""
train.py — Fine-tune YOLOv8n for ambulance detection.

This is the training entry point referenced by ai_model/README.md and the
root README's "Machine Learning Pipeline" section. It is a thin, well-
documented wrapper around the Ultralytics training API — there is no novel
training logic to hide here; the value-add for this project is the data
pipeline (collection + labeling discipline) and the *deployment-side*
validation gates in ai_model/inference/detect.py, not a custom trainer.

Usage:
    python train.py --data ../dataset/data.yaml --epochs 100 --imgsz 224

Expects a YOLO-format dataset (images/ + labels/ + data.yaml) under
ai_model/dataset/ — see dataset/README.md for how this project's dataset
was assembled and its current size/limitations.
"""

import argparse
from pathlib import Path

from ultralytics import YOLO


def main(args):
    model = YOLO(args.base_model)

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=args.device,
        project=str(Path(args.output_dir)),
        name="ambulance_yolov8n",
        # Augmentation tuned for outdoor traffic-camera footage: more color/
        # lighting jitter (day/night, weather) than the Ultralytics defaults,
        # less aggressive geometric distortion (vehicles keep a roughly fixed
        # orientation relative to a fixed-mount intersection camera).
        hsv_h=0.02,
        hsv_s=0.6,
        hsv_v=0.5,
        degrees=5.0,
        translate=0.1,
        scale=0.3,
        fliplr=0.5,
        flipud=0.0,
        mosaic=0.7,
    )

    metrics = model.val()
    print("Validation mAP50:", metrics.box.map50)
    print("Validation mAP50-95:", metrics.box.map)

    export_path = model.export(format="onnx", imgsz=args.imgsz)
    print("Exported ONNX model to:", export_path)


def parse_args():
    p = argparse.ArgumentParser(description="Fine-tune YOLOv8n for ambulance detection")
    p.add_argument("--base-model", default="yolov8n.pt", help="Pretrained base checkpoint to fine-tune from")
    p.add_argument("--data", default="../dataset/data.yaml")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--imgsz", type=int, default=224)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--patience", type=int, default=15, help="Early-stopping patience (epochs)")
    p.add_argument("--device", default="cpu", help="'cpu', '0' for first GPU, etc.")
    p.add_argument("--output-dir", default="../model_weights/runs")
    return p.parse_args()


if __name__ == "__main__":
    main(parse_args())
