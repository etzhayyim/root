"""(4) train: peft + trl LoRA on gemma-3-4b-it (bf16 on ROCm gfx1151).

Per ADR-2605250400 §1.4. Identical config to baien-distill train.py except:
  - student is gemma-3-4b-it (not BitNet)
  - dataset categorisation tracks langgraph-coding bench categories
  - output dir is gemma-coder-distill-out/iter-NN/
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..state import DistillState, TrainExample

LORA_DEFAULTS = {
    "r": 16,
    "alpha": 32,
    "dropout": 0.05,
    # Gemma 4 wraps attention projections in Gemma4ClippableLinear (which wraps an inner
    # nn.Linear). peft.LoraConfig refuses non-Linear targets, so we target the inner ".linear"
    # by suffix. For non-Gemma-4 students this is overridden at runtime via _resolve_targets().
    "target_modules": ["q_proj.linear", "k_proj.linear", "v_proj.linear", "o_proj.linear"],
    "optim": "adamw_torch",
    "learning_rate": 2e-4,
    "warmup_steps": 100,
    "scheduler": "cosine",
}


def _resolve_targets(model, student_id: str) -> list[str]:
    """Inspect the model and return LoRA target_modules appropriate for its arch.

    Most HF models expose `q_proj/k_proj/v_proj/o_proj` as plain nn.Linear. Gemma 4 wraps
    them in `Gemma4ClippableLinear`, so we must target the inner `.linear` submodule.
    """
    import torch.nn as nn
    has_wrapper = False
    for name, mod in model.named_modules():
        if name.endswith(".q_proj") and not isinstance(mod, nn.Linear):
            inner_linear = any(
                isinstance(sub, nn.Linear) for sub in mod.modules()
            )
            if inner_linear:
                has_wrapper = True
            break
    if has_wrapper:
        return ["q_proj.linear", "k_proj.linear", "v_proj.linear", "o_proj.linear"]
    return ["q_proj", "k_proj", "v_proj", "o_proj"]


def train_lora(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[train] starting LoRA (peft+trl, ADR-2605250400 §1.2)")

    examples = state.get("training_examples", [])
    if not examples:
        state["notes"].append("[train] no examples — abort")
        state["decision"] = "abort"
        return state

    iter_idx = state.get("iter", 0)
    base_out = Path("gemma-coder-distill-out") / f"iter-{iter_idx:02d}"
    base_out.mkdir(parents=True, exist_ok=True)

    dataset_path = base_out / "train.jsonl"
    _write_jsonl(dataset_path, examples)
    dataset_hash = _sha256_file(dataset_path)

    epochs = 1 if state.get("quick") else 2
    student_id = state.get("student_model_id", "google/gemma-4-e4b-it")
    cfg: dict[str, Any] = {
        **LORA_DEFAULTS,
        "base_model": student_id,
        "epochs": epochs,
        "batch_size": 1,
        "dataset_path": str(dataset_path),
        "dataset_hash": dataset_hash,
        "n_examples": len(examples),
        "iter": iter_idx,
    }

    if state.get("dry_run"):
        state["notes"].append(
            f"[train] dry-run — would train r={cfg['r']} epochs={epochs} "
            f"n={len(examples)} dataset_hash={dataset_hash[:8]}…"
        )
        state["lora_path"] = base_out
        _write_checkpoint(base_out, cfg, final_loss=None, status="dry-run")
        state["decision"] = "continue"
        return state

    import os
    os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
    os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(student_id)
    model = AutoModelForCausalLM.from_pretrained(student_id, dtype=torch.bfloat16)

    from peft import LoraConfig, get_peft_model
    resolved_targets = _resolve_targets(model, student_id)
    state["notes"].append(f"[train] LoRA targets resolved: {resolved_targets}")
    lora_cfg = LoraConfig(
        r=cfg["r"], lora_alpha=cfg["alpha"], lora_dropout=cfg["dropout"],
        target_modules=resolved_targets,
        task_type="CAUSAL_LM", bias="none",
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    from datasets import Dataset
    def _format(ex: dict[str, str]) -> dict[str, str]:
        if getattr(tok, "chat_template", None):
            prompt_str = tok.apply_chat_template(
                [{"role": "user", "content": ex["prompt"]}],
                tokenize=False, add_generation_prompt=True,
            )
        else:
            prompt_str = f"<start_of_turn>user\n{ex['prompt']}<end_of_turn>\n<start_of_turn>model\n"
        return {"prompt": prompt_str, "completion": ex["response"]}

    ds = Dataset.from_list([ex.to_jsonl() for ex in examples]).map(_format)

    from trl import SFTConfig, SFTTrainer  # type: ignore
    sft = SFTConfig(
        output_dir=str(base_out / "sft-run"),
        num_train_epochs=epochs,
        per_device_train_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=4,
        learning_rate=cfg["learning_rate"],
        warmup_steps=cfg["warmup_steps"],
        lr_scheduler_type=cfg["scheduler"],
        bf16=True,
        use_cpu=not torch.cuda.is_available(),
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
        packing=False,
    )
    trainer = SFTTrainer(model=model, args=sft, train_dataset=ds, processing_class=tok)
    result = trainer.train()
    final_loss = float(getattr(result, "training_loss", float("nan")))

    adapter_dir = base_out / "adapter"
    model.save_pretrained(str(adapter_dir))
    tok.save_pretrained(str(adapter_dir))

    merged_dir = base_out / "merged"
    _merge(student_id, adapter_dir, merged_dir)

    state["lora_path"] = base_out
    state["notes"].append(
        f"[train] done adapter={adapter_dir} merged={merged_dir} loss={final_loss:.4f}"
    )
    _write_checkpoint(base_out, cfg, final_loss=final_loss, status="trained")
    state["decision"] = "continue"
    return state


def _merge(base_model_id: str, adapter_dir: Path, out_dir: Path) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    tok = AutoTokenizer.from_pretrained(base_model_id)
    base = AutoModelForCausalLM.from_pretrained(base_model_id, dtype=torch.bfloat16)
    peft_model = PeftModel.from_pretrained(base, str(adapter_dir))
    merged = peft_model.merge_and_unload()
    out_dir.mkdir(parents=True, exist_ok=True)
    # Bypass save_pretrained's safetensors path entirely — transformers ignores
    # safe_serialization=False on this version, hitting numpy ctypes int32 overflow
    # on Windows for >2 GB tensors (e.g. Gemma 4 embed_tokens at 262144*hidden in bf16).
    # Manual torch.save → pytorch_model.bin is loadable by AutoModelForCausalLM.from_pretrained.
    torch.save(merged.state_dict(), str(out_dir / "pytorch_model.bin"))
    merged.config.save_pretrained(str(out_dir))
    if hasattr(merged, "generation_config") and merged.generation_config is not None:
        merged.generation_config.save_pretrained(str(out_dir))
    tok.save_pretrained(str(out_dir))


def _write_jsonl(path: Path, examples: list[TrainExample]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex.to_jsonl(), ensure_ascii=False) + "\n")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _write_checkpoint(out_dir: Path, cfg: dict, final_loss: float | None,
                      status: str) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "gemma-coder-distill",
        "parent_kind": "google/gemma-4-e4b-it",
        "trainer": "peft+trl (ADR-2605250400 §1.2 fallback)",
        "status": status,
        "final_loss": final_loss,
        **cfg,
    }
    (out_dir / "vertex_training_checkpoint.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
    )
