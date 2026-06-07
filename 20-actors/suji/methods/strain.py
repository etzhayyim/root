"""suji (筋) — sustained-load strain → 強張り (stiffness) over a work session. Stdlib only.

緊張 (tension, the instantaneous %MVC from `muscle.py`) becomes 強張り (stiffness) when
it is held. A static posture is an isometric contraction sustained for the length of a
work session, and isometric load has a known endurance limit that falls steeply with
%MVC (Rohmert, 1960; the classic "15% MVC = sustainable, above it fatigue accrues"
result). Two mechanisms produce stiffness:

  1. ACUTE — at moderate/high %MVC the muscle approaches its endurance time T_end(f);
     the closer held-time gets to T_end, the more metabolite accumulation / fatigue.
  2. CHRONIC low-load — even below the 15% threshold, continuously recruited low-
     threshold motor units ("Cinderella" units, Hägg) accrue strain over hours; this
     is the dominant mechanism of desk-work 肩こり (stiff shoulders/neck).

Endurance model (representative, G7/G10 — a mechanistic power law, NOT a clinical
prescription): T_end(f) ≈ 0.2 · f^-2.32 minutes, fit so that 50% MVC ≈ 1 min,
25% ≈ 5 min, 15% ≈ ~16 min. Stiffness index ∈ [0,1) = 1 - exp(-dose), where dose
combines the acute and chronic terms over the session.

NON-DIAGNOSTIC (G1): a stiffness index is a normalised load-time dose, not a medical
finding. It maps to "this muscle has been working hard for a long time", which is the
mechanism of ordinary postural discomfort — never a diagnosis (mitate/iyashi own that).
SELF-REFERENCED (G3): indices are compared against the SAME member's other postures
(non-終末 trajectory), never ranked across people.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from muscle import MuscleTension

CHRONIC_THRESHOLD_PCT = 2.0     # below this %MVC, essentially no sustained recruitment
CHRONIC_WEIGHT = 0.45           # weight of the chronic low-load dose vs acute
ENDURANCE_FLOOR_PCT = 8.0       # below this %MVC, acute endurance treated as effectively long


def endurance_minutes(mvc_pct: float) -> float:
    """Rohmert-type isometric endurance time (minutes) at a given %MVC.

    Returns math.inf below the endurance floor (low-load static work has no acute
    failure point; chronic accumulation handles that regime).
    """
    if mvc_pct <= ENDURANCE_FLOOR_PCT:
        return math.inf
    f = mvc_pct / 100.0
    return 0.2 * f ** -2.32


@dataclass(frozen=True)
class MuscleStrain:
    name: str
    mvc_pct: float
    session_minutes: float
    endurance_minutes: float    # acute endurance limit at this %MVC (inf if low-load)
    acute_dose: float           # session / endurance (0 if endurance is inf)
    chronic_dose: float         # low-load accumulation
    stiffness_index: float      # [0,1) — the 強張り score (1 - exp(-total dose))
    over_endurance: bool        # held longer than the acute endurance limit


def muscle_strain(t: MuscleTension, session_minutes: float) -> MuscleStrain:
    """Stiffness accrued by one muscle holding `mvc_pct` for `session_minutes`."""
    if session_minutes < 0:
        raise ValueError("session_minutes must be >= 0")
    t_end = endurance_minutes(t.mvc_pct)
    acute = 0.0 if math.isinf(t_end) else session_minutes / t_end
    # chronic dose: load above the recruitment threshold, accumulated per hour.
    excess = max(0.0, t.mvc_pct - CHRONIC_THRESHOLD_PCT) / 100.0
    chronic = CHRONIC_WEIGHT * excess * (session_minutes / 60.0)
    dose = acute + chronic
    stiffness = 1.0 - math.exp(-dose)
    return MuscleStrain(
        name=t.name,
        mvc_pct=t.mvc_pct,
        session_minutes=session_minutes,
        endurance_minutes=t_end,
        acute_dose=acute,
        chronic_dose=chronic,
        stiffness_index=stiffness,
        over_endurance=(not math.isinf(t_end)) and session_minutes > t_end,
    )


def session_strain(tensions: list[MuscleTension], session_minutes: float = 120.0) -> list[MuscleStrain]:
    """Stiffness map for a whole work session (default 2 hours of continuous posture)."""
    return [muscle_strain(t, session_minutes) for t in tensions]


def stiffness_band(stiffness_index: float) -> str:
    """A coarse human-readable band for the stiffness index (display only, non-diagnostic)."""
    if stiffness_index < 0.20:
        return "low"
    if stiffness_index < 0.45:
        return "moderate"
    if stiffness_index < 0.70:
        return "high"
    return "very-high"
