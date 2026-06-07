"""assemble_flows.py — 鼎 (kanae) domestic-flow-chain-assembly method (the coded R0 method).

Consumes a danjo budget ledger (danjo.methods.budget_ledger.build_ledger) and assembles
`com.etzhayyim.kanae.fundFlowEdge` records: the appropriation→outlay chain of the public
budget, as a graph of FACTUAL fiscal-flow edges (ADR-2605302300, domestic-flow-chain-assembly).

danjo finds, kanae renders. This is the render-input assembler. Constitutional discipline is
STRUCTURAL — built into the record shape, not left to the caller:
  G2  — output is kotoba-EAVT-bound datoms (no RisingWave/Postgres/Lance); here we emit the
        lexicon dicts that a kotoba cell asserts.
  G4  — NON-adjudicating: `flowClass` is descriptive only; `assert_non_adjudicating()` refuses
        any verdict token (crime/violation/guilt/違法/不正/有罪) anywhere in the edge.
  G5  — every edge cites ≥2 upstream gov.dataset.* record CIDs (the appropriation + its outlay).
  G6  — every edge names its open `methodNoteCid`.
  G10 — aggregate-first: endpoints are fiscal-authority / program / recipient-class aggregates;
        a named party would require `publiclyNamedBasis` (a source CID), which this method never
        fabricates — so no private recipient is named at R0.

Note: flowNarrative (the Murakumo-LLM factual description, G7) is NOT produced here — it requires
a live Murakumo node (murakumoInferenceAttestation.inferenceSubstrate const "murakumo"), which is
operator-gated. Offline we stop at the edge graph; the narrative is appended by the live cell.

Stdlib only. `created_at` is a parameter (default fixed) so assembly is deterministic + testable.
"""

from __future__ import annotations

from typing import Any

FLOW_CLASSES = {
    "appropriation", "outlay", "subaward", "procurement-award",
    "intergovernmental-transfer", "aid-disbursement", "loan", "repayment",
}
# Tokens that would turn a factual edge into a verdict — unrepresentable (G4).
_VERDICT_TOKENS = ("crime", "violation", "guilt", "fraud", "illegal", "違法", "不正", "有罪", "犯罪")

CELL_DID = "did:web:kanae.etzhayyim.com:cell:flow_assembler"
ATTEST_DID = "did:web:kanae.etzhayyim.com"
METHOD_NOTE = "kanae.methodNote:v1-global-seed:domestic-flow-chain-assembly:1.0.0-draft"
DEFAULT_CREATED_AT = "2026-06-07T00:00:00.000Z"


def _endpoint(kind: str, label: str, jurisdiction: str = "jpn") -> dict[str, Any]:
    """An aggregate endpoint (G10). No publiclyNamedBasis ⇒ no named party asserted."""
    return {"endpointKind": kind, "label": label, "jurisdiction": jurisdiction}


def assert_non_adjudicating(edge: dict[str, Any]) -> None:
    """G4: refuse any verdict token anywhere in the edge (defense in depth over the schema const)."""
    blob = " ".join(
        str(v) for v in (
            edge.get("flowClass", ""),
            edge.get("fromEndpoint", {}).get("label", ""),
            edge.get("toEndpoint", {}).get("label", ""),
        )
    ).lower()
    for tok in _VERDICT_TOKENS:
        if tok in blob:
            raise ValueError(f"G4 violation: verdict token {tok!r} in a fundFlowEdge")


def validate_edge(edge: dict[str, Any]) -> None:
    """Lexicon + charter gate check (fundFlowEdge required fields, enum, ≥2 CIDs)."""
    required = [
        "createdAt", "sourceCellDid", "flowClass", "fromEndpoint", "toEndpoint",
        "amount", "currency", "period", "jurisdiction", "sourceRecordCids",
        "methodNoteCid", "attestingDid",
    ]
    for f in required:
        if not edge.get(f) and edge.get(f) != 0:
            raise ValueError(f"fundFlowEdge missing required field {f!r}")
    if edge["flowClass"] not in FLOW_CLASSES:
        raise ValueError(f"flowClass {edge['flowClass']!r} not in lexicon enum")
    if len(edge["sourceRecordCids"]) < 2:
        raise ValueError("G5 violation: fundFlowEdge needs ≥2 sourceRecordCids")
    assert_non_adjudicating(edge)


def assemble(ledger: dict[str, Any], created_at: str = DEFAULT_CREATED_AT) -> list[dict[str, Any]]:
    """Budget ledger → fundFlowEdge list (appropriation + outlay chain).

    Each returned dict is a lexicon-valid fundFlowEdge PLUS yoro-projection annotations
    (`observedAt`, `_ministryLabel`, `_recipientLabel`) that the projector consumes.
    """
    edges: list[dict[str, Any]] = []
    treasury = _endpoint("fiscal-authority", "日本国 一般会計 (Japan General Account / National Treasury)")

    for key, g in sorted(ledger["groups"].items()):
        appropriations = g["appropriations"]
        outlays = g["outlays"]
        if not appropriations:
            # cannot ground an edge without an appropriation parent (G5 chain) — skip, observable gap
            continue
        approp = appropriations[0]
        ministry_label = approp["recipientName"]
        ministry = _endpoint("fiscal-authority", ministry_label)
        period = f"FY{g['fiscalYear']}"
        approp_cid = approp["cid"]
        # corroborating second CID for the appropriation edge: first outlay of the same program-year
        second_cid = outlays[0]["cid"] if outlays else (appropriations[1]["cid"] if len(appropriations) > 1 else None)

        if second_cid:
            approp_edge = {
                "createdAt": created_at,
                "sourceCellDid": CELL_DID,
                "flowClass": "appropriation",
                "fromEndpoint": treasury,
                "toEndpoint": ministry,
                "amount": str(approp["amountLocal"]),
                "currency": approp["currencyIso4217"],
                "period": period,
                "jurisdiction": g["jurisdiction"],
                "sourceRecordCids": [approp_cid, second_cid],
                "methodNoteCid": METHOD_NOTE,
                "stateAlignedFlag": approp["stateAlignedFlag"],
                "attestingDid": ATTEST_DID,
                # projection annotations (not part of the strict lexicon record):
                "observedAt": approp["awardDateUtc"],
                "_ministryLabel": ministry_label,
                "_recipientLabel": ministry_label,
                "_programCode": g["programCode"],
                "_sourceUrl": approp["sourceUrl"],
            }
            validate_edge(approp_edge)
            edges.append(approp_edge)

        for outlay in outlays:
            recipient = _endpoint("recipient-class", outlay["recipientName"])
            outlay_edge = {
                "createdAt": created_at,
                "sourceCellDid": CELL_DID,
                "flowClass": "outlay",
                "fromEndpoint": ministry,
                "toEndpoint": recipient,
                "amount": str(outlay["amountLocal"]),
                "currency": outlay["currencyIso4217"],
                "period": period,
                "jurisdiction": g["jurisdiction"],
                "sourceRecordCids": [outlay["cid"], approp_cid],  # outlay grounded by its appropriation (≥2)
                "methodNoteCid": METHOD_NOTE,
                "stateAlignedFlag": outlay["stateAlignedFlag"],
                "attestingDid": ATTEST_DID,
                "observedAt": outlay["awardDateUtc"],
                "_ministryLabel": ministry_label,
                "_recipientLabel": outlay["recipientName"],
                "_programCode": g["programCode"],
                "_sourceUrl": outlay["sourceUrl"],
            }
            validate_edge(outlay_edge)
            edges.append(outlay_edge)
    return edges


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "20-actors")
    from danjo.methods.budget_ledger import build_ledger, load_seed

    seed = sys.argv[1] if len(sys.argv) > 1 else "20-actors/danjo/data/gov-fiscal-seed.jp.json"
    edges = assemble(build_ledger(load_seed(seed)))
    print(f"assemble: {len(edges)} fundFlowEdge records")
    for e in edges:
        print(f"  {e['flowClass']:13} {e['period']} {e['fromEndpoint']['label'][:24]:24} → "
              f"{e['toEndpoint']['label'][:32]:32} ¥{int(e['amount']):,}")
