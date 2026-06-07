"""LangGraph Pregel wrapper for 潮目 (shionome) flow_graph — R0 scaffold.

Builds the in-memory capital-flow graph (buckets + flows + snapshots) and net-flow indices.
Coded core in methods/weave.py + state_machine.py. .solve() raises at R0 — live read-path
build over the kotoba Datom log is Council Lv6+ gated (G8).
"""
from __future__ import annotations

from typing import Any


class FlowGraphCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shionome R0 scaffold: flow_graph computes offline; live kotoba read-path build is "
            "Council Lv6+ gated (G8)."
        )
