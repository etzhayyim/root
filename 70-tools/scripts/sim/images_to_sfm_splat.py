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
    rec = max(recs.values(), key=lambda r: len(r.points3D))
    pts = list(rec.points3D.values())
    print(f"largest reconstruction: {len(rec.images)} registered images, {len(pts)} points")
    if len(pts) < 50:
        print("too few points")
        sys.exit(3)

    cx = sum(p.xyz[0] for p in pts) / len(pts)
    cy = sum(p.xyz[1] for p in pts) / len(pts)
    cz = sum(p.xyz[2] for p in pts) / len(pts)
    rad = max(((p.xyz[0] - cx) ** 2 + (p.xyz[1] - cy) ** 2 + (p.xyz[2] - cz) ** 2) ** 0.5 for p in pts) or 1.0
    scale = target_r / rad

    body = []
    for p in pts:
        rx = (p.xyz[0] - cx) * scale
        ry = (p.xyz[1] - cy) * scale
        rz = (p.xyz[2] - cz) * scale
        c = p.color
        body.append(
            struct.pack("<3f", rx, ry, rz)
            + struct.pack("<3f", 0.4, 0.4, 0.4)
            + bytes([int(c[0]) & 255, int(c[1]) & 255, int(c[2]) & 255, 240])
            + ID_QUAT
        )
    with open(out, "wb") as f:
        f.write(b"".join(body))
    print(f"wrote {out}: {len(body)} sparse SfM splats ({len(body) * 32} bytes)")


if __name__ == "__main__":
    main()
