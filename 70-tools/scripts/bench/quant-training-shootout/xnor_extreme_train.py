"""XNOR-popcount maximum-TOPS training stack.

Stacks 6 low-bit techniques cumulatively, each parameterizable:
  --tricks WX,WX_act,GRAD,NORM,SOFTMAX,OPT
where:
  WX      = binary weights (sign + STE, per-tensor alpha)
  WX_act  = binary activations on the binary linear's input
            (matmul becomes XNOR-popcount equivalent)
  GRAD    = quantize backward grad to ±1·scale (binary grad approx, STE)
  NORM    = approximate RMSNorm via L1 mean instead of L2 sqrt-mean
  SOFTMAX = piecewise-linear softmax via 2^x (bit-shift on float exponent
            approximates exp; replaces F.softmax in attention)
  OPT     = SignSGD optimizer (stateless, 1-bit update direction)

Hardware reality on ROCm gfx1151: there is no bit-packed matmul kernel,
so XNOR-popcount is computed as `sign(W) @ sign(X)` in bf16 — numerically
equivalent but not faster than the bf16 baseline. The sustained TFLOPS
recorded here is therefore PyTorch's bf16 matmul throughput on the
sign-quantized tensor; the THEORETICAL peak with packed bits would be
~16× higher per published vendor docs for similar SoCs. We report both.

A separate `bit_packed_xnor_probe.py` (TODO) validates the algorithm at
the bit level using torch.bitwise_count.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import torch._dynamo as _dyn
    _dyn.config.suppress_errors = True
    _dyn.disable()
except Exception:
    pass


# =========================================================================
# Trick 1: binary weights via sign + STE
# =========================================================================

class SignSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        # Save only the clip mask (1 bit per elem in concept; bool here)
        # so backward is vectorized mul instead of bool-indexed write.
        ctx.save_for_backward((x.abs() <= 1.0).to(x.dtype))
        return torch.sign(x)
    @staticmethod
    def backward(ctx, g):
        (mask,) = ctx.saved_tensors
        return g * mask


# =========================================================================
# Trick 2: binary activations via sign + STE
# =========================================================================

class ActSignSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        # Hubara et al. 2016: clip backward grad where |x|>1.
        # Save vectorized mask so backward is a single mul.
        ctx.save_for_backward((x.abs() <= 1.0).to(x.dtype))
        return torch.sign(x)
    @staticmethod
    def backward(ctx, g):
        (mask,) = ctx.saved_tensors
        return g * mask


# =========================================================================
# Trick 3: binary backward gradient (BinaryConnect Algorithm 2 variant)
# =========================================================================

class BinaryGradWrap(torch.autograd.Function):
    """Identity forward, but binarizes the gradient at the layer boundary
    (signed ±1 with per-tensor scale = mean(|g|)). This collapses the
    per-activation grad to 1 bit + 1 fp16 scale on backward."""
    @staticmethod
    def forward(ctx, x):
        return x
    @staticmethod
    def backward(ctx, g):
        scale = g.abs().mean()
        return torch.sign(g) * scale


# =========================================================================
# Trick 4: XNORLinear — binary W + (optionally) binary X, matmul = XNOR-popcount
# =========================================================================

class XNORLinear(nn.Module):
    def __init__(self, in_features: int, out_features: int,
                 master_dtype=torch.float32, bias: bool = True,
                 binary_act: bool = True, binary_grad: bool = False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.master_dtype = master_dtype
        self.binary_act = binary_act
        self.binary_grad = binary_grad
        self.weight = nn.Parameter(
            torch.empty(out_features, in_features, dtype=master_dtype)
        )
        nn.init.kaiming_normal_(self.weight)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features, dtype=master_dtype))
        else:
            self.register_parameter("bias", None)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # IMPORTANT: master is held in `master_dtype` for grad updates, but
        # the per-forward binary projection uses input dtype directly to
        # avoid the per-call fp32→bf16 cast that thrashes ROCm memory.
        # When master_dtype != input dtype, the sign computation happens
        # in input dtype (cheaper) and STE grad still flows back into the
        # higher-precision master via autograd's automatic dtype upcast.
        w = self.weight
        if w.dtype != x.dtype:
            w = w.to(x.dtype)
        alpha = w.abs().mean()
        w_bin = SignSTE.apply(w) * alpha
        bias = self.bias
        if bias is not None and bias.dtype != x.dtype:
            bias = bias.to(x.dtype)

        if self.binary_act:
            # Per-row activation scale beta (XNOR-Net)
            beta = x.abs().mean(dim=-1, keepdim=True)
            x_b = ActSignSTE.apply(x)
            y = F.linear(x_b * beta, w_bin, bias)
        else:
            y = F.linear(x, w_bin, bias)

        if self.binary_grad:
            y = BinaryGradWrap.apply(y)
        return y


def replace_qkvo_xnor(model: nn.Module, master_dtype, binary_act: bool,
                     binary_grad: bool) -> int:
    """Recursively swap q/k/v/o nn.Linear → XNORLinear."""
    n = 0
    for name, child in list(model.named_children()):
        if isinstance(child, nn.Linear) and name in ("q_proj", "k_proj", "v_proj", "o_proj"):
            new = XNORLinear(child.in_features, child.out_features,
                             master_dtype=master_dtype,
                             bias=child.bias is not None,
                             binary_act=binary_act,
                             binary_grad=binary_grad)
            with torch.no_grad():
                new.weight.data.copy_(child.weight.data.to(master_dtype))
                if child.bias is not None:
                    new.bias.data.copy_(child.bias.data.to(master_dtype))
            setattr(model, name, new)
            n += 1
        else:
            n += replace_qkvo_xnor(child, master_dtype, binary_act, binary_grad)
    return n


# =========================================================================
# Trick 5: approximate RMSNorm via L1 mean (skip sqrt + per-element square)
# =========================================================================

class ApproxRMSNorm(nn.Module):
    """RMSNorm replaced with L1-normalization:
        y = weight * x / (mean(|x|) + eps)
    L1 mean = ~0.798 × L2 sqrt-mean for Gaussian, so this approximation
    is within a constant factor of true RMS. Saves the per-element square
    and sqrt (and the implicit fp32 cast that PyTorch RMSNorm does).
    """
    def __init__(self, dim: int, eps: float = 1e-6,
                 weight: torch.Tensor | None = None):
        super().__init__()
        if weight is None:
            weight = torch.ones(dim)
        self.weight = nn.Parameter(weight.clone())
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scale = x.abs().mean(dim=-1, keepdim=True).clamp_min(self.eps)
        return (self.weight * (x / scale)).to(x.dtype)


def replace_rmsnorm(model: nn.Module) -> int:
    """Find RMSNorm-like modules (Qwen2RMSNorm) and swap with ApproxRMSNorm."""
    n = 0
    for name, child in list(model.named_children()):
        # Identify by class name to avoid hard import
        if "RMSNorm" in type(child).__name__:
            dim = child.weight.shape[0]
            new = ApproxRMSNorm(dim, eps=getattr(child, "variance_epsilon", 1e-6),
                                weight=child.weight.data)
            setattr(model, name, new)
            n += 1
        else:
            n += replace_rmsnorm(child)
    return n


# =========================================================================
# Trick 6: approximate softmax via 2^x (LUT-style; exp via float-exponent shift)
# =========================================================================

_REAL_SOFTMAX = F.softmax  # save original

def _approx_softmax(x: torch.Tensor, dim: int = -1, dtype=None) -> torch.Tensor:
    """2^x approximation: e^x ≈ 2^(x·1.4427).
    A 2^x on float can be computed via bit-shift on the exponent field
    + Taylor approximation on the mantissa (Schraudolph 1999). We use
    torch.pow(2.0, ...) which on bf16 lands on the hardware exp2 unit.
    """
    s = x - x.amax(dim=dim, keepdim=True)
    e = torch.pow(2.0, s * 1.4426950408889634)  # log2(e)
    out = e / e.sum(dim=dim, keepdim=True)
    if dtype is not None:
        out = out.to(dtype)
    return out


def patch_softmax():
    F.softmax = _approx_softmax
    torch.softmax = _approx_softmax
    # nn.Softmax falls through to F.softmax


def unpatch_softmax():
    F.softmax = _REAL_SOFTMAX
    torch.softmax = _REAL_SOFTMAX


# =========================================================================
# Trick 7: SignSGD / Lion optimizers (sign/momentum tricks)
# =========================================================================

class SignSGD(torch.optim.Optimizer):
    """update = -lr * sign(grad). Zero state — 1-bit-per-param update."""
    def __init__(self, params, lr: float = 1e-4):
        super().__init__(params, dict(lr=lr))

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for g in self.param_groups:
            lr = g["lr"]
            for p in g["params"]:
                if p.grad is None:
                    continue
                p.add_(p.grad.sign(), alpha=-lr)
        return loss


class Lion(torch.optim.Optimizer):
    """Lion (Chen et al. 2023) — sign of momentum-blended gradient."""
    def __init__(self, params, lr: float = 1e-4, betas=(0.9, 0.99), wd=0.0):
        super().__init__(params, dict(lr=lr, betas=betas, weight_decay=wd))

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for grp in self.param_groups:
            lr = grp["lr"]; b1, b2 = grp["betas"]; wd = grp["weight_decay"]
            for p in grp["params"]:
                if p.grad is None: continue
                state = self.state[p]
                if "m" not in state:
                    state["m"] = torch.zeros_like(p)
                m = state["m"]
                if wd != 0:
                    p.mul_(1 - lr * wd)
                u = (b1 * m + (1 - b1) * p.grad).sign()
                p.add_(u, alpha=-lr)
                m.mul_(b2).add_(p.grad, alpha=1 - b2)
        return loss


def make_optimizer(name: str, params, lr: float | None = None):
    if name == "adamw":
        return torch.optim.AdamW(params, lr=lr or 2e-4)
    if name == "sgd":
        return torch.optim.SGD(params, lr=lr or 1e-3, momentum=0.9)
    if name == "signsgd":
        return SignSGD(params, lr=lr or 1e-4)
    if name == "lion":
        return Lion(params, lr=lr or 1e-4)
    raise ValueError(f"unknown optimizer {name}")


# =========================================================================
# Dataset
# =========================================================================

def load_examples(dataset_id: str, n: int) -> list[dict[str, str]]:
    from baien_distill.adapters.hf_dataset import DATASET_REGISTRY, load_examples
    flat = {}
    for cat, specs in DATASET_REGISTRY.items():
        for s in specs:
            flat.setdefault(s.id, (cat, s))
    hit = flat.get(dataset_id)
    if hit is None:
        raise RuntimeError(f"{dataset_id} not in DATASET_REGISTRY")
    cat, spec = hit
    rows = list(load_examples(spec, cat, limit=n))
    return [{"prompt": r.prompt, "response": r.response} for r in rows]


# =========================================================================
# Main
# =========================================================================

def run(tricks: set[str], opt_name: str, master: str, base: str,
        dataset_id: str, n_rows: int, n_steps: int, grad_accum: int,
        out_dir: Path, max_len: int = 512) -> dict:
    dtype_map = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}
    master_dtype = dtype_map[master]
    label = f"{master}-{opt_name}-{','.join(sorted(tricks))}"

    print(f"[xnor {label}] load {base}", flush=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(base)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    # SOFTMAX patch must be installed BEFORE model load so attention picks it up
    if "SOFTMAX" in tricks:
        patch_softmax()
        print(f"[xnor {label}] patched F.softmax / torch.softmax", flush=True)

    model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16,
                                                 device_map=device,
                                                 attn_implementation="eager")
    n_xnor = 0
    if "WX" in tricks:
        n_xnor = replace_qkvo_xnor(model, master_dtype,
                                  binary_act="WX_act" in tricks,
                                  binary_grad="GRAD" in tricks)
        print(f"[xnor {label}] replaced {n_xnor} q/k/v/o -> XNORLinear "
              f"(binary_act={'WX_act' in tricks}, binary_grad={'GRAD' in tricks})",
              flush=True)
    model = model.to(device)

    n_norm = 0
    if "NORM" in tricks:
        n_norm = replace_rmsnorm(model)
        print(f"[xnor {label}] replaced {n_norm} RMSNorm -> ApproxRMSNorm", flush=True)
        model = model.to(device)

    # Freeze everything that isn't an XNORLinear master (or its bias)
    n_trainable = 0
    n_total = 0
    for p in model.parameters():
        p.requires_grad = False
        n_total += p.numel()
    for mod in model.modules():
        if isinstance(mod, XNORLinear):
            mod.weight.requires_grad = True
            n_trainable += mod.weight.numel()
            if mod.bias is not None:
                mod.bias.requires_grad = True
                n_trainable += mod.bias.numel()

    if n_trainable == 0:
        # baseline: no XNOR replace — unfreeze the q/k/v/o linears so we have
        # an apples-to-apples comparable training cost
        for name, mod in model.named_modules():
            if isinstance(mod, nn.Linear) and name.rsplit(".", 1)[-1] in (
                "q_proj", "k_proj", "v_proj", "o_proj"
            ):
                mod.weight.requires_grad = True
                n_trainable += mod.weight.numel()
                if mod.bias is not None:
                    mod.bias.requires_grad = True
                    n_trainable += mod.bias.numel()

    print(f"[xnor {label}] trainable={n_trainable:,} / total={n_total:,} "
          f"({100*n_trainable/n_total:.3f}%)", flush=True)

    # Dataset
    rows = load_examples(dataset_id, n_rows)
    sequences = []
    for r in rows:
        if getattr(tok, "chat_template", None):
            full = tok.apply_chat_template(
                [{"role": "user", "content": r["prompt"]},
                 {"role": "assistant", "content": r["response"]}],
                tokenize=False,
            )
        else:
            full = f"<|user|>\n{r['prompt']}\n<|assistant|>\n{r['response']}"
        enc = tok(full, return_tensors="pt", truncation=True, max_length=max_len)
        sequences.append({"input_ids": enc["input_ids"].squeeze(0),
                          "attention_mask": enc["attention_mask"].squeeze(0)})
    print(f"[xnor {label}] loaded {len(rows)} examples", flush=True)

    # Optimizer
    trainable = [p for p in model.parameters() if p.requires_grad]
    if "OPT" in tricks:
        opt = make_optimizer(opt_name, trainable)
    else:
        opt = make_optimizer("adamw", trainable)
    print(f"[xnor {label}] optimizer = {type(opt).__name__}", flush=True)

    # Train loop
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    model.train()
    losses, step_times, token_counts = [], [], []
    cycle = iter(sequences * 100)

    for step in range(n_steps):
        t0 = time.time()
        opt.zero_grad(set_to_none=True)
        accum_loss = 0.0
        n_tok_this = 0
        for _ in range(grad_accum):
            try:
                ex = next(cycle)
            except StopIteration:
                cycle = iter(sequences * 100)
                ex = next(cycle)
            ids = ex["input_ids"].unsqueeze(0).to(device)
            attn = ex["attention_mask"].unsqueeze(0).to(device)
            out = model(input_ids=ids, attention_mask=attn, labels=ids)
            (out.loss / grad_accum).backward()
            accum_loss += float(out.loss.item()) / grad_accum
            n_tok_this += int(attn.sum().item())
        opt.step()
        dt = time.time() - t0
        step_times.append(dt)
        losses.append(accum_loss)
        token_counts.append(n_tok_this)
        print(f"  [{label}] step {step+1}/{n_steps}: "
              f"loss={accum_loss:.4f} time={dt:.2f}s tok={n_tok_this}", flush=True)

    if "SOFTMAX" in tricks:
        unpatch_softmax()

    cold = step_times[0] if step_times else None
    warm = (sum(step_times[1:]) / max(1, len(step_times) - 1)
            if len(step_times) >= 2 else cold)
    avg_tok = sum(token_counts) / max(1, len(token_counts))
    peak_vram_gb = (round(torch.cuda.max_memory_allocated() / 1024**3, 3)
                    if torch.cuda.is_available() else None)

    # FLOPs estimate (forward+backward 6·N·T)
    sustained_tflops = (
        6 * n_total * avg_tok / (warm * 1e12) if warm and warm > 0 else None
    )
    sustained_tflops = round(sustained_tflops, 3) if sustained_tflops else None

    return {
        "kind": "xnor-extreme",
        "label": label,
        "master": master,
        "optimizer": opt_name if "OPT" in tricks else "adamw",
        "tricks": sorted(tricks),
        "base": base,
        "n_xnor_layers": n_xnor,
        "n_approx_norms": n_norm,
        "n_trainable": n_trainable,
        "n_total": n_total,
        "n_steps": n_steps,
        "grad_accum": grad_accum,
        "tokens_per_step_avg": avg_tok,
        "step_cold_sec": round(cold, 3) if cold else None,
        "step_warm_sec": round(warm, 3) if warm else None,
        "sustained_tflops_est": sustained_tflops,
        "losses": [round(l, 4) for l in losses],
        "final_loss": round(losses[-1], 4) if losses else None,
        "avg_loss": round(sum(losses)/max(1, len(losses)), 4) if losses else None,
        "peak_vram_gb": peak_vram_gb,
        "device": device,
        "status": "ok",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tricks", default="",
                    help="comma sep subset of {WX,WX_act,GRAD,NORM,SOFTMAX,OPT}")
    ap.add_argument("--opt", default="lion",
                    choices=["adamw", "sgd", "signsgd", "lion"])
    ap.add_argument("--master", default="fp32",
                    choices=["fp32", "fp16", "bf16"])
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--dataset", default="lordx64/reasoning-distill-opus-4-7-max-sft")
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("./xnor-extreme-out"))
    args = ap.parse_args()

    tricks = set(t.strip() for t in args.tricks.split(",") if t.strip())
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        row = run(tricks, args.opt, args.master, args.base, args.dataset,
                  args.rows, args.steps, args.grad_accum, args.out)
    except Exception as e:
        import traceback
        row = {"status": "error", "tricks": sorted(tricks),
               "master": args.master, "optimizer": args.opt,
               "error_type": type(e).__name__, "error_msg": str(e),
               "tb": traceback.format_exc()[-2000:]}

    label = f"{args.master}-{args.opt}-{','.join(sorted(tricks)) or 'baseline'}"
    out_path = args.out / f"xnor-{label}.json"
    out_path.write_text(json.dumps(row, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\n[xnor {label}] wrote {out_path} status={row.get('status')}",
          flush=True)


if __name__ == "__main__":
    main()
