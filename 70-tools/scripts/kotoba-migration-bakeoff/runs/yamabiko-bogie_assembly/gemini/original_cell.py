"""BogieAssemblyCell — yamabiko R0 Pregel cell (L2). R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    BogiePhase, BogieState,
    transition_to_frame_prepared, transition_to_wheel_set_mounted,
    transition_to_motor_installed, transition_to_brake_integrated,
    transition_to_air_spring_installed, transition_to_attestation_emitted,
)


class BogieAssemblyCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("frame", self._frame)
        g.add_node("wheel", self._wheel)
        g.add_node("motor", self._motor)
        g.add_node("brake", self._brake)
        g.add_node("air", self._air)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "frame")
        g.add_edge("frame", "wheel")
        g.add_edge("wheel", "motor")
        g.add_edge("motor", "brake")
        g.add_edge("brake", "air")
        g.add_edge("air", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"bogie_state": {
            "phase": BogiePhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "bogieIndex": state.get("bogieIndex", 0),
            "completionPct": 0,
        }}

    def _frame(self, s): return transition_to_frame_prepared(s)
    def _wheel(self, s): return transition_to_wheel_set_mounted(s)
    def _motor(self, s): return transition_to_motor_installed(s)
    def _brake(self, s): return transition_to_brake_integrated(s)
    def _air(self, s): return transition_to_air_spring_installed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["BogieAssemblyCell"]
