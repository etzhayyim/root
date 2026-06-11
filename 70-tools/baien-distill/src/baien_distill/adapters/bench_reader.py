"""Parse bench output formats so analyze.py + evaluate.py share one reader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def latest_microbench_jsonl(bench_dir: Path) -> Path | None:
    cands = sorted(
        list(bench_dir.glob("results-*.jsonl"))
        + list(bench_dir.glob("microbench-*/results.jsonl")),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    return cands[0] if cands else None


def parse_microbench_jsonl(path: Path) -> dict[str, float]:
    """Return {category → pass_rate} from a microbench jsonl."""
    by_cat: dict[str, list[bool]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            by_cat.setdefault(row["category"], []).append(bool(row["ok"]))
    return {c: sum(xs) / len(xs) for c, xs in by_cat.items() if xs}


def latest_lm_eval_dir(bench_dir: Path) -> Path | None:
    cands = sorted(bench_dir.glob("lm-eval-*/"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def parse_lm_eval_dir(dir_path: Path) -> dict[str, float]:
    """Return {task_id → primary_metric} from one lm-eval output tree.

    lm-eval-harness writes a per-model subdir with `results_*.json` files
    containing `{"results": {task_id: {metric: value, ...}}}`. We pick
    the first numeric metric per task as the headline.
    """
    out: dict[str, float] = {}
    for results_json in dir_path.rglob("results_*.json"):
        try:
            d = json.loads(results_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        for task_id, metrics in (d.get("results") or {}).items():
            primary = _primary_metric(metrics)
            if primary is not None:
                out[task_id] = primary
    return out


_METRIC_PREFERENCES = (
    "acc,none", "acc_norm,none", "exact_match,none",
    "prompt_level_strict_acc,none", "inst_level_strict_acc,none",
    "acc", "acc_norm", "exact_match",
)


def _primary_metric(metrics: dict[str, Any]) -> float | None:
    for k in _METRIC_PREFERENCES:
        if k in metrics:
            try:
                return float(metrics[k])
            except Exception:
                continue
    for k, v in metrics.items():
        if isinstance(v, (int, float)):
            return float(v)
    return None
