"""decommission_robot — kamado 竈 hot-zone decommission robot loop (R0 :representative).

The flagship behaviour behind the `decommission_robot` cell: a robot REMOVES THE
HUMAN from the H₂S / benzene / pyrophoric hot zone of a fossil refinery being wound
down (G9 — labor liberation; the freed worker routes to the Basic-High-Income
cohort). The crux is a hard safety gate: the robot may ONLY enter and cut once the
atmosphere has been purged / inerted BELOW the entry limit. Entry into an un-purged
zone is structurally unrepresentable — it raises SafetyError, never a warning.

Two runnable, tested halves:

  * `purge_to_entry` — a closed-loop purge/inert controller (substrate PID via
    `simulate`) drives the hazardous-gas concentration of a `GasConcentrationPlant`
    down to a target entry limit and reports whether entry is permitted.
  * `plan_cut_entry` — the entry + cut motion plan, gated fail-fast on:
      G3  intervention is decommission/remediate/convert/monitor/purge/inert only
          (closed-world civilian allowlist; "restart-fossil"/"expand" cannot pass)
      ENTRY GATE  final_ppm > gas_limit ⇒ SafetyError (the safety crux)
      G5/G7  no-server-key: member/operator signs, platform never
      G8  witness quorum ≥2 independent robot DIDs
      safety envelope  per-step joint-rate ceiling (slower if a human may be present)

kamado gates apply: this module is offline sim only (cell.py .solve() stays
Council-gated, G8); no process actuation; server_held_key=False, dry_run=True on
every record (G5/G11). Inference (not used in this deterministic loop) stays Murakumo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from _substrate import (
    PID,
    PlanarArm,
    SafetyEnvelope,
    SafetyError,
    assert_civilian,
    joint_trajectory,
    require_member_signature,
    simulate,
)

# kamado decommission/transition civilian-use allowlist (closed-world, N1/G3).
# A "restart-fossil"/"expand"/"throughput-revamp" use is NOT a member, so the
# closed-world refusal in assert_civilian rejects it (mirrors G3 of the
# decommission_plan state machine — fossil life-extension is unrepresentable).
PERMITTED_USES = ("decommission", "remediate", "purge", "inert", "monitor", "convert")

# Representative atmospheric entry limits (ppm). OSHA-style references; the exact
# numbers are :representative — the structural gate is "below the limit", not the
# specific value. H₂S: OSHA ceiling-ish ~10 ppm; benzene: ~1 ppm PEL-ish.
H2S_ENTRY_PPM = 10.0
BENZENE_ENTRY_PPM = 1.0

# Otete-class purge/cut arm :representative geometry — a 2-link planar reach (m).
KAMADO_ARM = PlanarArm(link_lengths=(1.2, 1.0))


@dataclass
class GasConcentrationPlant:
    """Hazardous-gas concentration dynamics of a confined refinery zone (ppm).

    The controlled quantity is the hazardous-gas concentration C (ppm). A purge /
    inert flow `command` (positive = forced ventilation / N₂ inerting) sweeps the
    gas out; a small constant `leak` feeds it back in (residual desorption /
    seepage from process metal), so a finite purge flow is needed just to hold a
    low concentration:

        dC/dt = -k_purge · command + leak        (C floored at 0)

    The leak is what makes this a real control problem: too small a steady purge
    cannot hold the zone below the entry limit. :representative lumped-parameter
    twin (the certified gas-detection + LEL/ventilation interlock is field-tier
    firmware, never this module).
    """

    k_purge: float = 0.20      # ppm reduced per unit purge-flow per second
    leak: float = 0.30         # ppm/s residual ingress (desorption / seepage)
    c: float = 120.0           # current hazardous-gas concentration (ppm)

    def measure(self) -> float:
        return self.c

    def step(self, command: float, dt: float) -> None:
        flow = max(0.0, command)  # purge flow is physically non-negative
        dcdt = -self.k_purge * flow + self.leak
        self.c = max(0.0, self.c + dcdt * dt)


class PurgeController:
    """PI purge controller — drives concentration DOWN to a target entry limit.

    The substrate `simulate` calls `step(error, dt)` with error = setpoint − pv =
    target − C. When C is above target this error is negative; the purge flow must
    be POSITIVE to sweep the gas out, so the controller acts on the *negated*
    error (the demand to lower the concentration). Output is clamped to a
    non-negative purge-flow band (you cannot un-purge a zone), with anti-windup
    inherited from the substrate PID. Exposes `.reset()` + `.step()` so it plugs
    straight into `simulate`.
    """

    def __init__(self, kp: float = 1.2, ki: float = 0.6, max_flow: float = 200.0):
        # Act on -error (the lower-the-concentration demand); clamp to [0, max_flow].
        self.pid = PID(kp=kp, ki=ki, out_min=0.0, out_max=max_flow)

    def reset(self) -> None:
        self.pid.reset()

    def step(self, error: float, dt: float) -> float:
        # error = target - C; demand to reduce = C - target = -error.
        return self.pid.step(-error, dt)


@dataclass(frozen=True)
class PurgeResult:
    """Outcome of a purge/inert run toward an entry limit (R0 :representative)."""

    use: str
    gas: str
    target_ppm: float
    initial_ppm: float
    final_ppm: float
    entry_permitted: bool      # concentration held at/below the entry limit
    purge_seconds: float
    settling_seconds: float
    representative: bool        # G11: sims-only at R0


def purge_to_entry(
    gas: str,
    target_ppm: float,
    use: str = "purge",
    initial_ppm: float = 120.0,
    k_purge: float = 0.20,
    leak: float = 0.30,
    kp: float = 1.2,
    ki: float = 0.6,
    max_flow: float = 200.0,
    steps: int = 6000,
    dt: float = 0.1,
) -> PurgeResult:
    """Run the purge/inert loop until hazardous-gas concentration ≤ target.

    Raises (assert_civilian) BEFORE any run if `use` is non-civilian / a fossil
    life-extension verb. `entry_permitted` is true iff the loop converges with the
    final concentration at/below the target entry limit — this is the value the
    entry gate in `plan_cut_entry` consumes.
    """
    assert_civilian(use, PERMITTED_USES)  # N1/G3 gate before any actuation modelling

    zone = GasConcentrationPlant(k_purge=k_purge, leak=leak, c=initial_ppm)
    controller = PurgeController(kp=kp, ki=ki, max_flow=max_flow)
    # tol is a concentration band around the target entry limit (ppm).
    res = simulate(zone, controller, setpoint=target_ppm, steps=steps, dt=dt, tol=0.25)

    final_ppm = round(zone.measure(), 4)
    settling_seconds = res.settling_step * dt if res.settling_step >= 0 else -1.0
    # Entry is permitted only when the loop actually settled at/below the limit.
    entry_permitted = res.converged and final_ppm <= target_ppm + 1e-6
    return PurgeResult(
        use=use,
        gas=gas,
        target_ppm=target_ppm,
        initial_ppm=initial_ppm,
        final_ppm=final_ppm,
        entry_permitted=entry_permitted,
        purge_seconds=round(steps * dt, 3),
        settling_seconds=round(settling_seconds, 3),
        representative=True,
    )


def plan_cut_entry(
    target_xy: tuple[float, float],
    final_ppm: float,
    gas_limit: float,
    member_sig: str,
    witness_sigs: list[str],
    use: str = "decommission",
    q_start: tuple[float, float] = (0.0, 0.0),
    human_present: bool = False,
    steps: int = 60,
    dt: float = 0.1,
    server_sig: str = "",
    displacement_cohort_ref: str = "bhi:cohort:hot-zone-decommission",
) -> dict:
    """Plan the robot's entry + cut into a hot zone. THE ENTRY GATE IS THE CRUX.

    Gate order is fail-fast:
      1. G3 / N1   civilian-use allowlist (assert_civilian) — restart-fossil/expand cannot pass.
      2. ENTRY GATE  `final_ppm > gas_limit` ⇒ SafetyError. The robot MUST NOT enter
                     an un-purged zone; this is structural, not advisory.
      3. G5/G7     no-server-key (require_member_signature).
      4. G8        witness quorum ≥2 (recorded, escalates Council Lv6+ on a miss; does not raise).
      5. envelope  IK reach + per-step joint-rate ceiling (slower if a human may be present).

    Returns a dry-run plan dict (serverHeldKey False, dryRun True). The freed
    hot-zone worker routes to the Basic-High-Income cohort `displacement_cohort_ref` (G9).
    """
    assert_civilian(use, PERMITTED_USES)  # G3/N1 — closed-world refusal of fossil life-extension

    # ── THE SAFETY CRUX (entry gate): never enter an un-purged hot zone. ──
    if final_ppm > gas_limit:
        raise SafetyError(
            f"ENTRY REFUSED: zone hazardous-gas concentration {final_ppm:.3f} ppm exceeds the "
            f"entry limit {gas_limit:.3f} ppm. The robot must NOT enter or cut until the "
            f"atmosphere is purged/inerted below the limit (structural gate, G11/G9 — "
            f"this removes the human from the hot zone, it never substitutes an unsafe entry)."
        )

    require_member_signature(member_sig, server_sig)  # G5/G7
    from _substrate import witness_quorum_ok  # local import keeps the gate order explicit
    quorum = witness_quorum_ok(witness_sigs)  # G8 (record, do not raise)

    x, y = target_xy
    reachable = KAMADO_ARM.reachable(x, y)
    joints_goal = KAMADO_ARM.ik2(x, y, elbow_up=True) if reachable else None

    env = SafetyEnvelope(
        max_joint_speed=1.0, human_proximity_speed=0.25, max_reach=KAMADO_ARM.max_reach
    )
    traj: list[tuple[float, ...]] = []
    envelope_ok = False
    violations: list[str] = []
    if joints_goal is not None:
        traj = joint_trajectory(q_start, joints_goal, steps=steps)
        check = env.check_trajectory(traj, dt=dt, human_present=human_present)
        envelope_ok = check["ok"]
        violations = check["violations"]

    return {
        "use": use,
        "targetXy": list(target_xy),
        "finalPpm": round(final_ppm, 4),
        "gasLimitPpm": round(gas_limit, 4),
        "entryPermitted": True,  # passed the entry gate above
        "reachable": reachable,
        "jointsGoal": list(joints_goal) if joints_goal is not None else None,
        "trajectorySteps": len(traj),
        "envelopeOk": envelope_ok,
        "envelopeViolations": violations,
        "humanPresent": human_present,
        "memberSig": member_sig,
        "witnessOk": quorum["ok"],
        "escalateCouncilLv6": quorum.get("escalate_council_lv6", False),
        "displacementCohortRef": displacement_cohort_ref,  # G9: freed worker → BHI cohort
        "serverHeldKey": False,  # G5 structural invariant
        "dryRun": True,          # G8/G11: R0 offline only
    }


def to_datoms(
    purge: PurgeResult,
    plan: dict,
    job_id: str,
    refinery: str,
    robot_id: str = "kamado-arm-01",
) -> dict:
    """Project a purge + entry-cut plan into kotoba EAVT-shaped datoms (G6).

    Aggregate-only (no person data; G4). Carries the displacement-cohort ref (G9),
    the no-server-key flag (G5) and the dry-run flag (G8/G11) the transactor needs.
    """
    return {
        ":decommission/id": job_id,
        ":decommission/refinery": refinery,
        ":decommission/robot": robot_id,
        ":decommission/use": plan["use"],
        ":decommission/gas": purge.gas,
        ":decommission/target-ppm": purge.target_ppm,
        ":decommission/initial-ppm": purge.initial_ppm,
        ":decommission/final-ppm": purge.final_ppm,
        ":decommission/entry-permitted": plan["entryPermitted"],
        ":decommission/purge-settling-seconds": purge.settling_seconds,
        ":decommission/reachable": plan["reachable"],
        ":decommission/trajectory-steps": plan["trajectorySteps"],
        ":decommission/envelope-ok": plan["envelopeOk"],
        ":decommission/human-present": plan["humanPresent"],
        ":decommission/member-sig": plan["memberSig"],
        ":decommission/witness-ok": plan["witnessOk"],
        ":decommission/displacement-cohort-ref": plan["displacementCohortRef"],  # G9
        ":decommission/server-held-key": plan["serverHeldKey"],  # G5: always false
        ":decommission/representative": purge.representative,    # G11
        ":decommission/dry-run": plan["dryRun"],                 # G8/G11
    }
