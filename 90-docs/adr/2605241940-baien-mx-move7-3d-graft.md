---
id: adr-2605241940-baien-mx-move7-3d-graft
title: "Baien Move 7 — 3D graft (Pixal3D SLAT / PointTransformer + 1.58-bit projector + frozen baien trunk)"
status: proposed
doc_type: adr
topic: baien-multimodal
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien Move 7 3D architecture
  - Move 7 data source = reuse baien-graft Pixal3D outputs (ADR-2605202115 amendment)
  - Move 7 fit within ADR-2605241900 edge ceiling
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605202115-baien-graft-3d-augmented-dataset
  - adr-2605232500-baien-mx-move1-image-graft-self-training
  - adr-2605241900-baien-edge-target-invariant
related:
  - 70-tools/baien-graft-pipeline/   (data source — Pixal3D backend per amendment)
  - 70-tools/baien-mx-train/         (extends Move 1 stack to modality=three_d)
supersedes: []
superseded_by: []
---

# Goal

Add **3D scene/object understanding** to baien via 1.58-bit projector,
reusing the **Pixal3D output already produced by baien-graft** as the
training data (per ADR-2605202115 amendment 2026-05-23).

Move 7 is unique among the modality grafts because **the data is
already being generated** by the same fleet for Move 1, so the
incremental data-gen cost is ~0.

# Edge fit (per ADR-2605241900)

Two encoder candidates, both small enough:

| Component | Size | Notes |
|---|---|---|
| **Option A**: PointTransformer-small (frozen, bf16) | **50 MB** | input = point cloud (N×3); ScanNet-class quality |
| **Option B**: re-use Pixal3D's **shape SLAT (.npz)** + 1.58-bit projector | **0 MB extra** | encoder IS Pixal3D-T which already runs in baien-graft; baien sees the SLAT directly via a small reshape |
| 1.58-bit projector | **2 MB** | output 14 3D tokens × 2560 |

This ADR defaults to **Option B (Pixal3D SLAT)**: the SLAT already
encodes the 3D shape from Pixal3D's training; we just bridge it to
baien via a projector. Zero extra encoder cost on edge.

Option A (PointTransformer) is available as a fallback if SLAT proves
insufficient signal.

Cumulative encoder footprint after Move 7 (Option B):
- SigLIP 170 MB + Whisper-tiny 80 MB + (Pixal3D SLAT inline, no extra) = **250 MB**
- Within 600 MB ceiling ✓

# Decision

| Pin | Value |
|---|---|
| Primary encoder | **Pixal3D shape SLAT** (already produced by `bgp-submit --generator pixal3d`) |
| Fallback encoder | `Uni3D-small` (or `PointTransformer-small`) if SLAT signal insufficient after Move 7 Phase B |
| Projector input dim | Pixal3D SLAT latent dim (TBD — read from Pixal3D-T config; cached in `MODALITY_REGISTRY`) |
| Projector output dim | 2560 |
| Downsample target | **14 3D tokens** (matches image budget for ceiling parity) |
| Chat-template insertion | `<three_d>` placeholder |
| Loss mask | mask all `<three_d>` positions to -100 |

# Numerical analysis

Trainable params: identical structure to Move 1's 14-token projector
(~7-9 M params, ~1.6 MB packed). No change to baien trunk.

Training-time budget on EVO-X2:

| Phase | rows | epochs | wall (ROCm 2.3×) |
|---|---|---|---|
| A smoke | 100 SLAT samples (= 100 baien-graft Pixal3D outputs) | 1 | ~45 sec |
| B bootstrap | 1 000 | 3 | ~15 min |
| C scale | 10 000 | 3 | ~2.5 h |

Phase A's 100 samples requires **3 Pixal3D runs** (48 views/sample
each gives 48 SLATs — wait, no, each Pixal3D run produces 1 shape SLAT
+ 1 tex SLAT, not 48 of each). So 100 distinct objects × 1 SLAT each
= 100 baien-graft Pixal3D runs. At 120 s/run = **3.3 h data-gen**.

# Eval (`three_d_microbench`)

5 verifiable 3D prompts (proposed):

| id | input | prompt | scorer |
|---|---|---|---|
| tmb_object_name | Pixal3D-generated SLAT from labeled image (e.g. chair) | "What 3D object is this? One word." | substring `chair` |
| tmb_geometry | SLAT of cube | "Is this object angular or round? One word." | `angular` |
| tmb_count_parts | SLAT of multi-part object | "How many primary parts? Single digit." | regex 1-9 matches GT |
| tmb_orientation | SLAT of asymmetric object | "Which axis is the long axis? x, y, or z." | exact GT |
| tmb_volume_compare | SLAT of large vs small same-class | (paired) "Larger or smaller than chair-A? One word." | substring `larger` or `smaller` matches GT |

Move 7 gate (analogous to Move 1):
- three_d_microbench ≥ 60% (3/5)
- text + image + audio microbench regression Δ ≥ -3 pp each

# Data source — Pixal3D reuse path

The baien-graft pipeline (`bgp-submit --generator pixal3d`) already
emits, per sample:

```
glb mesh
shape SLAT (.npz)       ← Move 7 input
tex   SLAT (.npz)       (unused by Move 7)
8 × normal renders      (Move 1 image graft input)
8 × clay renders        (Move 1 alt input)
8 × base_color renders  (Move 1 textured input)
24 × shaded renders     (Move 1 environmental variation)
```

The shape SLAT is a sparse-latent of the geometry — typically a few
hundred KB per sample, far smaller than the full glb mesh.

Adding the Move 7 data loader is a sample.json field read away:

```python
class GraftRow:
    ...
    shape_slat_path: Path | None    # Pixal3D backend only
```

And the trainer's `_build_inference_fn` for modality=three_d loads
the SLAT via numpy and passes it to the projector (no encoder forward
needed — SLAT is already a latent).

# Skeleton (extends `70-tools/baien-mx-train/`)

```
70-tools/baien-mx-train/src/baien_mx_train/
├── moves/
│   ├── audio.py            (Move 4)
│   └── three_d.py          (NEW — this ADR)
├── adapters/
│   ├── modality.py         (registry — adds "three_d")
│   └── graft_dataset.py    (extends GraftRow with shape_slat_path)
```

`moves/three_d.py`:

```python
def load_three_d_input(graft_row: GraftRow) -> torch.Tensor:
    """Load Pixal3D shape SLAT (.npz) for the trainer; returns (1, N, D)
    tensor ready for the 14-token projector."""
    import numpy as np
    slat = np.load(graft_row.shape_slat_path)  # likely {"coords": ..., "feats": ...}
    # TBD: exact field names depend on Pixal3D-T export schema
    return torch.from_numpy(slat["feats"]).unsqueeze(0).bfloat16()
```

# Implications

- Move 7 ships within the edge invariant (verified above).
- **No new encoder weights** on the deployed artifact (the SLAT path
  reuses Pixal3D-T which lives in baien-graft data-gen, not in baien
  inference). Net edge weight footprint: **+2 MB projector only**.
- Move 7 unblocks 3D-grounded multimodal output ("what is in this 3D
  scene?") with zero new dataset acquisition cost.
- Move 7's gate is the easiest of all Moves because data is already
  flowing and the modality is well-matched to baien-graft's strength.

# Acceptance criteria

1. `70-tools/baien-mx-train/src/baien_mx_train/moves/three_d.py` exists
   with the SLAT loader stub.
2. `adapters/modality.py` MODALITY_REGISTRY includes "three_d".
3. `adapters/graft_dataset.py` `GraftRow` gains `shape_slat_path`.
4. `e7m bench mx-train --modality three_d --phase A --dry-run` walks
   trainer setup; reports missing SLAT files clearly when none
   present in the graft data dir.

# Open issues

- Pixal3D-T's SLAT export schema needs verification (field names,
  shape, dtype). To be probed in next session — defer.
- Pixal3D's shape SLAT and Move 1's "view" images can be **co-trained
  cross-modally** in Move 2 (cross-modal fusion block per
  ADR-2605101000) — natural future direction.

# References

- ADR-2605202115 baien-graft 3D-augmented dataset (Pixal3D amendment 2026-05-23)
- ADR-2605232500 Move 1 image graft (same LLaVA pattern, different encoder)
- ADR-2605241900 baien edge-target invariant (this Move's ceiling check)
- Pixal3D Space: https://huggingface.co/spaces/TencentARC/Pixal3D
- PointTransformer-small (fallback): https://github.com/Pointcept/PointTransformerV3
