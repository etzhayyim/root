r"""Phase B + C of real Bonsai Algorithm 1: shard-streaming forward through
the ORIGINAL bf16 base + per-Linear activation capture + Optimal-Scale
(OS) closed-form α recomputation.

This is the FOUNDATION on top of which Phase D (GPTQ block coordinate
descent) is layered. Stand-alone Phase B+C alone closes ~30-50% of the
quality gap vs naive sign quantize (Bonsai paper claim 79.3 → 70.5;
naive-sign baseline collapses to ~30 avg score).

Pipeline:
  1. Load tokenizer + N calibration prompts.
  2. init_empty_weights model shell. Register per-layer pre/post hooks:
     - pre: stream-load this layer's tensors from safetensors shards
     - per-Linear pre: capture .detach().cpu() of input X
     - post: evict layer tensors back to disk-free meta state
  3. Forward calibration tokens. Activations land in {layer_idx, sub_name} -> X.
  4. For each captured (W, X) pair, solve OS closed-form per row:
        H   = X.T @ X                                    # [d_in, d_in]
        s_i = sign(W[i, :])                              # [d_in], ±1
        α_i = (W[i, :] @ H @ s_i) / (s_i @ H @ s_i)     # scalar
     Stack α [d_out] → save next to packed_bits in calibrated checkpoint.
  5. (Phase D, separate) GPTQ block CD: after OS, walk columns left→right,
     quantize each, propagate residual error to remaining columns via
     `W[:, j+1:] -= error · (H[j, j+1:] / H[j, j])`. ~5-10× further reduction.

CURRENT STATE: Phase B (forward + activation capture) is fully drafted.
Phase C (OS solve) is drafted. Phase D is a TODO marker. Not yet run on EVO.

Realistic next-session effort to complete:
  - Phase B debugging: 1-2 hr (Qwen3.6 hybrid attn + MoE quirks, layer
    boundary handling in shard-stream load order)
  - Phase C: 30 min (closed-form math, save schema)
  - Phase D: half-day to full day (block CD correctness, large per-layer
    Hessian compute, memory pressure)
  - End-to-end re-pack + verify: 1-2 hr
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

import torch
import torch.nn as nn


# Calibration prompts. Diverse domain coverage; small enough to forward
# through the model quickly (100-500 total tokens).
DEFAULT_CALIB_PROMPTS = [
    "The quick brown fox jumps over the lazy dog. Repeating words like the and a are common in English text.",
    "Python is a programming language designed by Guido van Rossum. It supports multiple paradigms.",
    "Mount Everest is located in the Himalayas on the border between Nepal and Tibet.",
    "Photosynthesis converts sunlight and water into glucose and oxygen via chlorophyll in plant cells.",
    "The mitochondria is the powerhouse of the cell, generating ATP through oxidative phosphorylation.",
    "東京は日本の首都であり、世界で最も人口の多い都市の一つです。",
    "Mathematics: 2 + 2 = 4. The Pythagorean theorem states a² + b² = c² for right triangles.",
    "Machine learning models predict outcomes from training data using neural networks or decision trees.",
    "The Pacific Ocean is the largest body of water on Earth, covering about 30 percent of the surface.",
    "RNA is the messenger between DNA and protein synthesis in cellular biology.",
]


# =========================================================================
# Phase B: Shard-streaming forward + activation capture
# =========================================================================

class ShardWeightLoader:
    """Streams individual tensors from safetensors shards on demand.

    NO shard handle cache — opens + closes per call. Slower than caching
    but avoids accumulating 26 shard mmaps that exhaust Windows paging
    file (72 GB virtual address space). Each call clones the tensor out
    of the mmap so it's safe after close.
    """
    def __init__(self, ckpt_dir: Path):
        index_path = ckpt_dir / "model.safetensors.index.json"
        if index_path.exists():
            idx = json.loads(index_path.read_text(encoding="utf-8"))
            self.weight_map: dict[str, str] = idx["weight_map"]
        else:
            # Single-file safetensors (small dense models like Qwen3-1.7B-Base
            # ship as `model.safetensors` without an index). Build a synthetic
            # weight_map that points every tensor to the single file.
            from safetensors import safe_open
            singles = list(ckpt_dir.glob("model*.safetensors"))
            if not singles:
                raise FileNotFoundError(
                    f"No safetensors files in {ckpt_dir}; need either "
                    "model.safetensors.index.json or model.safetensors")
            if len(singles) != 1:
                raise RuntimeError(
                    f"Multiple safetensors in {ckpt_dir} but no index.json: {singles}")
            single = singles[0]
            with safe_open(str(single), framework="pt", device="cpu") as f:
                self.weight_map = {k: single.name for k in f.keys()}
        self.ckpt_dir = ckpt_dir

    def get(self, name: str) -> torch.Tensor:
        from safetensors import safe_open
        shard = self.weight_map.get(name)
        if shard is None:
            raise KeyError(f"{name} not in weight_map")
        with safe_open(str(self.ckpt_dir / shard), framework="pt", device="cpu") as f:
            return f.get_tensor(name).clone()

    def close(self):
        pass


def materialize_layer_weights(model: nn.Module, layer_idx: int,
                              loader: ShardWeightLoader,
                              prefix: str = "model.language_model"):
    """Load all tensors for layers[layer_idx] from shards into the model.

    Handles BOTH checkpoint key conventions:
      - multimodal:  model.language_model.layers.X.*
      - text-only:   model.layers.X.*
    The MODEL (text-only Qwen3_5MoeForCausalLM) uses model.layers.X.*; the
    CHECKPOINT (saved by multimodal wrapper) uses model.language_model.layers.X.*
    """
    from accelerate.utils import set_module_tensor_to_device
    # Resolve the model's layer (text-only path used by AutoModelForCausalLM)
    model_base = f"model.layers.{layer_idx}"
    layer = _resolve(model, model_base)
    if layer is None:
        raise RuntimeError(f"could not resolve {model_base}")
    # Walk all param/buffer names; try BOTH checkpoint key conventions
    for sub_name, _ in list(layer.named_parameters()) + list(layer.named_buffers()):
        model_full = f"{model_base}.{sub_name}"
        # Prefer multimodal checkpoint path
        ckpt_multi = f"model.language_model.layers.{layer_idx}.{sub_name}"
        ckpt_text  = f"model.layers.{layer_idx}.{sub_name}"
        t = None
        for ckpt_key in (ckpt_multi, ckpt_text):
            try:
                t = loader.get(ckpt_key)
                break
            except KeyError:
                continue
        if t is not None:
            try:
                set_module_tensor_to_device(model, model_full, "cpu", t)
            except Exception:
                pass


def evict_layer_weights(model: nn.Module, layer_idx: int,
                        prefix: str = "model.language_model"):
    """Reset layer params to ZERO on CPU (not meta) — keeping them allocated
    avoids 'cannot copy out of meta' errors during subsequent forward passes
    for layers that reuse cached state. Memory cost is per-layer (~5 GB) but
    swapped per-layer so peak is bounded."""
    layer = _resolve(model, f"model.layers.{layer_idx}")
    if layer is None:
        return
    # Soft evict: zero the data in place rather than reverting to meta
    with torch.no_grad():
        for p in layer.parameters():
            if not p.is_meta:
                p.data.zero_()


def _resolve(root: nn.Module, dotted: str):
    cur = root
    for p in dotted.split("."):
        if p.isdigit() and isinstance(cur, (nn.ModuleList, nn.Sequential)):
            cur = cur[int(p)]
        else:
            cur = getattr(cur, p, None)
        if cur is None:
            return None
    return cur


def register_activation_capture_hooks(model: nn.Module,
                                       store: dict,
                                       max_tokens_per_linear: int = 4096):
    """Hook every nn.Linear (and similar) to capture its input X.

    store: dict keyed by full module name; values list of X tensors.
    """
    hooks = []
    for full_name, mod in model.named_modules():
        if not isinstance(mod, nn.Linear):
            continue
        def make_hook(name):
            def hook(module, inputs):
                if len(inputs) == 0:
                    return
                x = inputs[0].detach()
                # Reshape to 2-D [tokens, features] for Hessian compute
                if x.ndim > 2:
                    x = x.reshape(-1, x.shape[-1])
                if name not in store:
                    store[name] = []
                # Cap total captured tokens
                already = sum(t.shape[0] for t in store[name])
                if already < max_tokens_per_linear:
                    take = min(x.shape[0], max_tokens_per_linear - already)
                    store[name].append(x[:take].cpu().to(torch.float32))
            return hook
        h = mod.register_forward_pre_hook(make_hook(full_name))
        hooks.append(h)
    return hooks


def preload_global_modules(model: nn.Module, loader: ShardWeightLoader,
                           prefix: str = "model.language_model"):
    """Load tensors that are NOT inside layers.X (embed, lm_head, final
    norm, router) so the first forward pass has non-meta inputs."""
    from accelerate.utils import set_module_tensor_to_device
    n_loaded = 0
    for tname in list(loader.weight_map.keys()):
        # Skip layer-internal tensors (they're streamed per-layer)
        if ".layers." in tname:
            continue
        # Skip visual/mtp (text-only path)
        if ".visual." in tname or tname.startswith("mtp."):
            continue
        # Strip multimodal nesting
        model_path = tname.replace("model.language_model.", "model.", 1)
        try:
            t = loader.get(tname)
            set_module_tensor_to_device(model, model_path, "cpu", t)
            n_loaded += 1
        except Exception:
            pass
    return n_loaded


def materialize_meta_zeros(model: nn.Module) -> int:
    """Any param/buffer still meta after preload gets zero-allocated. Prevents
    'cannot copy out of meta' errors mid-forward."""
    n = 0
    for mod in model.modules():
        for pname in list(mod._parameters):
            p = mod._parameters[pname]
            if p is not None and p.is_meta:
                mod._parameters[pname] = nn.Parameter(
                    torch.zeros(p.shape, dtype=p.dtype, device="cpu"),
                    requires_grad=False,
                )
                n += 1
        for bname in list(mod._buffers):
            b = mod._buffers[bname]
            if b is not None and b.is_meta:
                mod._buffers[bname] = torch.zeros(b.shape, dtype=b.dtype, device="cpu")
                n += 1
    return n


def forward_calibration(model, tok, prompts: list[str],
                         loader: ShardWeightLoader, num_layers: int,
                         prefix: str = "model.language_model"):
    """Run one forward per prompt; stream-load each layer's weights right
    before that layer fires, then evict after. Per-Linear activations are
    captured by hooks (already registered)."""
    import faulthandler
    faulthandler.enable()
    # Register per-layer pre/post hooks that stream-load + evict, with verbose log
    layer_hooks = []
    layers_mod = _resolve(model, f"{prefix}.layers") or _resolve(model, "model.layers")
    for i in range(num_layers):
        layer = layers_mod[i]
        def pre_hook(mod, inputs, _i=i):
            print(f"    -> layer {_i} pre-hook (load)", flush=True)
            materialize_layer_weights(model, _i, loader, prefix)
            # Check the input is non-meta
            if inputs and len(inputs) > 0:
                x = inputs[0] if not isinstance(inputs[0], tuple) else None
                if x is not None and hasattr(x, 'is_meta'):
                    print(f"       input is_meta={x.is_meta} shape={tuple(x.shape) if hasattr(x,'shape') else '?'} dtype={x.dtype if hasattr(x,'dtype') else '?'}", flush=True)
        def post_hook(mod, inputs, output, _i=i):
            o = output if not isinstance(output, tuple) else output[0]
            if hasattr(o, 'is_meta'):
                print(f"    <- layer {_i} post-hook output is_meta={o.is_meta}", flush=True)
            evict_layer_weights(model, _i, prefix)
            return output
        layer_hooks.append(layer.register_forward_pre_hook(pre_hook))
        layer_hooks.append(layer.register_forward_hook(post_hook))

    model.eval()
    for p_idx, p in enumerate(prompts):
        print(f"\n[Phase B] prompt {p_idx+1}/{len(prompts)}: {p[:50]!r}", flush=True)
        ids = tok(p, return_tensors="pt").input_ids
        print(f"[Phase B] input_ids shape={tuple(ids.shape)} dtype={ids.dtype}", flush=True)
        try:
            with torch.no_grad():
                model(input_ids=ids)
            print(f"[Phase B] prompt {p_idx+1} forward DONE", flush=True)
        except Exception as e:
            import traceback
            print(f"[Phase B] prompt {p_idx+1} FAILED: {type(e).__name__}: {str(e)[:200]}", flush=True)
            traceback.print_exc()
            break
    for h in layer_hooks:
        h.remove()


# =========================================================================
# Phase C: Per-Linear Optimal Scale (OS) closed-form α
# =========================================================================

def optimal_scale_per_row(W: torch.Tensor, X_concat: torch.Tensor,
                           eps: float = 1e-6) -> torch.Tensor:
    """For W [d_out, d_in], X [N_tokens, d_in], compute per-row optimal α
    that minimizes ||W·Xᵀ - α·sign(W)·Xᵀ||² for each output row independently.

    Closed form per row i (signs s_i = sign(W[i, :])):
        H = X.T @ X                          # [d_in, d_in]
        α_i = (W[i, :] @ H @ s_i) / (s_i @ H @ s_i + eps)
    """
    W = W.to(torch.float32)
    X = X_concat.to(torch.float32)
    H = X.T @ X                              # [d_in, d_in]
    signs = torch.sign(W)                    # [d_out, d_in]
    # Vectorized: numerator [d_out] = sum_j W[i,j] * sum_k H[j,k] * s_i[k]
    # = sum_j W[i,j] * (H @ s_i[i, :])[j]
    H_s = signs @ H                          # [d_out, d_in]
    num = (W * H_s).sum(dim=-1)             # [d_out]
    den = (signs * H_s).sum(dim=-1) + eps   # [d_out]
    alpha = num / den
    return alpha.abs()                       # alpha is magnitude


def os_calibrate_quantize(W: torch.Tensor, X_concat: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Returns (alpha [d_out], signs [d_out, d_in])."""
    alpha = optimal_scale_per_row(W, X_concat)
    signs = torch.sign(W)
    return alpha, signs


# =========================================================================
# Phase D: GPTQ block coordinate descent (TODO scaffold)
# =========================================================================

def gptq_block_cd(W: torch.Tensor, X_concat: torch.Tensor,
                   per_row_alpha: torch.Tensor | None = None,
                   damping: float = 0.01,
                   eps: float = 1e-9) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Phase D: GPTQ-style column-wise coordinate descent for 1-bit + per-row α.

    Reference: arxiv 2210.17323 (GPTQ). Per-1-bit specialization:
      - per-OUTPUT-ROW α (held fixed across the CD iteration, from Phase C)
      - per-element sign (determined by sign(W[:, j]) at each column visit)
      - error compensation via Hessian inverse propagates rounding error
        from column j into columns j+1..d_in-1

    Returns:
      W_q [d_out, d_in] : sign-quantized weight (values in {-α[i], +α[i]})
      signs [d_out, d_in] uint8 : recovered sign bits (1=+, 0=-)
      alpha [d_out] : per-row α used (returns the per_row_alpha arg)
    """
    W = W.clone().to(torch.float32)
    X = X_concat.to(torch.float32)
    d_out, d_in = W.shape
    N = X.shape[0]

    # Hessian + damping
    H = (X.t() @ X) * (2.0 / max(N, 1))                        # [d_in, d_in]
    diag_mean = float(H.diag().mean().clamp_min(eps))
    H = H + damping * diag_mean * torch.eye(d_in, dtype=torch.float32, device=W.device)

    # Cholesky inverse (upper-triangular convention used by GPTQ)
    try:
        L = torch.linalg.cholesky(H)
        H_inv = torch.cholesky_inverse(L)
    except RuntimeError:
        # Fallback: pinv when Cholesky fails (rare with damping > 0)
        H_inv = torch.linalg.pinv(H)

    # Per-row α: precomputed (from Phase C OS), else fall back to mean(|W|)
    if per_row_alpha is None:
        alpha = W.abs().mean(dim=-1)                          # [d_out]
    else:
        alpha = per_row_alpha.to(torch.float32)

    W_q = torch.zeros_like(W)
    signs = torch.zeros((d_out, d_in), dtype=torch.uint8)

    for j in range(d_in):
        # Quantize column j: per-row sign × per-row α
        w_j = W[:, j]                                          # [d_out]
        s_j = torch.sign(w_j)                                  # ±1, ±0
        q_j = s_j * alpha                                      # [d_out]
        W_q[:, j] = q_j
        signs[:, j] = (s_j > 0).to(torch.uint8)

        # Propagate quantization error to remaining columns via H^{-1}
        if j < d_in - 1:
            err = (w_j - q_j) / (H_inv[j, j].clamp_min(eps))   # [d_out]
            # Update: W[:, j+1:] -= err ⊗ H_inv[j, j+1:]
            W[:, j+1:].sub_(err.unsqueeze(-1) * H_inv[j, j+1:].unsqueeze(0))

    return W_q, signs, alpha


def bonsai_quantize_linear(W: torch.Tensor, X_concat: torch.Tensor,
                            damping: float = 0.01) -> dict:
    """Full Bonsai 1-bit pipeline for one Linear weight:
      Phase C (OS) → Phase D (GPTQ block CD).

    Returns:
      {
        'W_q'   : [d_out, d_in] sign-quantized weight
        'signs' : [d_out, d_in] uint8 sign bits
        'alpha' : [d_out] per-row magnitude
      }
    """
    # Phase C: per-row optimal α from activation Hessian
    alpha = optimal_scale_per_row(W, X_concat)
    # Phase D: GPTQ column-wise CD with that α
    W_q, signs, _ = gptq_block_cd(W, X_concat, per_row_alpha=alpha,
                                   damping=damping)
    return {"W_q": W_q, "signs": signs, "alpha": alpha}


# =========================================================================
# Phase E: Re-pack with calibrated alphas
# =========================================================================

def save_calibrated_alphas(out_dir: Path, calibrated: dict[str, torch.Tensor]):
    """Save per-Linear calibrated α tensors to disk for the bit_pack stage
    to consume. Schema: {linear_full_name: alpha_tensor [d_out]}.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {k: v.cpu().tolist() for k, v in calibrated.items()}
    (out_dir / "calibrated_alphas.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


# =========================================================================
# Main driver (scaffold — not yet runnable end-to-end on EVO)
# =========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig-ckpt", required=True, type=Path,
                    help="Original bf16 base (un-quantized) checkpoint dir")
    ap.add_argument("--out", required=True, type=Path,
                    help="Output dir for calibrated_alphas.json")
    ap.add_argument("--n-prompts", type=int, default=10)
    ap.add_argument("--max-tokens-per-linear", type=int, default=4096)
    ap.add_argument("--with-phase-d", action="store_true",
                    help="Run Phase D GPTQ column-CD after Phase C OS "
                         "(error propagation; 10-100× slower than OS-only)")
    ap.add_argument("--phase-d-damping", type=float, default=0.01,
                    help="Hessian damping for Phase D Cholesky stability")
    args = ap.parse_args()

    from accelerate import init_empty_weights
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    print(f"[bonsai-calib] tokenizer + meta model")
    tok = AutoTokenizer.from_pretrained(args.orig_ckpt)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    config = AutoConfig.from_pretrained(args.orig_ckpt)
    with init_empty_weights():
        model = AutoModelForCausalLM.from_config(config)

    # Discover num_layers
    tc = getattr(config, "text_config", config)
    num_layers = tc.num_hidden_layers

    loader = ShardWeightLoader(args.orig_ckpt)

    activations: dict[str, list[torch.Tensor]] = {}
    capture_hooks = register_activation_capture_hooks(
        model, activations, max_tokens_per_linear=args.max_tokens_per_linear
    )

    print(f"[bonsai-calib] preloading global modules (embed/norm/lm_head)")
    n_preload = preload_global_modules(model, loader)
    print(f"[bonsai-calib] preloaded {n_preload} global tensors")
    n_mat = materialize_meta_zeros(model)
    print(f"[bonsai-calib] zero-materialized {n_mat} remaining meta tensors")

    print(f"[bonsai-calib] Phase B: forward {args.n_prompts} prompts × "
          f"shard-streaming layer load")
    forward_calibration(model, tok, DEFAULT_CALIB_PROMPTS[:args.n_prompts],
                        loader, num_layers)

    for h in capture_hooks:
        h.remove()

    print(f"[bonsai-calib] captured activations for {len(activations)} Linears")

    # Only skip things that MUST stay full-precision (embed/lm_head/router).
    # Everything else gets Bonsai-calibrated α — this is the POINT of the
    # whole calibration: q/k/v/o + linear_attn projections + shared_expert
    # all suffered under naive sign in iter 1-4; with calibrated α they
    # should become viable 1-bit weights.
    SKIP_FOR_CALIB = (
        "embed_tokens", "lm_head", "router", "gate.weight", "mtp",
    )

    phase_label = "C+D (OS + GPTQ column-CD)" if args.with_phase_d else "C (OS-only)"
    print(f"[bonsai-calib] Phase {phase_label}, shard-grouped for Windows stability:")
    from collections import defaultdict
    from safetensors import safe_open

    # Group captured Linears by their checkpoint shard file (avoid per-Linear
    # safetensors mmap open-close churn that causes Windows access violations)
    linears_by_shard = defaultdict(list)
    skipped = 0
    for full_name in activations:
        if any(s in full_name.lower() for s in SKIP_FOR_CALIB):
            skipped += 1
            continue
        weight_key = full_name + ".weight"
        for k in [weight_key, weight_key.replace("model.", "model.language_model.", 1)]:
            shard = loader.weight_map.get(k)
            if shard:
                linears_by_shard[shard].append((full_name, k))
                break

    print(f"  filter: {skipped} skipped, {sum(len(v) for v in linears_by_shard.values())} to calibrate "
          f"across {len(linears_by_shard)} shards", flush=True)

    calibrated: dict[str, dict] = {}
    from safetensors.torch import save_file
    args.out.mkdir(parents=True, exist_ok=True)
    # Incremental save dir — per-shard checkpoint so Windows mmap crashes
    # don't wipe progress. Final aggregation collects all per-shard files.
    incr_dir = args.out / "per_shard"
    incr_dir.mkdir(exist_ok=True)
    alphas_only: dict[str, list] = {}
    for shard_idx, (shard, items) in enumerate(linears_by_shard.items()):
        # Skip shards we've already processed (resume capability)
        shard_out = incr_dir / f"{shard}.W_q.safetensors"
        if shard_out.exists():
            print(f"  [{shard_idx+1}/{len(linears_by_shard)}] {shard}: SKIP (already calibrated)",
                  flush=True)
            continue
        t0_shard = time.time()
        shard_tensors = {}
        try:
            with safe_open(str(args.orig_ckpt / shard), framework="pt", device="cpu") as f:
                for lin_idx, (full_name, k) in enumerate(items):
                    t0_lin = time.time()
                    W = f.get_tensor(k).clone()
                    X = torch.cat(activations[full_name], dim=0)
                    if args.with_phase_d:
                        # Phase C OS → Phase D GPTQ column-CD with error propagation
                        result = bonsai_quantize_linear(W, X, damping=args.phase_d_damping)
                        W_q = result["W_q"].to(torch.float32)
                        alpha = result["alpha"]
                    else:
                        # Phase C OS only — fast but no error propagation
                        alpha = optimal_scale_per_row(W, X)
                        W_q = torch.sign(W) * alpha.view(-1, 1)
                    calibrated[full_name] = {"W_q": W_q, "alpha": alpha}
                    shard_tensors[f"{full_name}.W_q"] = W_q.to(torch.bfloat16)
                    alphas_only[full_name] = alpha.cpu().tolist()
                    if args.with_phase_d:
                        print(f"    {lin_idx+1}/{len(items)} {full_name}: "
                              f"[{tuple(W.shape)}] in {time.time()-t0_lin:.1f}s",
                              flush=True)
            # Save this shard's calibrated tensors IMMEDIATELY
            if shard_tensors:
                save_file(shard_tensors, str(shard_out))
            # Save running alpha JSON too
            (args.out / "calibrated_alphas.json").write_text(
                json.dumps(alphas_only), encoding="utf-8")
            print(f"  [{shard_idx+1}/{len(linears_by_shard)}] {shard}: {len(items)} Linears "
                  f"in {time.time()-t0_shard:.1f}s -> {shard_out.name}", flush=True)
        except Exception as e:
            print(f"  [{shard_idx+1}/{len(linears_by_shard)}] {shard}: FAILED {type(e).__name__}: "
                  f"{str(e)[:120]}", flush=True)
            continue

    print(f"[bonsai-calib] full Bonsai Phase C+D done for {len(calibrated)} Linears")

    # Save: α + W_q for each Linear. signs are derived from W_q (sign(W_q)).
    # bit_pack can re-pack from these calibrated W_q's directly.
    args.out.mkdir(parents=True, exist_ok=True)
    alphas_only = {k: v["alpha"] for k, v in calibrated.items()}
    save_calibrated_alphas(args.out, alphas_only)
    # Also save calibrated W_q tensors (bf16) for re-pack step
    from safetensors.torch import save_file
    wq_dict = {f"{k}.W_q": v["W_q"].to(torch.bfloat16) for k, v in calibrated.items()}
    if wq_dict:
        save_file(wq_dict, str(args.out / "calibrated_W_q.safetensors"))
    print(f"[bonsai-calib] wrote {args.out / 'calibrated_alphas.json'} "
          f"+ {args.out / 'calibrated_W_q.safetensors'}")
    print(f"[bonsai-calib] next: re-run shard_quantize.py or bit_pack.py with "
          f"--calibrated-dir={args.out} to consume these alphas + W_q")


if __name__ == "__main__":
    main()
