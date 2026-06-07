"""export.py — 潮目 (shionome) → kanae render payload. ADR-2606072200.

kanae (鼎) renders fund flows (Sankey/treemap). shionome emits its capital-movement :flow
datoms in kanae fundFlowEdge shape and packages the aggregate concentration into a JSON-safe
render payload.

Honest scope (G11 + G2): only CAPITAL-MOVEMENT flow kinds are exported as fund flows
(rotation / fund-inflow / fund-outflow / fx-flow). Observation-only kinds (cross-correlation /
price-move / volume-shift / yield-shift) are in other units (zscore / pct / bps), NOT capital
amounts, so they are excluded and reported as a skip count (no silent drop). Every payload
carries isMirror + noTrade flags. Offline, deterministic; no live publish (G8).
"""

from __future__ import annotations

import json

from weave import CAPITAL_MOVEMENT_KINDS, _kw


def to_kanae_flow(f: dict) -> dict:
    """One shionome capital-movement :flow → one kanae fundFlowEdge. Raises if the kind is an
    observation-only kind (not a capital amount)."""
    kind = _kw(f.get(":flow/kind"))
    if kind not in CAPITAL_MOVEMENT_KINDS:
        raise ValueError(f"export: {kind!r} is an observation, not a capital flow (excluded from kanae render)")
    return {
        "edgeId": "shionome:" + str(f.get(":flow/id", "?")),
        "flowType": kind,
        "donor": f.get(":flow/source", ""),
        "recipient": f.get(":flow/target", ""),
        "amount": float(f.get(":flow/magnitude", 0.0)),
        "currency": f.get(":flow/unit", ""),
        "asOf": int(f.get(":flow/as-of", 0)),
        "noTrade": True,
        "sources": list(f.get(":flow/sources", [])),
    }


def to_kanae_flows(g: dict) -> dict:
    """All capital-movement :flow → kanae flows; observation-only kinds skipped + counted."""
    flows, skipped = [], []
    for f in g["flows"]:
        if _kw(f.get(":flow/kind")) in CAPITAL_MOVEMENT_KINDS:
            flows.append(to_kanae_flow(f))
        else:
            skipped.append(f.get(":flow/id"))
    return {"flows": flows, "skipped": skipped, "skipped_count": len(skipped)}


def render_payload(c: dict) -> dict:
    """JSON-safe aggregate concentration for a kanae render (Sankey/treemap-ready). Tuples are
    flattened to [key, value] pairs; no sets remain. Carries the mirror/no-trade flags."""
    return {
        "actor": "shionome",
        "isMirror": True,
        "noTrade": True,
        "counts": {k: c[k] for k in ("bucket_count", "flow_count", "snapshot_count")},
        "net_flow_by_bucket": c["net_flow_by_bucket"],
        "rotation_pairs": c["rotation_pairs"],
        "inflow_shares": [list(s) for s in c["inflow_concentration"]["shares"]],
        "inflow_hhi": c["inflow_concentration"]["hhi"],
        "by_asset_class": c["by_asset_class"],
        "by_region": c["by_region"],
        "regime": c["regime"],
        "correlation_clusters": c["correlation_clusters"],
    }


def render_json(c: dict) -> str:
    """The render payload as a JSON string (proves it is fully serializable)."""
    return json.dumps(render_payload(c), ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn
    from weave import concentration, weave

    g = weave(load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-capital-flow-graph.kotoba.edn"))
    kf = to_kanae_flows(g)
    print(f"# shionome → kanae export — {len(kf['flows'])} capital flows, {kf['skipped_count']} observation-only skipped")
    for f in kf["flows"]:
        print(f"  {f['flowType']:13} {f['donor']} → {f['recipient']}  {f['amount']:.1f} {f['currency']}")
    print("  render payload JSON bytes:", len(render_json(concentration(g)).encode("utf-8")))
