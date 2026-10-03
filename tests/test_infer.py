"""Deterministic output and CLI checks; no model downloads or account access."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

# Keep test imports offline and their settings inside the checkout.
os.environ["YOLO_OFFLINE"] = "true"
os.environ["YOLO_AUTOINSTALL"] = "false"
config = Path(__file__).resolve().parents[1] / ".yolo-config"
config.mkdir(exist_ok=True)
os.environ["YOLO_CONFIG_DIR"] = str(config)

import cv2
import numpy as np
from PIL import Image
import torch
from ultralytics.engine.results import Results

from infer import main, save_result


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = np.full((37, 61, 3), 180, dtype=np.uint8)
        self.source = self.root / "source.png"
        cv2.imwrite(str(self.source), self.image)
        self.weights = self.root / "model.pt"
        self.weights.write_bytes(b"placeholder; validation tests never load this")

    def save(self, boxes, masks):
        result = Results(self.image, path=str(self.source), names={0: "crack"}, boxes=boxes, masks=masks)
        output = self.root / "output"
        save_result(result, output, self.source, self.weights, 0.25, 640, "cpu")
        return output

    def test_empty_result_writes_zero_mask_and_empty_instances(self):
        output = self.save(torch.empty((0, 6)), None)
        with Image.open(output / "mask.png") as image:
            self.assertEqual(image.mode, "L")
            mask = np.array(image)
        self.assertEqual(mask.shape, (37, 61))
        self.assertFalse(mask.any())
        self.assertEqual(json.loads((output / "predictions.json").read_text())["instances"], [])
        self.assertEqual(cv2.imread(str(output / "annotated.png")).shape, self.image.shape)

    def test_overlapping_instances_produce_exact_full_resolution_union(self):
        masks = torch.zeros((2, 37, 61))
        masks[0, 3:8, 5:10] = 1
        masks[1, 6:11, 8:13] = 1
        boxes = torch.tensor([[5, 3, 10, 8, 0.75, 0], [8, 6, 13, 11, 0.625, 0]])
        output = self.save(boxes, masks)
        with Image.open(output / "mask.png") as image:
            self.assertEqual(image.mode, "L")
            actual = np.array(image)
        expected = np.zeros((37, 61), dtype=np.uint8)
        expected[3:8, 5:10] = 255
        expected[6:11, 8:13] = 255
        np.testing.assert_array_equal(actual, expected)
        data = json.loads((output / "predictions.json").read_text())
        self.assertEqual((data["height"], data["width"]), (37, 61))
        self.assertEqual(data["instances"][1]["box_xyxy"], [8, 6, 13, 11])
        self.assertEqual(data["instances"][0]["confidence"], 0.75)
        self.assertEqual(data["instances"][0]["class_name"], "crack")

    def test_wrong_mask_dimensions_fail_before_writing(self):
        with self.assertRaisesRegex(ValueError, "full-resolution"):
            self.save(torch.tensor([[0, 0, 10, 10, 0.75, 0]]), torch.ones((1, 10, 10)))
        self.assertFalse((self.root / "output").exists())

    def test_boxes_without_masks_fail_before_writing(self):
        with self.assertRaisesRegex(ValueError, "without segmentation masks"):
            self.save(torch.tensor([[0, 0, 10, 10, 0.75, 0]]), None)

    def test_existing_results_are_preserved(self):
        output = self.save(torch.empty((0, 6)), None)
        before = {p.name: p.read_bytes() for p in output.iterdir()}
        with self.assertRaises(FileExistsError):
            save_result(SimpleNamespace(orig_shape=(37, 61), boxes=[], masks=None), output,
                        self.source, self.weights, 0.25, 640, "cpu")
        self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})

    def cli_error(self, extra, expected):
        argv = ["--weights", str(self.weights), "--source", str(self.source),
                "--output", str(self.root / "new-output")] + extra
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            main(argv)
        self.assertEqual(error.exception.code, 2)
        self.assertIn(expected, stderr.getvalue())
        self.assertFalse((self.root / "new-output").exists())

    def test_missing_weights_fail_without_creating_output(self):
        self.cli_error(["--weights", str(self.root / "missing.pt")], "existing local .pt")

    def test_missing_source_fails(self):
        self.cli_error(["--source", str(self.root / "missing.png")], "existing local image")

    def test_invalid_image_fails_before_model_loading(self):
        self.source.write_text("not an image")
        self.cli_error([], "could not be decoded")

    def test_invalid_options_fail(self):
        for value in ("0", "1.1", "nan", "inf"):
            with self.subTest(conf=value):
                self.cli_error(["--conf", value], "--conf must")
        self.cli_error(["--imgsz", "0"], "--imgsz must")

    def test_cli_refuses_an_existing_output_directory(self):
        target = self.root / "new-output"
        target.mkdir()
        before = self.source.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["--weights", str(self.weights), "--source", str(self.source), "--output", str(target)])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
