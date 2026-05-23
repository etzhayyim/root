"""Append a Move 1 multimodal entry to `90-docs/baien/multimodal-models.jsonl`.

Two-phase ship pattern (per ADR-2605231300 §commit_node, mirrored here for
ADR-2605232500):

  1. Python writes a JSONL row → reviewer-visible diff in git.
  2. `70-tools/scripts/llm-registry/gen-multimodal-entries.mjs` emits a TS
     module that is included in MODEL_REGISTRY only after the human
     reviewer flips `available: true`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .state import Move1State


MANIFEST_REL = Path("90-docs") / "baien" / "multimodal-models.jsonl"


def commit_to_registry(state: Move1State) -> None:
    cfg = state.cfg
    if state.projector_path is None:
        state.notes.append("[commit] no projector_path — nothing to register")
        return

    manifest_path = cfg.bench_dir.parent.parent / MANIFEST_REL
    if not manifest_path.parent.exists():
        manifest_path = cfg.bench_dir / "multimodal-models.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_id": f"baien-mx-move1-phase{cfg.phase}-iter-{state.iter:02d}",
        "kind": "baien-mx-move1-projector",
        "parent": "baien-bitnet-1.58bit-base",
        "huggingfaceModel": cfg.base_model,
        "imageEncoder": cfg.image_encoder,
        "projectorPath": str(state.projector_path),
        "trainJsonl": str(state.train_jsonl_path) if state.train_jsonl_path else None,
        "datasetHash": state.train_dataset_hash,
        "nTrainRows": state.n_train_rows,
        "phase": cfg.phase,
        "finalLoss": state.final_loss,
        "visualMicrobenchPassRate": state.visual_microbench_pass_rate,
        "textMicrobenchDeltaPp": state.text_microbench_delta_pp,
        "iter": state.iter,
        "decision": state.decision,
        "useCases": ["edge", "browser", "cpu", "image"],
        "available": False,           # default off — reviewer flips after eval review
        "registryStatus": (
            "manifest-only — run "
            "70-tools/scripts/llm-registry/gen-multimodal-entries.mjs to surface "
            "in MODEL_REGISTRY"
        ),
    }

    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    state.notes.append(
        f"[commit] appended multimodal manifest at {manifest_path}; "
        f"run `node 70-tools/scripts/llm-registry/gen-multimodal-entries.mjs` "
        f"to fold into llm-model-registry-multimodal.ts"
    )
