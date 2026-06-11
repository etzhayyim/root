"""commit_node helper — append a registry entry for the committed adapter.

Two-tier registration per ADR-2605070700 + ADR-2605092350:

1. **lineage row** — `vertex_training_checkpoint.json` written by train.py
   captures the full training run (always, even non-committed iters).
2. **routing entry** — on commit, we append a JSONL line to
   `90-docs/baien/distilled-models.jsonl`. A separate codegen step
   (`70-tools/scripts/llm-registry/gen-distilled-entries.mjs`) folds
   this manifest into `kotodama-host-sdk/src/llm-model-registry.ts` so
   the runtime can route to it.

Two-phase ship so that:
  - the loop never writes TS directly (fragile parsing),
  - the registry update is reviewable (manifest → PR → codegen → commit),
  - audit lineage and runtime routing are decoupled.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..state import DistillState

REGISTRY_MANIFEST_REL = Path("90-docs") / "baien" / "distilled-models.jsonl"


def commit_to_registry(state: DistillState) -> None:
    lora_path = state.get("lora_path")
    if not lora_path:
        state.setdefault("notes", []).append(
            "[commit] no lora_path — nothing to register"
        )
        return

    bench_dir: Path = state["bench_dir"]
    # bench_dir is `90-docs/baien/`; registry sits next to it.
    manifest_path = bench_dir.parent.parent / REGISTRY_MANIFEST_REL
    # Fall back to walking up from the bench dir if the relative path
    # isn't obvious (test fixtures etc.).
    if not manifest_path.parent.exists():
        manifest_path = bench_dir / "distilled-models.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    iter_idx = state.get("iter", 0)
    teacher = state.get("teacher")
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_id": f"baien-distill-iter-{iter_idx:02d}",
        "kind": "baien-distill-react",
        "parent": "baien-bitnet-1.58bit-base",
        "huggingfaceModel": "microsoft/bitnet-b1.58-2B-4T-bf16",  # base
        "adapterPath": str(Path(lora_path) / "adapter"),
        "mergedPath": str(Path(lora_path) / "merged"),
        "teacher_model": teacher.model_id if teacher else None,
        "teacher_license": teacher.license if teacher else None,
        "iter": iter_idx,
        "score_history": state.get("score_history", []),
        "decision": state.get("decision"),
        "useCases": ["edge", "browser", "cpu"],
        "available": False,    # default off until codegen + review lands the entry
        "registry_status": "manifest-only — run gen-distilled-entries.mjs to surface in MODEL_REGISTRY",
    }

    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    state.setdefault("notes", []).append(
        f"[commit] appended registry manifest at {manifest_path}; "
        f"run `node 70-tools/scripts/llm-registry/gen-distilled-entries.mjs` "
        f"to fold into llm-model-registry.ts"
    )
