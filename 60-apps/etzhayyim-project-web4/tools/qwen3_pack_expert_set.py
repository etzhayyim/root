#!/usr/bin/env python3
"""
Download and pack one Qwen3-30B-A3B expert set into a WebGPU-friendly int4 bundle.

Bundle format:
  [4B header_len_le]
  [header_json]
  [binary_blob]

Header includes tensor metadata and offsets for q4 row-wise tensors:
  - scales: float32[rows]
  - data: packed int4 values (two values per byte)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

HF_BASE = "https://huggingface.co"
DEFAULT_REPO = "Qwen/Qwen3-30B-A3B"
DEFAULT_REVISION = "main"
EXPERTS_PER_SET = 4


def parse_layers(spec: str, max_layers: int) -> List[int]:
    values: List[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            parts = chunk.split("-", 1)
            start = int(parts[0])
            end = int(parts[1])
            if start > end:
                raise ValueError(f"invalid layer range: {chunk}")
            values.extend(range(start, end + 1))
        else:
            values.append(int(chunk))
    uniq = sorted(set(values))
    for layer in uniq:
        if layer < 0 or layer >= max_layers:
            raise ValueError(f"layer out of range: {layer} (max {max_layers - 1})")
    return uniq


def tensor_name(layer_id: int, expert_id: int, proj: str) -> str:
    return f"model.layers.{layer_id}.mlp.experts.{expert_id}.{proj}.weight"


def to_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TensorTarget:
    layer_id: int
    expert_id: int
    proj_name: str
    short_name: str
    tensor_name: str


class HFClient:
    def __init__(self, repo: str, revision: str, token: str | None, timeout_sec: int):
        self.repo = repo
        self.revision = revision
        self.timeout_sec = timeout_sec
        self.header_cache: Dict[str, Tuple[Dict[str, object], int]] = {}
        self.base_headers: Dict[str, str] = {
            "User-Agent": "etzhayyim-web4-qwen3-packer/1.0",
        }
        if token:
            self.base_headers["Authorization"] = f"Bearer {token}"

    def resolve_url(self, filename: str) -> str:
        return f"{HF_BASE}/{self.repo}/resolve/{self.revision}/{filename}"

    def download_file(self, filename: str, extra_headers: Dict[str, str] | None = None) -> bytes:
        headers = dict(self.base_headers)
        if extra_headers:
            headers.update(extra_headers)

        url = self.resolve_url(filename)
        req = urllib.request.Request(url=url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            detail = body.decode("utf-8", errors="ignore")[:240]
            raise RuntimeError(f"HTTP {e.code} for {url}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"request failed for {url}: {e}") from e

    def get_json(self, filename: str) -> Dict[str, object]:
        body = self.download_file(filename)
        return json.loads(body.decode("utf-8"))

    def get_bytes(self, filename: str, start: int, end: int) -> bytes:
        return self.download_file(filename, {"Range": f"bytes={start}-{end}"})

    def get_safetensors_header(self, filename: str) -> Tuple[Dict[str, object], int]:
        if filename in self.header_cache:
            return self.header_cache[filename]

        first = self.get_bytes(filename, 0, 7)
        if len(first) != 8:
            raise RuntimeError(f"failed to read safetensors prefix for {filename}")
        header_len = struct.unpack("<Q", first)[0]
        header_start = 8
        header_end = 8 + header_len - 1
        header_bytes = self.get_bytes(filename, header_start, header_end)
        header = json.loads(header_bytes.decode("utf-8"))
        data_offset = 8 + int(header_len)
        self.header_cache[filename] = (header, data_offset)
        return header, data_offset


def iter_decoded_values(raw: bytes, dtype: str) -> Iterable[float]:
    if dtype == "BF16":
        for (u16,) in struct.iter_unpack("<H", raw):
            u32 = int(u16) << 16
            yield struct.unpack("<f", struct.pack("<I", u32))[0]
        return

    if dtype == "F16":
        # Python's struct format 'e' decodes IEEE754 binary16 (half precision).
        for (v,) in struct.iter_unpack("<e", raw):
            yield float(v)
        return

    if dtype == "F32":
        for (v,) in struct.iter_unpack("<f", raw):
            yield float(v)
        return

    raise ValueError(f"unsupported tensor dtype: {dtype}")


def quantize_q4_row_from_raw(raw: bytes, dtype: str, rows: int, cols: int) -> Tuple[bytes, bytes]:
    expected = rows * cols
    values = list(iter_decoded_values(raw, dtype))
    if len(values) != expected:
        raise ValueError(f"shape mismatch: expected {expected} values, got {len(values)}")

    scales: List[float] = []
    packed = bytearray()
    pending_low_nibble: int | None = None

    for r in range(rows):
        start = r * cols
        end = start + cols
        row_values = values[start:end]
        max_abs = 0.0
        for v in row_values:
            a = abs(v)
            if a > max_abs:
                max_abs = a

        scale = max_abs / 7.0 if max_abs > 1e-8 else 1.0
        scales.append(scale)
        inv = 1.0 / scale

        for v in row_values:
            q = int(round(v * inv))
            if q < -8:
                q = -8
            elif q > 7:
                q = 7
            nibble = q & 0x0F
            if pending_low_nibble is None:
                pending_low_nibble = nibble
            else:
                packed.append(pending_low_nibble | (nibble << 4))
                pending_low_nibble = None

    if pending_low_nibble is not None:
        packed.append(pending_low_nibble)

    expected_packed = (expected + 1) // 2
    if len(packed) != expected_packed:
        raise ValueError(f"packed length mismatch: expected {expected_packed}, got {len(packed)}")

    scales_bytes = struct.pack(f"<{len(scales)}f", *scales)
    return scales_bytes, bytes(packed)


def build_targets(layers: Iterable[int], expert_ids: Iterable[int]) -> List[TensorTarget]:
    targets: List[TensorTarget] = []
    for layer_id in layers:
        for expert_id in expert_ids:
            targets.append(
                TensorTarget(
                    layer_id=layer_id,
                    expert_id=expert_id,
                    proj_name="gate_proj",
                    short_name="gate",
                    tensor_name=tensor_name(layer_id, expert_id, "gate_proj"),
                )
            )
            targets.append(
                TensorTarget(
                    layer_id=layer_id,
                    expert_id=expert_id,
                    proj_name="up_proj",
                    short_name="up",
                    tensor_name=tensor_name(layer_id, expert_id, "up_proj"),
                )
            )
            targets.append(
                TensorTarget(
                    layer_id=layer_id,
                    expert_id=expert_id,
                    proj_name="down_proj",
                    short_name="down",
                    tensor_name=tensor_name(layer_id, expert_id, "down_proj"),
                )
            )
    return targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Qwen3-30B-A3B expert tensors and pack one set into int4 bundle"
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help="HuggingFace repo id")
    parser.add_argument("--revision", default=DEFAULT_REVISION, help="Repo revision")
    parser.add_argument("--set-id", type=int, required=True, help="Expert set id (0-31)")
    parser.add_argument(
        "--layers",
        default="0-47",
        help="Layer spec, e.g. 0-47 or 0,1,2 (used for partial smoke builds)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output bundle path, e.g. data/qwen3-30b-a3b/experts/set-000.bin",
    )
    parser.add_argument(
        "--token",
        default="",
        help="HF token (optional, or set HF_TOKEN env var)",
    )
    parser.add_argument("--timeout-sec", type=int, default=120, help="HTTP timeout seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without downloading tensors")
    parser.add_argument(
        "--max-tensors",
        type=int,
        default=0,
        help="Optional limit for downloaded tensors (debug/smoke)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    set_id = args.set_id
    if set_id < 0 or set_id >= 32:
        print("set-id must be 0-31", file=sys.stderr)
        return 2

    token = (
        args.token.strip()
        or os.environ.get("HF_TOKEN", "").strip()
        or os.environ.get("HUGGINGFACE_HUB_TOKEN", "").strip()
        or None
    )

    client = HFClient(args.repo, args.revision, token, args.timeout_sec)

    config = client.get_json("config.json")
    num_layers = int(config.get("num_hidden_layers", 48))
    hidden_dim = int(config.get("hidden_size", 2048))
    moe_intermediate_dim = int(config.get("moe_intermediate_size", 768))
    num_experts = int(config.get("num_experts", 128))

    layers = parse_layers(args.layers, num_layers)
    expert_start = set_id * EXPERTS_PER_SET
    expert_ids = list(range(expert_start, expert_start + EXPERTS_PER_SET))
    for expert_id in expert_ids:
        if expert_id >= num_experts:
            print(f"expert id out of range: {expert_id}", file=sys.stderr)
            return 2

    index_data = client.get_json("model.safetensors.index.json")
    weight_map = index_data.get("weight_map")
    if not isinstance(weight_map, dict):
        print("invalid model index: missing weight_map", file=sys.stderr)
        return 2

    targets = build_targets(layers, expert_ids)
    if args.max_tensors > 0:
        targets = targets[: args.max_tensors]

    missing = [t.tensor_name for t in targets if t.tensor_name not in weight_map]
    if missing:
        print("missing tensor(s) in index:", file=sys.stderr)
        for name in missing[:20]:
            print(f"  - {name}", file=sys.stderr)
        return 2

    shard_counts: Dict[str, int] = {}
    for t in targets:
        shard = str(weight_map[t.tensor_name])
        shard_counts[shard] = shard_counts.get(shard, 0) + 1

    print(f"repo={args.repo}@{args.revision}")
    print(f"set_id={set_id} expert_ids={expert_ids} layers={layers[0]}..{layers[-1]} ({len(layers)} layers)")
    print(f"target_tensors={len(targets)} shards={len(shard_counts)}")
    if args.dry_run:
        for shard, count in sorted(shard_counts.items()):
            print(f"  {shard}: {count} tensors")
        return 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_blob = bytearray()
    tensor_entries: List[Dict[str, object]] = []
    source_shards = sorted(shard_counts.keys())

    for idx, target in enumerate(targets, start=1):
        shard = str(weight_map[target.tensor_name])
        header, data_offset = client.get_safetensors_header(shard)
        meta = header.get(target.tensor_name)
        if not isinstance(meta, dict):
            raise RuntimeError(f"tensor metadata missing for {target.tensor_name}")
        shape = meta.get("shape")
        dtype = meta.get("dtype")
        data_offsets = meta.get("data_offsets")

        if not isinstance(shape, list) or len(shape) != 2:
            raise RuntimeError(f"expected 2D tensor for {target.tensor_name}, got shape={shape}")
        if not isinstance(dtype, str):
            raise RuntimeError(f"missing dtype for {target.tensor_name}")
        if not isinstance(data_offsets, list) or len(data_offsets) != 2:
            raise RuntimeError(f"invalid data_offsets for {target.tensor_name}")

        rows = int(shape[0])
        cols = int(shape[1])
        start = data_offset + int(data_offsets[0])
        end = data_offset + int(data_offsets[1]) - 1

        print(
            f"[{idx:04d}/{len(targets):04d}] layer={target.layer_id} expert={target.expert_id} "
            f"{target.short_name} shard={shard}"
        )

        raw = client.get_bytes(shard, start, end)
        scales_bytes, packed = quantize_q4_row_from_raw(raw, dtype, rows, cols)

        scale_offset = len(data_blob)
        data_blob.extend(scales_bytes)
        data_offset_rel = len(data_blob)
        data_blob.extend(packed)

        tensor_entries.append(
            {
                "layer_id": target.layer_id,
                "expert_id": target.expert_id,
                "name": target.short_name,
                "shape": [rows, cols],
                "dtype": dtype,
                "quant": "q4_row",
                "scale_offset": scale_offset,
                "scale_length": len(scales_bytes),
                "data_offset": data_offset_rel,
                "data_length": len(packed),
            }
        )

    header_obj = {
        "format": "qwen3-moex-set-bundle",
        "version": 1,
        "model_id": args.repo,
        "revision": args.revision,
        "set_id": set_id,
        "expert_ids": expert_ids,
        "layers": layers,
        "hidden_dim": hidden_dim,
        "moe_intermediate_dim": moe_intermediate_dim,
        "quantization": {"bits": 4, "scheme": "row_symmetric"},
        "source_shards": source_shards,
        "tensor_count": len(tensor_entries),
        "generated_at": to_iso_utc(),
        "tensors": tensor_entries,
    }
    header_bytes = json.dumps(header_obj, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if len(header_bytes) > 0xFFFFFFFF:
        raise RuntimeError("header too large for u32 header_len")

    with output_path.open("wb") as fp:
        fp.write(struct.pack("<I", len(header_bytes)))
        fp.write(header_bytes)
        fp.write(data_blob)

    file_hash = hashlib.sha256()
    with output_path.open("rb") as fp:
        while True:
            chunk = fp.read(1024 * 1024)
            if not chunk:
                break
            file_hash.update(chunk)

    bundle_size = output_path.stat().st_size
    sidecar_path = output_path.with_suffix(output_path.suffix + ".meta.json")
    sidecar = {
        "bundle_path": str(output_path),
        "sha256": file_hash.hexdigest(),
        "size_bytes": bundle_size,
        "size_mb": round(bundle_size / (1024 * 1024), 3),
        "set_id": set_id,
        "expert_ids": expert_ids,
        "layers": layers,
        "tensor_count": len(tensor_entries),
        "generated_at": to_iso_utc(),
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"wrote bundle: {output_path}")
    print(f"size_mb={sidecar['size_mb']} sha256={sidecar['sha256']}")
    print(f"wrote metadata: {sidecar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
