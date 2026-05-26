"""isaaclab.envs.mdp — Manager-Based MDP term builders + standard functions.

Mirrors `isaaclab.envs.mdp` (Isaac Lab 1.x). Provides the building blocks
for composing RL environments declaratively via observation/reward/event
term groups. Standard mdp.* functions cover the canonical Cartpole / DP
training surface.

Term classes:
  - ObsTerm   — observation function + params + clip/scale
  - RewTerm   — reward function + weight + params
  - EventTerm — reset/event hook function + params

Group classes:
  - ObsGroup  — composes multiple ObsTerm into a single observation vector
  - RewGroup  — composes multiple RewTerm into a scalar reward (sum of weighted)
  - EventGroup — composes EventTerm into a reset/event handler

Standard mdp.* functions:
  - observations: joint_pos_rel, joint_vel_rel, base_lin_vel, base_ang_vel,
                  last_action, generated_commands
  - rewards: is_alive, is_terminated, joint_pos_l2, joint_vel_l2, action_l2,
             action_rate_l2, joint_torques_l2
  - events: reset_joints_by_offset, reset_joints_to_default,
            randomize_rigid_body_mass, randomize_rigid_body_material
  - commands: CommandGeneratorBase + NullCommand + UniformVelocityCommand
              + UniformPose3DCommand (random per-env goal targets with
              resampling interval; integrates with mdp.generated_commands)
  - actions:  ActionManager + JointEffortAction / JointPositionAction /
              JointVelocityAction (action vector composition + dispatch
              onto env effort buffers; PD/P controllers for position/velocity
              target modes)

stdlib-only.
"""

from .actions import (
    ActionManager,
    ActionTerm,
    ActionTermCfgBase,
    JointEffortAction,
    JointEffortActionCfg,
    JointPositionAction,
    JointPositionActionCfg,
    JointVelocityAction,
    JointVelocityActionCfg,
)
from .commands import (
    CommandCfgBase,
    CommandGeneratorBase,
    NullCommand,
    UniformPose3DCommand,
    UniformPose3DCommandCfg,
    UniformPose3DRanges,
    UniformVelocityCommand,
    UniformVelocityCommandCfg,
    UniformVelocityRanges,
)
from .events import (
    EventTerm,
    randomize_rigid_body_mass,
    reset_joints_by_offset,
    reset_joints_to_default,
)
from .observations import (
    ObsGroup,
    ObsTerm,
    base_ang_vel,
    base_lin_vel,
    generated_commands,
    joint_pos_rel,
    joint_vel_rel,
    last_action,
)
from .rewards import (
    RewGroup,
    RewTerm,
    action_l2,
    action_rate_l2,
    is_alive,
    is_terminated,
    joint_pos_l2,
    joint_torques_l2,
    joint_vel_l2,
)

__all__ = [
    # Term classes
    "ObsTerm", "RewTerm", "EventTerm",
    "ObsGroup", "RewGroup",
    # Observation functions
    "joint_pos_rel", "joint_vel_rel",
    "base_lin_vel", "base_ang_vel",
    "last_action", "generated_commands",
    # Reward functions
    "is_alive", "is_terminated",
    "joint_pos_l2", "joint_vel_l2",
    "action_l2", "action_rate_l2", "joint_torques_l2",
    # Event functions
    "reset_joints_by_offset", "reset_joints_to_default",
    "randomize_rigid_body_mass",
    # Command generators
    "CommandCfgBase", "CommandGeneratorBase",
    "NullCommand",
    "UniformVelocityCommand", "UniformVelocityCommandCfg", "UniformVelocityRanges",
    "UniformPose3DCommand", "UniformPose3DCommandCfg", "UniformPose3DRanges",
    # Action terms + manager
    "ActionTerm", "ActionTermCfgBase", "ActionManager",
    "JointEffortAction", "JointEffortActionCfg",
    "JointPositionAction", "JointPositionActionCfg",
    "JointVelocityAction", "JointVelocityActionCfg",
]
