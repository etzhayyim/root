#!/usr/bin/env python3
"""Baien-MX CPU smoke (ADR 2605101000 step 5/6).

Materializes 32 mixed multimodal "rows" matching the
v_training_multimodal_sample MV shape (text + optional triple +
optional vec768 + optional vec4096 + optional 3d-blob), builds a
BaienMXModel + a small mock-trunk readout, runs N optimizer steps,
and verifies that **every projector whose modality column was
non-NULL on at least one row received non-zero gradient**. This is
the test that catches:

  - silent disconnection between BaienMXModel.encode_modalities and
    the fusion block (e.g. forgotten requires_grad after a freeze)
  - per-modality optimizer param-group misses (training-runner
    regressions where one modality's row in
    vertex_training_checkpoint stays empty)
  - STE breakage in BitLinear (regresses bitnet_qat unit tests too,
    but the smoke is the integration witness)

CPU-only, fast (≈ 5 s on a laptop). No real trunk weights loaded.
The H100 sprint (step 6) replaces the mock-trunk with the real
BitNet 2B and the synthetic rows with a real
v_training_multimodal_sample snapshot.

Usage:
    python baien-mx-smoke.py --steps 5 --batch 8 --output /tmp/baien-mx-smoke
    python baien-mx-smoke.py --dry-run        # plan only, no train
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make the kotodama src importable when running from a checkout.
_SRC = Path(__file__).resolve().parents[2] / "20-actors" / "kotodama" / "py" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Baien-MX CPU smoke runner")
    p.add_argument("--steps", type=int, default=5)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--rows", type=int, default=32)
    p.add_argument("--d-model", type=int, default=64,
                   help="Test trunk hidden dim (real trunk = 2560).")
    p.add_argument("--triple-vocab-size", type=int, default=1024)
    p.add_argument("--threed-latent-dim", type=int, default=256)
    p.add_argument("--seed", type=int, default=20260510)
    p.add_argument("--learning-rate", type=float, default=5e-3)
    p.add_argument("--output", default="/tmp/baien-mx-smoke")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def _plan(args: argparse.Namespace) -> dict:
    return {
        "kind": "baien-mx-train",
        "modalities": ["triple", "vec768", "vec4096fp8", "3dblob"],
        "rows": args.rows,
        "batch": args.batch,
        "steps": args.steps,
        "dModel": args.d_model,
        "tripleVocabSize": args.triple_vocab_size,
        "threedLatentDim": args.threed_latent_dim,
        "seed": args.seed,
        "learningRate": args.learning_rate,
        "output": args.output,
    }


def _generate_mixed_rows(args: argparse.Namespace, rng) -> list[dict]:
    """Synthesize 32 multimodal rows mimicking
    v_training_multimodal_sample's LEFT-JOIN result. Each modality is
    present on a deterministic but mixed subset of rows so every
    projector branch fires on at least one row."""
    import torch
    rows = []
    for i in range(args.rows):
        # Mod 4 cycle so each modality is present on at least 25% of rows.
        present_triple = (i % 2 == 0)
        present_vec768 = (i % 3 == 0)
        present_vec4096 = (i % 4 == 0)
        present_3d = (i % 5 == 0)
        rows.append({
            "text_ids": torch.randint(0, 256, (16,), generator=rng),
            "triple": (
                (
                    torch.randint(0, args.triple_vocab_size, (1,), generator=rng).item(),
                    torch.randint(0, args.triple_vocab_size, (1,), generator=rng).item(),
                    torch.randint(0, args.triple_vocab_size, (1,), generator=rng).item(),
                ) if present_triple else None
            ),
            "vec768": (
                torch.randn(768, generator=rng) if present_vec768 else None
            ),
            "vec4096": (
                torch.randn(4096, generator=rng) if present_vec4096 else None
            ),
            "threed": (
                torch.randn(args.threed_latent_dim, generator=rng) if present_3d else None
            ),
        })
    return rows


def _mini_batches(rows: list[dict], batch_size: int):
    """Yield grouped sub-batches of rows that share the same modality
    presence pattern. Real H100 training will use a more sophisticated
    bucketing but for the smoke this is enough — what matters is that
    every projector receives gradient at least once over the 5 steps.
    """
    import torch
    by_pattern: dict[tuple[bool, bool, bool, bool], list[dict]] = {}
    for r in rows:
        pat = (
            r["triple"] is not None,
            r["vec768"] is not None,
            r["vec4096"] is not None,
            r["threed"] is not None,
        )
        by_pattern.setdefault(pat, []).append(r)

    for _pat, group in by_pattern.items():
        for i in range(0, len(group), batch_size):
            chunk = group[i:i + batch_size]
            if not chunk:
                continue
            sample = {
                "text_ids": torch.stack([r["text_ids"] for r in chunk]),
            }
            if chunk[0]["triple"] is not None:
                sample["triple"] = (
                    torch.tensor([r["triple"][0] for r in chunk]),
                    torch.tensor([r["triple"][1] for r in chunk]),
                    torch.tensor([r["triple"][2] for r in chunk]),
                )
            if chunk[0]["vec768"] is not None:
                sample["vec768"] = torch.stack([r["vec768"] for r in chunk])
            if chunk[0]["vec4096"] is not None:
                sample["vec4096"] = torch.stack([r["vec4096"] for r in chunk])
            if chunk[0]["threed"] is not None:
                sample["threed"] = torch.stack([r["threed"] for r in chunk])
            yield sample


def _train(args: argparse.Namespace) -> dict:
    """Heavy imports lazy so --dry-run stays fast."""
    import torch

    from kotodama.modules.baien_mx import (
        BaienMXModel,
        BaienMXSample,
    )

    rng = torch.Generator().manual_seed(args.seed)

    model = BaienMXModel(
        d_model=args.d_model,
        triple_vocab_size=args.triple_vocab_size,
        threed_latent_dim=args.threed_latent_dim,
        n_q_heads=8,
        n_kv_heads=2,
        ffn_hidden=128,
    )
    # Tiny mock readout standing in for the BitNet trunk + LM head.
    readout = torch.nn.Linear(args.d_model, 1)

    opt = torch.optim.Adam(
        list(model.parameters()) + list(readout.parameters()),
        lr=args.learning_rate,
    )

    rows = _generate_mixed_rows(args, rng)
    losses: list[float] = []
    grad_seen: dict[str, bool] = {
        "triple": False, "vec768": False, "vec4096fp8": False, "3dblob": False,
    }

    name_to_modality = {
        "proj_triple": "triple",
        "proj_vec768": "vec768",
        "proj_vec4096": "vec4096fp8",
        "proj_3d": "3dblob",
    }

    step = 0
    for step in range(args.steps):
        opt.zero_grad()
        # Run all sub-batches of one full epoch per step. With
        # rows=32, batch=8, this is ~5 mini-batches per step.
        step_loss = 0.0
        nb = 0
        for batch in _mini_batches(rows, args.batch):
            sample = BaienMXSample(
                text_ids=batch["text_ids"],
                triple=batch.get("triple"),
                vec768=batch.get("vec768"),
                vec4096=batch.get("vec4096"),
                threed=batch.get("threed"),
            )
            streams = model.encode_modalities(sample)
            if not streams:
                # text-only batch — skip in the smoke (the mock trunk
                # has nothing to read; real trunk handles this).
                continue
            # Concat modality token streams, fuse, mean-pool, regress
            # against a deterministic target derived from text_ids.
            tokens = torch.cat(list(streams.values()), dim=1)
            fused = model.fusion(tokens)
            pooled = fused.mean(dim=1)
            target = (sample.text_ids.float().mean(dim=-1, keepdim=True) > 128).float()
            loss = ((readout(pooled) - target) ** 2).mean()
            loss.backward()
            step_loss += float(loss.detach())
            nb += 1
        opt.step()
        losses.append(step_loss / max(nb, 1))
        # After the optimizer step, scrape gradient presence per
        # modality so we can assert each branch fired at least once.
        for attr_name, modality_name in name_to_modality.items():
            sub = getattr(model, attr_name)
            for p in sub.parameters():
                if p.grad is not None and p.grad.abs().sum().item() > 0:
                    grad_seen[modality_name] = True
                    break
        print(
            f"[baien-mx-smoke] step {step+1}/{args.steps} "
            f"loss={losses[-1]:.4f} grad_seen={grad_seen}",
            flush=True,
        )

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "ok": True,
        "plan": _plan(args),
        "metrics": {
            "lossSeries": losses,
            "finalLoss": losses[-1] if losses else None,
            "gradSeen": grad_seen,
            "stepsCompleted": step + 1 if losses else 0,
        },
    }
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[baien-mx-smoke] wrote {summary_path}")

    # Hard assertions — turn the smoke into a self-checking witness.
    missing = [m for m, seen in grad_seen.items() if not seen]
    assert not missing, (
        f"smoke FAILED — these projectors never received gradient: "
        f"{missing}. Either the synthesized rows did not exercise the "
        f"modality, or BaienMXModel skipped its branch."
    )
    return summary


def main() -> int:
    args = _parse_args()
    plan = _plan(args)
    print("[baien-mx-smoke] plan:", json.dumps(plan, indent=2))
    if args.dry_run:
        print("[baien-mx-smoke] --dry-run set, skipping training")
        return 0
    try:
        _train(args)
    except AssertionError as e:
        print(f"[baien-mx-smoke] FAILED: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[baien-mx-smoke] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
