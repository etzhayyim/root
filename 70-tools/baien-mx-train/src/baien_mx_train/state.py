"""Training state + config dataclasses for baien Move 1 image graft.

Mirrors ADR-2605232500 §Training-stack pin + §Numerical analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# Phase identifier from ADR §Numerical analysis training-time budget table.
Phase = Literal["A", "B", "C", "D"]


PHASE_DEFAULTS: dict[str, dict[str, int]] = {
    "A": {"n_samples": 100, "epochs": 1},     # ~80 s smoke
    "B": {"n_samples": 1000, "epochs": 3},    # ~40 min bootstrap
    "C": {"n_samples": 10000, "epochs": 3},   # ~6.7 h scale
    "D": {"n_samples": 50000, "epochs": 3},   # ~33 h overnight
}


@dataclass(frozen=True)
class Move1Config:
    """All knobs that ADR-2605232500 pins. Built from CLI flags."""
    # data
    bench_dir: Path                                   # 90-docs/baien/
    graft_data_dir: Path                              # baien-graft sample.json root
    phase: Phase = "A"
    images_per_sample: int = 4                        # 4 of N views per baien-graft sample

    # model
    base_model: str = "microsoft/bitnet-b1.58-2B-4T-bf16"
    image_encoder: str = "google/siglip-base-patch16-224"

    # architecture (matches ADR §Decision; 14 chosen to divide SigLIP's
    # 196 patches evenly = pool kernel 14. ADR-2605232500 said 16; this
    # is a 12.5% smaller token budget that matches the math.)
    image_token_count: int = 14                       # projector downsample target (196/14=14)
    siglip_out_dim: int = 768                          # SigLIP-base patch-16-224
    baien_hidden_size: int = 2560                      # from baien config.json (verified)

    # train
    lr: float = 5e-4
    warmup_steps: int = 50
    per_device_batch: int = 1
    grad_accum: int = 4
    bf16: bool = True
    max_seq_text_tokens: int = 256                     # +16 image = 272 total

    # eval gate (ADR §Eval)
    visual_microbench_threshold: float = 0.60
    text_regression_floor_pp: float = -3.0

    # output
    out_root: Path = field(default=Path("baien-mx-out"))
    dry_run: bool = False


@dataclass
class Move1State:
    """Mutable per-iter state. Lives across train → eval → register nodes."""
    cfg: Move1Config
    iter: int = 0

    # populated as we go
    train_jsonl_path: Path | None = None
    train_dataset_hash: str | None = None
    n_train_rows: int = 0

    projector_path: Path | None = None
    final_loss: float | None = None

    visual_microbench_pass_rate: float | None = None
    text_microbench_delta_pp: float | None = None

    decision: Literal["pending", "commit", "retry", "abort"] = "pending"
    notes: list[str] = field(default_factory=list)


def resolve_phase(cfg: Move1Config) -> dict[str, int]:
    return PHASE_DEFAULTS.get(cfg.phase, PHASE_DEFAULTS["A"])
