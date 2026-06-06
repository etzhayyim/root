"""Phase state machine for the suji (筋) load_solve cell — the coded heart.

Drives one posture through static inverse dynamics → muscle %MVC, and enforces the
load-bearing invariant: the result is NON-DIAGNOSTIC by construction. The gates are
pure, unit-tested transitions; the cell's .solve() raises until Council activation.

Invariants enforced here:
  G1  — NON-DIAGNOSTIC (医師法 §17): the emitted payload may carry mechanical fields
        only (moments, forces, %MVC, kgf). Any diagnosis/disease/prescription/treatment
        key is REFUSED by construction (the field is structurally absent and the
        transition asserts the forbidden set is empty — the nusa/tazuna/kamado pattern).
  G9  — kotoba-EAVT: outputs are shaped as jointLoad + muscleTension Datoms.
  G10 — mechanically-grounded only: muscle groups come from the Hill-model SPECS table;
        no 経絡/気/波動 (kizashi N8).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# allow `from load import …` when run from the cell directory
_METHODS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "methods")
if _METHODS not in sys.path:
    sys.path.insert(0, _METHODS)

from load import solve_posture_loads          # noqa: E402
from muscle import solve_muscle_tensions       # noqa: E402
from posture import Posture                    # noqa: E402
from segment import build_body                 # noqa: E402

# Keys a strain/load payload may NEVER contain (医師法 §17 force-separation, G1).
FORBIDDEN_CLINICAL_KEYS = (
    "diagnosis", "disease", "icd", "icd10", "prescription", "treatment",
    "medication", "condition", "pathology", "prognosis",
)


class LoadPhase(Enum):
    INIT = "init"
    SOLVED = "solved"
    DISTRIBUTED = "distributed"
    NONDIAGNOSTIC_OK = "nondiagnostic_ok"
    EMITTED = "emitted"


@dataclass
class LoadState:
    phase: str = LoadPhase.INIT.value
    total_mass_kg: float = 70.0
    stature_m: float = 1.70
    posture: dict[str, Any] = field(default_factory=dict)
    joint_loads: list[dict[str, Any]] = field(default_factory=list)
    muscle_tensions: list[dict[str, Any]] = field(default_factory=list)
    emitted: list[dict[str, Any]] = field(default_factory=list)


def _posture_from_state(s: LoadState) -> Posture:
    p = s.posture
    return Posture(
        head_flexion_deg=float(p["headFlexDeg"]),
        trunk_flexion_deg=float(p.get("trunkFlexDeg", 5.0)),
        shoulder_flexion_deg=float(p.get("shoulderFlexDeg", 15.0)),
        elbow_flexion_deg=float(p.get("elbowFlexDeg", 90.0)),
        shoulder_elevation_deg=float(p.get("shoulderElevationDeg", 0.0)),
        arms_supported=bool(p.get("armsSupported", True)),
    )


def transition_static_inverse_dynamics(s: LoadState) -> LoadState:
    """RNEA gravity-term solve: posture → per-joint moment + cervical compressive load."""
    if s.phase != LoadPhase.INIT.value:
        raise ValueError(f"static_inverse_dynamics requires INIT, got {s.phase}")
    body = build_body(s.total_mass_kg, s.stature_m)
    loads = solve_posture_loads(body, _posture_from_state(s))
    out = [{
        "joint": "cervicothoracic", "momentNm": round(loads.cervical.extensor_moment_nm, 4),
        "compressiveKgf": round(loads.cervical.compressive_load_kgf, 2),
        "multVsHead": round(loads.cervical.multiplier_vs_head, 2),
    }]
    for j in loads.joints:
        if j.joint == "cervicothoracic":
            continue
        out.append({"joint": j.joint, "momentNm": round(j.moment_nm, 4)})
    s.joint_loads = out
    s._loads = loads  # type: ignore[attr-defined]
    s.phase = LoadPhase.SOLVED.value
    return s


def transition_muscle_distribute(s: LoadState) -> LoadState:
    """Hill-type distribution: joint moments → per-muscle force + %MVC (緊張)."""
    if s.phase != LoadPhase.SOLVED.value:
        raise ValueError(f"muscle_distribute requires SOLVED, got {s.phase}")
    body = build_body(s.total_mass_kg, s.stature_m)
    tensions = solve_muscle_tensions(body, _posture_from_state(s), s._loads)  # type: ignore[attr-defined]
    s.muscle_tensions = [
        {"group": t.name.replace("_", "-"), "forceN": round(t.force_n, 2),
         "mvcPct": round(t.mvc_pct, 2)}
        for t in tensions
    ]
    s.phase = LoadPhase.DISTRIBUTED.value
    return s


def transition_assert_nondiagnostic(s: LoadState) -> LoadState:
    """G1: refuse if any payload field is a clinical/diagnostic key (医師法 §17)."""
    if s.phase != LoadPhase.DISTRIBUTED.value:
        raise ValueError(f"assert_nondiagnostic requires DISTRIBUTED, got {s.phase}")
    for rec in s.joint_loads + s.muscle_tensions:
        bad = [k for k in rec if k.lower() in FORBIDDEN_CLINICAL_KEYS]
        if bad:
            raise ValueError(f"G1 non-diagnostic violation: clinical key(s) {bad} present")
    s.phase = LoadPhase.NONDIAGNOSTIC_OK.value
    return s


def transition_emit(s: LoadState) -> LoadState:
    """Shape the verified loads + tensions as kotoba Datoms (G9)."""
    if s.phase != LoadPhase.NONDIAGNOSTIC_OK.value:
        raise ValueError(f"emit requires NONDIAGNOSTIC_OK, got {s.phase}")
    pid = s.posture.get("postureId", "p-adhoc")
    datoms: list[dict[str, Any]] = []
    for i, j in enumerate(s.joint_loads):
        datoms.append({"load/id": f"{pid}-load-{i}", "load/posture": pid,
                       "load/joint": j["joint"], "load/moment-nm": j["momentNm"]})
    for i, m in enumerate(s.muscle_tensions):
        datoms.append({"muscle/id": f"{pid}-musc-{i}", "muscle/posture": pid,
                       "muscle/group": m["group"], "muscle/mvc-pct": m["mvcPct"]})
    s.emitted = datoms
    s.phase = LoadPhase.EMITTED.value
    return s
