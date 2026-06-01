r"""Custom packed-bit inference engine for roso 1-bit MoE siblings.

Reads bit-packed safetensors (output of bit_pack.py: keys end in
`.packed_bits` + `.alpha`), reconstructs the dense weight on the fly per
forward call, and uses standard transformers attention / MoE forward paths.

Key modules:
  - PackedBinaryLinear  — replaces nn.Linear; stores int32 packed bits +
                          fp16 alpha; forward unpacks to ±alpha bf16
  - PackedMoEExperts    — replaces the MoE expert weight container;
                          stores [E,P] packed + [E] alpha; on access of
                          a single expert e, unpacks to ±alpha[e] bf16

Loader strategy:
  1. init_empty_weights — build meta-model from config (~zero memory)
  2. Walk modules; identify each nn.Linear matching quantize pattern
  3. Replace with PackedBinaryLinear (only int32+fp16 buffers, much smaller)
  4. For 3-D MoE experts (nn.Parameter, not Linear): replace with PackedMoEExperts
  5. Load packed shard-by-shard; assign packed_bits/alpha into target modules
  6. For skipped tensors (embed/lm_head/router/norm/conv1d): use set_module_tensor_to_device
  7. Run forward

This bypasses both the from_pretrained mmap problem (we load shard-by-shard)
and the dispatch meta-tensor problem (we don't use accelerate dispatch).

Memory budget: ~5 GB packed q/k/v/o weights + ~3 GB MoE experts (per-expert
packed) + ~3 GB skipped fp16 tensors (embed/lm_head/router/conv1d/norms) =
roughly 11 GB resident. Fits in 64 GB OS RAM with huge margin.

Usage:
    python -m roso_distill.packed_infer \
        --ckpt C:\Users\gad\roso-35b-out\sibling-00-Qwen__Qwen3.6-35B-A3B-packed \
        --prompt "Hello" --max-new-tokens 10
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
import torch.nn.functional as F


# =========================================================================
# Packed-bit modules
# =========================================================================

def _unpack_signs(packed_bits: torch.Tensor, K: int, dtype) -> torch.Tensor:
    """packed_bits: int32 [..., P] where P = ceil(K/32).
    Returns ±1 tensor [..., K] in the requested dtype.

    Bit i of word j -> element j*32 + i. 1 -> +1, 0 -> -1.
    """
    P = packed_bits.size(-1)
    K_padded = P * 32
    arange32 = torch.arange(32, dtype=torch.int32, device=packed_bits.device)
    # [..., P, 32] : bit i of word
    bits = (packed_bits.unsqueeze(-1) >> arange32) & 1
    # flatten last 2 dims -> [..., K_padded]
    flat = bits.reshape(*packed_bits.shape[:-1], K_padded).to(dtype)
    signs = flat * 2.0 - 1.0
    # Truncate to real K
    return signs[..., :K]


class PackedBinaryLinear(nn.Module):
    """2-D nn.Linear replacement using packed bits + per-tensor alpha.

    Caches the unpacked weight after first forward to avoid re-unpacking
    every call (huge speedup at the cost of layer-worth of dense memory
    while in use).
    """

    def __init__(self, in_features: int, out_features: int, bias: bool = False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        K = in_features * out_features
        P = (K + 31) // 32
        self.register_buffer("packed_bits",
                             torch.zeros(1, P, dtype=torch.int32))
        # Per-output-channel alpha (was per-tensor scalar in iter 1)
        self.register_buffer("alpha",
                             torch.zeros(out_features, dtype=torch.float16))
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.register_parameter("bias", None)
        self._cached_weight = None
        self._cached_dtype = None

    def _build_weight(self, dtype) -> torch.Tensor:
        if self._cached_weight is not None and self._cached_dtype == dtype:
            return self._cached_weight
        K = self.in_features * self.out_features
        signs = _unpack_signs(self.packed_bits, K, dtype).reshape(1, -1)[0]
        signs = signs[:K].reshape(self.out_features, self.in_features)
        # Broadcast per-output-channel alpha [d_out] -> [d_out, 1]
        alpha = self.alpha.to(dtype).view(self.out_features, 1)
        W = signs * alpha
        self._cached_weight = W
        self._cached_dtype = dtype
        return W

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        W = self._build_weight(x.dtype)
        b = self.bias.to(x.dtype) if self.bias is not None else None
        return F.linear(x, W, b)

    def extra_repr(self) -> str:
        return (f"in={self.in_features}, out={self.out_features}, "
                f"bias={self.bias is not None}, packed=True")


class PackedMoEExpertWeight(nn.Module):
    """3-D MoE expert weight container [E, d_out, d_in] (or [E, d_in, d_out])
    using per-expert packed bits + per-expert alpha.

    Mimics nn.Parameter access semantics: indexable as a tensor.
    """

    def __init__(self, shape: tuple[int, ...]):
        super().__init__()
        assert len(shape) == 3, f"expected 3-D shape, got {shape}"
        E, d1, d2 = shape
        self.shape_full = shape
        K_per_e = d1 * d2
        P = (K_per_e + 31) // 32
        self.register_buffer("packed_bits",
                             torch.zeros(E, P, dtype=torch.int32))
        # Per-(expert, output_channel) alpha: [E, d_out] (was [E] in iter 1)
        self.register_buffer("alpha",
                             torch.zeros(E, d1, dtype=torch.float16))
        self._expert_cache: dict = {}

    def get_expert_cached(self, e: int, dtype) -> torch.Tensor:
        key = (e, dtype)
        if key in self._expert_cache:
            return self._expert_cache[key]
        W = self.get_expert(e, dtype)
        self._expert_cache[key] = W
        return W

    def get_expert(self, e: int, dtype=torch.bfloat16) -> torch.Tensor:
        """Unpack a single expert's weight [d1, d2] with per-output-channel alpha."""
        key = (e, dtype)
        if key in self._expert_cache:
            return self._expert_cache[key]
        E, d1, d2 = self.shape_full
        K = d1 * d2
        bits = self.packed_bits[e:e+1]                         # [1, P]
        signs = _unpack_signs(bits, K, dtype)[0].reshape(d1, d2)  # [d1, d2]
        # Per-output-channel alpha [d1] -> [d1, 1]
        alpha = self.alpha[e].to(dtype).view(d1, 1)
        W = signs * alpha
        self._expert_cache[key] = W
        return W

    def get_all(self, dtype=torch.bfloat16) -> torch.Tensor:
        """Unpack all experts (used for `experts.weight[idx]` style access)."""
        E, d1, d2 = self.shape_full
        K = d1 * d2
        signs = _unpack_signs(self.packed_bits, K, dtype)      # [E, K]
        alpha = self.alpha.to(dtype).view(E, 1)
        return (signs * alpha).reshape(E, d1, d2)

    def extra_repr(self) -> str:
        return f"shape={self.shape_full}, packed=True"


# =========================================================================
# Module replacement helpers
# =========================================================================

QUANT_LINEAR_NAMES = {"q_proj", "k_proj", "v_proj", "o_proj",
                      "in_proj_qkv", "in_proj_z", "in_proj_a", "in_proj_b",
                      "out_proj", "gate_proj", "up_proj", "down_proj"}


def replace_linears_with_packed(model: nn.Module) -> int:
    """Walk model, swap quantize-target nn.Linear with PackedBinaryLinear.
    Returns count of swaps."""
    n = 0
    for name, child in list(model.named_children()):
        short = name
        if isinstance(child, nn.Linear) and short in QUANT_LINEAR_NAMES:
            new = PackedBinaryLinear(child.in_features, child.out_features,
                                     bias=child.bias is not None)
            # Try to copy bias if it exists and is not meta
            if child.bias is not None and not child.bias.is_meta:
                with torch.no_grad():
                    new.bias.copy_(child.bias)
            setattr(model, name, new)
            n += 1
        else:
            n += replace_linears_with_packed(child)
    return n


def _nav(root: nn.Module, parts: list[str]):
    """Walk a module path, handling both attribute access and ModuleList indexing."""
    cur = root
    for p in parts:
        if cur is None:
            return None
        if p.isdigit() and isinstance(cur, (nn.ModuleList, nn.Sequential)):
            try:
                cur = cur[int(p)]
            except (IndexError, KeyError):
                return None
        else:
            cur = getattr(cur, p, None)
    return cur


def _ckpt_to_model_path(tname: str) -> str | None:
    """Map a checkpoint key to the text-only Qwen3_5MoeForCausalLM model path.

    Multimodal wrapper checkpoint uses `model.language_model.X` for text and
    `model.visual.X` for vision. `AutoModelForCausalLM.from_config` instantiates
    the text-only `Qwen3_5MoeForCausalLM` whose paths are `model.X`. Strip
    `language_model` prefix; return None for visual/mtp (not in text model).
    """
    # Skip visual + mtp branches (not present in text-only CausalLM model)
    if ".visual." in tname or tname.startswith("model.visual.") or tname.startswith("mtp."):
        return None
    # Strip the language_model nesting
    return tname.replace("model.language_model.", "model.", 1)


def replace_3d_moe_experts_with_packed(model: nn.Module, pack_meta: dict) -> int:
    """For each 3-D MoE expert parameter, replace with PackedMoEExpertWeight."""
    n = 0
    for tensor_name, meta in pack_meta.items():
        if meta["ndim"] != 3:
            continue
        # Map checkpoint path -> model path
        model_path = _ckpt_to_model_path(tensor_name)
        if model_path is None:
            continue
        path = model_path.split(".")
        parent = _nav(model, path[:-1])
        if parent is None:
            continue
        attr_name = path[-1]
        shape = tuple(meta["shape"])
        new = PackedMoEExpertWeight(shape)
        # Replace the nn.Parameter with our module via setattr trickery:
        # delattr first to avoid Parameter/Module type collision
        if hasattr(parent, attr_name):
            try:
                delattr(parent, attr_name)
            except AttributeError:
                pass
        setattr(parent, attr_name, new)
        n += 1
    return n


# =========================================================================
# Loader
# =========================================================================

def patch_moe_experts_forward(model: nn.Module):
    """Monkey-patch any module that owns AT LEAST ONE PackedMoEExpertWeight
    (handles mixed packed + bf16 modes where one projection is skipped).
    """
    n_patched = 0
    for mod_name, mod in model.named_modules():
        gp = getattr(mod, "gate_up_proj", None)
        dp = getattr(mod, "down_proj", None)
        gp_packed = isinstance(gp, PackedMoEExpertWeight)
        dp_packed = isinstance(dp, PackedMoEExpertWeight)
        if gp_packed or dp_packed:
            _bind_packed_experts_forward(mod, gp_packed, dp_packed)
            n_patched += 1
    return n_patched


def _bind_packed_experts_forward(experts_mod: nn.Module, gp_packed: bool, dp_packed: bool):
    """Replace `forward` to support mixed PackedMoEExpertWeight + bf16
    nn.Parameter MoE experts. Each projection independently packed or not.
    """
    gp_mod = experts_mod.gate_up_proj
    dp_mod = experts_mod.down_proj
    act_fn = getattr(experts_mod, "act_fn", None)

    def _get_gp(e, dtype):
        if gp_packed:
            return gp_mod.get_expert_cached(e, dtype)
        return gp_mod[e].to(dtype)

    def _get_dp(e, dtype):
        if dp_packed:
            return dp_mod.get_expert_cached(e, dtype)
        return dp_mod[e].to(dtype)

    def packed_forward(hidden_states, selected_experts, routing_weights):
        """Token-by-token loop for simplicity. NOT performance-optimised.

        hidden_states: [N, hidden]   (flat tokens after reshape)
        selected_experts: [N, K]      indices into experts
        routing_weights: [N, K]       softmax-weighted contribution per expert
        """
        dtype = hidden_states.dtype
        device = hidden_states.device
        N, hidden = hidden_states.shape
        out = torch.zeros_like(hidden_states)
        K = selected_experts.shape[1]
        # Iterate ACTIVE experts; gather tokens routed to each
        unique_e = torch.unique(selected_experts.flatten())
        for e in unique_e.tolist():
            # mask: which (token, slot) pairs route to expert e?
            mask = (selected_experts == e)        # [N, K] bool
            if not mask.any():
                continue
            # Per-token weight: sum routing_weights for this expert
            tok_w = (routing_weights * mask.to(dtype)).sum(dim=1)  # [N]
            tok_idx = (tok_w > 0).nonzero(as_tuple=False).flatten()
            if tok_idx.numel() == 0:
                continue
            # Unpack this expert's two projections (mixed packed/bf16 path)
            gp_e = _get_gp(e, dtype).to(device)   # [d_gp1, d_gp2]
            dp_e = _get_dp(e, dtype).to(device)   # [d_dp1, d_dp2]
            x = hidden_states[tok_idx]                            # [Nt, hidden]
            # gate_up_proj computes [gate, up] concatenated; standard Qwen MoE
            # convention: gp_e shape is [2*inter, hidden] -> y = x @ gp_e.T -> [Nt, 2*inter]
            y = x @ gp_e.t()
            inter = y.shape[-1] // 2
            gate = y[..., :inter]
            up = y[..., inter:]
            if act_fn is not None:
                gate = act_fn(gate)
            h = gate * up                                          # [Nt, inter]
            # down_proj: dp_e shape [hidden, inter] -> out = h @ dp_e.T -> [Nt, hidden]
            o = h @ dp_e.t()
            # weight by routing
            o = o * tok_w[tok_idx].unsqueeze(-1)
            out[tok_idx] = out[tok_idx] + o
        return out

    experts_mod.forward = packed_forward


def load_packed_checkpoint(ckpt_dir: Path) -> tuple[object, object]:
    """Build meta-model + load packed checkpoint shard-by-shard."""
    from accelerate import init_empty_weights
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    from accelerate.utils import set_module_tensor_to_device
    from safetensors import safe_open

    print(f"[load] config + tokenizer", flush=True)
    config = AutoConfig.from_pretrained(ckpt_dir)
    tok = AutoTokenizer.from_pretrained(ckpt_dir)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    print(f"[load] init_empty_weights -> meta model", flush=True)
    t0 = time.time()
    with init_empty_weights():
        model = AutoModelForCausalLM.from_config(config)
    print(f"[load] meta model built in {time.time()-t0:.1f}s "
          f"({sum(p.numel() for p in model.parameters()):,} params)", flush=True)

    # Load pack metadata sidecar
    meta_path = ckpt_dir / "bit_pack_meta.json"
    pack_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    print(f"[load] pack_meta: {len(pack_meta)} quantized tensors", flush=True)

    # Swap modules to packed variants
    n_2d = replace_linears_with_packed(model)
    n_3d = replace_3d_moe_experts_with_packed(model, pack_meta)
    print(f"[load] replaced {n_2d} Linear -> PackedBinaryLinear, "
          f"{n_3d} MoE expert -> PackedMoEExpertWeight", flush=True)

    # Walk shards, assign tensors
    idx = json.loads((ckpt_dir / "model.safetensors.index.json").read_text(encoding="utf-8"))
    wm = idx["weight_map"]
    shards = sorted(set(wm.values()))
    print(f"[load] walking {len(shards)} shards", flush=True)
    n_assigned = 0
    n_skipped_missing = 0
    for sf in shards:
        src = ckpt_dir / sf
        with safe_open(src, framework="pt", device="cpu") as f:
            for tname in f.keys():
                t = f.get_tensor(tname)
                # Skip visual + mtp branches (not in text-only model)
                model_tname = _ckpt_to_model_path(tname)
                if model_tname is None:
                    continue
                # packed_bits / alpha keys
                if model_tname.endswith(".packed_bits") or model_tname.endswith(".alpha"):
                    base_name = model_tname.rsplit(".", 1)[0]
                    suffix = model_tname.rsplit(".", 1)[1]
                    parts = base_name.split(".")
                    target = _nav(model, parts[:-1])
                    if target is None:
                        n_skipped_missing += 1
                        continue
                    leaf = parts[-1]
                    leaf_mod = getattr(target, leaf, None)
                    # Case A: leaf == "weight" -> parent linear is PackedBinaryLinear
                    if leaf == "weight" and isinstance(target, PackedBinaryLinear):
                        if suffix == "packed_bits":
                            target.packed_bits.copy_(t)
                        else:
                            target.alpha.copy_(t.reshape(-1)[:target.alpha.numel()])
                        n_assigned += 1
                    elif isinstance(leaf_mod, PackedMoEExpertWeight):
                        if suffix == "packed_bits":
                            leaf_mod.packed_bits.copy_(t)
                        else:
                            # alpha may be [E] (iter 1) or [E, d_out] (iter 2)
                            if t.ndim == leaf_mod.alpha.ndim:
                                leaf_mod.alpha.copy_(t)
                            else:
                                leaf_mod.alpha.copy_(t.reshape(leaf_mod.alpha.shape))
                        n_assigned += 1
                    elif isinstance(leaf_mod, PackedBinaryLinear):
                        if suffix == "packed_bits":
                            leaf_mod.packed_bits.copy_(t)
                        else:
                            leaf_mod.alpha.copy_(t.reshape(-1)[:leaf_mod.alpha.numel()])
                        n_assigned += 1
                    else:
                        n_skipped_missing += 1
                else:
                    # Standard tensor: assign via accelerate (use mapped path)
                    try:
                        set_module_tensor_to_device(model, model_tname, "cpu", t)
                        n_assigned += 1
                    except Exception as e:
                        n_skipped_missing += 1
    print(f"[load] assigned={n_assigned}, skipped(unmatched)={n_skipped_missing}",
          flush=True)

    # Materialize any remaining meta tensors (buffers, optional params not in
    # checkpoint) as zeros so forward doesn't blow up on .item()/.all() etc.
    n_materialized = 0
    for mod_name, m in model.named_modules():
        for pname in list(m._parameters):
            p = m._parameters[pname]
            if p is not None and p.is_meta:
                m._parameters[pname] = nn.Parameter(
                    torch.zeros(p.shape, dtype=p.dtype, device="cpu"),
                    requires_grad=False,
                )
                n_materialized += 1
        for bname in list(m._buffers):
            b = m._buffers[bname]
            if b is not None and b.is_meta:
                m._buffers[bname] = torch.zeros(b.shape, dtype=b.dtype, device="cpu")
                n_materialized += 1
    print(f"[load] materialized {n_materialized} remaining meta tensors as zeros",
          flush=True)

    # Monkey-patch MoE expert forward to use our packed unpack path
    n_patched = patch_moe_experts_forward(model)
    print(f"[load] patched {n_patched} MoE expert blocks to use packed forward",
          flush=True)
    return tok, model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True, type=Path)
    ap.add_argument("--prompt", default="Hello! The capital of Japan is")
    ap.add_argument("--max-new-tokens", type=int, default=5)
    args = ap.parse_args()

    tok, model = load_packed_checkpoint(args.ckpt)
    model.eval()

    # forward smoke
    print(f"\n[gen] prompt={args.prompt!r}", flush=True)
    ids = tok(args.prompt, return_tensors="pt").input_ids
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=args.max_new_tokens,
                             do_sample=False, pad_token_id=tok.eos_token_id)
    dt = time.time() - t0
    n_new = int(out.shape[1] - ids.shape[1])
    text = tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
    print(f"[gen] {n_new} tok in {dt:.1f}s = {n_new/max(dt,1e-9):.2f} tok/s",
          flush=True)
    print(f"[gen] output: {text!r}", flush=True)
    (args.ckpt / "packed_infer_smoke.json").write_text(json.dumps({
        "prompt": args.prompt,
        "completion": text,
        "n_new_tokens": n_new,
        "wall_sec": round(dt, 2),
        "tok_per_sec": round(n_new / max(dt, 1e-9), 3),
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
