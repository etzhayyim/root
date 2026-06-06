"""allocate.py — 扶持 (fuchi) maintainer sustenance allocation. ADR-2606052300.

THE HEART of the actor and the charter-clean inverse of an investment fund's cap-table.

A VC fund computes equity stakes and a return waterfall. 扶持 computes, for a cohort of
covenant-bound maintainers (信者) who keep etzhayyim's actors alive, each one's:

  - weight        w = ln(1 + min(tenure_years, 40)) * hazard   (the Displacement-Dividend
                                                                 curve, ADR-2606032130)
  - share         w_i / Σ w_j over the VOWED cohort            (sums to 1; PRIORITY, not cash)
  - priority_rank 1 = provisioned first under a scarce stage-capacity cap
  - floor         in-kind sustenance floor at elapsed=0, stage-capped, decaying over 5y

The single invariant that makes this charter-clean and NOT an investment vehicle:

  * cash_usd_micros is structurally 0 for every allocation (cash≡0, ADR-2605301020 N1);
  * the instrument is one of {in-kind-grant, sustenance, tooling-access, compute-access} —
    equity / debt / convertible / revenue-share / profit-claim / carry / dividend are a
    ValueError, never an allocation (G1, Charter-Rider §2(b));
  * the maintainer's work product is commons (owns_payoff is structurally False, G5).

There is no NAV, no IRR, no exit, no liquidation. A "share" governs only the SEQUENCING and
the in-kind floor — exactly what allocate.py in 50-infra/etzhayyim-public-fund/displacement
does for displaced workers, reused here for active maintainers.

Stdlib only. Deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TENURE_CAP_YEARS = 40.0
HAZARD_MIN = 1.0
HAZARD_MAX = 2.0
HORIZON_YEARS = 5.0

# G1 — sustenance instruments only (mirror of the ontology :alloc/instrument :db/allowed).
ALLOWED_INSTRUMENTS = ("in-kind-grant", "sustenance", "tooling-access", "compute-access")
# The investment-fund vocabulary that is UNREPRESENTABLE here (defensive denylist; the
# allowlist above is the real gate — this only sharpens the error message).
FORBIDDEN_INSTRUMENTS = (
    "equity", "debt", "convertible", "revenue-share", "profit-claim",
    "carry", "dividend", "loan", "interest", "warrant", "option", "exit",
)


def assert_instrument(instrument: str) -> str:
    """G1 INVARIANT — only a sustenance instrument is allocatable. Anything resembling an
    investment / debt / return claim is a ValueError (not an investment fund)."""
    instr = str(instrument or "").lstrip(":").lower()
    if instr in FORBIDDEN_INSTRUMENTS:
        raise ValueError(
            f"G1: instrument {instr!r} is an investment/return vehicle — UNREPRESENTABLE "
            "(扶持 is sustenance, not a fund; Charter-Rider §2(b))"
        )
    if instr not in ALLOWED_INSTRUMENTS:
        raise ValueError(f"G1: instrument {instr!r} not in {ALLOWED_INSTRUMENTS}")
    return instr


@dataclass(frozen=True)
class Maintainer:
    did: str
    tenure_months: int            # 勤続 months of mission service
    hazard_permille: int          # [1000, 2000] -> 1.0 .. 2.0 toil-hazard
    maintains: tuple[str, ...] = ()      # actor handles kept alive
    prior_imputed_usd_micros_yr: int = 0  # in-kind valuation only; NEVER cash
    covenant: str = "vowed"       # "outreach" (minimal floor) | "vowed" (full sustenance)
    owns_payoff: bool = False     # G5 — structurally False; work product is commons


@dataclass(frozen=True)
class Allocation:
    maintainer_did: str
    instrument: str               # G1 — one of ALLOWED_INSTRUMENTS
    weight: float
    share: float                  # fraction of cohort PRIORITY; Σ == 1 over vowed cohort
    priority_rank: int            # 1 = provisioned first under a scarce cap
    floor_usd_micros_yr: int      # in-kind floor at elapsed=0, stage-capped
    cash_usd_micros: int = 0      # INVARIANT: always 0 (cash≡0, N1)
    server_held_key: bool = False  # G9 — always False (no-server-key)

    def __post_init__(self) -> None:
        # The structural proofs, asserted at construction (defence in depth alongside schema).
        if self.cash_usd_micros != 0:
            raise ValueError("cash≡0 INVARIANT (G2/N4): 扶持 never disburses cash")
        if self.server_held_key:
            raise ValueError("no-server-key INVARIANT (G9): allocation is member/Council-signed")
        assert_instrument(self.instrument)


def _capped_tenure_years(tenure_months: int) -> float:
    return min(tenure_months / 12.0, TENURE_CAP_YEARS)


def _hazard(hazard_permille: int) -> float:
    h = hazard_permille / 1000.0
    if not (HAZARD_MIN <= h <= HAZARD_MAX):
        raise ValueError(f"hazard out of [1.0,2.0]: {h}")
    return h


def tenure_weight(m: Maintainer) -> float:
    """w = ln(1 + min(tenure_years, cap)) * hazard. Log compresses the gradient so a 40y
    maintainer is ~2x a 5y one (not 8x) — honours service without a per-person income
    leaderboard (ADR-2605261000 N6; same curve as Displacement Dividend)."""
    return math.log1p(_capped_tenure_years(m.tenure_months)) * _hazard(m.hazard_permille)


def floor_decay(elapsed_months: int) -> float:
    """decay(t) = clamp(1 - t/HORIZON, 0, 1). The sustenance floor tapers over 5 years as
    the maintainer ascends the Liberation Ladder toward full Basic High Income."""
    t = elapsed_months / 12.0
    return max(0.0, min(1.0, 1.0 - t / HORIZON_YEARS))


def allocate(
    cohort: list[Maintainer],
    stage_ceiling_usd_micros_yr: int,
    elapsed_months: int = 0,
    instrument: str = "sustenance",
) -> list[Allocation]:
    """Allocate tenure-weighted in-kind sustenance over a maintainer cohort.

    Only `vowed` maintainers join the tenure-weighted share pool (the covenant gate, G4).
    `outreach` maintainers receive a minimal floor (share 0) until they vow — they are not
    abandoned, but the full tenure-weighted sustenance is covenant-bound.

    Returns Allocations whose `cash_usd_micros` is structurally 0. Raises if any maintainer
    claims `owns_payoff` (G5) or if `instrument` is an investment vehicle (G1).
    """
    instr = assert_instrument(instrument)
    if any(m.owns_payoff for m in cohort):
        raise ValueError("G5: a maintainer cannot own the payoff — work product is commons")

    vowed = [m for m in cohort if m.covenant == "vowed"]
    total_w = sum(tenure_weight(m) for m in vowed)
    decay = floor_decay(elapsed_months)
    ranked = sorted(vowed, key=tenure_weight, reverse=True)
    rank_of = {m.did: i + 1 for i, m in enumerate(ranked)}

    out: list[Allocation] = []
    for m in cohort:
        if m.covenant == "vowed":
            w = tenure_weight(m)
            share = (w / total_w) if total_w > 0 else 0.0
            rank = rank_of[m.did]
            floor = min(m.prior_imputed_usd_micros_yr, stage_ceiling_usd_micros_yr)
            floor = int(round(floor * decay))
        else:  # outreach — minimal floor, no share (pre-vow)
            w = 0.0
            share = 0.0
            rank = len(vowed) + 1
            floor = int(round(min(m.prior_imputed_usd_micros_yr,
                                  stage_ceiling_usd_micros_yr) * decay * 0.25))
        out.append(Allocation(
            maintainer_did=m.did,
            instrument=instr,
            weight=round(w, 6),
            share=round(share, 6),
            priority_rank=rank,
            floor_usd_micros_yr=floor,
            cash_usd_micros=0,
            server_held_key=False,
        ))
    # vowed allocations first (priority order), then outreach
    out.sort(key=lambda a: (a.priority_rank, -a.weight))
    return out


def cohort_from_seed(records: list[dict]) -> list[Maintainer]:
    """Build a cohort from seed :maintainer/* maps (edn keyword-keyed)."""
    def kw(v):
        return str(v or "").lstrip(":").split("/")[-1].lower()
    out = []
    for r in records:
        out.append(Maintainer(
            did=r.get(":maintainer/did", "?"),
            tenure_months=int(r.get(":maintainer/tenure-months", 0)),
            hazard_permille=int(r.get(":maintainer/hazard-permille", 1000)),
            maintains=tuple(r.get(":maintainer/maintains", []) or []),
            prior_imputed_usd_micros_yr=int(r.get(":maintainer/prior-imputed-usd-micros-yr", 0)),
            covenant=kw(r.get(":maintainer/covenant", ":vowed")),
            owns_payoff=bool(r.get(":maintainer/owns-payoff", False)),
        ))
    return out
