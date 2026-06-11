"""LiDAR proxy via MuJoCo mj_ray() — pre-flight for ADR-2605261600 R2 binding.

ADR R2 calls for CARLA lidar kernel + Vulkan RT GPU sensor backbone. CARLA is
a full game engine (heavy R2 install). This sandbox check uses MuJoCo's built-in
geometric raycast (`mj_ray`) as a structural proxy:

  - Cast N rays from a sensor pose, get hit distance + hit geom id
  - Build a Cartesian point cloud
  - Save .ply (ASCII, viewable in MeshLab / CloudCompare / paraview)

This is NOT what R2 ships — R2 needs photoreal ray-traced lidar with
intensity / dual-return / range noise. But it proves the geometry pipeline
end to end (MJCF parse → raycast → point cloud → file).
"""
from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np

MODEL = Path(__file__).parent / "kusawake.xml"
OUT = Path(__file__).parent / "out" / "kusawake_lidar.ply"
OUT.parent.mkdir(exist_ok=True)

# 16-line solid-state lidar @ chassis top (matches ADR Wave 1 spec)
N_LINES = 16
N_AZI = 360  # 1° azimuth resolution
ELEV_RANGE_DEG = (-15.0, 15.0)
MAX_RANGE = 50.0
SENSOR_POS = np.array([0.55, 0.0, 0.62])  # on top of LiDAR puck


def build_directions() -> np.ndarray:
    """Spherical fan: shape (N_LINES * N_AZI, 3) unit vectors in world frame."""
    elev = np.deg2rad(np.linspace(ELEV_RANGE_DEG[0], ELEV_RANGE_DEG[1], N_LINES))
    azi = np.deg2rad(np.linspace(0, 360, N_AZI, endpoint=False))
    e, a = np.meshgrid(elev, azi, indexing="ij")
    x = np.cos(e) * np.cos(a)
    y = np.cos(e) * np.sin(a)
    z = np.sin(e)
    return np.stack([x, y, z], axis=-1).reshape(-1, 3)


def cast_lidar(model: mujoco.MjModel, data: mujoco.MjData) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cast all rays from SENSOR_POS. Returns (points_world, hit_dist, hit_geom)."""
    mujoco.mj_forward(model, data)
    pos = SENSOR_POS.astype(np.float64)
    dirs = build_directions()

    n = dirs.shape[0]
    dists = np.full(n, np.inf)
    geom_ids = np.full(n, -1, dtype=np.int32)

    geomgroup = np.array([1, 1, 1, 1, 1, 1], dtype=np.uint8)
    geomid_out = np.zeros(1, dtype=np.int32)

    for i in range(n):
        dist = mujoco.mj_ray(
            model, data, pos, dirs[i],
            geomgroup, 1,  # flg_static = include world
            -1,            # bodyexclude = none
            geomid_out,
        )
        if dist >= 0:
            dists[i] = min(dist, MAX_RANGE)
            geom_ids[i] = geomid_out[0]

    hit_mask = np.isfinite(dists)
    points = pos + dirs[hit_mask] * dists[hit_mask, None]
    return points, dists, geom_ids


def write_ply(path: Path, points: np.ndarray, intensity: np.ndarray) -> None:
    """ASCII PLY with per-point intensity (0..255 grayscale)."""
    n = points.shape[0]
    with path.open("w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {n}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for (x, y, z), v in zip(points, intensity):
            v8 = int(np.clip(v * 255, 0, 255))
            f.write(f"{x:.4f} {y:.4f} {z:.4f} {v8} {v8} {v8}\n")


def main() -> int:
    print(f"Model: {MODEL}")
    m = mujoco.MjModel.from_xml_path(str(MODEL))
    d = mujoco.MjData(m)

    # Move chassis +5m forward so lidar sees ground at varying ranges
    d.qpos[:2] = [5.0, 0.0]
    print(f"Lidar pose: {SENSOR_POS} (top of chassis lidar puck)")
    print(f"Sweep: {N_LINES} elev × {N_AZI} azi = {N_LINES * N_AZI} rays")

    points, dists, geom_ids = cast_lidar(m, d)
    n_hits = points.shape[0]
    print(f"Hits: {n_hits} / {N_LINES * N_AZI} ({100 * n_hits / (N_LINES * N_AZI):.1f}%)")

    # Hit-geom histogram
    geom_names = {int(g): mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(g)) for g in set(geom_ids) if g >= 0}
    unique, counts = np.unique(geom_ids[geom_ids >= 0], return_counts=True)
    print("\nHit-geom histogram:")
    for u, c in sorted(zip(unique, counts), key=lambda x: -x[1]):
        nm = geom_names.get(int(u)) or f"<id={u}>"
        print(f"  {c:5d}  {nm}")

    # Range stats
    finite = dists[np.isfinite(dists)]
    print(f"\nRange stats (m): min={finite.min():.2f} / mean={finite.mean():.2f} / max={finite.max():.2f}")

    # Intensity proxy: inverse-square attenuation, normalized
    intensity = 1.0 / (1.0 + (dists[np.isfinite(dists)] / 5.0) ** 2)

    write_ply(OUT, points, intensity)
    print(f"\nWrote: {OUT} ({OUT.stat().st_size} B)")
    print(f"View with: meshlab {OUT}  /  cloudcompare {OUT}  /  pcl_viewer {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
