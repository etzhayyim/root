"""LangGraph Pregel wrapper for the tedai evidence_audit (手代) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606101400). The hash-evidence ->
project-datoms -> assemble-batch path is implemented as pure, unit-tested transitions in
state_machine.py.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_assemble_batch,
    transition_hash_evidence,
    transition_project_datoms,
)


class EvidenceAuditCell:
    """Hash-only evidence + Datom projection of every DesktopOp. G7/G9 (live ingest gated, G6)."""

    def __init__(self) -> None:
        self._steps = [
            transition_hash_evidence,
            transition_project_datoms,
            transition_assemble_batch,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tedai R0 scaffold: activate evidence_audit via Council ADR (post-2606101400)"
        )
