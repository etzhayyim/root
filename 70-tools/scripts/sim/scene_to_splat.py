#!/usr/bin/env python3
"""scene_to_splat — coarse PLACEHOLDER 3D-Gaussian-Splat (.splat) from a city
scene, so the GsplatAdapter render path is visible/verifiable before a real
photoreal splat exists.

This is NOT photoreal and NOT the Mapillary product: it samples Gaussians on
building surfaces + roads from the OSM scene boxes, in the renderer's y-up frame
(matching the box render), and writes the antimatter15 32-byte `.splat` format
(pos f32×3, scale f32×3, RGBA u8×4, quat u8×4). The real detailed splat comes
from `trainGsplatFromMapillary` (COLMAP→gsplat, ADR-2605092800) once a Mapillary
client token is available; this placeholder only proves the render pipeline.

Usage:
  python3 scene_to_splat.py <scene.json> <out.splat> [max_splats]
"""
import json
import struct
import sys

ID_QUAT = bytes([255, 128, 128, 128])  # identity rotation (qw≈1, qxyz≈0)


def splat_rec(px, py, pz, s, rgb):
    return (
        struct.pack("<3f", px, py, pz)
        + struct.pack("<3f", s, s, s)
        + bytes([rgb[0], rgb[1], rgb[2], 235])
        + ID_QUAT
    )


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    scene = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 48000

    bb = scene["bbox_m"]
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2

    def to_render(x, y, z):
        # recentre + rotate −90° about X (sim z-up → render y-up): (X,Z,−Y)
        return (x - cx, z, -(y - cy))

    recs = []

    def emit(x, y, z, s, rgb):
        rx, ry, rz = to_render(x, y, z)
        recs.append(splat_rec(rx, ry, rz, s, rgb))

    for b in scene["buildings"]:
        x0, y0, x1, y1 = b["aabb"]
        h = b["height"]
        rgb = (110, 136, 156) if h >= 30 else (150, 148, 142)
        sx, sy = max(1.0, x1 - x0), max(1.0, y1 - y0)
        nx = max(2, min(6, int(sx / 6) + 1))
        ny = max(2, min(6, int(sy / 6) + 1))
        nz = max(2, min(10, int(h / 5) + 1))
        # roof grid
        for i in range(nx):
            for j in range(ny):
                emit(x0 + sx * i / (nx - 1), y0 + sy * j / (ny - 1), h, 2.0, rgb)
        # facades (4 walls × vertical levels)
        for k in range(nz):
            z = h * k / (nz - 1)
            for i in range(nx):
                fx = x0 + sx * i / (nx - 1)
                emit(fx, y0, z, 2.0, rgb)
                emit(fx, y1, z, 2.0, rgb)
            for j in range(ny):
                fy = y0 + sy * j / (ny - 1)
                emit(x0, fy, z, 2.0, rgb)
                emit(x1, fy, z, 2.0, rgb)

    for r in scene["roads"]:
        path = r["path"]
        for a, c in zip(path, path[1:]):
            dx, dy = c[0] - a[0], c[1] - a[1]
            length = (dx * dx + dy * dy) ** 0.5
            steps = max(1, int(length / 5))
            for t in range(steps + 1):
                f = t / max(1, steps)
                emit(a[0] + dx * f, a[1] + dy * f, 0.2, 1.4, (78, 78, 86))

    for o in scene.get("objects", []):
        emit(o["pos"][0], o["pos"][1], o.get("h", 2.0) * 0.6, 1.2, (120, 180, 120))

    if len(recs) > cap:
        step = len(recs) / cap
        recs = [recs[int(i * step)] for i in range(cap)]

    with open(out, "wb") as f:
        f.write(b"".join(recs))
    print(f"wrote {out}: {len(recs)} placeholder splats "
          f"({len(recs) * 32} bytes) — coarse, NOT photoreal (awaiting trainGsplatFromMapillary)")


if __name__ == "__main__":
    main()
