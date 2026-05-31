"""Vision PII filter operator-side diagnostic CLI.

Usage:

  # 1. Validate current env setup:
  python3 -m e7m_dataset.vision_pii_diagnose check
  # → reports onnxruntime / numpy / pillow / scipy availability
  # → reports ETZ_VISION_PII_* env vars
  # → if FACE_MODEL set, classifies it + names the backend that would be used
  # → exit 0 = ready, 1 = missing model, 2 = missing critical dep

  # 2. Classify a specific ONNX model:
  python3 -m e7m_dataset.vision_pii_diagnose classify /path/to/face.onnx
  # → "centerface" | "yolov8-face" | "retinaface" | "generic"

  # 3. Smoke-test a backend against a synthetic 640x480 RGB image:
  python3 -m e7m_dataset.vision_pii_diagnose smoke /path/to/face.onnx
  # → loads via the auto-detect kind, runs detect_faces, prints count

Reduces operator-side production-rollout debugging — before running
Mapillary fetch w/ ETZ_VISION_PII_BACKEND env, run `check` to confirm
that real backend would load + Pillow blur works.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path
from typing import Optional


_REQUIRED_DEPS = ("onnxruntime", "numpy")
_RECOMMENDED_DEPS = ("PIL", "scipy", "onnx")


def _check_dep(name: str) -> tuple[bool, str]:
    """Returns (ok, version_or_error_msg)."""
    try:
        mod = __import__(name)
    except ImportError as exc:
        return False, str(exc)
    version = getattr(mod, "__version__", None)
    if version is None and name == "PIL":
        try:
            from PIL import __version__ as v
            version = v
        except Exception:
            version = "unknown"
    return True, str(version or "unknown")


def _cmd_check(args: argparse.Namespace) -> int:
    """Validate that the env is ready for vision PII fetches."""
    report: dict = {
        "required": {},
        "recommended": {},
        "env": {},
        "model_classification": None,
    }
    critical_missing = False

    for dep in _REQUIRED_DEPS:
        ok, info = _check_dep(dep)
        report["required"][dep] = {"available": ok, "version": info if ok else None,
                                    "error": None if ok else info}
        if not ok:
            critical_missing = True

    for dep in _RECOMMENDED_DEPS:
        ok, info = _check_dep(dep)
        report["recommended"][dep] = {"available": ok, "version": info if ok else None,
                                       "error": None if ok else info}

    for env_var in ("ETZ_VISION_PII_BACKEND", "ETZ_VISION_PII_FACE_MODEL",
                    "ETZ_VISION_PII_PLATE_MODEL", "ETZ_VISION_PII_AGE_MODEL",
                    "ETZ_VISION_PII_ALLOW_STUB"):
        report["env"][env_var] = os.environ.get(env_var)

    face_path = report["env"]["ETZ_VISION_PII_FACE_MODEL"]
    no_model = face_path is None
    if face_path and not critical_missing:
        try:
            from .vision_pii_filter import _classify_face_model_kind
            kind = _classify_face_model_kind(face_path)
            report["model_classification"] = {"path": face_path, "kind": kind}
        except Exception as exc:   # noqa: BLE001
            report["model_classification"] = {
                "path": face_path, "error": str(exc),
            }

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _print_human(report)

    if critical_missing:
        return 2
    if no_model:
        return 1
    if report["model_classification"] and "error" in (report["model_classification"] or {}):
        return 1
    return 0


def _print_human(report: dict) -> None:
    print("Vision PII filter setup check\n")
    print("Required deps:")
    for dep, info in report["required"].items():
        mark = "✓" if info["available"] else "✘"
        ver = info["version"] or info["error"]
        print(f"  {mark} {dep}: {ver}")
    print("Recommended deps:")
    for dep, info in report["recommended"].items():
        mark = "✓" if info["available"] else "?"
        ver = info["version"] or info["error"]
        print(f"  {mark} {dep}: {ver}")
    print("Environment:")
    for k, v in report["env"].items():
        if v is None:
            print(f"  - {k}: (unset)")
        elif "MODEL" in k and v:
            exists = Path(v).exists()
            print(f"  - {k}: {v}  [{'exists' if exists else 'MISSING'}]")
        else:
            print(f"  - {k}: {v}")
    if report["model_classification"]:
        mc = report["model_classification"]
        if "error" in mc:
            print(f"\nFace model classify: ✘ {mc['error']}")
        else:
            print(f"\nFace model classify: ✓ {mc['kind']}")
            print(f"  (would route to: {_kind_to_backend_name(mc['kind'])})")
    elif report["env"]["ETZ_VISION_PII_FACE_MODEL"] is None:
        print("\nFace model classify: skipped (ETZ_VISION_PII_FACE_MODEL unset)")


def _kind_to_backend_name(kind: str) -> str:
    return {
        "centerface": "CenterFaceOnnxBackend",
        "yolov8-face": "Yolov8FaceOnnxBackend",
        "retinaface": "RetinaFaceOnnxBackend",
        "generic": "OnnxFaceBackend (generic Nx{5,6,7})",
    }.get(kind, "OnnxFaceBackend")


def _cmd_classify(args: argparse.Namespace) -> int:
    from .vision_pii_filter import _classify_face_model_kind
    try:
        kind = _classify_face_model_kind(args.model_path)
    except Exception as exc:   # noqa: BLE001
        print(f"classify: failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({
            "model_path": args.model_path,
            "kind": kind,
            "backend": _kind_to_backend_name(kind),
        }))
    else:
        print(f"kind={kind}  backend={_kind_to_backend_name(kind)}")
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    """Synthesize a small RGB image, run detect_faces, report count."""
    from .vision_pii_filter import (
        _classify_face_model_kind,
        CenterFaceOnnxBackend, Yolov8FaceOnnxBackend, RetinaFaceOnnxBackend,
        OnnxFaceBackend, VisionPiiBackendUnavailable,
    )
    try:
        kind = _classify_face_model_kind(args.model_path)
    except VisionPiiBackendUnavailable as exc:
        print(f"smoke: classify failed: {exc}", file=sys.stderr)
        return 2

    backend_cls = {
        "centerface": CenterFaceOnnxBackend,
        "yolov8-face": Yolov8FaceOnnxBackend,
        "retinaface": RetinaFaceOnnxBackend,
    }.get(kind, OnnxFaceBackend)

    try:
        backend = backend_cls(model_path=args.model_path)
    except VisionPiiBackendUnavailable as exc:
        print(f"smoke: backend init failed: {exc}", file=sys.stderr)
        return 2

    try:
        from PIL import Image   # type: ignore
        import numpy as np
    except ImportError as exc:
        print(f"smoke: Pillow+numpy required: {exc}", file=sys.stderr)
        return 2

    rng = np.random.RandomState(0)
    arr = rng.randint(0, 256, size=(480, 640, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    boxes = backend.detect_faces(buf.getvalue())
    summary = {
        "model_path": args.model_path,
        "kind": kind,
        "backend": backend_cls.__name__,
        "image_size": [640, 480],
        "detections": len(boxes),
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"smoke: kind={kind} backend={backend_cls.__name__} "
              f"detections={len(boxes)}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Vision PII filter operator-side diagnostic CLI."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Validate env / deps / model classification")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=_cmd_check)

    p_classify = sub.add_parser("classify", help="Classify a face ONNX model")
    p_classify.add_argument("model_path")
    p_classify.add_argument("--json", action="store_true")
    p_classify.set_defaults(func=_cmd_classify)

    p_smoke = sub.add_parser("smoke", help="Smoke-test backend with synthetic image")
    p_smoke.add_argument("model_path")
    p_smoke.add_argument("--json", action="store_true")
    p_smoke.set_defaults(func=_cmd_smoke)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
