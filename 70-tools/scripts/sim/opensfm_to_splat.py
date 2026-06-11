#!/usr/bin/env python3
"""opensfm_to_splat — OpenSfM reconstruction.json (Mapillary SLS) → .splat.

Converts the colored sparse 3-D point cloud of a real street-imagery
Structure-from-Motion reconstruction into the antimatter15 32-byte `.splat`
format the kami-pipelines GsplatAdapter renders. This is the REAL-imagery
preview cloud (sparse SfM points, not a dense trained 3DGS — that is the GPU
gsplat optimization step initialized from exactly this data + the images).

Frame: OpenSfM is gravity-aligned z-up; we centre on the cloud centroid, map
z-up→render y-up ((x,z,−y)), and normalise to a fixed radius so a generic
orbit viewer frames any city.

Source: Mapillary Street-Level Sequences (CC-BY-SA) — attribute Mapillary.

Usage:
  python3 opensfm_to_splat.py <reconstruction.json> <out.splat> [target_radius]
"""
import json
import struct
import sys

ID_QUAT = bytes([255, 128, 128, 128])


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    recon = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    target_r = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0

    rec = recon[0] if isinstance(recon, list) else recon
    pts = rec.get("points", {})
    if not pts:
        print("no points in reconstruction")
        sys.exit(1)

    coords = []
    cols = []
    for p in pts.values():
        x, y, z = p["coordinates"]
        coords.append((x, y, z))
        c = p.get("color", [180, 180, 180])
        cols.append((int(c[0]) & 255, int(c[1]) & 255, int(c[2]) & 255))

    n = len(coords)
    cx = sum(c[0] for c in coords) / n
    cy = sum(c[1] for c in coords) / n
    cz = sum(c[2] for c in coords) / n
    # max radius from centroid (after centring)
    rad = max(((c[0] - cx) ** 2 + (c[1] - cy) ** 2 + (c[2] - cz) ** 2) ** 0.5 for c in coords)
    scale = (target_r / rad) if rad > 1e-6 else 1.0

    recs = []
    for (x, y, z), (r, g, b) in zip(coords, cols):
        # centre + normalise, z-up → render y-up: (x, z, -y)
        rx = (x - cx) * scale
        ry = (z - cz) * scale
        rz = -(y - cy) * scale
        s = max(0.15, target_r * 0.006)  # splat radius ∝ scene size
        recs.append(
            struct.pack("<3f", rx, ry, rz)
            + struct.pack("<3f", s, s, s)
            + bytes([r, g, b, 240])
            + ID_QUAT
        )

    with open(out, "wb") as f:
        f.write(b"".join(recs))
    print(f"wrote {out}: {n} SfM points → splats ({n * 32} bytes), "
          f"radius≈{target_r:.0f} (real Mapillary street imagery; CC-BY-SA)")


if __name__ == "__main__":
    main()
