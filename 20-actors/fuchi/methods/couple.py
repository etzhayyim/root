"""couple.py — 扶持 (fuchi) R1(d): Displacement-Dividend cohort coupling.

Per ADR-2606052300 R1 + ADR-2606032130 (Displacement Dividend) G2. This is the structural
join between the labor-liberation mission's two halves:

    a displacing actor automates human toil  ──▶  its SURPLUS becomes a donation
       (sanae / hataori / kiyome / tazuna …)        │
                                                     ▼  TitheRouter 10% split (ADR-2605192130)
                                          gross = tithe(10%) + earmark(90%)
                                                     │
                                                     ▼  per-cohort Public-Fund EARMARK
                                          the imputed-value BUDGET CEILING that 扶持's
                                          in-kind sustenance for that cohort draws on

**G2 coupling gate** (ADR-2606032130): *no live displacement without a funded cohort.* A
displacement event is ADMISSIBLE only if its cohort earmark is **funded** AND the committed
in-kind sustenance floor is **≤ the earmark**. Otherwise the displacement is REFUSED — the actor
may not shed human toil faster than the Public Fund can sustain the people affected.

Honest note on cash: the surplus→donation is a REAL USDC inflow into the Public Fund (donations
are USDC — that is allowed). What the maintainer/displaced worker RECEIVES is still in-kind,
cash≡0 (enforced at the allocate/route/book layer). The earmark is a budget ceiling in
imputed-value USD micros/yr, not a cash transfer to a person.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

TITHE_BPS = 1000  # 10% TitheRouter split (ADR-2605192130); basis points of 10_000


@dataclass(frozen=True)
class DisplacementEvent:
    displacing_actor: str
    cohort_id: str
    displaced_count: int
    surplus_usd_micros_yr: int
    funded: bool = False          # has the surplus→donation actually landed in the Public Fund?

    def __post_init__(self) -> None:
        if self.surplus_usd_micros_yr < 0:
            raise ValueError("surplus cannot be negative")
        if self.displaced_count < 0:
            raise ValueError("displaced_count cannot be negative")


@dataclass(frozen=True)
class CohortEarmark:
    cohort_id: str
    displacing_actor: str
    gross_usd_micros_yr: int
    tithe_usd_micros: int
    earmark_usd_micros_yr: int
    funded: bool

    def __post_init__(self) -> None:
        # exact integer split — gross = tithe + earmark (okaimono settlement-intent pattern)
        if self.tithe_usd_micros + self.earmark_usd_micros_yr != self.gross_usd_micros_yr:
            raise ValueError("TitheRouter split INVARIANT: gross must equal tithe + earmark exactly")


def earmark_from_surplus(event: DisplacementEvent) -> CohortEarmark:
    """Apply the 10% TitheRouter split to a displacing actor's surplus → a per-cohort earmark.
    gross = tithe + earmark, exact integer split (no rounding leak)."""
    gross = int(event.surplus_usd_micros_yr)
    tithe = gross * TITHE_BPS // 10_000
    earmark = gross - tithe
    return CohortEarmark(
        cohort_id=event.cohort_id,
        displacing_actor=event.displacing_actor,
        gross_usd_micros_yr=gross,
        tithe_usd_micros=tithe,
        earmark_usd_micros_yr=earmark,
        funded=bool(event.funded),
    )


def coupling_gate(
    event: DisplacementEvent,
    earmark: CohortEarmark,
    committed_floor_usd_micros_yr: int,
) -> dict:
    """G2 coupling gate — is this displacement admissible?

    Admissible iff the earmark is FUNDED and the committed in-kind sustenance floor is within it.
    A displacement with no funded cohort, or one that would commit more sustenance than the
    funded earmark covers, is REFUSED (no live displacement without a funded cohort).
    """
    committed = int(committed_floor_usd_micros_yr)
    if not earmark.funded:
        return {"event": event.displacing_actor, "cohort": event.cohort_id,
                "committed": committed, "headroom": 0, "admissible": False,
                "reason": "G2: no funded cohort earmark — displacement REFUSED "
                          "(surplus→donation has not landed in the Public Fund)"}
    if committed > earmark.earmark_usd_micros_yr:
        return {"event": event.displacing_actor, "cohort": event.cohort_id,
                "committed": committed, "headroom": earmark.earmark_usd_micros_yr - committed,
                "admissible": False,
                "reason": f"G2: committed sustenance {committed} exceeds funded earmark "
                          f"{earmark.earmark_usd_micros_yr} — displacement REFUSED "
                          "(cannot shed toil faster than the cohort can be sustained)"}
    return {"event": event.displacing_actor, "cohort": event.cohort_id,
            "committed": committed, "headroom": earmark.earmark_usd_micros_yr - committed,
            "admissible": True,
            "reason": "G2: funded cohort earmark covers the committed sustenance — admissible"}


def events_from_seed(records: list[dict]) -> list[DisplacementEvent]:
    return [DisplacementEvent(
        displacing_actor=r.get(":event/displacing-actor", "?"),
        cohort_id=r.get(":event/cohort-id", "?"),
        displaced_count=int(r.get(":event/displaced-count", 0)),
        surplus_usd_micros_yr=int(r.get(":event/surplus-usd-micros-yr", 0)),
        funded=bool(r.get(":event/funded", False)),
    ) for r in records]
