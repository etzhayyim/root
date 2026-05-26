"""isaaclab.controllers — high-level joint-space + task-space controllers.

Mirror of `isaaclab.controllers` (Isaac Lab 1.x). Provides drop-in controllers
that consume a current articulation state + a task-space command and emit
joint-space deltas (or torques) for downstream `JointPositionAction` /
`JointEffortAction` to apply.

R1.x scope:
  - DifferentialIKController — Jacobian-based IK (damped least squares /
    pseudoinverse) for arm reaching tasks. The canonical Isaac Lab API for
    manipulators; pairs with iter 40's JointPositionAction.

Future R1.x adds:
  - OperationalSpaceController (OSC) — task-space torque control
  - ImpedanceController         — Cartesian stiffness/damping
"""

from .differential_ik import (
    DifferentialIKController,
    DifferentialIKControllerCfg,
)

__all__ = ["DifferentialIKController", "DifferentialIKControllerCfg"]
