#!/usr/bin/env python3
"""kakaku 価格 — price-difference / supply-demand visualization payload + viewer.

ADR-2605091200. Reads the seed graph, computes the SAME signals as py/agent.py
(landed price, cross-merchant/region spread, supply/demand index) — agent.py is the
single source of truth, the viz never re-implements the math — and emits:

  1. viz/price-intel.json  — the viz payload (data CONTRACT the in-browser kotoba-wasm
     node / kami-engine consumes; browser-native, ADR-2606013600).
  2. viz/price-intel.htm   — a SELF-CONTAINED viewer (payload inlined into _template.htm;
     opens via file://, no external fetch).

A BUYER price-transparency + supply-resilience surface, NEVER a trading signal (kakaku G2):
the page shows where a thing is cheaper and whether supply is tight, never a buy/sell call.

stdlib only. Usage:
    python3 viz/build_viz_data.py [../kotoba/seed.edn]
"""
from __future__ import annotations
import json
import os
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "methods"))
sys.path.insert(0, str(_HERE.parent / "py"))
from kakaku_edn import classify, load_edn  # noqa: E402
import agent  # noqa: E402


def build_payload(products, merchants, offers, price_history) -> dict:
    """One viz record per product: ranked offers (landed) + spread + supply/demand,
    all via agent.py. Region is joined from the merchant registry."""
    region_of = {m["merchantId"]: m.get("region", "unknown") for m in merchants.values()}
    for o in offers:
        o["region"] = region_of.get(o["merchantId"], "unknown")

    cards = []
    for pid, p in products.items():
        # this seed carries one product; attach all offers to it
        poffers = offers
        arb = agent.handle_arbitrage({"offers": poffers})
        sd = agent.handle_supply_demand({"offers": poffers, "priceHistory": price_history})
        cards.append({
            "productId": pid,
            "name": p.get("name", pid),
            "offers": [{"merchantId": o["merchantId"], "region": o["region"],
                        "landed": agent.landed_price(o), "availability": o["availability"]}
                       for o in sorted(poffers, key=agent.landed_price)],
            "cheapestMerchant": arb.get("cheapestMerchant"),
            "minLanded": arb.get("minLanded"),
            "maxLanded": arb.get("maxLanded"),
            "spread": arb.get("spread"),
            "spreadFraction": arb.get("spreadFraction"),
            "notable": arb.get("notable"),
            "byRegion": arb.get("byRegion", {}),
            "supplyDemandIndex": sd.get("supplyDemandIndex"),
            "reading": sd.get("reading"),
            # G2 invariant, mirrored from agent.handle_arbitrage
            "intent": arb.get("intent", "buyer-transparency+supply-resilience"),
        })
    return {"generator": "kakaku/viz/build_viz_data.py",
            "intent": "buyer-transparency+supply-resilience", "cards": cards}


def render_html(payload: dict, template: pathlib.Path) -> str:
    tpl = template.read_text(encoding="utf-8")
    return tpl.replace("/*__PAYLOAD__*/null", json.dumps(payload, ensure_ascii=False))


def main(argv: list[str]) -> int:
    seed = pathlib.Path(argv[1]) if len(argv) > 1 else (_HERE.parent / "kotoba" / "seed.edn")
    rows = load_edn(seed)
    products, merchants, offers, ph = classify(rows)
    payload = build_payload(products, merchants, offers, ph)

    (_HERE / "price-intel.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    tpl = _HERE / "_template.htm"
    if tpl.exists():
        (_HERE / "price-intel.htm").write_text(render_html(payload, tpl))
    n_cards = len(payload["cards"])
    n_offers = sum(len(c["offers"]) for c in payload["cards"])
    print(f"kakaku viz: {n_cards} product card(s), {n_offers} offer(s) → price-intel.json"
          + (" + price-intel.htm" if tpl.exists() else " (no _template.htm)"))
    for c in payload["cards"]:
        print(f"  → {c['productId']}: spread {c['spread']} ({c['spreadFraction']}), "
              f"{c['reading']}, cheapest {c['cheapestMerchant']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
