"""LangGraph Pregel wrapper for the tazuna (手綱) teleop_session cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606042100 §Roadmap). The control plane
relays member-signed actuation commands under Transparent Force (G3) + no-server-key (G4) with a
soft-RT deadman/e-stop/latency guard (G10). It is NOT a certified safety system.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_build_grant,
    transition_relay_command,
    transition_verify_force_auth,
)


class TeleopSessionCell:
    """Transparent-Force, server-keyless teleoperation session. G3/G4/G10/N1."""

    def __init__(self) -> None:
        self._steps = [
            transition_verify_force_auth,
            transition_build_grant,
            transition_relay_command,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tazuna R0 scaffold: activate teleop_session via Council ADR "
            "(post-2606042100 ratification; live actuation Lv6+, :powered-actuation Lv7+)"
        )
