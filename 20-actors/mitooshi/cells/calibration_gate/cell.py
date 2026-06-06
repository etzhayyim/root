"""LangGraph Pregel wrapper for mitooshi calibration_gate (見通し) — R0 scaffold.

G7/G9/G12 promotion membrane: clears a model version for live forecasting ONLY if it
beats baseline (skill>0), is calibrated (PIT deviation within bound), and carries a
member/operator signature (no-server-key). Coded refusal gate in state_machine.py.
.solve() raises at R0 — actual promotion is Council Lv6+ + operator gated (G10).
"""
from __future__ import annotations
from typing import Any


class CalibrationGateCell:
    """Skill + calibration + no-server-key promotion gate. G7/G9/G12."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "mitooshi R0 scaffold: calibration_gate reviews offline; actual model "
            "promotion is Council Lv6+ + operator gated (G9/G10)."
        )
