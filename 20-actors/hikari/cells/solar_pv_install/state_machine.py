"""solar_pv_install state machine — Otete panel-install motion (gated transitions).

Pure, deterministic transitions enforcing hikari gates. The runnable motion
planner lives in ../../methods/panel_install.py; this wires it into a phase
machine ending at a member-signed, dry-run install record (G7/G8/G10). cell.py
.solve() stays Council-gated.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "methods"))

from panel_install import plan_panel_install, to_datoms  # noqa: E402


class InstallPhase(Enum):
    INIT = "init"
    MOTION_PLANNED = "motion_planned"
    JOB_COMMITTED = "job_committed"


@dataclass
class InstallState:
    phase: str = InstallPhase.INIT.value
    job_id: str = "install-01"
    robot_id: str = "otete-01"
    use: str = "install"
    target_x: float = 1.5
    target_y: float = 0.4
    human_present: bool = False
    member_sig: str = ""
    server_sig: str = ""
    witness_sigs: list[str] = field(default_factory=list)
    reachable: bool = False
    envelope_ok: bool = False
    payload: dict = field(default_factory=dict)


def _state(state: dict[str, Any]) -> InstallState:
    cs = state.get("cell_state")
    if isinstance(cs, dict):
        s = InstallState()
        s.__dict__.update(cs)
        return s
    return InstallState()


def transition_plan_motion(state: dict[str, Any]) -> dict[str, Any]:
    """Plan the install motion (raises on non-civilian use / server key / no member sig)."""
    cs = _state(state)
    cs.use = state.get("use", cs.use)
    cs.target_x = float(state.get("target_x", cs.target_x))
    cs.target_y = float(state.get("target_y", cs.target_y))
    cs.human_present = bool(state.get("human_present", cs.human_present))
    cs.member_sig = state.get("member_sig", cs.member_sig)
    cs.server_sig = state.get("server_sig", cs.server_sig)
    cs.witness_sigs = state.get("witness_sigs", cs.witness_sigs)

    plan = plan_panel_install(
        (cs.target_x, cs.target_y),
        member_sig=cs.member_sig,
        witness_sigs=cs.witness_sigs,
        use=cs.use,
        human_present=cs.human_present,
        server_sig=cs.server_sig,
    )
    cs.reachable = plan.reachable
    cs.envelope_ok = plan.envelope_ok
    cs.payload["plan"] = to_datoms(plan, cs.job_id, cs.robot_id)
    cs.payload["_witness_ok"] = plan.witness_ok
    cs.phase = InstallPhase.MOTION_PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "commit_job"}


def transition_commit_job(state: dict[str, Any]) -> dict[str, Any]:
    """Commit a dry-run install job only if reachable + envelope-safe + quorum met."""
    cs = _state(state)
    if not cs.reachable:
        raise ValueError("target unreachable: cannot commit install job")
    if not cs.envelope_ok:
        raise ValueError("trajectory violates safety envelope: cannot commit install job")
    if not cs.payload.get("_witness_ok"):
        raise ValueError("witness quorum < 2 (G8): cannot commit install job")
    cs.payload["job"] = {**cs.payload["plan"], "committed": True, "dryRun": True}
    cs.phase = InstallPhase.JOB_COMMITTED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
