#!/usr/bin/env python3
"""sukashi 透かし — fraud-evidence bridge to akashi's malak candidate intake (ADR-2606071600 G13).

Maps sukashi :adfraud.signal/* records that are routed-to :akashi-malak into
com.etzhayyim.akashi.malakEvidenceCandidate-shaped records. This is the structural
expression of G13: sukashi NEVER runs its own malak import or makes an accusation — it
emits CANDIDATE evidence (reviewStatus = "candidate-only") and hands it to akashi's
existing review gate, which alone decides on any malak import.

Charter (G4/G13): every emitted record is non-adjudicating (nonAdjudicatingNotice = true),
reviewStatus is locked to "candidate-only" (sukashi cannot escalate), and it is OFFLINE —
this produces a fixture/record dict, it does not POST anything (no live handoff; G7/G11).

stdlib only. Usage:
    python3 methods/fraud_bridge.py            # write a candidate-evidence fixture from the seed
"""
from __future__ import annotations
import sys
import os
import json
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sukashi_edn import load_edn, classify  # noqa: E402

ATTESTING_DID = "did:web:etzhayyim.com:actor:sukashi"
# sukashi's own published method note describing how a signal was derived — the mandatory
# SECOND source (akashi requires sourceCids minLength 2): the evidence bundle + the method.
METHOD_NOTE_CID = "bafy-sukashi-methodnote-fraud-bridge-v0"

# sukashi fraud-kind → akashi candidateType (akashi knownValues only).
KIND_TO_CANDIDATE = {
    ":phishing-landing": "public-phishing-url-match",
    ":scam-finance": "brand-abuse-report-match",
    ":fake-endorsement": "brand-abuse-report-match",
    ":counterfeit-goods": "brand-abuse-report-match",
    ":domain-spoof": "public-ioc-domain-match",
    ":typosquat-delivery": "public-ioc-domain-match",
    ":malvertising-redirect": "public-ioc-domain-match",
    ":unauthorized-reseller": "public-ioc-domain-match",
    ":sellers-json-mismatch": "public-ioc-domain-match",
    ":shared-fraud-infra": "public-ioc-domain-match",
    ":cloaking": "public-ioc-domain-match",
}


def bridge_to_malak(fraud_signals):
    """Map :akashi-malak-routed sukashi signals → akashi malakEvidenceCandidate records.

    Only signals explicitly routed-to :akashi-malak are bridged; others belong to
    kurashimori / tasuke / danjo and are NOT akashi's concern. Returns a list of dicts
    shaped for com.etzhayyim.akashi.malakEvidenceCandidate.
    """
    out = []
    for f in fraud_signals:
        if f.get(":adfraud.signal/routed-to") != ":akashi-malak":
            continue
        kind = f.get(":adfraud.signal/kind", ":unknown")
        evidence = f.get(":adfraud.signal/evidence-cid")
        # sourceCids must have ≥2 entries: the evidence bundle + sukashi's method note.
        source_cids = [c for c in (evidence, METHOD_NOTE_CID) if c]
        if len(source_cids) < 2:
            source_cids = [evidence or "bafy-sukashi-evidence-missing", METHOD_NOTE_CID]
        rec = {
            "createdAt": f.get(":adfraud.signal/observed-at", "1970-01-01T00:00:00Z"),
            "candidateType": KIND_TO_CANDIDATE.get(kind, "public-ioc-domain-match"),
            "sourceCids": source_cids,
            "methodNoteCid": METHOD_NOTE_CID,
            "reviewStatus": "candidate-only",   # sukashi NEVER escalates (G13)
            "nonAdjudicatingNotice": True,      # G4
            "attestingDid": ATTESTING_DID,
        }
        if evidence:
            rec["publicIndicatorCid"] = evidence
        out.append(rec)
    return out


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = here / "data" / "seed-ad-supply-chain.kotoba.edn"
    outdir = here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    _, _, _, _, fraud = classify(load_edn(seed))
    candidates = bridge_to_malak(fraud)
    (outdir / "akashi-malak-candidates.json").write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"sukashi.fraud_bridge: {len(candidates)} candidate-evidence record(s) → akashi "
          f"malakEvidenceCandidate (reviewStatus=candidate-only; NO live import — G13). "
          f"wrote {outdir/'akashi-malak-candidates.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
