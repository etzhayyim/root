#!/usr/bin/env python3
"""meyasu 目安 — unified arbitrage-intel dashboard payload + viewer.

Reads the representative fused inputs (kotoba/seed.json), runs them through py/agent.py's
handle_fuse (single source of truth — the viz re-implements no fusion logic), and emits:

  1. viz/meyasu-intel.json — the dashboard payload (data CONTRACT; browser-native)
  2. viz/meyasu-intel.htm  — a SELF-CONTAINED viewer (payload inlined; opens via file://)

One row per product: price spread, supply/demand now, forecast band, trajectory, and an
attention flag with its planner route. A BUYER-transparency + supply-resilience surface,
NEVER a trading board (meyasu G1): no buy/sell call, no affiliate, no purchase nudge.

stdlib only. Usage:
    python3 viz/build_viz_data.py [../kotoba/seed.json]
"""
from __future__ import annotations
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "py"))
import agent  # noqa: E402


def build_payload(seed_items: list) -> dict:
    fused = agent.handle_fuse({"items": seed_items})
    return {
        "generator": "meyasu/viz/build_viz_data.py",
        "intent": "buyer-transparency+supply-resilience",   # G1
        "cards": fused["cards"],
        "refused": fused["refused"],
    }


def render_html(payload: dict, template: pathlib.Path) -> str:
    return template.read_text(encoding="utf-8").replace(
        "/*__PAYLOAD__*/null", json.dumps(payload, ensure_ascii=False))


def main(argv: list[str]) -> int:
    seed = pathlib.Path(argv[1]) if len(argv) > 1 else (_HERE.parent / "kotoba" / "seed.json")
    items = json.loads(seed.read_text(encoding="utf-8")).get("items", [])
    payload = build_payload(items)
    (_HERE / "meyasu-intel.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    tpl = _HERE / "_template.htm"
    if tpl.exists():
        (_HERE / "meyasu-intel.htm").write_text(render_html(payload, tpl))
    n = len(payload["cards"])
    att = sum(1 for c in payload["cards"] if c.get("attention"))
    print(f"meyasu viz: {n} card(s), {att} attention → meyasu-intel.json"
          + (" + meyasu-intel.htm" if tpl.exists() else ""))
    for c in payload["cards"]:
        print(f"  → {c['productId']}: spread {c['priceSpread']} ({c['trajectory']}), "
              f"{'ATTENTION→'+c['routeTo'] if c['attention'] else 'route '+c['routeTo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
