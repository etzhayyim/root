"""LangGraph Pregel wrapper for the tedai pairing_broker (手代) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606101400). The verify-owner ->
build-grant -> read-allowed / authorize-mutate path is implemented as pure, unit-tested transitions
in state_machine.py.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_authorize_mutate,
    transition_build_grant,
    transition_read_allowed,
    transition_verify_owner,
)


class PairingBrokerCell:
    """Member-keyless device pairing broker: own-device-only, member-signed mutate. G1/G3/G5."""

    def __init__(self) -> None:
        self._steps = [
            transition_verify_owner,
            transition_build_grant,
            transition_read_allowed,
            transition_authorize_mutate,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tedai R0 scaffold: activate pairing_broker via Council ADR (post-2606101400)"
        )
