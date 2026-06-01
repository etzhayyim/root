"""CLI entry — `python -m roso_distill ...` and `roso ...`.

Pipeline: pull_base → quantize → recovery (if Phase B) → attest → commit.
Each stage updates RosoState in-place. dry-run mode walks the entire
pipeline without loading any model weights.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .attestation import attest
from .commit import commit_to_registry
from .pull_base import pull
from .quantize import quantize
from .recovery import recovery
from .state import BASE_CANDIDATES, RosoConfig, RosoState, derive_sibling_id


def main() -> int:
    ap = argparse.ArgumentParser(prog="roso")
    ap.add_argument("--base-model", required=True, choices=sorted(BASE_CANDIDATES.keys()),
                    help="HF id of the base model to Bonsai-quantize")
    ap.add_argument("--quant-method", default="bonsai-w1",
                    choices=["bonsai-w1", "bnb-nf4", "bnb-int8", "gptq-w4", "manual-stub"])
    ap.add_argument("--phase", choices=["A", "B"], default="A",
                    help="A = quantize only (~10 min on EVO-X2 ROCm); "
                         "B = quantize + distill recovery (~1-3 days)")
    ap.add_argument("--out-root", type=Path, default=Path("roso-out"))
    ap.add_argument("--bench-dir", type=Path, default=Path("90-docs/baien"))
    ap.add_argument("--recovery-datasets", nargs="*",
                    default=["lordx64/reasoning-distill-opus-4-7-max-sft"])
    ap.add_argument("--recovery-n-per-dataset", type=int, default=5000)
    ap.add_argument("--dry-run", action="store_true",
                    help="walk full pipeline without loading any model weights")
    args = ap.parse_args()

    cfg = RosoConfig(
        base_model=args.base_model,
        quant_method=args.quant_method,
        phase=args.phase,
        out_root=args.out_root,
        bench_dir=args.bench_dir,
        recovery_datasets=tuple(args.recovery_datasets),
        recovery_n_per_dataset=args.recovery_n_per_dataset,
        dry_run=args.dry_run,
    )
    state = RosoState(cfg=cfg)

    # Run pipeline stages
    state = pull(state)
    if state.decision != "abort":
        state = quantize(state)
    if state.decision != "abort":
        state = recovery(state)
    if state.decision != "abort":
        state = attest(state)
    if state.decision != "abort" and state.attestation_passed:
        state.decision = "commit"
        commit_to_registry(state)
    elif state.decision == "pending":
        state.decision = "abort"

    print("\n=== roso trace ===")
    for n in state.notes:
        print(" ", n)
    print(f"\nbase:                 {cfg.base_model}")
    print(f"quant_method:         {cfg.quant_method}")
    print(f"phase:                {cfg.phase}")
    print(f"sibling_id:           {state.sibling_id or derive_sibling_id(cfg.base_model, cfg.quant_method, cfg.phase)}")
    print(f"packed_gb:            {state.packed_weights_gb}")
    print(f"ram_4k_gb:            {state.attestation_ram_4k_gb}")
    print(f"ram_16k_gb:           {state.attestation_ram_16k_gb}")
    print(f"edge_invariant_pass:  {state.attestation_passed}")
    print(f"decision:             {state.decision}")
    return 0 if state.decision in ("commit", "abort") else 1


if __name__ == "__main__":
    sys.exit(main())
