"""LangGraph Pregel wrapper for the karakuri session_broker (絡繰) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039200 §Decision).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_authorize_mutate,
    transition_build_grant,
    transition_read_allowed,
    transition_verify_owner,
)


class SessionBrokerCell:
    """Member-principal, server-keyless service-session broker. G1/G3/G5/G6."""

    def __init__(self) -> None:
        self._steps = [
            transition_verify_owner,
            transition_build_grant,
            transition_read_allowed,
            transition_authorize_mutate,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "karakuri R0 scaffold: activate session_broker via Council ADR "
            "(post-2606039200 ratification)"
        )
