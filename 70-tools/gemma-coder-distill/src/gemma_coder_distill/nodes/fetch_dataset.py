"""(2) fetch_dataset: pull SFT examples from registered sources.

Per ADR-2605250400 §1.3 — three signal sources, all weighted toward
weak categories from analyze():

  1. HF Opus-distilled SFT (Apache 2.0 only)
  2. LangGraph-API-specific synthetic via judah LiteLLM Claude (governance-gated)
  3. Harvest from existing first-party LangGraph code in this repo

For iter-00 / quick we only enable (1) (HF) — (2) and (3) come online
after ADR-2605250400 §3 Step 5.
"""

from __future__ import annotations

from ..state import DistillState, TrainExample

# Apache/MIT-licensed only. license must be reviewed per ADR-2605250400 §2.
DATASET_REGISTRY: list[dict[str, str]] = [
    {
        "name": "lordx64/reasoning-distill-opus-4-7-max-sft",
        "license": "apache-2.0",
        "category": "reasoning",
        "rows": "7823",
        "notes": "Opus-distilled general reasoning — indirect Opus signal per ADR-2605231300 §3a",
    },
    # TODO Step 4: add coding-specific Apache/MIT corpora (per-iter license review)
    # e.g. nvidia/OpenCodeReasoning (if Apache), allenai/CodeT, etc.
]


def fetch_dataset(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[fetch] loading HF corpora")

    if state.get("dry_run"):
        state["notes"].append(
            f"[fetch] dry-run — would pull from {len(DATASET_REGISTRY)} datasets, "
            f"weak={state.get('weak_categories', [])}"
        )
        state["training_examples"] = []
        state["decision"] = "continue"
        return state

    from datasets import load_dataset  # type: ignore

    examples: list[TrainExample] = []
    quick = state.get("quick", False)
    cap = 200 if quick else 5000

    for spec in DATASET_REGISTRY:
        try:
            ds = load_dataset(spec["name"], split="train", streaming=True)
        except Exception as e:
            state["notes"].append(f"[fetch] skip {spec['name']}: {e!r}")
            continue
        n = 0
        for row in ds:
            prompt = row.get("prompt") or row.get("instruction") or row.get("question")
            response = row.get("response") or row.get("output") or row.get("answer")
            if not prompt or not response:
                continue
            examples.append(TrainExample(
                prompt=str(prompt), response=str(response),
                source=f"hf:{spec['name']}", category=spec["category"],
            ))
            n += 1
            if n >= cap:
                break
        state["notes"].append(f"[fetch] {spec['name']}: +{n} examples")

    state["training_examples"] = examples
    state["notes"].append(f"[fetch] total examples={len(examples)}")
    state["decision"] = "continue" if examples else "abort"
    return state
