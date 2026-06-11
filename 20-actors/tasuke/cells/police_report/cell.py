"""LangGraph Pregel wrapper for 助 (tasuke) police_report — R0 scaffold.

Generates the member-authored police-side filings (被害届 / 被害状況報告書 / 証拠目録 /
被害額算定書). Coded core in state_machine.py. .solve() raises at R0 — live filing is Council
Lv6+ + operator gated (G9)."""
from __future__ import annotations

from typing import Any


class PoliceReportCell:
    """Police-side document generation. G1 (free) / G2 (member submits) / G3 (member-authored)."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tasuke R0 scaffold: police_report drafts member-authored filings offline; live "
            "filing/submission is Council Lv6+ + operator gated (G9)."
        )
