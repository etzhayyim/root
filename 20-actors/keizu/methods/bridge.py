"""bridge.py — 系図 (keizu) cross-actor compose: danjo + kanae → keizu :rel/:money. ADR-2606066000.

keizu sits atop its siblings (CLAUDE.md): it can compose **danjo** cross-reference links and
**kanae** fiscal-flow edges into its own relation graph. This bridge is a PURE mapping +
validation step — offline only; live sibling ingest is G8-gated.

The load-bearing property: every imported record is run through keizu's OWN gates
(`weave.validate_rel` / `validate_money`), so a sibling CANNOT smuggle a charter violation into
keizu. A danjo category that reads like a verdict, or a kanae edge with <2 sources, is REFUSED at
the import boundary — defense in depth for G2 (non-adjudicating) and G3 (≥2 sources).

Stdlib only.
"""

from __future__ import annotations

from typing import Any

from weave import VERDICT_TOKENS, _kw, validate_money, validate_rel

# kanae fundFlowEdge flow types → keizu money kinds (factual disclosed flows only).
KANAE_FLOW_TO_KIND = {
    "appropriation": "budget-outlay",
    "outlay": "budget-outlay",
    "subaward": "subsidy",
    "subsidy": "subsidy",
    "grant": "grant",
    "aid": "grant",
    "transfer": "grant",
    "loan": "grant",
    "procurement": "procurement-award",
    "award": "procurement-award",
}

# danjo crossReferenceLink link types → keizu factual rel kinds. NOTE: danjo is itself
# non-adjudicating, but the bridge re-asserts the gate (a verdict-ish category is refused).
DANJO_LINK_TO_KIND = {
    "awardee-officer-ubo-link": "co-membership",
    "officer-edge": "co-membership",
    "appointment": "appointment",
    "advisory": "advisory-role",
    "revolving-door": "revolving-door",
    "donor-recipient": "funding-tie",
    "procurement-award": "procurement-award",
    "statement-attribution": "statement-attribution",
}


def bridge_kanae_flow(edge: dict) -> dict:
    """kanae fundFlowEdge → validated keizu :money datom. Raises on an unknown flow type or a
    keizu-gate violation (G2/G3)."""
    flow = _kw(edge.get("flowType", edge.get(":flowType", "")))
    if flow not in KANAE_FLOW_TO_KIND:
        raise ValueError(f"bridge: unknown kanae flowType {flow!r} — refuse to guess (sourcing-honesty)")
    sources = [s for s in (edge.get("sources") or edge.get("sourceCids") or []) if str(s).strip()]
    m = {
        ":money/id": "kanae:" + str(edge.get("id", edge.get("edgeId", "?"))),
        ":money/payer": edge.get("donor", edge.get("from", "")),
        ":money/payee": edge.get("recipient", edge.get("to", "")),
        ":money/kind": ":" + KANAE_FLOW_TO_KIND[flow],
        ":money/amount": float(edge.get("amount", 0.0)),
        ":money/currency": edge.get("currency", ""),
        ":money/as-of": int(edge.get("asOf", 0)),
        ":money/sourcing": ":representative",   # an imported sibling record is representative (G11)
        ":money/sources": sources,
    }
    validate_money(m)   # keizu's own G2/G3 gate — the import cannot bypass it
    return m


def bridge_danjo_crossref(link: dict) -> dict:
    """danjo crossReferenceLink → validated keizu :rel datom. A verdict-bearing category is
    refused (G2 defense in depth); an under-sourced link is refused (G3)."""
    raw_kind = _kw(link.get("linkType", link.get("category", link.get("kind", ""))))
    if raw_kind in VERDICT_TOKENS:
        raise ValueError(f"bridge: danjo category {raw_kind!r} is a verdict — refused at import (G2)")
    if raw_kind not in DANJO_LINK_TO_KIND:
        raise ValueError(f"bridge: unmapped danjo link type {raw_kind!r} — refuse to guess")
    sources = [s for s in (link.get("sourceRecordCids") or link.get("sources") or []) if str(s).strip()]
    r = {
        ":rel/id": "danjo:" + str(link.get("id", link.get("linkId", "?"))),
        ":rel/source": link.get("from", link.get("source", "")),
        ":rel/target": link.get("to", link.get("target", "")),
        ":rel/kind": ":" + DANJO_LINK_TO_KIND[raw_kind],
        ":rel/weight": float(link.get("weight", 1.0)),
        ":rel/as-of": int(link.get("asOf", 0)),
        ":rel/non-adjudicating-notice": True,
        ":rel/sourcing": ":representative",
        ":rel/sources": sources,
    }
    validate_rel(r)     # keizu's own G2/G3 gate
    return r


def bridge_batch(batch: dict) -> dict:
    """Compose a mixed sibling batch → keizu datoms. Each record validated; the whole batch
    fails if any record violates a keizu gate (no partial smuggling)."""
    out: dict[str, list] = {"rels": [], "money": []}
    for e in batch.get("kanae", []):
        out["money"].append(bridge_kanae_flow(e))
    for l in batch.get("danjo", []):
        out["rels"].append(bridge_danjo_crossref(l))
    return out


if __name__ == "__main__":
    demo = {
        "kanae": [{"id": "f1", "flowType": "appropriation", "donor": "jp-mof", "payee": "jp-meti",
                   "recipient": "jp-meti", "amount": 1.0e9, "currency": "JPY", "asOf": 20250401,
                   "sources": ["https://www.mof.go.jp/a", "https://www.mof.go.jp/b"]}],
        "danjo": [{"id": "x1", "linkType": "awardee-officer-ubo-link", "from": "jp-vendor-x",
                   "to": "jp-fsc-biz-1", "asOf": 20250215,
                   "sourceRecordCids": ["cid:aaa", "cid:bbb"]}],
    }
    out = bridge_batch(demo)
    print(f"# keizu bridge — kanae→money={len(out['money'])} danjo→rels={len(out['rels'])} (all validated)")
    for m in out["money"]:
        print("  money", m[":money/id"], m[":money/kind"], m[":money/amount"])
    for r in out["rels"]:
        print("  rel  ", r[":rel/id"], r[":rel/kind"], r[":rel/source"], "→", r[":rel/target"])
