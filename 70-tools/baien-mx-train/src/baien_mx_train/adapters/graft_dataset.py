"""Read baien-graft sample.json outputs (per ADR-2605202115) into an
(image, caption) iterator for Move 1 training.

Each baien-graft sample produces multiple (image, caption) rows
(default 4, the 4 canonical views). Pixal3D output gives 48 view
variants — we sample `images_per_sample` of them.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GraftRow:
    image_path: Path
    caption: str
    main_object: str
    source_sample: str          # sample slug for lineage
    color: str | None = None    # ground-truth color (set by synthetic data; None for real images)


def iter_graft_rows(graft_root: Path, *, images_per_sample: int = 4,
                    seed: int = 0) -> Iterable[GraftRow]:
    """Walk `graft_root` for sample.json files and yield rows.

    Expected layout (per ADR-2605202115):

      graft_root/
        <slug>/sample.json   # describes the sample
        <slug>/image.png     # input image
        <slug>/view_*.png    # rendered views (4 for Hunyuan3D, 48 for Pixal3D)
    """
    rng = random.Random(seed)
    for sample_json in sorted(graft_root.glob("*/sample.json")):
        try:
            meta = json.loads(sample_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = sample_json.parent.name
        captions = meta.get("multi_view_caption", {})  # {view_name: caption}
        main_object = (meta.get("main_object") or "").strip()
        views = list(captions.items())
        if not views:
            continue
        rng.shuffle(views)
        color = (meta.get("_color") or "").strip().lower() or None
        for view_name, cap in views[:images_per_sample]:
            img_path = sample_json.parent / f"{view_name}.png"
            if not img_path.exists():
                continue
            if not cap or not main_object:
                continue
            yield GraftRow(
                image_path=img_path,
                caption=cap,
                main_object=main_object,
                source_sample=slug,
                color=color,
            )


def collect(graft_root: Path, *, n_rows: int,
            images_per_sample: int = 4) -> list[GraftRow]:
    """Materialize up to n_rows of GraftRow."""
    out: list[GraftRow] = []
    for r in iter_graft_rows(graft_root, images_per_sample=images_per_sample):
        out.append(r)
        if len(out) >= n_rows:
            break
    return out
