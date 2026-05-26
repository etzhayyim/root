"""Quantization stage — load base fp16, walk modules, dispatch to chosen
quantizer (Bonsai-w1 default), write packed weights + manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

from .adapters.bonsai_quantizer import quantize_module
from .state import BASE_CANDIDATES, RosoState


def quantize(state: RosoState) -> RosoState:
    cfg = state.cfg
    state.notes.append(f"[quantize] method={cfg.quant_method} base={cfg.base_model}")

    spec = BASE_CANDIDATES.get(cfg.base_model)
    if spec is None:
        state.notes.append(f"[quantize] unknown base — abort")
        state.decision = "abort"
        return state

    out_dir = cfg.out_root / f"sibling-{state.iter:02d}-{cfg.base_model.replace('/', '__')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    if cfg.dry_run:
        # produce a deterministic dry-run manifest that downstream stages
        # (attestation, commit) can read.
        manifest = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "base_model": cfg.base_model,
            "method": cfg.quant_method,
            "phase": cfg.phase,
            "iter": state.iter,
            "expected_packed_gb": spec["expected_1bit_gb"],
            "expected_kv_4k_gb": float(spec["kv_at_16k_gb"]) / 4,
            "expected_kv_16k_gb": spec["kv_at_16k_gb"],
            "status": "dry-run",
            "TODO": "real quantize requires torch + transformers + base weights",
        }
        manifest_path = out_dir / "quantize_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        state.quantized_path = out_dir
        state.packed_weights_gb = float(spec["expected_1bit_gb"])
        state.notes.append(
            f"[quantize] dry-run — projected packed {spec['expected_1bit_gb']} GB → {out_dir}"
        )
        return state

    # ----- Real path -----
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if state.base_local_path is None:
        state.notes.append("[quantize] no base_local_path — pull stage must run first")
        state.decision = "abort"
        return state

    # Server tier / large bases: use shard-streaming quantizer (bypasses
    # transformers.from_pretrained which mmaps ALL shards at once and
    # blows past Windows paging file on 35B BF16 / 72 GB).
    tier = spec.get("tier", "edge")
    expected_load_gb = float(spec.get("fp16_gb", 0))
    if tier == "server" or expected_load_gb > 20:
        from .shard_quantize import shard_streaming_quantize
        state.notes.append(
            f"[quantize] server tier path: shard-streaming quantize "
            f"(bypasses transformers.from_pretrained mmap of all {expected_load_gb} GB)"
        )
        summary = shard_streaming_quantize(
            base_dir=state.base_local_path,
            out_dir=out_dir,
            method=cfg.quant_method,
        )
        # Save tokenizer to output (shard_streaming_quantize copies non-weight
        # files including tokenizer_config.json already; AutoTokenizer load
        # for save_pretrained is unnecessary but kept for parity with edge path)
        try:
            tok = AutoTokenizer.from_pretrained(str(state.base_local_path))
            tok.save_pretrained(str(out_dir))
        except Exception as e:
            state.notes.append(f"[quantize] tokenizer save skipped ({type(e).__name__})")
        # Persist manifest
        manifest = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "base_model": cfg.base_model,
            "method": cfg.quant_method,
            "phase": cfg.phase,
            "iter": state.iter,
            "actual_params": summary["total_params"],
            "actual_quantized_params": summary["quantized_params"],
            "actual_packed_gb": summary["expected_packed_gb_at_1bit"],
            "expected_packed_gb": spec["expected_1bit_gb"],
            "quantized_layers": summary["quantized_layers"],
            "skipped_layers": summary["skipped_layers"],
            "n_shards": summary["n_shards"],
            "total_time_sec": summary["total_time_sec"],
            "status": "shard-streaming naive-sign-quantize (server tier path)",
        }
        (out_dir / "quantize_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")
        state.quantized_path = out_dir
        state.packed_weights_gb = float(summary["expected_packed_gb_at_1bit"])
        state.notes.append(
            f"[quantize] shard-streaming done: "
            f"{summary['quantized_layers']} layers quantized / "
            f"{summary['skipped_layers']} skipped, "
            f"projected packed {summary['expected_packed_gb_at_1bit']:.2f} GB "
            f"(at true 1-bit), {summary['total_time_sec']:.1f}s total"
        )
        return state

    state.notes.append(f"[quantize] loading {state.base_local_path} (fp16, in-memory)")
    model = AutoModelForCausalLM.from_pretrained(
        str(state.base_local_path), dtype=torch.float16
    )
    tok = AutoTokenizer.from_pretrained(str(state.base_local_path))

    # Quantize each linear layer in-place so save_pretrained writes the
    # sign-quantized tensors. Phase B recovery loads this checkpoint as
    # the SFT student.
    state.notes.append("[quantize] walking modules with quantize_module(in_place=True)")
    result = quantize_module(model, method=cfg.quant_method, in_place=True)

    state.notes.append(f"[quantize] saving quantized checkpoint → {out_dir}")
    model.save_pretrained(str(out_dir))

    # Persist packed weights summary alongside the model.
    manifest = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_model": cfg.base_model,
        "method": cfg.quant_method,
        "phase": cfg.phase,
        "iter": state.iter,
        "actual_params": result["total_params"],
        "actual_packed_bytes": result["total_packed_bytes"],
        "actual_packed_gb": result["packed_gb"],
        "expected_packed_gb": spec["expected_1bit_gb"],
        "status": "naive-sign-quantize (TODO: replace with real Bonsai algorithm)",
    }
    manifest_path = out_dir / "quantize_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Also write tokenizer to the output dir so downstream tooling can load
    tok.save_pretrained(str(out_dir))

    state.quantized_path = out_dir
    state.packed_weights_gb = float(result["packed_gb"])
    state.notes.append(
        f"[quantize] packed {result['packed_gb']:.3f} GB across {result['total_params']:,} params"
    )
    return state


def manifest_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
