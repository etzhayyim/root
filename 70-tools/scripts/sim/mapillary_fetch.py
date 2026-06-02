#!/usr/bin/env python3
"""mapillary_fetch — pull Mapillary street-level image metadata for a bbox and
write a manifest that feeds the 3-D Gaussian-Splat training pipeline.

This is the IMAGE-ACQUISITION front of the existing repo pipeline
`com.etzhayyim.apps.maps.trainGsplatFromMapillary` (ADR-2605092800):

    mapillary_fetch.py (this)  →  manifest of image ids + thumb URLs + poses
        →  trainGsplatFromMapillary worker (Vultr/RunPod GPU pod):
               COLMAP SfM  →  gsplat/nerfstudio training  →  PLY → B2
        →  kami-pipelines GsplatAdapter renders the PLY in the Shibuya sim.

The COLMAP + gsplat training step is an OFFLINE GPU job (10–20 min/scene); it is
NOT run here. This script only assembles the input manifest, which is the part
that needs the Mapillary API.

Auth: set MAPILLARY_TOKEN (free client token, graph.mapillary.com v4). Without
it the script prints the manifest schema + the exact training invocation and
exits 0 (so the pipeline is documented even offline).

Usage:
  MAPILLARY_TOKEN=MLY|... python3 mapillary_fetch.py \
      --bbox 139.6985,35.6585,139.7025,35.6605 \
      --out 70-tools/e7m-sim/scenes/shibuya/shibuya_mapillary.manifest.json \
      --limit 120
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

GRAPH = "https://graph.mapillary.com/images"
FIELDS = "id,computed_geometry,geometry,compass_angle,captured_at,thumb_2048_url"


def fetch(bbox, token, limit):
    q = urllib.parse.urlencode({
        "fields": FIELDS,
        "bbox": bbox,
        "limit": str(min(limit, 2000)),
        "access_token": token,
    })
    req = urllib.request.Request(
        f"{GRAPH}?{q}", headers={"User-Agent": "etzhayyim-e7m-sim/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("data", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", default="139.6985,35.6585,139.7025,35.6605",
                    help="minLng,minLat,maxLng,maxLat (default: Shibuya Scramble)")
    ap.add_argument("--out", default="70-tools/e7m-sim/scenes/shibuya/shibuya_mapillary.manifest.json")
    ap.add_argument("--limit", type=int, default=120)
    ap.add_argument("--name", default="shibuya_scramble")
    args = ap.parse_args()

    token = os.environ.get("MAPILLARY_TOKEN")
    minlng, minlat, maxlng, maxlat = (float(v) for v in args.bbox.split(","))
    lat0, lng0 = (minlat + maxlat) / 2, (minlng + maxlng) / 2

    if not token:
        print(
            "MAPILLARY_TOKEN not set — acquisition is documented but not run.\n\n"
            "Step 1 (this script): export MAPILLARY_TOKEN then re-run to write the\n"
            f"  manifest to {args.out}.\n"
            "Step 2 (offline GPU): hand the manifest's image ids to the existing\n"
            "  XRPC procedure to enqueue COLMAP→gsplat training:\n\n"
            f'    com.etzhayyim.apps.maps.trainGsplatFromMapillary '
            f'{{ "lat": {lat0:.5f}, "lng": {lng0:.5f}, "radiusM": 120, "maxImages": {args.limit} }}\n\n'
            "  → worker runs COLMAP SfM + gsplat on a GPU pod, uploads PLY to B2,\n"
            "    inserts a vertex_maps_gsplat_asset row (ADR-2605092800).\n"
            "Step 3 (render): the Shibuya sim's GsplatAdapter loads that PLY.\n"
        )
        return 0

    imgs = fetch(args.bbox, token, args.limit)
    manifest = {
        "name": args.name,
        "source": "Mapillary Graph API v4",
        "bbox_lnglat": [minlng, minlat, maxlng, maxlat],
        "origin": {"lat": round(lat0, 7), "lng": round(lng0, 7)},
        "count": len(imgs),
        "images": [
            {
                "id": im["id"],
                "geometry": im.get("computed_geometry") or im.get("geometry"),
                "compass_angle": im.get("compass_angle"),
                "captured_at": im.get("captured_at"),
                "thumb_url": im.get("thumb_2048_url"),
            }
            for im in imgs
        ],
        "train_invocation": {
            "xrpc": "com.etzhayyim.apps.maps.trainGsplatFromMapillary",
            "input": {"lat": round(lat0, 7), "lng": round(lng0, 7),
                      "radiusM": 120, "maxImages": args.limit,
                      "mapillaryImageIds": [im["id"] for im in imgs]},
        },
    }
    with open(args.out, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}: {len(imgs)} Mapillary images for {args.name}. "
          f"Next: enqueue trainGsplatFromMapillary with the manifest's image ids.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
