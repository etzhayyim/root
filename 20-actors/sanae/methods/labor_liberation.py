"""labor_liberation — empirical Liberation Priority Score (LPS) + freed-labour-hours.

Per ADR-2606032100. Pure stdlib. Two computations:

  1. lps(...)            — the ranking score used to prioritize which toil to automate.
  2. freed_labor_hours() — given a deployment that automates a fraction of an occupation's
                           tasks, how many human labour-hours/year are freed, and how large
                           the displacement cohort is (feeds ADR-2606032130 pool sizing).

Everything is order-of-magnitude and `:representative` (G8). The point is the SHAPE of the
priority, not a sourced dataset; R2 replaces the seed with measured ISCO-occupation gap data.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectorGap:
    name: str
    isic: str
    isco: str
    unspsc: str
    headcount: float        # world employment in the occupation (persons)
    misery: float           # drudgery+danger+exploitation+dignity-deficit, ~[1,3]
    automatability: float   # OSS+edge-robotics feasibility, [0,1]
    charter_fit: float      # passes non-goals, [0,1] (0 = excluded, e.g. mining/weapons)
    coverage_gap: float     # 1 = no actor, 0 = already robotics-covered


def lps(g: SectorGap) -> float:
    """Liberation Priority Score = headcount × misery × automatability × charter_fit × coverage_gap.

    headcount is logged so a 0.8B sector does not swamp everything else by 10^4."""
    import math
    return math.log10(max(g.headcount, 1.0)) * g.misery * g.automatability * g.charter_fit * g.coverage_gap


def freed_labor_hours(
    headcount: float,
    hours_per_worker_yr: float,
    task_automation_fraction: float,
) -> float:
    """Human labour-hours/year removed by automating `task_automation_fraction` of the work."""
    return headcount * hours_per_worker_yr * task_automation_fraction


def displacement_cohort_size(headcount: float, task_automation_fraction: float) -> int:
    """Approx number of workers whose role is displaced (and thus owed the dividend)."""
    return int(round(headcount * task_automation_fraction))


# `:representative` seed for the ADR-2606032100 ranking (order-of-magnitude).
SEED_GAPS: list[SectorGap] = [
    SectorGap("sanae (field agriculture)", "A01", "6111/9211", "70", 7.0e8, 2.6, 0.55, 1.0, 0.85),
    SectorGap("hataori (garment/apparel)", "C13-14", "7531/8219", "53", 6.5e7, 2.9, 0.45, 1.0, 1.0),
    SectorGap("kiyome (domestic/cleaning)", "T/N81", "9111/9112", "76", 1.1e8, 2.4, 0.55, 1.0, 1.0),
    SectorGap("kamado (food service)", "I56", "5120/9412", "90", 1.0e8, 2.1, 0.45, 1.0, 1.0),
    SectorGap("kuramori (warehouse)", "H52", "9333/8219", "24", 4.0e7, 2.2, 0.70, 1.0, 0.9),
    SectorGap("tatekata (construction)", "F", "7119/9313", "72", 2.6e8, 2.6, 0.45, 1.0, 0.5),
    SectorGap("hofuri (meat processing)", "C10", "7511/9211", "23", 3.0e7, 2.9, 0.50, 1.0, 0.9),
    SectorGap("soma (forestry)", "A02", "6210/9215", "70", 5.0e6, 3.0, 0.40, 1.0, 1.0),
    SectorGap("ama (fishing/aquaculture)", "A03", "6222/9216", "70", 3.8e7, 2.9, 0.35, 1.0, 0.9),
    # excluded by N1 — charter_fit 0 → LPS 0, proving the gate zeroes it out
    SectorGap("MINING (excluded N1)", "B", "8111/9311", "20", 2.5e7, 3.0, 0.6, 0.0, 1.0),
]


def ranked_seed() -> list[tuple[str, float]]:
    return sorted(((g.name, lps(g)) for g in SEED_GAPS), key=lambda kv: kv[1], reverse=True)


if __name__ == "__main__":
    print("Liberation Priority Score ranking (:representative seed):")
    for i, (name, score) in enumerate(ranked_seed(), 1):
        print(f"  {i:2d}. {name:34s} LPS={score:5.2f}")
    fh = freed_labor_hours(7.0e8, 2000, 0.3)
    print(f"\nsanae illustrative: automating 30% of field-labour tasks frees "
          f"{fh/1e9:.1f}B labour-hours/yr; cohort ≈ {displacement_cohort_size(7.0e8, 0.3)/1e6:.0f}M workers.")
