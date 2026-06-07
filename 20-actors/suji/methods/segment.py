"""suji (筋) — anthropometric sagittal-plane segment chain. Stdlib only.

The skeleton this actor reasons over is a 2-D (sagittal) articulated chain of rigid
body segments, exactly the `PlanarChain` articulation that kami-genesis solves
(Featherstone RNEA/CRBA, ADR-2605311500/1800). Each segment carries a mass, a
length, and a centre-of-mass (CoM) location along its long axis, derived from the
member's total body mass M (kg) and stature H (m) using standard regression
fractions:

  - segment mass as a fraction of M       — Winter, *Biomechanics and Motor
    Control of Human Movement* (4e), Table 4.1 (Dempster-derived).
  - segment length as a fraction of H     — Drillis & Contini (1966), as
    tabulated by Winter.
  - CoM as a fraction of segment length from the proximal joint — Winter Table 4.1.

These are population-average values for an adult; they are `:representative`
(G7 sourcing-honesty), not a scan of any individual. Feeding a real per-member
scan (kizashi 兆) carries 要配慮 PII and is encrypted-envelope gated (G4) — that is
kizashi's job, not suji's.

NON-DIAGNOSTIC (G1): this module computes masses and lengths. It says nothing
about health. It is the mass-distribution input to a statics problem, like the
section table of a beam in a CAD stress analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

GRAVITY = 9.80665  # m/s^2

# Winter (4e) Table 4.1 — segment mass as a fraction of total body mass M.
# Sagittal chain relevant to seated laptop posture. Trunk is split into
# thorax+abdomen (upper) and pelvis (lower) so a lumbar lean can be modelled.
_MASS_FRAC = {
    "head_neck": 0.081,
    "thorax_abdomen": 0.355,   # thorax 0.216 + abdomen 0.139 (Winter), lumped above L5/S1
    "pelvis": 0.142,
    "upper_arm": 0.028,        # one arm
    "forearm": 0.016,          # one arm
    "hand": 0.006,             # one arm
}

# Segment length as a fraction of stature H (Drillis & Contini via Winter).
_LEN_FRAC = {
    "head_neck": 0.182,        # vertex→C7/T1 region (head 0.130 + neck portion)
    "thorax_abdomen": 0.288,   # C7/T1 → L5/S1
    "pelvis": 0.095,           # L5/S1 → hip
    "upper_arm": 0.186,        # shoulder → elbow
    "forearm": 0.146,          # elbow → wrist
    "hand": 0.108,             # wrist → fingertip
}

# CoM location as a fraction of segment length, measured from the PROXIMAL joint
# (the joint nearer the body's base of support for the trunk chain; for limbs the
# proximal joint is the one nearer the trunk). Winter Table 4.1.
_COM_FRAC = {
    "head_neck": 0.55,         # head+neck CoM ~ above C7/T1 toward the skull
    "thorax_abdomen": 0.50,
    "pelvis": 0.50,
    "upper_arm": 0.436,
    "forearm": 0.430,
    "hand": 0.506,
}


@dataclass(frozen=True)
class Segment:
    """A rigid body segment of the sagittal chain."""

    name: str
    mass_kg: float            # segment mass
    length_m: float           # proximal joint → distal joint
    com_frac: float           # CoM from proximal joint, as fraction of length_m
    paired: bool = False      # True for limb segments that occur left+right

    @property
    def weight_n(self) -> float:
        """Gravitational force on this segment (a single segment; not the pair)."""
        return self.mass_kg * GRAVITY

    @property
    def com_m(self) -> float:
        """Distance of the CoM from the proximal joint, along the long axis."""
        return self.com_frac * self.length_m


@dataclass(frozen=True)
class BodyModel:
    """The member's anthropometric segment set, indexed by segment name."""

    total_mass_kg: float
    stature_m: float
    segments: dict[str, Segment]

    def seg(self, name: str) -> Segment:
        return self.segments[name]


def build_body(total_mass_kg: float = 70.0, stature_m: float = 1.70) -> BodyModel:
    """Construct the sagittal segment chain for a member of mass M and stature H.

    Defaults are a ~50th-percentile adult (`:representative`, G7). Paired limb
    segments (arm/forearm/hand) store the mass of ONE limb; callers that load both
    arms onto a single midline joint (e.g. both forearms on a keyboard) multiply by 2.
    """
    if total_mass_kg <= 0 or stature_m <= 0:
        raise ValueError("total_mass_kg and stature_m must be positive")
    paired = {"upper_arm", "forearm", "hand"}
    segments: dict[str, Segment] = {}
    for name in _MASS_FRAC:
        segments[name] = Segment(
            name=name,
            mass_kg=_MASS_FRAC[name] * total_mass_kg,
            length_m=_LEN_FRAC[name] * stature_m,
            com_frac=_COM_FRAC[name],
            paired=name in paired,
        )
    return BodyModel(total_mass_kg, stature_m, segments)


def head_mass_kg(total_mass_kg: float = 70.0) -> float:
    """Head+neck mass. ~5.4 kg at 67 kg matches Hansraj's 12-lb head (G7 anchor)."""
    return _MASS_FRAC["head_neck"] * total_mass_kg
