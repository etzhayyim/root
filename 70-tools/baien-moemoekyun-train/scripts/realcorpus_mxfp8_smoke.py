#!/usr/bin/env python3
"""realcorpus_mxfp8_smoke.py — train TinyTransformer with REAL R1.4 corpus on 5090.

Uses real BitNet tokenizer (matches production R1.4 vocab) but TinyTransformer
model (fits in 8 GB free VRAM with MMLU sharing 5090).

Validates: corpus tokenization + MXFP8 quantize gradient flow + per-source loss.
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
    def __init__(self, hidden, n_heads=8):
        super().__init__()
        self.qkv = nn.Linear(hidden, 3 * hidden, bias=False)
        self.out = nn.Linear(hidden, hidden, bias=False)
        self.n_heads = n_heads
        self.head_dim = hidden // n_heads
    def forward(self, x):
        B, T, H = x.shape
        qkv = self.qkv(x).view(B, T, 3, self.n_heads, self.head_dim).transpose(1, 3)
        q, k, v = qkv.unbind(dim=2)
        attn = (q @ k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        mask = torch.triu(torch.ones(T, T, dtype=torch.bool, device=x.device), diagonal=1)
        attn = attn.masked_fill(mask, float('-inf'))
        attn = torch.softmax(attn, dim=-1)
        out = (attn @ v).transpose(1, 2).contiguous().view(B, T, H)
        return self.out(out)


class TinyFFN(nn.Module):
    def __init__(self, hidden, intermediate):
        super().__init__()
        self.gate_proj = nn.Linear(hidden, intermediate, bias=False)
        self.up_proj = nn.Linear(hidden, intermediate, bias=False)
        self.down_proj = nn.Linear(intermediate, hidden, bias=False)
    def forward(self, x):
        return self.down_proj(nn.functional.silu(self.gate_proj(x)) * self.up_proj(x))


class TinyBlock(nn.Module):
    def __init__(self, hidden, intermediate, n_heads=8):
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
    def __init__(self, vocab, hidden, intermediate, n_layers, n_heads=8):
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
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            if (shift_labels != -100).any():
                loss = nn.functional.cross_entropy(
                    shift_logits.view(-1, self.vocab),
                    shift_labels.view(-1),
                    ignore_index=-100,
                )
            else:
                loss = torch.tensor(0.0, device=x.device, requires_grad=True)
        class Out: pass
        o = Out()
        o.loss = loss
        o.logits = logits
        return o


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
    p.add_argument("--corpus", default="/workspace/r14-corpus-shard.jsonl")
    p.add_argument("--tokenizer", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    p.add_argument("--hidden", type=int, default=1024)
    p.add_argument("--intermediate", type=int, default=4096)
    p.add_argument("--n-layers", type=int, default=6)
    p.add_argument("--n-heads", type=int, default=16)
    p.add_argument("--n-experts", type=int, default=64)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--expert-hidden-ratio", type=int, default=16)
    p.add_argument("--n-steps", type=int, default=200)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--seq-len", type=int, default=512)
    p.add_argument("--precision", default="mxfp8")
    p.add_argument("--moemoekyun-src", default="/workspace/baien-moemoekyun-train/src")
    p.add_argument("--output", default="/workspace/realcorpus-smoke-result.jsonl")
    args = p.parse_args()

    sys.path.insert(0, args.moemoekyun_src)
    from baien_moemoekyun.moe import BaienMoEResidual
    from baien_moemoekyun.attach import BitNetFFNWithMoE, collect_aux_losses
    from baien_moemoekyun.trainer import apply_mxfp4_quantize, build_optimizer

    print(f"[env] torch={torch.__version__} cuda={torch.cuda.is_available()}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=False)
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id or 0
    vocab_size = len(tok)
    print(f"[tok] {args.tokenizer} vocab={vocab_size} pad={tok.pad_token_id}")

    pairs = []
    with open(args.corpus) as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))
    print(f"[data] {len(pairs)} pairs")

    print(f"\n[tok] tokenizing (seq_len={args.seq_len})...")
    tokenized = []
    src_counts = {}
    for pair in pairs:
        ids, labels = format_pair(pair, tok, max_len=args.seq_len)
        if len(ids) < args.seq_len:
            pad_n = args.seq_len - len(ids)
            ids = torch.cat([ids, torch.full((pad_n,), tok.pad_token_id, dtype=ids.dtype)])
            labels = torch.cat([labels, torch.full((pad_n,), -100, dtype=labels.dtype)])
        tokenized.append((ids, labels, pair.get("_source", "?")))
        src_counts[pair.get("_source", "?")] = src_counts.get(pair.get("_source", "?"), 0) + 1
    print(f"[tok] per-source: {src_counts}")

    print(f"\n[build] TinyTransformer h={args.hidden} L={args.n_layers} I={args.intermediate}")
    model = TinyTransformer(vocab_size, args.hidden, args.intermediate, args.n_layers, args.n_heads)
    model.to(device, dtype=torch.bfloat16).train()

    last_layer = model.layers[-1]
    backbone_ffn = last_layer.mlp
    moe_branch = BaienMoEResidual(
        hidden_size=args.hidden,
        num_experts=args.n_experts,
        top_k=args.top_k,
        intermediate_size=args.intermediate,
        expert_hidden_ratio=args.expert_hidden_ratio,
    ).to(device, dtype=torch.bfloat16)
    wrapper = BitNetFFNWithMoE(backbone_ffn, moe_branch).to(device, dtype=torch.bfloat16)
    last_layer.mlp = wrapper
    moe_wrappers = {f"layers.{args.n_layers-1}.mlp": wrapper}

    for n, p in model.named_parameters():
        p.requires_grad = ("moe_branch" in n) or n.endswith(".alpha")
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"[moe] trainable={trainable/1e6:.2f}M / total={total/1e6:.2f}M")

    if args.precision == "mxfp8":
        wdt = torch.float8_e4m3fn
        q = apply_mxfp4_quantize(model, moe_wrappers, block_size=32, weight_dtype=wdt, activation_dtype=wdt)
        print(f"[quant] mxfp8: {len(q)} modules")

    opt = build_optimizer(moe_wrappers, lr_router=1e-4, lr_experts=2e-4, lr_alpha=5e-5)

    import random
    rng = random.Random(42)

    def get_batch():
        idxs = rng.sample(range(len(tokenized)), args.batch_size)
        ids = torch.stack([tokenized[i][0] for i in idxs]).to(device)
        labels = torch.stack([tokenized[i][1] for i in idxs]).to(device)
        sources = [tokenized[i][2] for i in idxs]
        return ids, labels, sources

    print(f"\n[warmup] 2")
    for _ in range(2):
        opt.zero_grad()
        ids, labels, _ = get_batch()
        out = model(ids, labels=labels)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device)
        (out.loss + 0.01 * aux).backward()
        opt.step()
    if device.type == "cuda":
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()

    print(f"\n[train] {args.n_steps} steps  bs={args.batch_size} seq={args.seq_len}")
    if device.type == "cuda":
        ev_s = torch.cuda.Event(enable_timing=True); ev_e = torch.cuda.Event(enable_timing=True)
        ev_s.record()
    t0 = time.perf_counter()
    losses = []
    per_source_loss = {}
    per_source_count = {}
    log_every = max(1, args.n_steps // 20)
    for step in range(args.n_steps):
        opt.zero_grad()
        ids, labels, sources = get_batch()
        out = model(ids, labels=labels)
        aux = collect_aux_losses(moe_wrappers).to(out.loss.device)
        (out.loss + 0.01 * aux).backward()
        opt.step()
        lv = float(out.loss.detach())
        losses.append(lv)
        for src in sources:
            per_source_loss[src] = per_source_loss.get(src, 0.0) + lv
            per_source_count[src] = per_source_count.get(src, 0) + 1
        if (step + 1) % log_every == 0 or step == 0:
            print(f"  step {step+1:4d}/{args.n_steps}  lm={lv:.4f}  aux={float(aux.detach()):.4f}")
    if device.type == "cuda":
        ev_e.record(); torch.cuda.synchronize()
        gpu_ms = ev_s.elapsed_time(ev_e)
    else:
        gpu_ms = None
    wall = time.perf_counter() - t0

    per_source_avg = {src: per_source_loss[src] / per_source_count[src] for src in per_source_loss}
    tokens_total = args.batch_size * args.seq_len * args.n_steps
    flops_total = 6.0 * trainable * tokens_total
    tflops = flops_total / 1e12 / wall
    peak = 419.0
    util = tflops / peak * 100
    vram = torch.cuda.max_memory_allocated() / 1e9 if device.type == "cuda" else 0

    print(f"\n[result] wall={wall:.2f}s tokens={tokens_total} {tflops:.2f} TFLOPS @ {util:.1f}%")
    print(f"[result] loss[0]={losses[0]:.4f} loss[-1]={losses[-1]:.4f} Δ={losses[-1]-losses[0]:+.4f}")
    print(f"[result] vram_peak={vram:.2f} GB")
    print(f"[result] per-source avg loss:")
    for src, avg in sorted(per_source_avg.items()):
        print(f"  {src:22} {avg:.4f}  ({per_source_count[src]} batches)")

    entry = {
        "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
        "adr": "ADR-2605263100",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "phase": f"realcorpus-smoke-{args.precision}",
        "vendor": "runpod-secure",
        "gpu_model": "nvidia-rtx-5090",
        "precision": args.precision,
        "model": f"TinyTransformer h={args.hidden} L={args.n_layers}",
        "tokenizer": args.tokenizer,
        "vocab_size": vocab_size,
        "corpus_examples": len(pairs),
        "corpus_sha256": "037076af5aa4d873cd9743be4e89648a5a2c0bbac2b9d3641d4233ca00f6becf",
        "corpus_cid": "bafybeidnsicmjn3j5j2aiarygi33iovvymvputq2hjt2hkebyq7moxw3gu",
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
        "loss_first": round(losses[0], 4),
        "loss_last": round(losses[-1], 4),
        "loss_delta": round(losses[-1] - losses[0], 4),
        "loss_min": round(min(losses), 4),
        "loss_curve_sampled": [round(l, 4) for l in losses[::max(1, len(losses)//30)]],
        "per_source_avg_loss": {k: round(v, 4) for k, v in per_source_avg.items()},
        "per_source_batches": per_source_count,
        "tflops_measured": round(tflops, 3),
        "tflops_theoretical_peak": peak,
        "tflops_utilization_pct": round(util, 2),
        "vram_peak_gb": round(vram, 2),
        "scoring_note": "REAL R1.4 corpus (cycle 20 assembled, 4715 ex, sha256:037076af) on TinyTransformer. Production BitNet 2B + 128×7 experts pending MMLU VRAM release.",
        "founder_did": "did:web:jun.etzhayyim.com",
        "council_post_ratification_target": "2026-06-19+",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\n[done] appended {args.output}")


if __name__ == "__main__":
    main()
