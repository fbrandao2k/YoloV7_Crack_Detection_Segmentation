"""Run one local image through a local Ultralytics YOLOv8 segmentation model."""

import argparse
import json
import os
from pathlib import Path


def save_result(result, output, source, weights, conf, imgsz, device):
    """Save a union mask at source resolution, an annotation, and instance metadata."""
    import cv2
    import numpy as np

    height, width = result.orig_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    instances = []
    if result.masks is not None:
        masks = result.masks.data.cpu().numpy()
        if masks.shape != (len(result.boxes), height, width):
            raise ValueError("Expected one full-resolution mask per box; use retina_masks=True")
        mask[np.any(masks > 0, axis=0)] = 255
    elif len(result.boxes):
        raise ValueError("Model returned boxes without segmentation masks")
    for box in result.boxes:
        class_id = int(box.cls.item())
        instances.append({
            "class_id": class_id,
            "class_name": result.names[class_id],
            "confidence": float(box.conf.item()),
            "box_xyxy": box.xyxy[0].cpu().tolist(),
        })
    # Reserving a new directory also protects the source image and existing results.
    output.mkdir(parents=True, exist_ok=False)
    if not cv2.imwrite(str(output / "annotated.png"), result.plot()):
        raise OSError("Could not write annotated.png")
    if not cv2.imwrite(str(output / "mask.png"), mask):
        raise OSError("Could not write mask.png")
    metadata = {
        "source": str(source), "weights": str(weights),
        "width": width, "height": height,
        "confidence_threshold": conf, "image_size": imgsz, "device": device,
        "mask": "mask.png", "mask_values": {"background": 0, "foreground": 255},
        "instances": instances,
    }
    (output / "predictions.json").write_text(
        json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", required=True, type=Path, help="Local YOLOv8 segmentation .pt")
    parser.add_argument("--source", required=True, type=Path, help="One local image")
    parser.add_argument("--output", type=Path, default=Path("demo-output"), help="New output directory")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu", help="cpu (default), or a compatible CUDA device")
    args = parser.parse_args(argv)
    if not 0 < args.conf <= 1:
        parser.error("--conf must be greater than 0 and at most 1")
    if args.imgsz <= 0:
        parser.error("--imgsz must be positive")
    weights, source, output = (p.expanduser().resolve() for p in (args.weights, args.source, args.output))
    if not weights.is_file() or weights.suffix.lower() != ".pt":
        parser.error("--weights must be an existing local .pt file")
    if not source.is_file():
        parser.error("--source must be an existing local image file")
    if output.exists():
        parser.error("--output already exists; choose a new directory")

    # Configure Ultralytics before importing it: no online checks or auto-installs.
    os.environ["YOLO_OFFLINE"] = "true"
    os.environ["YOLO_AUTOINSTALL"] = "false"
    config = Path(__file__).resolve().parent / ".yolo-config"
    config.mkdir(exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(config)
    import cv2
    from ultralytics import YOLO

    image = cv2.imread(str(source))
    if image is None:
        parser.error("--source could not be decoded as an image")
    model = YOLO(str(weights))
    if model.task != "segment":
        parser.error("--weights must be an Ultralytics segmentation checkpoint")
    result = model.predict(
        source=image, conf=args.conf, imgsz=args.imgsz, device=args.device,
        retina_masks=True, save=False, verbose=False,
    )[0]
    save_result(result, output, source, weights, args.conf, args.imgsz, args.device)
    print(f"Saved {len(result.boxes)} instance(s) to {output}")


if __name__ == "__main__":
    main()
