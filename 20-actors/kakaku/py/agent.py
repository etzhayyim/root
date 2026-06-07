#!/usr/bin/env python3
"""kakaku 価格 — global price-difference / supply-demand intel actor (kotoba WASM cell).

ADR-2605091200 (resident ingest) + this actor's CLAUDE.md data model. Runs in-WASM
on kotoba :8077. Handlers operate over one kotoba EAVT graph of canonical products,
merchants, current offers, and an append-only `priceHistory` time series:

  handle_rank        cheapest / best-overall / suspicious over landed price (G3)
  handle_arbitrage   cross-merchant + cross-region price SPREAD for one product
  handle_supply_demand   availability + price-velocity → a bounded supply/demand index
  handle_demand      observation-frequency demand proxy (never a forecast; mitooshi owns that)
  handle_intel       aggregate-first price-transparency report (G4, public-good)
  handle_social      compose a charter-clean aggregate social post (G4/G11)

Constitutional posture (this is what separates kakaku from a trading/affiliate engine):

  G2 non-speculative   — kakaku surfaces price DIFFERENCE for the BUYER and routes supply
                         concentration to resilience; it NEVER emits a buy/sell trading
                         signal and never trades. Forecasting is mitooshi's job (distribution
                         -only). Arbitrage here = consumer transparency, not profit capture.
  G3 no ads/affiliate  — ranking is landed-price + trust only; affiliate params are stripped;
                         no paid placement, ever.
  G4 aggregate-first   — intel + social default to anonymized public aggregates; targeted
                         output is the gated exception (ossekai discipline).
  G5 Murakumo-only     — any LLM call is via the kotoba `llm` host binding (127.0.0.1:4000,
                         gemma3:4b); no external LLM client (ADR-2605215000).
  G6 kotoba state      — observations are kotoba Datoms (append-only priceHistory); no SQL.
  G11 outward-gated    — live social post / scrape ingest require an operator ref; this R0
                         build computes records and does not post or scrape live.

This R0 build computes and returns reports; it does not run live retailer ingest and
does not broadcast social posts (both G11-gated). Seed data is representative (G10).
"""
from __future__ import annotations

from statistics import median
from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# Per-week public-aggregate post ceiling (G4, mirrors ossekai aggregate_publisher).
SOCIAL_WEEKLY_CEILING = 100
# A spread at/above this fraction of the cheapest landed price is "notable" for intel.
NOTABLE_SPREAD_FRACTION = 0.15
# Trust/availability weights for best-overall ranking (CLAUDE.md "Ranking Rules").
_AVAILABILITY_RANK = {"in-stock": 2, "preorder": 1, "backorder": 0, "out-of-stock": -2, "unknown": -1}


# --------------------------------------------------------------------------- #
# landed price — the single comparison basis (CLAUDE.md: never sticker alone)
# --------------------------------------------------------------------------- #
def landed_price(offer: dict) -> int:
    """price + shippingFee in minor units. Cross-site comparison ranks on this, not
    sticker price (CLAUDE.md Ranking Rules)."""
    return int(offer.get("price", 0)) + int(offer.get("shippingFee", 0))


# --------------------------------------------------------------------------- #
# rank — cheapest / best-overall / suspicious
# --------------------------------------------------------------------------- #
class RankState(TypedDict, total=False):
    productId: str
    offers: list
    merchants: dict


def _best_overall_score(offer: dict, merchants: dict) -> float:
    """Weighted by landed price (lower better), availability, ETA, and merchant trust.
    Higher score = better overall offer. Never weighted by paid placement (G3)."""
    landed = landed_price(offer)
    avail = _AVAILABILITY_RANK.get(offer.get("availability", "unknown"), -1)
    eta_days = float(offer.get("deliveryEtaDays", 14))
    m = merchants.get(offer.get("merchantId"), {})
    trust = float(m.get("reputationScore", 0.5))
    # normalize landed into a 0..1-ish reward by inverse; small constant guards div0
    price_reward = 1_000_000.0 / (landed + 1.0)
    return price_reward + (avail * 2.0) - (eta_days * 0.05) + (trust * 3.0)


def _is_suspicious(offer: dict, landed_vals: list, merchants: dict) -> bool:
    """Unusually low landed price vs the field, inactive merchant, missing stock state,
    or a broken source URL (CLAUDE.md). Suspicious offers are flagged, never ranked #1."""
    m = merchants.get(offer.get("merchantId"), {})
    if m.get("status") not in (None, "active"):
        return True
    if not offer.get("availability") or offer.get("availability") == "unknown":
        return True
    if not offer.get("productUrl"):
        return True
    if len(landed_vals) >= 3:
        med = median(landed_vals)
        if med > 0 and landed_price(offer) < med * 0.4:  # <40% of median ⇒ too-good-to-be-true
            return True
    return False


def handle_rank(state: RankState) -> dict:
    offers = list(state.get("offers", []))
    merchants = state.get("merchants", {})
    if not offers:
        return {**state, "cheapest": None, "bestOverall": None, "suspicious": []}
    landed_vals = [landed_price(o) for o in offers]
    suspicious = [o for o in offers if _is_suspicious(o, landed_vals, merchants)]
    sus_ids = {id(o) for o in suspicious}
    clean = [o for o in offers if id(o) not in sus_ids] or offers
    cheapest = min(clean, key=landed_price)
    best = max(clean, key=lambda o: _best_overall_score(o, merchants))
    return {
        **state,
        "cheapest": cheapest,
        "bestOverall": best,
        "suspicious": suspicious,
    }


# --------------------------------------------------------------------------- #
# arbitrage — cross-merchant + cross-region price SPREAD (consumer transparency)
# --------------------------------------------------------------------------- #
def handle_arbitrage(state: dict) -> dict:
    """Compute the landed-price SPREAD for one canonical product across merchants and,
    when offers carry a `region`, across regions. This is buyer-facing transparency
    (where is it cheaper?) and a supply-resilience signal — NOT a trading instruction
    (G2): kakaku reports the gap, it does not tell anyone to capture it.

    Returns minLanded / maxLanded / spread / spreadFraction, a per-region min table,
    and `notable` when the spread crosses NOTABLE_SPREAD_FRACTION."""
    offers = [o for o in state.get("offers", []) if not o.get("suspicious")]
    if len(offers) < 2:
        return {**state, "spread": 0, "spreadFraction": 0.0, "notable": False, "byRegion": {}}
    landed = [(landed_price(o), o) for o in offers]
    lo_val, lo = min(landed, key=lambda t: t[0])
    hi_val, hi = max(landed, key=lambda t: t[0])
    spread = hi_val - lo_val
    frac = spread / lo_val if lo_val else 0.0

    by_region: dict = {}
    for val, o in landed:
        region = o.get("region", "unknown")
        cur = by_region.get(region)
        if cur is None or val < cur["minLanded"]:
            by_region[region] = {"minLanded": val, "merchantId": o.get("merchantId")}

    return {
        **state,
        "minLanded": lo_val,
        "maxLanded": hi_val,
        "cheapestMerchant": lo.get("merchantId"),
        "dearestMerchant": hi.get("merchantId"),
        "spread": spread,
        "spreadFraction": round(frac, 4),
        "notable": frac >= NOTABLE_SPREAD_FRACTION,
        "byRegion": by_region,
        # framing invariant (G2): consumer/resilience signal, never a trade
        "intent": "buyer-transparency+supply-resilience",
    }


# --------------------------------------------------------------------------- #
# supply/demand — bounded index from availability + price velocity
# --------------------------------------------------------------------------- #
def _price_velocity(history: list) -> float:
    """Signed fractional change between the oldest and newest observation in a sorted
    priceHistory window. Positive = rising (demand-pressure proxy), negative = falling."""
    pts = sorted(history, key=lambda h: h.get("observedAt", ""))
    if len(pts) < 2:
        return 0.0
    first = int(pts[0].get("totalPrice", pts[0].get("price", 0)))
    last = int(pts[-1].get("totalPrice", pts[-1].get("price", 0)))
    return (last - first) / first if first else 0.0


def handle_supply_demand(state: dict) -> dict:
    """Derive a bounded supply/demand index in [-1, 1] for one product from current
    offer availability (supply side) and recent price velocity (demand-pressure side).

    +1 ≈ tight supply / rising price (scarcity); -1 ≈ ample supply / falling price (glut).
    This is an OBSERVATION-derived index, not a forecast (G2): it describes the present
    state of the public market; mitooshi owns probabilistic futures."""
    offers = state.get("offers", [])
    history = state.get("priceHistory", [])
    if not offers:
        return {**state, "supplyDemandIndex": 0.0, "inStockRatio": 0.0, "priceVelocity": 0.0}

    in_stock = sum(1 for o in offers if o.get("availability") == "in-stock")
    in_stock_ratio = in_stock / len(offers)
    # supply scarcity rises as in-stock ratio falls
    scarcity = 1.0 - in_stock_ratio  # 0 (ample) .. 1 (scarce)
    velocity = _price_velocity(history)
    # blend: scarcity centered to [-1,1], plus clamped velocity; mean keeps it bounded
    scarcity_signed = (scarcity - 0.5) * 2.0
    velocity_clamped = max(-1.0, min(1.0, velocity * 4.0))  # ±25% move ⇒ saturates
    index = max(-1.0, min(1.0, (scarcity_signed + velocity_clamped) / 2.0))
    return {
        **state,
        "supplyDemandIndex": round(index, 4),
        "inStockRatio": round(in_stock_ratio, 4),
        "priceVelocity": round(velocity, 4),
        "reading": "scarcity" if index > 0.33 else "glut" if index < -0.33 else "balanced",
    }


# --------------------------------------------------------------------------- #
# demand — observation-frequency proxy (NOT a forecast)
# --------------------------------------------------------------------------- #
def handle_demand(state: dict) -> dict:
    """A demand PROXY from how often a product is observed/queried across merchants in
    the window — a present-tense interest signal, never a predicted future quantity
    (G2; forecasting is mitooshi). Returns observationCount + a normalized 0..1 share
    against the cohort total when provided."""
    history = state.get("priceHistory", [])
    obs = len(history)
    cohort_total = int(state.get("cohortObservationTotal", 0))
    share = (obs / cohort_total) if cohort_total else 0.0
    return {
        **state,
        "observationCount": obs,
        "merchantCount": len({h.get("merchantId") for h in history}),
        "demandShare": round(share, 4),
        "kind": "present-interest-proxy",  # G2: not a forecast
    }


# --------------------------------------------------------------------------- #
# intel — aggregate-first price-transparency report (public-good)
# --------------------------------------------------------------------------- #
def handle_intel(state: dict) -> dict:
    """Compose an aggregate-first intel record for one product: the spread, the cheapest
    landed offer, the supply/demand reading. Aggregate (anonymized) is the DEFAULT shape
    (G4); merchant names appear only because price transparency is the public good — no
    member targeting and no purchase nudge. Optionally narrated via Murakumo (G5)."""
    arb = handle_arbitrage(state)
    sd = handle_supply_demand(state)
    summary = {
        "productId": state.get("productId"),
        "minLanded": arb.get("minLanded"),
        "spread": arb.get("spread"),
        "spreadFraction": arb.get("spreadFraction"),
        "notable": arb.get("notable"),
        "supplyDemandIndex": sd.get("supplyDemandIndex"),
        "reading": sd.get("reading"),
        "shape": "aggregate",  # G4: aggregate-first
    }
    narration = _narrate(summary) if (llm is not None and state.get("narrate")) else None
    return {**state, "intel": summary, "narration": narration}


def _narrate(summary: dict) -> str | None:
    try:
        return str(
            llm.infer(  # type: ignore[union-attr]
                model="gemma3:4b",
                prompt="Write ONE neutral sentence of consumer price transparency (no "
                "buy/sell advice, no urgency) for this price summary: " + str(summary),
            )
        )
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# social — compose a charter-clean aggregate post (G4/G11)
# --------------------------------------------------------------------------- #
def handle_social(state: dict) -> dict:
    """Build (but do not broadcast) an aggregate-first social post from an intel record.
    Defaults to an anonymized public-good price-transparency note; never a purchase nudge,
    urgency, or affiliate link (G3/G4). Live posting is operator-gated (G11): without
    `operatorRef` the post is returned as a :draft and nothing is broadcast. The weekly
    aggregate ceiling (G4) is enforced against `postsThisWeek`."""
    intel = state.get("intel") or handle_intel(state).get("intel", {})
    posts_this_week = int(state.get("postsThisWeek", 0))
    if posts_this_week >= SOCIAL_WEEKLY_CEILING:
        return {**state, "post": None, "refused": True,
                "reason": f"weekly aggregate ceiling reached ({SOCIAL_WEEKLY_CEILING}/wk, G4)"}

    frac_pct = round(float(intel.get("spreadFraction", 0.0)) * 100, 1)
    text = (
        f"価格透明性: {intel.get('productId', 'product')} の現在の最安 landed 価格差は "
        f"{frac_pct}% ({intel.get('reading', 'balanced')})。"
        " 購買勧誘ではなく公共的な価格可視化です。"
    )
    post = {
        "text": text,
        "shape": "aggregate",      # G4 aggregate-first
        "lexicon": "app.bsky.feed.post",
        "affiliate": False,        # G3
        "nudge": False,            # G4: no urgency/purchase nudge
    }
    operator_ref = state.get("operatorRef")
    if not operator_ref:
        return {**state, "post": post, "state": "draft",
                "reason": "live broadcast is operator-gated (G11)"}
    return {**state, "post": post, "state": "posted", "operatorRef": operator_ref}
