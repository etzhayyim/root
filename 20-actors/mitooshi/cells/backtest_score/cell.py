"""LangGraph Pregel wrapper for mitooshi backtest_score (見通し) — R0 scaffold.

Runs the leak-free proper-scoring backtest (methods/score.py) over a set of issued
forecasts and the observations that realized them, emitting a scorecard + per-forecast
residual datoms + calibration + skill-vs-baseline. The coded reasoner lives in
state_machine.py (`score_batch` — leak-checked, refuses G1 point / G2 use / G5 leak); the
scoring engine itself runs (it is pure + offline). .solve() raises only because wiring it to
the LIVE Datom log read/write is Council Lv6+ + operator gated (G10).
"""
from __future__ import annotations
from typing import Any


class BacktestScoreCell:
    """Leak-free proper-scoring backtest + calibration + skill. G5/G12."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "mitooshi R0 scaffold: scoring runs offline via methods/score.py; live Datom "
            "log read/write is Council Lv6+ + operator gated (G10)."
        )
