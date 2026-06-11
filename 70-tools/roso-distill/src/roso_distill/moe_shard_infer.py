r"""MoE-aware shard-streaming inference engine for roso server-tier siblings.

Bypasses transformers.from_pretrained (which pre-mmaps ALL safetensors
shards and explodes Windows paging file on 35B BF16). Uses accelerate's
init_empty_weights + load_checkpoint_and_dispatch with per-layer disk
offload — accelerate reads each tensor from its shard lazily, no full
mmap of all shards upfront.

For MoE specifically: per-token forward only touches the top-K active
experts per layer (8 of 256 in Qwen3.6-35B-A3B). Accelerate's offload
mechanism transparently loads each MoE expert's slice on first access
and evicts after — so per-token resident memory is roughly:
    embed + router + 8 active experts/layer × 40 layers + lm_head
which is ~2-6 GB depending on host vs disk placement.

Usage:
    python moe_shard_infer.py --ckpt C:\Users\gad\roso-35b-out\sibling-... \
        --prompt "Hello" --max-new-tokens 20
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTORCH_HIP_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


def build_engine(ckpt_dir: Path, offload_dir: Path,
                 cpu_budget_gib: int = 50,
                 keep_resident: tuple[str, ...] = (
                     "embed_tokens", "lm_head", "norm",
                 )):
    """Build the inference engine with init_empty_weights + lazy disk load."""
    print(f"[engine] config + tokenizer load (small) ...", flush=True)
    config = AutoConfig.from_pretrained(ckpt_dir)
    tok = AutoTokenizer.from_pretrained(ckpt_dir)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    print(f"[engine] init_empty_weights — building meta-model "
          f"(no actual tensors allocated)", flush=True)
    t0 = time.time()
    with init_empty_weights():
        model = AutoModelForCausalLM.from_config(config)
    print(f"[engine] meta-model built in {time.time()-t0:.1f}s "
          f"({sum(p.numel() for p in model.parameters()):,} params)", flush=True)

    # Use accelerate's auto device_map with explicit memory budgets so it
    # plans CPU + disk split itself. offload_state_dict=False avoids the
    # "Cannot copy out of meta tensor" error when some model params don't
    # match any checkpoint key (e.g. optional mtp head, unused attention
    # type per layer in hybrid linear+full attention models).
    print(f"[engine] load_checkpoint_and_dispatch from {ckpt_dir}", flush=True)
    print(f"[engine]   offload -> {offload_dir}", flush=True)
    t0 = time.time()
    offload_dir.mkdir(parents=True, exist_ok=True)
    # NOTE: accelerate's max_memory takes cpu/cuda/mps/etc but NOT "disk".
    # Disk offload is auto-triggered via offload_folder when cpu/cuda budgets
    # are exceeded.
    max_memory = {"cpu": f"{cpu_budget_gib}GiB"}
    model = load_checkpoint_and_dispatch(
        model, str(ckpt_dir),
        device_map="auto",
        max_memory=max_memory,
        offload_folder=str(offload_dir),
        offload_state_dict=False,            # avoid meta-tensor copy error
        offload_buffers=True,
        no_split_module_classes=[],
    )
    print(f"[engine] checkpoint dispatched in {time.time()-t0:.1f}s", flush=True)
    model.eval()
    return tok, model


def generate(tok, model, prompt: str, max_new_tokens: int = 20) -> dict:
    print(f"\n[gen] prompt={prompt!r}", flush=True)
    inputs = tok(prompt, return_tensors="pt")
    ids = inputs["input_ids"]
    print(f"[gen] tokenized to {ids.shape[1]} tokens", flush=True)
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    dt = time.time() - t0
    text = tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
    n_new = int(out.shape[1] - ids.shape[1])
    rate = n_new / max(dt, 1e-9)
    print(f"[gen] generated {n_new} tokens in {dt:.1f}s = {rate:.2f} tok/s", flush=True)
    print(f"[gen] output: {text!r}", flush=True)
    return {
        "prompt": prompt,
        "completion": text,
        "n_new_tokens": n_new,
        "wall_sec": round(dt, 2),
        "tokens_per_sec": round(rate, 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True, type=Path)
    ap.add_argument("--offload", type=Path, default=None)
    ap.add_argument("--prompt", default="Hello! The capital of Japan is")
    ap.add_argument("--max-new-tokens", type=int, default=10)
    ap.add_argument("--cpu-budget-gib", type=int, default=50)
    args = ap.parse_args()
    if args.offload is None:
        args.offload = args.ckpt.parent / "infer_offload"

    tok, model = build_engine(args.ckpt, args.offload,
                              cpu_budget_gib=args.cpu_budget_gib)
    result = generate(tok, model, args.prompt, args.max_new_tokens)

    out_path = args.ckpt / "moe_shard_infer_smoke.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\n[done] wrote {out_path}")


if __name__ == "__main__":
    main()
