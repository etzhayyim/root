"""(5) train_lora: peft+trl LoRA on the bf16 master per ADR-2605092350 §LoRA.

Layout per ADR-2605231300 §5:

  base_out/
    train.jsonl                       # the SFT corpus
    adapter/                          # LoRA adapter (peft save_pretrained)
    merged/                           # LoRA merged into base (HF model dir)
    vertex_training_checkpoint.json   # lineage row (ADR-2605070700)

The `merged/` directory is what `e7m bench micro --model <merged>`
loads at eval time; the `adapter/` is what gets shipped to the model
registry on a successful commit (ADR-2605092350 §related).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..state import DistillState, TrainExample

# Per ADR-2605231300 §5 table.
LORA_DEFAULTS = {
    "r": 16,
    "alpha": 32,
    "dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "optim": "adamw_torch",
    "learning_rate": 2e-4,
    "warmup_steps": 100,
    "scheduler": "cosine",
}

BASE_MODEL_ID = "microsoft/bitnet-b1.58-2B-4T-bf16"


def train_lora(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[train] starting LoRA")

    examples = state.get("training_examples", [])
    if not examples:
        state["notes"].append("[train] no examples — abort")
        state["decision"] = "abort"
        return state

    iter_idx = state.get("iter", 0)
    base_out = Path("baien-distill-out") / f"iter-{iter_idx:02d}"
    base_out.mkdir(parents=True, exist_ok=True)

    dataset_path = base_out / "train.jsonl"
    _write_jsonl(dataset_path, examples)
    dataset_hash = _sha256_file(dataset_path)

    epochs = 1 if state.get("quick") else 2
    student_id = state.get("student_model_id") or BASE_MODEL_ID
    cfg: dict[str, Any] = {
        **LORA_DEFAULTS,
        "base_model": student_id,
        "epochs": epochs,
        "batch_size": 1,
        "dataset_path": str(dataset_path),
        "dataset_hash": dataset_hash,
        "n_examples": len(examples),
        "teacher_model": state["teacher"].model_id if state["teacher"] else None,
        "iter": iter_idx,
    }

    if state.get("dry_run"):
        state["notes"].append(
            f"[train] dry-run — would train with r={cfg['r']} epochs={epochs} "
            f"n={len(examples)} dataset_hash={dataset_hash[:8]}…"
        )
        state["lora_path"] = base_out
        _write_checkpoint_row(base_out, cfg, final_loss=None, status="dry-run")
        return state

    # Real training path. The adapters.baien_student.load_student() helper
    # already sets up the dynamo/inductor suppression we need on Windows.
    from ..adapters.baien_student import load_student

    tok, model = load_student(student_id)

    from peft import LoraConfig, get_peft_model

    lora_cfg = LoraConfig(
        r=cfg["r"], lora_alpha=cfg["alpha"], lora_dropout=cfg["dropout"],
        target_modules=list(cfg["target_modules"]), task_type="CAUSAL_LM", bias="none",
    )
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # Build dataset using the model's chat template (so eval at inference
    # time uses the same format the model was tuned on).
    from datasets import Dataset

    def _format(ex: dict[str, str]) -> dict[str, str]:
        if getattr(tok, "chat_template", None):
            prompt_str = tok.apply_chat_template(
                [{"role": "user", "content": ex["prompt"]}],
                tokenize=False, add_generation_prompt=True,
            )
        else:
            prompt_str = f"<|user|>\n{ex['prompt']}\n<|assistant|>\n"
        return {"prompt": prompt_str, "completion": ex["response"]}

    ds = Dataset.from_list([ex.to_jsonl() for ex in examples]).map(_format)

    import torch as _t
    from trl import SFTConfig, SFTTrainer  # type: ignore

    _gpu = _t.cuda.is_available()
    sft = SFTConfig(
        output_dir=str(base_out / "sft-run"),
        num_train_epochs=epochs,
        per_device_train_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=4,
        learning_rate=cfg["learning_rate"],
        warmup_steps=cfg["warmup_steps"],
        lr_scheduler_type=cfg["scheduler"],
        bf16=True,
        use_cpu=not _gpu,  # GPU when available (ROCm/CUDA); fall back to CPU
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
        packing=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft,
        train_dataset=ds,
        processing_class=tok,
    )

    result = trainer.train()
    final_loss = float(getattr(result, "training_loss", float("nan")))

    adapter_dir = base_out / "adapter"
    model.save_pretrained(str(adapter_dir))
    tok.save_pretrained(str(adapter_dir))

    merged_dir = base_out / "merged"
    merge_adapter(student_id, adapter_dir, merged_dir)

    state["lora_path"] = base_out
    state["notes"].append(
        f"[train] done — adapter={adapter_dir} merged={merged_dir} loss={final_loss:.4f}"
    )
    _write_checkpoint_row(base_out, cfg, final_loss=final_loss, status="trained")
    return state


def merge_adapter(base_model_id: str, adapter_dir: Path, out_dir: Path) -> Path:
    """Merge a LoRA adapter into the base model and save as a standalone
    HF model dir that `transformers.AutoModelForCausalLM.from_pretrained`
    can load. Returns the output directory.

    This is what `evaluate.py` points `e7m bench micro --model` at.
    """
    from ..adapters.baien_student import load_student

    tok, base = load_student(base_model_id)

    from peft import PeftModel

    peft_model = PeftModel.from_pretrained(base, str(adapter_dir))
    merged = peft_model.merge_and_unload()

    out_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(out_dir))
    tok.save_pretrained(str(out_dir))
    return out_dir


# ----- helpers ------------------------------------------------------------

def _write_jsonl(path: Path, examples: list[TrainExample]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex.to_jsonl(), ensure_ascii=False) + "\n")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _write_checkpoint_row(out_dir: Path, cfg: dict, final_loss: float | None,
                          status: str) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "baien-distill-react",
        "parent_kind": "bitnet-b1.58-2B-4T-bf16",
        "status": status,
        "final_loss": final_loss,
        **cfg,
    }
    (out_dir / "vertex_training_checkpoint.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
    )
