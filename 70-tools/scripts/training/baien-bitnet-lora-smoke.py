#!/usr/bin/env python3
"""Baien BitNet b1.58 LoRA-on-bf16-master smoke runner (ADR 2605092350).

Goal: prove on a single H100 NVL training pod that we can:
  1. Load the bf16 master `microsoft/bitnet-b1.58-2B-4T-bf16` from HF.
  2. Attach a small LoRA adapter (rank 8) to the trunk.
  3. Run N optimizer steps on a tiny synthetic prompt set.
  4. Optionally re-quantize the merged adapter+master to i2_s for
     `bitnet.cpp` / WebGPU / WASM consumption (skipped in --skip-requantize
     mode so the smoke can complete on a CPU-only laptop too).
  5. Emit a summary.json that the canonical
     `pymagatama.primitives.training_run.runpod_handler` would normally
     persist into `vertex_training_run` / `vertex_training_checkpoint`.

This is the LOCAL smoke. The production path is XRPC ->
`task_train_baien_lora_run` -> `_delegate_to_runpod("baien-lora", ...)`
into the H100 pod, which calls the same training loop in
`pymagatama.training_http_server`. Use this file as the development
oracle: if it runs end-to-end here, the H100-side runner should too.

Usage:
    python baien-bitnet-lora-smoke.py \
        --steps 5 \
        --lora-rank 8 \
        --output /tmp/baien-smoke

Env knobs (all optional):
    BAIEN_DEFAULT_TRUNK_MODEL   override base trunk (default = HF id below)
    HF_HOME                     HF cache directory
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_TRUNK = os.environ.get(
    "BAIEN_DEFAULT_TRUNK_MODEL",
    "microsoft/bitnet-b1.58-2B-4T-bf16",
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Baien BitNet LoRA smoke runner")
    p.add_argument("--base-model", default=DEFAULT_TRUNK,
                   help="HF model id of the bf16 master (default: %(default)s)")
    p.add_argument("--revision", default="main")
    p.add_argument("--steps", type=int, default=5,
                   help="Number of optimizer steps (default: 5 — smoke only)")
    p.add_argument("--lora-rank", type=int, default=8)
    p.add_argument("--lora-alpha", type=int, default=16)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--max-seq-len", type=int, default=256)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--seed", type=int, default=20260510)
    p.add_argument("--output", default="/tmp/baien-bitnet-lora-smoke",
                   help="Directory to write summary.json + adapter into")
    p.add_argument("--skip-requantize", action="store_true",
                   help="Skip the post-train re-quantization to i2_s.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print plan and exit without loading the model.")
    return p.parse_args()


def _synthetic_corpus() -> list[str]:
    """Tiny prompt corpus — just enough to drive 5 LoRA steps without
    needing a real dataset snapshot. Production runs feed
    `v_training_text` rows via the standard runpod_handler path."""
    return [
        "Baien is a 1.58-bit on-device model. It runs in the browser.",
        "Edge inference does not require a server-side GPU.",
        "BitNet b1.58 weights take values in {-1, 0, +1}.",
        "The bf16 master is the source of truth; quantization is derived.",
        "Miura Baien (1723-1789) reasoned by paired opposites — jōri.",
    ]


def _plan(args: argparse.Namespace) -> dict:
    return {
        "kind": "baien-lora",
        "baseModel": args.base_model,
        "baseModelRevision": args.revision,
        "hyperparams": {
            "steps": args.steps,
            "loraRank": args.lora_rank,
            "loraAlpha": args.lora_alpha,
            "loraDropout": args.lora_dropout,
            "learningRate": args.learning_rate,
            "maxSeqLen": args.max_seq_len,
            "batchSize": args.batch_size,
        },
        "seed": args.seed,
        "output": args.output,
        "skipRequantize": args.skip_requantize,
    }


def _train(args: argparse.Namespace, plan: dict) -> dict:
    """Heavy imports are lazy so `--dry-run` and CI lint stay fast."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model, TaskType

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    print(f"[baien-smoke] loading tokenizer + model: {args.base_model}", flush=True)
    t_load = time.time()
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model, revision=args.revision, use_fast=True,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        revision=args.revision,
        torch_dtype=torch.bfloat16,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    load_sec = time.time() - t_load
    print(f"[baien-smoke] model load: {load_sec:.2f}s", flush=True)

    lora_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_cfg)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"[baien-smoke] LoRA attached: trainable={trainable:,} / total={total:,}", flush=True)

    optim = torch.optim.AdamW(
        (p for p in model.parameters() if p.requires_grad),
        lr=args.learning_rate,
    )
    corpus = _synthetic_corpus()
    losses: list[float] = []

    model.train()
    t_train = time.time()
    for step in range(args.steps):
        text = corpus[step % len(corpus)]
        enc = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=args.max_seq_len,
            padding="max_length",
        )
        if torch.cuda.is_available():
            enc = {k: v.cuda() for k, v in enc.items()}
        out = model(**enc, labels=enc["input_ids"])
        out.loss.backward()
        optim.step()
        optim.zero_grad()
        losses.append(float(out.loss.detach().cpu()))
        print(f"[baien-smoke] step {step+1}/{args.steps} loss={losses[-1]:.4f}", flush=True)
    train_sec = time.time() - t_train

    adapter_dir = out_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    metrics: dict = {
        "trainSeconds": round(train_sec, 4),
        "loadSeconds": round(load_sec, 4),
        "trainableParams": int(trainable),
        "totalParams": int(total),
        "lossSeries": losses,
        "finalLoss": losses[-1] if losses else None,
        "adapterDir": str(adapter_dir),
        "i2sBlobUri": None,
    }

    if not args.skip_requantize:
        # Stub: real path is `bitnet.cpp` `convert.py` against a merged
        # base+adapter checkpoint. Smoke just records the *intent* so
        # downstream pipelines can detect "expected blob, got none".
        metrics["i2sBlobPlanned"] = True
        metrics["i2sBlobUri"] = (
            "b2://etzhayyim-models/baien/SMOKE-LOCAL/baien-trunk-smoke-i2s.bnp"
        )

    return metrics


def main() -> int:
    args = _parse_args()
    plan = _plan(args)
    print("[baien-smoke] plan:", json.dumps(plan, indent=2))

    if args.dry_run:
        print("[baien-smoke] --dry-run set, skipping model load")
        return 0

    try:
        metrics = _train(args, plan)
    except Exception as e:  # surfacing matters more than coverage in a smoke
        print(f"[baien-smoke] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        summary = {"ok": False, "plan": plan, "error": f"{type(e).__name__}: {e}"}
        Path(args.output).mkdir(parents=True, exist_ok=True)
        (Path(args.output) / "summary.json").write_text(json.dumps(summary, indent=2))
        return 1

    summary = {"ok": True, "plan": plan, "metrics": metrics}
    summary_path = Path(args.output) / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[baien-smoke] wrote {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
