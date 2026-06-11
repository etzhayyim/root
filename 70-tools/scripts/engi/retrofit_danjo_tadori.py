#!/usr/bin/env python3
"""retrofit_danjo_tadori — map danjo/tadori findings onto 縁(:en) edges.

ADR-2606011000 §D6/§D7 (gated, design-first per §D9). danjo (ADR-2605301600) emits
`discrepancyObservation`s over `named-party` entities; tadori (ADR-2605301400) emits
`attributionFinding`s over actor/address/cluster entities. Both are already edges in
disguise — this is the reference transform that re-expresses them in the engi
vocabulary so the whole accountability surface lives on ONE graph.

NON-ADJUDICATING is preserved: a danjo observation is NOT a verdict, so its :en edge is
`:en/kind :entangled-with` (an observed relation), never an ownership/guilt assertion.
The §4(2) floor still governs which named parties may be published (danjo's own gate);
this transform does not widen it — it only changes the SHAPE of an already-permitted fact.
"""
from __future__ import annotations


def danjo_observation_to_en(obs: dict) -> dict:
    """danjo discrepancyObservation → :en edge (observed entanglement, non-adjudicating).

    obs shape (danjo manifest vocab): {"id", "subject", "object", "kind", "weight"}
    where subject/object are organism ids (named-party or institution) and kind is the
    observed relation (e.g. 'procurement', 'appointment', 'budget-line')."""
    return {
        ":en/id": f"en.danjo.{obs['id']}",
        ":en/kind": ":entangled-with",                 # observed, NOT adjudicated
        ":en/from": obs["subject"],
        ":en/to": obs["object"],
        ":en/grasping-load": float(obs.get("weight", 1.0)),
        ":en/source": ":danjo-observation",
        ":en/note": str(obs.get("kind", "discrepancy-observation")),
        ":en/sourcing": ":authoritative" if obs.get("verified") else ":representative",
    }


def tadori_finding_to_en(finding: dict) -> dict:
    """tadori attributionFinding → :en edge (on-chain custody/flow).

    finding shape (tadori manifest vocab): {"id", "actor", "entity", "txValue",
    "relation"} where actor→entity is the attributed control/flow and relation ∈
    {controls, funds, custodies}."""
    rel = finding.get("relation", "custodies")
    kind = ":custodies" if rel in ("controls", "custodies") else ":flows-to"
    return {
        ":en/id": f"en.tadori.{finding['id']}",
        ":en/kind": kind,
        ":en/from": finding["actor"],
        ":en/to": finding["entity"],
        # on-chain value is real custody/flow → contributes grasping-load directly.
        ":en/grasping-load": float(finding.get("txValue", 1.0)),
        ":en/source": ":onchain",
        ":en/note": rel,
        ":en/sourcing": ":authoritative",
    }


# Crosswalk table (also documented in RETROFIT-danjo-tadori.md), exposed for tests.
CROSSWALK = {
    "danjo.discrepancyObservation": {
        "en_kind": ":entangled-with",
        "source": ":danjo-observation",
        "note": "non-adjudicating; observed relation, never a verdict",
    },
    "danjo.named-party":      {"en_endpoint": ":organism (kind :human|:institutional)"},
    "tadori.attributionFinding": {
        "en_kind": ":custodies|:flows-to",
        "source": ":onchain",
        "note": "txValue → :en/grasping-load (real custody/flow)",
    },
    "tadori.cluster":         {"en_endpoint": ":organism (kind :synthetic|:institutional)"},
}


if __name__ == "__main__":
    obs = {"id": "obs-001", "subject": "org.state.jp.mof", "object": "org.corp.jp.vendor-x",
           "kind": "procurement", "weight": 3.0, "verified": True}
    fnd = {"id": "f-001", "actor": "org.addr.0xabc", "entity": "org.corp.exchange-y",
           "relation": "controls", "txValue": 12.5}
    import json
    print(json.dumps({"danjo": danjo_observation_to_en(obs),
                      "tadori": tadori_finding_to_en(fnd)}, indent=2, ensure_ascii=False))
