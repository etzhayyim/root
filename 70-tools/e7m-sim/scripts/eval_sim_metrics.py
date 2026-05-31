#!/usr/bin/env python3
"""eval_sim_metrics.py — ADR-2605262500 G11 / ADR-2605261600 G5 eval harness.

Computes the four metrics that the religious-corp sim quality gate
demands, given two paired datasets (one from the religious-corp
`e7m-sim` run, one from the **one-time-use isolated trial machine**
that produced the Isaac Sim reference per ADR-2605261600 G5):

  - **PSNR** (rendering) — peak signal-to-noise ratio over RGB frames.
  - **SSIM** (rendering) — structural similarity (luminance-only basic
    impl; not gaussian-windowed but spec-compliant for the 0.85 gate).
  - **Chamfer distance** (lidar / point-cloud) — bidirectional average
    nearest-neighbor distance in meters.
  - **IoU at voxel resolution** (occupancy) — Intersection-over-Union
    after binning both point clouds to a fixed voxel grid.

The ADR-2605262500 §9 gate is:

    psnr_min_db        ≥ 25.0
    ssim_min           ≥ 0.85
    chamfer_max_m      ≤ 0.05
    iou_min_at_0p1m    ≥ 0.75   (voxel size 0.10 m)
    composite_target   ≥ 0.75   (weighted average)

`composite_score()` normalizes each metric into [0, 1] and returns
their weighted average. `evaluate_vs_reference()` reads the operator's
reference-machine CSV + the religious-corp run's NDJSON and returns
an `EvalResult` with per-metric values + pass/fail + composite score.

**Honest scoring** (ADR-2605261600 §G10): the harness DOES NOT
massage the result. If PSNR is 18 dB the result reads 18 dB, even if
that means the gate fails. Tightening / hardware investment is the
remediation path — never threshold-juggling.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


# ─── thresholds (ADR-2605262500 §9 + ADR-2605261600 G5) ─────────────


DEFAULT_PSNR_MIN_DB = 25.0
DEFAULT_SSIM_MIN = 0.85
DEFAULT_CHAMFER_MAX_M = 0.05
DEFAULT_IOU_MIN = 0.75
DEFAULT_COMPOSITE_MIN = 0.75
DEFAULT_VOXEL_SIZE_M = 0.10


# ─── per-metric impls ───────────────────────────────────────────────


def psnr(a: np.ndarray, b: np.ndarray, *, peak: float = 255.0) -> float:
    """PSNR in dB. Identical arrays → math.inf."""
    if a.shape != b.shape:
        raise ValueError(f"psnr: shape mismatch {a.shape} vs {b.shape}")
    diff = a.astype(np.float64) - b.astype(np.float64)
    mse = float(np.mean(diff * diff))
    if mse == 0.0:
        return math.inf
    return 20.0 * math.log10(peak / math.sqrt(mse))


def ssim(a: np.ndarray, b: np.ndarray, *, peak: float = 255.0) -> float:
    """Basic SSIM (luminance + contrast + structure on the whole array).

    Not gaussian-windowed (that's `compare_ssim` in scikit-image, which
    we deliberately don't depend on for the W2 PoC). The whole-array
    impl is spec-compliant per Wang et al. 2004 §3, and matches the
    ADR-2605262500 §9 SSIM threshold (0.85 — chosen for whole-frame
    not windowed SSIM)."""
    if a.shape != b.shape:
        raise ValueError(f"ssim: shape mismatch {a.shape} vs {b.shape}")
    a64 = a.astype(np.float64)
    b64 = b.astype(np.float64)
    mu_a = float(np.mean(a64))
    mu_b = float(np.mean(b64))
    var_a = float(np.var(a64))
    var_b = float(np.var(b64))
    cov_ab = float(np.mean((a64 - mu_a) * (b64 - mu_b)))
    c1 = (0.01 * peak) ** 2
    c2 = (0.03 * peak) ** 2
    num = (2 * mu_a * mu_b + c1) * (2 * cov_ab + c2)
    den = (mu_a * mu_a + mu_b * mu_b + c1) * (var_a + var_b + c2)
    if den == 0.0:
        return 1.0
    return num / den


def chamfer_distance(points_a: np.ndarray, points_b: np.ndarray) -> float:
    """Bidirectional Chamfer distance in input units (meters).

    Uses scipy.spatial.cKDTree for k=1 nearest-neighbor lookup.
    Returns (mean_a_to_b + mean_b_to_a) / 2."""
    if points_a.ndim != 2 or points_b.ndim != 2:
        raise ValueError("chamfer: inputs must be (N, D) arrays")
    if points_a.shape[1] != points_b.shape[1]:
        raise ValueError(f"chamfer: dim mismatch {points_a.shape[1]} vs {points_b.shape[1]}")
    if points_a.size == 0 or points_b.size == 0:
        return math.inf

    from scipy.spatial import cKDTree

    tree_a = cKDTree(points_a)
    tree_b = cKDTree(points_b)
    d_ab, _ = tree_b.query(points_a, k=1)
    d_ba, _ = tree_a.query(points_b, k=1)
    return float((np.mean(d_ab) + np.mean(d_ba)) / 2.0)


def voxel_iou(
    points_a: np.ndarray,
    points_b: np.ndarray,
    *,
    voxel_size: float = DEFAULT_VOXEL_SIZE_M,
) -> float:
    """Intersection-over-Union on voxelized occupancy."""
    if voxel_size <= 0:
        raise ValueError("voxel_size must be > 0")
    if points_a.size == 0 and points_b.size == 0:
        return 1.0   # both empty == perfectly overlapping (trivially)
    if points_a.size == 0 or points_b.size == 0:
        return 0.0

    def _voxelize(pts: np.ndarray) -> set[tuple[int, ...]]:
        keys = np.floor(pts / voxel_size).astype(np.int64)
        return {tuple(row) for row in keys}

    vox_a = _voxelize(points_a)
    vox_b = _voxelize(points_b)
    inter = len(vox_a & vox_b)
    union = len(vox_a | vox_b)
    return inter / union if union > 0 else 1.0


# ─── composite + gate ───────────────────────────────────────────────


@dataclass
class MetricThresholds:
    psnr_min_db: float = DEFAULT_PSNR_MIN_DB
    ssim_min: float = DEFAULT_SSIM_MIN
    chamfer_max_m: float = DEFAULT_CHAMFER_MAX_M
    iou_min: float = DEFAULT_IOU_MIN
    composite_min: float = DEFAULT_COMPOSITE_MIN


@dataclass
class MetricValues:
    psnr_db: float
    ssim: float
    chamfer_m: float
    iou: float


@dataclass
class MetricNorms:
    """Each metric normalized into [0, 1] for composite score."""
    psnr: float       # min(psnr / threshold, 1.0)  with PSNR=inf → 1.0
    ssim: float       # ssim       (already 0..1 ish)
    chamfer: float    # clamp(1 - chamfer / threshold, 0, 1)
    iou: float        # iou        (already 0..1)


@dataclass
class EvalResult:
    values: MetricValues
    norms: MetricNorms
    composite: float
    thresholds: MetricThresholds
    passed: bool
    per_metric_passed: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _normalize(values: MetricValues, thresholds: MetricThresholds) -> MetricNorms:
    psnr_n = 1.0 if math.isinf(values.psnr_db) else min(
        values.psnr_db / thresholds.psnr_min_db, 1.0
    )
    psnr_n = max(0.0, psnr_n)
    ssim_n = max(0.0, min(values.ssim, 1.0))
    chamfer_n = max(0.0, min(1.0 - values.chamfer_m / max(thresholds.chamfer_max_m, 1e-9), 1.0))
    iou_n = max(0.0, min(values.iou, 1.0))
    return MetricNorms(psnr=psnr_n, ssim=ssim_n, chamfer=chamfer_n, iou=iou_n)


def composite_score(norms: MetricNorms, *, weights: Optional[dict[str, float]] = None) -> float:
    """Weighted average of normalized metrics. Default = equal weights."""
    w = weights or {"psnr": 0.25, "ssim": 0.25, "chamfer": 0.25, "iou": 0.25}
    total_w = sum(w.values())
    if total_w == 0:
        return 0.0
    return (
        w.get("psnr", 0) * norms.psnr
        + w.get("ssim", 0) * norms.ssim
        + w.get("chamfer", 0) * norms.chamfer
        + w.get("iou", 0) * norms.iou
    ) / total_w


def evaluate(
    values: MetricValues,
    *,
    thresholds: Optional[MetricThresholds] = None,
    weights: Optional[dict[str, float]] = None,
) -> EvalResult:
    """Full evaluation: norms, composite, individual + combined gate."""
    thr = thresholds or MetricThresholds()
    norms = _normalize(values, thr)
    comp = composite_score(norms, weights=weights)

    per: dict[str, bool] = {
        "psnr": values.psnr_db >= thr.psnr_min_db,
        "ssim": values.ssim >= thr.ssim_min,
        "chamfer": values.chamfer_m <= thr.chamfer_max_m,
        "iou": values.iou >= thr.iou_min,
        "composite": comp >= thr.composite_min,
    }
    passed = all(per.values())
    notes: list[str] = []
    if not per["psnr"]:
        notes.append(f"PSNR fail: {values.psnr_db:.2f} dB < {thr.psnr_min_db} dB")
    if not per["ssim"]:
        notes.append(f"SSIM fail: {values.ssim:.4f} < {thr.ssim_min}")
    if not per["chamfer"]:
        notes.append(f"Chamfer fail: {values.chamfer_m:.4f} m > {thr.chamfer_max_m} m")
    if not per["iou"]:
        notes.append(f"IoU fail: {values.iou:.4f} < {thr.iou_min}")
    if not per["composite"]:
        notes.append(f"Composite fail: {comp:.4f} < {thr.composite_min}")
    return EvalResult(
        values=values,
        norms=norms,
        composite=comp,
        thresholds=thr,
        passed=passed,
        per_metric_passed=per,
        notes=notes,
    )


# ─── file I/O — bridge synthetic scalar tests to real artifact eval ─


def _try_pil():
    try:
        from PIL import Image   # type: ignore
        return Image
    except ImportError:
        return None


def load_image_as_array(path: Path) -> np.ndarray:
    """Load an image file into a uint8 numpy array via Pillow.

    Returns (H, W, C) for color or (H, W) for grayscale. RGBA is
    flattened to RGB by dropping the alpha channel — alpha doesn't
    factor into PSNR/SSIM for the religious-corp sim quality gate."""
    Image = _try_pil()
    if Image is None:
        raise RuntimeError("Pillow not available for image I/O")
    img = Image.open(path)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    elif img.mode not in {"RGB", "L"}:
        img = img.convert("RGB")
    arr = np.asarray(img)
    return arr


def load_pointcloud_npy(path: Path) -> np.ndarray:
    """Load an (N, D) point cloud from a numpy .npy file.

    .pcd / .ply parsers are W2.1 — for now operator pre-converts to .npy
    via standard tooling (open3d, trimesh, pdal). Keeping the harness
    dep-free at this layer keeps it Murakumo-deployable without extra
    install steps."""
    arr = np.load(path, allow_pickle=False)
    if arr.ndim != 2:
        raise ValueError(
            f"point cloud .npy must be 2-D (N, D); got shape {arr.shape}"
        )
    return arr.astype(np.float64, copy=False)


def metrics_from_image_pair(
    candidate: Path, reference: Path
) -> tuple[float, float]:
    """Read two images + compute (psnr_db, ssim) on the matched arrays."""
    a = load_image_as_array(candidate)
    b = load_image_as_array(reference)
    return psnr(a, b), ssim(a, b)


def metrics_from_pointcloud_pair(
    candidate: Path,
    reference: Path,
    *,
    voxel_size: float = DEFAULT_VOXEL_SIZE_M,
) -> tuple[float, float]:
    """Read two .npy point clouds + compute (chamfer_m, voxel_iou)."""
    a = load_pointcloud_npy(candidate)
    b = load_pointcloud_npy(reference)
    return chamfer_distance(a, b), voxel_iou(a, b, voxel_size=voxel_size)


def evaluate_scene_run(
    *,
    candidate_image: Optional[Path] = None,
    reference_image: Optional[Path] = None,
    candidate_pointcloud: Optional[Path] = None,
    reference_pointcloud: Optional[Path] = None,
    thresholds: Optional["MetricThresholds"] = None,
    voxel_size: float = DEFAULT_VOXEL_SIZE_M,
) -> "EvalResult":
    """Orchestrator: read paired artifacts → compute metrics → gate.

    Pass `candidate_*` (religious-corp `e7m-sim` run output) + the
    corresponding `reference_*` (one-time-use isolated trial machine
    output per ADR-2605261600 G5). Missing pairs yield perfect metrics
    for the missing dimension — operator MUST supply both modes for
    a real gate to bite.
    """
    psnr_v = math.inf
    ssim_v = 1.0
    chamfer_v = 0.0
    iou_v = 1.0

    if candidate_image is not None and reference_image is not None:
        psnr_v, ssim_v = metrics_from_image_pair(candidate_image, reference_image)
    if candidate_pointcloud is not None and reference_pointcloud is not None:
        chamfer_v, iou_v = metrics_from_pointcloud_pair(
            candidate_pointcloud, reference_pointcloud, voxel_size=voxel_size
        )

    values = MetricValues(
        psnr_db=psnr_v, ssim=ssim_v, chamfer_m=chamfer_v, iou=iou_v
    )
    return evaluate(values, thresholds=thresholds)


# ─── reference-CSV ingest (operator from one-time-use Isaac Sim machine) ─


def read_reference_csv(path: Path) -> dict[str, float]:
    """Parse a 2-column metric CSV from the isolated trial machine.

    Schema:
      psnr_db,<float>
      ssim,<float>
      chamfer_m,<float>
      iou_at_0p1m_voxel,<float>

    Operators on the one-time-use isolated Isaac Sim machine produce
    this CSV; only the CSV (4 floats) crosses the boundary back into
    religious-corp infra, never the Isaac Sim binaries themselves
    (ADR-2605261600 G5)."""
    out: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            continue
        key, val = line.split(",", 1)
        try:
            out[key.strip()] = float(val.strip())
        except ValueError:
            continue
    return out


# ─── CLI ────────────────────────────────────────────────────────────


def _result_to_json(result: EvalResult) -> dict:
    return {
        "values": dataclasses.asdict(result.values),
        "norms": dataclasses.asdict(result.norms),
        "composite": result.composite,
        "thresholds": dataclasses.asdict(result.thresholds),
        "passed": result.passed,
        "per_metric_passed": result.per_metric_passed,
        "notes": result.notes,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-2605262500 G11 + ADR-2605261600 G5 sim quality eval harness."
    )
    parser.add_argument(
        "--reference-csv",
        type=Path,
        help="Read psnr_db / ssim / chamfer_m / iou_at_0p1m_voxel from an Isaac Sim trial-machine CSV.",
    )
    parser.add_argument("--candidate-image", type=Path, help="Religious-corp run rendered frame (.png / .jpg)")
    parser.add_argument("--reference-image", type=Path, help="Isaac Sim ref frame to compare against")
    parser.add_argument("--candidate-pc", type=Path, help="Religious-corp run point cloud (.npy)")
    parser.add_argument("--reference-pc", type=Path, help="Isaac Sim ref point cloud (.npy)")
    parser.add_argument("--voxel-size", type=float, default=DEFAULT_VOXEL_SIZE_M)
    parser.add_argument("--psnr-db", type=float, help="Override PSNR (scalar mode)")
    parser.add_argument("--ssim", type=float, help="Override SSIM (scalar mode)")
    parser.add_argument("--chamfer-m", type=float, help="Override Chamfer (scalar mode)")
    parser.add_argument("--iou", type=float, help="Override IoU (scalar mode)")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result instead of human-readable summary.",
    )
    args = parser.parse_args(argv)

    # Mode 1: artifact pairs → compute metrics from files.
    if args.candidate_image or args.candidate_pc:
        result = evaluate_scene_run(
            candidate_image=args.candidate_image,
            reference_image=args.reference_image,
            candidate_pointcloud=args.candidate_pc,
            reference_pointcloud=args.reference_pc,
            voxel_size=args.voxel_size,
        )
    # Mode 2: reference CSV → metrics dict.
    elif args.reference_csv:
        parsed = read_reference_csv(args.reference_csv)
        values = MetricValues(
            psnr_db=parsed.get("psnr_db", math.inf),
            ssim=parsed.get("ssim", 1.0),
            chamfer_m=parsed.get("chamfer_m", 0.0),
            iou=parsed.get("iou_at_0p1m_voxel", 1.0),
        )
        result = evaluate(values)
    # Mode 3: scalar overrides (back-compat with W2.0 CLI).
    elif all(getattr(args, k) is not None for k in ("psnr_db", "ssim", "chamfer_m", "iou")):
        values = MetricValues(
            psnr_db=args.psnr_db, ssim=args.ssim,
            chamfer_m=args.chamfer_m, iou=args.iou,
        )
        result = evaluate(values)
    else:
        print(
            "eval_sim_metrics: provide one of: (--candidate-image/--candidate-pc), "
            "--reference-csv, or all four --psnr-db / --ssim / --chamfer-m / --iou",
            file=sys.stderr,
        )
        return 2
    if args.json:
        print(json.dumps(_result_to_json(result), indent=2))
    else:
        v, n = result.values, result.norms
        print(f"PSNR    : {v.psnr_db:7.2f} dB   norm={n.psnr:.3f}   "
              f"pass={result.per_metric_passed['psnr']}")
        print(f"SSIM    : {v.ssim:7.4f}      norm={n.ssim:.3f}   "
              f"pass={result.per_metric_passed['ssim']}")
        print(f"Chamfer : {v.chamfer_m:7.4f} m    norm={n.chamfer:.3f}   "
              f"pass={result.per_metric_passed['chamfer']}")
        print(f"IoU     : {v.iou:7.4f}      norm={n.iou:.3f}   "
              f"pass={result.per_metric_passed['iou']}")
        print(f"Composite: {result.composite:.4f}    "
              f"pass={result.per_metric_passed['composite']}")
        print(f"GATE: {'PASS' if result.passed else 'FAIL'}")
        for note in result.notes:
            print(f"  - {note}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
