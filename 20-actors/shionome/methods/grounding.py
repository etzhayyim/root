"""grounding.py — 潮目 (shionome) stock-layer ENTITY-GROUNDING bridge. ADR-2606072200 (R1).

The stock pyramid (weave.stock_pyramid) sizes each money-and-markets LAYER as an aggregate
(equities ≈ $115tn, …). This bridge answers the next question HONESTLY: *who is inside each
layer?* — it decomposes a pyramid layer into the NAMED real entities that sibling actors already
mirror, and reports the COVERAGE gap (how much of the layer is actually grounded vs still
illustrative).

  - the EQUITIES layer ← kabuto 兜 listed-company ledger (org.corp.* — name/ticker/market-cap)
  - a cross-cutting SYSTEMIC-INSTITUTIONS overlay ← hokorobi 綻び (G-SIB banks / insurers /
    pensions / CCPs span equities+debt+pensions, so they are an overlay, NOT one pyramid layer)

DISCIPLINE (unchanged from the actor's gates):
  - G2 トレードはしない — a market-cap / institution count is a SIZE, descriptive, never a
    rating / signal / target / solvency verdict. Every report carries no_trade_notice = true.
  - G1 — the grounded entities are PUBLIC companies / systemic institutions already mirrored by
    kabuto / hokorobi (public/power-only, person-excluded); shionome adds no new entity, only a
    read-side view that names the constituents of a public asset class.
  - HONESTY — value_coverage is a stated LOWER BOUND (only sized companies contribute); the
    count denominator is an explicit :representative universe figure, not a live count;
    ungrounded_layers names exactly what is NOT yet backed by entities.
  - FAIL-OPEN — a missing/unreadable sibling ledger yields [] (the layer is reported ungrounded),
    never a crash. shionome's core (weave/concentration) does NOT import this bridge.

Stdlib only. Pure functions take already-loaded record lists; only load_ledger touches disk.
"""

from __future__ import annotations

import pathlib
from collections import Counter

from weave import _kw

# A :representative universe denominator (a documented public order-of-magnitude reference, NOT a
# live count) used ONLY to express count coverage as an honest fraction. ~50k–58k companies are
# exchange-listed worldwide (WFE statistics order of magnitude).
LISTED_UNIVERSE = 55000

# ── per-layer grounding ROADMAP (the honest map of what can / cannot be entity-grounded) ──────
# For every money-pyramid asset-class: which sibling actor's entity ledger (if any) can decompose
# it, and — where it CANNOT yet — the explicit reason. This turns "ungrounded" from a bare list
# into an actionable, honest roadmap. A macro AGGREGATE layer (M2, bond-market size, gold stock)
# is a central-bank / index aggregate, not a per-entity sum from any ledger the repo holds; G1
# would also bar holder-tracking for gold/cash/crypto. We do NOT fabricate a grounding the data
# cannot honestly support (トレードはしない discipline extends to coverage honesty).
LAYER_GROUNDING = {
    "equities":     {"source_actor": "kabuto",  "status": "grounded",
                     "reason": "listed-company ledger (org.corp.*) decomposes the layer by named issuer; kanjō adds disclosure depth"},
    "debt":         {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "bond-market SIZE is a SIFMA/BIS aggregate; no per-issuer debt-outstanding ledger (kanjō discloses corporate BS, NOT tradable debt-securities outstanding — conflating them would mis-size the layer). Candidate issuers: ooyake (sovereign) + kabuto (corporate)"},
    "broad-money":  {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "M2 is a central-bank / banking-system aggregate (BIS / World Bank); not entity-decomposable"},
    "cash":         {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "physical currency outstanding is a central-bank aggregate; no holder ledger (G1 bars holder-tracking)"},
    "real-estate":  {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "no real-estate-entity / parcel ledger in the repo; total value is a Savills aggregate"},
    "gold":         {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "above-ground stock value is a World Gold Council aggregate; no holder ledger (G1 bars holder-tracking)"},
    "crypto":       {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "total market-cap aggregate; no issuer ledger in the repo"},
    "derivatives":  {"source_actor": None,        "status": "ungroundable-at-r0",
                     "reason": "OTC gross-notional is a BIS aggregate; not entity-decomposable from any repo ledger"},
}


def load_ledger(path) -> list:
    """Load a sibling actor's EDN ledger (a top-level vector of records). FAIL-OPEN: a missing or
    unreadable ledger returns [] — the bridge degrades to 'ungrounded', it never crashes shionome."""
    p = pathlib.Path(path)
    if not p.exists():
        return []
    try:
        from _edn import load_edn
        data = load_edn(p)
    except Exception:  # noqa: BLE001 — fail-open by design
        return []
    return data if isinstance(data, list) else []


def kabuto_equity_constituents(records: list) -> list[dict]:
    """Named listed-company constituents of the global EQUITIES layer, from a kabuto ledger. A
    company record carries :company/name (address / contact / supply-edge / process records do
    not, so they are skipped). :company/market-cap-busd is a FACTUAL public-record size, never a
    rating (G2); it may be absent (the company is then named-but-unsized)."""
    out = []
    for r in records:
        if not isinstance(r, dict) or not r.get(":company/name"):
            continue
        mc = r.get(":company/market-cap-busd")
        out.append({
            "id": r.get(":company/id"),
            "name": r.get(":company/name"),
            "ticker": r.get(":company/ticker"),
            "country": r.get(":company/country"),
            "sector": _kw(r.get(":company/sector")) if r.get(":company/sector") else None,
            "market_cap_busd": float(mc) if mc is not None else None,
            "sourcing": _kw(r.get(":company/sourcing")) if r.get(":company/sourcing") else None,
        })
    return out


def hokorobi_institutions(records: list) -> list[dict]:
    """Systemic financial INSTITUTIONS from a hokorobi ledger (:organism/kind :institution). A
    cross-cutting overlay (G-SIB banks / insurers / pensions / CCPs span equities+debt+pensions —
    they do not belong to a single pyramid layer). Resilience overlay, never a solvency verdict (G2)."""
    out = []
    for r in records:
        if not isinstance(r, dict) or _kw(r.get(":organism/kind")) != "institution":
            continue
        out.append({
            "id": r.get(":organism/id"),
            "label": r.get(":organism/label"),
            "sector": _kw(r.get(":inst/sector")) if r.get(":inst/sector") else None,
            "sii": _kw(r.get(":inst/sii")) if r.get(":inst/sii") else None,
            "jurisdiction": r.get(":inst/jurisdiction"),
            "sourcing": _kw(r.get(":organism/sourcing")) if r.get(":organism/sourcing") else None,
        })
    return out


def kanjo_disclosed_companies(records: list) -> set:
    """The set of org.corp.* company ids that have ≥1 DISCLOSED filing in a kanjō ledger
    (:fin.filing/company). Used to measure DISCLOSURE DEPTH of the equities layer — which named
    constituents are not just listed but carry primary-disclosure financials (an authoritative
    depth signal). A presence count, never a fundamental rating (G2)."""
    out = set()
    for r in records:
        if isinstance(r, dict) and r.get(":fin.filing/company"):
            out.add(r[":fin.filing/company"])
    return out


def ground_equities(layer_usd_tn: float, constituents: list[dict],
                    universe: int = LISTED_UNIVERSE, disclosed_ids: set | None = None) -> dict:
    """Ground the EQUITIES stock layer in named listed companies, reporting HONESTLY:
      - grounded_entities       — how many named companies back the layer,
      - grounded_market_cap_usd_tn — Σ market-cap of the sized subset (→ value coverage of $layer),
      - value_coverage_of_layer — a LOWER BOUND (only companies that report a market-cap count),
      - count_coverage_of_universe — fraction of a :representative listed-universe denominator,
      - with_disclosed_financials — DEPTH: how many named constituents also carry kanjō primary
        disclosure (an authoritative-depth signal, not a fundamental rating).
    A size/count is factual; nothing here is a rating/signal/target (G2)."""
    disclosed_ids = disclosed_ids or set()
    n = len(constituents)
    sized = [c for c in constituents if c["market_cap_busd"] is not None]
    mcap_tn = sum(c["market_cap_busd"] for c in sized) / 1000.0  # USD billions → USD trillions
    top = sorted(sized, key=lambda c: -c["market_cap_busd"])[:10]
    disclosed = [c for c in constituents if c["id"] in disclosed_ids]
    return {
        "layer": "equities",
        "layer_usd_tn": round(float(layer_usd_tn), 4),
        "grounded_entities": n,
        "entities_with_size": len(sized),
        "grounded_market_cap_usd_tn": round(mcap_tn, 4),
        "value_coverage_of_layer": round(mcap_tn / layer_usd_tn, 4) if layer_usd_tn else 0.0,
        "value_coverage_is_lower_bound": len(sized) < n,
        "count_coverage_of_universe": round(n / universe, 5) if universe else 0.0,
        "universe_denominator": universe,
        "universe_sourcing": "representative",   # WFE order-of-magnitude, NOT a live count
        "with_disclosed_financials": len(disclosed),   # kanjō DEPTH (authoritative disclosure)
        "disclosed_sample": [c["name"] for c in disclosed][:10],
        "top_constituents": [
            {"name": c["name"], "ticker": c["ticker"], "market_cap_busd": c["market_cap_busd"]}
            for c in top
        ],
        "no_trade_notice": True,
    }


def grounding_roadmap(pyramid: dict) -> list[dict]:
    """Per-layer grounding STATUS for every money-pyramid layer — the honest map of what is
    entity-grounded vs what cannot be (and why), from the LAYER_GROUNDING registry. Turns the
    'ungrounded' set into an actionable roadmap rather than a bare list."""
    rows = []
    for l in pyramid.get("layers", []):
        ac = l["asset_class"]
        spec = LAYER_GROUNDING.get(ac, {"source_actor": None, "status": "unmapped",
                                         "reason": "no grounding spec for this asset class"})
        rows.append({
            "asset_class": ac,
            "layer_usd_tn": l.get("usd_tn"),
            "source_actor": spec["source_actor"],
            "status": spec["status"],
            "reason": spec["reason"],
        })
    return rows


def systemic_overlay(institutions: list[dict]) -> dict:
    """The cross-cutting systemic-institution overlay (from hokorobi). Counts by sector + sourcing
    honesty; it sizes nothing against a single layer. Resilience map, never a solvency verdict (G2)."""
    by_sector = dict(sorted(Counter(i["sector"] or "(unknown)" for i in institutions).items()))
    auth = sum(1 for i in institutions if i["sourcing"] == "authoritative")
    return {
        "institutions": len(institutions),
        "by_sector": by_sector,
        "authoritative": auth,
        "representative": len(institutions) - auth,
        "note": "cross-cutting systemic overlay — G-SIB banks / insurers / pensions / CCPs span "
                "equities+debt+pensions, not one pyramid layer; resilience map, never a solvency verdict",
        "no_trade_notice": True,
    }


def ground(pyramid: dict, kabuto_records: list, hokorobi_records: list,
           kanjo_records: list | None = None) -> dict:
    """The full stock-layer grounding report: decompose pyramid layers into named real entities
    WHERE a sibling ledger exists, add disclosure DEPTH (kanjō) to the equities layer, and stay
    HONEST about the rest via the per-layer roadmap. Every figure is an aggregate / size / coverage
    fraction — never a per-entity rating/signal/target (G2/G4)."""
    layers = {l["asset_class"]: l for l in pyramid.get("layers", [])}
    eq_layer = float(layers.get("equities", {}).get("usd_tn", 0.0))
    disclosed = kanjo_disclosed_companies(kanjo_records or [])
    equities = ground_equities(eq_layer, kabuto_equity_constituents(kabuto_records),
                               disclosed_ids=disclosed)
    overlay = systemic_overlay(hokorobi_institutions(hokorobi_records))
    grounded_classes = {"equities"} if equities["grounded_entities"] else set()
    ungrounded = [l["asset_class"] for l in pyramid.get("layers", [])
                  if l["asset_class"] not in grounded_classes]
    return {
        "equities": equities,
        "systemic_institutions_overlay": overlay,
        "roadmap": grounding_roadmap(pyramid),
        "ungrounded_layers": ungrounded,
        "summary": {
            "pyramid_layers": len(pyramid.get("layers", [])),
            "layers_with_entity_grounding": len(grounded_classes),
            "total_named_entities": equities["grounded_entities"] + overlay["institutions"],
            "no_trade_notice": True,
        },
    }


if __name__ == "__main__":
    from _edn import load_edn
    from weave import stock_pyramid, weave

    here = pathlib.Path(__file__).resolve()
    actor = here.parents[1]
    root = here.parents[3]
    g = weave(load_edn(actor / "data" / "seed-capital-flow-graph.kotoba.edn"))
    pyr = stock_pyramid(g)
    kab = load_ledger(root / "20-actors" / "kabuto" / "data" / "seed-public-companies.kotoba.edn")
    hok = load_ledger(root / "20-actors" / "hokorobi" / "data" / "seed-finrisk-graph.kotoba.edn")
    knj = load_ledger(root / "20-actors" / "kanjo" / "data" / "seed-financial-facts.kotoba.edn")
    rep = ground(pyr, kab, hok, knj)

    eq = rep["equities"]
    print("# 潮目 (shionome) — stock-layer ENTITY GROUNDING (どこまで実エンティティで裏付けたか)\n")
    print(f"## equities layer — ${eq['layer_usd_tn']:.0f}tn, grounded by {eq['grounded_entities']} named companies")
    print(f"- value coverage: ${eq['grounded_market_cap_usd_tn']:.1f}tn of ${eq['layer_usd_tn']:.0f}tn "
          f"= {eq['value_coverage_of_layer']*100:.1f}%"
          + ("  (LOWER BOUND — only sized companies count)" if eq["value_coverage_is_lower_bound"] else ""))
    print(f"- count coverage: {eq['grounded_entities']} / ~{eq['universe_denominator']} listed "
          f"(:{eq['universe_sourcing']}) = {eq['count_coverage_of_universe']*100:.2f}%")
    print(f"- disclosure depth (kanjō): {eq['with_disclosed_financials']} with primary-disclosure financials "
          f"{eq['disclosed_sample']}")
    print("- top constituents:")
    for c in eq["top_constituents"]:
        mc = c["market_cap_busd"]
        print(f"    {c['name']} ({c['ticker']}): ${mc:.0f}bn" if mc is not None else f"    {c['name']}")
    ov = rep["systemic_institutions_overlay"]
    print(f"\n## systemic-institutions overlay — {ov['institutions']} institutions "
          f"({ov['authoritative']} authoritative): {ov['by_sector']}")
    print("\n## per-layer grounding roadmap (what can/cannot be entity-grounded, and why)")
    for r in rep["roadmap"]:
        mark = "✓" if r["status"] == "grounded" else "·"
        src = r["source_actor"] or "—"
        print(f"  {mark} {r['asset_class']:<13} ${r['layer_usd_tn']:>6.0f}tn  [{r['status']}] src={src}")
        print(f"      {r['reason']}")
    s = rep["summary"]
    print(f"\n## summary: {s['layers_with_entity_grounding']}/{s['pyramid_layers']} pyramid layers grounded; "
          f"{s['total_named_entities']} named entities total — descriptive, NOT advice (トレードはしない)")
