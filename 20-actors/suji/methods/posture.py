"""suji (筋) — laptop-workstation → sagittal posture (joint angles). Stdlib only.

This is the kinematic front-end: it turns an ergonomic *setup* (where the screen
is, where the keyboard is, whether the back is supported) into the joint angles of
the sagittal chain. Those angles are the input to the static inverse-dynamics solve
(`load.py`). The mapping is a documented, monotonic ergonomic model — NOT a
biometric measurement (that is kizashi 兆, encrypted-gated). All angles are degrees.

Angle conventions (sagittal plane, sign = direction of gravitational loading):

  - head_flexion_deg   : forward tilt of the head from upright-neutral. 0 = ear over
                         shoulder; larger = "looking down at the screen" (tech-neck).
                         The dominant driver of cervical load (Hansraj 2014).
  - trunk_flexion_deg  : forward lean of the thorax from vertical. 0 = upright/supported.
  - shoulder_flexion_deg: elevation of the upper arm forward from the side. Reaching
                         forward/up to a keyboard raises this; loads the deltoid +
                         upper trapezius (scapular stabilisation).
  - elbow_flexion_deg  : 0 = straight; ~90 = forearm horizontal (neutral typing).
  - shoulder_elevation : scapular shrug (deg-equivalent), driven by a keyboard that
                         is too high relative to the seated elbow. Loads upper trap.

Lower screen → more head flexion. Lower/unsupported seat-back → more trunk flexion.
Higher keyboard or no armrest → more shoulder flexion + scapular elevation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Workstation:
    """An ergonomic setup. Heights are relative to the seated eye / elbow as noted."""

    name: str
    # vertical offset of screen-centre BELOW seated eye level, cm (positive = below).
    # laptop on lap ~ 35 cm below eye; laptop on desk ~ 20 cm; external monitor at
    # eye height ~ 0 cm.
    screen_below_eye_cm: float
    # vertical offset of the keyboard home row ABOVE the seated elbow, cm
    # (positive = above → shoulder shrug/reach). external keyboard at elbow ~ 0.
    keyboard_above_elbow_cm: float
    back_supported: bool          # is the thoracolumbar spine supported by a backrest?
    arms_supported: bool          # are the forearms resting (desk/armrest) vs floating?


@dataclass(frozen=True)
class Posture:
    """Sagittal joint angles (deg) plus context flags consumed by load.py."""

    head_flexion_deg: float
    trunk_flexion_deg: float
    shoulder_flexion_deg: float
    elbow_flexion_deg: float
    shoulder_elevation_deg: float
    arms_supported: bool


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def posture_from_workstation(ws: Workstation) -> Posture:
    """Map an ergonomic setup to sagittal joint angles (documented monotonic model).

    Calibration choices (illustrative, G7 — not a clinical goniometry standard):
      - head flexion ≈ 1.1° per cm the screen sits below eye level, capped at 60°
        (the Hansraj table tops out at 60°). 0 cm below → ~5° resting flexion.
      - trunk flexion: 5° if supported, else 20° self-supported slump.
      - shoulder flexion ≈ 0.8° per cm keyboard-above-elbow + a 15° forward-reach base.
      - scapular elevation ≈ 1.2° per cm keyboard-above-elbow (shrug toward a high board).
      - elbow ~ 90° neutral typing (kept fixed; forearm horizontal).
    """
    head = _clamp(5.0 + 1.1 * ws.screen_below_eye_cm, 0.0, 60.0)
    trunk = 5.0 if ws.back_supported else 20.0
    shoulder = _clamp(15.0 + 0.8 * max(0.0, ws.keyboard_above_elbow_cm), 0.0, 90.0)
    elevation = _clamp(1.2 * max(0.0, ws.keyboard_above_elbow_cm), 0.0, 45.0)
    return Posture(
        head_flexion_deg=head,
        trunk_flexion_deg=trunk,
        shoulder_flexion_deg=shoulder,
        elbow_flexion_deg=90.0,
        shoulder_elevation_deg=elevation,
        arms_supported=ws.arms_supported,
    )


# Three reference laptop scenarios — the answer to "what does a laptop posture do".
LAPTOP_ON_LAP = Workstation(
    name="laptop-on-lap",
    screen_below_eye_cm=35.0,        # screen far below eye → deep head flexion
    keyboard_above_elbow_cm=-5.0,    # keyboard low, but arms unsupported on lap
    back_supported=False,
    arms_supported=False,
)
LAPTOP_ON_DESK = Workstation(
    name="laptop-on-desk",
    screen_below_eye_cm=20.0,
    keyboard_above_elbow_cm=6.0,     # raised laptop → mild shrug/reach
    back_supported=True,
    arms_supported=True,
)
EXTERNAL_MONITOR_EYE_LEVEL = Workstation(
    name="external-monitor+keyboard",
    screen_below_eye_cm=0.0,         # monitor top at eye level → near-neutral neck
    keyboard_above_elbow_cm=0.0,     # external keyboard at elbow height
    back_supported=True,
    arms_supported=True,
)

REFERENCE_WORKSTATIONS = [LAPTOP_ON_LAP, LAPTOP_ON_DESK, EXTERNAL_MONITOR_EYE_LEVEL]
