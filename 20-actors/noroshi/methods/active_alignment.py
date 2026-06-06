"""noroshi (烽) active-alignment + laser-safety core — the packaging-robotics face (ADR-2606051600).

The safety-critical noroshi skill: a photonic packaging robot aligns an optical fibre to an on-chip
grating coupler by *active alignment* — it sweeps the fibre tip while measuring coupled power and
climbs to the peak — and it may only energise the alignment laser through a hard **laser-safety
interlock** (IEC 60825 class gate) and a **civilian-use** gate. Like tazuna's teleop_safety, this is
kept pure + deterministic so it can be unit-tested before any robot or laser exists.

Two responsibilities, in priority order:

  1. enable_laser()  — REFUSE to energise unless (a) the intended use is civilian (N1: weaponisation /
                       directed-energy / dazzle is structurally unrepresentable) and (b) for any class
                       above Class 1, a physical enclosure interlock + safety attestation are present.
                       Best-effort soft-safety, NOT an IEC 60825 certified safety controller (R5/Lv7+).
  2. align()         — Hooke-Jeeves pattern search over fibre (dx,dy) maximising coupling efficiency
                       (a Gaussian of misalignment), converging to the unknown peak within tolerance.

No hardware, no live laser, no live actuation (G7 outward-gated). The robot displaces human
fibre-alignment technicians, so a live fleet is G2-coupled to the Displacement Dividend (ADR-2606032130).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Civilian photonic-fab uses only. Weaponisation is unrepresentable (N1, like tazuna :weaponizable).
PERMITTED_USES = ("alignment", "comms", "soldering", "trimming", "inspection")
FORBIDDEN_USES = ("weapon", "directed-energy", "dazzle", "fire-control")
# IEC 60825 laser classes; anything above Class 1 is potentially hazardous → interlock required.
HAZARDOUS_CLASSES = ("2", "3R", "3B", "4")


class LaserSafetyError(ValueError):
    """N1 / IEC 60825 — the laser may not be energised for this use or without an interlock."""


@dataclass(frozen=True)
class LaserSpec:
    laser_class: str = "1"          # IEC 60825 class
    use: str = "alignment"          # must be in PERMITTED_USES
    enclosure_interlock: bool = False   # physical beam enclosure / door interlock present
    safety_attestation_ref: str = ""    # operator safety attestation (e.g. attest:noroshi-lsm-001)


def enable_laser(spec: LaserSpec) -> None:
    """Raise unless the laser may be energised. No return value (gate only).

    Civilian-use gate first (N1), then the IEC 60825 interlock gate for any hazardous class.
    """
    if spec.use in FORBIDDEN_USES or spec.use not in PERMITTED_USES:
        raise LaserSafetyError(
            f"N1: use {spec.use!r} is not a permitted civilian photonic-fab use; "
            "weaponisation / directed-energy can never be energised (Mission Charter §1.12)"
        )
    if spec.laser_class in HAZARDOUS_CLASSES:
        if not spec.enclosure_interlock:
            raise LaserSafetyError(
                f"IEC 60825: a Class-{spec.laser_class} laser requires a physical enclosure "
                "interlock before energising (soft-safety gate; not a certified safety controller)"
            )
        if not spec.safety_attestation_ref:
            raise LaserSafetyError(
                f"IEC 60825: a Class-{spec.laser_class} laser requires an operator safety "
                "attestation reference before energising"
            )


# ── coupling model + active-alignment search ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class CouplerModel:
    """Gaussian coupling vs lateral misalignment from the (unknown) optimal fibre offset."""

    peak_efficiency: float = 0.80   # η0 at perfect alignment (grating-coupler ~ -1 dB)
    mode_radius_um: float = 5.0     # 1/e alignment tolerance (µm)
    opt_x_um: float = 2.3           # unknown true peak offset the robot must FIND
    opt_y_um: float = -1.7

    def efficiency(self, dx_um: float, dy_um: float) -> float:
        r2 = (dx_um - self.opt_x_um) ** 2 + (dy_um - self.opt_y_um) ** 2
        return self.peak_efficiency * math.exp(-r2 / (self.mode_radius_um ** 2))

    @staticmethod
    def loss_db(efficiency: float) -> float:
        return -10.0 * math.log10(max(efficiency, 1e-12))


@dataclass(frozen=True)
class AlignmentResult:
    x_um: float
    y_um: float
    efficiency: float
    loss_db: float
    probes: int
    converged: bool


def align(
    model: CouplerModel,
    laser: LaserSpec,
    start_x_um: float = 0.0,
    start_y_um: float = 0.0,
    step_um: float = 4.0,
    tol_um: float = 0.05,
    max_probes: int = 2000,
) -> AlignmentResult:
    """Hooke-Jeeves pattern search for peak coupling. Raises (via enable_laser) before any probe.

    Probes the four axis-aligned neighbours at the current step; moves to the best improving one,
    else halves the step. Terminates when the step shrinks below tol_um (converged) or the probe
    budget is exhausted. Deterministic — same model + start ⇒ same trajectory.
    """
    enable_laser(laser)                                   # safety gate BEFORE energising / probing

    x, y = start_x_um, start_y_um
    best = model.efficiency(x, y)
    step = step_um
    probes = 1
    while step > tol_um and probes < max_probes:
        improved = False
        for dx, dy in ((step, 0.0), (-step, 0.0), (0.0, step), (0.0, -step)):
            probes += 1
            eff = model.efficiency(x + dx, y + dy)
            if eff > best:
                best, x, y = eff, x + dx, y + dy
                improved = True
                break
        if not improved:
            step /= 2.0
    return AlignmentResult(
        x_um=round(x, 4), y_um=round(y, 4),
        efficiency=round(best, 6), loss_db=round(CouplerModel.loss_db(best), 4),
        probes=probes, converged=step <= tol_um,
    )


def coarse_scan(
    model: CouplerModel, laser: LaserSpec, span_um: float = 70.0, step_um: float | None = None
) -> tuple[float, float, float, int]:
    """Coarse acquisition: raster the fibre over ±span at ~mode-radius spacing → best (x,y,eff,probes).

    Real fibre alignment cannot start with a gradient method when the fibre is tens of µm outside the
    micron-wide coupling lobe (efficiency underflows to 0, so there is no gradient to climb). A coarse
    raster at ~mode-radius spacing is guaranteed to land at least one sample inside the lobe. Raises
    (via enable_laser) before any probe.
    """
    enable_laser(laser)
    step = model.mode_radius_um if step_um is None else step_um
    if step <= 0 or span_um <= 0:
        raise ValueError("span_um and step_um must be positive")
    n = int(span_um / step)
    best_x, best_y, best_eff, probes = 0.0, 0.0, model.efficiency(0.0, 0.0), 1
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * step, j * step
            probes += 1
            eff = model.efficiency(x, y)
            if eff > best_eff:
                best_x, best_y, best_eff = x, y, eff
    return best_x, best_y, best_eff, probes


def spiral_search(
    model: CouplerModel, laser: LaserSpec, span_um: float = 70.0,
    step_um: float | None = None, detect_floor: float = 1e-6,
) -> tuple[float, float, float, int]:
    """Acquisition by an expanding-square spiral that STOPS on first signal → best (x,y,eff,probes).

    What a real fibre aligner does: spiral outward from the nominal position and halt the moment the
    photodiode sees coupling above `detect_floor`, instead of rastering the whole field. For the common
    case (a small initial misalignment) this finds the lobe in a handful of probes rather than the full
    (2n+1)² raster. Bounded by ±span. Raises (via enable_laser) before any probe.
    """
    enable_laser(laser)
    step = model.mode_radius_um if step_um is None else step_um
    if step <= 0 or span_um <= 0:
        raise ValueError("span_um and step_um must be positive")
    max_ring = int(span_um / step)
    ix = iy = 0
    best = (0.0, 0.0, model.efficiency(0.0, 0.0))
    probes = 1
    if best[2] > detect_floor:
        return (*best, probes)
    # Expanding-square spiral: run lengths 1,1,2,2,3,3,… cycling R, U, L, D.
    dirs = ((1, 0), (0, 1), (-1, 0), (0, -1))
    di, run = 0, 1
    while run <= 2 * max_ring + 1:
        for _ in range(2):
            dx, dy = dirs[di % 4]
            for _ in range(run):
                ix, iy = ix + dx, iy + dy
                if max(abs(ix), abs(iy)) > max_ring:
                    return (*best, probes)
                x, y = ix * step, iy * step
                probes += 1
                eff = model.efficiency(x, y)
                if eff > best[2]:
                    best = (x, y, eff)
                if eff > detect_floor:
                    return (best[0], best[1], best[2], probes)
            di += 1
        run += 1
    return (*best, probes)


def align_two_stage(
    model: CouplerModel, laser: LaserSpec, span_um: float = 70.0,
    coarse_step_um: float | None = None, fine_tol_um: float = 0.05, acquire: str = "raster",
) -> AlignmentResult:
    """Coarse acquisition → Hooke-Jeeves fine refinement. Robust to a far / narrow-lobe start.

    `acquire` selects the coarse stage: "raster" (exhaustive, guaranteed lobe capture) or "spiral"
    (expanding-square, stops on first signal — far fewer probes for a small initial misalignment).
    Total probe count sums both stages. Same laser-safety gate as `align` (energised once, civilian).
    """
    step = model.mode_radius_um if coarse_step_um is None else coarse_step_um
    if acquire == "spiral":
        cx, cy, _, cprobes = spiral_search(model, laser, span_um, step)
    elif acquire == "raster":
        cx, cy, _, cprobes = coarse_scan(model, laser, span_um, step)
    else:
        raise ValueError("acquire must be 'raster' or 'spiral'")
    fine = align(model, laser, start_x_um=cx, start_y_um=cy, step_um=step, tol_um=fine_tol_um)
    return AlignmentResult(
        x_um=fine.x_um, y_um=fine.y_um, efficiency=fine.efficiency, loss_db=fine.loss_db,
        probes=cprobes + fine.probes, converged=fine.converged,
    )


def report(model: CouplerModel | None = None) -> str:
    """Render the packaging-robotics face out/ artifact."""
    model = model or CouplerModel()
    safe = LaserSpec(laser_class="1", use="alignment")
    res = align(model, safe)
    lines = [
        "# noroshi 烽 — photonic active alignment (fibre ↔ grating coupler)",
        "",
        f"- true peak offset : ({model.opt_x_um}, {model.opt_y_um}) µm  (unknown to the robot)",
        f"- found offset     : ({res.x_um}, {res.y_um}) µm  in {res.probes} probes "
        f"({'converged' if res.converged else 'budget-exhausted'})",
        f"- coupling         : η = {res.efficiency}  → insertion loss {res.loss_db} dB",
        "",
        "## laser-safety interlock (IEC 60825 + N1 civilian-use)",
        "- Class 1 alignment laser              → energise OK",
        "- Class 4 without enclosure interlock  → REFUSED",
        "- use = 'directed-energy' / 'weapon'   → REFUSED (structurally unrepresentable, N1)",
        "",
        "> R0 simulation only — no robot, no live laser, no live actuation (G7). A live fleet displaces "
        "human alignment technicians ⇒ G2-coupled to the Displacement Dividend (ADR-2606032130).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
