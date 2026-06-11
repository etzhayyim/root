"""Generate a tiny synthetic baien-graft-shaped dataset for Move 1 smoke runs.

Real baien-graft samples need Hunyuan3D-2 or Pixal3D on EVO-X2 (~30 min
for 25 images per ADR-2605202115 + datagen_runbook). For pipeline smoke
validation we don't actually need 3D meshes — Move 1 SFT only consumes
the original image + caption + main_object string.

This script writes 10 single-object PIL-drawn images with deterministic
captions in the same directory layout the trainer expects.

Usage:
  python gen_synthetic_smoke_data.py --out ~/baien-graft-smoke
  → ~/baien-graft-smoke/{slug}/sample.json + view_0.png  (×10)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

# (slug, main_object noun, fill color name, draw fn) — main_object is what
# the visual_microbench scorer will match on.
SHAPES = [
    ("red-square",     "square",   "red"),
    ("blue-circle",    "circle",   "blue"),
    ("green-triangle", "triangle", "green"),
    ("yellow-star",    "star",     "yellow"),
    ("purple-diamond", "diamond",  "purple"),
    ("orange-cross",   "cross",    "orange"),
    ("black-square",   "square",   "black"),
    ("pink-circle",    "circle",   "pink"),
    ("brown-triangle", "triangle", "brown"),
    ("gray-square",    "square",   "gray"),
]


def draw_shape(draw: ImageDraw.ImageDraw, shape: str, color: str,
               size: int = 224) -> None:
    pad = size // 4
    box = (pad, pad, size - pad, size - pad)
    if shape == "square":
        draw.rectangle(box, fill=color)
    elif shape == "circle":
        draw.ellipse(box, fill=color)
    elif shape == "triangle":
        cx = size // 2
        draw.polygon([(cx, pad), (size - pad, size - pad), (pad, size - pad)],
                     fill=color)
    elif shape == "star":
        # simple 5-point star
        import math
        cx, cy = size // 2, size // 2
        r_out = (size - 2 * pad) // 2
        r_in = r_out // 2
        pts = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
        draw.polygon(pts, fill=color)
    elif shape == "diamond":
        cx, cy = size // 2, size // 2
        d = (size - 2 * pad) // 2
        draw.polygon([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)],
                     fill=color)
    elif shape == "cross":
        thick = (size - 2 * pad) // 4
        cx, cy = size // 2, size // 2
        draw.rectangle((cx - thick, pad, cx + thick, size - pad), fill=color)
        draw.rectangle((pad, cy - thick, size - pad, cy + thick), fill=color)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True,
                    help="output dir (will be created; one subdir per sample)")
    ap.add_argument("--size", type=int, default=224)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for slug, shape, color in SHAPES:
        sample_dir = args.out / slug
        sample_dir.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (args.size, args.size), "white")
        draw = ImageDraw.Draw(img)
        draw_shape(draw, shape, color, size=args.size)
        img.save(sample_dir / "view_0.png")
        sample_json = sample_dir / "sample.json"
        sample_json.write_text(
            json.dumps({
                "main_object": shape,
                "multi_view_caption": {
                    "view_0": f"a {color} {shape} on a white background",
                },
                "_synthetic": True,
                "_color": color,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"[gen-synthetic-smoke] wrote {len(SHAPES)} samples → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
