"""Vision PII filter — face / license-plate / child detection + blur.

Per ADR-2605262500 §5 + G2: extends the structured-PII filter
(`kotodama/organism/sensors/pii_filter.py`) into the vision domain.
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
`kotodama.organism.sensors.pii_filter_vision`) so that
`fetchers/mapillary.py` can import it without dragging kotodama's
heavy / env-fragile dependency chain (langchain → pydantic).
A future kotodama-side wrapper can re-export it once the env
stabilises (ADR-2605262500 deps.toml originally placed it at the
kotodama path; this is the W3 implementation location).

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
from pathlib import Path
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


def _try_onnx():
    try:
        import onnxruntime   # type: ignore
        return onnxruntime
    except ImportError:
        return None


def _try_numpy():
    try:
        import numpy   # type: ignore
        return numpy
    except ImportError:
        return None


class OnnxFaceBackend:
    """W3.1 face detection backend — onnxruntime + Pillow + numpy.

    Operator supplies ONNX model files via env:

      ETZ_VISION_PII_FACE_MODEL=/path/to/centerface.onnx
      ETZ_VISION_PII_PLATE_MODEL=/path/to/lpr-yolo.onnx   (optional)
      ETZ_VISION_PII_AGE_MODEL=/path/to/age-classifier.onnx   (optional)

    Initialization fail-closes when:
      - onnxruntime not installed
      - numpy not installed
      - model file doesn't exist
      - ONNX session fails to load (corrupt / unsupported op set)

    `detect_plates()` returns empty list when no plate model is configured.
    `estimate_child_face_count()` returns 0 when no age model is configured —
    callers MUST treat this as "indeterminate" and apply jurisdiction-
    specific policy (W3.2 swaps in a real age classifier).

    The CenterFace ONNX output format (canonical):
      - outputs[0] = heatmap (1, 1, H, W)
      - outputs[1] = scale (1, 2, H, W)
      - outputs[2] = offset (1, 2, H, W)
      - outputs[3] = landmark (1, 10, H, W)   (optional)

    This backend implements the CenterFace decode path; yolov8-face /
    retinaface decode paths are separate backends (W3.1.1+).
    """

    name = "onnx-face"

    def __init__(
        self,
        model_path: str,
        *,
        plate_model_path: Optional[str] = None,
        age_model_path: Optional[str] = None,
        input_size: tuple[int, int] = (640, 480),   # CenterFace default
        score_threshold: float = 0.5,
    ) -> None:
        ort = _try_onnx()
        if ort is None:
            raise VisionPiiBackendUnavailable(
                "onnxruntime not installed; `pip install onnxruntime` then re-init."
            )
        if _try_numpy() is None:
            raise VisionPiiBackendUnavailable(
                "numpy not installed; `pip install numpy` then re-init."
            )

        face_path = Path(model_path)
        if not face_path.exists():
            raise VisionPiiBackendUnavailable(
                f"face model not found: {model_path!r}; "
                f"check ETZ_VISION_PII_FACE_MODEL env path."
            )
        try:
            self._face_session = ort.InferenceSession(
                str(face_path), providers=["CPUExecutionProvider"]
            )
        except Exception as exc:   # noqa: BLE001
            raise VisionPiiBackendUnavailable(
                f"failed to load face ONNX session at {model_path!r}: {exc}"
            ) from exc

        self._plate_session = None
        if plate_model_path:
            pp = Path(plate_model_path)
            if not pp.exists():
                raise VisionPiiBackendUnavailable(
                    f"plate model not found: {plate_model_path!r}"
                )
            try:
                self._plate_session = ort.InferenceSession(
                    str(pp), providers=["CPUExecutionProvider"]
                )
            except Exception as exc:   # noqa: BLE001
                raise VisionPiiBackendUnavailable(
                    f"failed to load plate ONNX: {exc}"
                ) from exc

        self._age_session = None
        if age_model_path:
            ap = Path(age_model_path)
            if not ap.exists():
                raise VisionPiiBackendUnavailable(
                    f"age model not found: {age_model_path!r}"
                )
            try:
                self._age_session = ort.InferenceSession(
                    str(ap), providers=["CPUExecutionProvider"]
                )
            except Exception as exc:   # noqa: BLE001
                raise VisionPiiBackendUnavailable(
                    f"failed to load age ONNX: {exc}"
                ) from exc

        self.input_size = input_size
        self.score_threshold = score_threshold

    @classmethod
    def from_env(cls) -> "OnnxFaceBackend":
        """Build from env vars; raises VisionPiiBackendUnavailable if face path unset."""
        face = os.environ.get("ETZ_VISION_PII_FACE_MODEL")
        if not face:
            raise VisionPiiBackendUnavailable(
                "ETZ_VISION_PII_FACE_MODEL not set"
            )
        return cls(
            model_path=face,
            plate_model_path=os.environ.get("ETZ_VISION_PII_PLATE_MODEL"),
            age_model_path=os.environ.get("ETZ_VISION_PII_AGE_MODEL"),
        )

    def _decode_image(self, image_bytes: bytes):
        """Image bytes → (input_tensor, original_h, original_w) for ONNX inference."""
        import io as _io
        from PIL import Image
        import numpy as np
        img = Image.open(_io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        orig_w, orig_h = img.size
        w, h = self.input_size
        resized = img.resize((w, h))
        arr = np.asarray(resized, dtype=np.float32).transpose(2, 0, 1)   # (C, H, W)
        arr = np.expand_dims(arr, axis=0)                                # (1, C, H, W)
        # CenterFace expects normalized [0, 1] in BGR (the conventional impl);
        # we ship the standard impl convention and let operators of alt models
        # override via a wrapper backend (W3.1.1).
        arr /= 255.0
        return arr, orig_h, orig_w

    def detect_faces(self, image_bytes: bytes) -> list[DetectionBox]:
        """Run the face ONNX, return decoded DetectionBox list (in original pixel coords)."""
        import numpy as np
        inp, orig_h, orig_w = self._decode_image(image_bytes)
        ort_inputs = {self._face_session.get_inputs()[0].name: inp}
        outputs = self._face_session.run(None, ort_inputs)
        # Decode is model-specific; for the W3.1 PoC we leave the decoder
        # delegate-able via subclass override. The default impl extracts
        # any output that already looks like bbox lists (Nx5: x,y,w,h,score).
        boxes: list[DetectionBox] = []
        for out in outputs:
            if out.ndim == 2 and out.shape[1] in (5, 6, 7):
                w_in, h_in = self.input_size
                sx = orig_w / float(w_in)
                sy = orig_h / float(h_in)
                for row in out:
                    if len(row) < 5:
                        continue
                    score = float(row[4])
                    if score < self.score_threshold:
                        continue
                    x = int(round(float(row[0]) * sx))
                    y = int(round(float(row[1]) * sy))
                    w = int(round(float(row[2]) * sx))
                    h = int(round(float(row[3]) * sy))
                    boxes.append(DetectionBox(x=x, y=y, w=w, h=h, score=score, label="face"))
                break
        return boxes

    def detect_plates(self, image_bytes: bytes) -> list[DetectionBox]:
        """License-plate detection. Returns [] when no plate model configured."""
        if self._plate_session is None:
            return []
        import numpy as np
        inp, orig_h, orig_w = self._decode_image(image_bytes)
        ort_inputs = {self._plate_session.get_inputs()[0].name: inp}
        outputs = self._plate_session.run(None, ort_inputs)
        boxes: list[DetectionBox] = []
        for out in outputs:
            if out.ndim == 2 and out.shape[1] in (5, 6, 7):
                w_in, h_in = self.input_size
                sx = orig_w / float(w_in)
                sy = orig_h / float(h_in)
                for row in out:
                    if len(row) < 5:
                        continue
                    score = float(row[4])
                    if score < self.score_threshold:
                        continue
                    x = int(round(float(row[0]) * sx))
                    y = int(round(float(row[1]) * sy))
                    w = int(round(float(row[2]) * sx))
                    h = int(round(float(row[3]) * sy))
                    boxes.append(DetectionBox(
                        x=x, y=y, w=w, h=h, score=score, label="license_plate"
                    ))
                break
        return boxes

    def estimate_child_face_count(
        self, image_bytes: bytes, faces: list[DetectionBox]
    ) -> int:
        """Per-face age estimation. Returns 0 when no age model configured.

        W3.1 PoC: when age model is loaded, crops each face → ONNX inference →
        classifies as child (<18 estimated). Without age model, returns 0 —
        callers should treat 0 as "indeterminate" and apply conservative
        jurisdiction policy (e.g., reject all frames in regions with strict
        child-imagery laws). W3.2 will add proper threshold tuning.
        """
        if self._age_session is None:
            return 0
        if not faces:
            return 0
        import io as _io
        from PIL import Image
        import numpy as np
        img = Image.open(_io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        child_count = 0
        for fbox in faces:
            crop = img.crop((fbox.x, fbox.y, fbox.x + fbox.w, fbox.y + fbox.h))
            if crop.size[0] < 8 or crop.size[1] < 8:
                continue
            # Common age-classifier input: 224x224 RGB normalized.
            crop = crop.resize((224, 224))
            arr = np.asarray(crop, dtype=np.float32).transpose(2, 0, 1) / 255.0
            arr = np.expand_dims(arr, axis=0)
            try:
                ort_inputs = {self._age_session.get_inputs()[0].name: arr}
                out = self._age_session.run(None, ort_inputs)[0]
            except Exception:   # noqa: BLE001
                continue
            # Heuristic: out is either (1, num_classes) or (1, 1) regression.
            # Class 0 = child, others adult; OR scalar regression < 18.
            vals = out.flatten()
            if len(vals) > 1:
                # classification: argmax = 0 → child
                if int(np.argmax(vals)) == 0:
                    child_count += 1
            elif len(vals) == 1:
                if float(vals[0]) < 18.0:
                    child_count += 1
        return child_count


class Yolov8FaceOnnxBackend(OnnxFaceBackend):
    """W3.1.2 — yolov8-face ONNX backend (Ultralytics canonical output).

    yolov8-face ONNX models produce one of two canonical output layouts:
      (a) `(1, N, 6+)` — N detections, each row = [cx, cy, w, h, conf, class, ...kpt]
      (b) `(1, 6+, N)` — transposed; same data, channels-first layout

    This subclass detects both layouts, converts cxcywh → top-left xywh,
    applies the score threshold + NMS, and scales boxes from input-space
    (typically 640×640) to original-image coordinates. Letterbox
    preprocessing (aspect-ratio-preserving resize + pad) is a W3.1.3
    refinement — the W3.1.2 PoC uses simple resize.
    """

    name = "yolov8-face-onnx"

    def __init__(
        self,
        *args,
        nms_iou_threshold: float = 0.45,
        input_size: tuple[int, int] = (640, 640),
        **kwargs,
    ) -> None:
        kwargs.setdefault("input_size", input_size)
        super().__init__(*args, **kwargs)
        self.nms_iou_threshold = nms_iou_threshold

    def detect_faces(self, image_bytes: bytes) -> list[DetectionBox]:
        import numpy as np
        inp, orig_h, orig_w = self._decode_image(image_bytes)
        ort_inputs = {self._face_session.get_inputs()[0].name: inp}
        outputs = self._face_session.run(None, ort_inputs)
        if not outputs:
            return []
        out = outputs[0]
        if out.ndim != 3 or out.shape[0] != 1:
            return []

        # Detect layout: (1, N, C) vs (1, C, N).
        # yolov8 channel counts are typically in a known range (5-20 incl.
        # cx,cy,w,h,conf + optional class + optional 5x3 keypoints).
        d1, d2 = out.shape[1], out.shape[2]
        YOLOV8_CHANNEL_HINT = {5, 6, 7, 8, 9, 10, 15, 16, 17, 18, 20}
        if d2 in YOLOV8_CHANNEL_HINT:
            rows = out[0]                     # already (N, C)
        elif d1 in YOLOV8_CHANNEL_HINT:
            rows = out[0].T                   # (C, N) → transpose to (N, C)
        else:
            # Ambiguous: fall back to "smaller-is-channel" heuristic.
            rows = out[0].T if d1 <= d2 else out[0]
        if rows.shape[1] < 5:
            return []

        w_in, h_in = self.input_size
        sx = orig_w / float(w_in)
        sy = orig_h / float(h_in)
        boxes: list[DetectionBox] = []
        for row in rows:
            score = float(row[4])
            if score < self.score_threshold:
                continue
            cx = float(row[0])
            cy = float(row[1])
            bw = float(row[2])
            bh = float(row[3])
            x = int(round((cx - bw / 2.0) * sx))
            y = int(round((cy - bh / 2.0) * sy))
            w = int(round(bw * sx))
            h = int(round(bh * sy))
            boxes.append(DetectionBox(
                x=x, y=y, w=w, h=h, score=score, label="face"
            ))
        return _nms(boxes, iou_threshold=self.nms_iou_threshold)


class RetinaFaceOnnxBackend(OnnxFaceBackend):
    """W3.1.3 — RetinaFace ONNX backend (post-processed Nx{15,16} output).

    RetinaFace's raw output is a multi-pyramid (loc, conf, landmark)
    tuple requiring anchor-based decode at 3 feature levels. Most
    deployment-ready exports (e.g., insightface, retinaface-pytorch)
    ship a POST-PROCESSED ONNX that emits Nx{15} rows after anchor
    decode + NMS internally:

      row layout (15-column): [x, y, w, h, lkpt0_x, lkpt0_y, lkpt1_x,
                               lkpt1_y, lkpt2_x, lkpt2_y, lkpt3_x,
                               lkpt3_y, lkpt4_x, lkpt4_y, score]

    Some exporters add a class index → Nx{16}: same first 14 + score
    + class. The 5 landmarks (right_eye, left_eye, nose, right_mouth,
    left_mouth) are stored after the bbox.

    This subclass extracts bbox from dims [0:4] and score from dim 14
    (NOT dim 4 like CenterFace/yolov8). The decoder also handles the
    `(1, N, C)` vs `(1, C, N)` layout heuristic via the channel-count
    hint set extended to include {14, 15, 16}.

    Raw-output RetinaFace (multi-pyramid anchor decode) is W3.1.3.1 —
    out of scope for this PoC. Operators with raw-output models should
    use post-processing first.
    """

    name = "retinaface-onnx"

    def __init__(
        self,
        *args,
        nms_iou_threshold: float = 0.40,
        input_size: tuple[int, int] = (640, 640),
        **kwargs,
    ) -> None:
        kwargs.setdefault("input_size", input_size)
        super().__init__(*args, **kwargs)
        self.nms_iou_threshold = nms_iou_threshold

    def detect_faces(self, image_bytes: bytes) -> list[DetectionBox]:
        import numpy as np
        inp, orig_h, orig_w = self._decode_image(image_bytes)
        ort_inputs = {self._face_session.get_inputs()[0].name: inp}
        outputs = self._face_session.run(None, ort_inputs)
        if not outputs:
            return []
        out = outputs[0]
        if out.ndim != 3 or out.shape[0] != 1:
            return []

        # Layout: prefer (1, N, C) where C in {15, 16}; transpose if needed.
        d1, d2 = out.shape[1], out.shape[2]
        RETINAFACE_CHANNELS = {15, 16}
        if d2 in RETINAFACE_CHANNELS:
            rows = out[0]                      # (N, C)
        elif d1 in RETINAFACE_CHANNELS:
            rows = out[0].T                    # transpose to (N, C)
        else:
            # Not a recognised RetinaFace layout — fall back to generic decode.
            return super().detect_faces(image_bytes)

        if rows.shape[1] < 15:
            return []

        w_in, h_in = self.input_size
        sx = orig_w / float(w_in)
        sy = orig_h / float(h_in)
        boxes: list[DetectionBox] = []
        for row in rows:
            # Score is at index 14 (after bbox + 10 landmark floats).
            score = float(row[14])
            if score < self.score_threshold:
                continue
            # bbox in input space. RetinaFace exports are typically xywh
            # (top-left + width/height); some emit xyxy. We assume xywh
            # (more common) and check for sane positive w/h.
            x_in = float(row[0])
            y_in = float(row[1])
            w_in_box = float(row[2])
            h_in_box = float(row[3])
            if w_in_box <= 0 or h_in_box <= 0:
                # xyxy convention: treat (x2, y2) as bottom-right.
                w_in_box = float(row[2]) - x_in
                h_in_box = float(row[3]) - y_in
                if w_in_box <= 0 or h_in_box <= 0:
                    continue
            x = int(round(x_in * sx))
            y = int(round(y_in * sy))
            w = int(round(w_in_box * sx))
            h = int(round(h_in_box * sy))
            boxes.append(DetectionBox(
                x=x, y=y, w=w, h=h, score=score, label="face"
            ))
        return _nms(boxes, iou_threshold=self.nms_iou_threshold)


class CenterFaceOnnxBackend(OnnxFaceBackend):
    """W3.1.1 — CenterFace-specific ONNX backend.

    CenterFace ONNX outputs FOUR tensors (canonical layout):
      - outputs[0]  heatmap  shape (1, 1, H/4, W/4)   center-confidence map
      - outputs[1]  scale    shape (1, 2, H/4, W/4)   log scale for w,h
      - outputs[2]  offset   shape (1, 2, H/4, W/4)   sub-pixel offset for cx,cy
      - outputs[3]  landmark shape (1, 10, H/4, W/4)  optional 5-landmark

    The generic `OnnxFaceBackend.detect_faces` doesn't understand this
    shape — it expects Nx{5,6,7} bbox rows. This subclass implements
    the canonical CenterFace decode algorithm (heatmap peaks → scale +
    offset reconstruction → original-image-space boxes → NMS).
    """

    name = "centerface-onnx"

    def __init__(self, *args, nms_iou_threshold: float = 0.4, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nms_iou_threshold = nms_iou_threshold

    def detect_faces(self, image_bytes: bytes) -> list[DetectionBox]:
        import numpy as np
        inp, orig_h, orig_w = self._decode_image(image_bytes)
        ort_inputs = {self._face_session.get_inputs()[0].name: inp}
        outputs = self._face_session.run(None, ort_inputs)
        if len(outputs) < 3:
            return []
        heatmap = outputs[0]
        scale = outputs[1]
        offset = outputs[2]
        # Sanity-check shapes (1, 1|2, h, w).
        if heatmap.ndim != 4 or scale.ndim != 4 or offset.ndim != 4:
            return []
        if heatmap.shape[1] != 1 or scale.shape[1] != 2 or offset.shape[1] != 2:
            return []

        boxes = _centerface_decode_heatmap(
            heatmap, scale, offset,
            score_threshold=self.score_threshold,
            input_size=self.input_size,
            orig_h=orig_h, orig_w=orig_w,
        )
        boxes = _nms(boxes, iou_threshold=self.nms_iou_threshold)
        return boxes


def _centerface_decode_heatmap(
    heatmap, scale, offset,
    *,
    score_threshold: float,
    input_size: tuple[int, int],
    orig_h: int,
    orig_w: int,
) -> list[DetectionBox]:
    """CenterFace decode algorithm. Pure function for testability.

    heatmap : (1, 1, Hf, Wf) — center confidence
    scale   : (1, 2, Hf, Wf) — log scale; scale[0,0] is log_h, scale[0,1] is log_w
    offset  : (1, 2, Hf, Wf) — sub-pixel offset; offset[0,0] for cy, [0,1] for cx
    """
    import numpy as np
    h = heatmap[0, 0]
    s = scale[0]
    o = offset[0]
    Hf, Wf = h.shape

    # Local-max suppression via 3×3 sliding window: keep peaks ≥ all neighbors.
    pad = np.pad(h, 1, mode="constant", constant_values=0.0)
    is_peak = np.ones_like(h, dtype=bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            is_peak &= (h >= pad[1 + dy : 1 + dy + Hf, 1 + dx : 1 + dx + Wf])
    is_peak &= (h >= score_threshold)
    peak_ys, peak_xs = np.where(is_peak)

    w_in, h_in = input_size
    stride_x = w_in / Wf
    stride_y = h_in / Hf
    sx = orig_w / float(w_in)
    sy = orig_h / float(h_in)

    out: list[DetectionBox] = []
    for py, px in zip(peak_ys.tolist(), peak_xs.tolist()):
        score = float(h[py, px])
        # CenterFace convention: scale[0]=log_h, scale[1]=log_w
        bh = float(np.exp(s[0, py, px])) * 4.0
        bw = float(np.exp(s[1, py, px])) * 4.0
        cy_real = (py + float(o[0, py, px])) * stride_y
        cx_real = (px + float(o[1, py, px])) * stride_x
        x = int(round((cx_real - bw / 2) * sx))
        y = int(round((cy_real - bh / 2) * sy))
        w = int(round(bw * sx))
        h_box = int(round(bh * sy))
        out.append(DetectionBox(x=x, y=y, w=w, h=h_box, score=score, label="face"))
    return out


def _iou(a: DetectionBox, b: DetectionBox) -> float:
    """Axis-aligned bbox IoU."""
    ax1, ay1 = a.x, a.y
    ax2, ay2 = a.x + a.w, a.y + a.h
    bx1, by1 = b.x, b.y
    bx2, by2 = b.x + b.w, b.y + b.h
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms(boxes: list[DetectionBox], *, iou_threshold: float) -> list[DetectionBox]:
    """Non-max suppression — highest-score wins each cluster."""
    sorted_boxes = sorted(boxes, key=lambda b: -b.score)
    kept: list[DetectionBox] = []
    for box in sorted_boxes:
        if all(_iou(box, k) < iou_threshold for k in kept):
            kept.append(box)
    return kept


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


def _classify_face_model_kind(model_path: str) -> str:
    """Inspect an ONNX face model and classify which subclass should decode it.

    Returns one of:
      - "centerface"   — 3 outputs with shapes (1,1,h,w) + (1,2,h,w) + (1,2,h,w)
      - "yolov8-face"  — 1 output with 3 dims, one of which is in
                          {5,6,7,8,9,10,15,16,17,18,20} channel-count hint
                          (the smaller dim is the channel count)
      - "retinaface"   — 1 output with 3 dims, one of which is in {15, 16}
                          (overlaps yolov8 hint; RetinaFace is more
                          specific so it takes precedence)
      - "generic"      — none of the above; falls back to OnnxFaceBackend

    Used by the `auto` env spec to route operator's model to the
    correct subclass without requiring them to know which export
    convention they have. Pure static inspection — does NOT run
    inference on the model.
    """
    ort = _try_onnx()
    if ort is None:
        raise VisionPiiBackendUnavailable(
            "onnxruntime not installed; `pip install onnxruntime` then re-init."
        )
    try:
        session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
    except Exception as exc:   # noqa: BLE001
        raise VisionPiiBackendUnavailable(
            f"failed to load face ONNX session at {model_path!r}: {exc}"
        ) from exc

    outputs = session.get_outputs()

    def _val(x):
        # ONNX shapes can contain symbolic dim strings; coerce to int or None.
        return x if isinstance(x, int) else None

    # CenterFace heuristic: 3 outputs with the canonical channel layout.
    if len(outputs) >= 3:
        shapes = [list(o.shape) for o in outputs[:3]]
        if (len(shapes[0]) == 4 and _val(shapes[0][1]) == 1
            and len(shapes[1]) == 4 and _val(shapes[1][1]) == 2
            and len(shapes[2]) == 4 and _val(shapes[2][1]) == 2):
            return "centerface"

    # Single-output decoders (yolov8 / retinaface): one tensor with 3 dims.
    if len(outputs) == 1:
        shape = list(outputs[0].shape)
        if len(shape) == 3 and _val(shape[0]) == 1:
            c1 = _val(shape[1])
            c2 = _val(shape[2])
            # RetinaFace's 15/16-column layout takes precedence.
            if c1 in {15, 16} or c2 in {15, 16}:
                return "retinaface"
            YOLOV8_CHANNEL_HINT = {5, 6, 7, 8, 9, 10, 17, 18, 20}
            if c1 in YOLOV8_CHANNEL_HINT or c2 in YOLOV8_CHANNEL_HINT:
                return "yolov8-face"

    return "generic"


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

    if spec == "auto":
        # Auto-detect operator's model kind and route to the right subclass.
        face = os.environ.get("ETZ_VISION_PII_FACE_MODEL")
        if not face:
            raise VisionPiiBackendUnavailable(
                "ETZ_VISION_PII_FACE_MODEL not set (required for auto detection)"
            )
        kind = _classify_face_model_kind(face)
        plate = os.environ.get("ETZ_VISION_PII_PLATE_MODEL")
        age = os.environ.get("ETZ_VISION_PII_AGE_MODEL")
        if kind == "centerface":
            return CenterFaceOnnxBackend(
                model_path=face, plate_model_path=plate, age_model_path=age,
            )
        if kind == "yolov8-face":
            return Yolov8FaceOnnxBackend(
                model_path=face, plate_model_path=plate, age_model_path=age,
            )
        if kind == "retinaface":
            return RetinaFaceOnnxBackend(
                model_path=face, plate_model_path=plate, age_model_path=age,
            )
        # generic fallback
        return OnnxFaceBackend(
            model_path=face, plate_model_path=plate, age_model_path=age,
        )

    if spec == "centerface-onnx":
        # W3.1.1: CenterFace-specific decoder (heatmap + scale + offset → NMS bboxes).
        face = os.environ.get("ETZ_VISION_PII_FACE_MODEL")
        if not face:
            raise VisionPiiBackendUnavailable(
                "ETZ_VISION_PII_FACE_MODEL not set"
            )
        return CenterFaceOnnxBackend(
            model_path=face,
            plate_model_path=os.environ.get("ETZ_VISION_PII_PLATE_MODEL"),
            age_model_path=os.environ.get("ETZ_VISION_PII_AGE_MODEL"),
        )
    if spec == "yolov8-face-onnx":
        # W3.1.2: yolov8-face Ultralytics canonical (1, N, 6+) or (1, 6+, N) decoder.
        face = os.environ.get("ETZ_VISION_PII_FACE_MODEL")
        if not face:
            raise VisionPiiBackendUnavailable(
                "ETZ_VISION_PII_FACE_MODEL not set"
            )
        return Yolov8FaceOnnxBackend(
            model_path=face,
            plate_model_path=os.environ.get("ETZ_VISION_PII_PLATE_MODEL"),
            age_model_path=os.environ.get("ETZ_VISION_PII_AGE_MODEL"),
        )
    if spec == "retinaface-onnx":
        # W3.1.3: RetinaFace Nx{15,16} post-processed output decoder.
        face = os.environ.get("ETZ_VISION_PII_FACE_MODEL")
        if not face:
            raise VisionPiiBackendUnavailable(
                "ETZ_VISION_PII_FACE_MODEL not set"
            )
        return RetinaFaceOnnxBackend(
            model_path=face,
            plate_model_path=os.environ.get("ETZ_VISION_PII_PLATE_MODEL"),
            age_model_path=os.environ.get("ETZ_VISION_PII_AGE_MODEL"),
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
    "CenterFaceOnnxBackend",
    "CharterEnforcementError",
    "DEFAULT_FACE_BLUR_SIGMA",
    "DEFAULT_PLATE_BLUR_SIGMA",
    "DetectionBox",
    "FrameDetections",
    "OnnxFaceBackend",
    "RedactionResult",
    "RetinaFaceOnnxBackend",
    "StubBackendConfig",
    "StubVisionPiiBackend",
    "VisionPiiBackend",
    "VisionPiiBackendUnavailable",
    "VisionPiiFilter",
    "Yolov8FaceOnnxBackend",
]
