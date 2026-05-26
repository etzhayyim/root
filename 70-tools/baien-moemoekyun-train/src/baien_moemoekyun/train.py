"""train.py — R1.4 train invocation per ADR-2605262100.

Loads BitNet 2B + applies BaienMoEResidual surgery + freezes backbone + trains
router + experts + alpha on coding corpus via trl SFTTrainer.

Run:
    python -m baien_moemoekyun.train --config configs/r1.4-iter01.yaml

R1.3 smoke (100 ex × 10 steps):
    python -m baien_moemoekyun.train --config configs/r1.4-iter01.yaml --override training.num_train_epochs=0.001 corpus.total_examples=100

Status: R1.1-R1.2 implementation skeleton. R1.3 smoke requires actual HF dataset
loading + trl SFTTrainer integration (deliverable: this file, fully realized).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch
import yaml

# Add src/ to path when running as module
sys.path.insert(0, str(Path(__file__).parent.parent))

from baien_moemoekyun import (  # noqa: E402
    attach_moe_to_model,
    freeze_backbone_verify,
)
from baien_moemoekyun.attach import collect_aux_losses  # noqa: E402

logger = logging.getLogger("baien-moemoekyun-train")


def env_hash() -> str:
    """G15: deterministic hash of runtime env for reproducibility."""
    parts = [
        f"torch={torch.__version__}",
        f"cuda={torch.cuda.is_available()}",
    ]
    if torch.cuda.is_available():
        parts.append(f"gpu={torch.cuda.get_device_name(0)}")
        if hasattr(torch.version, "hip") and torch.version.hip:
            parts.append(f"rocm={torch.version.hip}")
        elif torch.version.cuda:
            parts.append(f"cuda={torch.version.cuda}")
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return h


def load_config(path: str) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def resolve_moe_layers(spec: str | list[int], n_layers: int) -> list[int]:
    """Convert 'last_25_percent' / 'every_4th' / explicit list to indices."""
    if isinstance(spec, list):
        return spec
    if spec == "last_25_percent":
        start = int(n_layers * 0.75)
        return list(range(start, n_layers))
    if spec == "every_4th":
        return list(range(3, n_layers, 4))
    if spec == "last_50_percent":
        start = int(n_layers * 0.50)
        return list(range(start, n_layers))
    raise ValueError(f"Unknown moe_layers spec: {spec}")


def build_model(config: dict) -> tuple[Any, Any, dict]:
    """Returns (model, tokenizer, installed_moe_wrappers)."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = config["base_model"]
    logger.info("Loading base model: %s", base)
    tokenizer = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    n_layers = model.config.num_hidden_layers
    moe_layers = resolve_moe_layers(config["moe"]["moe_layers"], n_layers)
    logger.info("Installing MoE on %d layers: %s", len(moe_layers), moe_layers)

    inner_model = model.model if hasattr(model, "model") else model
    installed = attach_moe_to_model(
        inner_model,
        moe_layer_indices=moe_layers,
        hidden_size=model.config.hidden_size,
        intermediate_size=model.config.intermediate_size,
        num_experts=config["moe"]["num_experts"],
        top_k=config["moe"]["top_k"],
        expert_hidden_ratio=config["moe"]["expert_hidden_ratio"],
        alpha_init=config["moe"]["alpha_init"],
        alpha_init_jitter=config["moe"]["alpha_init_jitter"],
    )

    # G5/G8 verify
    summary = freeze_backbone_verify(inner_model, installed)
    logger.info("Param summary: %s", summary)
    return model, tokenizer, installed


def build_dataset(config: dict, tokenizer):
    """Load + sample + tokenize the R1.4 corpus mix.

    R1.0 skeleton: only handles Tier A datasets already pinned via IPFS.
    PENDING_W3/W4/W5 sources are SKIPPED with WARN (R2.0 deliverable to wire those).
    """
    from datasets import load_dataset, concatenate_datasets

    total = config["corpus"]["total_examples"]
    seed = config["corpus"]["sampling_seed"]
    parts = []
    for source in config["corpus"]["sources"]:
        if str(source.get("cid", "")).startswith("PENDING_"):
            logger.warning("SKIP source '%s' (CID %s pending). Adjust proportions when wired.", source["name"], source["cid"])
            continue
        n = int(total * source["proportion"])
        logger.info("Loading %s: %d examples (license=%s tier=%s)", source["name"], n, source["license"], source["tier"])
        # HF dataset id from name
        ds = load_dataset(source["name"], split="train", streaming=False)
        ds = ds.shuffle(seed=seed).select(range(min(n, len(ds))))
        parts.append(ds)

    if not parts:
        raise RuntimeError("No dataset sources available (all PENDING). Wire W3/W4/W5 first.")

    combined = concatenate_datasets(parts).shuffle(seed=seed)
    logger.info("Combined corpus: %d examples", len(combined))
    return combined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--override", nargs="*", default=[],
                        help="key=value overrides, e.g., training.num_train_epochs=0.001")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    config = load_config(args.config)
    # Apply overrides (simple dot-notation, no nested list support)
    for ov in args.override:
        if "=" not in ov:
            continue
        key, value = ov.split("=", 1)
        d = config
        parts = key.split(".")
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        try:
            value = yaml.safe_load(value)
        except Exception:
            pass
        d[parts[-1]] = value
        logger.info("Override applied: %s = %s", key, value)

    # ─── R1.0 reproducibility envelope (G15 MANDATORY) ────────────────────
    repro = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "env_hash": env_hash(),
    }
    if torch.cuda.is_available():
        repro["gpu_name"] = torch.cuda.get_device_name(0)
        if hasattr(torch.version, "hip") and torch.version.hip:
            repro["rocm_version"] = torch.version.hip
        elif torch.version.cuda:
            repro["cuda_version"] = torch.version.cuda
    logger.info("Reproducibility envelope: %s", repro)

    # ─── Build model + dataset ─────────────────────────────────────────────
    model, tokenizer, installed = build_model(config)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    for wrapper in installed.values():
        wrapper.to(device)
        wrapper.moe_branch.to(dtype=torch.bfloat16)

    dataset = build_dataset(config, tokenizer)

    # ─── R1.3-R1.4 train: trl SFTTrainer (R1.1 skeleton, full impl pending) ─
    # The full SFTTrainer integration with custom compute_loss override that adds aux_loss
    # is a substantial integration. Skeleton below shows the structure:

    try:
        from trl import SFTTrainer, SFTConfig
    except ImportError:
        logger.warning("trl not installed — install via pip install trl>=0.11 on EVO-X2 to actually train")
        logger.info("R1.0 dry exit: model + dataset built successfully (skeleton)")
        return

    output_dir = config["output"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    sft_config = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"],
        learning_rate=config["training"]["learning_rate_experts"],  # default; per-group LR via custom optimizer
        warmup_steps=config["training"]["lr_scheduler"]["warmup_steps"],
        lr_scheduler_type=config["training"]["lr_scheduler"]["type"],
        bf16=config["training"]["bf16"],
        gradient_checkpointing=config["training"]["gradient_checkpointing"],
        dataloader_num_workers=config["training"]["dataloader_num_workers"],
        seed=config["training"]["seed"],
        max_seq_length=config["training"]["max_seq_length"],
        save_steps=config["output"]["snapshot_every_n_steps"],
        logging_steps=10,
        report_to="none",  # No wandb / no telemetry per Charter Rider §2(c)
    )

    # Custom optimizer with per-group LR (router / experts / alpha)
    # NOTE: this requires custom train loop override; SFTTrainer alone uses single LR.
    # R1.1 deliverable: subclass SFTTrainer to wire per-group LR + add aux_loss to loss.
    # For R1.0 scaffold, log a TODO:
    logger.warning("R1.1 deliverable: subclass SFTTrainer for per-group LR + aux_loss collection")
    logger.warning("Current scaffold uses single LR + no aux_loss (G6 MANDATORY violation if run as-is)")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=sft_config,
    )

    train_result = trainer.train()
    logger.info("Train result: %s", train_result.metrics)

    # Save merged checkpoint
    trainer.save_model(output_dir)
    logger.info("Checkpoint saved to %s", output_dir)

    # ─── Write reproducibility + summary JSON ──────────────────────────────
    summary = {
        "adr": "ADR-2605262100",
        "config_path": args.config,
        "reproducibility": repro,
        "param_summary": freeze_backbone_verify(
            model.model if hasattr(model, "model") else model, installed
        ),
        "train_metrics": train_result.metrics,
        "ended_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    bench_out = config["output"]["bench_output"]
    os.makedirs(os.path.dirname(bench_out), exist_ok=True)
    with open(bench_out, "a") as f:
        f.write(json.dumps(summary) + "\n")
    logger.info("Summary appended to %s", bench_out)


if __name__ == "__main__":
    main()
