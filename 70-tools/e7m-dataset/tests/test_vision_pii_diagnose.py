"""Tests for the vision PII filter operator-diagnostic CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


from e7m_dataset import vision_pii_diagnose as diag


# Reuse the synthesizers from the main test module without re-importing the
# whole world.
def _make_yolov8_onnx(path):
    import numpy as np
    import onnx
    from onnx import helper, TensorProto, numpy_helper
    arr = np.array([[[320.0, 240.0, 40.0, 60.0, 0.9]]], dtype=np.float32)
    tensor = numpy_helper.from_array(arr, name="output_const")
    node = helper.make_node("Constant", inputs=[], outputs=["output"], value=tensor)
    graph = helper.make_graph(
        nodes=[node], name="Y",
        inputs=[helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, 640, 640])],
        outputs=[helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 1, 5])],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.save(model, str(path))


# ─── check ──────────────────────────────────────────────────────────


def test_check_reports_required_deps_ok(monkeypatch, capsys):
    """In this dev env, onnxruntime/numpy are installed → check returns 1
    (because ETZ_VISION_PII_FACE_MODEL is unset)."""
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    monkeypatch.delenv("ETZ_VISION_PII_BACKEND", raising=False)
    rc = diag.main(["check"])
    assert rc == 1   # no critical missing dep but no face model
    captured = capsys.readouterr()
    assert "onnxruntime" in captured.out
    assert "skipped" in captured.out


def test_check_json_output(monkeypatch, capsys):
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    rc = diag.main(["check", "--json"])
    assert rc == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "required" in payload
    assert "onnxruntime" in payload["required"]
    assert payload["required"]["onnxruntime"]["available"] is True
    assert payload["model_classification"] is None


def test_check_classifies_face_model_when_set(monkeypatch, capsys, tmp_path):
    onnx_path = tmp_path / "y.onnx"
    _make_yolov8_onnx(onnx_path)
    monkeypatch.setenv("ETZ_VISION_PII_FACE_MODEL", str(onnx_path))
    monkeypatch.delenv("ETZ_VISION_PII_BACKEND", raising=False)
    rc = diag.main(["check", "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["model_classification"]["kind"] == "yolov8-face"


# ─── classify ───────────────────────────────────────────────────────


def test_classify_yolov8(tmp_path, capsys):
    onnx_path = tmp_path / "y.onnx"
    _make_yolov8_onnx(onnx_path)
    rc = diag.main(["classify", str(onnx_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "yolov8-face" in captured.out
    assert "Yolov8FaceOnnxBackend" in captured.out


def test_classify_json_output(tmp_path, capsys):
    onnx_path = tmp_path / "y.onnx"
    _make_yolov8_onnx(onnx_path)
    rc = diag.main(["classify", str(onnx_path), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "yolov8-face"
    assert payload["backend"] == "Yolov8FaceOnnxBackend"


def test_classify_missing_model_fails(tmp_path):
    rc = diag.main(["classify", str(tmp_path / "no-such.onnx")])
    assert rc == 2


def test_classify_corrupt_model_fails(tmp_path):
    bad = tmp_path / "bad.onnx"
    bad.write_bytes(b"not onnx")
    rc = diag.main(["classify", str(bad)])
    assert rc == 2


# ─── smoke ──────────────────────────────────────────────────────────


def test_smoke_runs_detect_faces(tmp_path, capsys):
    onnx_path = tmp_path / "y.onnx"
    _make_yolov8_onnx(onnx_path)
    rc = diag.main(["smoke", str(onnx_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "kind=yolov8-face" in captured.out
    assert "backend=Yolov8FaceOnnxBackend" in captured.out
    assert "detections=" in captured.out


def test_smoke_json(tmp_path, capsys):
    onnx_path = tmp_path / "y.onnx"
    _make_yolov8_onnx(onnx_path)
    rc = diag.main(["smoke", str(onnx_path), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "yolov8-face"
    assert payload["backend"] == "Yolov8FaceOnnxBackend"
    assert payload["image_size"] == [640, 480]
    assert payload["detections"] == 1   # the synth Nx5 has score 0.9 ≥ 0.5


def test_smoke_missing_model_fails(tmp_path):
    rc = diag.main(["smoke", str(tmp_path / "no-such.onnx")])
    assert rc == 2
