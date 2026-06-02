"""TsutaeFirmwareLoadCell — tsutae R0 Pregel cell (L4, joseph). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    FirmwarePhase,
    transition_to_image_verified,
    transition_to_blob_ratio_checked,
    transition_to_bootloader_unlock_confirmed,
    transition_to_flashed,
    transition_to_attestation_emitted,
)


class TsutaeFirmwareLoadCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify", self._verify)
        g.add_node("blob_guard", self._blob_guard)
        g.add_node("bootloader_guard", self._bootloader_guard)
        g.add_node("flash", self._flash)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify")
        g.add_edge("verify", "blob_guard")
        g.add_edge("blob_guard", "bootloader_guard")
        g.add_edge("bootloader_guard", "flash")
        g.add_edge("flash", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"firmware_state": {
            "phase": FirmwarePhase.INIT.value,
            "deviceId": state.get("deviceId", "TSUTAE-DEV-0001"),
            "completionPct": 0,
        }}

    def _verify(self, s): return transition_to_image_verified(s)
    def _blob_guard(self, s): return transition_to_blob_ratio_checked(s)
    def _bootloader_guard(self, s): return transition_to_bootloader_unlock_confirmed(s)
    def _flash(self, s): return transition_to_flashed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaeFirmwareLoadCell"]
