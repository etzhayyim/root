"""State + config for Bonsai-pattern baien sibling production.

Per ADR-2605242000 §Phase 1. Each base candidate has its own
attestation pre-check (per ADR-2605241900 invariant table).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# Per ADR-2605242000 §Base-model feasibility. Only Apache-2.0 / MIT bases are
# auto-permitted; Llama-3.x requires explicit reviewer override (Llama
# Community License has 700M MAU clause we don't want by default).
BASE_CANDIDATES: dict[str, dict] = {
    "Zyphra/Zamba2-1.2B": {
        "arch": "ssm",
        "license": "apache-2.0",
        "params": 1_200_000_000,
        "fp16_gb": 2.4,
        "expected_1bit_gb": 0.17,
        "kv_at_16k_gb": 0.07,
        "kv_at_128k_gb": 0.5,
        "best_for": "long-context edge / mass-deploy (pretrain only — prefer -Instruct)",
    },
    "Zyphra/Zamba2-1.2B-Instruct": {
        "arch": "ssm",
        "license": "apache-2.0",
        "params": 1_200_000_000,
        "fp16_gb": 2.4,
        "expected_1bit_gb": 0.17,
        "kv_at_16k_gb": 0.07,
        "kv_at_128k_gb": 0.5,
        "best_for": "long-context edge / mass-deploy ★ (ultrachat_200k SFT + DPO; 3/5 microbench bf16 verified 2026-05-23)",
    },
    "Zyphra/Zamba2-2.7B-Instruct": {
        "arch": "ssm",
        "license": "apache-2.0",
        "params": 2_700_000_000,
        "fp16_gb": 5.4,
        "expected_1bit_gb": 0.38,
        "kv_at_16k_gb": 0.10,
        "kv_at_128k_gb": 0.7,
        "best_for": "long-context edge (Instruct variant)",
    },
    "Zyphra/Zamba2-7B-Instruct": {
        "arch": "ssm",
        "license": "apache-2.0",
        "params": 7_000_000_000,
        "fp16_gb": 14,
        "expected_1bit_gb": 1.0,
        "kv_at_16k_gb": 0.15,
        "kv_at_128k_gb": 1.2,
        "best_for": "quality + long-context edge ★ (Instruct variant)",
    },
    "Zyphra/Zamba2-2.7B": {
        "arch": "ssm",
        "license": "apache-2.0",
        "params": 2_700_000_000,
        "fp16_gb": 5.4,
        "expected_1bit_gb": 0.38,
        "kv_at_16k_gb": 0.10,
        "kv_at_128k_gb": 0.7,
        "best_for": "long-context edge",
    },
    "Zyphra/Zamba2-7B": {
        "arch": "ssm",
        "license": "apache-2.0",
        "params": 7_000_000_000,
        "fp16_gb": 14,
        "expected_1bit_gb": 1.0,
        "kv_at_16k_gb": 0.15,
        "kv_at_128k_gb": 1.2,
        "best_for": "quality + long-context edge ★",
    },
    "Qwen/Qwen3-8B": {
        "arch": "dense",
        "license": "apache-2.0",
        "params": 8_190_000_000,
        "fp16_gb": 16,
        "expected_1bit_gb": 1.15,                # Bonsai 8B measured
        "kv_at_16k_gb": 2.0,
        "kv_at_128k_gb": 16.0,                   # impractical
        "best_for": "quality @4k (Bonsai-proven)",
    },
    "Qwen/Qwen2.5-Coder-7B": {
        "arch": "dense",
        "license": "apache-2.0",
        "params": 7_000_000_000,
        "fp16_gb": 14,
        "expected_1bit_gb": 1.0,
        "kv_at_16k_gb": 2.0,
        "kv_at_128k_gb": 16.0,
        "best_for": "code specialist",
    },
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B": {
        "arch": "dense",
        "license": "mit",
        "params": 7_000_000_000,
        "fp16_gb": 14,
        "expected_1bit_gb": 1.0,
        "kv_at_16k_gb": 2.0,
        "kv_at_128k_gb": 16.0,
        "best_for": "reasoning specialist",
    },
    "Qwen/Qwen3.6-35B-A3B": {
        "arch": "moe-hybrid",
        "license": "apache-2.0",
        "params": 35_000_000_000,
        "active_params": 3_000_000_000,
        "fp16_gb": 72,
        "expected_1bit_gb": 4.4,
        "kv_at_16k_gb": 0.5,
        "kv_at_128k_gb": 4.0,
        "best_for": "server tier — MoE A3B sparse activation (8-of-256 experts)",
        "tier": "server",
        "tier_doc": "ADR-2605242100 4-tier ladder server tier; ADR-2605215000 Murakumo fleet compliant",
        "multimodal": True,
    },
    "mistralai/Mistral-7B-v0.3": {
        "arch": "dense",
        "license": "apache-2.0",
        "params": 7_000_000_000,
        "fp16_gb": 14,
        "expected_1bit_gb": 1.0,
        "kv_at_16k_gb": 2.0,
        "kv_at_128k_gb": 16.0,
        "best_for": "general 7B baseline",
    },
}


# Edge invariant ceilings from ADR-2605241900 §Decision (canonical SoT).
# Amended 2026-05-23 per ADR-2605242000 §Conflict — param ceiling raised to
# 12B since Bonsai 1-bit packing makes packed-weights the binding criterion
# (Prism ML 2026 Qwen3-8B → 1.15 GB packed verified). 12 B is the wall where
# 1-bit packing still fits 1.6 GB packed-weight ceiling.
EDGE_INVARIANT = {
    "trunk_params_max": 12_000_000_000,
    "packed_weights_gb_max": 1.6,
    "inference_4k_gb_max": 2.0,
    "inference_16k_gb_max": 2.5,
    "context_max_tokens": 16384,
    "encoder_cumulative_mb_max": 600,
}


QuantMethod = Literal["bonsai-w1", "bnb-nf4", "bnb-int8", "gptq-w4", "manual-stub"]
Phase = Literal["A", "B"]   # A = quantize-only, B = quantize + distill recovery


@dataclass(frozen=True)
class RosoConfig:
    base_model: str                                 # one of BASE_CANDIDATES keys
    quant_method: QuantMethod = "bonsai-w1"
    phase: Phase = "A"
    out_root: Path = field(default=Path("roso-out"))
    bench_dir: Path = field(default=Path("90-docs/baien"))

    # recovery (Phase B) knobs
    recovery_datasets: tuple[str, ...] = (
        "lordx64/reasoning-distill-opus-4-7-max-sft",
    )
    recovery_n_per_dataset: int = 5_000
    recovery_lr: float = 1e-4
    recovery_epochs: int = 1
    recovery_batch_size: int = 1

    # context window for attestation
    attestation_ctx_4k: int = 4096
    attestation_ctx_16k: int = 16384

    dry_run: bool = False


@dataclass
class RosoState:
    cfg: RosoConfig
    iter: int = 0

    base_local_path: Path | None = None         # after pull_base
    base_fp16_size_gb: float | None = None

    quantized_path: Path | None = None
    packed_weights_gb: float | None = None

    recovery_jsonl_path: Path | None = None
    recovery_final_loss: float | None = None

    # attestation results
    attestation_ram_4k_gb: float | None = None
    attestation_ram_16k_gb: float | None = None
    attestation_iphone14_first_token_ms: float | None = None  # may stay None pre-device
    attestation_passed: bool = False

    # final
    sibling_id: str | None = None               # e.g. roso-zamba-1.2b
    decision: Literal["pending", "commit", "retry", "abort"] = "pending"
    notes: list[str] = field(default_factory=list)


def derive_sibling_id(base_model: str, quant_method: QuantMethod, phase: Phase) -> str:
    """Map e.g. (Zyphra/Zamba2-1.2B, bonsai-w1, B) -> roso-zamba2-1.2b. roso = Bonsai-pattern 1-bit Mamba/Zamba family (this module); baien = ternary BitNet family (ADR-2605092350). Both share the edge-target invariant (ADR-2605241900)."""
    name = base_model.split("/")[-1].lower().replace("_", "-")
    return f"roso-{name}"
