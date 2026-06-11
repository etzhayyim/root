"""Move 7 3D loader — ADR-2605241940.

Uses **Pixal3D shape SLAT** (.npz) as the input latent, bypassing any
runtime 3D encoder. The data is already produced by `bgp-submit
--generator pixal3d` (per ADR-2605202115 amendment 2026-05-23).

Skeleton: SLAT exact schema (field names, dim, shape) needs verification
against the upstream Pixal3D-T export; deferred to next session probe.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


def load_three_d_input(shape_slat_path: Path, *, device: str = "cpu",
                       dtype: str = "bfloat16"):
    """Load Pixal3D shape SLAT (.npz) and shape it for the projector.

    Real impl: `np.load(shape_slat_path)` → extract latent feats →
    (1, n_input_tokens, output_dim). Stub returns zeros for the dry-run
    path.

    Output shape must match `MODALITY_REGISTRY['three_d']`:
      (1, n_input_tokens=128, output_dim=128)   [TBD verify]
    """
    import torch
    bf16 = getattr(torch, dtype)
    return torch.zeros((1, 128, 128), dtype=bf16, device=device)


def slat_schema_probe(shape_slat_path: Path) -> dict:
    """Inspect a Pixal3D shape SLAT file to surface its actual schema
    (field names, dtypes, shapes). Use this in the next session to fill
    in the MODALITY_REGISTRY['three_d'] dims correctly."""
    import numpy as np

    if not shape_slat_path.exists():
        return {"error": f"file not found: {shape_slat_path}"}
    arr = np.load(shape_slat_path)
    return {
        "keys": list(arr.keys()) if hasattr(arr, "keys") else None,
        "shapes": {k: tuple(arr[k].shape) for k in (arr.keys() if hasattr(arr, "keys") else [])},
        "dtypes": {k: str(arr[k].dtype) for k in (arr.keys() if hasattr(arr, "keys") else [])},
    }
