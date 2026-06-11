"""(6) commit: append a row to gemma-coder-distill manifest on gate pass.

Per ADR-2605250400 §3 Step 5. The manifest at
90-docs/baien/gemma-coder-distill-models.jsonl is the single source of truth
for shipped adapters (analogous to baien's distilled-models.jsonl).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..state import DistillState

MANIFEST = Path("90-docs/baien/gemma-coder-distill-models.jsonl")


def commit(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[commit] manifest append")
    if state.get("decision") != "commit" and not state.get("dry_run"):
        state["notes"].append("[commit] skipped — gate not passed")
        return state

    iter_idx = state.get("iter", 0)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "adr": "2605250400",
        "iter": iter_idx,
        "parent": state.get("student_model_id", "google/gemma-4-e4b-it"),
        "adapter_path": str(state.get("lora_path", "")),
        "baseline_pass_pct": state.get("baseline_pass_pct"),
        "new_pass_pct": state.get("new_pass_pct"),
        "delta_pp": state.get("delta_pp"),
        "n_examples": len(state.get("training_examples", [])),
        "weak_categories": state.get("weak_categories", []),
        "tag": f"gemma4-coder:e4b-iter{iter_idx:02d}",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    state["notes"].append(f"[commit] appended row: tag={row['tag']}")
    return state
