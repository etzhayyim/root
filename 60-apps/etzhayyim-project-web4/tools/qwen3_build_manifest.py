#!/usr/bin/env python3
"""
Build a control-plane manifest from locally packed expert set bundles.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build qwen3 set manifest from local bundles")
    parser.add_argument(
        "--bundles-dir",
        required=True,
        help="Directory containing set-XXX.bin files",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Manifest JSON output path",
    )
    parser.add_argument(
        "--blob-endpoint",
        default="https://etzhayyim-static-sites.jp-osa-1.linodeobjects.com",
        help="Public blob endpoint",
    )
    parser.add_argument(
        "--blob-prefix",
        default="models/qwen3-30b-a3b/experts",
        help="Object key prefix for set bundles",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Manifest version",
    )
    parser.add_argument(
        "--model-id",
        default="etzhayyim/etzhayyim-distributed-moe-260222",
        help="Model identifier to publish in manifest",
    )
    parser.add_argument(
        "--num-layers",
        type=int,
        default=48,
        help="Total model layers",
    )
    parser.add_argument(
        "--num-experts",
        type=int,
        default=128,
        help="Total experts",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=8,
        help="Router top-k experts",
    )
    parser.add_argument(
        "--experts-per-device",
        type=int,
        default=4,
        help="Experts served per browser device",
    )
    parser.add_argument(
        "--num-sets",
        type=int,
        default=32,
        help="Total expert sets",
    )
    parser.add_argument(
        "--host-attention-key",
        default="models/qwen3-30b-a3b/host/attention.safetensors",
        help="S3 object key for host-side attention weights",
    )
    parser.add_argument(
        "--host-router-key",
        default="models/qwen3-30b-a3b/host/router.safetensors",
        help="S3 object key for host-side router weights",
    )
    parser.add_argument(
        "--host-embedding-key",
        default="models/qwen3-30b-a3b/host/embedding.safetensors",
        help="S3 object key for host-side embedding weights",
    )
    parser.add_argument(
        "--host-total-size-mb",
        type=float,
        default=2400.0,
        help="Host-side weight total size (MB)",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            chunk = fp.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_bundle_header(path: Path) -> Dict[str, object]:
    with path.open("rb") as fp:
        prefix = fp.read(4)
        if len(prefix) != 4:
            raise RuntimeError(f"{path}: invalid bundle (short header_len)")
        header_len = struct.unpack("<I", prefix)[0]
        header_bytes = fp.read(header_len)
        if len(header_bytes) != header_len:
            raise RuntimeError(f"{path}: invalid bundle (short header)")
        header = json.loads(header_bytes.decode("utf-8"))
    return header


def main() -> int:
    args = parse_args()
    bundles_dir = Path(args.bundles_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(bundles_dir.glob("set-*.bin"))
    if not files:
        raise RuntimeError(f"no bundles found in {bundles_dir}")

    sets: List[Dict[str, object]] = []
    hidden_dim = 2048
    moe_intermediate_dim = 768
    quant_bits = 4
    all_layers = set()

    for path in files:
        header = load_bundle_header(path)
        set_id = int(header["set_id"])
        expert_ids = [int(x) for x in header["expert_ids"]]
        layers = [int(x) for x in header.get("layers", [])]
        all_layers.update(layers)
        hidden_dim = int(header.get("hidden_dim", hidden_dim))
        moe_intermediate_dim = int(header.get("moe_intermediate_dim", moe_intermediate_dim))
        quant_bits = int(header.get("quantization", {}).get("bits", quant_bits))

        file_size = path.stat().st_size
        checksum = sha256_file(path)
        sets.append(
            {
                "set_id": set_id,
                "expert_ids": expert_ids,
                "blob_key": f"{args.blob_prefix}/{path.name}",
                "size_mb": round(file_size / (1024 * 1024), 3),
                "checksum_sha256": checksum,
                "tensor_count": int(header.get("tensor_count", 0)),
                "layers_covered": layers,
            }
        )

    sets.sort(key=lambda x: int(x["set_id"]))

    manifest = {
        "model_id": args.model_id,
        "version": args.version,
        "blob_endpoint": args.blob_endpoint,
        "num_layers": args.num_layers,
        "num_experts": args.num_experts,
        "hidden_dim": hidden_dim,
        "moe_intermediate_dim": moe_intermediate_dim,
        "top_k": args.top_k,
        "experts_per_device": args.experts_per_device,
        "num_sets": args.num_sets,
        "quant_bits": quant_bits,
        "sets_available": len(sets),
        "layers_available": sorted(all_layers),
        "host_weights": {
            "attention_blob_key": args.host_attention_key,
            "router_blob_key": args.host_router_key,
            "embedding_blob_key": args.host_embedding_key,
            "total_size_mb": args.host_total_size_mb,
        },
        "sets": sets,
    }

    output_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"wrote manifest: {output_path} (sets={len(sets)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
