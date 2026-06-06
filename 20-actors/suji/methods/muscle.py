"""suji (筋) — muscle tension: distribute joint moments to muscles (%MVC). Stdlib only.

The muscles half. Each static joint moment from `load.py` is balanced by a prime-mover
muscle group acting at its anatomical moment arm (a Hill-type force = moment / arm).
Dividing by the muscle's maximum force F_max = PCSA × specific-tension gives the
%MVC (percent of maximum voluntary contraction) — the mechanical meaning of 緊張
("tension"): how hard that muscle must work just to hold the posture.

Muscle groups (laptop-relevant sagittal set):
  - cervical_extensors  (splenius / semispinalis) — hold the head; tech-neck driver.
  - upper_trapezius     — suspend/elevate the shoulder girdle; the 肩こり muscle.
  - levator_scapulae    — co-stabiliser of the scapula under shrug + forward head.
  - anterior_deltoid    — hold the arm forward to the keyboard.
  - erector_spinae      — resist the lumbar lean (trunk flexion).

PCSA / moment-arm / specific-tension values are population `:representative` (G7).
specific tension ≈ 60 N/cm² (Buchanan/Zajac musculotendon range). The cervical leg
is anchored to Hansraj; the others are mechanistically grounded but illustrative
(G10 — mechanical moment balance only; NO 経絡/気/波動 stiffness theory, kizashi N8).

NON-DIAGNOSTIC (G1): %MVC is a force ratio, not a diagnosis. High %MVC is "this
muscle is working hard", never "you have a condition".
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from load import PostureLoads
from segment import GRAVITY, BodyModel

SPECIFIC_TENSION_N_CM2 = 60.0


@dataclass(frozen=True)
class MuscleSpec:
    name: str
    pcsa_cm2: float            # physiological cross-sectional area
    moment_arm_m: float

    @property
    def f_max_n(self) -> float:
        return self.pcsa_cm2 * SPECIFIC_TENSION_N_CM2


# Representative bilateral group PCSAs (sum of left+right where paired).
SPECS = {
    "cervical_extensors": MuscleSpec("cervical_extensors", pcsa_cm2=12.0, moment_arm_m=0.020),
    "upper_trapezius":    MuscleSpec("upper_trapezius",    pcsa_cm2=9.0,  moment_arm_m=0.025),
    "levator_scapulae":   MuscleSpec("levator_scapulae",   pcsa_cm2=5.0,  moment_arm_m=0.020),
    "anterior_deltoid":   MuscleSpec("anterior_deltoid",   pcsa_cm2=10.0, moment_arm_m=0.030),
    "erector_spinae":     MuscleSpec("erector_spinae",     pcsa_cm2=34.0, moment_arm_m=0.055),
}


@dataclass(frozen=True)
class MuscleTension:
    name: str
    force_n: float
    f_max_n: float
    mvc_pct: float             # 100 * force / f_max — the tension level (緊張)


def _tension(name: str, force_n: float) -> MuscleTension:
    spec = SPECS[name]
    force_n = max(0.0, force_n)
    return MuscleTension(name, force_n, spec.f_max_n, 100.0 * force_n / spec.f_max_n)


def solve_muscle_tensions(body: BodyModel, posture, loads: PostureLoads) -> list[MuscleTension]:
    """Map the posture's joint loads to per-muscle force and %MVC."""
    out: list[MuscleTension] = []

    # cervical extensors balance the cervicothoracic moment at their moment arm.
    cerv_arm = SPECS["cervical_extensors"].moment_arm_m
    out.append(_tension("cervical_extensors", loads.cervical.extensor_moment_nm / cerv_arm))

    # anterior deltoid balances the shoulder flexion moment.
    sh = next(j for j in loads.joints if j.joint == "shoulder")
    out.append(_tension("anterior_deltoid", sh.moment_nm / SPECS["anterior_deltoid"].moment_arm_m))

    # erector spinae balance the lumbosacral moment.
    ls = next(j for j in loads.joints if j.joint == "lumbosacral")
    out.append(_tension("erector_spinae", ls.moment_nm / SPECS["erector_spinae"].moment_arm_m))

    # upper trapezius: suspends/elevates the shoulder girdle. Loaded by (a) scapular
    # elevation toward a high keyboard, (b) suspending the arm when unsupported, and
    # (c) co-contraction that rises with forward-head/screen-down posture (EMG-grounded,
    # illustrative G10 composite).
    arm_each = (body.seg("upper_arm").mass_kg + body.seg("forearm").mass_kg
                + body.seg("hand").mass_kg)
    arm_w_pair = arm_each * GRAVITY * 2.0
    elev = math.sin(math.radians(posture.shoulder_elevation_deg))
    support_factor = 1.0 if not posture.arms_supported else 0.4
    head_co = 0.15 * loads.cervical.head_weight_n * math.sin(math.radians(posture.head_flexion_deg))
    trap_force = arm_w_pair * (0.3 + 0.7 * elev) * support_factor + head_co
    out.append(_tension("upper_trapezius", trap_force))

    # levator scapulae: scales with the same shrug + forward-head drivers, smaller share.
    lev_force = 0.5 * (arm_w_pair * (0.2 + 0.6 * elev) * support_factor) + 0.6 * head_co
    out.append(_tension("levator_scapulae", lev_force))

    return out
