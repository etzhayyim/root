"""LangGraph Pregel wrapper for the kamado decommission_robot (竈) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606051500 §Decision).
The runnable purge + entry-gate loop lives in ../../methods/decommission_robot.py;
the gated phase machine (purge → entry-gated cut → member-signed dry-run commit)
lives in state_machine.py and is unit-tested at R0. No live process actuation /
hot-zone entry without Council Lv6+ + operator + certified-safety review (G8/G11).
"""
from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_commit_entry,
    transition_plan_cut,
    transition_purge,
)


class DecommissionRobotCell:
    """Hot-zone purge → entry-gated cut for a fossil asset wind-down. G3/G5/G8/G9/G11."""

    def __init__(self) -> None:
        self._steps = [transition_purge, transition_plan_cut, transition_commit_entry]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kamado R0 scaffold: activate decommission_robot via Council ADR "
            "(post-2606051500 ratification) + operator + certified-safety review (G8/G11)"
        )
