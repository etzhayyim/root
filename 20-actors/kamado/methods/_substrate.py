"""_substrate — re-export the shared infra-robotics substrate for kamado/methods.

Centralises the sys.path insert so every kamado method module (and its tests)
can flat-import the substrate exactly like hikari/methods imports its siblings:

    from _substrate import GasConcentrationPlant, PID, simulate, assert_civilian

The substrate lives in 20-actors/kuni-umi/robotics/ (the planetary-infra fleet
coordinator owns the reference engine; domain actors compose it).
"""

from __future__ import annotations

import pathlib
import sys

_ROBOTICS = pathlib.Path(__file__).resolve().parents[2] / "kuni-umi" / "robotics"
if str(_ROBOTICS) not in sys.path:
    sys.path.insert(0, str(_ROBOTICS))

from control import PID, ControlResult, simulate  # noqa: E402
from kinematics import PlanarArm, Pose, joint_trajectory  # noqa: E402
from plant import FirstOrderPlant, Plant  # noqa: E402
from safety import (  # noqa: E402
    SafetyEnvelope,
    SafetyError,
    assert_civilian,
    require_member_signature,
    witness_quorum_ok,
)

__all__ = [
    "PID",
    "ControlResult",
    "simulate",
    "PlanarArm",
    "Pose",
    "joint_trajectory",
    "FirstOrderPlant",
    "Plant",
    "SafetyEnvelope",
    "SafetyError",
    "assert_civilian",
    "require_member_signature",
    "witness_quorum_ok",
]
