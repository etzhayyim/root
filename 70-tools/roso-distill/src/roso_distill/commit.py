"""commit_node — append Bonsai sibling to roso-models.jsonl, then point
the codegen script.

Two-phase ship pattern shared with baien-distill (ADR-2605231300
§commit_node) and baien-mx-train (ADR-2605232500 §Storage and
registration): Python writes a JSONL line, codegen emits TS, reviewer
flips `available: true`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .state import RosoState, derive_sibling_id


MANIFEST_REL = Path("90-docs") / "baien" / "roso-models.jsonl"


def commit_to_registry(state: RosoState) -> None:
    cfg = state.cfg
    if state.attestation_passed is not True:
        state.notes.append("[commit] attestation not passed — refusing to register")
        return

    sibling_id = state.sibling_id or derive_sibling_id(
        cfg.base_model, cfg.quant_method, cfg.phase,
    )
    state.sibling_id = sibling_id

    bench_dir = cfg.bench_dir
    manifest_path = bench_dir.parent.parent / MANIFEST_REL
    if not manifest_path.parent.exists():
        manifest_path = bench_dir / "roso-models.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_id": sibling_id,
        "kind": "roso-bonsai-1bit",
        "base_model": cfg.base_model,
        "quant_method": cfg.quant_method,
        "phase": cfg.phase,
        "quantizedPath": str(state.quantized_path) if state.quantized_path else None,
        "recoveryDatasets": list(cfg.recovery_datasets) if cfg.phase == "B" else [],
        "recoveryNPerDataset": cfg.recovery_n_per_dataset if cfg.phase == "B" else 0,
        "recoveryFinalLoss": state.recovery_final_loss,
        "packedGB": state.packed_weights_gb,
        "ram4kGB": state.attestation_ram_4k_gb,
        "ram16kGB": state.attestation_ram_16k_gb,
        "iphone14FirstTokenMs": state.attestation_iphone14_first_token_ms,
        "edgeInvariantPassed": state.attestation_passed,
        "iter": state.iter,
        "decision": state.decision,
        "useCases": ["edge", "browser", "cpu"],
        "available": False,
        "registryStatus": (
            "manifest-only — run "
            "70-tools/scripts/llm-registry/gen-roso-entries.mjs to surface in "
            "MODEL_REGISTRY (Phase 1 ADR-2605242000 §Phase 3)"
        ),
    }

    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    state.notes.append(
        f"[commit] appended {sibling_id} to {manifest_path}; "
        f"run `node 70-tools/scripts/llm-registry/gen-roso-entries.mjs` to fold "
        f"into llm-model-registry-roso.ts"
    )
