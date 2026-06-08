"""isaac_sway_sim — STS crane anti-sway transfer driven through the clean-room
``isaacsim.core.api`` surface (kotodama.nv_compat).

The ship-to-shore crane is, dynamically, a *cart + hanging load* — exactly the
topology Isaac Sim ships as **Cartpole** (prismatic trolley + revolute load).
The Cartpole's stable equilibrium ``theta = π`` is the load hanging straight
down; ``theta`` deviating from ``π`` is container sway. This module:

  * builds a ``World`` + Cartpole ``Articulation`` through the public Isaac API,
  * places the load hanging,
  * drives the trolley toward a target slot with an **anti-sway state feedback**
    (``apply_action({"joint_efforts": ...})``), and
  * reads back ``get_joint_positions`` to score residual sway.

It deliberately reuses the *exact* call/return shapes of Isaac Sim 4.x so a
script written against real Isaac runs unchanged — but no NVIDIA code is linked
(clean-room, ADR-2605261800). When the ``kotodama`` package cannot be imported
(e.g. its optional langchain deps are absent), ``isaac_available()`` returns
False and callers/tests skip gracefully.

Per ADR-2606082000 (niyaku R0).
"""

from __future__ import annotations

import math
import os
import sys
import types
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_KOTODAMA_REL = os.path.join(
    "40-engine", "kotoba", "crates", "kotoba-kotodama", "py", "src"
)


def _resolve_py_src() -> str:
    """Locate the kotodama package source.

    Order: ``NIYAKU_KOTODAMA_SRC`` env override → walk parent dirs for a
    *populated* ``40-engine/kotoba/.../py/src`` (the kotoba submodule may be
    unchecked-out in a fresh worktree). Returns the first hit, else the
    monorepo-relative default (which may not exist — load_isaac then fails and
    callers skip).
    """
    env = os.environ.get("NIYAKU_KOTODAMA_SRC")
    if env and os.path.isdir(os.path.join(env, "kotodama", "nv_compat")):
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        cand = os.path.join(here, _KOTODAMA_REL)
        if os.path.isdir(os.path.join(cand, "kotodama", "nv_compat")):
            return os.path.abspath(cand)
        here = os.path.dirname(here)
    # default (monorepo root is 3 levels up from methods/)
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", _KOTODAMA_REL)
    )


_PY_SRC = _resolve_py_src()

HANG = math.pi  # cartpole theta of a load hanging straight down (stable)


def _ensure_kotodama_stub() -> None:
    """Register a lightweight ``kotodama`` package object so submodule imports
    resolve WITHOUT executing the heavy ``kotodama/__init__.py`` (which eagerly
    pulls langchain/pydantic). The nv_compat.isaacsim subtree is stdlib-only.
    """
    if _PY_SRC not in sys.path:
        sys.path.insert(0, _PY_SRC)
    if "kotodama" not in sys.modules:
        pkg = types.ModuleType("kotodama")
        pkg.__path__ = [os.path.join(_PY_SRC, "kotodama")]  # type: ignore[attr-defined]
        sys.modules["kotodama"] = pkg


def isaac_available() -> bool:
    """True iff the clean-room ``isaacsim.core.api`` surface can be imported."""
    try:
        load_isaac()
        return True
    except Exception:
        return False


def load_isaac() -> Dict[str, Any]:
    """Import and return the Isaac API symbols this module drives."""
    _ensure_kotodama_stub()
    from kotodama.nv_compat.isaacsim.core.api import World, Articulation  # noqa: E402
    from kotodama.nv_compat.isaacsim.assets import Cartpole  # noqa: E402
    return {"World": World, "Articulation": Articulation, "Cartpole": Cartpole}


# ── anti-sway feedback in Cartpole coordinates ──────────────────────────────


@dataclass
class StsAntiSway:
    """Trolley-force feedback law on Cartpole state [x, x_dot, theta, theta_dot].

    phi = theta - π is the sway from the hanging equilibrium. The law positions
    the trolley (kp/kd) while damping sway (k_phi/k_phid). In the Cartpole
    convention a +force pushes the cart +x AND drives phi positive (the load
    lags behind), so positive phi / phi_dot must SUBTRACT from the force to bleed
    sway energy — all four feedback terms are negative.
    """

    kp: float = 6.0
    kd: float = 10.0
    k_phi: float = 25.0
    k_phid: float = 12.0
    max_force: float = 100.0

    def force(self, state: List[float], x_target: float) -> float:
        x, x_dot, theta, theta_dot = state
        phi = theta - HANG
        u = (
            -self.kp * (x - x_target)
            - self.kd * x_dot
            - self.k_phi * phi
            - self.k_phid * theta_dot
        )
        return max(-self.max_force, min(self.max_force, u))


@dataclass
class TransferReport:
    reached: bool
    final_x: float
    residual_sway_rad: float   # |theta - π| at the end
    peak_sway_rad: float
    steps: int
    anti_sway: bool


def run_sts_transfer(
    x_target: float,
    anti_sway: bool = True,
    push_force: float = 12.0,
    steps: int = 1200,
    physics_dt: float = 1.0 / 120.0,
    pos_tol: float = 0.05,
    controller: Optional[StsAntiSway] = None,
) -> TransferReport:
    """Drive the trolley to ``x_target`` through the Isaac API.

    ``anti_sway=True`` uses ``StsAntiSway`` state feedback; ``False`` uses a
    naive proportional push (no sway damping) for comparison. Returns residual
    sway so a test can assert the controller demonstrably quietens the load.

    Raises ImportError (via ``load_isaac``) if the Isaac surface is unavailable.
    """
    api = load_isaac()
    World, Articulation, Cartpole = api["World"], api["Articulation"], api["Cartpole"]
    cart = Cartpole(prim_path="/World/STS_Crane")
    world = World(physics_dt=physics_dt)
    art = Articulation(prim_path=cart.prim_path, name=cart.name, urdf_text=cart.urdf_text)
    world.add_articulation(art)
    world.reset()
    art.set_joint_positions([0.0, HANG])  # trolley at origin, load hanging

    ctrl = controller or StsAntiSway()
    peak = 0.0
    reached = False
    i = 0
    for i in range(steps):
        state = art.get_joint_positions() + art.get_joint_velocities()
        # state = [x, theta, x_dot, theta_dot] -> reorder to [x, x_dot, theta, theta_dot]
        s = [state[0], state[2], state[1], state[3]]
        if anti_sway:
            f = ctrl.force(s, x_target)
        else:
            f = max(-ctrl.max_force, min(ctrl.max_force, -push_force * (s[0] - x_target)))
        art.apply_action({"joint_efforts": [f, 0.0]})
        world.step()
        sway = abs(art.get_joint_positions()[1] - HANG)
        peak = max(peak, sway)
        if abs(art.get_joint_positions()[0] - x_target) <= pos_tol and sway <= 0.02:
            reached = True
            break
    final = art.get_joint_positions()
    return TransferReport(
        reached=reached,
        final_x=final[0],
        residual_sway_rad=abs(final[1] - HANG),
        peak_sway_rad=peak,
        steps=i + 1,
        anti_sway=anti_sway,
    )


def report_to_datoms(report: TransferReport, sim_id: str) -> List[Tuple[str, str, Any]]:
    """Serialise a transfer report to kotoba EAVT datom tuples (e a v).

    Entity id ``niyaku/sim/<sim_id>``; attributes under ``:niyaku.sim/*``.
    (G6 kotoba-EAVT-native; emitted, never written to an external store here.)
    """
    e = f"niyaku/sim/{sim_id}"
    return [
        (e, ":niyaku.sim/anti-sway", report.anti_sway),
        (e, ":niyaku.sim/reached", report.reached),
        (e, ":niyaku.sim/final-x", round(report.final_x, 4)),
        (e, ":niyaku.sim/residual-sway-rad", round(report.residual_sway_rad, 5)),
        (e, ":niyaku.sim/peak-sway-rad", round(report.peak_sway_rad, 5)),
        (e, ":niyaku.sim/steps", report.steps),
    ]
