"""(1) analyze: read latest e7m bench outputs and rank weak categories.

ADR-2605231300 §1.
"""

from __future__ import annotations

from ..adapters.bench_reader import (
    latest_lm_eval_dir, latest_microbench_jsonl,
    parse_lm_eval_dir, parse_microbench_jsonl,
)
from ..state import CategorySpec, DistillState

# Frontier-best from §A of frontier-bench-snapshot-260523.md
FRONTIER_BEST: dict[str, float] = {
    "IFEval":       0.945,   # GLM-5.1 / K2.6
    "MMLU":         0.953,   # MMLU-Redux, K2.6
    "GPQA Diamond": 0.924,   # Qwen3.7
    "Global PIQA":  0.914,   # Qwen3.7
    "Reasoning":    0.971,   # HMMT 2026 Feb (Qwen3.7)
    "Multilingual": 0.906,   # MMMLU (Opus-4.6)
    "General":      0.95,    # rough — MMLU-Redux as proxy
}

HIGH_PRIORITY_CATEGORIES = {"IFEval", "Multilingual"}


def _gap_score(category: str, baien: float) -> float:
    frontier = FRONTIER_BEST.get(category, 0.9)
    gap = max(0.0, frontier - baien)
    below_random = max(0.0, 0.5 - baien) * 0.5
    bonus = 1.0 if category in HIGH_PRIORITY_CATEGORIES else 0.0
    return gap + below_random + bonus


def analyze(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[analyze] reading latest bench outputs")

    bench_dir = state["bench_dir"]
    by_cat: dict[str, float] = {}

    micro = latest_microbench_jsonl(bench_dir)
    if micro is not None:
        by_cat.update(parse_microbench_jsonl(micro))
        state["notes"].append(f"[analyze] microbench rows from {micro.name}: "
                              f"{len(by_cat)} categories")

    lm_dir = latest_lm_eval_dir(bench_dir)
    if lm_dir is not None:
        lm = parse_lm_eval_dir(lm_dir)
        for k, v in lm.items():
            # lm-eval gives finer-grained task ids; map to higher-level category
            cat = _category_for_lm_task(k)
            # take the more recent (lm-eval) over micro for the same category
            by_cat[cat] = v
        state["notes"].append(f"[analyze] lm-eval rows from {lm_dir.name}: "
                              f"{len(lm)} tasks")

    if not by_cat:
        state["notes"].append("[analyze] no bench data found — abort scheduled")
        state["weak_categories"] = []
        state["decision"] = "abort"
        return state

    ranked = sorted(
        (
            CategorySpec(
                name=c,
                baien_score=s,
                frontier_best=FRONTIER_BEST.get(c),
                gap_score=_gap_score(c, s),
                rationale=(
                    f"baien={s:.3f} frontier_best="
                    f"{FRONTIER_BEST.get(c, float('nan')):.3f}"
                ),
            )
            for c, s in by_cat.items()
        ),
        key=lambda x: x.gap_score, reverse=True,
    )
    n_pick = 3 if state.get("quick") else min(3, len(ranked))
    state["weak_categories"] = ranked[:n_pick]
    state["score_before"] = by_cat
    state["notes"].append(
        "[analyze] weakest categories: " +
        ", ".join(f"{c.name}({c.baien_score:.2f})" for c in ranked[:n_pick])
    )
    return state


def _category_for_lm_task(task_id: str) -> str:
    t = task_id.lower()
    if "ifeval" in t:
        return "IFEval"
    if "gpqa" in t:
        return "GPQA Diamond"
    if "mmlu_redux" in t or t.startswith("mmlu"):
        return "MMLU"
    if "piqa" in t:
        return "Global PIQA"
    if "wmt" in t or any(lang in t for lang in (
        "_jp", "_ja", "_de", "_fr", "_zh", "_es", "_ar", "_ru"
    )):
        return "Multilingual"
    return "General"
