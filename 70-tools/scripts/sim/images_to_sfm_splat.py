#!/usr/bin/env python3
"""images_to_sfm_splat — street images → CPU Structure-from-Motion → .splat.

No-GPU path to a SPARSE 3-D point cloud from a folder of overlapping street
photos (e.g. Mapillary thumbnails fetched by mapillary_fetch.py). Runs COLMAP
SfM via pycolmap (feature extraction → exhaustive matching → incremental
mapping), takes the largest reconstruction, and writes its colored sparse
points as an antimatter15 32-byte `.splat` for the kami GsplatAdapter.

This is the PREVIEW cloud; a dense photoreal 3DGS still needs gsplat GPU
training (see GSPLAT-RUNBOOK.md). Verified on 80 Shibuya Mapillary images →
19 registered → 2,235 points.

Deps (isolated venv):  python3 -m venv v && v/bin/pip install pycolmap
Usage:
  v/bin/python images_to_sfm_splat.py <image_dir> <out.splat> [target_radius] [work_dir]
"""
import os
import struct
import sys

import pycolmap

ID_QUAT = bytes([255, 128, 128, 128])


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    img_dir = sys.argv[1]
    out = sys.argv[2]
    target_r = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    work = sys.argv[4] if len(sys.argv) > 4 else "/tmp/sfm_work"
    os.makedirs(work, exist_ok=True)
    db = os.path.join(work, "db.db")
    if os.path.exists(db):
        os.remove(db)

    pycolmap.extract_features(db, img_dir)
    pycolmap.match_exhaustive(db)
    recs = pycolmap.incremental_mapping(db, img_dir, work)
    if not recs:
        print("no reconstruction (insufficient image overlap)")
        sys.exit(2)
    import numpy as np

    rec = max(recs.values(), key=lambda r: len(r.points3D))
    p3d = list(rec.points3D.values())
    print(f"largest reconstruction: {len(rec.images)} registered images, {len(p3d)} points")
    if len(p3d) < 50:
        print("too few points")
        sys.exit(3)

    pts = np.array([p.xyz for p in p3d], float)
    cols = np.array([list(p.color) for p in p3d], float)

    # Gravity-align to render y-up: the camera centres are ~co-planar at
    # eye/car height, so the normal of the plane through them is "up". Rotate
    # that normal → +Y, drop the ground to y≈0, scale horizontally to target_r —
    # so a physics ground plane at y=0 sits on the reconstructed street.
    cams = []
    for im in rec.images.values():
        try:
            cams.append(np.array(im.projection_center(), float))
        except Exception:
            cams.append(np.array(im.cam_from_world.inverse().translation, float))
    cams = np.array(cams)
    _, _, vt = np.linalg.svd(cams - cams.mean(0))
    normal = vt[-1]
    if np.dot(cams.mean(0) - pts.mean(0), normal) < 0:
        normal = -normal
    up = np.array([0.0, 1.0, 0.0])
    v = np.cross(normal, up)
    c = float(np.dot(normal, up))
    if np.linalg.norm(v) < 1e-6:
        R = np.eye(3) if c > 0 else np.diag([1.0, -1.0, 1.0])
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * ((1 - c) / float(v @ v))
    P = (R @ (pts - pts.mean(0)).T).T
    P[:, 1] -= np.percentile(P[:, 1], 5)  # ground ≈ y = 0
    horiz = np.sqrt(P[:, 0] ** 2 + P[:, 2] ** 2)
    P *= target_r / (np.percentile(horiz, 95) or 1.0)

    body = []
    for i in range(len(P)):
        body.append(
            struct.pack("<3f", float(P[i, 0]), float(P[i, 1]), float(P[i, 2]))
            + struct.pack("<3f", 0.4, 0.4, 0.4)
            + bytes([int(cols[i, 0]) & 255, int(cols[i, 1]) & 255, int(cols[i, 2]) & 255, 240])
            + ID_QUAT
        )
    with open(out, "wb") as f:
        f.write(b"".join(body))
    print(f"wrote {out}: {len(body)} sparse SfM splats ({len(body) * 32} bytes)")


if __name__ == "__main__":
    main()
