#!/usr/bin/env python3
"""production_bitnet_moe_r14_full.py — full R1.4 train (128 experts × 7 layers).

Cycle 28+ deliverable: scale cycle 26's working smoke (16 experts × 3 layers,
100 steps, Δ-1.74) to full R1.4 specification per ADR-2605262100:
  - 128 experts (vs 16)
  - 7 layers = last 25% of BitNet 2B's 28 layers (vs 3 = 10%)
  - 5000 steps (vs 100)
  - With cycle 26's fp32 routing fix at source (commit 297259405)
  - With NaN-skip safety (kept from cycle 26)

VRAM estimate on 5090 (with MMLU coexisting):
  BitNet 2B bf16 frozen: 4.85 GB
  + MoE residual 128 experts × 7 layers (dense_FFN/32 each): ~3-4 GB
  + Activations (bs=1, seq=512): ~2-3 GB
  + Optimizer fp32 (Adam moments) for ~1B trainable: ~4-8 GB
  Total: 14-20 GB → tight when MMLU + new process hold 22 GB
  Use bs=1 + gradient_checkpointing if needed

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
    # R1.4 spec defaults
    p.add_argument("--n-experts", type=int, default=128, help="ADR-2605261900 §1 = 128")
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32, help="dense_FFN/32 per ADR")
    p.add_argument("--layers-fraction", type=float, default=0.25, help="last 25% layers per ADR")
    p.add_argument("--n-steps", type=int, default=5000, help="R1.4 spec = 5000 = 5K examples × 1 epoch")
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--seq-len", type=int, default=512)
    p.add_argument("--precision", default="mxfp8", choices=["bf16", "mxfp8"])
    # Cycle 26 hyperparameters that worked
    p.add_argument("--lr-router", type=float, default=2e-5)
    p.add_argument("--lr-experts", type=float, default=5e-5)
    p.add_argument("--lr-alpha", type=float, default=1e-5)
    p.add_argument("--aux-loss-weight", type=float, default=0.0005)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--warmup-steps", type=int, default=100)
    p.add_argument("--checkpoint-every", type=int, default=500)
    p.add_argument("--output", default="/workspace/r14-full-result.jsonl")
    p.add_argument("--checkpoint-dir", default="/workspace/moe-ckpt-r14-full/")
    # R2 partial backbone unfreeze (ADR-2605262100 §3.2)
    p.add_argument("--unfreeze-last-n-layers", type=int, default=0,
                   help="R2: unfreeze backbone shared FFN + layernorm in last N layers (0 = pure R1 frozen-backbone)")
    p.add_argument("--unfreeze-lr", type=float, default=5e-6,
                   help="R2: LR for unfrozen backbone params (default 5e-6 = ~10x lower than MoE LR)")
    p.add_argument("--routing-mode", default="learned", choices=["learned", "distance"],
                   help="MoE router type: 'learned' (default linear) | 'distance' (MoCLE-style cluster centroids)")
    p.add_argument("--expert-kind", default="ffn", choices=["ffn", "memory"],
                   help="Expert kind: 'ffn' (default 2-layer SiLU) | 'memory' (UltraMem-style single learnable vector)")
    p.add_argument("--alpha-init", type=float, default=0.0,
                   help="α gate init (default 0.0 per G5; cycle 113 found that α=0 → zero gradient flow through residual path, "
                        "so a small non-zero init like 0.1 may be needed to bootstrap training)")
    p.add_argument("--alpha-init-jitter", type=float, default=1e-3,
                   help="α init jitter for symmetry-breaking (default 1e-3)")
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.attach import (
        attach_moe_to_model, collect_aux_losses, freeze_backbone_verify
    )
    from baien_moemoekyun.trainer import apply_mxfp4_quantize, build_optimizer

    device = torch.device("cuda")
    print(f"[env] {torch.cuda.get_device_name(0)}")
    print(f"[env] free VRAM: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated())/1e9:.2f} GB")

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
    hidden = cfg.hidden_size
    intermediate = cfg.intermediate_size
    n_layers = cfg.num_hidden_layers
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
        routing_mode=args.routing_mode,
        expert_kind=args.expert_kind,
        alpha_init=args.alpha_init,
        alpha_init_jitter=args.alpha_init_jitter,
    )
    print(f"[moe] routing_mode={args.routing_mode} expert_kind={args.expert_kind}")
    for fqn, w in moe_wrappers.items():
        w.to(device=device, dtype=torch.bfloat16)
    print(f"[moe] attached {len(moe_wrappers)} wrappers  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    freeze_backbone_verify(model, moe_wrappers)
    # R2 PARTIAL UNFREEZE per ADR-2605262100 §3.2: shared FFN + layernorm
    # in the LAST `unfreeze_last_n_layers` layers at LR `unfreeze_lr`
    # (default 5e-6 = 4-10x lower than MoE LR to prevent catastrophic forgetting)
    backbone_unfrozen = []
    if getattr(args, "unfreeze_last_n_layers", 0) > 0:
        unfreeze_n = args.unfreeze_last_n_layers
        n_layers = model.config.num_hidden_layers
        unfreeze_layer_indices = list(range(n_layers - unfreeze_n, n_layers))
        # Unfreeze backbone shared FFN (mlp.backbone_ffn = original BitNet FFN) + layernorm in target layers
        for layer_idx in unfreeze_layer_indices:
            layer = model.model.layers[layer_idx]
            # The MoE wrapper (BitNetFFNWithMoE) preserved original FFN as `original_ffn`
            if hasattr(layer.mlp, "original_ffn"):
                for p in layer.mlp.original_ffn.parameters():
                    p.requires_grad = True
                    backbone_unfrozen.append(p)
            elif hasattr(layer, "mlp"):
                # Non-MoE layer: full mlp is backbone
                for p in layer.mlp.parameters():
                    p.requires_grad = True
                    backbone_unfrozen.append(p)
            # Unfreeze layer norms
            for ln_attr in ("input_layernorm", "post_attention_layernorm"):
                ln = getattr(layer, ln_attr, None)
                if ln is not None:
                    for p in ln.parameters():
                        p.requires_grad = True
                        backbone_unfrozen.append(p)
        print(f"[r2-unfreeze] unfroze {len(backbone_unfrozen)} backbone params across last {unfreeze_n} layers")
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"[moe] trainable={trainable/1e6:.2f}M / total={total/1e6:.2f}M ({100*trainable/total:.2f}%)")

    if args.precision == "mxfp8":
        try:
            wdt = torch.float8_e4m3fn
            q = apply_mxfp4_quantize(model, moe_wrappers, block_size=32, weight_dtype=wdt, activation_dtype=wdt)
            print(f"[quant] mxfp8: {len(q)} modules")
        except Exception as e:
            print(f"[quant] mxfp8 unavailable: {e}; bf16 fallback")
            args.precision = "bf16"

    # Build optimizer with cycle 26 LR
    opt = build_optimizer(
        moe_wrappers,
        lr_router=args.lr_router,
        lr_experts=args.lr_experts,
        lr_alpha=args.lr_alpha,
    )
    # R2: add backbone unfrozen params at much lower LR
    if backbone_unfrozen:
        opt.add_param_group({"params": backbone_unfrozen, "lr": args.unfreeze_lr, "name": "backbone_unfrozen"})
        print(f"[r2-unfreeze] added backbone param group at LR {args.unfreeze_lr}")
    # Add linear warmup + cosine decay scheduler
    from torch.optim.lr_scheduler import LambdaLR
    def lr_lambda(step):
        if step < args.warmup_steps:
            return step / args.warmup_steps
        # Cosine decay from warmup to n_steps
        progress = (step - args.warmup_steps) / max(1, args.n_steps - args.warmup_steps)
        import math
        return 0.5 * (1 + math.cos(math.pi * progress))
    sched = LambdaLR(opt, lr_lambda=lr_lambda)
    print(f"[opt] built (warmup={args.warmup_steps} steps cosine to {args.n_steps})  vram={torch.cuda.memory_allocated()/1e9:.2f} GB")

    # Load + tokenize corpus
    print(f"\n[data] loading {args.corpus}")
    pairs = []
    with open(args.corpus) as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))
    print(f"[data] {len(pairs)} pairs")

    print(f"\n[tok] pre-tokenizing (seq_len={args.seq_len})...")
    tokenized = []
    for pair in pairs:
        ids, labels = format_pair(pair, tok, max_len=args.seq_len)
        if len(ids) < args.seq_len:
            pad_n = args.seq_len - len(ids)
            ids = torch.cat([ids, torch.full((pad_n,), tok.pad_token_id, dtype=ids.dtype)])
            labels = torch.cat([labels, torch.full((pad_n,), -100, dtype=labels.dtype)])
        tokenized.append((ids, labels, pair.get("_source", "?")))
    print(f"[tok] {len(tokenized)} tokenized")

    import random
    rng = random.Random(42)
    def get_batch():
        idxs = rng.sample(range(len(tokenized)), args.batch_size)
        ids = torch.stack([tokenized[i][0] for i in idxs]).to(device)
        labels = torch.stack([tokenized[i][1] for i in idxs]).to(device)
        srcs = [tokenized[i][2] for i in idxs]
        return ids, labels, srcs

    # Probe VRAM
    print(f"\n[probe] 1 step...")
    opt.zero_grad()
    ids, labels, _ = get_batch()
    try:
        out = model(ids, labels=labels)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device).float().to(out.loss.dtype)
        (out.loss + args.aux_loss_weight * aux).backward()
        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], args.grad_clip
        )
        opt.step()
        sched.step()
        print(f"[probe] OK  loss={float(out.loss):.4f}  vram_peak={torch.cuda.max_memory_allocated()/1e9:.2f} GB")
    except torch.cuda.OutOfMemoryError as e:
        print(f"[probe] OOM: {str(e)[:200]}")
        print(f"[probe] consider --layers-fraction smaller, --n-experts smaller, or wait for VRAM")
        sys.exit(2)

    # Main train loop
    print(f"\n[train] {args.n_steps} steps bs={args.batch_size} seq={args.seq_len}")
    Path(args.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    torch.cuda.reset_peak_memory_stats()
    ev_s = torch.cuda.Event(enable_timing=True)
    ev_e = torch.cuda.Event(enable_timing=True)
    ev_s.record()
    t0 = time.perf_counter()

    losses = []
    per_source_loss = {}
    per_source_count = {}
    n_nan_skipped = 0
    log_every = max(1, args.n_steps // 100)

    for step in range(args.n_steps):
        opt.zero_grad()
        ids, labels, sources = get_batch()
        out = model(ids, labels=labels)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device).float().to(out.loss.dtype)
        if torch.isnan(out.loss) or torch.isinf(out.loss):
            n_nan_skipped += 1
            opt.zero_grad()
            sched.step()
            losses.append(float("nan"))
            for src in sources:
                per_source_count[src] = per_source_count.get(src, 0) + 1
            continue
        loss_total = out.loss + args.aux_loss_weight * aux
        loss_total.backward()
        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], args.grad_clip
        )
        opt.step()
        sched.step()
        lv = float(out.loss.detach())
        losses.append(lv)
        for src in sources:
            per_source_loss[src] = per_source_loss.get(src, 0.0) + lv
            per_source_count[src] = per_source_count.get(src, 0) + 1
        if (step + 1) % log_every == 0 or step == 0:
            current_lr = opt.param_groups[1]["lr"]  # expert group LR
            print(f"  step {step+1:4d}/{args.n_steps}  lm={lv:.4f}  aux={float(aux.detach()):.4f}  lr_exp={current_lr:.2e}  nan_skipped={n_nan_skipped}")

        # Checkpoint
        if (step + 1) % args.checkpoint_every == 0:
            ckpt_path = Path(args.checkpoint_dir) / f"step-{step+1}.pt"
            ckpt = {fqn: w.state_dict() for fqn, w in moe_wrappers.items()}
            torch.save(ckpt, ckpt_path)
            print(f"  [ckpt] {ckpt_path}")

    ev_e.record()
    torch.cuda.synchronize()
    gpu_ms = ev_s.elapsed_time(ev_e)
    wall = time.perf_counter() - t0

    # Final
    ckpt_final = Path(args.checkpoint_dir) / "final.pt"
    ckpt = {fqn: w.state_dict() for fqn, w in moe_wrappers.items()}
    torch.save(ckpt, ckpt_final)
    print(f"\n[ckpt] final: {ckpt_final}")

    per_source_avg = {src: per_source_loss[src] / max(1, per_source_count.get(src, 1)) for src in per_source_loss}
    tokens_total = args.batch_size * args.seq_len * args.n_steps
    flops_total = 6.0 * trainable * tokens_total
    tflops = flops_total / 1e12 / wall
    peak = 419.0 if args.precision == "mxfp8" else 104.8
    util = tflops / peak * 100
    vram = torch.cuda.max_memory_allocated() / 1e9
    valid_losses = [l for l in losses if not (l != l)]  # filter NaN

    print(f"\n[result] wall={wall:.0f}s = {wall/60:.1f}min  gpu_ms={gpu_ms:.0f}")
    print(f"[result] tokens={tokens_total} TFLOPS={tflops:.2f} util={util:.2f}%")
    print(f"[result] VRAM peak={vram:.2f} GB")
    print(f"[result] NaN skipped: {n_nan_skipped}/{args.n_steps} = {100*n_nan_skipped/args.n_steps:.1f}%")
    if valid_losses:
        print(f"[result] loss[0]={valid_losses[0]:.4f}  loss[-1]={valid_losses[-1]:.4f}  min={min(valid_losses):.4f}")
    print(f"[result] per-source avg loss:")
    for src, avg in sorted(per_source_avg.items()):
        print(f"  {src:22} {avg:.4f}")

    entry = {
        "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
        "adr": "ADR-2605263100",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "phase": f"r14-full-{args.precision}",
        "vendor": "runpod-secure",
        "gpu_model": "nvidia-rtx-5090",
        "precision": args.precision,
        "model": f"{args.model} + moemoekyun MoE residual ({n_moe} layers, {args.n_experts} experts)",
        "corpus_examples": len(pairs),
        "corpus_sha256": "037076af5aa4d873cd9743be4e89648a5a2c0bbac2b9d3641d4233ca00f6becf",
        "n_experts": args.n_experts,
        "top_k": args.top_k,
        "expert_hidden_ratio": args.expert_hidden_ratio,
        "layers_fraction": args.layers_fraction,
        "n_moe_layers": n_moe,
        "trainable_params_count": trainable,
        "total_params_count": total,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "seq_len": args.seq_len,
        "tokens_per_step": args.batch_size * args.seq_len,
        "lr_router": args.lr_router,
        "lr_experts": args.lr_experts,
        "lr_alpha": args.lr_alpha,
        "aux_loss_weight": args.aux_loss_weight,
        "warmup_steps": args.warmup_steps,
        "grad_clip": args.grad_clip,
        "n_nan_skipped": n_nan_skipped,
        "nan_skip_pct": round(100 * n_nan_skipped / args.n_steps, 2),
        "wall_sec": round(wall, 3),
        "loss_first": round(valid_losses[0], 4) if valid_losses else None,
        "loss_last": round(valid_losses[-1], 4) if valid_losses else None,
        "loss_min": round(min(valid_losses), 4) if valid_losses else None,
        "per_source_avg_loss": {k: round(v, 4) for k, v in per_source_avg.items()},
        "tflops_measured": round(tflops, 3),
        "tflops_utilization_pct": round(util, 2),
        "vram_peak_gb": round(vram, 2),
        "checkpoint_final": str(ckpt_final),
        "scoring_note": f"R1.4 FULL spec: {args.n_experts}x{n_moe} experts. Cycle 28+ scale-up from cycle 26 smoke.",
        "founder_did": "did:web:jun.etzhayyim.com",
        "council_post_ratification_target": "2026-06-19+",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n[done] appended to {args.output}")


if __name__ == "__main__":
    main()
