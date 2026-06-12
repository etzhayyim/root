"""panel_install — hikari solar_pv_install robot motion loop (R0 :representative).

The runnable, tested core behind the `solar_pv_install` cell. It plans an Otete
arm motion that places a PV panel at a target pose and refuses to dispatch unless
every structural gate holds:

  N1   civilian-use only (assert_civilian)            install / service / inspect
  G15/G7 no-server-key (require_member_signature)      member signs, platform never
  G8   witness quorum >=2 independent robot DIDs        kuni-umi constitutional
  safety envelope                                       per-step joint-rate ceiling,
                                                         slower whenever a person may
                                                         be in the work cell
  G2 (kuni-umi)  motion stays a planned trajectory; this module never actuates —
                 cell.py .solve() is Council-gated (R0 dry-run only).

Reachability + IK come from the substrate PlanarArm (kami-genesis stand-in).
"""

from __future__ import annotations

from dataclasses import dataclass

from _substrate import (
    PlanarArm,
    SafetyEnvelope,
    assert_civilian,
    joint_trajectory,
    require_member_signature,
    witness_quorum_ok,
)

PERMITTED_USES = ("install", "service", "inspect", "clean")

# Otete arm :representative geometry — a 2-link planar reach model (metres).
OTETE_ARM = PlanarArm(link_lengths=(1.2, 1.0))


@dataclass(frozen=True)
class PanelInstallPlan:
    """A dry-run panel-install motion plan (R0). Never an actuation command."""

    use: str
    target_xy: tuple[float, float]
    reachable: bool
    joints_goal: tuple[float, float] | None
    trajectory_steps: int
    envelope_ok: bool
    envelope_violations: list[str]
    human_present: bool
    member_sig: str
    witness_ok: bool
    server_held_key: bool
    dry_run: bool


def plan_panel_install(
    target_xy: tuple[float, float],
    member_sig: str,
    witness_sigs: list[str],
    q_start: tuple[float, float] = (0.0, 0.0),
    use: str = "install",
    human_present: bool = False,
    steps: int = 60,
    dt: float = 0.1,
    server_sig: str = "",
) -> PanelInstallPlan:
    """Plan an install motion. Raises before planning if a structural gate fails.

    Gate order is fail-fast: civilian use, then no-server-key, then witness quorum.
    Only after the gates pass do we solve IK and check the trajectory envelope.
    A witness-quorum miss does not raise (it is a Council-escalation Datom), so the
    plan is returned with witness_ok=False for the audit trail.
    """
    assert_civilian(use, PERMITTED_USES)               # N1
    require_member_signature(member_sig, server_sig)   # G15/G7
    quorum = witness_quorum_ok(witness_sigs)           # G8 (record, do not raise)

    x, y = target_xy
    reachable = OTETE_ARM.reachable(x, y)
    joints_goal = OTETE_ARM.ik2(x, y, elbow_up=True) if reachable else None

    env = SafetyEnvelope(max_joint_speed=1.0, human_proximity_speed=0.25, max_reach=OTETE_ARM.max_reach)
    traj: list[tuple[float, ...]] = []
    envelope_ok = False
    violations: list[str] = []
    if joints_goal is not None:
        traj = joint_trajectory(q_start, joints_goal, steps=steps)
        check = env.check_trajectory(traj, dt=dt, human_present=human_present)
        envelope_ok = check["ok"]
        violations = check["violations"]

    return PanelInstallPlan(
        use=use,
        target_xy=target_xy,
        reachable=reachable,
        joints_goal=joints_goal,
        trajectory_steps=len(traj),
        envelope_ok=envelope_ok,
        envelope_violations=violations,
        human_present=human_present,
        member_sig=member_sig,
        witness_ok=quorum["ok"],
        server_held_key=False,  # G15: structural invariant
        dry_run=True,           # G10: R0 offline only
    )


def to_datoms(plan: PanelInstallPlan, job_id: str, robot_id: str = "otete-01") -> dict:
    """Project an install plan into kotoba EAVT-shaped datoms (G6)."""
    return {
        ":install/id": job_id,
        ":install/robot": robot_id,
        ":install/use": plan.use,
        ":install/target-x": plan.target_xy[0],
        ":install/target-y": plan.target_xy[1],
        ":install/reachable": plan.reachable,
        ":install/trajectory-steps": plan.trajectory_steps,
        ":install/envelope-ok": plan.envelope_ok,
        ":install/human-present": plan.human_present,
        ":install/member-sig": plan.member_sig,
        ":install/witness-ok": plan.witness_ok,
        ":install/server-held-key": plan.server_held_key,  # G15: always false
        ":install/dry-run": plan.dry_run,                   # G10
    }
