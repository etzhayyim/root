"""Vision PII filter — face / license-plate / child detection + blur.

Per ADR-2605262500 §5 + G2: extends the structured-PII filter
(`pymagatama/organism/sensors/pii_filter.py`) into the vision domain.
Required at Mapillary fetch time (`fetchers/mapillary.py`); also
applicable to any future image-bearing Tier-C source.

Three concerns are layered:

  1. **Face blur**         — detect, then Gaussian-blur σ ≥ 15 px each box.
  2. **License plate blur** — detect, then Gaussian-blur σ ≥ 20 px each box.
  3. **Child detection**   — heuristic age estimate on detected faces;
                              if any face < 18 years estimated, the
                              ENTIRE frame is rejected (no partial
                              blur attempted — fail-closed for child
                              presence).

Architecture is fail-closed by default:

  - No detection backend loaded → every `redact()` call raises
    `VisionPiiBackendUnavailable`.
  - Operator opts into a real backend via `ETZ_VISION_PII_BACKEND`
    (one of: `centerface-onnx`, `yolov8-face-onnx`, `stub-allow`).
  - `stub-allow` is for tests / dry-runs only and is gated behind
    `ETZ_VISION_PII_ALLOW_STUB=1` — without that env, the stub is
    rejected even if requested.

This module lives at `e7m_dataset.vision_pii_filter` (not at
`pymagatama.organism.sensors.pii_filter_vision`) so that
`fetchers/mapillary.py` can import it without dragging pymagatama's
heavy / env-fragile dependency chain (langchain → pydantic).
A future pymagatama-side wrapper can re-export it once the env
stabilises (ADR-2605262500 deps.toml originally placed it at the
pymagatama path; this is the W3 implementation location).

Backends (deferred to W3.1 real-model installation):

  - `centerface-onnx`     — small face detector, MIT, 6 MB ONNX
  - `yolov8-face-onnx`    — yolov8n-face, AGPL-3 base but Apache-2.0
                              re-implementations exist; operator picks
  - `retinaface-onnx`     — heavier RetinaFace + 4-landmark output
  - `stub-allow`          — synchronous in-process stub; configurable
                              via `StubBackendConfig` for tests

License-plate detection is a separate model (CCPD-trained YOLO is
common); some face detectors also output plate boxes via auxiliary
heads. The operator wires both via env-paths (W3.1):

  ETZ_VISION_PII_FACE_MODEL=/path/to/centerface.onnx
  ETZ_VISION_PII_PLATE_MODEL=/path/to/lpr-yolo.onnx
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field
from typing import Optional, Protocol


# ─── exceptions ─────────────────────────────────────────────────────


class VisionPiiBackendUnavailable(RuntimeError):
    """Raised when no detection backend can load + strict mode is on
    (which is the default; only `ETZ_VISION_PII_ALLOW_STUB=1` opens it)."""


class CharterEnforcementError(RuntimeError):
    """Raised when a frame violates G2 hard rules (e.g., child detected
    + frame_rejected propagation across a boundary that expected redacted bytes)."""


# ─── result types ───────────────────────────────────────────────────


@dataclass(frozen=True)
class DetectionBox:
    """A single detection — pixel-space (x, y, w, h) bbox + confidence."""
    x: int
    y: int
    w: int
    h: int
    score: float
    label: str  # "face" / "license_plate" / future labels


@dataclass
class FrameDetections:
    faces: list[DetectionBox] = field(default_factory=list)
    plates: list[DetectionBox] = field(default_factory=list)
    child_face_count: int = 0


@dataclass
class RedactionResult:
    """Outcome of `VisionPiiFilter.redact(image_bytes)`.

    `redacted_bytes` is the safe-for-downstream image bytes; the
    original bytes stay in the caller's possession (the fetcher pins
    them to annex behind a Council-attestation-gated unlock per
    ADR-2605262500 §5). `frame_rejected=True` means no redacted_bytes
    will be produced — the entire frame is dropped fail-closed for
    child presence."""

    detections: FrameDetections
    frame_rejected: bool
    rejection_reason: Optional[str]   # set iff frame_rejected
    redacted_bytes: Optional[bytes]   # None iff frame_rejected
    backend_name: str


# ─── backend protocol ───────────────────────────────────────────────


class VisionPiiBackend(Protocol):
    """Pluggable detection backend. Implementations under
    `e7m_dataset.vision_pii_backends.*`."""

    name: str

    def detect_faces(self, image_bytes: bytes) -> list[DetectionBox]: ...

    def detect_plates(self, image_bytes: bytes) -> list[DetectionBox]: ...

    def estimate_child_face_count(
        self, image_bytes: bytes, faces: list[DetectionBox]
    ) -> int: ...


# ─── stub backend (tests / dry-runs only) ───────────────────────────


@dataclass
class StubBackendConfig:
    """Configurable stub for tests. Returns the boxes you set up here.

    `face_boxes` / `plate_boxes` are the detections returned per call.
    `child_count` is what `estimate_child_face_count` returns."""

    face_boxes: list[DetectionBox] = field(default_factory=list)
    plate_boxes: list[DetectionBox] = field(default_factory=list)
    child_count: int = 0


class StubVisionPiiBackend:
    """Test/dry-run backend.  Gate: `ETZ_VISION_PII_ALLOW_STUB=1`
    (verified by `VisionPiiFilter.__init__` — NOT here, so tests can
    instantiate this class directly with `allow_stub=True`)."""

    name = "stub-allow"

    def __init__(self, config: Optional[StubBackendConfig] = None) -> None:
        self.config = config or StubBackendConfig()

    def detect_faces(self, image_bytes: bytes) -> list[DetectionBox]:
        return list(self.config.face_boxes)

    def detect_plates(self, image_bytes: bytes) -> list[DetectionBox]:
        return list(self.config.plate_boxes)

    def estimate_child_face_count(
        self, image_bytes: bytes, faces: list[DetectionBox]
    ) -> int:
        return self.config.child_count


# ─── filter ─────────────────────────────────────────────────────────


# Charter Rider §2-mandated blur radii (per ADR-2605262500 §5 + row #67).
DEFAULT_FACE_BLUR_SIGMA = 15
DEFAULT_PLATE_BLUR_SIGMA = 20


class VisionPiiFilter:
    """Vision PII filter — G2 enforcement gate for image ingest.

    Default policy is fail-closed. Tests use the stub backend with
    `allow_stub=True` (mirrors the `ETZ_VISION_PII_ALLOW_STUB=1` env
    that production code respects)."""

    def __init__(
        self,
        *,
        backend: Optional[VisionPiiBackend] = None,
        face_blur_sigma: int = DEFAULT_FACE_BLUR_SIGMA,
        plate_blur_sigma: int = DEFAULT_PLATE_BLUR_SIGMA,
        allow_stub: bool = False,
    ) -> None:
        self.face_blur_sigma = face_blur_sigma
        self.plate_blur_sigma = plate_blur_sigma

        if backend is None:
            backend = _resolve_backend_from_env(allow_stub=allow_stub)
        if isinstance(backend, StubVisionPiiBackend):
            # Even if the caller hands in a stub, gate it on allow_stub.
            env_allow = os.environ.get("ETZ_VISION_PII_ALLOW_STUB") == "1"
            if not (allow_stub or env_allow):
                raise VisionPiiBackendUnavailable(
                    "stub backend rejected: set ETZ_VISION_PII_ALLOW_STUB=1 "
                    "(tests / dry-runs only) or install a real backend."
                )
        self.backend = backend

    def redact(
        self,
        image_bytes: bytes,
        *,
        mime_type: str = "image/jpeg",
    ) -> RedactionResult:
        """Run face + plate detection, blur, and child-presence check.

        Returns RedactionResult. On child detection the frame is
        rejected (no redacted_bytes produced); the caller MUST drop
        the frame entirely. On detection backend or PIL unavailability
        with strict mode on, raises VisionPiiBackendUnavailable."""

        faces = self.backend.detect_faces(image_bytes)
        plates = self.backend.detect_plates(image_bytes)
        child_count = self.backend.estimate_child_face_count(image_bytes, faces)

        detections = FrameDetections(
            faces=faces, plates=plates, child_face_count=child_count
        )

        if child_count > 0:
            return RedactionResult(
                detections=detections,
                frame_rejected=True,
                rejection_reason=(
                    f"child face detected (count={child_count}); "
                    "frame fail-closed per ADR-2605262500 §5"
                ),
                redacted_bytes=None,
                backend_name=self.backend.name,
            )

        # Apply blur over detected boxes.
        try:
            redacted = _blur_boxes(
                image_bytes,
                faces,
                plates,
                face_sigma=self.face_blur_sigma,
                plate_sigma=self.plate_blur_sigma,
                mime_type=mime_type,
            )
        except _PillowUnavailable as exc:
            raise VisionPiiBackendUnavailable(
                f"Pillow not available for blur operation: {exc}"
            ) from exc

        return RedactionResult(
            detections=detections,
            frame_rejected=False,
            rejection_reason=None,
            redacted_bytes=redacted,
            backend_name=self.backend.name,
        )


# ─── env-driven backend resolution ──────────────────────────────────


def _resolve_backend_from_env(*, allow_stub: bool) -> VisionPiiBackend:
    """Resolve the backend per ETZ_VISION_PII_BACKEND env var.

    Honors `allow_stub=True` AND `ETZ_VISION_PII_ALLOW_STUB=1` only.
    Real ONNX backends are W3.1 deliverables — the W3.0 PoC ships
    only the stub path."""
    spec = os.environ.get("ETZ_VISION_PII_BACKEND", "").strip().lower()
    env_allow_stub = os.environ.get("ETZ_VISION_PII_ALLOW_STUB") == "1"

    if spec == "stub-allow":
        if not (allow_stub or env_allow_stub):
            raise VisionPiiBackendUnavailable(
                "stub-allow backend requires ETZ_VISION_PII_ALLOW_STUB=1"
            )
        return StubVisionPiiBackend()

    if spec in {"centerface-onnx", "yolov8-face-onnx", "retinaface-onnx"}:
        raise VisionPiiBackendUnavailable(
            f"backend '{spec}' is a W3.1 deliverable; operator must install "
            f"model files + onnxruntime + Pillow + provide model paths via "
            f"ETZ_VISION_PII_FACE_MODEL / ETZ_VISION_PII_PLATE_MODEL envs."
        )

    if not spec:
        raise VisionPiiBackendUnavailable(
            "no ETZ_VISION_PII_BACKEND set. Choose one of: "
            "'centerface-onnx' / 'yolov8-face-onnx' / 'retinaface-onnx' "
            "(W3.1 real models) or 'stub-allow' + ETZ_VISION_PII_ALLOW_STUB=1 "
            "for tests."
        )

    raise VisionPiiBackendUnavailable(
        f"unknown backend '{spec}'. "
        f"Known: centerface-onnx / yolov8-face-onnx / retinaface-onnx / stub-allow."
    )


# ─── blur op (Pillow) ───────────────────────────────────────────────


class _PillowUnavailable(RuntimeError):
    pass


def _blur_boxes(
    image_bytes: bytes,
    faces: list[DetectionBox],
    plates: list[DetectionBox],
    *,
    face_sigma: int,
    plate_sigma: int,
    mime_type: str,
) -> bytes:
    """Apply Gaussian blur over each detection box. Pillow required."""
    try:
        from PIL import Image, ImageFilter   # type: ignore
    except ImportError as exc:
        raise _PillowUnavailable(str(exc)) from exc

    img = Image.open(io.BytesIO(image_bytes))
    img.load()

    for box, sigma in [(b, face_sigma) for b in faces] + [
        (b, plate_sigma) for b in plates
    ]:
        x0 = max(0, box.x)
        y0 = max(0, box.y)
        x1 = min(img.width, box.x + box.w)
        y1 = min(img.height, box.y + box.h)
        if x1 <= x0 or y1 <= y0:
            continue
        region = img.crop((x0, y0, x1, y1)).filter(
            ImageFilter.GaussianBlur(radius=sigma)
        )
        img.paste(region, (x0, y0))

    fmt = "JPEG" if "jpeg" in mime_type or "jpg" in mime_type else "PNG"
    out = io.BytesIO()
    img.save(out, format=fmt)
    return out.getvalue()


__all__ = [
    "CharterEnforcementError",
    "DEFAULT_FACE_BLUR_SIGMA",
    "DEFAULT_PLATE_BLUR_SIGMA",
    "DetectionBox",
    "FrameDetections",
    "RedactionResult",
    "StubBackendConfig",
    "StubVisionPiiBackend",
    "VisionPiiBackend",
    "VisionPiiBackendUnavailable",
    "VisionPiiFilter",
]
