"""CNS — single-tick orchestrator.

The CNS:
  1. Reads repo state via sensors.read_all().
  2. Diffs against the previous tick (read from most-recent _observations file).
  3. Picks the lowest-score × highest-leverage axis as the next-action target.
  4. Asks the emitter to persist a new cycle file.

LangGraph is overkill for a 5-node DAG; this stays in plain Python until
multi-node fan-out is needed (then promote to a kotodama cell colony).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .constitution import AXES
from .sensors import AxisReading, read_all


_CYCLE_RE = re.compile(r"-cycle-(\d+)\.md$")
_SCORE_RE = re.compile(r"^\|\s*\d+\s*\|.*?\|\s*(\d+)\s*/\s*10\s*\|", re.MULTILINE)


@dataclass
class TickResult:
    cycle: int
    readings: dict[str, AxisReading]
    prev_scores: dict[str, int]
    deltas: dict[str, int]
    total: int
    prev_total: int
    chosen_axis: str
    chosen_reason: str


def _read_prev(observations_dir: Path) -> tuple[int, dict[str, int]]:
    """Return (last_cycle_number, axis_scores) from most-recent observation."""
    files = sorted(observations_dir.glob("*-cycle-*.md"))
    if not files:
        return 0, {}
    last = files[-1]
    m = _CYCLE_RE.search(last.name)
    last_n = int(m.group(1)) if m else 0
    body = last.read_text(encoding="utf-8", errors="ignore")
    scores: dict[str, int] = {}
    # naive parse: order of axes in the table = AXES order
    matches = _SCORE_RE.findall(body)
    for axis, val in zip(AXES, matches):
        try:
            scores[axis.key] = int(val)
        except ValueError:
            continue
    return last_n, scores


def tick(repo: Path) -> TickResult:
    readings = read_all(repo)
    obs_dir = repo / "_observations"
    obs_dir.mkdir(exist_ok=True)
    last_n, prev_scores = _read_prev(obs_dir)

    total = sum(r.score for r in readings.values())
    prev_total = sum(prev_scores.get(a.key, 0) for a in AXES)
    deltas = {k: readings[k].score - prev_scores.get(k, readings[k].score) for k in readings}

    # Pick lowest score × highest leverage. Score gap = (10 - score). Priority = gap * leverage.
    best_axis = ""
    best_priority = -1
    for k, r in readings.items():
        gap = 10 - r.score
        priority = gap * r.leverage
        if priority > best_priority:
            best_priority = priority
            best_axis = k
    chosen_reason = (
        f"axis={best_axis} score={readings[best_axis].score}/10 "
        f"leverage={readings[best_axis].leverage} priority={best_priority}"
    )
    return TickResult(
        cycle=last_n + 1,
        readings=readings,
        prev_scores=prev_scores,
        deltas=deltas,
        total=total,
        prev_total=prev_total,
        chosen_axis=best_axis,
        chosen_reason=chosen_reason,
    )
