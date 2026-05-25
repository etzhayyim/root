r"""Convert Bonsai-calibrated W_q + α (from bonsai_calibrate.py) into a
packed-bit safetensors checkpoint compatible with packed_infer.py.

Reads:
  --calibrated-dir/calibrated_W_q.safetensors  (W_q in bf16, values ±α)
  --calibrated-dir/calibrated_alphas.json      (per-row α magnitudes)
  --orig-ckpt/                                 (original bf16 base for skipped tensors + structure)

Writes:
  --out-dir/
    model-XXXXX-of-26.safetensors  (packed bits for calibrated Linears, bf16 passthrough for skipped)
    model.safetensors.index.json
    bit_pack_meta.json
    config.json, tokenizer files (copied from orig)
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import torch


def pack_bits_uint32(signs: torch.Tensor) -> torch.Tensor:
    flat = signs.reshape(-1)
    K = flat.numel()
    P = (K + 31) // 32
    K_padded = P * 32
    if K_padded > K:
        flat = torch.cat([flat, torch.zeros(K_padded - K, dtype=flat.dtype, device=flat.device)])
    bits = (flat > 0).to(torch.int32).reshape(P, 32)
    powers = (1 << torch.arange(32, device=flat.device, dtype=torch.int32))
    return (bits * powers).sum(dim=-1).to(torch.int32).contiguous()


def pack_calibrated_tensor(W_q: torch.Tensor) -> dict:
    """W_q is sign-quantized 2-D [d_out, d_in] with values in {-α_i, +α_i} per row.
    Recover α [d_out] = max(|W_q[i]|) per row, then bit-pack signs.
    """
    W_fp = W_q.to(torch.float32)
    alpha = W_fp.abs().max(dim=-1).values   # [d_out]
    signs = torch.sign(W_fp)
    # Pack: signs has shape [d_out, d_in]; pack last 2 dims into bits
    packed = pack_bits_uint32(signs).unsqueeze(0)   # [1, P]
    return {
        "packed_bits": packed,
        "alpha": alpha.to(torch.float16),
        "shape": list(W_q.shape),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrated-dir", required=True, type=Path)
    ap.add_argument("--orig-ckpt", required=True, type=Path,
                    help="Original bf16 base for shard structure + skipped tensors")
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    from safetensors.torch import load_file, save_file
    from safetensors import safe_open

    # Prefer per_shard/*.W_q.safetensors (incremental save survives crashes).
    # Fall back to single calibrated_W_q.safetensors if per_shard is empty.
    per_shard_dir = args.calibrated_dir / "per_shard"
    wq_tensors: dict[str, torch.Tensor] = {}
    if per_shard_dir.exists() and any(per_shard_dir.glob("*.W_q.safetensors")):
        shard_files = sorted(per_shard_dir.glob("*.W_q.safetensors"))
        print(f"[pack-calib] loading {len(shard_files)} per-shard W_q files...", flush=True)
        for sf in shard_files:
            chunk = load_file(str(sf))
            wq_tensors.update(chunk)
            print(f"  {sf.name}: +{len(chunk)} tensors (total={len(wq_tensors)})", flush=True)
    else:
        wq_path = args.calibrated_dir / "calibrated_W_q.safetensors"
        if not wq_path.exists():
            raise FileNotFoundError(
                f"Missing {per_shard_dir}/*.W_q.safetensors AND {wq_path}; "
                f"run bonsai_calibrate.py first")
        print(f"[pack-calib] loading single {wq_path.name}...", flush=True)
        wq_tensors = load_file(str(wq_path))
    print(f"[pack-calib] total {len(wq_tensors)} W_q tensors loaded", flush=True)

    # Walk original shards, swap calibrated tensors with packed, copy others.
    # Handle BOTH multi-shard (model.safetensors.index.json) AND single-file
    # (model.safetensors) checkpoints.
    index_path = args.orig_ckpt / "model.safetensors.index.json"
    if index_path.exists():
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        weight_map = idx["weight_map"]
    else:
        singles = list(args.orig_ckpt.glob("model*.safetensors"))
        if len(singles) != 1:
            raise RuntimeError(
                f"Need either index.json or single model.safetensors in {args.orig_ckpt}; "
                f"got {len(singles)} candidates")
        single = singles[0]
        with safe_open(str(single), framework="pt", device="cpu") as f:
            weight_map = {k: single.name for k in f.keys()}
        idx = {"metadata": {}, "weight_map": weight_map}
    shards_to_tensors: dict[str, list[str]] = {}
    for tname, shard in weight_map.items():
        shards_to_tensors.setdefault(shard, []).append(tname)

    # Map base ORIG tensor name -> W_q via SUFFIX matching (robust to text-only
    # vs multimodal prefix divergence: Bonsai hooks see `model.layers.X.*`
    # while multimodal checkpoint stores `model.language_model.layers.X.*`).
    # For each W_q key, find an ORIG name that ends with the same suffix.
    calibrated_map: dict[str, torch.Tensor] = {}
    orig_names_set = set(weight_map.keys())
    unmatched = []
    for key, t in wq_tensors.items():
        # key: "model.layers.6.linear_attn.in_proj_a.W_q"
        # suffix without "model." prefix: "layers.6.linear_attn.in_proj_a.weight"
        body = key.rsplit(".W_q", 1)[0]
        if body.startswith("model."):
            sub = body[len("model."):]
        else:
            sub = body
        target = sub + ".weight"
        # Try direct match first
        if f"model.{target}" in orig_names_set:
            calibrated_map[f"model.{target}"] = t
            continue
        # Try multimodal prefix
        mm = f"model.language_model.{target}"
        if mm in orig_names_set:
            calibrated_map[mm] = t
            continue
        # Fallback: scan for any orig name ending with `.{target}`
        suffix = "." + target
        hits = [n for n in orig_names_set if n.endswith(suffix)]
        if len(hits) == 1:
            calibrated_map[hits[0]] = t
        elif len(hits) > 1:
            print(f"  WARN ambiguous: {key} matches {hits}", flush=True)
            calibrated_map[hits[0]] = t
        else:
            unmatched.append(key)
    print(f"[pack-calib] mapped {len(calibrated_map)}/{len(wq_tensors)} W_q -> orig "
          f"(unmatched={len(unmatched)})", flush=True)
    if unmatched[:5]:
        print(f"  first unmatched: {unmatched[:5]}", flush=True)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    new_weight_map: dict[str, str] = {}
    pack_meta: dict[str, dict] = {}
    n_packed = 0
    n_copied = 0
    t0_all = time.time()
    for shard_idx, (shard_file, tnames) in enumerate(shards_to_tensors.items()):
        t0 = time.time()
        new_tensors: dict[str, torch.Tensor] = {}
        with safe_open(str(args.orig_ckpt / shard_file), framework="pt", device="cpu") as f:
            for tname in f.keys():
                t = f.get_tensor(tname).clone()
                if tname in calibrated_map:
                    # Use Bonsai-calibrated W_q instead
                    packed = pack_calibrated_tensor(calibrated_map[tname])
                    new_tensors[f"{tname}.packed_bits"] = packed["packed_bits"]
                    new_tensors[f"{tname}.alpha"] = packed["alpha"]
                    new_weight_map[f"{tname}.packed_bits"] = shard_file
                    new_weight_map[f"{tname}.alpha"] = shard_file
                    pack_meta[tname] = {"shape": packed["shape"], "ndim": t.ndim, "n_experts": 1}
                    n_packed += 1
                else:
                    new_tensors[tname] = t
                    new_weight_map[tname] = shard_file
                    n_copied += 1
        save_file(new_tensors, str(args.out_dir / shard_file))
        dt = time.time() - t0
        sz = (args.out_dir / shard_file).stat().st_size / 1e9
        print(f"  [{shard_idx+1}/{len(shards_to_tensors)}] {shard_file}: {sz:.2f} GB in {dt:.1f}s "
              f"(packed={n_packed} copied={n_copied})", flush=True)

    (args.out_dir / "model.safetensors.index.json").write_text(json.dumps({
        "metadata": idx.get("metadata", {}),
        "weight_map": new_weight_map,
    }, indent=2), encoding="utf-8")
    (args.out_dir / "bit_pack_meta.json").write_text(json.dumps(pack_meta, indent=2), encoding="utf-8")
    # Copy config + tokenizer
    for f in args.orig_ckpt.iterdir():
        if f.is_file() and not f.name.endswith(".safetensors") and f.name != "model.safetensors.index.json":
            shutil.copy2(f, args.out_dir / f.name)
    total = time.time() - t0_all
    print(f"\n[pack-calib] DONE in {total:.1f}s — packed {n_packed} calibrated + copied {n_copied} original tensors")
    print(f"             out: {args.out_dir}")


if __name__ == "__main__":
    main()
