"""LangGraph Pregel wrapper for the hotaru bulk_crystal_design (蛍) cell — R0 scaffold.

Single-crystal InP boule growth DESIGN (LEC / VGF / VB) + thermal-field simulation.
Emits crystalGrowthDesign records with :fabricated false (G2). NEVER grows a crystal.
"""

from __future__ import annotations

from typing import Any


class BulkCrystalDesignCell:
    """InP single-crystal growth design + sim. fabricated=false (G2); In sourcing (G4)."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "hotaru R0 scaffold: bulk_crystal_design is design/sim only; live III-V "
            "crystal growth is PROHIBITED through R3 (ADR-2605265500 §2) — activation "
            "requires the R4+ re-evaluation gate (Council Lv7+)."
        )
