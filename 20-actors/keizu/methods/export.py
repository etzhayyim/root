"""export.py — 系図 (keizu) → kanae render payload. ADR-2606066000.

The manifest promise: "keizu emits the relation/:money datoms kanae visualizes." This is the
outbound side of bridge.py: it maps keizu fiscal `:money` flows into kanae fundFlowEdge shape and
packages the aggregate concentration into a JSON-safe render payload (Sankey/treemap-ready).

Honest scope (G11 + G2): only kanae-representable FISCAL kinds are exported as fund flows
(procurement / subsidy / grant / outlay). `:political-donation` is NOT a government fiscal flow,
so it is excluded from the kanae payload and reported as a skip count (no silent drop). Offline,
deterministic; no live publish (G8).
"""

from __future__ import annotations

import json
from typing import Any

from weave import _kw

# keizu money-kind → kanae fundFlowEdge flowType (inverse of bridge.KANAE_FLOW_TO_KIND for the
# invertible fiscal kinds). political-donation is intentionally absent (not a govt fiscal flow).
KEIZU_KIND_TO_KANAE = {
    "budget-outlay": "outlay",
    "subsidy": "subsidy",
    "grant": "grant",
    "procurement-award": "procurement",
}


def to_kanae_flow(m: dict) -> dict:
    """One keizu :money → one kanae fundFlowEdge. Raises if the kind is not a govt fiscal flow."""
    kind = _kw(m.get(":money/kind"))
    if kind not in KEIZU_KIND_TO_KANAE:
        raise ValueError(f"export: {kind!r} is not a kanae fiscal flow (e.g. political-donation excluded)")
    return {
        "edgeId": "keizu:" + str(m.get(":money/id", "?")),
        "flowType": KEIZU_KIND_TO_KANAE[kind],
        "donor": m.get(":money/payer", ""),
        "recipient": m.get(":money/payee", ""),
        "amount": float(m.get(":money/amount", 0.0)),
        "currency": m.get(":money/currency", ""),
        "asOf": int(m.get(":money/as-of", 0)),
        "sources": list(m.get(":money/sources", [])),
    }


def to_kanae_flows(g: dict) -> dict:
    """All fiscal :money → kanae flows; non-fiscal kinds (political-donation) skipped + counted."""
    flows, skipped = [], []
    for m in g["money"]:
        if _kw(m.get(":money/kind")) in KEIZU_KIND_TO_KANAE:
            flows.append(to_kanae_flow(m))
        else:
            skipped.append(m.get(":money/id"))
    return {"flows": flows, "skipped": skipped, "skipped_count": len(skipped)}


def render_payload(c: dict) -> dict:
    """JSON-safe aggregate concentration for a kanae render (Sankey/treemap-ready). Tuples are
    flattened to [key, value] pairs; no sets remain. Carries the mirror/non-adjudicating flags."""
    return {
        "actor": "keizu",
        "isMirror": True,
        "nonAdjudicating": True,
        "counts": {k: c[k] for k in ("node_count", "committee_count", "rel_count",
                                     "money_count", "statement_count")},
        "money_by_payee": [list(s) for s in c["money_concentration"]["shares"]],
        "money_by_payer": [list(s) for s in c["payer_concentration"]["shares"]],
        "money_hhi": {"payee": c["money_concentration"]["hhi"],
                      "payer": c["payer_concentration"]["hhi"]},
        "by_jurisdiction": c["by_jurisdiction"],
        "committee_cross_organ": c["committee_cross_organ"],
        "cross_committee_seats": c["cross_committee_seats"],
        "connector_seats": c["connector_seats"],
        "revolving_door": c["revolving_door"],
        "award_and_fund": c["award_and_fund"],
        "statement_index": {"count": c["statement_index"]["count"],
                            "by_speaker": [list(s) for s in c["statement_index"]["by_speaker"]],
                            "by_topic": c["statement_index"]["by_topic"]},
    }


def render_json(c: dict) -> str:
    """The render payload as a JSON string (proves it is fully serializable)."""
    return json.dumps(render_payload(c), ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn
    from weave import concentration, weave

    g = weave(load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn"))
    kf = to_kanae_flows(g)
    print(f"# keizu → kanae export — {len(kf['flows'])} fiscal flows, {kf['skipped_count']} non-fiscal skipped")
    for f in kf["flows"]:
        print(f"  {f['flowType']:12} {f['donor']} → {f['recipient']}  {f['amount']:.0f} {f['currency']}")
    print("  render payload JSON bytes:", len(render_json(concentration(g)).encode("utf-8")))
