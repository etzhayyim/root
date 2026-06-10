"""fibre_loop — noroshi (烽) fibre-optic infrastructure operational loop (R0 :representative).

The runnable, tested core behind the `fibre_loop` cell: the three field operations of laying
fibre-optic cable, end to end — **lay → align → splice** — composed under noroshi's constitutional
gates. 烽 (the beacon-fire watchtower) is the original optical telecom; this is its modern body: a
cable plow / ROV laying duct along a planned route, the fibre actively aligned to a coupler, and two
fibre ends fusion-spliced into a continuous link.

Each phase is a real, deterministic sub-model, reusing the shared infra-robotics substrate and
noroshi's EXISTING safety-critical aligner — nothing is reimplemented:

  LAY    — a `CableLayPlant` (a `Plant`): cross-track-error dynamics of a cable-lay plow/ROV tracking
           a planned route against a small constant seabed/soil drift. A PI tracking controller from
           the substrate (`PID` + `simulate`) drives the cross-track error to ~0.
  ALIGN  — the EXISTING noroshi `align(CouplerModel, LaserSpec)` Hooke-Jeeves search + IEC 60825 laser
           interlock from active_alignment.py (imported, NOT duplicated) → coupling loss (dB).
  SPLICE — a `splice_loss_db(lateral_offset_um, cleave_angle_deg)` fusion-splice loss model (loss grows
           with lateral offset² and cleave angle) + a fusion-splice acceptance threshold.

The whole loop runs offline with no hardware, no network and no live laser. noroshi gates apply:
N1/G3 civilian-only (laying fibre, never a force use), G5 IEC 60825 laser-safety (inherited from the
reused aligner), G7 no-server-key (the segment commit is member/operator-signed, the platform holds
no key — server_held_key=False), G8 outward-gated (dry_run=True; live actuation is Council Lv6+).
A live cable-laying fleet displaces fibre-laying crews ⇒ G2-coupled to the Displacement Dividend.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from _substrate import (
    PID,
    assert_civilian,
    require_member_signature,
    simulate,
    witness_quorum_ok,
)

# REUSE the existing aligner + laser-safety gate — same methods/ dir, flat import. NOT reimplemented.
from active_alignment import CouplerModel, LaserSpec, align

# noroshi fibre civilian-use allowlist (closed-world, N1). Laying / repairing fibre is never a force use.
PERMITTED_USES = ("lay", "align", "splice", "inspect", "repair", "bury")

# Fusion-splice acceptance threshold (dB). A good arc-fusion splice is typically ≤0.05–0.1 dB insertion
# loss (ITU-T G.652/G.657 field practice); we take 0.10 dB as the acceptance ceiling.
SPLICE_LOSS_MAX_DB = 0.10

# Splice-loss model coefficients (:representative — arithmetic, no measured splicer).
# Lateral core offset dominates (loss ∝ offset²); a non-zero cleave angle adds an angular-mismatch term.
_SPLICE_K_OFFSET = 0.0016      # dB per (µm offset)²
_SPLICE_K_ANGLE = 0.012        # dB per (degree of cleave-angle mismatch)²


@dataclass(frozen=True)
class LayResult:
    """Outcome of the cross-track tracking run for the cable-lay plow/ROV."""

    use: str
    initial_xte_m: float
    final_xte_m: float
    track_converged: bool
    settling_seconds: float
    max_abs_xte_m: float


@dataclass(frozen=True)
class SpliceResult:
    """Outcome of a single fusion splice against the acceptance threshold."""

    lateral_offset_um: float
    cleave_angle_deg: float
    loss_db: float
    threshold_db: float
    passed: bool


@dataclass(frozen=True)
class FibreSegmentResult:
    """The composed lay → align → splice record for one fibre segment (dry-run, R0)."""

    use: str
    # lay
    track_converged: bool
    final_xte_m: float
    lay_settling_seconds: float
    # align (from the reused noroshi aligner)
    coupling_loss_db: float
    align_converged: bool
    # splice
    splice_loss_db: float
    splice_passed: bool
    # composition + governance
    witness_ok: bool
    overall_ok: bool
    server_held_key: bool        # G7: always False
    dry_run: bool                # G8: R0 offline only
    representative: bool          # G10: arithmetic, no measured device


# ── LAY: cross-track-error tracking plant ────────────────────────────────────────────────────────
@dataclass
class CableLayPlant:
    """Cross-track-error dynamics of a cable-lay plow / ROV tracking a planned route.

    The controlled quantity is the **cross-track error** `e` (m) — the lateral distance of the plow
    from the planned cable route. A lateral steering / thruster `command` corrects it; a small constant
    `drift` (seabed current / soil pull) pushes the plow off-line:

        de/dt = k·command + drift

    The PI tracking controller is driven with error = setpoint − e (setpoint 0), so its output goes
    negative when the plow is on the +e side: a negative steering command reduces e, while the PI
    integral cancels the constant drift to leave ~zero steady-state cross-track error. This is the
    :representative twin of the field-tier path-tracking loop; a real plow runs the hard-RT cell
    under a certified controller.
    """

    k: float = 1.0          # steering authority (m/s per unit command)
    drift: float = 0.05     # constant cross-track drift disturbance (m/s)
    e: float = 0.0          # current cross-track error (m)

    def measure(self) -> float:
        return self.e

    def step(self, command: float, dt: float) -> None:
        dedt = self.k * command + self.drift
        self.e += dedt * dt


def lay_segment(
    route_xte0: float,
    use: str = "lay",
    k: float = 1.0,
    drift: float = 0.05,
    kp: float = 3.0,
    ki: float = 1.5,
    cmd_limit: float = 5.0,
    steps: int = 4000,
    dt: float = 0.01,
    tol: float = 1e-3,
) -> LayResult:
    """Track the planned route from an initial cross-track error to ~0. Raises (assert_civilian) first.

    `route_xte0` is the plow's initial lateral offset (m) from the planned route; the PI tracking loop
    drives it to the setpoint (0) while rejecting the constant drift. Returns convergence + settling.
    """
    assert_civilian(use, PERMITTED_USES)  # N1 gate before any actuation modelling

    plant = CableLayPlant(k=k, drift=drift, e=route_xte0)
    pid = PID(kp=kp, ki=ki, out_min=-cmd_limit, out_max=cmd_limit)
    res = simulate(plant, pid, setpoint=0.0, steps=steps, dt=dt, tol=tol)
    settling_seconds = res.settling_step * dt if res.settling_step >= 0 else -1.0
    return LayResult(
        use=use,
        initial_xte_m=round(route_xte0, 6),
        final_xte_m=round(res.final_value, 6),
        track_converged=res.converged,
        settling_seconds=round(settling_seconds, 3),
        max_abs_xte_m=res.max_abs_error,
    )


# ── SPLICE: fusion-splice loss model ──────────────────────────────────────────────────────────────
def splice_loss_db(lateral_offset_um: float, cleave_angle_deg: float) -> float:
    """Fusion-splice insertion loss (dB) — grows with lateral core offset² and cleave-angle mismatch².

    A :representative monotone model: a perfect splice (zero offset, zero angle) is lossless; loss rises
    quadratically with both lateral core offset and the residual cleave-angle mismatch. Both inputs are
    magnitudes (a negative offset/angle is the same as its absolute value).
    """
    off = abs(lateral_offset_um)
    ang = abs(cleave_angle_deg)
    return round(_SPLICE_K_OFFSET * off * off + _SPLICE_K_ANGLE * ang * ang, 6)


def splice(
    lateral_offset_um: float,
    cleave_angle_deg: float,
    threshold_db: float = SPLICE_LOSS_MAX_DB,
) -> SpliceResult:
    """Evaluate a single fusion splice against the acceptance threshold (default fusion ≤0.10 dB)."""
    loss = splice_loss_db(lateral_offset_um, cleave_angle_deg)
    return SpliceResult(
        lateral_offset_um=round(abs(lateral_offset_um), 6),
        cleave_angle_deg=round(abs(cleave_angle_deg), 6),
        loss_db=loss,
        threshold_db=threshold_db,
        passed=loss <= threshold_db,
    )


# ── COMPOSE: lay → align → splice for one segment ──────────────────────────────────────────────────
def lay_align_splice(
    route_xte0: float,
    member_sig: str,
    witness_sigs: list[str],
    use: str = "lay",
    server_sig: str = "",
    coupler: CouplerModel | None = None,
    laser: LaserSpec | None = None,
    splice_offset_um: float = 0.4,
    splice_cleave_angle_deg: float = 0.3,
    splice_threshold_db: float = SPLICE_LOSS_MAX_DB,
    lay_kwargs: dict | None = None,
) -> FibreSegmentResult:
    """Run the full fibre-segment loop end to end under noroshi's gates (dry-run, R0).

    Gate order (refuse before any modelling):
      1. assert_civilian(use)            — N1/G3 closed-world civilian-use gate.
      2. require_member_signature(...)   — G7 no-server-key: member-signed, no platform signature.
    Then lay (cross-track tracking) → align (the REUSED noroshi Hooke-Jeeves aligner + IEC 60825 laser
    gate) → splice (fusion-splice acceptance). Witness quorum (G8) is recorded on the result; the whole
    record is dry_run=True / server_held_key=False at R0 (live actuation is Council Lv6+, G8).
    """
    assert_civilian(use, PERMITTED_USES)              # N1/G3 gate
    require_member_signature(member_sig, server_sig)  # G7 no-server-key gate

    coupler = coupler or CouplerModel()
    # align() runs enable_laser() internally → IEC 60825 + N1 laser gate (G5). A weapon use raises here.
    laser = laser or LaserSpec(use="alignment")

    lay = lay_segment(route_xte0, use=use, **(lay_kwargs or {}))
    alignment = align(coupler, laser)
    sp = splice(splice_offset_um, splice_cleave_angle_deg, threshold_db=splice_threshold_db)
    wq = witness_quorum_ok(witness_sigs)

    overall_ok = (
        lay.track_converged
        and alignment.converged
        and sp.passed
        and wq["ok"]
    )
    return FibreSegmentResult(
        use=use,
        track_converged=lay.track_converged,
        final_xte_m=lay.final_xte_m,
        lay_settling_seconds=lay.settling_seconds,
        coupling_loss_db=alignment.loss_db,
        align_converged=alignment.converged,
        splice_loss_db=sp.loss_db,
        splice_passed=sp.passed,
        witness_ok=wq["ok"],
        overall_ok=overall_ok,
        server_held_key=False,   # G7
        dry_run=True,            # G8
        representative=True,     # G10
    )


def to_datoms(result: FibreSegmentResult, segment_id: str) -> dict:
    """Project a fibre-segment result into kotoba EAVT-shaped datoms (G9).

    Aggregate-only, no person data (G4). The transactor appends these to the canonical Datom log; here
    we return the entity map a transactor would write.
    """
    return {
        ":fibre.segment/id": segment_id,
        ":fibre.segment/use": result.use,
        ":fibre.segment/track-converged": result.track_converged,
        ":fibre.segment/final-xte-m": result.final_xte_m,
        ":fibre.segment/lay-settling-seconds": result.lay_settling_seconds,
        ":fibre.segment/coupling-loss-db": result.coupling_loss_db,
        ":fibre.segment/align-converged": result.align_converged,
        ":fibre.segment/splice-loss-db": result.splice_loss_db,
        ":fibre.segment/splice-passed": result.splice_passed,
        ":fibre.segment/witness-ok": result.witness_ok,
        ":fibre.segment/overall-ok": result.overall_ok,
        ":fibre.segment/server-held-key": result.server_held_key,  # G7
        ":fibre.segment/dry-run": result.dry_run,                  # G8
        ":fibre.segment/representative": result.representative,    # G10
    }


def report() -> str:
    """Render the fibre-loop face out/ artifact (honest R0 framing for the governance test)."""
    lay = lay_segment(route_xte0=2.0)
    sp = splice(0.4, 0.3)
    seg = lay_align_splice(
        route_xte0=2.0, member_sig="m:ed25519:demo",
        witness_sigs=["did:web:robot-a", "did:web:robot-b"],
    )
    lines = [
        "# noroshi 烽 — fibre-optic infrastructure loop (lay → align → splice)",
        "",
        "## lay (cross-track route tracking)",
        f"- initial cross-track error : {lay.initial_xte_m} m",
        f"- final cross-track error   : {lay.final_xte_m} m  "
        f"({'converged' if lay.track_converged else 'not-converged'} "
        f"in {lay.settling_seconds}s)",
        "",
        "## align (reused Hooke-Jeeves aligner + IEC 60825 laser gate)",
        f"- coupling insertion loss   : {seg.coupling_loss_db} dB  "
        f"({'converged' if seg.align_converged else 'not-converged'})",
        "",
        "## splice (fusion-splice acceptance)",
        f"- splice loss               : {sp.loss_db} dB  "
        f"(threshold {SPLICE_LOSS_MAX_DB} dB → {'PASS' if sp.passed else 'FAIL'})",
        "",
        f"## segment overall : {'OK' if seg.overall_ok else 'NOT-OK'}  "
        f"(serverHeldKey={seg.server_held_key}, dryRun={seg.dry_run})",
        "",
        "> R0 simulation only — no robot, no live laser, no live cable plow, no live actuation (G7/G8). "
        "A live cable-laying fleet displaces fibre crews ⇒ G2-coupled to the Displacement Dividend "
        "(ADR-2606032130). :representative — arithmetic + the reused aligner, no measured device (G10).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
