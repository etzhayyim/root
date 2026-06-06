"""Phase state machine for the suji (筋) strain_accumulate cell — second coded cell.

Takes per-muscle tensions (%MVC, 緊張) + a held session duration and accumulates the
Rohmert sustained-isometric dose into a 強張り (stiffness) map. Enforces two invariants
structurally: NON-DIAGNOSTIC (G1) and SELF-REFERENCED Wellbecoming (G3).

Invariants enforced here:
  G1  — NON-DIAGNOSTIC (医師法 §17): the emitted strainReport may carry mechanical fields
        only; any clinical key is refused (the load_solve FORBIDDEN_CLINICAL_KEYS reuse).
  G3  — SELF-REFERENCED: a strain record carries NO population-ranking field (percentile /
        rank / cohort / vsOthers). Stiffness is compared only against the same member's
        other postures; the gate refuses any cross-person ranking key by construction.
  G9  — kotoba-EAVT: outputs are shaped as strainReport Datoms (as-of; 非終末論).
  G10 — mechanically-grounded only: bands come from strain.stiffness_band (Rohmert dose).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "methods")
if _METHODS not in sys.path:
    sys.path.insert(0, _METHODS)

from muscle import MuscleTension                       # noqa: E402
from strain import muscle_strain, stiffness_band       # noqa: E402

# G1 — reuse the load_solve clinical-key denylist (single source of the rule).
try:  # robust whether or not the cells dir is already on sys.path
    from load_solve.state_machine import FORBIDDEN_CLINICAL_KEYS  # noqa: E402
except Exception:  # pragma: no cover - fallback keeps the cell self-contained
    FORBIDDEN_CLINICAL_KEYS = (
        "diagnosis", "disease", "icd", "icd10", "prescription", "treatment",
        "medication", "condition", "pathology", "prognosis",
    )

# G3 — fields that would turn a self-referenced trajectory into a population ranking.
FORBIDDEN_RANKING_KEYS = (
    "percentile", "rank", "ranking", "cohort", "vsothers", "populationmean",
    "zscore", "leaderboard", "scoreofsoul",
)


class StrainPhase(Enum):
    INIT = "init"
    DOSED = "dosed"
    BANDED = "banded"
    SELF_REF_OK = "self_ref_ok"
    EMITTED = "emitted"


@dataclass
class StrainState:
    phase: str = StrainPhase.INIT.value
    posture_id: str = "p-adhoc"
    session_minutes: float = 120.0
    tensions: list[dict[str, Any]] = field(default_factory=list)   # [{group, mvcPct}]
    strains: list[dict[str, Any]] = field(default_factory=list)
    emitted: list[dict[str, Any]] = field(default_factory=list)


def transition_rohmert_dose(s: StrainState) -> StrainState:
    """Accumulate the Rohmert sustained-isometric dose per muscle (緊張 → 強張り)."""
    if s.phase != StrainPhase.INIT.value:
        raise ValueError(f"rohmert_dose requires INIT, got {s.phase}")
    if not s.tensions:
        raise ValueError("no muscle tensions to accumulate")
    out: list[dict[str, Any]] = []
    for t in s.tensions:
        mvc = float(t["mvcPct"])
        mt = MuscleTension(name=t["group"], force_n=0.0, f_max_n=1.0, mvc_pct=mvc)
        st = muscle_strain(mt, s.session_minutes)
        end = -1.0 if st.endurance_minutes == float("inf") else round(st.endurance_minutes, 2)
        out.append({
            "group": t["group"], "mvcPct": round(mvc, 2), "sessionMinutes": s.session_minutes,
            "enduranceMinutes": end, "stiffnessIndex": round(st.stiffness_index, 4),
        })
    s.strains = out
    s.phase = StrainPhase.DOSED.value
    return s


def transition_band(s: StrainState) -> StrainState:
    """Attach the coarse display band (Rohmert dose → low/moderate/high/very-high)."""
    if s.phase != StrainPhase.DOSED.value:
        raise ValueError(f"band requires DOSED, got {s.phase}")
    for rec in s.strains:
        rec["band"] = stiffness_band(rec["stiffnessIndex"])
    s.phase = StrainPhase.BANDED.value
    return s


def transition_assert_self_referenced(s: StrainState) -> StrainState:
    """G1 + G3: refuse clinical keys AND any population-ranking field."""
    if s.phase != StrainPhase.BANDED.value:
        raise ValueError(f"assert_self_referenced requires BANDED, got {s.phase}")
    for rec in s.strains:
        for k in rec:
            kl = k.lower()
            if kl in FORBIDDEN_CLINICAL_KEYS:
                raise ValueError(f"G1 non-diagnostic violation: clinical key '{k}'")
            if kl in FORBIDDEN_RANKING_KEYS:
                raise ValueError(f"G3 self-referenced violation: ranking key '{k}'")
        if not (0.0 <= rec["stiffnessIndex"] <= 1.0):
            raise ValueError(f"stiffnessIndex out of [0,1]: {rec['stiffnessIndex']}")
    s.phase = StrainPhase.SELF_REF_OK.value
    return s


def transition_emit(s: StrainState) -> StrainState:
    """Shape the verified strain map as kotoba strainReport Datoms (G9, as-of)."""
    if s.phase != StrainPhase.SELF_REF_OK.value:
        raise ValueError(f"emit requires SELF_REF_OK, got {s.phase}")
    datoms: list[dict[str, Any]] = []
    for i, rec in enumerate(s.strains):
        datoms.append({
            "strain/id": f"{s.posture_id}-strain-{i}", "strain/posture": s.posture_id,
            "strain/group": rec["group"], "strain/session-min": rec["sessionMinutes"],
            "strain/stiffness": rec["stiffnessIndex"], "strain/band": rec["band"],
            "strain/as-of": 0,
        })
    s.emitted = datoms
    s.phase = StrainPhase.EMITTED.value
    return s
