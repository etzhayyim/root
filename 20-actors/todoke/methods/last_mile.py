"""last_mile — pure-Python mirror of the todoke-route Rust core + courier liberation sizing.

Per ADR-2606042300. Stdlib only. Two purposes:

  1. ``plan_last_mile`` / safety-envelope helpers — a faithful Python mirror of the Rust
     ``todoke-route`` crate (one model, two runtimes — the sumitsubo pattern, ADR-2606033600).
     The cell state-machine calls this; the deployed run calls the Rust crate. The parity test
     in ``test_last_mile.py`` pins the two implementations to the same visiting order.

  2. ``courier_freed_hours`` / ``displacement_cohort_size`` — sizing for the labour-liberation
     mission (ISIC H53 / ISCO 9621 parcel-courier toil) and the G2 Displacement-Dividend
     coupling (ADR-2606032130). Order-of-magnitude and ``:representative`` (G10).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SAE_LEVEL_CEILING = 4  # N2: Level 5 is a non-goal

# Per-zone speed caps in m/s — MUST match Zone::speed_cap_mps in route/src/lib.rs.
ZONE_SPEED_CAP_MPS: dict[str, float | None] = {
    "sidewalk": 1.8,
    "crosswalk": 1.4,
    "doorpath": 1.0,
    "bikelane": 4.2,
    "road": None,  # not in the todoke ODD (N2)
}


class EnvelopeViolation(Exception):
    """A constitutional refusal (G7): the plan would break the safety envelope / ODD."""


@dataclass(frozen=True)
class Stop:
    id: int
    x: float
    y: float
    zone: str  # one of ZONE_SPEED_CAP_MPS keys

    def dist(self, other: "Stop") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


def _check_envelope(stops: list[Stop], sae_level: int, commanded_mps: float) -> None:
    """G7 gate — raise BEFORE any route is produced, mirroring the Rust `Err` returns."""
    if sae_level > SAE_LEVEL_CEILING:
        raise EnvelopeViolation(f"G7: SAE level {sae_level} exceeds ceiling {SAE_LEVEL_CEILING} (N2)")
    for s in stops:
        cap = ZONE_SPEED_CAP_MPS.get(s.zone)
        if cap is None:
            raise EnvelopeViolation(f"G7: stop {s.id} zone {s.zone!r} outside todoke ODD (N2)")
        if commanded_mps > cap:
            raise EnvelopeViolation(
                f"G7: commanded {commanded_mps} m/s exceeds {s.zone} cap {cap} m/s at stop {s.id}"
            )


def _nearest_neighbour(stops: list[Stop]) -> list[int]:
    n = len(stops)
    visited = [False] * n
    visited[0] = True
    tour = [0]
    cur = 0
    for _ in range(1, n):
        best, best_d = None, math.inf
        for j, s in enumerate(stops):
            if visited[j]:
                continue
            d = stops[cur].dist(s)
            if d < best_d - 1e-12 or (d <= best_d + 1e-12 and (best is None or j < best)):
                best_d, best = d, j
        assert best is not None
        visited[best] = True
        tour.append(best)
        cur = best
    return tour


def _two_opt(seed: list[int], stops: list[Stop]) -> list[int]:
    tour = list(seed)
    n = len(tour)
    if n < 4:
        return tour
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):  # depot (index 0) pinned
            for k in range(i + 1, n):
                a, b, c = stops[tour[i - 1]], stops[tour[i]], stops[tour[k]]
                d_next = stops[tour[k + 1]] if k + 1 < n else None
                before = a.dist(b) + (c.dist(d_next) if d_next else 0.0)
                after = a.dist(c) + (b.dist(d_next) if d_next else 0.0)
                if after + 1e-9 < before:
                    tour[i:k + 1] = reversed(tour[i:k + 1])
                    improved = True
    return tour


def plan_last_mile(stops: list[Stop], sae_level: int = 4, commanded_mps: float = 1.5):
    """Return (order_of_ids, length_m) for a safety-validated last-mile path.

    `stops[0]` is the depot/drop curb; the path is open (no return). Raises
    EnvelopeViolation if the run would break the envelope (G7) — mirroring the Rust crate.
    """
    if not stops:
        raise EnvelopeViolation("G7: no stops to route")
    _check_envelope(stops, sae_level, commanded_mps)
    seq = _two_opt(_nearest_neighbour(stops), stops)
    length = sum(stops[seq[i]].dist(stops[seq[i + 1]]) for i in range(len(seq) - 1))
    return [stops[i].id for i in seq], length


# --- Labour-liberation sizing (mission + G2 coupling) ---------------------------------

def courier_freed_hours(headcount: float, hours_per_worker_yr: float, automation_fraction: float) -> float:
    """Human courier labour-hours/year removed by automating `automation_fraction` of stops."""
    return headcount * hours_per_worker_yr * automation_fraction


def displacement_cohort_size(headcount: float, automation_fraction: float) -> int:
    """Approx number of courier roles displaced (owed the tenure-weighted dividend, ADR-2606032130)."""
    return int(round(headcount * automation_fraction))


if __name__ == "__main__":
    # `:representative` order-of-magnitude (G10): global parcel-courier pool ISCO 9621.
    HEAD = 1.9e7  # ~19M parcel/postal couriers worldwide (order-of-magnitude)
    fh = courier_freed_hours(HEAD, 2200, 0.30)
    print(f"todoke illustrative: automating 30% of last-mile stops frees "
          f"{fh / 1e9:.1f}B courier-hours/yr; cohort ≈ {displacement_cohort_size(HEAD, 0.30) / 1e6:.1f}M roles.")
