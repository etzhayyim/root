"""commissioning — the runnable kuni-umi → open-ot handoff (3-layer integration).

This is the deterministic reference behind CommissioningCell.commission_test /
register_with_open_ot (cells/commissioning/cell.py), which raise NotImplementedError
because the live path needs deps.sdk + open-ot XRPC. Here we prove the handoff
end-to-end OFFLINE:

  Layer 1 (plant)    MicrogridPlant — the islanded grid being commissioned
  Layer 2 (control)  DroopPI — the open-ot DROOP_P_F + PI field-tier loop
  Layer 3 (coord)    this harness — runs the acceptance test (black-start ramp +
                     droop-P-f load-step response), enforces the >=2 witness
                     quorum (G8), and emits the open-ot loop registrations the
                     real CommissioningCell would XRPC to open-ot.

No SDK, no XRPC, no hardware: a dry-run record (G15 no-server-key, R0 offline).
The acceptance test reuses the same substrate plant + controller a domain actor
(hikari) uses, so "commissioned here" means "the loop the field tier will run".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from control import PID, Droop, DroopPI, simulate
from plant import MicrogridPlant
from safety import require_member_signature, witness_quorum_ok

# Anti-islanding ROCOF trip threshold (Hz/s) — see hikari/methods/microgrid.py.
ROCOF_TRIP_HZ_PER_S = 2.0


@dataclass(frozen=True)
class CommissionRecord:
    """A dry-run commissioning record handed from kuni-umi to open-ot (G6/G8/G15)."""

    site_did: str
    open_ot_loop_dids: tuple[str, ...]
    acceptance_passed: bool
    acceptance_tier: str        # "python-twin" (R0) | "device-wasm" (R1 evidence)
    final_freq_hz: float
    rocof_tripped: bool
    witness_ok: bool
    escalate_council_lv6: bool
    member_sig: str
    server_held_key: bool
    site_state: str            # "operational" | "punch-list"
    dry_run: bool


def _rocof(traj, window_s: float = 0.1) -> float:
    if len(traj) < 2:
        return 0.0
    dt = traj[1][0] - traj[0][0]
    span = max(1, round(window_s / dt)) if dt > 0 else 1
    worst = 0.0
    for i in range(span, len(traj)):
        d = traj[i][0] - traj[i - span][0]
        if d > 0:
            worst = max(worst, abs(traj[i][1] - traj[i - span][1]) / d)
    return worst


def run_microgrid_acceptance(load_step_kw: float = 140.0) -> dict:
    """S2 microgrid acceptance test: load step + droop-P-f response (open-ot DROOP_P_F).

    Returns {passed, final_freq_hz, rocof, rocof_tripped}. `passed` requires the
    frequency to recover to 50 Hz AND the ROCOF guard to NOT trip (a clean island).
    """
    grid = MicrogridPlant(p_load=100.0, f=50.0)
    grid.set_load(load_step_kw)
    controller = DroopPI(
        Droop(nominal=grid.f_nom, droop_r=0.04, p_base=100.0, p_min=0.0, p_max=200.0),
        PID(kp=4.0, ki=20.0, out_min=-200.0, out_max=200.0),
    )
    res = simulate(grid, controller, setpoint=grid.f_nom, steps=8000, dt=0.01, tol=1e-2)
    r = _rocof(res.trajectory)
    return {
        "passed": res.converged and r <= ROCOF_TRIP_HZ_PER_S,
        "final_freq_hz": round(res.final_value, 4),
        "rocof": round(r, 4),
        "rocof_tripped": r > ROCOF_TRIP_HZ_PER_S,
    }


def commission_microgrid_site(
    site_did: str,
    loop_dids: list[str],
    member_sig: str,
    witness_sigs: list[str],
    load_step_kw: float = 140.0,
    server_sig: str = "",
    device_evidence: dict | None = None,
) -> CommissionRecord:
    """Commission an islanded-microgrid site and hand its loops to open-ot.

    Fail-fast gates: member signature (G15/G7) before anything. The witness quorum
    (G8) is recorded (Council-escalation flag) rather than raised. The site only
    becomes "operational" if the acceptance test passes AND the quorum holds.

    `device_evidence` (R1): a result dict from the device-in-the-loop golden
    trace (device_loop.py — the REAL open-ot DROOP_P_F + ANTI_ISLANDING_ROCOF
    wasm executed under Wasmtime). When supplied and consistent (frequency
    restored, no trip, twin verdict match), the record's acceptance tier is
    "device-wasm" instead of "python-twin". Inconsistent evidence demotes the
    site to punch-list — device evidence can only tighten, never loosen.
    """
    require_member_signature(member_sig, server_sig)  # G15/G7
    quorum = witness_quorum_ok(witness_sigs)           # G8 (record, escalate)
    acceptance = run_microgrid_acceptance(load_step_kw)

    tier = "python-twin"
    device_ok = True
    if device_evidence is not None:
        device_ok = (
            bool(device_evidence.get("freq_restored"))
            and not device_evidence.get("rocof_trip", True)
            and bool(device_evidence.get("twin_verdict_match"))
            and bool(device_evidence.get("dry_run"))
            and device_evidence.get("server_held_key") is False
        )
        tier = "device-wasm" if device_ok else "python-twin"

    operational = acceptance["passed"] and quorum["ok"] and device_ok
    return CommissionRecord(
        site_did=site_did,
        open_ot_loop_dids=tuple(loop_dids),
        acceptance_passed=acceptance["passed"],
        acceptance_tier=tier,
        final_freq_hz=acceptance["final_freq_hz"],
        rocof_tripped=acceptance["rocof_tripped"],
        witness_ok=quorum["ok"],
        escalate_council_lv6=quorum.get("escalate_council_lv6", False),
        member_sig=member_sig,
        server_held_key=False,  # G15 structural invariant
        site_state="operational" if operational else "punch-list",
        dry_run=True,           # R0/R1 offline only
    )


def to_datoms(record: CommissionRecord) -> dict:
    """Project a commissioning record into kotoba EAVT-shaped datoms (G6)."""
    return {
        ":commission/site": record.site_did,
        ":commission/open-ot-loops": list(record.open_ot_loop_dids),
        ":commission/acceptance-passed": record.acceptance_passed,
        ":commission/acceptance-tier": record.acceptance_tier,
        ":commission/final-freq-hz": record.final_freq_hz,
        ":commission/rocof-tripped": record.rocof_tripped,
        ":commission/witness-ok": record.witness_ok,
        ":commission/escalate-council-lv6": record.escalate_council_lv6,
        ":commission/member-sig": record.member_sig,
        ":commission/server-held-key": record.server_held_key,  # G15: always false
        ":commission/site-state": record.site_state,
        ":commission/dry-run": record.dry_run,
    }
