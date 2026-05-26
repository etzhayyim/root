"""Tests for vision_pii_filter (ADR-2605262500 §5 / G2).

Validates:
  - Default-fail-closed behavior (no env, no allow_stub → unavailable)
  - Stub backend gating via allow_stub / ETZ_VISION_PII_ALLOW_STUB
  - Face/plate blur when Pillow is available (real blur smoke)
  - Child-presence full-frame rejection (G5)
  - Detection-box clipping for out-of-bounds rectangles

The tests do NOT need network access. Real ONNX backends are W3.1
deliverables and not exercised here.
"""

from __future__ import annotations

import io
import os

import pytest

from e7m_dataset.vision_pii_filter import (
    DetectionBox,
    OnnxFaceBackend,
    StubBackendConfig,
    StubVisionPiiBackend,
    VisionPiiBackendUnavailable,
    VisionPiiFilter,
)


# ─── helpers ────────────────────────────────────────────────────────


def _tiny_jpeg() -> bytes:
    """Make a 64x48 RGB JPEG with a deterministic gradient.

    Solid-color images blur to themselves (no change), making blur-applied
    assertions impossible to verify. The gradient guarantees blur produces
    different bytes from the source within a detection box.
    """
    from PIL import Image
    img = Image.new("RGB", (64, 48))
    pixels = img.load()
    for y in range(48):
        for x in range(64):
            pixels[x, y] = (
                (x * 4) % 256,
                (y * 5) % 256,
                ((x + y) * 3) % 256,
            )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# ─── fail-closed by default ─────────────────────────────────────────


def test_default_is_fail_closed(monkeypatch):
    """No backend env, no allow_stub → __init__ raises."""
    monkeypatch.delenv("ETZ_VISION_PII_BACKEND", raising=False)
    monkeypatch.delenv("ETZ_VISION_PII_ALLOW_STUB", raising=False)
    with pytest.raises(VisionPiiBackendUnavailable, match="no ETZ_VISION_PII_BACKEND set"):
        VisionPiiFilter()


def test_unknown_backend_rejects(monkeypatch):
    monkeypatch.setenv("ETZ_VISION_PII_BACKEND", "magic-blur-9000")
    with pytest.raises(VisionPiiBackendUnavailable, match="unknown backend"):
        VisionPiiFilter()


def test_real_backend_w3_1_now_shipped(monkeypatch):
    """W3.1 shipped: real ONNX path is wired. Without ETZ_VISION_PII_FACE_MODEL
    set, init fails-closed with a clear "model env not set" message."""
    monkeypatch.setenv("ETZ_VISION_PII_BACKEND", "centerface-onnx")
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    with pytest.raises(VisionPiiBackendUnavailable, match="ETZ_VISION_PII_FACE_MODEL"):
        VisionPiiFilter()


def test_stub_backend_requires_explicit_allow(monkeypatch):
    """Even with env spec, stub backend fail-closed without ALLOW_STUB=1."""
    monkeypatch.setenv("ETZ_VISION_PII_BACKEND", "stub-allow")
    monkeypatch.delenv("ETZ_VISION_PII_ALLOW_STUB", raising=False)
    with pytest.raises(VisionPiiBackendUnavailable, match="ALLOW_STUB"):
        VisionPiiFilter()


def test_stub_backend_with_env_allow(monkeypatch):
    monkeypatch.setenv("ETZ_VISION_PII_BACKEND", "stub-allow")
    monkeypatch.setenv("ETZ_VISION_PII_ALLOW_STUB", "1")
    f = VisionPiiFilter()
    assert f.backend.name == "stub-allow"


def test_stub_backend_with_kwarg_allow():
    """`allow_stub=True` kwarg also unlocks stub backend (tests path)."""
    f = VisionPiiFilter(backend=StubVisionPiiBackend(), allow_stub=True)
    assert f.backend.name == "stub-allow"


# ─── stub backend redaction ────────────────────────────────────────


def test_redaction_no_detections_passes_through():
    f = VisionPiiFilter(
        backend=StubVisionPiiBackend(StubBackendConfig()),
        allow_stub=True,
    )
    img = _tiny_jpeg()
    result = f.redact(img)
    assert not result.frame_rejected
    assert result.redacted_bytes is not None
    assert result.detections.faces == []
    assert result.detections.plates == []
    assert result.detections.child_face_count == 0


def test_face_box_triggers_blur():
    cfg = StubBackendConfig(
        face_boxes=[DetectionBox(x=10, y=10, w=20, h=20, score=0.9, label="face")]
    )
    f = VisionPiiFilter(backend=StubVisionPiiBackend(cfg), allow_stub=True)
    img = _tiny_jpeg()
    result = f.redact(img)
    assert not result.frame_rejected
    assert len(result.detections.faces) == 1
    # Redacted bytes must differ from original (blur applied).
    assert result.redacted_bytes is not None
    assert result.redacted_bytes != img


def test_plate_box_also_triggers_blur():
    cfg = StubBackendConfig(
        plate_boxes=[DetectionBox(x=5, y=5, w=15, h=8, score=0.85, label="license_plate")]
    )
    f = VisionPiiFilter(backend=StubVisionPiiBackend(cfg), allow_stub=True)
    result = f.redact(_tiny_jpeg())
    assert len(result.detections.plates) == 1
    assert result.redacted_bytes is not None


def test_child_presence_triggers_frame_rejection():
    """G5 §5: child detected → entire frame dropped, no redacted_bytes."""
    cfg = StubBackendConfig(
        face_boxes=[DetectionBox(x=0, y=0, w=30, h=30, score=0.95, label="face")],
        child_count=1,
    )
    f = VisionPiiFilter(backend=StubVisionPiiBackend(cfg), allow_stub=True)
    result = f.redact(_tiny_jpeg())
    assert result.frame_rejected is True
    assert result.redacted_bytes is None
    assert result.rejection_reason is not None
    assert "child face detected" in result.rejection_reason


# ─── W3.1 OnnxFaceBackend (operator-supplied model paths) ───────────


def test_w3_1_onnx_backend_fails_when_model_missing(tmp_path):
    """Init with nonexistent model path → VisionPiiBackendUnavailable."""
    with pytest.raises(VisionPiiBackendUnavailable, match="face model not found"):
        OnnxFaceBackend(model_path=str(tmp_path / "no-such-model.onnx"))


def test_w3_1_from_env_fails_without_face_model(monkeypatch):
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    with pytest.raises(VisionPiiBackendUnavailable, match="not set"):
        OnnxFaceBackend.from_env()


def test_w3_1_from_env_fails_when_path_doesnt_exist(monkeypatch, tmp_path):
    monkeypatch.setenv("ETZ_VISION_PII_FACE_MODEL", str(tmp_path / "missing.onnx"))
    with pytest.raises(VisionPiiBackendUnavailable, match="face model not found"):
        OnnxFaceBackend.from_env()


def test_w3_1_from_env_fails_when_plate_model_missing(monkeypatch, tmp_path):
    """Face path exists (fake file ok at this gate) but plate path missing → fail-closed."""
    fake_face = tmp_path / "fake-face.onnx"
    fake_face.write_bytes(b"FAKE")
    monkeypatch.setenv("ETZ_VISION_PII_FACE_MODEL", str(fake_face))
    monkeypatch.setenv("ETZ_VISION_PII_PLATE_MODEL", str(tmp_path / "missing-plate.onnx"))
    # Init will fail trying to load fake face first (ONNX session creation fails).
    # If face load somehow succeeded, plate-missing would still raise. Either
    # way → VisionPiiBackendUnavailable.
    with pytest.raises(VisionPiiBackendUnavailable):
        OnnxFaceBackend.from_env()


def test_w3_1_resolve_backend_env_routes_to_onnx_when_centerface_selected(monkeypatch):
    """ETZ_VISION_PII_BACKEND=centerface-onnx → must try to instantiate
    OnnxFaceBackend; no face model path → fail-closed."""
    monkeypatch.setenv("ETZ_VISION_PII_BACKEND", "centerface-onnx")
    monkeypatch.delenv("ETZ_VISION_PII_FACE_MODEL", raising=False)
    with pytest.raises(VisionPiiBackendUnavailable, match="ETZ_VISION_PII_FACE_MODEL"):
        VisionPiiFilter()


def test_w3_1_corrupt_onnx_model_fails_closed(monkeypatch, tmp_path):
    """A non-ONNX file at the path → onnxruntime InferenceSession will reject
    it, the backend constructor must catch + raise VisionPiiBackendUnavailable."""
    bad = tmp_path / "not-actually-onnx.onnx"
    bad.write_bytes(b"this is not a valid ONNX model")
    with pytest.raises(VisionPiiBackendUnavailable, match="failed to load face"):
        OnnxFaceBackend(model_path=str(bad))


def test_out_of_bounds_boxes_are_clipped():
    """A face box outside the image must not crash the blur op."""
    cfg = StubBackendConfig(
        face_boxes=[
            DetectionBox(x=-50, y=-50, w=20, h=20, score=0.5, label="face"),
            DetectionBox(x=1000, y=1000, w=20, h=20, score=0.5, label="face"),
        ]
    )
    f = VisionPiiFilter(backend=StubVisionPiiBackend(cfg), allow_stub=True)
    result = f.redact(_tiny_jpeg())
    # Boxes report normally; blur skips them silently (no exception).
    assert not result.frame_rejected
    assert result.redacted_bytes is not None
    assert len(result.detections.faces) == 2
