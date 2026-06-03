"""Displacement Dividend — tenure-weighted in-kind allocation (reference implementation).

Per ADR-2606032130. Pure stdlib. This computes, for a displacement cohort, each
displaced worker's tenure-weighted SHARE and in-kind transition FLOOR. It NEVER
produces a cash amount: `cash_stipend_usd_micros` is structurally 0 for every
worker (the on-chain proof that N1 / cash≡0 holds, ADR-2605301020 §5).

What a "share" governs (never a cash split):
  1. onboarding-priority rank within a Liberation-Ladder stage capacity cap, and
  2. the in-kind imputed-income transition floor (food/shelter/energy/care/learning
     valued at market-equivalent), capped at the stage ceiling and decaying over a
     5-year HORIZON as the worker ascends the Ladder toward full Basic High Income.

Formula (ADR-2606032130):
    w_i   = ln(1 + min(tenure_years_i, TENURE_CAP)) * hazard_i
    share = w_i / sum(w_j)                                  # sum(share) == 1
    floor_i(t) = min(prior_imputed_i, stage_ceiling) * decay(t)
    decay(t)   = clamp(1 - t/HORIZON, 0, 1)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TENURE_CAP_YEARS = 40.0
HAZARD_MIN = 1.0
HAZARD_MAX = 2.0
HORIZON_YEARS = 5.0


@dataclass(frozen=True)
class DisplacedWorker:
    subject_did: str
    tenure_months: int           # 勤続年数 × 12
    hazard_permille: int         # [1000, 2000] -> 1.0 .. 2.0
    prior_imputed_usd_micros_yr: int = 0  # in-kind valuation only; NEVER paid as cash
    covenant: str = "vowed"      # "outreach" (minimal floor) | "vowed" (full dividend)


@dataclass(frozen=True)
class Allocation:
    subject_did: str
    weight: float
    share: float                 # fraction of cohort priority; sum == 1 over vowed cohort
    priority_rank: int           # 1 = provisioned first under a scarce stage cap
    floor_usd_micros_yr: int     # in-kind transition floor at elapsed_months=0, stage-capped
    cash_stipend_usd_micros: int = 0  # INVARIANT: always 0 (N1)


def _capped_tenure_years(tenure_months: int) -> float:
    return min(tenure_months / 12.0, TENURE_CAP_YEARS)


def _hazard(hazard_permille: int) -> float:
    h = hazard_permille / 1000.0
    if not (HAZARD_MIN <= h <= HAZARD_MAX):
        raise ValueError(f"hazard out of [1.0,2.0]: {h}")
    return h


def tenure_weight(worker: DisplacedWorker) -> float:
    """w_i = ln(1 + min(tenure_years, cap)) * hazard. Log compresses the gradient so a
    40y veteran is ~2x a 5y worker (not 8x) — honours seniority without a per-person
    income leaderboard (ADR-2605261000 N6)."""
    return math.log1p(_capped_tenure_years(worker.tenure_months)) * _hazard(worker.hazard_permille)


def floor_decay(elapsed_months: int) -> float:
    """decay(t) = clamp(1 - t/HORIZON, 0, 1)."""
    t = elapsed_months / 12.0
    return max(0.0, min(1.0, 1.0 - t / HORIZON_YEARS))


def allocate(
    cohort: list[DisplacedWorker],
    stage_ceiling_usd_micros_yr: int,
    elapsed_months: int = 0,
) -> list[Allocation]:
    """Allocate tenure-weighted in-kind shares + floors over a cohort.

    Only `vowed` workers participate in the tenure-weighted share pool (the covenant
    gate, N7). `outreach` workers receive a minimal floor (share 0) until they vow.
    """
    vowed = [w for w in cohort if w.covenant == "vowed"]
    total_w = sum(tenure_weight(w) for w in vowed)
    decay = floor_decay(elapsed_months)

    # rank vowed workers by weight (desc) for onboarding priority under a scarce cap
    ranked = sorted(vowed, key=tenure_weight, reverse=True)
    rank_of = {w.subject_did: i + 1 for i, w in enumerate(ranked)}

    out: list[Allocation] = []
    for w in cohort:
        w_i = tenure_weight(w)
        is_vowed = w.covenant == "vowed"
        share = (w_i / total_w) if (is_vowed and total_w > 0) else 0.0
        # floor: never below prior standard (in-kind), capped at the stage ceiling, decaying
        capped_prior = min(w.prior_imputed_usd_micros_yr, stage_ceiling_usd_micros_yr)
        floor = int(round(capped_prior * decay)) if is_vowed else int(round(capped_prior * decay * 0.0))
        out.append(
            Allocation(
                subject_did=w.subject_did,
                weight=w_i,
                share=share,
                priority_rank=rank_of.get(w.subject_did, 0),
                floor_usd_micros_yr=floor,
                cash_stipend_usd_micros=0,  # INVARIANT
            )
        )
    return out


if __name__ == "__main__":  # tiny demo
    cohort = [
        DisplacedWorker("did:web:ex:veteran", tenure_months=30 * 12, hazard_permille=1800, prior_imputed_usd_micros_yr=8_000_000_000),
        DisplacedWorker("did:web:ex:midcareer", tenure_months=10 * 12, hazard_permille=1800, prior_imputed_usd_micros_yr=6_000_000_000),
        DisplacedWorker("did:web:ex:newcomer", tenure_months=1 * 12, hazard_permille=1800, prior_imputed_usd_micros_yr=4_000_000_000),
    ]
    for a in allocate(cohort, stage_ceiling_usd_micros_yr=5_000_000_000, elapsed_months=0):
        print(f"{a.subject_did:24s} w={a.weight:5.3f} share={a.share:5.3f} "
              f"rank={a.priority_rank} floor={a.floor_usd_micros_yr/1e6:7.1f} USD/yr cash={a.cash_stipend_usd_micros}")
