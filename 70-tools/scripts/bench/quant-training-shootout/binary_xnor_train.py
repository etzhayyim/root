"""Binary XNOR-popcount training with master weights in {fp32, fp16, bf16}
and low-precision (non-Adam) optimizers {sgd-momentum, signsgd, lion}.

Algorithm:
  - q/k/v/o nn.Linear layers are replaced with BinaryLinear.
  - BinaryLinear maintains a master weight tensor in the chosen dtype.
  - Forward:  W_b = sign(W_master) * alpha    where alpha = mean(|W_master|)
              y   = (W_b @ x) + bias
    This is numerically equivalent to the XNOR-popcount kernel of
    Rastegari et al. 2016 in the "binary weights, float activations" mode
    that Bonsai 8B 1-bit (Prism ML 2026) uses. A true bit-packed XNOR-popcount
    kernel would unpack to the same arithmetic; on this hw (ROCm gfx1151)
    there is no native popcount-matmul kernel, so we compute via dense
    bf16 matmul on the sign-quantized tensor.
  - Backward:  straight-through estimator (STE) with clip — gradient
    passes through sign as identity but is zeroed where |W_master| > 1.

Optimizers:
  - SGD-momentum: classic, optimizer state = 1 momentum buffer per param
  - SignSGD:      update = -lr * sign(grad), NO state at all (1-bit comms)
  - Lion (Chen 2023): sign(beta1·m + (1-beta1)·g) update with momentum, 1
                      state buffer (same memory as SGD-momentum, sign-based)

Single-row CLI:
  python binary_xnor_train.py --master fp32 --opt lion --steps 3 \\
      --rows 8 --out C:\\Users\\gad\\binary-out
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


# ---------- Binary layer (XNOR-popcount semantics) ------------------------

class _SignSTE(torch.autograd.Function):
    """sign(x) forward; straight-through with |x|<=1 clip on backward."""
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return torch.sign(x)

    @staticmethod
    def backward(ctx, g):
        (x,) = ctx.saved_tensors
        g = g.clone()
        g[x.abs() > 1.0] = 0
        return g


class BinaryLinear(nn.Module):
    """Linear layer whose weight is binarized at every forward.

    Master weight kept in `master_dtype` and trained directly (no LoRA).
    Forward = (sign(W) * mean(|W|)) @ x + bias. Bias and master weight
    are the only trainable parameters.
    """
    def __init__(self, in_features: int, out_features: int,
                 master_dtype=torch.float32, bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.master_dtype = master_dtype
        self.weight = nn.Parameter(
            torch.empty(out_features, in_features, dtype=master_dtype)
        )
        nn.init.kaiming_normal_(self.weight)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features, dtype=master_dtype))
        else:
            self.register_parameter("bias", None)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Compute the binary projection in master dtype (so STE grad flows
        # back at master precision), then CAST DOWN to input dtype for the
        # matmul + output. This keeps the rest of the model in its native
        # dtype (bf16 for Qwen) — XNOR-Net keeps masters in fp32 only for
        # the optimizer step; compute stays low-precision.
        w = self.weight
        alpha = w.abs().mean()
        w_bin = _SignSTE.apply(w) * alpha
        w_bin_cast = w_bin.to(x.dtype)
        bias_cast = self.bias.to(x.dtype) if self.bias is not None else None
        return F.linear(x, w_bin_cast, bias_cast)

    def extra_repr(self) -> str:
        return (f"in={self.in_features}, out={self.out_features}, "
                f"master_dtype={self.master_dtype}, "
                f"bias={self.bias is not None}")


def replace_qkvo_with_binary(model: nn.Module, master_dtype) -> int:
    """Recursively replace q/k/v/o_proj nn.Linear with BinaryLinear.

    Returns the count of replaced layers.
    """
    replaced = 0
    for name, child in list(model.named_children()):
        if isinstance(child, nn.Linear) and name in ("q_proj", "k_proj", "v_proj", "o_proj"):
            new = BinaryLinear(child.in_features, child.out_features,
                               master_dtype=master_dtype,
                               bias=child.bias is not None)
            # Initialize master from the pretrained weight (cast to master dtype)
            with torch.no_grad():
                new.weight.data.copy_(child.weight.data.to(master_dtype))
                if child.bias is not None:
                    new.bias.data.copy_(child.bias.data.to(master_dtype))
            setattr(model, name, new)
            replaced += 1
        else:
            replaced += replace_qkvo_with_binary(child, master_dtype)
    return replaced


# ---------- Optimizers (non-Adam) -----------------------------------------

class SignSGD(torch.optim.Optimizer):
    """Update = -lr * sign(grad). Stateless (no momentum, no Adam moments).
    Closest to "1-bit optimizer" — entire update direction is 1 bit/param.
    """
    def __init__(self, params, lr: float = 1e-4):
        super().__init__(params, dict(lr=lr))

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            lr = group["lr"]
            for p in group["params"]:
                if p.grad is None:
                    continue
                p.add_(p.grad.sign(), alpha=-lr)
        return loss


class Lion(torch.optim.Optimizer):
    """Lion (Chen et al. 2023) — sign-based with momentum. Per-param state =
    one momentum buffer (same memory as SGD-momentum). Update is sign of
    a momentum-blended gradient, so the *direction* fits in 1 bit/param.
    """
    def __init__(self, params, lr: float = 1e-4,
                 betas: tuple[float, float] = (0.9, 0.99),
                 weight_decay: float = 0.0):
        super().__init__(params, dict(lr=lr, betas=betas, weight_decay=weight_decay))

    @torch.no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            lr = group["lr"]
            b1, b2 = group["betas"]
            wd = group["weight_decay"]
            for p in group["params"]:
                if p.grad is None:
                    continue
                state = self.state[p]
                if "m" not in state:
                    state["m"] = torch.zeros_like(p)
                m = state["m"]
                # Decoupled weight decay
                if wd != 0:
                    p.mul_(1 - lr * wd)
                # Update direction
                u = (b1 * m + (1 - b1) * p.grad).sign()
                p.add_(u, alpha=-lr)
                # Update momentum
                m.mul_(b2).add_(p.grad, alpha=1 - b2)
        return loss


def make_optimizer(name: str, params, lr: float | None = None):
    if name == "sgd":
        # SGD-momentum baseline. lr 1e-3 + momentum 0.9 is conservative.
        return torch.optim.SGD(params, lr=lr or 1e-3, momentum=0.9)
    if name == "signsgd":
        return SignSGD(params, lr=lr or 1e-4)
    if name == "lion":
        return Lion(params, lr=lr or 1e-4)
    raise ValueError(f"unknown optimizer {name}")


# ---------- Dataset --------------------------------------------------------

def load_examples(dataset_id: str, n: int) -> list[dict[str, str]]:
    from baien_distill.adapters.hf_dataset import DATASET_REGISTRY, load_examples
    flat: dict[str, tuple[str, object]] = {}
    for cat, specs in DATASET_REGISTRY.items():
        for s in specs:
            flat.setdefault(s.id, (cat, s))
    hit = flat.get(dataset_id)
    if hit is None:
        raise RuntimeError(f"{dataset_id} not in DATASET_REGISTRY")
    cat, spec = hit
    rows = list(load_examples(spec, cat, limit=n))
    return [{"prompt": r.prompt, "response": r.response} for r in rows]


# ---------- Main run -------------------------------------------------------

def run(master: str, opt: str, base: str, dataset_id: str,
        n_rows: int, n_steps: int, grad_accum: int, out_dir: Path,
        max_len: int = 512) -> dict:
    dtype_map = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}
    master_dtype = dtype_map[master]
    print(f"[binary {master}/{opt}] load base = {base}", flush=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(base)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16,
                                                 device_map=device)
    # Replace q/k/v/o with BinaryLinear
    n_replaced = replace_qkvo_with_binary(model, master_dtype)
    model = model.to(device)
    print(f"[binary {master}/{opt}] replaced {n_replaced} Linear -> BinaryLinear "
          f"(master_dtype={master_dtype})", flush=True)

    # Freeze everything that's NOT a BinaryLinear master parameter
    n_trainable = 0
    n_total = 0
    for p in model.parameters():
        p.requires_grad = False
        n_total += p.numel()
    for mod in model.modules():
        if isinstance(mod, BinaryLinear):
            mod.weight.requires_grad = True
            n_trainable += mod.weight.numel()
            if mod.bias is not None:
                mod.bias.requires_grad = True
                n_trainable += mod.bias.numel()
    print(f"[binary {master}/{opt}] trainable={n_trainable:,} / total={n_total:,} "
          f"({100*n_trainable/n_total:.3f}%)", flush=True)

    # Dataset: build chat-formatted (prompt+completion) sequences
    rows = load_examples(dataset_id, n_rows)
    print(f"[binary {master}/{opt}] loaded {len(rows)} examples", flush=True)
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

    # Optimizer on the trainable (BinaryLinear master) params
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = make_optimizer(opt, trainable_params)

    # Manual SFT loop
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model.train()
    losses: list[float] = []
    step_times: list[float] = []
    rng = iter(sequences * 100)  # cycle if needed

    for step in range(n_steps):
        t0 = time.time()
        optimizer.zero_grad(set_to_none=True)
        accum_loss = 0.0
        for _ in range(grad_accum):
            try:
                ex = next(rng)
            except StopIteration:
                rng = iter(sequences * 100)
                ex = next(rng)
            ids = ex["input_ids"].unsqueeze(0).to(device)
            attn = ex["attention_mask"].unsqueeze(0).to(device)
            out = model(input_ids=ids, attention_mask=attn, labels=ids)
            loss = out.loss / grad_accum
            loss.backward()
            accum_loss += loss.item()
        optimizer.step()
        dt = time.time() - t0
        step_times.append(dt)
        losses.append(accum_loss)
        print(f"  step {step+1}/{n_steps}: loss={accum_loss:.4f} time={dt:.2f}s",
              flush=True)

    final_loss = losses[-1] if losses else float("nan")
    avg_loss = sum(losses) / max(1, len(losses))
    cold = step_times[0] if step_times else None
    warm = (sum(step_times[1:]) / max(1, len(step_times) - 1)
            if len(step_times) >= 2 else cold)
    peak_vram_gb = (round(torch.cuda.max_memory_allocated() / 1024**3, 3)
                    if torch.cuda.is_available() else None)

    row = {
        "kind": "binary-xnor",
        "master": master,
        "optimizer": opt,
        "base": base,
        "n_layers_replaced": n_replaced,
        "n_trainable": n_trainable,
        "n_total": n_total,
        "n_steps": n_steps,
        "grad_accum": grad_accum,
        "step_cold_sec": round(cold, 2) if cold else None,
        "step_warm_sec": round(warm, 2) if warm else None,
        "losses": [round(l, 4) for l in losses],
        "final_loss": round(final_loss, 4),
        "avg_loss": round(avg_loss, 4),
        "peak_vram_gb": peak_vram_gb,
        "device": device,
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="fp32",
                    choices=["fp32", "fp16", "bf16"])
    ap.add_argument("--opt", default="lion",
                    choices=["sgd", "signsgd", "lion"])
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--dataset", default="lordx64/reasoning-distill-opus-4-7-max-sft")
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("./binary-out"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    try:
        row = run(args.master, args.opt, args.base, args.dataset,
                  args.rows, args.steps, args.grad_accum, args.out)
        row["status"] = "ok"
    except Exception as e:
        import traceback
        row = {"status": "error", "master": args.master, "optimizer": args.opt,
               "error_type": type(e).__name__, "error_msg": str(e),
               "tb": traceback.format_exc()[-2000:]}
    out_path = args.out / f"binary-{args.master}-{args.opt}.json"
    out_path.write_text(json.dumps(row, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\n[binary {args.master}/{args.opt}] wrote {out_path} "
          f"status={row.get('status')}", flush=True)


if __name__ == "__main__":
    main()
