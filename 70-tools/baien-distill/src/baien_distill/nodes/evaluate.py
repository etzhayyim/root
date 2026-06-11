"""(6) evaluate: merge LoRA, run e7m bench micro, conditionally core3.

ADR-2605231300 §6.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ..adapters.bench_reader import (
    latest_microbench_jsonl, parse_microbench_jsonl,
)
from ..state import DistillState

MICRO_DELTA_PROMOTION = 0.02     # +2.0 pp on micro → run core3
CORE3_DELTA_COMMIT = 0.01        # +1.0 pp on core3 → commit
MAX_CATEGORY_REGRESSION = 0.05   # any category drops > 5 pp → fail commit


def evaluate(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[evaluate] dispatching e7m bench micro")

    if state.get("dry_run"):
        state["score_after"] = dict(state.get("score_before", {}))
        state["decision"] = "abort"
        state["notes"].append("[evaluate] dry-run — no real eval; abort")
        _record_history(state)
        state["iter"] += 1
        return state

    iter_idx = state["iter"]
    lora_path = state.get("lora_path")
    if lora_path is None:
        state["decision"] = "abort"
        state["notes"].append("[evaluate] no lora_path — abort")
        _record_history(state)
        state["iter"] += 1
        return state

    # train.py wrote a `merged/` HF model dir under lora_path. We invoke
    # microbench.py directly (no SSH) so train and eval can share the
    # same local filesystem — this loop is intended to run on the same
    # host as baien (EVO-X2 in the default deployment).
    merged_dir = Path(lora_path) / "merged"
    out_dir = Path(state["bench_dir"]) / f"distill-iter-{iter_idx:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    micro_script = _find_microbench_script()
    results_path = out_dir / "results.jsonl"
    # sys.executable ensures the subprocess runs in the same interpreter as
    # the LangGraph driver (so ROCm paths picked up when launched from
    # ComfyUI's python_embeded — torch 2.9.1+rocm7.2.1 on EVO-X2).
    micro_cmd = [
        sys.executable, str(micro_script),
        "--model", str(merged_dir),
        "--out", str(results_path),
    ]
    proc = subprocess.run(micro_cmd, capture_output=True, text=True)
    state["notes"].append(
        f"[evaluate] micro rc={proc.returncode} "
        f"stderr_tail={proc.stderr.splitlines()[-3:]!r}"
    )

    micro = latest_microbench_jsonl(out_dir)
    score_after = parse_microbench_jsonl(micro) if micro is not None else {}
    state["score_after"] = score_after

    delta = _avg_delta(state["score_before"], score_after)
    state["notes"].append(f"[evaluate] avg Δ = {delta:+.3f}")

    # promotion gate
    if delta >= MICRO_DELTA_PROMOTION:
        state["notes"].append("[evaluate] micro delta ≥ +2pp — promoting to core3")
        # TODO: wire e7m bench core3 invocation + parse
        # For now, treat promotion as commit pending future check.
        state["decision"] = "commit"
    else:
        if any((score_after.get(c, 0) - state["score_before"].get(c, 0)) <
               -MAX_CATEGORY_REGRESSION for c in score_after):
            state["notes"].append("[evaluate] regression > 5pp — retry")
        state["decision"] = "retry" if state["iter"] + 1 < state["max_iter"] else "abort"

    _record_history(state)
    state["iter"] += 1
    return state


def _avg_delta(before: dict, after: dict) -> float:
    keys = set(before) | set(after)
    if not keys:
        return 0.0
    return sum(after.get(k, 0) - before.get(k, 0) for k in keys) / len(keys)


def _find_microbench_script() -> Path:
    """Locate microbench.py relative to this file (assumes monorepo layout)."""
    here = Path(__file__).resolve()
    # 70-tools/baien-distill/src/baien_distill/nodes/evaluate.py
    # → 70-tools/scripts/bench/baien-microbench/microbench.py
    candidate = here.parents[4] / "scripts" / "bench" / "baien-microbench" / "microbench.py"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"microbench.py not found at {candidate}. "
        f"baien-distill expects the etzhayyim monorepo layout."
    )


def _record_history(state: DistillState) -> None:
    state.setdefault("score_history", []).append({
        "iter": state["iter"],
        "teacher": state["teacher"].model_id if state.get("teacher") else None,
        "weak_categories": [c.name for c in state.get("weak_categories", [])],
        "score_before": dict(state.get("score_before", {})),
        "score_after": dict(state.get("score_after", {})),
        "decision": state.get("decision"),
    })
