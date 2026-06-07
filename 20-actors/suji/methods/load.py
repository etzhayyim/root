"""suji (筋) — static inverse dynamics: posture → joint moments + spinal load. Stdlib only.

This is the bones half. Given the sagittal joint angles (`posture.py`) and the
segment masses (`segment.py`), it solves the STATIC inverse-dynamics problem: the
gravitational moment each joint must resist to hold the posture against gravity.
This is the gravity term of the Featherstone Recursive Newton-Euler Algorithm
(RNEA) reduced to statics — the exact computation kami-genesis runs over a
`PlanarChain` (ADR-2605311500/1800); here it is the closed-form static special case
so it runs in stdlib and is independently checkable.

EMPIRICAL ANCHOR (G7/G10) — the cervical (neck) model reproduces the published
forward-head-posture loads of Hansraj (2014), *Surgical Technology International* 25,
"Assessment of stresses in the cervical spine caused by posture and position of the
head": neutral ≈ head weight, rising to ~5× head weight at 60° flexion (the
"60 lb tech-neck" figure). See `test_load.py::test_reproduces_hansraj_table`.

NON-DIAGNOSTIC (G1, 医師法 §17): every output is a mechanical quantity — a moment
(N·m), a muscle force (N), a compressive load (N / kg-force). None of them is a
diagnosis, a disease, or a treatment. This is the structural-engineering stress
analysis of a posture, not a medical examination.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from segment import GRAVITY, BodyModel

# --- Cervical lever model (Hansraj-calibrated) -------------------------------
# The cervical extensors (splenius capitis / semispinalis) hold the head against
# its forward gravitational moment about the C7/T1 pivot. The compressive load on
# the cervical spine is the muscle force plus the head's axial weight component.
#
#   L(theta) = W_head * ( RHO * sin(theta) + cos(theta) )
#
# where RHO = (effective head-CoM horizontal lever) / (cervical extensor moment arm).
# With the anatomical defaults below RHO = 5.0, which reproduces Hansraj's table
# (neutral→1×, 15°→~2.3×, 30°→~3.3×, 45°→~4.2×, 60°→~4.8× head weight).
HEAD_COM_LEVER_M = 0.10      # effective horizontal lever of head CoM at full flexion
CERVICAL_EXT_ARM_M = 0.02    # cervical extensor moment arm (posterior to vertebral body)


@dataclass(frozen=True)
class CervicalLoad:
    head_flexion_deg: float
    head_weight_n: float
    extensor_moment_nm: float       # gravitational moment about C7/T1
    extensor_force_n: float         # cervical extensor muscle force to balance it
    compressive_load_n: float       # total compressive load on the cervical spine
    compressive_load_kgf: float     # same, in kg-force (the Hansraj unit)
    multiplier_vs_head: float       # compressive_load / head_weight (Hansraj's "×")


def cervical_load(
    head_flexion_deg: float,
    head_weight_n: float,
    head_com_lever_m: float = HEAD_COM_LEVER_M,
    extensor_arm_m: float = CERVICAL_EXT_ARM_M,
) -> CervicalLoad:
    """Forward-head-posture cervical load. Reproduces Hansraj (2014) (G7 anchor)."""
    if head_weight_n <= 0:
        raise ValueError("head_weight_n must be positive")
    if extensor_arm_m <= 0:
        raise ValueError("extensor_arm_m must be positive")
    theta = math.radians(head_flexion_deg)
    rho = head_com_lever_m / extensor_arm_m
    moment = head_weight_n * head_com_lever_m * math.sin(theta)
    ext_force = moment / extensor_arm_m
    compressive = head_weight_n * (rho * math.sin(theta) + math.cos(theta))
    return CervicalLoad(
        head_flexion_deg=head_flexion_deg,
        head_weight_n=head_weight_n,
        extensor_moment_nm=moment,
        extensor_force_n=ext_force,
        compressive_load_n=compressive,
        compressive_load_kgf=compressive / GRAVITY,
        multiplier_vs_head=compressive / head_weight_n,
    )


# --- Generic static joint moment (RNEA gravity term) -------------------------
@dataclass(frozen=True)
class JointLoad:
    joint: str                 # "cervicothoracic" | "shoulder" | "elbow" | "lumbosacral"
    moment_nm: float           # net gravitational moment the joint must resist
    note: str = ""


def _horizontal_lever(length_m: float, com_frac: float, flexion_deg: float) -> float:
    """Horizontal moment arm of a flexed segment's CoM about its proximal joint.

    A segment flexed `flexion_deg` forward from vertical has its CoM a horizontal
    distance length*com_frac*sin(flexion) ahead of the proximal joint — the lever
    on which gravity acts. (Pure-vertical segment → zero lever.)
    """
    return length_m * com_frac * math.sin(math.radians(flexion_deg))


def shoulder_moment(body: BodyModel, shoulder_flexion_deg: float, elbow_flexion_deg: float,
                    arms_supported: bool) -> JointLoad:
    """Gravitational moment about the glenohumeral joint from the held-out arm(s).

    If the forearms are supported (desk/armrest) the distal arm weight is reacted by
    the support, so only the upper-arm contributes; unsupported, the whole limb hangs
    on the deltoid/scapular stabilisers. Both arms load the shoulder girdle → ×2.
    """
    ua = body.seg("upper_arm")
    fa = body.seg("forearm")
    hand = body.seg("hand")
    # upper-arm CoM lever about shoulder
    m = ua.weight_n * _horizontal_lever(ua.length_m, ua.com_frac, shoulder_flexion_deg)
    if not arms_supported:
        # forearm + hand hang at the elbow, a further lever out from the shoulder
        elbow_x = ua.length_m * math.sin(math.radians(shoulder_flexion_deg))
        fa_x = elbow_x + _horizontal_lever(fa.length_m, fa.com_frac, 90.0 - elbow_flexion_deg)
        hand_x = elbow_x + fa.length_m * math.sin(math.radians(90.0 - elbow_flexion_deg)) \
            + _horizontal_lever(hand.length_m, hand.com_frac, 90.0 - elbow_flexion_deg)
        m += fa.weight_n * fa_x + hand.weight_n * hand_x
    return JointLoad("shoulder", m * 2.0,  # both arms
                     note="forearms supported" if arms_supported else "arms unsupported (hanging)")


def lumbosacral_moment(body: BodyModel, trunk_flexion_deg: float,
                       head: CervicalLoad) -> JointLoad:
    """Gravitational moment about L5/S1 from the leaned trunk + head-arm load above it.

    Erector spinae must resist the forward moment of the thorax/abdomen mass plus the
    head carried at the top of the chain. (Pelvis sits on the seat → not above L5/S1.)
    """
    thorax = body.seg("thorax_abdomen")
    m = thorax.weight_n * _horizontal_lever(thorax.length_m, thorax.com_frac, trunk_flexion_deg)
    # head mass rides at the top of the trunk; its horizontal offset adds a lever
    head_x = thorax.length_m * math.sin(math.radians(trunk_flexion_deg))
    m += head.head_weight_n * head_x
    return JointLoad("lumbosacral", m, note="trunk lean + carried head")


@dataclass(frozen=True)
class PostureLoads:
    cervical: CervicalLoad
    joints: list[JointLoad]   # cervicothoracic (from cervical), shoulder, lumbosacral


def solve_posture_loads(body: BodyModel, posture) -> PostureLoads:
    """Full static inverse-dynamics solve for a posture (the RNEA gravity term)."""
    from segment import head_mass_kg  # local import to keep module graph shallow
    head_w = head_mass_kg(body.total_mass_kg) * GRAVITY
    cerv = cervical_load(posture.head_flexion_deg, head_w)
    joints = [
        JointLoad("cervicothoracic", cerv.extensor_moment_nm, note="cervical extensor moment"),
        shoulder_moment(body, posture.shoulder_flexion_deg, posture.elbow_flexion_deg,
                        posture.arms_supported),
        lumbosacral_moment(body, posture.trunk_flexion_deg, cerv),
    ]
    return PostureLoads(cervical=cerv, joints=joints)
