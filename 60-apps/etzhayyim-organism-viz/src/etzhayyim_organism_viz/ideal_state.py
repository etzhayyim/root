"""Encoded ideal state — homeostatic ranges, not target values.

Per ADR-2605192100 §1.15 (non-eschatological), the ideal is a healthy
trajectory shape, not a fixed destination. Each `HomeostaticRange` defines
the band the corresponding observable should stay in. Outside the band on
either side is a `death_signature` — the organism is sick.

Source for the numerical bands: `90-docs/<TIMESTAMP>-ideal-ecosystem-state.md`
(emitted by the active-inference loop's first tick on this topic).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class HomeostaticRange:
    name: str
    symbol: str
    lo: float | None        # None = unbounded below
    hi: float | None        # None = unbounded above (unbounded above is OK; that's anti-eschatology)
    unit: str
    hard: bool              # True = constitutional invariant; ANY violation is a crisis
    death_signature: str    # human-readable warning


# Stocks + flows
RANGES: tuple[HomeostaticRange, ...] = (
    HomeostaticRange("Council seats filled",     "s_council",   5,    5,    "seats",  True,  "<5 → constitutional crisis"),
    HomeostaticRange("Substrate live",           "s_substrate", 6,    7,    "of 7",   False, "≤3 → single-substrate dependency"),
    HomeostaticRange("Charter Rider coverage",   "r_rider",     0.95, 1.0,  "ratio",  False, "<0.80 → sanctification 崩壊"),
    HomeostaticRange("Tithe ratio (exact)",      "r_tithe",     0.10, 0.10, "ratio",  True,  "≠ 10% → 産霊 violation"),
    HomeostaticRange("ADR velocity (30d avg)",   "v_adr",       0.5,  5.0,  "ADR/day",False, "=0 → stall; >5 → noise"),
    HomeostaticRange("Tick cadence",             "f_tick",      1/24, 24,   "/day",   False, "<1/wk → 縁起 broken"),
    HomeostaticRange("Cell count (alive)",       "n_cells",     30,   200,  "cells",  False, "<10 → 単純化; >500 → uncontrollable"),
    HomeostaticRange("Cell pruning ratio (90d)", "r_prune",     0.05, 0.20, "ratio",  False, "0% → bonsai 死; >40% → 焦土"),
    HomeostaticRange("Sister-corps",             "n_sister",    1,    None, "corps",  False, "=0 → reproduction unproven"),
    HomeostaticRange("Members net flow",         "dM_dt",       0,    None, "/Q",     True,  "<0 impossible per §1.3"),
    HomeostaticRange("Land alienation count",    "n_alien",     0,    0,    "events", True,  ">0 → constitutional crisis"),
    HomeostaticRange("MGI",                      "mgi",         1.0,  None, "ratio",  False, "≤1.0 → 子孫 priority breach"),
    HomeostaticRange("Chaos rehearsals (Q)",     "n_chaos",     1,    None, "/Q",     False, "=0/Y → anti-fragile decay"),
    HomeostaticRange("Hard invariant violations","n_viol",      0,    0,    "events", True,  "≥1 → Council convocation"),
    HomeostaticRange("Eschatological content",   "n_apoc",      0,    0,    "items",  True,  "≥1 → §1.15 violation"),
)


def in_range(rng: HomeostaticRange, value: float) -> bool:
    if rng.lo is not None and value < rng.lo:
        return False
    if rng.hi is not None and value > rng.hi:
        return False
    return True


def deviation(rng: HomeostaticRange, value: float) -> float:
    """Signed deviation outside the band. 0 if inside. Sign = direction of breach."""
    if rng.lo is not None and value < rng.lo:
        return value - rng.lo            # negative
    if rng.hi is not None and value > rng.hi:
        return value - rng.hi            # positive
    return 0.0
