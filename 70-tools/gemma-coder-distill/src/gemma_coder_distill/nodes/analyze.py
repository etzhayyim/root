"""(1) analyze: read baseline langgraph-coding bench, find weak categories.

Reads the latest `results-langgraph-*.jsonl` under bench_dir. Categories
with pass rate < 60% are flagged as weak — those drive dataset filtering
in fetch_dataset.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from ..state import DistillState


def analyze(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[analyze] reading langgraph-coding bench")
    bench_dir: Path = state["bench_dir"]

    candidates = sorted(bench_dir.glob("results-langgraph-*.jsonl"))
    if not candidates:
        state["notes"].append(
            "[analyze] no langgraph-coding baseline — run "
            "70-tools/scripts/bench/langgraph-coding/run.py first"
        )
        state["decision"] = "abort"
        return state

    latest = candidates[-1]
    state["notes"].append(f"[analyze] baseline: {latest.name}")

    by_cat: dict[str, list[bool]] = defaultdict(list)
    with latest.open() as f:
        for line in f:
            row = json.loads(line)
            by_cat[row.get("category", "?")].append(bool(row.get("passed")))

    total = sum(len(v) for v in by_cat.values())
    passed = sum(sum(v) for v in by_cat.values())
    state["baseline_pass_pct"] = 100 * passed / total if total else 0.0

    weak = [cat for cat, results in by_cat.items()
            if 100 * sum(results) / len(results) < 60.0]
    state["weak_categories"] = weak

    state["notes"].append(
        f"[analyze] baseline pass={state['baseline_pass_pct']:.1f}% "
        f"weak={weak}"
    )
    state["decision"] = "continue"
    return state
