# YoloV7_Crack_Detection_Segmentation

This tutorial is based on the YOLOv7 repository by WongKinYiu. This notebook shows training on your own custom objects.

In this tutorial, it will be utilized an open source computer vision dataset available on Roboflow Universe in the website https://universe.roboflow.com/university-bswxt/crack-bphdr, which contains more than 4000 images, train set, valid set, and test set, with the labels for the segmentation.

![crackSegmentation](https://github.com/user-attachments/assets/69e991ad-3baf-48bf-8981-170dc44c369a)

## Update
Crack Segmentation with Yolo V8, best weight = https://drive.google.com/file/d/1XWHCK-MTiz2AJqJyz5LT-sAFLeFef91E/view?usp=sharing

## Local inference demo (YOLOv8 segmentation)

Run a single image on your own machine, using the YOLOv8 checkpoint linked
above. This command-line demo needs no Roboflow package, API key, account, or
dataset download. The YOLOv7 notebooks use a different model implementation;
their checkpoints are not supported by this demo. The original training
notebooks and their dependency versions remain separate.

Use Python 3.12 and a fresh virtual environment. The pinned CPU setup was
tested on Windows x64; Linux and macOS have not been tested. Commands below
use PowerShell from the repository directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt
.\.venv\Scripts\python.exe -m pip check
```

On Linux, use `python3.12 -m venv .venv` and `.venv/bin/python` in place of
the Windows executable. The CPU wheel command follows the
[PyTorch 2.7.1 installation instructions](https://pytorch.org/get-started/previous-versions/#v271).
Direct dependencies are pinned; this is not a full transitive lockfile.
`omegaconf` is required to deserialize configuration in the linked legacy
checkpoint, even though no training or dataset configuration is used here.

Download the linked weights through your browser and save them as
`weights/crack-yolov8.pt`. Weights are not bundled. The downloaded file tested
for this demo was 92,285,330 bytes with SHA-256
`95adb860396bee6dc21742cffd25449aebd489bfe6dae011cad1cc9835af6f08`.
Check the download with `Get-FileHash weights/crack-yolov8.pt -Algorithm SHA256`.
Load only checkpoints you trust: PyTorch `.pt` files can contain executable
pickle data.

```powershell
.\.venv\Scripts\python.exe infer.py --weights weights/crack-yolov8.pt --source path/to/crack.jpg --output demo-output --device cpu
```

For a repeatable smoke input, this creates an artificial crack image. It is
only a plumbing check and does not measure accuracy on real concrete:

```powershell
.\.venv\Scripts\python.exe -c "from PIL import Image, ImageDraw; im=Image.new('RGB',(640,480),(180,180,180)); ImageDraw.Draw(im).line([(80,30),(130,110),(210,180),(240,270),(380,350),(430,460)],fill=(25,25,25),width=6); im.save('synthetic-crack.png')"
.\.venv\Scripts\python.exe infer.py --weights weights/crack-yolov8.pt --source synthetic-crack.png --output demo-output-synthetic
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The new output directory contains `annotated.png`, `mask.png`, and
`predictions.json`. The PNG mask matches the original image dimensions:
background is 0, foreground is 255, and overlapping instances are merged.
The JSON contains pixel-coordinate boxes, classes, and confidence per
instance; it does not contain per-instance masks. An empty result still
saves all three files with a black mask and an empty `instances` list.
Existing output directories are refused. Choose another `--output` for each
run. `--conf` defaults to 0.25 and `--imgsz` to 640.

Inference uses local files, disables Ultralytics online checks and automatic
dependency installation, and keeps its settings in ignored `.yolo-config/`.
Full-resolution masks use `retina_masks=True`, as implemented in the
[pinned segmentation predictor](https://github.com/ultralytics/ultralytics/blob/v8.4.19/ultralytics/models/yolo/segment/predict.py).
This is a local CLI example; it does not start an HTTP service. CUDA, field
accuracy, and the original training workflows have not been validated by
the demo smoke checks.

## Roboflow and dataset preparation

Roboflow remains a dataset source for the training tutorials, including
workspace `university-bswxt`, project `crack-bphdr`, version 2. The YOLOv8
notebook requests the `yolov5` export; the YOLOv7 notebooks request the
`yolov7` export. Keep those formats and the dataset attribution when
reproducing the tutorials. Plain inference requires only a compatible
checkpoint and a local image, so Roboflow is excluded from
`requirements-inference.txt`.

The YOLOv8 dataset-download cell now reads `ROBOFLOW_API_KEY` from the
environment or prompts with `getpass` when it is unset. Inject it locally
through your secret manager or use the hidden prompt; do not put a value
in notebook code or save it in outputs. This key is only needed when
downloading the training dataset.

Removing every Roboflow reference would lose dataset provenance, and
removing the download calls would break the current preparation steps.
Roboflow could also be removed from training preparation by supplying an
equivalent local dataset, labels, train/validation/test splits, and
`data.yaml`, then adapting each notebook's dataset paths. That migration
is outside this demo.
