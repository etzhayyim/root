"""Action terms — composable action processors.

Mirror of `isaaclab.envs.mdp.actions` (Isaac Lab 1.x). Action terms slice a
flat action vector into per-joint commands, optionally apply scale + offset,
and dispatch the result onto the env's articulation via one of three
control modes (effort / position / velocity).

Surface:
  - ActionTerm                    — abstract base; subclass implements
                                     `process_actions(raw)` (transform raw →
                                     processed) + `apply_actions(env)`
                                     (write the processed action onto the env)
  - JointEffortActionCfg / JointEffortAction
        — torque-control: writes scaled raw action directly to
          `env._applied_force` / `env._applied_torques` (matches the existing
          Cartpole / DoublePendulum action injection convention)
  - JointPositionActionCfg / JointPositionAction
        — position target with PD controller: writes
          K_p * (target - current) - K_d * current_vel into effort
  - JointVelocityActionCfg / JointVelocityAction
        — velocity target with P controller: writes
          K_p * (target - current_vel) into effort

ActionManager composes one or more ActionTerm into a single action vector.
`process_actions(raw)` slices `raw` by per-term offsets and dispatches each
slice to its term's process_actions. `apply_actions(env)` then triggers
every term's apply_actions in registration order — terms write into env
state which is consumed by the env's `_physics_step()` on the next sim
tick.

Standard usage:

    am = ActionManager([
        JointEffortAction(JointEffortActionCfg(joint_names=[0], scale=10.0)),
    ])
    raw_action = [0.3]                          # 1-DoF for Cartpole
    am.process_actions(raw_action)
    am.apply_actions(env)                       # writes env._applied_force
    env._physics_step()                         # consumes the action

Pure stdlib. Reuses no external state; each term carries its own buffers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ────────────────────────────────────────────────────────────────────────────
# ActionTerm base
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class ActionTermCfgBase:
    """Base cfg for every ActionTerm subclass.

    `joint_names` is a list of integer joint indices (env-specific) the
    action term targets. For Cartpole the convention is `[0]` = cart slider.
    Real Isaac Lab uses joint NAME strings + regex; the nv_compat surface
    keeps it index-based for kernel-level clarity.

    `scale` multiplies the raw action element-wise; `offset` adds.
    `action_dim` is OPTIONAL — when None it's inferred from `joint_names`
    (one action element per joint). Override only for terms that want
    one action element to drive multiple joints (rare).
    """
    asset_name: str = "robot"
    joint_names: List[int] = field(default_factory=list)
    scale: float = 1.0
    offset: float = 0.0
    action_dim: Optional[int] = None


class ActionTerm:
    """Abstract base for one action processor.

    Subclasses MUST implement:
      - `apply_actions(env)`   — write `self.processed_actions` onto env
      - (optionally) `process_actions(raw)` — transform `raw` → processed

    Base provides:
      - `action_dim`           — int, computed from cfg
      - `raw_actions`          — most recent raw action slice
      - `processed_actions`    — most recent processed action (scale + offset
                                  by default; subclasses override the
                                  transformation if more is needed)
      - `reset()`              — clear buffers
    """

    cfg: ActionTermCfgBase

    def __init__(self, cfg: ActionTermCfgBase):
        self.cfg = cfg
        if not cfg.joint_names:
            raise ValueError(f"{type(self).__name__}.cfg.joint_names must be non-empty")
        self._dim: int = cfg.action_dim if cfg.action_dim is not None else len(cfg.joint_names)
        self.raw_actions: List[float] = [0.0] * self._dim
        self.processed_actions: List[float] = [0.0] * self._dim

    @property
    def action_dim(self) -> int:
        return self._dim

    @property
    def joint_names(self) -> List[int]:
        return list(self.cfg.joint_names)

    def process_actions(self, raw: List[float]) -> None:
        """Default impl: scale + offset element-wise into processed_actions."""
        if len(raw) != self._dim:
            raise ValueError(
                f"{type(self).__name__}: expected {self._dim} action elements, got {len(raw)}"
            )
        self.raw_actions = list(raw)
        s, o = self.cfg.scale, self.cfg.offset
        self.processed_actions = [r * s + o for r in raw]

    def apply_actions(self, env: Any) -> None:
        raise NotImplementedError("ActionTerm.apply_actions must be overridden")

    def reset(self) -> None:
        self.raw_actions = [0.0] * self._dim
        self.processed_actions = [0.0] * self._dim


# ────────────────────────────────────────────────────────────────────────────
# JointEffortAction (torque control)
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class JointEffortActionCfg(ActionTermCfgBase):
    """Torque-control cfg. Action element = direct effort (Nm or N).

    Default `scale=1.0` means the raw action is the effort itself; for
    Cartpole-style "policy outputs in [-1, 1], scaled to force_mag" patterns
    set `scale=cartpole_cfg.force_mag` (typically 10.0).
    """


class JointEffortAction(ActionTerm):
    """Write processed action directly into env's effort buffer.

    Env contract: env exposes either `_applied_force` (single-DoF prismatic,
    Cartpole) or `_applied_torques` (multi-DoF revolute, DoublePendulum).
    The action term writes into whichever attribute exists, in joint_names
    order. If a joint index N is in `joint_names`, the term writes
    `processed_actions[i]` into `env._applied_torques[N]` (or
    `_applied_force` when N=0 and that attribute exists).
    """

    def apply_actions(self, env: Any) -> None:
        # Multi-DoF revolute path (DoublePendulum-like).
        if hasattr(env, "_applied_torques"):
            torques = list(env._applied_torques)
            # Extend if too short.
            while len(torques) < max(self.cfg.joint_names) + 1:
                torques.append(0.0)
            for slot, joint in enumerate(self.cfg.joint_names):
                if slot < len(self.processed_actions):
                    torques[joint] = self.processed_actions[slot]
            env._applied_torques = tuple(torques) if isinstance(env._applied_torques, tuple) else torques
            return
        # Single-DoF prismatic path (Cartpole-like).
        if hasattr(env, "_applied_force") and self.cfg.joint_names == [0]:
            env._applied_force = float(self.processed_actions[0])
            return
        # Fallback for envs that hold actions as `_actions[env_idx][joint]`
        # (DirectRLEnv subclasses). Write per-env-0 only here.
        if hasattr(env, "_actions") and env._actions:
            actions_per_env = env._actions[0]
            while len(actions_per_env) < max(self.cfg.joint_names) + 1:
                actions_per_env.append(0.0)
            for slot, joint in enumerate(self.cfg.joint_names):
                if slot < len(self.processed_actions):
                    actions_per_env[joint] = self.processed_actions[slot]
            return
        raise RuntimeError(
            f"JointEffortAction: env has no _applied_force / _applied_torques / "
            f"_actions buffer to write into"
        )


# ────────────────────────────────────────────────────────────────────────────
# JointPositionAction (PD position control)
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class JointPositionActionCfg(ActionTermCfgBase):
    """Position-target cfg with PD gains.

    Action element = target joint position. Effort = K_p * (target - q) -
    K_d * dq. `use_default_offset=True` (Isaac Lab default) treats raw=0 as
    "hold current default position" — useful for residual policies.
    """
    p_gain: float = 50.0
    d_gain: float = 5.0
    use_default_offset: bool = True


class JointPositionAction(ActionTerm):
    """PD controller — converts position target to torque via
    `tau = K_p (q_target - q) - K_d dq` and writes into env effort buffer."""

    cfg: JointPositionActionCfg

    def __init__(self, cfg: JointPositionActionCfg):
        super().__init__(cfg)
        # Per-joint default offset (current position at first apply or reset).
        self._default_q: List[float] = [0.0] * self._dim

    def reset(self) -> None:
        super().reset()
        self._default_q = [0.0] * self._dim

    def set_default_offset(self, env: Any) -> None:
        """Snapshot the current joint positions for the configured joints as
        the new default offset. Call at episode reset for residual policies."""
        if hasattr(env, "get_joint_positions"):
            q = env.get_joint_positions()
            for slot, joint in enumerate(self.cfg.joint_names):
                if 0 <= joint < len(q):
                    self._default_q[slot] = float(q[joint])

    def apply_actions(self, env: Any) -> None:
        cfg: JointPositionActionCfg = self.cfg  # type: ignore[assignment]
        # Read current joint state.
        if not (hasattr(env, "get_joint_positions") and hasattr(env, "get_joint_velocities")):
            raise RuntimeError(
                "JointPositionAction: env must expose get_joint_positions + get_joint_velocities"
            )
        q = env.get_joint_positions()
        dq = env.get_joint_velocities()
        # Compute torque per joint.
        torques_to_apply: List[tuple] = []  # (joint_idx, torque)
        for slot, joint in enumerate(self.cfg.joint_names):
            target = self.processed_actions[slot]
            if cfg.use_default_offset:
                target += self._default_q[slot]
            qj = q[joint] if joint < len(q) else 0.0
            dqj = dq[joint] if joint < len(dq) else 0.0
            tau = cfg.p_gain * (target - qj) - cfg.d_gain * dqj
            torques_to_apply.append((joint, tau))
        # Write into env effort buffer.
        if hasattr(env, "_applied_torques"):
            torques = list(env._applied_torques)
            max_idx = max((j for j, _ in torques_to_apply), default=0)
            while len(torques) < max_idx + 1:
                torques.append(0.0)
            for j, t in torques_to_apply:
                torques[j] = t
            env._applied_torques = tuple(torques) if isinstance(env._applied_torques, tuple) else torques
        elif hasattr(env, "_applied_force") and self.cfg.joint_names == [0]:
            env._applied_force = float(torques_to_apply[0][1])
        else:
            raise RuntimeError(
                "JointPositionAction: env has no _applied_force / _applied_torques buffer"
            )


# ────────────────────────────────────────────────────────────────────────────
# JointVelocityAction (P velocity control)
# ────────────────────────────────────────────────────────────────────────────


@dataclass
class JointVelocityActionCfg(ActionTermCfgBase):
    """Velocity-target cfg. Effort = K_p * (target_vel - dq)."""
    p_gain: float = 10.0


class JointVelocityAction(ActionTerm):
    """P controller — converts velocity target to torque via
    `tau = K_p (dq_target - dq)`."""

    cfg: JointVelocityActionCfg

    def apply_actions(self, env: Any) -> None:
        cfg: JointVelocityActionCfg = self.cfg  # type: ignore[assignment]
        if not hasattr(env, "get_joint_velocities"):
            raise RuntimeError(
                "JointVelocityAction: env must expose get_joint_velocities"
            )
        dq = env.get_joint_velocities()
        torques_to_apply: List[tuple] = []
        for slot, joint in enumerate(self.cfg.joint_names):
            target_vel = self.processed_actions[slot]
            dqj = dq[joint] if joint < len(dq) else 0.0
            tau = cfg.p_gain * (target_vel - dqj)
            torques_to_apply.append((joint, tau))
        if hasattr(env, "_applied_torques"):
            torques = list(env._applied_torques)
            max_idx = max((j for j, _ in torques_to_apply), default=0)
            while len(torques) < max_idx + 1:
                torques.append(0.0)
            for j, t in torques_to_apply:
                torques[j] = t
            env._applied_torques = tuple(torques) if isinstance(env._applied_torques, tuple) else torques
        elif hasattr(env, "_applied_force") and self.cfg.joint_names == [0]:
            env._applied_force = float(torques_to_apply[0][1])
        else:
            raise RuntimeError(
                "JointVelocityAction: env has no _applied_force / _applied_torques buffer"
            )


# ────────────────────────────────────────────────────────────────────────────
# ActionManager — composes multiple terms
# ────────────────────────────────────────────────────────────────────────────


class ActionManager:
    """Composes multiple ActionTerm into a single combined action vector.

    `total_action_dim` = sum of each term's `action_dim`.
    `process_actions(raw)` slices `raw` by per-term offsets and dispatches
    each slice. `apply_actions(env)` then triggers every term's
    `apply_actions(env)` in registration order.

    Reset propagates to all terms (zeros internal buffers).
    """

    def __init__(self, terms: List[ActionTerm]):
        if not terms:
            raise ValueError("ActionManager requires at least one ActionTerm")
        self.terms: List[ActionTerm] = list(terms)
        self._term_names: List[str] = [type(t).__name__ for t in terms]
        # Cache per-term action slice offsets.
        self._offsets: List[int] = []
        off = 0
        for t in self.terms:
            self._offsets.append(off)
            off += t.action_dim
        self.total_action_dim: int = off

    def process_actions(self, raw: List[float]) -> None:
        """Slice `raw` and dispatch to each term in order."""
        if len(raw) != self.total_action_dim:
            raise ValueError(
                f"ActionManager: expected {self.total_action_dim} action elements, "
                f"got {len(raw)}"
            )
        for i, term in enumerate(self.terms):
            start = self._offsets[i]
            end = start + term.action_dim
            term.process_actions(raw[start:end])

    def apply_actions(self, env: Any) -> None:
        """Apply every term to env in registration order."""
        for term in self.terms:
            term.apply_actions(env)

    def reset(self, env_ids: Optional[List[int]] = None) -> None:
        """Reset all terms. `env_ids` is accepted for API parity but the
        nv_compat terms are env-agnostic (state is in the env)."""
        for term in self.terms:
            term.reset()

    @property
    def term_names(self) -> List[str]:
        return list(self._term_names)

    def num_terms(self) -> int:
        return len(self.terms)
