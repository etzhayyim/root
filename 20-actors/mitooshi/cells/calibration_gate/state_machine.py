"""Phase state machine for the mitooshi calibration_gate (見通し) cell.

The G7/G9/G12 promotion membrane. A model version goes LIVE (promoted=true → its
forecasts are published) ONLY after this gate CLEARS it. It clears ONLY if:
  G12 — the model BEATS its baseline on the primary proper score (skill > 0); an
        unskilled model is refused promotion (no pseudoscience, no overfit-to-noise).
  G7  — calibration deviation ≤ threshold (the PIT histogram is acceptably uniform);
        a miscalibrated / overconfident model is refused.
  G9  — the promotion is signed by a member/operator DID; a server signature is REFUSED
        (no-server-key, ADR-2605231525). serverHeldKey is structurally false.
  G1  — no forecast in the evaluated set asserts a point (carried through from issuance).

REFUSAL gate (like precursor_safety / hotaru): it does not auto-promote, it refuses to
clear a model that violates a gate. Council Lv6+ + operator is the outward G10 boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

DEFAULT_DEVIATION_MAX = 0.4    # PIT L1-deviation ceiling for "calibrated enough"


class GatePhase(Enum):
    INIT = "init"
    CLEARED = "cleared"
    REFUSED = "refused"


@dataclass
class GateState:
    phase: str = GatePhase.INIT.value
    model_id: str = ""
    to_version: int = 2
    skill: float = 0.0
    deviation: float = 0.0
    deviation_max: float = DEFAULT_DEVIATION_MAX
    signed_by: str = ""          # member/operator DID; "" or starting with "server" is refused
    point_asserted_any: bool = False
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> GateState:
    return GateState(**d.get("cell_state", {}))


def review_promotion(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.model_id = state.get("model_id", cs.model_id)
    cs.to_version = int(state.get("to_version", cs.to_version))
    cs.skill = float(state.get("skill", cs.skill))
    cs.deviation = float(state.get("deviation", cs.deviation))
    cs.deviation_max = float(state.get("deviation_max", cs.deviation_max))
    cs.signed_by = state.get("signed_by", cs.signed_by) or ""
    cs.point_asserted_any = bool(state.get("point_asserted_any", cs.point_asserted_any))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = GatePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    # G1 — no point assertion may have slipped through.
    if cs.point_asserted_any:
        return refuse("G1: an evaluated forecast asserts a deterministic point; promotion refused (非終末論)")
    # G12 — must beat the baseline.
    if not cs.skill > 0.0:
        return refuse(f"G12: model {cs.model_id!r} skill {cs.skill:.4f} ≤ 0; does not beat baseline; promotion refused")
    # G7 — must be calibrated enough.
    if cs.deviation > cs.deviation_max:
        return refuse(f"G7: calibration deviation {cs.deviation:.4f} > {cs.deviation_max:.4f}; miscalibrated; promotion refused")
    # G9 — no-server-key: member/operator signature required.
    if not cs.signed_by or cs.signed_by.lower().startswith("server"):
        return refuse(f"G9: promotion of {cs.model_id!r} needs a member/operator signature; server signature refused (no-server-key)")

    cs.payload = {
        "modelId": cs.model_id,
        "toVersion": cs.to_version,
        "skill": round(cs.skill, 6),
        "deviation": round(cs.deviation, 6),
        "signedBy": cs.signed_by,
        "serverHeldKey": False,
        "promoted": True,
    }
    cs.refusal = ""
    cs.phase = GatePhase.CLEARED.value
    return {"cell_state": cs.__dict__}
