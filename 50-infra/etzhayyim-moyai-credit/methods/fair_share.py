"""moyai 舫い — fair-share scheduler: where give-to-get meets the Basic-High-Income firewall.

This module decides, for a given draw request, whether it is FREE or must BURN credit. It is
the load-bearing answer to the design's two hard constraints:

  (A) "keep a reward for inference participation" — under contention, discretionary surplus
      compute is scheduled by reciprocity: those who contributed (hold credit) draw first.

  (B) "must NOT affect Basic High Income; it's give-to-get for *information*" — essential
      information access is never gated. Every member (and the public read path) gets an
      unconditional **subsistence floor** of inference, always, regardless of credit. That
      floor is *information-as-Basic-High-Income*: delivered by need, never by contribution.
      moyai credit only ever governs the *discretionary surplus above the floor, and only
      while the mesh is congested.*

So moyai is a **congestion fair-share scheduler, not a toll-gate**:

  - within the subsistence floor          → FREE, no credit, ever (information-as-BHI)
  - above the floor, mesh idle            → FREE (credit only matters under contention)
  - above the floor, mesh congested       → costs credit; contributors prioritised

The result: a member with zero moyai credit is *never* denied essential information and
their Basic High Income is *completely untouched*. They only wait, behind contributors, for
*non-essential surplus* compute *when the mesh is busy*. That is reciprocity for a scarce
shared resource — the 入会権 (iriai-ken, commons-use-right) model — not welfare and not a
benefit lever (anti-class).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Unconditional per-member inference allowance per period — "information-as-BHI". Delivered
# by need, never by contribution; moyai credit can neither increase nor decrease it.
SUBSISTENCE_FLOOR_UNITS = 100

# Mesh load (0.0..1.0) at/above which surplus draws start costing credit. Below this the mesh
# has spare capacity and surplus is free for everyone — credit only bites under contention.
CONTENTION_THRESHOLD = 0.80


class Decision(Enum):
    FREE_SUBSISTENCE = "free-subsistence"   # within floor → information-as-BHI, never gated
    FREE_IDLE = "free-idle"                 # above floor but mesh idle → free for all
    CHARGE_SURPLUS = "charge-surplus"       # above floor AND congested → burn credit
    DEFERRED_NO_CREDIT = "deferred"         # surplus wanted, congested, no credit → wait


@dataclass(frozen=True)
class DrawVerdict:
    decision: Decision
    credit_to_burn: int       # 0 unless CHARGE_SURPLUS
    essential_guaranteed: bool  # True whenever essential info is served (always within floor)
    note: str


def affects_basic_high_income() -> bool:
    """INVARIANT (the user's explicit constraint): moyai NEVER affects Basic High Income.

    The subsistence floor is unconditional and the only thing credit ever gates is
    discretionary surplus under contention. There is no code path by which holding,
    spending, or lacking moyai credit changes any member's BHI provision. Always False.
    """
    return False


def evaluate_draw(
    *,
    requested_units: int,
    floor_used_this_period: int,
    mesh_load: float,
    credit_balance: float,
) -> DrawVerdict:
    """Decide how a single draw of `requested_units` is served.

    `floor_used_this_period` = subsistence units the member has already consumed this period.
    Pure, deterministic function — no side effects, no RNG.
    """
    if requested_units <= 0:
        raise ValueError("moyai fair-share: requested_units must be positive")

    floor_remaining = max(0, SUBSISTENCE_FLOOR_UNITS - floor_used_this_period)

    # (1) Anything within the subsistence floor is free, unconditionally — information-as-BHI.
    if requested_units <= floor_remaining:
        return DrawVerdict(
            Decision.FREE_SUBSISTENCE, 0, True,
            "within subsistence floor — information-as-Basic-High-Income, never gated",
        )

    # Beyond the floor we are in *discretionary surplus* territory. The portion that still
    # fits in the floor is always served free; only the overage is subject to reciprocity.
    surplus = requested_units - floor_remaining

    # (2) If the mesh is not congested, surplus is free for everyone (credit only bites
    #     under contention — moyai is a fair-share scheduler, not a toll-gate).
    if mesh_load < CONTENTION_THRESHOLD:
        return DrawVerdict(
            Decision.FREE_IDLE, 0, True,
            f"surplus served free — mesh idle (load {mesh_load:.2f} < {CONTENTION_THRESHOLD})",
        )

    # (3) Above the floor AND congested → discretionary surplus costs credit. Contributors
    #     (credit holders) are scheduled first; the floor portion was already guaranteed free.
    if credit_balance + 1e-9 >= surplus:
        return DrawVerdict(
            Decision.CHARGE_SURPLUS, surplus, True,
            "surplus under contention — burning moyai credit (情報を得るには情報を生成する)",
        )

    # (4) Surplus wanted under contention but the requester never contributed → deferred,
    #     NOT denied: their essential floor was already served; only non-essential surplus
    #     waits behind contributors. Basic High Income is untouched (essential_guaranteed).
    return DrawVerdict(
        Decision.DEFERRED_NO_CREDIT, 0, True,
        "surplus deferred behind contributors — essential floor already served; "
        "contribute compute to draw surplus under load (give-to-get)",
    )
