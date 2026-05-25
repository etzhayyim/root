"""Shard-streaming bit-packed sign quantize for large MoE / server-tier bases.

Bypasses transformers' `from_pretrained` which mmaps ALL safetensors shards
at once (blows past Windows paging file on 35B BF16 / 72 GB). Instead:

  1. Read `model.safetensors.index.json` (tensor name -> shard file map)
  2. For each shard one at a time:
       - Open via safetensors.safe_open (mmap just this shard)
       - For each tensor: load -> if 2D Linear weight, sign-quantize -> save
       - Close shard (mmap released)
  3. Copy index.json + tokenizer / config / preprocessor files unchanged

Peak virtual memory = largest single shard (~4 GB), not full model (72 GB).
Works on Windows ROCm without paging file expansion.

Quantize rule: any 2-D tensor whose name ends with `.weight` AND is NOT an
embedding / lm_head / router gets sign-quantized in-place:
  alpha = mean(|W|)
  W_new = sign(W) * alpha   (stored at original dtype bf16/fp16)

Embedding tables and the router (gate) are critical for MoE quality and
stay full-precision. Optionally, lm_head can also stay fp (per BitNet
practice).
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import torch


# Tensor name patterns that should STAY full-precision
SKIP_PATTERNS = (
    "embed_tokens",       # input embedding
    "embed_out",          # tied
    "lm_head",            # output projection (BitNet keeps it fp)
    "router",             # MoE router/gate weights
    "gate.weight",        # MoE gate (top-k routing)
    "mtp",                # multi-token prediction head
    # 2026-05-24 kaizen iter 1: Mamba SSM dynamics break under naive sign
    "linear_attn",
    # MoE shared expert — high-frequency path, keep full. Small (~0.4 GB).
    "shared_expert",
    # First + last 3 decoder layers full (extended Bonsai recipe — naive sign
    # without activation calibration needs wider boundary buffer).
    "layers.0.", "layers.1.", "layers.2.",
    "layers.37.", "layers.38.", "layers.39.",
    # 2026-05-24 kaizen iter 2: full_attention layers (every 4th) loop on
    # quantize. self_attn weights are critical for attention scoring.
    "self_attn",
    # 2026-05-24 kaizen iter 3: MoE down_proj (intermediate -> hidden) propagates
    # noise back to residual stream. Keep full-precision; quantize only gate_up_proj.
    "experts.down_proj",
)


def _should_quantize(name: str, tensor: torch.Tensor) -> bool:
    """True if this tensor is a Linear-like weight to sign-quantize.

    Covers:
      - 2-D nn.Linear weights (q/k/v/o, etc.)
      - 3-D MoE stacked expert weights `[num_experts, d_in, d_out]`
        (gate_up_proj / down_proj in Qwen MoE family)

    Excludes embeddings, lm_head, router/gate, RMSNorm, conv1d (Mamba SSM).
    """
    nm = name.lower()
    for skip in SKIP_PATTERNS:
        if skip in nm:
            return False
    # 2-D Linear weights
    if name.endswith(".weight") and tensor.ndim == 2:
        return True
    # 3-D MoE expert stacked weights (NOT conv1d which is also 3-D)
    # Qwen MoE convention: gate_up_proj / down_proj as [E, d_in, d_out]
    # (no trailing .weight in this layout — the parameter IS the tensor)
    if tensor.ndim == 3 and "experts" in nm and "conv1d" not in nm:
        return True
    return False


def _sign_quantize_tensor(t: torch.Tensor) -> torch.Tensor:
    """Sign-quantize a 2-D or 3-D tensor in-place semantically.

    - 2-D [d_out, d_in]: PER-OUTPUT-CHANNEL alpha = mean(|W[i,:]|) for each i.
                          ~1000× more granular than per-tensor; quality boost.
    - 3-D [E, d_out, d_in]: per-(expert, output_channel) alpha = mean over d_in.
                            Each of E experts × d_out output channels has own scale.
    Returns new tensor in original dtype.
    """
    orig_dtype = t.dtype
    t_fp = t.to(torch.float32)
    # Empirical α scale factor: 0.5 dampens reconstruction overshoot for
    # naive sign-quantize without calibration. Real Bonsai paper computes
    # this via per-layer optimization; we approximate with a global 0.5.
    ALPHA_SCALE = 0.5
    if t_fp.ndim == 2:
        # Per-output-channel alpha. t shape [d_out, d_in] -> alpha [d_out, 1]
        alphas = t_fp.abs().mean(dim=-1, keepdim=True) * ALPHA_SCALE
        q = torch.sign(t_fp) * alphas
    elif t_fp.ndim == 3:
        # Per-(expert, output_channel) alpha. shape [E, d_out, d_in]
        # alpha shape [E, d_out, 1]; broadcast over d_in
        alphas = t_fp.abs().mean(dim=-1, keepdim=True) * ALPHA_SCALE
        q = torch.sign(t_fp) * alphas
    else:
        raise ValueError(f"unsupported ndim={t_fp.ndim} for sign-quantize")
    return q.to(orig_dtype)


def shard_streaming_quantize(base_dir: Path, out_dir: Path,
                              method: str = "bonsai-w1",
                              dtype_override: str | None = None,
                              ) -> dict:
    """Walk safetensors shards, sign-quantize Linear weights in-place,
    write to out_dir. Returns summary dict.
    """
    from safetensors.torch import save_file
    from safetensors import safe_open

    base_dir = Path(base_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Find shard index
    index_path = base_dir / "model.safetensors.index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        weight_map: dict[str, str] = idx["weight_map"]
        # Group tensors by shard
        shards_to_tensors: dict[str, list[str]] = {}
        for tname, shard_file in weight_map.items():
            shards_to_tensors.setdefault(shard_file, []).append(tname)
    else:
        # Single-file model
        single = next(base_dir.glob("*.safetensors"))
        with safe_open(single, framework="pt", device="cpu") as f:
            shards_to_tensors = {single.name: list(f.keys())}

    print(f"[shard-quant] {len(shards_to_tensors)} shards, "
          f"{sum(len(v) for v in shards_to_tensors.values())} tensors total",
          flush=True)

    # Per-shard processing
    total_params = 0
    total_quantized_params = 0
    total_quantized_layers = 0
    total_skipped_layers = 0
    sizes_summary = []

    t0_all = time.time()
    for shard_idx, (shard_file, tnames) in enumerate(shards_to_tensors.items()):
        t0 = time.time()
        src = base_dir / shard_file
        dst = out_dir / shard_file
        new_tensors: dict[str, torch.Tensor] = {}
        with safe_open(src, framework="pt", device="cpu") as f:
            for tname in f.keys():
                t = f.get_tensor(tname)
                total_params += t.numel()
                if _should_quantize(tname, t):
                    new_tensors[tname] = _sign_quantize_tensor(t)
                    total_quantized_params += t.numel()
                    total_quantized_layers += 1
                else:
                    new_tensors[tname] = t.clone()
                    total_skipped_layers += 1
        # Save shard
        save_file(new_tensors, str(dst))
        dt = time.time() - t0
        size_gb = dst.stat().st_size / 1e9
        sizes_summary.append({"shard": shard_file, "size_gb": round(size_gb, 2),
                              "time_sec": round(dt, 1)})
        print(f"  [{shard_idx+1}/{len(shards_to_tensors)}] {shard_file}: "
              f"{size_gb:.2f} GB in {dt:.1f}s "
              f"({len(new_tensors)} tensors)", flush=True)
        del new_tensors

    # Copy non-weight files (config, tokenizer, etc.)
    for f in base_dir.iterdir():
        if f.is_file() and not f.name.endswith(".safetensors"):
            shutil.copy2(f, out_dir / f.name)
        elif f.is_dir() and f.name not in (".cache",):
            shutil.copytree(f, out_dir / f.name, dirs_exist_ok=True)

    total_time = time.time() - t0_all

    summary = {
        "method": method,
        "total_params": total_params,
        "quantized_params": total_quantized_params,
        "quantize_ratio": round(total_quantized_params / max(total_params, 1), 4),
        "quantized_layers": total_quantized_layers,
        "skipped_layers": total_skipped_layers,
        "n_shards": len(shards_to_tensors),
        "shards": sizes_summary,
        "total_time_sec": round(total_time, 1),
        "expected_packed_gb_at_1bit": total_quantized_params / 8 / 1e9,
        "note": (
            "naive-sign-quantize stored as original dtype (bf16/fp16). "
            "Embedding + lm_head + router/gate kept full-precision. "
            "TODO: replace with real Bonsai per-layer algorithm + bit-packed storage."
        ),
    }
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--method", default="bonsai-w1")
    args = ap.parse_args()
    s = shard_streaming_quantize(args.base_dir, args.out_dir, args.method)
    print(json.dumps(s, indent=2))
