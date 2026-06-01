"""Phase B — distill recovery after Bonsai-style quantization.

Delegates to the existing `baien-distill` ReAct loop (ADR-2605231300)
with the quantized weights as the "student" and the configured
Apache-2.0 distill datasets as the "teacher".

Why delegate: we already debugged the SFT + commit_node + codegen
pipeline in baien-distill. No point re-implementing.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

from .state import RosoState


def recovery(state: RosoState) -> RosoState:
    cfg = state.cfg
    if cfg.phase == "A":
        state.notes.append("[recovery] phase A — quantize only, skipping recovery")
        return state

    if state.quantized_path is None:
        state.notes.append("[recovery] no quantized_path — must quantize first")
        state.decision = "abort"
        return state

    state.notes.append(
        f"[recovery] phase B — distill recovery on "
        f"{len(cfg.recovery_datasets)} datasets × {cfg.recovery_n_per_dataset} rows each"
    )

    out_dir = Path(state.quantized_path) / "recovery"
    out_dir.mkdir(parents=True, exist_ok=True)

    if cfg.dry_run:
        manifest = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "phase": "B",
            "datasets": list(cfg.recovery_datasets),
            "n_per_dataset": cfg.recovery_n_per_dataset,
            "lr": cfg.recovery_lr,
            "epochs": cfg.recovery_epochs,
            "batch_size": cfg.recovery_batch_size,
            "expected_loss": None,
            "status": "dry-run",
            "TODO": (
                "wire to baien_distill.train.train_lora() with student="
                "Bonsai-quantized weights + dataset = recovery_datasets union."
            ),
        }
        (out_dir / "recovery_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        state.recovery_jsonl_path = out_dir / "recovery_manifest.json"
        state.recovery_final_loss = None
        state.notes.append(f"[recovery] dry-run manifest → {out_dir}")
        return state

    # ----- Real path -----
    # Delegate to baien-distill's SFT loop. The student is the quantized
    # model on disk; the dataset is the union of cfg.recovery_datasets
    # (which are already wired in baien_distill.adapters.hf_dataset
    # DATASET_REGISTRY under category="General" / "Reasoning" / etc.).
    try:
        from baien_distill.adapters.hf_dataset import DATASET_REGISTRY, load_examples
        from baien_distill.nodes.train import train_lora as distill_train
        from baien_distill.state import new_state as distill_new_state
    except ImportError as e:
        state.notes.append(
            f"[recovery] baien-distill not installed; pip install -e ../../baien-distill — {e!r}"
        )
        state.decision = "abort"
        return state

    state.notes.append(
        "[recovery] delegating SFT to baien_distill.train.train_lora "
        f"(student={state.quantized_path}, datasets={cfg.recovery_datasets})"
    )

    # Load examples from the requested recovery datasets via baien-distill
    # adapter registry. DATASET_REGISTRY is keyed by category (Reasoning /
    # General / Multilingual / …) with list[DatasetSpec] under each; we
    # flatten on HF id.
    flat: dict[str, tuple[str, object]] = {}
    for cat, specs in DATASET_REGISTRY.items():
        for s in specs:
            flat.setdefault(s.id, (cat, s))

    training_examples = []
    for ds_id in cfg.recovery_datasets:
        hit = flat.get(ds_id)
        if hit is None:
            state.notes.append(f"[recovery] dataset {ds_id} not in DATASET_REGISTRY — skip")
            continue
        category, spec = hit
        rows = list(load_examples(spec, category, limit=cfg.recovery_n_per_dataset))
        training_examples.extend(rows)
        state.notes.append(
            f"[recovery] loaded {len(rows)} examples from {ds_id} (category={category})"
        )
    if not training_examples:
        state.notes.append("[recovery] no examples loaded — abort")
        state.decision = "abort"
        return state

    sub = distill_new_state(
        bench_dir=Path(state.quantized_path),
        max_iter=1,
        n_per_category=cfg.recovery_n_per_dataset,
        source="hf",
        quick=False,
        dry_run=False,
        student_model_id=str(state.quantized_path),  # override BASE_MODEL_ID
    )
    sub["training_examples"] = training_examples

    sub = distill_train(sub)

    lora_path = sub.get("lora_path")
    decision = sub.get("decision", "pending")
    notes = sub.get("notes", [])
    state.notes.extend(f"[recovery|distill] {n}" for n in notes)

    if decision == "abort" or lora_path is None:
        state.notes.append("[recovery] distill_train aborted — propagating")
        state.decision = "abort"
        return state

    # Read checkpoint row from baien-distill output for final_loss
    ckpt_path = Path(lora_path) / "checkpoint.json"
    if ckpt_path.exists():
        ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
        state.recovery_final_loss = ckpt.get("final_loss")
    state.recovery_jsonl_path = Path(lora_path)

    # Mirror manifest so attestation/commit see a single canonical doc
    manifest = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": "B",
        "datasets": list(cfg.recovery_datasets),
        "n_per_dataset": cfg.recovery_n_per_dataset,
        "lr": cfg.recovery_lr,
        "epochs": cfg.recovery_epochs,
        "batch_size": cfg.recovery_batch_size,
        "final_loss": state.recovery_final_loss,
        "lora_path": str(lora_path),
        "status": "trained",
    }
    (out_dir / "recovery_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    state.notes.append(
        f"[recovery] done — lora_path={lora_path} loss={state.recovery_final_loss}"
    )
    return state
