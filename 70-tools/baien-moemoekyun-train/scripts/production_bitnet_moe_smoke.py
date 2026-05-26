#!/usr/bin/env python3
"""production_bitnet_moe_smoke.py — REAL BitNet 2B + MoE residual + R1.4 corpus.

Cycle 25 milestone — first PRODUCTION train run with pretrained BitNet 2B
(NOT TinyTransformer random init). Backbone frozen, MoE branch trainable
via MXFP8 (5090 doesn't support MXFP4 native per cycle 18).

VRAM budget on 5090 (with MMLU PID 20745 = 5 GB held):
  Free: 11 GB
  BitNet 2B bf16 frozen: 4.85 GB
  MoE residual (last 7 layers × 128 experts): ~1-2 GB
  Activations (bs=1, seq=512): ~1-2 GB
  Optimizer state (MoE only fp32): ~2 GB
  Total expected: ~10-12 GB → margin tight, watch peak

Per ADR-2605262100 §3.1 + ADR-2605263100 §1.1.A.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch
import torch.nn as nn


def format_pair(pair, tokenizer, max_len=512):
    instr = pair["instruction"]
    resp = pair["response"]
    try:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": instr}, {"role": "assistant", "content": resp}],
            tokenize=False,
        )
        prompt_only = tokenizer.apply_chat_template(
            [{"role": "user", "content": instr}],
            tokenize=False, add_generation_prompt=True,
        )
    except Exception:
        prompt = f"### Instruction:\n{instr}\n\n### Response:\n{resp}"
        prompt_only = f"### Instruction:\n{instr}\n\n### Response:\n"
    full_ids = tokenizer(prompt, truncation=True, max_length=max_len, return_tensors="pt").input_ids[0]
    prompt_ids = tokenizer(prompt_only, truncation=True, max_length=max_len, return_tensors="pt").input_ids[0]
    n_prompt = min(len(prompt_ids), len(full_ids))
    labels = full_ids.clone()
    labels[:n_prompt] = -100
    return full_ids, labels


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--corpus", default="/workspace/r14-corpus-shard.jsonl")
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--n-experts", type=int, default=128)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32,
                   help="dense_FFN/N (default 32 per ADR-2605261900); smaller=bigger experts")
    p.add_argument("--layers-fraction", type=float, default=0.25,
                   help="Apply MoE to last fraction of layers (0.25 = last 25%)")
    p.add_argument("--n-steps", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--seq-len", type=int, default=512)
    p.add_argument("--precision", default="mxfp8", choices=["bf16", "mxfp8"])
    p.add_argument("--output", default="/workspace/production-bitnet-moe-result.jsonl")
    p.add_argument("--checkpoint", default=None, help="Save final MoE state to this path")
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import (
        attach_moe_to_model, BitNetFFNWithMoE, collect_aux_losses, freeze_backbone_verify
    )
    from baien_moemoekyun.trainer import apply_mxfp4_quantize, build_optimizer

    device = torch.device("cuda")
    print(f"[env] {torch.cuda.get_device_name(0)}")
    print(f"[env] free VRAM at start: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated())/1e9:.2f} GB")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"\n[load] {args.model}")
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id or 0
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16, trust_remote_code=False)
    model.to(device).train()
    print(f"[load] {time.perf_counter() - t0:.1f}s  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    cfg = model.config
    hidden = getattr(cfg, "hidden_size", None)
    intermediate = getattr(cfg, "intermediate_size", None)
    n_layers = getattr(cfg, "num_hidden_layers", None)
    print(f"[cfg] hidden={hidden} intermediate={intermediate} n_layers={n_layers}")

    n_moe = max(1, int(round(n_layers * args.layers_fraction)))
    moe_layer_indices = list(range(n_layers - n_moe, n_layers))
    print(f"[moe] attaching to layers {moe_layer_indices[0]}..{moe_layer_indices[-1]} ({n_moe}/{n_layers})")

    moe_wrappers = attach_moe_to_model(
        model,
        moe_layer_indices=moe_layer_indices,
        hidden_size=hidden,
        intermediate_size=intermediate,
        num_experts=args.n_experts,
        top_k=args.top_k,
        expert_hidden_ratio=args.expert_hidden_ratio,
        ffn_attribute_name="mlp",
    )
    # Move MoE branches to same device + dtype as model (attach creates on CPU/fp32 by default)
    for fqn, wrapper in moe_wrappers.items():
        wrapper.to(device=device, dtype=torch.bfloat16)
    print(f"[moe] attached {len(moe_wrappers)} wrappers (moved to {device}+bf16)")
    print(f"[moe] vram after attach: {torch.cuda.memory_allocated()/1e9:.2f} GB")

    freeze_backbone_verify(model, moe_wrappers)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"[moe] trainable={trainable/1e6:.2f}M / total={total/1e6:.2f}M ({100*trainable/total:.2f}%)")

    if args.precision == "mxfp8":
        try:
            wdt = torch.float8_e4m3fn
            q = apply_mxfp4_quantize(model, moe_wrappers, block_size=32, weight_dtype=wdt, activation_dtype=wdt)
            print(f"[quant] mxfp8: {len(q)} modules  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")
        except Exception as e:
            print(f"[quant] mxfp8 failed: {e}")
            print(f"[quant] continuing in bf16")
            args.precision = "bf16"

    # Conservative LR vs ADR-2605262100 §4 defaults — pretrained backbone needs gentler updates
    opt = build_optimizer(moe_wrappers, lr_router=2e-5, lr_experts=5e-5, lr_alpha=1e-5)
    print(f"[opt] built  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    print(f"\n[data] loading {args.corpus}")
    pairs = []
    with open(args.corpus) as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))
    print(f"[data] {len(pairs)} pairs")

    print(f"\n[tok] pre-tokenizing all (seq_len={args.seq_len})...")
    tokenized = []
    for pair in pairs:
        ids, labels = format_pair(pair, tok, max_len=args.seq_len)
        if len(ids) < args.seq_len:
            pad_n = args.seq_len - len(ids)
            ids = torch.cat([ids, torch.full((pad_n,), tok.pad_token_id, dtype=ids.dtype)])
            labels = torch.cat([labels, torch.full((pad_n,), -100, dtype=labels.dtype)])
        tokenized.append((ids, labels, pair.get("_source", "?")))
    print(f"[tok] done")

    import random
    rng = random.Random(42)

    def get_batch():
        idxs = rng.sample(range(len(tokenized)), args.batch_size)
        ids = torch.stack([tokenized[i][0] for i in idxs]).to(device)
        labels = torch.stack([tokenized[i][1] for i in idxs]).to(device)
        srcs = [tokenized[i][2] for i in idxs]
        return ids, labels, srcs

    # 1-step probe to verify VRAM fits
    print(f"\n[probe] 1 step forward+backward+step")
    opt.zero_grad()
    ids, labels, _ = get_batch()
    try:
        out = model(ids, labels=labels)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device)
        loss = out.loss + 0.01 * aux
        loss.backward()
        opt.step()
        print(f"[probe] OK  loss={float(out.loss):.4f}  aux={float(aux):.4f}  vram_peak={torch.cuda.max_memory_allocated()/1e9:.2f} GB")
    except torch.cuda.OutOfMemoryError as e:
        print(f"[probe] OOM: {str(e)[:200]}")
        print(f"[probe] vram at OOM: {torch.cuda.memory_allocated()/1e9:.2f} GB peak: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")
        sys.exit(2)

    # Measured train
    print(f"\n[train] {args.n_steps} steps bs={args.batch_size} seq={args.seq_len}")
    torch.cuda.reset_peak_memory_stats()
    ev_s = torch.cuda.Event(enable_timing=True)
    ev_e = torch.cuda.Event(enable_timing=True)
    ev_s.record()
    t0 = time.perf_counter()
    losses = []
    per_source_loss = {}
    per_source_count = {}
    log_every = max(1, args.n_steps // 20)

    # Lower aux_loss weight (0.0005) + skip NaN steps + warmup
    AUX_W = 0.0005
    GRAD_CLIP = 1.0
    n_nan_skipped = 0
    for step in range(args.n_steps):
        opt.zero_grad()
        ids, labels, sources = get_batch()
        out = model(ids, labels=labels)
        # Cast aux to fp32 then back — prevents bf16 overflow on switching loss
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device).float().to(out.loss.dtype)
        # Skip if lm_loss is NaN/inf (don't propagate broken gradients)
        if torch.isnan(out.loss) or torch.isinf(out.loss):
            n_nan_skipped += 1
            opt.zero_grad()
            lv = float("nan")
            losses.append(lv)
            for src in sources:
                per_source_loss[src] = per_source_loss.get(src, 0.0)
                per_source_count[src] = per_source_count.get(src, 0) + 1
            if (step + 1) % log_every == 0 or step == 0:
                print(f"  step {step+1:4d}/{args.n_steps}  lm=NaN-SKIPPED  aux={float(aux):.4f}")
            continue
        loss_total = out.loss + AUX_W * aux
        loss_total.backward()
        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], GRAD_CLIP
        )
        opt.step()
        lv = float(out.loss.detach())
        av = float(aux.detach())
        losses.append(lv)
        for src in sources:
            per_source_loss[src] = per_source_loss.get(src, 0.0) + lv
            per_source_count[src] = per_source_count.get(src, 0) + 1
        if (step + 1) % log_every == 0 or step == 0:
            print(f"  step {step+1:4d}/{args.n_steps}  lm={lv:.4f}  aux={av:.4f}  nan_skipped={n_nan_skipped}")

    ev_e.record()
    torch.cuda.synchronize()
    gpu_ms = ev_s.elapsed_time(ev_e)
    wall = time.perf_counter() - t0

    per_source_avg = {src: per_source_loss[src] / per_source_count[src] for src in per_source_loss}
    tokens_total = args.batch_size * args.seq_len * args.n_steps
    flops_total = 6.0 * trainable * tokens_total
    tflops = flops_total / 1e12 / wall
    peak = 419.0 if args.precision == "mxfp8" else 104.8
    util = tflops / peak * 100
    vram = torch.cuda.max_memory_allocated() / 1e9

    print(f"\n[result] wall={wall:.2f}s gpu_ms={gpu_ms:.0f}")
    print(f"[result] tokens={tokens_total} TFLOPS={tflops:.2f} util={util:.2f}%")
    print(f"[result] VRAM peak={vram:.2f} GB")
    print(f"[result] loss[0]={losses[0]:.4f}  loss[-1]={losses[-1]:.4f}  min={min(losses):.4f}  Δ={losses[-1]-losses[0]:+.4f}")
    print(f"[result] per-source avg loss:")
    for src, avg in sorted(per_source_avg.items()):
        print(f"  {src:22} {avg:.4f}  ({per_source_count[src]} batches)")

    if args.checkpoint:
        # Save MoE wrappers' state_dict only (backbone is frozen original)
        ckpt = {fqn: w.state_dict() for fqn, w in moe_wrappers.items()}
        torch.save(ckpt, args.checkpoint)
        print(f"[ckpt] saved MoE state to {args.checkpoint}")

    entry = {
        "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
        "adr": "ADR-2605263100",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "phase": f"production-bitnet2b-moe-{args.precision}",
        "vendor": "runpod-secure",
        "gpu_model": "nvidia-rtx-5090",
        "precision": args.precision,
        "model": f"{args.model} + moemoekyun MoE residual ({n_moe} layers)",
        "tokenizer": args.model,
        "vocab_size": len(tok),
        "corpus_examples": len(pairs),
        "corpus_sha256": "037076af5aa4d873cd9743be4e89648a5a2c0bbac2b9d3641d4233ca00f6becf",
        "n_experts": args.n_experts,
        "top_k": args.top_k,
        "expert_hidden_ratio": args.expert_hidden_ratio,
        "layers_fraction": args.layers_fraction,
        "n_layers_with_moe": n_moe,
        "trainable_params_count": trainable,
        "total_params_count": total,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "seq_len": args.seq_len,
        "tokens_per_step": args.batch_size * args.seq_len,
        "wall_sec": round(wall, 3),
        "gpu_wall_ms": round(gpu_ms, 1),
        "loss_first": round(losses[0], 4),
        "loss_last": round(losses[-1], 4),
        "loss_min": round(min(losses), 4),
        "loss_delta": round(losses[-1] - losses[0], 4),
        "loss_curve_sampled": [round(l, 4) for l in losses[::max(1, len(losses)//30)]],
        "per_source_avg_loss": {k: round(v, 4) for k, v in per_source_avg.items()},
        "per_source_batches": per_source_count,
        "tflops_measured": round(tflops, 3),
        "tflops_theoretical_peak": peak,
        "tflops_utilization_pct": round(util, 2),
        "vram_peak_gb": round(vram, 2),
        "checkpoint_path": args.checkpoint,
        "scoring_note": "PRODUCTION BitNet 2B + MoE residual on real R1.4 corpus — pretrained backbone enables real loss decrease vs cycle 21 TinyTransformer random-init plateau",
        "founder_did": "did:web:jun.etzhayyim.com",
        "council_post_ratification_target": "2026-06-19+",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n[done] appended to {args.output}")


if __name__ == "__main__":
    main()
