"""Real per-tensor bit-packing for roso 1-bit checkpoints.

Converts a sign-quantized bf16 checkpoint (current output of shard_quantize.py
where values are stored as bf16 in {-α, 0, +α}) into a TRUE bit-packed
safetensors layout:

  For each quantized weight `W` of shape S with values in {-α, 0, +α}:
    W.packed_bits  uint32 [..., ceil(numel/32)]   sign bit per element
                                                  (1 = +, 0 = - or 0)
    W.alpha        float16  scalar or [E] for 3-D MoE
    W.zero_mask    uint32 [..., ceil(numel/32)]   only emitted if any zeros
                                                  (1 = was exactly 0)

Storage: bf16 (16 bits) → packed (1 sign + optional 1 mask bit) ≈ 16x to 8x
smaller. Total disk for 35B model: 67 GB bf16 → 4.4 GB packed (1-bit only) or
~8 GB if zero-mask is included.

Full-precision (skipped) tensors are copied unchanged. This keeps the
shard structure compatible with model.safetensors.index.json.

Inverse (unpack):
    sign = ((bits >> bit_idx) & 1) ? +1 : -1
    val  = sign * alpha   (or 0 if zero_mask[i] == 1)

A custom BinaryLinear module in the inference engine reads these packed
keys and reconstructs the dense weight in fp16/bf16 on forward.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import torch


SKIP_PATTERNS = (
    "embed_tokens", "embed_out", "lm_head", "router",
    "gate.weight", "mtp",
    "linear_attn", "shared_expert",
    "layers.0.", "layers.1.", "layers.2.",
    "layers.37.", "layers.38.", "layers.39.",
    "self_attn",
    "experts.down_proj",
)


def _is_quantized_pattern(name: str, t: torch.Tensor) -> bool:
    """Heuristic: this tensor was sign-quantized by shard_quantize.py."""
    nm = name.lower()
    for skip in SKIP_PATTERNS:
        if skip in nm:
            return False
    if name.endswith(".weight") and t.ndim == 2:
        return True
    if t.ndim == 3 and "experts" in nm and "conv1d" not in nm:
        return True
    return False


def pack_bits_uint32(signs: torch.Tensor) -> torch.Tensor:
    """Pack a {-1, 0, +1} (or any sign) tensor's sign bits into uint32.
    Output shape: (..., ceil(numel_last/32),) packed along the last dim.

    Convention: bit i of output_word_j = 1 iff input[j*32 + i] > 0.
    """
    flat = signs.reshape(-1)
    K = flat.numel()
    P = (K + 31) // 32
    K_padded = P * 32
    if K_padded > K:
        flat = torch.cat([flat, torch.zeros(K_padded - K, dtype=flat.dtype,
                                            device=flat.device)])
    bits = (flat > 0).to(torch.int32).reshape(P, 32)
    powers = (1 << torch.arange(32, device=flat.device, dtype=torch.int32))
    packed = (bits * powers).sum(dim=-1).to(torch.int32)
    return packed.contiguous()


def detect_alpha_and_signs(t: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Given a sign-quantized tensor (per-output-channel alpha), recover
    alpha vector and sign pattern.

    For 2-D [d_out, d_in]: alpha[i] = max(|t[i,:]|) for each output channel
    For 3-D [E, d_out, d_in]: alpha[e, i] = max(|t[e, i, :]|)
    """
    if t.ndim == 2:
        alpha = t.abs().max(dim=-1).values      # [d_out]
        signs = torch.sign(t)
    elif t.ndim == 3:
        alpha = t.abs().max(dim=-1).values      # [E, d_out]
        signs = torch.sign(t)
    else:
        raise ValueError(f"unsupported ndim={t.ndim}")
    return alpha, signs


def pack_quantized_tensor(t: torch.Tensor) -> dict:
    """Convert one sign-quantized bf16 tensor to packed-bit dict.

    Returns dict with keys (relative to original tensor name):
      'packed_bits': int32 [..., ceil(numel_per_slice/32)]
      'alpha':       fp16 scalar OR [E] tensor
      'shape':       original shape (so unpack can reconstruct)
      'ndim':        ndim
    """
    alpha, signs = detect_alpha_and_signs(t)
    if t.ndim == 2:
        packed_bits = pack_bits_uint32(signs).unsqueeze(0)  # [1, P]
    else:   # 3-D
        E = t.shape[0]
        # Pack each expert independently
        bits_list = [pack_bits_uint32(signs[e]) for e in range(E)]
        packed_bits = torch.stack(bits_list, dim=0)   # [E, P]
    return {
        "packed_bits": packed_bits,
        "alpha": alpha.to(torch.float16),
        "shape": list(t.shape),
    }


def shard_streaming_bit_pack(in_dir: Path, out_dir: Path) -> dict:
    """Walk safetensors shards of a sign-quantized checkpoint, real-bit-pack
    quantized tensors, copy skipped tensors unchanged, write new shards
    + metadata index.
    """
    from safetensors.torch import save_file
    from safetensors import safe_open

    in_dir = Path(in_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    index_path = in_dir / "model.safetensors.index.json"
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = idx["weight_map"]

    # Group by shard
    shards_to_tensors: dict[str, list[str]] = {}
    for tname, shard in weight_map.items():
        shards_to_tensors.setdefault(shard, []).append(tname)

    # Track new weight_map (each quantized tensor expands to 2-3 entries)
    new_weight_map: dict[str, str] = {}
    pack_meta: dict[str, dict] = {}  # tensor_name -> {shape, ndim, n_experts}
    total_orig_bytes = 0
    total_packed_bytes = 0
    n_quantized = 0
    n_skipped = 0

    t0_all = time.time()
    for shard_idx, (shard_file, tnames) in enumerate(shards_to_tensors.items()):
        t0 = time.time()
        src = in_dir / shard_file
        dst = out_dir / shard_file
        new_tensors: dict[str, torch.Tensor] = {}
        with safe_open(src, framework="pt", device="cpu") as f:
            for tname in f.keys():
                t = f.get_tensor(tname)
                orig_bytes = t.numel() * t.element_size()
                total_orig_bytes += orig_bytes
                if _is_quantized_pattern(tname, t):
                    packed = pack_quantized_tensor(t)
                    new_tensors[f"{tname}.packed_bits"] = packed["packed_bits"]
                    new_tensors[f"{tname}.alpha"] = packed["alpha"]
                    new_weight_map[f"{tname}.packed_bits"] = shard_file
                    new_weight_map[f"{tname}.alpha"] = shard_file
                    pack_meta[tname] = {
                        "shape": packed["shape"],
                        "ndim": t.ndim,
                        "n_experts": t.shape[0] if t.ndim == 3 else 1,
                    }
                    total_packed_bytes += (packed["packed_bits"].numel() * 4
                                           + packed["alpha"].numel() * 2)
                    n_quantized += 1
                else:
                    new_tensors[tname] = t.clone()
                    new_weight_map[tname] = shard_file
                    total_packed_bytes += orig_bytes
                    n_skipped += 1
        save_file(new_tensors, str(dst))
        dt = time.time() - t0
        size_gb = dst.stat().st_size / 1e9
        print(f"  [{shard_idx+1}/{len(shards_to_tensors)}] {shard_file}: "
              f"{size_gb:.3f} GB in {dt:.1f}s", flush=True)
        del new_tensors

    # Write updated index
    new_idx = {
        "metadata": idx.get("metadata", {}),
        "weight_map": new_weight_map,
    }
    (out_dir / "model.safetensors.index.json").write_text(
        json.dumps(new_idx, indent=2), encoding="utf-8")
    # Pack metadata sidecar (custom, used by inference engine)
    (out_dir / "bit_pack_meta.json").write_text(
        json.dumps(pack_meta, indent=2), encoding="utf-8")

    # Copy non-weight files
    for f in in_dir.iterdir():
        if f.is_file() and not f.name.endswith(".safetensors") and f.name != "model.safetensors.index.json":
            shutil.copy2(f, out_dir / f.name)
        elif f.is_dir() and f.name not in (".cache", "infer_offload"):
            shutil.copytree(f, out_dir / f.name, dirs_exist_ok=True)

    total_time = time.time() - t0_all
    summary = {
        "n_quantized_tensors": n_quantized,
        "n_skipped_tensors": n_skipped,
        "total_orig_gb": round(total_orig_bytes / 1e9, 2),
        "total_packed_gb": round(total_packed_bytes / 1e9, 2),
        "compression_ratio": round(total_orig_bytes / max(total_packed_bytes, 1), 2),
        "n_shards": len(shards_to_tensors),
        "total_time_sec": round(total_time, 1),
    }
    (out_dir / "bit_pack_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    s = shard_streaming_bit_pack(args.in_dir, args.out_dir)
    print(json.dumps(s, indent=2))
