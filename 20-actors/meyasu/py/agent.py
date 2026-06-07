#!/usr/bin/env python3
"""meyasu 目安 — unified arbitrage / supply-demand intel orchestrator (kotoba WASM cell).

The "統合 arbitrage アクター": meyasu does NOT compute price or forecast math itself — it
FUSES the outputs of three sibling actors into one per-product public-good intel surface:

  kakaku 価格   → cross-merchant/region price SPREAD + present supply/demand index
  mitooshi 見通し → the forecast DISTRIBUTION of that supply/demand index (next horizon)
  ossekai 御節介 → the aggregate-first publication discipline (this cell mirrors it)

  handle_fuse     kakaku spread/SD + mitooshi forecast → one unified arbitrage-intel card
  handle_publish  cards → aggregate-first social post + planner handoff

meyasu is a 目安 — a guide / yardstick, NOT a trade. The whole point of the name is that it
surfaces WHERE a good is cheaper and whether supply is tightening, for the BUYER and for
SUPPLY RESILIENCE — it never tells anyone to capture a spread.

Constitutional posture (the union of its siblings' invariants):

  G1 non-speculative   — intent is buyer-transparency + supply-resilience; meyasu never emits
                         a trade / price target and never settles money.
  G2 distribution-respecting — a forecast it consumes MUST be a distribution (point_asserted
                         false) with a resilience use; a point/speculative forecast is refused.
  G3 aggregate-first   — published intel is anonymized aggregate (shape == "aggregate").
  G4 non-adjudicating  — attention-flagged cards are ROUTED to a planner (okaimono for buyers,
                         danjo/kanae for resilience); meyasu states, the planner decides.
  G5 Murakumo-only     — any narration is via the kotoba `llm` host binding (no external LLM).
  no-server-key        — live publication is operator-gated; default is a :draft.

This R0 build computes and returns records/drafts; live ingest of sibling outputs and live
publication are operator-gated. Inputs are representative (G honesty).
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# G2 — a consumed forecast's use must be non-speculative (mirrors mitooshi ALLOWED_USE).
RESILIENCE_USES = (":resilience", ":planning", ":nowcast", ":early-warning", ":research")
# G4 — where an attention-flagged card is routed (meyasu never decides itself).
BUYER_PLANNER = "okaimono"        # provisioning-commons handles the buyer side
RESILIENCE_PLANNER = "danjo"      # accountability/resilience planner
# trajectory threshold on the supply/demand index forecast vs the present reading.
TRAJECTORY_DELTA = 0.1


# --------------------------------------------------------------------------- #
# fuse — kakaku (spread + SD now) + mitooshi (forecast band next) → one card
# --------------------------------------------------------------------------- #
class FuseState(TypedDict, total=False):
    items: list
    cards: list
    refused: list


def _trajectory(now_index, forecast_mean) -> str:
    """Compare the forecast supply/demand mean to the present index → a plain-language
    direction. 'tightening' = scarcity rising, 'easing' = glut rising, else 'stable'."""
    if now_index is None or forecast_mean is None:
        return "unknown"
    d = float(forecast_mean) - float(now_index)
    if d > TRAJECTORY_DELTA:
        return "tightening"
    if d < -TRAJECTORY_DELTA:
        return "easing"
    return "stable"


def fuse_one(item: dict) -> dict:
    """Fuse one product's kakaku + mitooshi records into a unified arbitrage-intel card.
    Raises ValueError if the forecast is a point assertion or a speculative use (G2)."""
    k = item.get("kakaku", {})
    f = item.get("mitooshi", {})
    if f:
        if f.get("pointAsserted"):
            raise ValueError("G2: consumed forecast is point-asserted (distribution-only)")
        if f.get("use") and f["use"] not in RESILIENCE_USES:
            raise ValueError(f"G2: forecast use {f['use']!r} is not in the resilience set")
    now_index = k.get("supplyDemandIndex")
    mean = f.get("mean")
    sd = f.get("sd")
    trajectory = _trajectory(now_index, mean)
    notable = bool(k.get("notable"))
    # attention = a notable spread that is ALSO forecast to tighten → route to resilience
    attention = notable and trajectory == "tightening"
    return {
        "productId": item.get("productId"),
        "priceSpread": k.get("spread"),
        "spreadFraction": k.get("spreadFraction"),
        "notableSpread": notable,
        "cheapestMerchant": k.get("cheapestMerchant"),
        "supplyDemandNow": now_index,
        "reading": k.get("reading"),
        "forecastBand": ([round(mean - sd, 4), round(mean + sd, 4)]
                         if (mean is not None and sd is not None) else None),
        "trajectory": trajectory,
        "attention": attention,
        "routeTo": RESILIENCE_PLANNER if attention else BUYER_PLANNER,   # G4
        "intent": "buyer-transparency+supply-resilience",                 # G1
    }


def handle_fuse(state: FuseState) -> dict:
    """Fuse a batch of per-product {kakaku, mitooshi} records into unified cards; a forecast
    that violates G2 is refused per-item with a reason (never silently dropped)."""
    cards: list = []
    refused: list = []
    for item in state.get("items", []):
        try:
            cards.append(fuse_one(item))
        except ValueError as e:
            refused.append({"productId": item.get("productId"), "reason": str(e)})
    return {**state, "cards": cards, "refused": refused}


# --------------------------------------------------------------------------- #
# publish — aggregate-first social post + planner handoff (G3/G4/no-server-key)
# --------------------------------------------------------------------------- #
def compose_card_post(card: dict) -> dict:
    """Compose ONE aggregate-first post from a unified card. Buyer transparency + resilience
    framing; no urgency, no affiliate, no purchase nudge, no trade call (G1/G3)."""
    frac_pct = round(float(card.get("spreadFraction", 0.0)) * 100, 1)
    text = (
        f"目安: {card.get('productId', 'product')} の現在の最安価格差は約 {frac_pct}%、"
        f"供給/需要は {card.get('reading', 'balanced')}、見通しは {card.get('trajectory', 'unknown')}。"
        " 公共的な価格・供給の透明化であり、売買の勧誘ではありません。"
    )
    return {
        "text": text,
        "shape": "aggregate",       # G3
        "lexicon": "app.bsky.feed.post",
        "nudge": False,             # G1 — no purchase/trade nudge
        "affiliate": False,
        "routeTo": card.get("routeTo"),
    }


def handle_publish(state: dict) -> dict:
    """Compose aggregate posts from fused cards and (optionally) publish. Attention cards are
    handed off to their planner (G4); publication is operator-gated (no-server-key): without
    `operatorRef` posts are :draft. Aggregate-share is 100% (never targets an individual)."""
    operator_ref = state.get("operatorRef")
    posts: list = []
    handoffs: list = []
    for c in state.get("cards", []):
        post = compose_card_post(c)
        post["state"] = "posted" if operator_ref else "draft"
        posts.append(post)
        if c.get("attention"):
            handoffs.append({"productId": c.get("productId"), "routeTo": c.get("routeTo"),
                             "reason": "notable spread + tightening forecast → resilience review"})
    return {**state, "posts": posts, "handoffs": handoffs, "broadcast": bool(operator_ref),
            "aggregateSharePct": 100 if posts else 0}


# --------------------------------------------------------------------------- #
# persist — fused card → kotoba Datoms (operator-gated write, no-server-key)
# --------------------------------------------------------------------------- #
def card_to_datoms(card: dict, observed_at: str) -> list:
    """Flatten a fused card into kotoba Datoms ([eid, attr, value]) over the meyasu schema.
    A forecast is written as a BAND (forecast-band-lo/hi), NEVER a point (G1/G2). Pure."""
    pid = card.get("productId", "unknown")
    eid = f"meyasu.card.{pid}.{observed_at}"
    band = card.get("forecastBand")
    datoms = [
        [eid, ":meyasu.card/id", eid],
        [eid, ":meyasu.card/product", pid],
        [eid, ":meyasu.card/price-spread", int(card.get("priceSpread") or 0)],
        [eid, ":meyasu.card/spread-fraction", float(card.get("spreadFraction") or 0.0)],
        [eid, ":meyasu.card/notable-spread", bool(card.get("notableSpread"))],
        [eid, ":meyasu.card/supply-demand-now", float(card.get("supplyDemandNow") or 0.0)],
        [eid, ":meyasu.card/reading", f":{card.get('reading', 'balanced')}"],
        [eid, ":meyasu.card/trajectory", f":{card.get('trajectory', 'unknown')}"],
        [eid, ":meyasu.card/attention", bool(card.get("attention"))],
        [eid, ":meyasu.card/route-to", card.get("routeTo", BUYER_PLANNER)],
        [eid, ":meyasu.card/intent", card.get("intent", "buyer-transparency+supply-resilience")],
        [eid, ":meyasu.card/observed-at", observed_at],
    ]
    if band:
        datoms.append([eid, ":meyasu.card/forecast-band-lo", float(band[0])])
        datoms.append([eid, ":meyasu.card/forecast-band-hi", float(band[1])])
    return datoms


def handle_persist(state: dict) -> dict:
    """Build the kotoba Datom transaction for the fused cards. no-server-key: the tx is
    RETURNED, not written, unless an `operatorRef` is present (G6/G11 outward-gated). The
    G1 invariant holds in the datoms — a forecast is a band, never a point assertion."""
    observed_at = state.get("observedAt", "1970-01-01T00:00:00Z")
    datoms: list = []
    for card in state.get("cards", []):
        datoms.extend(card_to_datoms(card, observed_at))
    operator_ref = state.get("operatorRef")
    return {
        **state,
        "datoms": datoms,
        "datomCount": len(datoms),
        "writeState": "committed" if operator_ref else "tx-only",   # no-server-key
        "operatorRef": operator_ref,
    }
