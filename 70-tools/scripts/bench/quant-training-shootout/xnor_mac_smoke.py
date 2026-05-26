"""Self-contained Mac MPS smoke for the XNOR-popcount max-TOPS stack.

No external deps beyond torch + transformers + huggingface_hub. Uses
synthetic prompts so no `datasets` / `peft` / `trl` / `baien_distill`
needed. Designed to complete in ~5-10 min on Apple Silicon (M-class GPU
via PyTorch MPS backend).

Run:
  python xnor_mac_smoke.py --model HuggingFaceTB/SmolLM2-135M-Instruct --steps 2

Drops into the same 5-row matrix as the EVO progressive shootout:
  R0 baseline-bf16
  R1 W-bin
  R2 W+X-bin (XNOR matmul)
  R3 +approx-norm +approx-softmax
  R4 max-TOPS (+binary-grad + SignSGD)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
import torch.nn as nn
import torch.nn.functional as F


# -------- STE + binary primitives ----------------------------------------

class SignSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward((x.abs() <= 1.0).to(x.dtype))
        return torch.sign(x)
    @staticmethod
    def backward(ctx, g):
        (mask,) = ctx.saved_tensors
        return g * mask


class ActSignSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward((x.abs() <= 1.0).to(x.dtype))
        return torch.sign(x)
    @staticmethod
    def backward(ctx, g):
        (mask,) = ctx.saved_tensors
        return g * mask


class BinaryGradWrap(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        return x
    @staticmethod
    def backward(ctx, g):
        return torch.sign(g) * g.abs().mean()


class XNORLinear(nn.Module):
    def __init__(self, in_f, out_f, bias=True, binary_act=True, binary_grad=False):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(out_f, in_f, dtype=torch.float32))
        nn.init.kaiming_normal_(self.weight)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_f, dtype=torch.float32))
        else:
            self.register_parameter("bias", None)
        self.binary_act = binary_act
        self.binary_grad = binary_grad

    def forward(self, x):
        w = self.weight
        if w.dtype != x.dtype:
            w = w.to(x.dtype)
        alpha = w.abs().mean()
        w_bin = SignSTE.apply(w) * alpha
        bias = self.bias.to(x.dtype) if self.bias is not None else None
        if self.binary_act:
            beta = x.abs().mean(dim=-1, keepdim=True)
            x_b = ActSignSTE.apply(x)
            y = F.linear(x_b * beta, w_bin, bias)
        else:
            y = F.linear(x, w_bin, bias)
        if self.binary_grad:
            y = BinaryGradWrap.apply(y)
        return y


class ApproxRMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6, weight=None):
        super().__init__()
        if weight is None:
            weight = torch.ones(dim)
        self.weight = nn.Parameter(weight.clone())
        self.eps = eps
    def forward(self, x):
        scale = x.abs().mean(dim=-1, keepdim=True).clamp_min(self.eps)
        return (self.weight * (x / scale)).to(x.dtype)


def replace_qkvo(model, binary_act, binary_grad):
    n = 0
    for name, child in list(model.named_children()):
        if isinstance(child, nn.Linear) and name in ("q_proj","k_proj","v_proj","o_proj"):
            new = XNORLinear(child.in_features, child.out_features,
                             bias=child.bias is not None,
                             binary_act=binary_act, binary_grad=binary_grad)
            with torch.no_grad():
                new.weight.data.copy_(child.weight.data.float())
                if child.bias is not None:
                    new.bias.data.copy_(child.bias.data.float())
            setattr(model, name, new)
            n += 1
        else:
            n += replace_qkvo(child, binary_act, binary_grad)
    return n


def replace_rmsnorm(model):
    n = 0
    for name, child in list(model.named_children()):
        if "RMSNorm" in type(child).__name__:
            dim = child.weight.shape[0]
            new = ApproxRMSNorm(dim, eps=getattr(child, "variance_epsilon", 1e-6),
                                weight=child.weight.data)
            setattr(model, name, new)
            n += 1
        else:
            n += replace_rmsnorm(child)
    return n


_REAL_SOFTMAX = F.softmax
def _approx_softmax(x, dim=-1, dtype=None):
    s = x - x.amax(dim=dim, keepdim=True)
    e = torch.pow(2.0, s * 1.4426950408889634)
    out = e / e.sum(dim=dim, keepdim=True)
    if dtype is not None:
        out = out.to(dtype)
    return out
def patch_softmax():
    F.softmax = _approx_softmax
    torch.softmax = _approx_softmax
def unpatch_softmax():
    F.softmax = _REAL_SOFTMAX
    torch.softmax = _REAL_SOFTMAX


class SignSGD(torch.optim.Optimizer):
    def __init__(self, params, lr=1e-4):
        super().__init__(params, dict(lr=lr))
    @torch.no_grad()
    def step(self, closure=None):
        for g in self.param_groups:
            for p in g["params"]:
                if p.grad is None: continue
                p.add_(p.grad.sign(), alpha=-g["lr"])


def synthetic_prompts(n: int) -> list[str]:
    """8 tiny prompts that always tokenize without truncation."""
    pool = [
        "What is the capital of Japan? The capital is Tokyo.",
        "2 + 2 equals 4. Five times five is 25.",
        "Water freezes at 0 degrees Celsius and boils at 100.",
        "The sun rises in the east and sets in the west.",
        "Python is a programming language designed by Guido van Rossum.",
        "Photosynthesis converts sunlight into chemical energy in plants.",
        "Mount Everest is the tallest mountain on Earth above sea level.",
        "The mitochondria is the powerhouse of the cell in biology.",
    ]
    out = []
    for i in range(n):
        out.append(pool[i % len(pool)])
    return out


def run_row(label: str, tricks: set[str], opt_name: str, model_id: str,
            n_rows: int, n_steps: int, grad_accum: int, max_len: int,
            device: torch.device) -> dict:
    print(f"\n[{label}] tricks={sorted(tricks)} opt={opt_name} device={device}",
          flush=True)

    if "SOFTMAX" in tricks:
        patch_softmax()

    from transformers import AutoModelForCausalLM, AutoTokenizer
    t_load = time.time()
    tok = AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id, dtype=torch.float32, attn_implementation="eager"
    )
    model = model.to(device)
    t_load = time.time() - t_load
    print(f"[{label}] loaded {model_id} in {t_load:.1f}s", flush=True)

    n_xnor = n_norm = 0
    if "WX" in tricks:
        n_xnor = replace_qkvo(model, binary_act="WX_act" in tricks,
                             binary_grad="GRAD" in tricks)
        model = model.to(device)
        print(f"[{label}] replaced {n_xnor} q/k/v/o -> XNORLinear", flush=True)
    if "NORM" in tricks:
        n_norm = replace_rmsnorm(model)
        model = model.to(device)
        print(f"[{label}] replaced {n_norm} RMSNorm -> ApproxRMSNorm", flush=True)

    # Freeze all, then unfreeze trainable
    n_trainable = 0
    for p in model.parameters():
        p.requires_grad = False
    if "WX" in tricks:
        for mod in model.modules():
            if isinstance(mod, XNORLinear):
                mod.weight.requires_grad = True
                n_trainable += mod.weight.numel()
                if mod.bias is not None:
                    mod.bias.requires_grad = True
                    n_trainable += mod.bias.numel()
    else:
        # baseline: unfreeze q/k/v/o linears
        for name, mod in model.named_modules():
            short = name.rsplit(".", 1)[-1]
            if isinstance(mod, nn.Linear) and short in ("q_proj","k_proj","v_proj","o_proj"):
                mod.weight.requires_grad = True
                n_trainable += mod.weight.numel()
                if mod.bias is not None:
                    mod.bias.requires_grad = True
                    n_trainable += mod.bias.numel()

    n_total = sum(p.numel() for p in model.parameters())
    print(f"[{label}] trainable={n_trainable:,} / total={n_total:,} "
          f"({100*n_trainable/n_total:.3f}%)", flush=True)

    # Tokenize synthetic prompts
    prompts = synthetic_prompts(n_rows)
    sequences = []
    for p in prompts:
        enc = tok(p, return_tensors="pt", truncation=True, max_length=max_len)
        sequences.append(enc["input_ids"].to(device))

    # Optimizer
    trainable = [p for p in model.parameters() if p.requires_grad]
    if opt_name == "signsgd":
        opt = SignSGD(trainable, lr=1e-4)
    elif opt_name == "sgd":
        opt = torch.optim.SGD(trainable, lr=1e-3, momentum=0.9)
    else:
        opt = torch.optim.AdamW(trainable, lr=2e-4)
    print(f"[{label}] optimizer = {type(opt).__name__}", flush=True)

    # Manual SFT loop
    model.train()
    losses, step_times, token_counts = [], [], []
    seq_iter = iter(sequences * 100)
    for step in range(n_steps):
        t0 = time.time()
        opt.zero_grad(set_to_none=True)
        accum_loss = 0.0
        n_tok = 0
        for _ in range(grad_accum):
            try:
                ids = next(seq_iter)
            except StopIteration:
                seq_iter = iter(sequences * 100)
                ids = next(seq_iter)
            out = model(input_ids=ids, labels=ids)
            (out.loss / grad_accum).backward()
            accum_loss += float(out.loss.item()) / grad_accum
            n_tok += int(ids.numel())
        opt.step()
        dt = time.time() - t0
        step_times.append(dt)
        losses.append(accum_loss)
        token_counts.append(n_tok)
        print(f"  [{label}] step {step+1}/{n_steps}: loss={accum_loss:.4f} time={dt:.2f}s tok={n_tok}",
              flush=True)

    if "SOFTMAX" in tricks:
        unpatch_softmax()

    cold = step_times[0] if step_times else None
    warm = (sum(step_times[1:]) / max(1, len(step_times) - 1)
            if len(step_times) >= 2 else cold)
    avg_tok = sum(token_counts) / max(1, len(token_counts))
    sustained_tflops = (6 * n_total * avg_tok / (warm * 1e12)
                        if warm and warm > 0 else None)

    return {
        "label": label, "tricks": sorted(tricks), "opt": opt_name,
        "n_xnor": n_xnor, "n_norm": n_norm,
        "n_trainable": n_trainable, "n_total": n_total,
        "tokens_per_step_avg": avg_tok,
        "step_cold_sec": round(cold, 3) if cold else None,
        "step_warm_sec": round(warm, 3) if warm else None,
        "sustained_tflops_est": round(sustained_tflops, 3) if sustained_tflops else None,
        "losses": [round(l, 4) for l in losses],
        "final_loss": round(losses[-1], 4) if losses else None,
        "load_sec": round(t_load, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM2-135M-Instruct")
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--out", type=Path,
                    default=Path("./xnor-mac-smoke-out"))
    ap.add_argument("--device", default="auto", choices=["auto","mps","cpu","cuda"])
    args = ap.parse_args()

    if args.device == "auto":
        if torch.backends.mps.is_available():
            dev = torch.device("mps")
        elif torch.cuda.is_available():
            dev = torch.device("cuda")
        else:
            dev = torch.device("cpu")
    else:
        dev = torch.device(args.device)

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"[xnor-mac] model={args.model} device={dev} rows={args.rows} "
          f"steps={args.steps} grad_accum={args.grad_accum} max_len={args.max_len}",
          flush=True)

    ROWS = [
        ("R0-baseline-fp32",          set(),                                       "adamw"),
        ("R1-W-bin",                  {"WX"},                                      "adamw"),
        ("R2-W+X-bin-XNOR",           {"WX","WX_act"},                             "adamw"),
        ("R3-+norm+softmax",          {"WX","WX_act","NORM","SOFTMAX"},            "adamw"),
        ("R4-max-TOPS-signsgd",       {"WX","WX_act","GRAD","NORM","SOFTMAX","OPT"}, "signsgd"),
    ]

    results = []
    for label, tricks, opt in ROWS:
        try:
            row = run_row(label, tricks, opt, args.model, args.rows,
                          args.steps, args.grad_accum, args.max_len, dev)
            row["status"] = "ok"
        except Exception as e:
            import traceback
            row = {"label": label, "status": "error",
                   "error_type": type(e).__name__, "error_msg": str(e),
                   "tb": traceback.format_exc()[-800:]}
        (args.out / f"{label}.json").write_text(
            json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        results.append(row)

    summary_path = args.out / "xnor_mac_results.json"
    summary_path.write_text(json.dumps({
        "model": args.model, "device": str(dev),
        "rows": args.rows, "steps": args.steps,
        "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[xnor-mac] wrote {summary_path}", flush=True)

    print("\n## XNOR max-TOPS smoke summary (Mac)")
    print()
    print("| row | trainable | step_warm_s | sustained TFLOPS | final_loss | losses |")
    print("|---|---|---|---|---|---|")
    for r in results:
        if r.get("status") == "ok":
            losses = ",".join(f"{l:.2f}" for l in r.get("losses", []))
            print(f"| {r['label']:30} | {r['n_trainable']:>9,} | "
                  f"{r.get('step_warm_sec','—'):>5} | "
                  f"{r.get('sustained_tflops_est','—'):>5} | "
                  f"{r.get('final_loss','—'):>5} | {losses} |")
        else:
            err = r.get("error_type", r.get("status","?"))
            print(f"| {r['label']:30} | ERROR ({err}) | — | — | — | — |")


if __name__ == "__main__":
    main()
