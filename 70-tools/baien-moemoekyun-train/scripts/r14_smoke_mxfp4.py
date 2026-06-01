#!/usr/bin/env python3
"""r14_smoke_mxfp4.py — R1.4 smoke MXFP4 train + TFLOPS measurement.

Validates the cycle 17 trainer.py precision="mxfp4" path end-to-end:
  1. Load BitNet 2B-4T-bf16 (or fall back to GPT-2 124M if VRAM tight)
  2. Attach BaienMoEResidual to last 25% of layers (G2 placement)
  3. apply_mxfp4_quantize on router + experts (cycle 17 cmd)
  4. Build optimizer with per-group LR (existing trainer.py)
  5. Run N forward+backward steps on tiny synthetic data
  6. Measure TFLOPS via torch.cuda.Event + flops-counter

Per ADR-2605263100 §6 runlog schema. Output appended to:
  90-docs/baien/runpod-5090-runlog-260526.jsonl

Run on RunPod RTX 5090:
  python3 r14_smoke_mxfp4.py --n-steps 10 --batch-size 1 --seq-len 256
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure baien_moemoekyun importable
SCRIPT_DIR = Path(__file__).parent
PKG_SRC = SCRIPT_DIR.parent / "src"
sys.path.insert(0, str(PKG_SRC))

import torch
import torch.nn as nn


def synth_batch(vocab_size: int, batch_size: int, seq_len: int, device: torch.device):
    """Synthetic input_ids batch (uniform-random) for smoke testing forward+backward."""
    ids = torch.randint(0, vocab_size, (batch_size, seq_len), device=device)
    return {"input_ids": ids, "labels": ids.clone()}


def count_trainable_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def estimate_tflops(
    trainable_params: int,
    batch_size: int,
    seq_len: int,
    n_steps: int,
    wall_sec: float,
) -> tuple[float, float]:
    """Rough estimate of train TFLOPS.

    Per-step FLOPs ≈ 6 × trainable_params × tokens (for transformer train forward+backward).
    Returns (total_flops, tflops_sustained).
    """
    tokens_total = batch_size * seq_len * n_steps
    flops_total = 6.0 * trainable_params * tokens_total
    tflops = flops_total / 1e12 / wall_sec
    return flops_total, tflops


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16",
                        help="HF model id (or 'gpt2' for VRAM-tight smoke)")
    parser.add_argument("--n-steps", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--seq-len", type=int, default=256)
    parser.add_argument("--precision", default="mxfp4", choices=["bf16", "mxfp4", "mxfp8"])
    parser.add_argument("--n-experts", type=int, default=128)
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--layers-fraction", type=float, default=0.25,
                        help="Apply MoE residual to last fraction of layers (default 0.25)")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--runlog",
                        default=str(Path(__file__).parent.parent.parent.parent /
                                    "90-docs/baien/runpod-5090-runlog-260526.jsonl"))
    parser.add_argument("--council-target", default="2026-06-19+")
    args = parser.parse_args()

    print(f"[env] torch={torch.__version__} cuda={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[env] device={torch.cuda.get_device_name(0)}")
        print(f"[env] vram_total={torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    # Check torchao + MXFP4 availability before any heavy load
    if args.precision in ("mxfp4", "mxfp8"):
        try:
            import torchao
            from torchao.prototype.mx_formats import MXDynamicActivationMXWeightConfig
            from torchao.prototype.mx_formats.config import SUPPORTED_ELEM_DTYPES
            print(f"[env] torchao={torchao.__version__}")
            print(f"[env] supported MX dtypes: {SUPPORTED_ELEM_DTYPES}")
            if args.precision == "mxfp4" and not hasattr(torch, "float4_e2m1fn_x2"):
                print("[warn] torch.float4_e2m1fn_x2 unavailable — falling back to mxfp8")
                args.precision = "mxfp8"
        except ImportError as e:
            print(f"[err] torchao MXFP4 unavailable: {e}")
            sys.exit(2)

    # Load model
    print(f"\n[load] {args.model}")
    t0 = time.perf_counter()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, trust_remote_code=False
    )
    model.to(device).train()
    vocab_size = model.config.vocab_size
    print(f"[load] {time.perf_counter() - t0:.1f}s, vocab={vocab_size}")

    # Attach MoE residual to last `layers_fraction` of layers
    from baien_moemoekyun.attach import (
        attach_moe_to_model,
        freeze_backbone_verify,
    )
    cfg = model.config
    hidden_size = getattr(cfg, "hidden_size", None) or getattr(cfg, "n_embd", None)
    intermediate_size = getattr(cfg, "intermediate_size", None) or getattr(cfg, "n_inner", None)
    if intermediate_size is None and hidden_size is not None:
        intermediate_size = 4 * hidden_size  # GPT-2 default
    n_layers = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer", None)
    if not all([hidden_size, intermediate_size, n_layers]):
        raise RuntimeError(f"Cannot resolve hidden/intermediate/n_layers from config: {cfg}")
    # Detect ffn attribute name based on model family
    ffn_attr_name = "mlp"  # default for GPT-2, BitNet, LLaMA-style
    # last `layers_fraction` indices
    n_moe_layers = max(1, int(round(n_layers * args.layers_fraction)))
    moe_layer_indices = list(range(n_layers - n_moe_layers, n_layers))
    print(f"\n[moe] hidden={hidden_size} intermediate={intermediate_size} n_layers={n_layers}")
    print(f"[moe] attaching residual to layers {moe_layer_indices[0]}..{moe_layer_indices[-1]} ({n_moe_layers}/{n_layers})")
    moe_wrappers = attach_moe_to_model(
        model,
        moe_layer_indices=moe_layer_indices,
        hidden_size=hidden_size,
        intermediate_size=intermediate_size,
        num_experts=args.n_experts,
        top_k=args.top_k,
        ffn_attribute_name=ffn_attr_name,
    )
    print(f"[moe] attached {len(moe_wrappers)} wrappers")

    # G8: freeze backbone, only MoE branch + alpha trainable
    freeze_backbone_verify(model, moe_wrappers)
    trainable = count_trainable_params(model)
    total = sum(p.numel() for p in model.parameters())
    print(f"[moe] trainable={trainable/1e6:.1f}M / total={total/1e6:.1f}M ({100*trainable/total:.1f}%)")

    # Apply MXFP4 quantize via cycle 17 trainer.apply_mxfp4_quantize
    if args.precision in ("mxfp4", "mxfp8"):
        from baien_moemoekyun.trainer import apply_mxfp4_quantize
        weight_dt = torch.float4_e2m1fn_x2 if args.precision == "mxfp4" else torch.float8_e4m3fn
        act_dt = torch.float8_e4m3fn
        print(f"\n[quant] precision={args.precision} weight={weight_dt} activation={act_dt}")
        quantized = apply_mxfp4_quantize(
            model, moe_wrappers, block_size=32,
            weight_dtype=weight_dt, activation_dtype=act_dt,
        )
        print(f"[quant] quantized {len(quantized)} modules")

    # Build optimizer
    from baien_moemoekyun.trainer import build_optimizer
    opt = build_optimizer(moe_wrappers, lr_router=1e-4, lr_experts=2e-4, lr_alpha=5e-5)

    # Warmup (compile / kernel cache)
    print(f"\n[warmup] 2 steps...")
    for _ in range(2):
        opt.zero_grad()
        batch = synth_batch(vocab_size, args.batch_size, args.seq_len, device)
        out = model(**batch)
        loss = out.loss if hasattr(out, "loss") else out[0]
        loss.backward()
        opt.step()
    torch.cuda.synchronize() if device.type == "cuda" else None

    # Measured train loop
    print(f"\n[train] {args.n_steps} steps bs={args.batch_size} seqlen={args.seq_len}")
    if device.type == "cuda":
        start_ev = torch.cuda.Event(enable_timing=True)
        end_ev = torch.cuda.Event(enable_timing=True)
        start_ev.record()
    t_start = time.perf_counter()
    losses = []
    for step in range(args.n_steps):
        opt.zero_grad()
        batch = synth_batch(vocab_size, args.batch_size, args.seq_len, device)
        out = model(**batch)
        loss = out.loss if hasattr(out, "loss") else out[0]
        # Add aux loss (G6 MANDATORY) — collect from MoE wrappers
        from baien_moemoekyun.attach import collect_aux_losses
        aux = collect_aux_losses(moe_wrappers)
        if aux.device != loss.device:
            aux = aux.to(loss.device)
        total_loss = loss + 0.01 * aux
        total_loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
        print(f"  step {step+1}/{args.n_steps}  lm_loss={float(loss.detach()):.4f}  aux={float(aux.detach()):.4f}")
    if device.type == "cuda":
        end_ev.record()
        torch.cuda.synchronize()
        gpu_wall_ms = start_ev.elapsed_time(end_ev)
    else:
        gpu_wall_ms = None
    wall_sec = time.perf_counter() - t_start
    print(f"[train] wall={wall_sec:.2f}s  gpu_wall_ms={gpu_wall_ms}")

    # TFLOPS measurement
    flops_total, tflops = estimate_tflops(
        trainable, args.batch_size, args.seq_len, args.n_steps, wall_sec
    )
    print(f"\n[tflops] trainable={trainable/1e6:.1f}M params")
    print(f"[tflops] tokens={args.batch_size*args.seq_len*args.n_steps} total_flops={flops_total/1e12:.2f}T")
    print(f"[tflops] sustained={tflops:.2f} TFLOPS")
    if device.type == "cuda":
        # Theoretical peak for 5090
        theoretical_peak = {
            "mxfp4": 1318.0,   # 2:4 sparse FP4 (Blackwell native)
            "mxfp8": 419.0,    # H100/Blackwell FP8
            "bf16":  104.8,    # 5090 bf16 dense
        }.get(args.precision, 0.0)
        util_pct = tflops / theoretical_peak * 100 if theoretical_peak else 0.0
        print(f"[tflops] theoretical_peak_{args.precision}={theoretical_peak} TFLOPS  utilization={util_pct:.2f}%")
    else:
        theoretical_peak = 0.0
        util_pct = 0.0

    # VRAM peak
    if device.type == "cuda":
        vram_peak_gb = torch.cuda.max_memory_allocated() / 1e9
        print(f"[vram] peak={vram_peak_gb:.2f} GB")
    else:
        vram_peak_gb = 0.0

    # Append runlog entry per ADR-2605263100 §6
    entry = {
        "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
        "adr": "ADR-2605263100",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "phase": f"train-r1.4-{args.precision}",
        "vendor": "runpod-secure",
        "gpu_model": "nvidia-rtx-5090",
        "gpu_count": 1,
        "pod_endpoint": "ssh://root@157.157.221.30:51691",
        "precision": args.precision,
        "te_version": None,
        "torchao_version": __import__("torchao").__version__ if args.precision in ("mxfp4", "mxfp8") else None,
        "model": f"{args.model} + moemoekyun MoE residual",
        "n_experts": args.n_experts,
        "top_k": args.top_k,
        "layers_fraction": args.layers_fraction,
        "n_layers_with_moe": len(moe_wrappers),
        "trainable_params_count": trainable,
        "frozen_params_count": total - trainable,
        "train_dataset_cids": ["synthetic-random-tokens (SMOKE, NOT real corpus)"],
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
        "seq_len": args.seq_len,
        "tokens_per_step": args.batch_size * args.seq_len,
        "wall_sec": round(wall_sec, 3),
        "gpu_wall_ms": gpu_wall_ms,
        "loss_curve": [round(l, 4) for l in losses],
        "tflops_measured": round(tflops, 3),
        "tflops_theoretical_peak": theoretical_peak,
        "tflops_utilization_pct": round(util_pct, 2),
        "vram_peak_gb": round(vram_peak_gb, 2),
        "founder_did": "did:web:jun.etzhayyim.com",
        "council_post_ratification_target": args.council_target,
        "scoring_note": "synthetic-tokens smoke — establishes pipeline + TFLOPS baseline; R1.4 full run requires real corpus assembly",
    }
    Path(args.runlog).parent.mkdir(parents=True, exist_ok=True)
    with open(args.runlog, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n[done] appended to {args.runlog}")
    print(f"[done] {tflops:.2f} TFLOPS sustained at {util_pct:.1f}% of theoretical peak ({args.precision})")


if __name__ == "__main__":
    main()
