"""LangGraph Pregel wrapper for 助 (tasuke) intake_triage — R0 scaffold.

Consent-gated, free, no-server-key victim intake → scam-KIND classification + severity + the free
public windows + the first-response checklist. Coded core in state_machine.py. .solve() raises at
R0 — live case opening into the canonical Datom log is Council Lv6+ + operator gated (G9).
"""
from __future__ import annotations

from typing import Any


class IntakeTriageCell:
    """Victim intake + triage. G1 (free) / G4 (KIND not verdict) / G7 (consent + no-server-key)."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tasuke R0 scaffold: intake_triage classifies offline; live case opening into the "
            "canonical Datom log is Council Lv6+ + operator gated (G9)."
        )
