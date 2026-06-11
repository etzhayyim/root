#!/usr/bin/env python3
"""Standalone MXFP4 smoke for RTX 5090 — proves cycle 17 trainer.apply_mxfp4_quantize() works on real Blackwell HW + measures TFLOPS.

Avoids loading BitNet 2B (would OOM with MMLU+train_oka sharing GPU).

Pattern: build a TINY 4-layer transformer-like model with MoE residual on last layer,
apply MXFP4 quantize via cycle 17 function, train 10 steps on synthetic data,
measure sustained TFLOPS via torch.cuda.Event + 6×params×tokens formula.

Run on pod (after scp):
    cd /workspace
    python3 standalone_mxfp4_smoke.py --hidden 1024 --n-experts 32 --n-steps 10 --batch-size 4 --seq-len 256
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn as nn


class TinyAttention(nn.Module):
    def __init__(self, hidden: int, n_heads: int = 8):
        super().__init__()
        self.qkv = nn.Linear(hidden, 3 * hidden, bias=False)
        self.out = nn.Linear(hidden, hidden, bias=False)
        self.n_heads = n_heads
        self.head_dim = hidden // n_heads
    def forward(self, x):
        B, T, H = x.shape
        qkv = self.qkv(x).view(B, T, 3, self.n_heads, self.head_dim).transpose(1, 3)
        q, k, v = qkv.unbind(dim=2)
        # Simple scaled-dot attention
        attn = (q @ k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn = torch.softmax(attn, dim=-1)
        out = (attn @ v).transpose(1, 2).contiguous().view(B, T, H)
        return self.out(out)


class TinyFFN(nn.Module):
    def __init__(self, hidden: int, intermediate: int):
        super().__init__()
        self.gate_proj = nn.Linear(hidden, intermediate, bias=False)
        self.up_proj = nn.Linear(hidden, intermediate, bias=False)
        self.down_proj = nn.Linear(intermediate, hidden, bias=False)
    def forward(self, x):
        return self.down_proj(nn.functional.silu(self.gate_proj(x)) * self.up_proj(x))


class TinyBlock(nn.Module):
    def __init__(self, hidden: int, intermediate: int, n_heads: int = 8):
        super().__init__()
        self.ln1 = nn.LayerNorm(hidden)
        self.attn = TinyAttention(hidden, n_heads)
        self.ln2 = nn.LayerNorm(hidden)
        self.mlp = TinyFFN(hidden, intermediate)
    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class TinyTransformer(nn.Module):
    def __init__(self, vocab: int, hidden: int, intermediate: int, n_layers: int, n_heads: int = 8):
        super().__init__()
        self.embed = nn.Embedding(vocab, hidden)
        self.layers = nn.ModuleList([TinyBlock(hidden, intermediate, n_heads) for _ in range(n_layers)])
        self.ln_f = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, vocab, bias=False)
        self.vocab = vocab
    def forward(self, input_ids, labels=None):
        x = self.embed(input_ids)
        for layer in self.layers:
            x = layer(x)
        x = self.ln_f(x)
        logits = self.head(x)
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits.view(-1, self.vocab), labels.view(-1))

        class Out: pass
        o = Out()
        o.loss = loss
        o.logits = logits
        return o


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hidden", type=int, default=1024)
    p.add_argument("--intermediate", type=int, default=4096)
    p.add_argument("--n-layers", type=int, default=4)
    p.add_argument("--n-heads", type=int, default=8)
    p.add_argument("--vocab", type=int, default=32000)
    p.add_argument("--n-experts", type=int, default=32)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=32)
    p.add_argument("--n-steps", type=int, default=10)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--seq-len", type=int, default=256)
    p.add_argument("--precision", default="mxfp4", choices=["bf16", "mxfp4", "mxfp8"])
    p.add_argument("--device", default="cuda")
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--output", default="/workspace/standalone-mxfp4-smoke-result.jsonl")
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.moe import BaienMoEResidual
    from baien_moemoekyun.attach import BitNetFFNWithMoE, collect_aux_losses
    from baien_moemoekyun.trainer import apply_mxfp4_quantize, build_optimizer

    print(f"[env] torch={torch.__version__} cuda={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[env] device={torch.cuda.get_device_name(0)}")
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    if args.precision in ("mxfp4", "mxfp8"):
        import torchao
        from torchao.prototype.mx_formats.config import SUPPORTED_ELEM_DTYPES
        print(f"[env] torchao={torchao.__version__}")
        print(f"[env] supported MX dtypes: {SUPPORTED_ELEM_DTYPES}")
        if args.precision == "mxfp4" and not hasattr(torch, "float4_e2m1fn_x2"):
            print("[warn] no torch.float4_e2m1fn_x2; falling back to mxfp8")
            args.precision = "mxfp8"

    # Build tiny model
    print(f"\n[build] TinyTransformer h={args.hidden} i={args.intermediate} L={args.n_layers}")
    model = TinyTransformer(args.vocab, args.hidden, args.intermediate, args.n_layers, args.n_heads)
    model.to(device, dtype=torch.bfloat16).train()
    print(f"[build] total params={sum(p.numel() for p in model.parameters())/1e6:.2f}M")

    # Attach MoE to last layer only
    last_layer = model.layers[-1]
    backbone_ffn = last_layer.mlp
    moe_branch = BaienMoEResidual(
        hidden_size=args.hidden,
        num_experts=args.n_experts,
        top_k=args.top_k,
        intermediate_size=args.intermediate,
        expert_hidden_ratio=args.expert_hidden_ratio,
    ).to(device, dtype=torch.bfloat16)
    import inspect
    bw_sig = inspect.signature(BitNetFFNWithMoE.__init__)
    bw_kwargs = {}
    if "alpha_init" in bw_sig.parameters:
        bw_kwargs["alpha_init"] = 0.0
    if "alpha_init_jitter" in bw_sig.parameters:
        bw_kwargs["alpha_init_jitter"] = 1e-3
    wrapper = BitNetFFNWithMoE(backbone_ffn, moe_branch, **bw_kwargs).to(device, dtype=torch.bfloat16)
    last_layer.mlp = wrapper
    moe_wrappers = {f"layers.{args.n_layers-1}.mlp": wrapper}
    print(f"[moe] attached to layer {args.n_layers-1}; n_experts={args.n_experts} top_k={args.top_k}")

    # Freeze backbone (all params except MoE branch + α)
    for n, p in model.named_parameters():
        is_trainable = ("moe_branch" in n) or n.endswith(".alpha")
        p.requires_grad = is_trainable
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"[moe] trainable={trainable/1e6:.2f}M / total={total/1e6:.2f}M ({100*trainable/total:.1f}%)")

    # Apply MX quantize (torchao 0.18 requires activation_dtype == weight_dtype)
    if args.precision in ("mxfp4", "mxfp8"):
        wdt = torch.float4_e2m1fn_x2 if args.precision == "mxfp4" else torch.float8_e4m3fn
        adt = wdt  # torchao constraint
        print(f"\n[quant] precision={args.precision} weight={wdt} act={adt}")
        quantized = apply_mxfp4_quantize(
            model, moe_wrappers, block_size=32,
            weight_dtype=wdt, activation_dtype=adt,
        )
        print(f"[quant] quantized {len(quantized)} modules")

    opt = build_optimizer(moe_wrappers, lr_router=1e-4, lr_experts=2e-4, lr_alpha=5e-5)

    # Warmup
    print(f"\n[warmup] 2 steps...")
    for _ in range(2):
        opt.zero_grad()
        ids = torch.randint(0, args.vocab, (args.batch_size, args.seq_len), device=device)
        out = model(ids, labels=ids)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device)
        loss = out.loss + 0.01 * aux
        loss.backward()
        opt.step()
    if device.type == "cuda":
        torch.cuda.synchronize()

    # Measured loop
    print(f"\n[train] {args.n_steps} steps bs={args.batch_size} seq={args.seq_len}")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
        ev_start = torch.cuda.Event(enable_timing=True)
        ev_end = torch.cuda.Event(enable_timing=True)
        ev_start.record()
    t0 = time.perf_counter()
    losses = []
    aux_losses = []
    for step in range(args.n_steps):
        opt.zero_grad()
        ids = torch.randint(0, args.vocab, (args.batch_size, args.seq_len), device=device)
        out = model(ids, labels=ids)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device)
        loss = out.loss + 0.01 * aux
        loss.backward()
        opt.step()
        losses.append(float(out.loss.detach()))
        aux_losses.append(float(aux.detach()))
        print(f"  step {step+1}/{args.n_steps} lm={losses[-1]:.4f} aux={aux_losses[-1]:.4f}")
    if device.type == "cuda":
        ev_end.record()
        torch.cuda.synchronize()
        gpu_ms = ev_start.elapsed_time(ev_end)
    else:
        gpu_ms = None
    wall = time.perf_counter() - t0

    # TFLOPS (forward+backward ≈ 6 × trainable × tokens)
    tokens_total = args.batch_size * args.seq_len * args.n_steps
    flops_total = 6.0 * trainable * tokens_total
    tflops = flops_total / 1e12 / wall
    peak_table = {"mxfp4": 1318.0, "mxfp8": 419.0, "bf16": 104.8}
    peak = peak_table.get(args.precision, 0.0)
    util = tflops / peak * 100 if peak else 0.0

    print(f"\n[result] wall={wall:.3f}s gpu_ms={gpu_ms}")
    print(f"[result] tokens={tokens_total} flops={flops_total/1e12:.3f}T")
    print(f"[result] sustained={tflops:.2f} TFLOPS  peak_{args.precision}={peak}  util={util:.2f}%")
    if device.type == "cuda":
        vram = torch.cuda.max_memory_allocated() / 1e9
        print(f"[result] vram_peak={vram:.2f} GB")
    else:
        vram = 0.0

    entry = {
        "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
        "adr": "ADR-2605263100",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "phase": f"smoke-standalone-{args.precision}",
        "vendor": "runpod-secure",
        "gpu_model": "nvidia-rtx-5090",
        "precision": args.precision,
        "torchao_version": __import__("torchao").__version__ if args.precision in ("mxfp4", "mxfp8") else None,
        "model": f"TinyTransformer (synthetic) h={args.hidden} L={args.n_layers}",
        "n_experts": args.n_experts,
        "top_k": args.top_k,
        "trainable_params_count": trainable,
        "total_params_count": total,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "seq_len": args.seq_len,
        "tokens_per_step": args.batch_size * args.seq_len,
        "wall_sec": round(wall, 3),
        "gpu_wall_ms": gpu_ms,
        "loss_curve_lm": [round(l, 4) for l in losses],
        "loss_curve_aux": [round(l, 4) for l in aux_losses],
        "tflops_measured": round(tflops, 3),
        "tflops_theoretical_peak": peak,
        "tflops_utilization_pct": round(util, 2),
        "vram_peak_gb": round(vram, 2),
        "scoring_note": "STANDALONE smoke — validates cycle 17 apply_mxfp4_quantize on real Blackwell HW (NOT BitNet 2B; that's gated on free 5090 VRAM ≥ 24 GB)",
        "founder_did": "did:web:jun.etzhayyim.com",
        "council_post_ratification_target": "2026-06-19+",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n[done] {tflops:.2f} TFLOPS @ {util:.1f}% of {args.precision} peak — appended to {args.output}")


if __name__ == "__main__":
    main()
