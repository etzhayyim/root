"""(5) evaluate: re-run langgraph-coding bench on merged model, compute delta.

Per ADR-2605250400 §1.5. Spawns 70-tools/scripts/bench/langgraph-coding/run.py
as a subprocess; emits results-langgraph-iterNN.jsonl alongside baseline.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ..state import DistillState

GATE_QUICK_PP = 0.0  # iter-00 smoke: no regression
GATE_REAL_PP = 3.0   # iter-01+: ≥ +3pp


def evaluate(state: DistillState) -> DistillState:
    state.setdefault("notes", []).append("[evaluate] re-running langgraph-coding bench")

    lora_path: Path = state["lora_path"]
    merged_dir = lora_path / "merged"
    iter_idx = state.get("iter", 0)
    bench_dir: Path = state["bench_dir"]
    out_file = bench_dir / f"results-langgraph-iter{iter_idx:02d}.jsonl"

    if state.get("dry_run"):
        state["notes"].append("[evaluate] dry-run — skipping subprocess")
        state["new_pass_pct"] = state.get("baseline_pass_pct", 0.0)
        state["delta_pp"] = 0.0
        state["decision"] = "commit"
        return state

    env_override = os.environ.get("GEMMA_CODER_BENCH_RUNNER")
    if env_override:
        bench_runner = Path(env_override)
    else:
        # repo-relative resolution (fails when installed standalone — set the env var instead)
        try:
            bench_runner = (
                Path(__file__).resolve().parents[5]
                / "scripts" / "bench" / "langgraph-coding" / "run.py"
            )
        except IndexError:
            raise RuntimeError(
                "Cannot resolve bench runner via repo layout; "
                "set GEMMA_CODER_BENCH_RUNNER=/path/to/run.py"
            )
    cmd = [
        sys.executable, str(bench_runner),
        "--model", f"file://{merged_dir}",
        "--model-id", f"gemma4-coder:e4b-iter{iter_idx:02d}",
        "--out", str(out_file),
    ]
    state["notes"].append(f"[evaluate] cmd: {' '.join(cmd)}")
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        state["notes"].append(f"[evaluate] FAIL rc={p.returncode} stderr={p.stderr[:300]!r}")
        state["decision"] = "abort"
        return state

    n_pass = n_total = 0
    with out_file.open() as f:
        for line in f:
            row = json.loads(line)
            n_total += 1
            if row.get("passed"):
                n_pass += 1
    new_pct = 100 * n_pass / n_total if n_total else 0.0
    state["new_pass_pct"] = new_pct
    state["delta_pp"] = new_pct - state.get("baseline_pass_pct", 0.0)

    gate = GATE_QUICK_PP if state.get("quick") else GATE_REAL_PP
    if state["delta_pp"] >= gate:
        state["decision"] = "commit"
        state["notes"].append(
            f"[evaluate] PASS new={new_pct:.1f}% delta={state['delta_pp']:+.1f}pp ≥ gate={gate}pp"
        )
    else:
        state["decision"] = "abort"
        state["notes"].append(
            f"[evaluate] GATE FAIL new={new_pct:.1f}% delta={state['delta_pp']:+.1f}pp < gate={gate}pp"
        )
    return state
