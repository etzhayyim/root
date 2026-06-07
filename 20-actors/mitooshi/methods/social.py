#!/usr/bin/env python3
"""mitooshi 見通し — aggregate-first resilience advisory + social post (R1, offline).

ADR-2606051800. The non-adjudicating delivery layer: turn a forecast DISTRIBUTION over a
public series (e.g. a kakaku supply-demand-index) into an aggregate-first resilience
advisory and an AT Proto social post — routed to a PLANNER, never rendered as advice.

This is the charter-clean inverse of a "price call". Every gate holds in code:

  G1 distribution-only   — a forecast with point_asserted=True is REFUSED at the door; the
                           text always states a band (mean ± sd), never a single number.
  G2 non-speculative     — use must be in the resilience set; trade/speculation is refused.
  G3 non-adjudicating    — every advisory MUST name a planner to route to (danjo/kanae/
                           watari); mitooshi states the distribution, the planner decides.
                           No advice / rating / valuation / 業績予想 text.
  G4 aggregate-first     — posts are anonymized aggregates (shape == "aggregate"); no target.
  G6 Murakumo-only       — optional narration via the kotoba `llm` host binding only.
  no-server-key          — live broadcast is operator-gated; default is a :draft.

stdlib only. Usage:
    python3 social.py --series s-… --mean 0.2 --sd 0.3 --route danjo
"""
from __future__ import annotations

import sys

try:
    from kotoba import llm  # type: ignore
except ImportError:  # local dev / offline
    llm = None  # type: ignore

# G2 — the only non-speculative uses; trade/speculation/wager/position are NOT members.
ALLOWED_USE = (":resilience", ":planning", ":nowcast", ":early-warning", ":research")
# G3 — the planners mitooshi may route a resilience advisory to (it never decides itself).
PLANNERS = ("danjo", "kanae", "watari")


def compose_resilience_advisory(series: str, mean: float, sd: float, target: int,
                                use: str = ":resilience", point_asserted: bool = False,
                                route_to: str = "danjo") -> dict:
    """Compose ONE aggregate-first resilience advisory from a forecast distribution. Refuses
    (ValueError) a point assertion (G1), an illegal use (G2), or a missing/invalid planner
    route (G3). The text states a BAND, never a single value."""
    if point_asserted:
        raise ValueError("G1: mitooshi cannot post a point-asserted forecast (distribution-only)")
    if use not in ALLOWED_USE:
        raise ValueError(f"G2: use {use!r} not in the non-speculative set {ALLOWED_USE}")
    if route_to not in PLANNERS:
        raise ValueError(f"G3: a resilience advisory must route to a planner {PLANNERS}, got {route_to!r}")
    lo, hi = round(mean - sd, 4), round(mean + sd, 4)
    text = (
        f"見通し(分布): 系列 {series} の t={target} 期待値は概ね [{lo}, {hi}] の範囲"
        f"(中心 {round(mean, 4)})。これは確率分布であり断定的な予測ではありません。"
        f"レジリエンス対応は {route_to} が判断します。"
    )
    return {
        "series": series,
        "text": text,
        "shape": "aggregate",          # G4
        "use": use,                     # G2
        "pointAsserted": False,         # G1
        "band68": [lo, hi],
        "routeTo": route_to,            # G3 — planner decides, mitooshi only states
        "lexicon": "app.bsky.feed.post",
        "narration": _narrate(series, lo, hi) if llm is not None else None,
    }


def _narrate(series: str, lo: float, hi: float):
    try:
        return str(llm.infer(  # type: ignore[union-attr]
            model="gemma3:4b",
            prompt=f"State, in ONE neutral sentence, that series {series} is expected in the "
                   f"range [{lo}, {hi}] as a probability distribution — no advice, no certainty."))
    except Exception:
        return None


def handle_social_post(state: dict) -> dict:
    """Compose aggregate resilience advisories from forecast records and (optionally) post.
    Each forecast = {series, mean, sd, target, [use], [pointAsserted], [routeTo]}. A point
    assertion (G1), illegal use (G2), or missing planner route (G3) is refused per-item with
    a reason. Live broadcast is operator-gated (no-server-key): without `operatorRef` posts
    are :draft. Aggregate-share is 100% (this layer never targets an individual, G4)."""
    operator_ref = state.get("operatorRef")
    posts: list = []
    refused: list = []
    for f in state.get("forecasts", []):
        try:
            adv = compose_resilience_advisory(
                series=f.get("series", "?"), mean=float(f.get("mean", 0.0)),
                sd=float(f.get("sd", 1.0)), target=int(f.get("target", 0)),
                use=f.get("use", ":resilience"), point_asserted=bool(f.get("pointAsserted", False)),
                route_to=f.get("routeTo", "danjo"))
        except ValueError as e:
            refused.append({"series": f.get("series"), "reason": str(e)})
            continue
        adv["state"] = "posted" if operator_ref else "draft"
        posts.append(adv)
    return {**state, "posts": posts, "refused": refused, "broadcast": bool(operator_ref),
            "aggregateSharePct": 100 if posts else 0}


def main(argv: list[str]) -> int:
    def opt(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default
    adv = compose_resilience_advisory(
        series=opt("--series", "s-demo"), mean=float(opt("--mean", "0.0")),
        sd=float(opt("--sd", "1.0")), target=int(opt("--target", "7")),
        route_to=opt("--route", "danjo"))
    print(adv["text"])
    print(f"  use={adv['use']} point={adv['pointAsserted']} route→{adv['routeTo']} shape={adv['shape']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
