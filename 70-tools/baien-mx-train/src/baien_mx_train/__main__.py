"""CLI entry — `python -m baien_mx_train ...`.

Per ADR-2605232500 §CLI surface, this wraps Move 1 training behind
phase-based defaults so the operator doesn't need to know the per-phase
numbers from the ADR (they're encoded in PHASE_DEFAULTS).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .state import Move1Config, Move1State
from .train import train


def main() -> int:
    ap = argparse.ArgumentParser(prog="baien-mx-train")
    ap.add_argument("--bench-dir", type=Path, default=Path("90-docs/baien"))
    ap.add_argument("--graft-data-dir", type=Path, required=True,
                    help="root of baien-graft sample outputs (per ADR-2605202115)")
    ap.add_argument("--phase", choices=["A", "B", "C", "D"], default="A")
    ap.add_argument("--base-model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    ap.add_argument("--image-encoder", default="google/siglip-base-patch16-224")
    ap.add_argument("--out-root", type=Path, default=Path("baien-mx-out"))
    ap.add_argument("--dry-run", action="store_true",
                    help="walk the trainer setup without loading SigLIP / baien")
    ap.add_argument("--eval-only", action="store_true",
                    help="skip training; init random projector + run visual_microbench "
                         "to measure the eval floor (untrained baseline). "
                         "Quality smoke per user request 2026-05-23.")
    ap.add_argument("--force-cpu", action="store_true",
                    help="force CPU even if CUDA/ROCm available "
                         "(workaround for BitNet × ROCm device-move issue)")
    args = ap.parse_args()

    cfg = Move1Config(
        bench_dir=args.bench_dir,
        graft_data_dir=args.graft_data_dir,
        phase=args.phase,
        base_model=args.base_model,
        image_encoder=args.image_encoder,
        out_root=args.out_root,
        dry_run=args.dry_run,
    )
    state = Move1State(cfg=cfg)
    if args.force_cpu:
        import os as _os
        _os.environ["CUDA_VISIBLE_DEVICES"] = ""
    if args.eval_only:
        from .eval import evaluate_baseline
        evaluate_baseline(state)
    else:
        train(state)

    print("\n=== mx-train notes ===")
    for n in state.notes:
        print(" ", n)
    print(f"\nn_train_rows={state.n_train_rows}")
    print(f"train_jsonl={state.train_jsonl_path}")
    print(f"dataset_hash={state.train_dataset_hash}")
    print(f"decision={state.decision}")
    if not cfg.dry_run:
        print("(real training path raises NotImplementedError until §Acceptance criteria #3 lands)")
    return 0 if state.decision in ("commit", "abort") or cfg.dry_run else 1


if __name__ == "__main__":
    sys.exit(main())
