"""isaacsim.core.api compat — World + Articulation + RigidPrim.

Public API mirror per Isaac Sim 4.x Python docs.
Backed by pymagatama.nv_compat._kernel Cartpole closed-form dynamics (R1.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..._kernel import (
    ArticulatedSystem,
    CartpoleConfig,
    CartpoleState,
    DoublePendulumConfig,
    DoublePendulumState,
    cartpole_cfg_from_urdf,
    cartpole_step,
    detect_cartpole_topology,
    detect_double_pendulum_topology,
    double_pendulum_cfg_from_urdf,
    double_pendulum_step,
    parse_urdf,
)


class World:
    """Mirror of isaacsim.core.api.World.

    Holds a flat list of articulations stepped in lockstep at fixed dt.
    """

    def __init__(self, physics_dt: float = 1.0 / 60.0, stage_units_in_meters: float = 1.0,
                 gravity: float = 9.81):
        self.physics_dt = physics_dt
        self.stage_units_in_meters = stage_units_in_meters
        self.gravity = gravity
        self._articulations: list[Articulation] = []

    def add_articulation(self, art: "Articulation") -> "Articulation":
        # Isaac Sim's API is `scene.add(...)`; both forms supported here.
        art._bind_to_world(self)
        self._articulations.append(art)
        return art

    @property
    def scene(self):
        return _SceneShim(self)

    def step(self, render: bool = False) -> None:
        for art in self._articulations:
            art._step()

    def reset(self) -> None:
        for art in self._articulations:
            art._reset_state()

    def articulations(self) -> list["Articulation"]:
        return list(self._articulations)


class _SceneShim:
    def __init__(self, world: World):
        self._world = world

    def add(self, prim: "Articulation") -> "Articulation":
        return self._world.add_articulation(prim)


class Articulation:
    """Mirror of isaacsim.core.prims.Articulation.

    Supported topologies (R1.1):
      - Cartpole (1 prismatic + 1 revolute, 2 DoF)
      - Double pendulum (2 revolute serial chain, 2 DoF)
    Featherstone for general n-link arrives at R1.5.
    """

    def __init__(self, prim_path: str, name: str, urdf_text: Optional[str] = None,
                 system: Optional[ArticulatedSystem] = None):
        if urdf_text is None and system is None:
            raise ValueError("provide one of urdf_text or system")
        if system is None:
            system = parse_urdf(urdf_text)  # type: ignore[arg-type]
        if detect_cartpole_topology(system):
            self._kind = "cartpole"
        elif detect_double_pendulum_topology(system):
            self._kind = "double_pendulum"
        else:
            raise NotImplementedError(
                f"R1.1 Articulation supports Cartpole + double pendulum; got `{system.name}`. "
                f"Featherstone for n-link arrives at R1.5."
            )
        self.prim_path = prim_path
        self.name = name
        self.system = system
        self._cp_state: CartpoleState = CartpoleState()
        self._dp_state: DoublePendulumState = DoublePendulumState()
        self._cp_cfg: Optional[CartpoleConfig] = None
        self._dp_cfg: Optional[DoublePendulumConfig] = None
        self._applied_force = 0.0
        self._applied_torques = (0.0, 0.0)
        self._world: Optional[World] = None

    def _bind_to_world(self, world: World) -> None:
        self._world = world
        if self._kind == "cartpole":
            self._cp_cfg = cartpole_cfg_from_urdf(
                self.system, gravity=world.gravity, dt=world.physics_dt
            )
        else:
            self._dp_cfg = double_pendulum_cfg_from_urdf(
                self.system, gravity=world.gravity, dt=world.physics_dt
            )

    def _step(self) -> None:
        if self._kind == "cartpole":
            if self._cp_cfg is None:
                raise RuntimeError("articulation not bound to world")
            cartpole_step(self._cp_state, self._applied_force, self._cp_cfg)
            self._applied_force = 0.0
        else:
            if self._dp_cfg is None:
                raise RuntimeError("articulation not bound to world")
            double_pendulum_step(self._dp_state, self._applied_torques, self._dp_cfg)
            self._applied_torques = (0.0, 0.0)

    def _reset_state(self) -> None:
        if self._kind == "cartpole":
            self._cp_state = CartpoleState()
            self._applied_force = 0.0
        else:
            self._dp_state = DoublePendulumState()
            self._applied_torques = (0.0, 0.0)

    # ---- Public Isaac Sim-style accessors ----

    def get_joint_positions(self) -> list[float]:
        if self._kind == "cartpole":
            return [self._cp_state.x, self._cp_state.theta]
        return [self._dp_state.q1, self._dp_state.q2]

    def get_joint_velocities(self) -> list[float]:
        if self._kind == "cartpole":
            return [self._cp_state.x_dot, self._cp_state.theta_dot]
        return [self._dp_state.q1_dot, self._dp_state.q2_dot]

    def set_joint_positions(self, positions: list[float]) -> None:
        if len(positions) != 2:
            raise ValueError("expects 2 joint positions")
        if self._kind == "cartpole":
            self._cp_state.x, self._cp_state.theta = positions[0], positions[1]
        else:
            self._dp_state.q1, self._dp_state.q2 = positions[0], positions[1]

    def set_joint_velocities(self, velocities: list[float]) -> None:
        if len(velocities) != 2:
            raise ValueError("expects 2 joint velocities")
        if self._kind == "cartpole":
            self._cp_state.x_dot, self._cp_state.theta_dot = velocities[0], velocities[1]
        else:
            self._dp_state.q1_dot, self._dp_state.q2_dot = velocities[0], velocities[1]

    def apply_action(self, action: dict) -> None:
        """isaacsim.core.api.ArticulationAction surface."""
        eff = action.get("joint_efforts") or action.get("efforts") or []
        if self._kind == "cartpole":
            if len(eff) >= 1:
                self._applied_force = float(eff[0])
        else:
            if len(eff) >= 2:
                self._applied_torques = (float(eff[0]), float(eff[1]))
            elif len(eff) == 1:
                self._applied_torques = (float(eff[0]), 0.0)


@dataclass
class RigidPrim:
    """Stub of isaacsim.core.prims.RigidPrim — R1.1 does not yet drive standalone rigid bodies.
    The struct is provided so existing scripts that *reference* RigidPrim type names import
    cleanly; instances raise on use until R1.5.
    """
    prim_path: str
    name: str
    mass: float = 0.0

    def get_world_pose(self):
        raise NotImplementedError(
            "RigidPrim.get_world_pose arrives at R1.5 with multi-body kami-genesis."
        )
