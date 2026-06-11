"""Tests for eval_sim_metrics.py — ADR-2605262500 G11 / ADR-2605261600 G5.

Validates the four primitive metrics + composite + gate logic with
synthetic data.  All offline; no Isaac Sim ref required.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest


# ─── module loading (hyphen in filename) ────────────────────────────


_THIS = Path(__file__).resolve()
_E7M_SIM = _THIS.parent.parent
_SCRIPT = _E7M_SIM / "scripts" / "eval_sim_metrics.py"


@pytest.fixture(scope="module")
def eval_mod():
    spec = importlib.util.spec_from_file_location("eval_sim_metrics", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["eval_sim_metrics"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── PSNR ───────────────────────────────────────────────────────────


def test_psnr_identical_arrays_is_infinity(eval_mod):
    a = np.full((16, 16, 3), 128, dtype=np.uint8)
    b = np.full((16, 16, 3), 128, dtype=np.uint8)
    assert math.isinf(eval_mod.psnr(a, b))


def test_psnr_offset_by_1_gives_known_value(eval_mod):
    """A uniform offset of 1 over 255 → MSE=1 → PSNR ≈ 48.13 dB."""
    a = np.full((16, 16, 3), 128, dtype=np.uint8)
    b = np.full((16, 16, 3), 129, dtype=np.uint8)
    val = eval_mod.psnr(a, b)
    assert 48.0 < val < 48.5


def test_psnr_shape_mismatch_raises(eval_mod):
    a = np.zeros((8, 8), dtype=np.uint8)
    b = np.zeros((4, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="shape mismatch"):
        eval_mod.psnr(a, b)


# ─── SSIM ───────────────────────────────────────────────────────────


def test_ssim_identical_arrays_is_one(eval_mod):
    a = np.random.RandomState(42).randint(0, 256, size=(32, 32, 3), dtype=np.uint8)
    b = a.copy()
    val = eval_mod.ssim(a, b)
    assert val == pytest.approx(1.0, abs=1e-9)


def test_ssim_high_for_small_perturbation(eval_mod):
    rng = np.random.RandomState(42)
    a = rng.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
    noise = rng.randint(-2, 3, size=a.shape, dtype=np.int16)
    b = np.clip(a.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    val = eval_mod.ssim(a, b)
    assert 0.85 < val <= 1.0


def test_ssim_shape_mismatch_raises(eval_mod):
    with pytest.raises(ValueError, match="shape mismatch"):
        eval_mod.ssim(np.zeros((4, 4)), np.zeros((8, 8)))


# ─── Chamfer ────────────────────────────────────────────────────────


def test_chamfer_identical_points_is_zero(eval_mod):
    pts = np.random.RandomState(7).randn(100, 3)
    val = eval_mod.chamfer_distance(pts, pts.copy())
    assert val == pytest.approx(0.0, abs=1e-9)


def test_chamfer_translated_points(eval_mod):
    """Translate by (0.05, 0, 0) m → chamfer = 0.05 m (bidirectional NN)."""
    pts = np.random.RandomState(7).randn(100, 3)
    b = pts + np.array([0.05, 0.0, 0.0])
    val = eval_mod.chamfer_distance(pts, b)
    assert val == pytest.approx(0.05, abs=1e-9)


def test_chamfer_empty_input_is_infinity(eval_mod):
    pts = np.random.randn(10, 3)
    assert math.isinf(eval_mod.chamfer_distance(np.zeros((0, 3)), pts))
    assert math.isinf(eval_mod.chamfer_distance(pts, np.zeros((0, 3))))


def test_chamfer_dim_mismatch_raises(eval_mod):
    with pytest.raises(ValueError, match="dim mismatch"):
        eval_mod.chamfer_distance(np.zeros((10, 3)), np.zeros((10, 2)))


# ─── Voxel IoU ──────────────────────────────────────────────────────


def test_voxel_iou_identical_points_is_one(eval_mod):
    pts = np.random.RandomState(11).randn(200, 3)
    val = eval_mod.voxel_iou(pts, pts.copy(), voxel_size=0.10)
    assert val == 1.0


def test_voxel_iou_disjoint_grids_is_zero(eval_mod):
    a = np.array([[0.0, 0.0, 0.0]])
    b = np.array([[10.0, 10.0, 10.0]])
    assert eval_mod.voxel_iou(a, b, voxel_size=0.10) == 0.0


def test_voxel_iou_both_empty_is_one(eval_mod):
    assert eval_mod.voxel_iou(np.zeros((0, 3)), np.zeros((0, 3))) == 1.0


def test_voxel_iou_one_empty_is_zero(eval_mod):
    assert eval_mod.voxel_iou(np.zeros((0, 3)), np.random.randn(5, 3)) == 0.0


def test_voxel_iou_partial_overlap(eval_mod):
    a = np.array([[0.0, 0.0, 0.0], [0.5, 0.0, 0.0], [1.0, 0.0, 0.0]])
    b = np.array([[0.5, 0.0, 0.0], [1.0, 0.0, 0.0], [1.5, 0.0, 0.0]])
    val = eval_mod.voxel_iou(a, b, voxel_size=0.10)
    # 2 of 4 voxels in union are intersection → 0.5
    assert val == pytest.approx(0.5, abs=1e-9)


# ─── normalization + composite + gate ───────────────────────────────


def test_evaluate_perfect_metrics_pass(eval_mod):
    v = eval_mod.MetricValues(psnr_db=math.inf, ssim=1.0, chamfer_m=0.0, iou=1.0)
    result = eval_mod.evaluate(v)
    assert result.passed is True
    assert all(result.per_metric_passed.values())
    assert result.composite == 1.0
    assert result.notes == []


def test_evaluate_all_fail(eval_mod):
    v = eval_mod.MetricValues(psnr_db=10.0, ssim=0.5, chamfer_m=0.5, iou=0.3)
    result = eval_mod.evaluate(v)
    assert result.passed is False
    assert not any(result.per_metric_passed[k] for k in ["psnr", "ssim", "chamfer", "iou"])
    assert len(result.notes) >= 4


def test_evaluate_boundary_thresholds_pass(eval_mod):
    """Exactly at the threshold values must pass (≥ / ≤ inclusive)."""
    v = eval_mod.MetricValues(psnr_db=25.0, ssim=0.85, chamfer_m=0.05, iou=0.75)
    result = eval_mod.evaluate(v)
    assert result.per_metric_passed["psnr"] is True
    assert result.per_metric_passed["ssim"] is True
    assert result.per_metric_passed["chamfer"] is True
    assert result.per_metric_passed["iou"] is True


def test_evaluate_one_metric_failure_aborts_combined_gate(eval_mod):
    """Even if composite is above 0.75, ANY individual metric failure
    must fail the overall gate (honest scoring; ADR §G10)."""
    # psnr fails (20 dB < 25), but other three are perfect.
    v = eval_mod.MetricValues(psnr_db=20.0, ssim=1.0, chamfer_m=0.0, iou=1.0)
    result = eval_mod.evaluate(v)
    assert result.composite >= 0.75   # weighted average still high
    assert result.per_metric_passed["psnr"] is False
    assert result.passed is False     # combined gate fails


def test_composite_uses_equal_weights_by_default(eval_mod):
    n = eval_mod.MetricNorms(psnr=1.0, ssim=0.5, chamfer=0.5, iou=0.5)
    val = eval_mod.composite_score(n)
    assert val == pytest.approx(0.625, abs=1e-9)


def test_composite_custom_weights(eval_mod):
    n = eval_mod.MetricNorms(psnr=1.0, ssim=0.0, chamfer=0.0, iou=0.0)
    val = eval_mod.composite_score(n, weights={"psnr": 1, "ssim": 1, "chamfer": 1, "iou": 1})
    # Equal weights → 1/4 = 0.25
    assert val == pytest.approx(0.25, abs=1e-9)
    val2 = eval_mod.composite_score(n, weights={"psnr": 4, "ssim": 0, "chamfer": 0, "iou": 0})
    # All weight on PSNR → 1.0
    assert val2 == pytest.approx(1.0, abs=1e-9)


# ─── reference-CSV ingest ───────────────────────────────────────────


def test_read_reference_csv_round_trips(eval_mod, tmp_path):
    csv = tmp_path / "ref.csv"
    csv.write_text(
        "# Isaac Sim trial machine reference for wadachi-r1-shibuya-1km\n"
        "psnr_db,28.5\n"
        "ssim,0.91\n"
        "chamfer_m,0.032\n"
        "iou_at_0p1m_voxel,0.81\n"
        "# comments are ignored\n"
        "\n"
        "extra_metric,42.0\n",
        encoding="utf-8",
    )
    parsed = eval_mod.read_reference_csv(csv)
    assert parsed == {
        "psnr_db": 28.5,
        "ssim": 0.91,
        "chamfer_m": 0.032,
        "iou_at_0p1m_voxel": 0.81,
        "extra_metric": 42.0,
    }


def test_reference_csv_drives_evaluate(eval_mod, tmp_path):
    csv = tmp_path / "ref.csv"
    csv.write_text(
        "psnr_db,28.0\nssim,0.90\nchamfer_m,0.03\niou_at_0p1m_voxel,0.80\n",
        encoding="utf-8",
    )
    parsed = eval_mod.read_reference_csv(csv)
    v = eval_mod.MetricValues(
        psnr_db=parsed["psnr_db"],
        ssim=parsed["ssim"],
        chamfer_m=parsed["chamfer_m"],
        iou=parsed["iou_at_0p1m_voxel"],
    )
    result = eval_mod.evaluate(v)
    assert result.passed is True
    assert result.composite >= 0.75


# ─── file I/O (Pillow image + numpy .npy point cloud) ───────────────


def _save_jpeg(arr: np.ndarray, path: Path) -> None:
    from PIL import Image
    Image.fromarray(arr).save(path, format="JPEG", quality=95)


def test_load_image_as_array_rgb(eval_mod, tmp_path):
    rng = np.random.RandomState(13)
    arr = rng.randint(0, 256, size=(32, 24, 3), dtype=np.uint8)
    p = tmp_path / "img.jpg"
    _save_jpeg(arr, p)
    loaded = eval_mod.load_image_as_array(p)
    # JPEG is lossy, but the shape + dtype must match.
    assert loaded.shape == (32, 24, 3)
    assert loaded.dtype == np.uint8


def test_metrics_from_image_pair_identical(eval_mod, tmp_path):
    arr = np.zeros((24, 24, 3), dtype=np.uint8)
    arr[:, :, 1] = 128
    p_a = tmp_path / "a.png"
    p_b = tmp_path / "b.png"
    from PIL import Image
    Image.fromarray(arr).save(p_a)
    Image.fromarray(arr).save(p_b)
    psnr_v, ssim_v = eval_mod.metrics_from_image_pair(p_a, p_b)
    assert math.isinf(psnr_v)
    assert ssim_v == pytest.approx(1.0, abs=1e-9)


def test_metrics_from_image_pair_different(eval_mod, tmp_path):
    rng = np.random.RandomState(42)
    a = rng.randint(0, 256, size=(48, 48, 3), dtype=np.uint8)
    b = rng.randint(0, 256, size=(48, 48, 3), dtype=np.uint8)
    p_a = tmp_path / "a.png"
    p_b = tmp_path / "b.png"
    from PIL import Image
    Image.fromarray(a).save(p_a)
    Image.fromarray(b).save(p_b)
    psnr_v, ssim_v = eval_mod.metrics_from_image_pair(p_a, p_b)
    # Random vs random → low PSNR, low SSIM.
    assert psnr_v < 15.0
    assert ssim_v < 0.30


def test_load_pointcloud_npy_round_trips(eval_mod, tmp_path):
    rng = np.random.RandomState(7)
    pts = rng.randn(50, 3).astype(np.float32)
    p = tmp_path / "pts.npy"
    np.save(p, pts)
    loaded = eval_mod.load_pointcloud_npy(p)
    assert loaded.shape == (50, 3)
    # Stored f32, loaded f64 (per docstring) — values still close.
    assert np.allclose(loaded, pts.astype(np.float64))


def test_load_pointcloud_npy_rejects_non_2d(eval_mod, tmp_path):
    p = tmp_path / "weird.npy"
    np.save(p, np.arange(24).reshape(2, 3, 4))
    with pytest.raises(ValueError, match="2-D"):
        eval_mod.load_pointcloud_npy(p)


def test_metrics_from_pointcloud_pair_translated(eval_mod, tmp_path):
    """Translate by 0.04m → chamfer ≈ 0.04m, voxel IoU > 0 (overlap remains
    at 0.10m voxels since translation < voxel size on most points)."""
    rng = np.random.RandomState(3)
    pts = rng.randn(150, 3)
    pts_b = pts + np.array([0.04, 0.0, 0.0])
    pa = tmp_path / "a.npy"
    pb = tmp_path / "b.npy"
    np.save(pa, pts)
    np.save(pb, pts_b)
    chamfer_v, iou_v = eval_mod.metrics_from_pointcloud_pair(pa, pb, voxel_size=0.10)
    assert chamfer_v == pytest.approx(0.04, abs=1e-9)
    assert 0.0 < iou_v <= 1.0


def test_evaluate_scene_run_image_only(eval_mod, tmp_path):
    """Image artifacts only → chamfer/iou default to perfect 0/1."""
    arr = np.full((32, 32, 3), 100, dtype=np.uint8)
    pa = tmp_path / "a.png"
    pb = tmp_path / "b.png"
    from PIL import Image
    Image.fromarray(arr).save(pa)
    Image.fromarray(arr).save(pb)
    result = eval_mod.evaluate_scene_run(
        candidate_image=pa, reference_image=pb,
    )
    assert result.passed is True
    assert math.isinf(result.values.psnr_db)
    assert result.values.chamfer_m == 0.0   # default for missing PC pair
    assert result.values.iou == 1.0


def test_evaluate_scene_run_both_modes(eval_mod, tmp_path):
    arr = np.full((32, 32, 3), 100, dtype=np.uint8)
    pa = tmp_path / "ia.png"
    pb = tmp_path / "ib.png"
    from PIL import Image
    Image.fromarray(arr).save(pa)
    Image.fromarray(arr).save(pb)
    pts = np.random.RandomState(1).randn(60, 3)
    pca = tmp_path / "pca.npy"
    pcb = tmp_path / "pcb.npy"
    np.save(pca, pts)
    np.save(pcb, pts)
    result = eval_mod.evaluate_scene_run(
        candidate_image=pa, reference_image=pb,
        candidate_pointcloud=pca, reference_pointcloud=pcb,
    )
    assert result.passed is True
    assert result.values.chamfer_m == 0.0
    assert result.values.iou == 1.0
