"""decommission_robot state machine — hot-zone purge → entry-gated cut (gated transitions).

Pure, deterministic transitions enforcing kamado gates. The runnable purge + entry
loop lives in ../../methods/decommission_robot.py; this wires it into a phase machine
that ends at a member-signed, dry-run cut record. cell.py .solve() stays Council-gated —
these transitions are exercised by tests, not live actuation.

Invariants enforced:
  ENTRY GATE — the robot may enter/cut ONLY after the purge loop holds the zone below
       the entry limit. `transition_plan_cut` raises SafetyError on an un-purged zone.
  G3 — intervention use ∈ decommission/remediate/purge/inert/monitor/convert (closed-world,
       via plan_cut_entry's assert_civilian); restart-fossil/expand cannot pass.
  G5 — no-server-key: the commit authorizes nothing; actuation = operator/member signature.
  G8 — outward-gated: real teardown is Council Lv6+ + operator; R0 = dry-run only.
  G9 — labor-liberation: the robot takes the H₂S/benzene hot-zone entry; the freed worker
       routes to the tenure-weighted Basic-High-Income cohort (ADR-2606032130).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = pathlib.Path(__file__).resolve().parents[2] / "methods"
# Append (not insert) so the sibling cell PACKAGES (feedstock_guard / decommission_plan,
# which share names with methods modules) keep priority on sys.path; we only need
# methods/ reachable for `_substrate` and the explicit file-load below.
if str(_METHODS) not in sys.path:
    sys.path.append(str(_METHODS))

# The methods module shares the name `decommission_robot` with THIS cell package,
# so a bare `import decommission_robot` would re-import the package, not the methods
# module. Load the methods file directly by path under a distinct module name.
_spec = importlib.util.spec_from_file_location(
    "kamado_decommission_robot_methods", _METHODS / "decommission_robot.py"
)
_methods = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _methods  # dataclass decorators need the module registered
_spec.loader.exec_module(_methods)

H2S_ENTRY_PPM = _methods.H2S_ENTRY_PPM
plan_cut_entry = _methods.plan_cut_entry
purge_to_entry = _methods.purge_to_entry
to_datoms = _methods.to_datoms


class RobotPhase(Enum):
    INIT = "init"
    PURGED = "purged"
    CUT_PLANNED = "cut_planned"
    ENTRY_COMMITTED = "entry_committed"


@dataclass
class RobotState:
    phase: str = RobotPhase.INIT.value
    job_id: str = "decom-01"
    refinery: str = "rf.jp.muroran"
    robot_id: str = "kamado-arm-01"
    gas: str = "H2S"
    use: str = "decommission"
    target_ppm: float = H2S_ENTRY_PPM
    gas_limit: float = H2S_ENTRY_PPM
    initial_ppm: float = 120.0
    target_x: float = 1.5
    target_y: float = 0.4
    human_present: bool = False
    member_sig: str = ""
    server_sig: str = ""
    witness_sigs: list[str] = field(default_factory=list)
    final_ppm: float = 0.0
    entry_permitted: bool = False
    reachable: bool = False
    envelope_ok: bool = False
    payload: dict = field(default_factory=dict)


def _state(state: dict[str, Any]) -> RobotState:
    cs = state.get("cell_state")
    if isinstance(cs, dict):
        s = RobotState()
        s.__dict__.update(cs)
        return s
    return RobotState()


def transition_purge(state: dict[str, Any]) -> dict[str, Any]:
    """Run the purge/inert loop (raises on non-civilian / fossil life-extension use, N1/G3)."""
    cs = _state(state)
    cs.use = state.get("use", cs.use)
    cs.gas = state.get("gas", cs.gas)
    cs.target_ppm = float(state.get("target_ppm", cs.target_ppm))
    cs.gas_limit = float(state.get("gas_limit", cs.gas_limit))
    cs.initial_ppm = float(state.get("initial_ppm", cs.initial_ppm))

    res = purge_to_entry(
        gas=cs.gas, target_ppm=cs.target_ppm, use=cs.use, initial_ppm=cs.initial_ppm
    )
    cs.final_ppm = res.final_ppm
    cs.entry_permitted = res.entry_permitted
    cs.payload["_purge"] = res  # carried to to_datoms at commit
    cs.payload["purge"] = {
        "gas": res.gas,
        "targetPpm": res.target_ppm,
        "finalPpm": res.final_ppm,
        "entryPermitted": res.entry_permitted,
        "settlingSeconds": res.settling_seconds,
    }
    cs.phase = RobotPhase.PURGED.value
    return {"cell_state": cs.__dict__, "next_node": "plan_cut"}


def transition_plan_cut(state: dict[str, Any]) -> dict[str, Any]:
    """ENTRY GATE: plan the entry + cut. Raises SafetyError if the zone is un-purged."""
    cs = _state(state)
    if cs.phase != RobotPhase.PURGED.value:
        raise ValueError("cut plan requires a completed purge first (entry gate)")
    cs.target_x = float(state.get("target_x", cs.target_x))
    cs.target_y = float(state.get("target_y", cs.target_y))
    cs.human_present = bool(state.get("human_present", cs.human_present))
    cs.member_sig = state.get("member_sig", cs.member_sig)
    cs.server_sig = state.get("server_sig", cs.server_sig)
    cs.witness_sigs = state.get("witness_sigs", cs.witness_sigs)

    # plan_cut_entry raises SafetyError if final_ppm > gas_limit (the safety crux),
    # on non-civilian use (G3), and on a server-held key / missing member sig (G5/G7).
    plan = plan_cut_entry(
        target_xy=(cs.target_x, cs.target_y),
        final_ppm=cs.final_ppm,
        gas_limit=cs.gas_limit,
        member_sig=cs.member_sig,
        witness_sigs=cs.witness_sigs,
        use=cs.use,
        human_present=cs.human_present,
        server_sig=cs.server_sig,
    )
    cs.reachable = plan["reachable"]
    cs.envelope_ok = plan["envelopeOk"]
    cs.payload["_plan"] = plan
    cs.payload["cut"] = plan
    cs.phase = RobotPhase.CUT_PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "commit_entry"}


def transition_commit_entry(state: dict[str, Any]) -> dict[str, Any]:
    """Commit a dry-run entry-cut record only if reachable + envelope-safe + quorum met."""
    cs = _state(state)
    if cs.phase != RobotPhase.CUT_PLANNED.value:
        raise ValueError("commit requires a planned cut first")
    plan = cs.payload["_plan"]
    if not cs.reachable:
        raise ValueError("target unreachable: cannot commit entry-cut")
    if not cs.envelope_ok:
        raise ValueError("trajectory violates safety envelope: cannot commit entry-cut")
    if not plan.get("witnessOk"):
        raise ValueError("witness quorum < 2 (G8): cannot commit entry-cut")

    record = to_datoms(cs.payload["_purge"], plan, cs.job_id, cs.refinery, cs.robot_id)
    record[":decommission/committed"] = True
    cs.payload["record"] = record
    cs.phase = RobotPhase.ENTRY_COMMITTED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
