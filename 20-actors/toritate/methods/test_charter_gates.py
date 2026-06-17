#!/usr/bin/env python3
"""toritate 執帳 — structural charter-gate conformance tests over the central lexicons.

ADR-2605262900. toritate is the accounting aggregation + transparent reporting + audit
attestation substrate — NOT a commercial accounting package. Its discipline is structural:
100% on-chain ledger (G3/G4), no fiat / no commercial accounting software (G8), no payroll
(G12 — volunteer ≠ employee), the 90/10 tithe split, donor-PII protection, and Council
attestation on annual + external-auditor records. This is the first executable check that
pins those gates at the schema layer (toritate is cross-linked by 7+ sibling actors —
wakai backstop, Public Fund, etc. — so a silent weakening here propagates widely).

toritate had NO dedicated charter-gate test before this file (verified 2026-06-16).
Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import json
import os

ON_CHAIN_RAILS = {"base-l2", "geth-private", "ipfs-record-only"}
NON_FIAT_ASSETS = {"usdc", "eth", "n-a"}
FIAT_TOKENS = ("usd", "jpy", "eur", "gbp", "cny", "fiat")  # must NOT be representable as ledger assets
PAYROLL_TOKENS = ("salary", "wage", "payroll", "bonus", "compensation")  # G12: no employment


def _lex_dir():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        cand = os.path.join(d, "00-contracts", "lexicons", "com", "etzhayyim", "toritate")
        if os.path.isdir(cand):
            return cand
        d = os.path.dirname(d)
    raise FileNotFoundError("could not locate 00-contracts/lexicons/com/etzhayyim/toritate")


LEX = _lex_dir()


def _load(name):
    with open(os.path.join(LEX, name)) as f:
        return json.load(f)


def _required_union(doc):
    s = set()

    def walk(o):
        if isinstance(o, dict):
            r = o.get("required")
            if isinstance(r, list):
                s.update(r)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(doc)
    return s


def _known(doc, field):
    out = set()

    def walk(o, parent=None):
        if isinstance(o, dict):
            if "knownValues" in o and parent == field:
                out.update(o["knownValues"])
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, parent)
    walk(doc)
    return out


# ── G3/G4 — 100% on-chain ledger ──
def test_ledger_entry_is_on_chain():
    doc = _load("ledgerEntry.json")
    req = _required_union(doc)
    for field in ("chain", "txCid", "counterpartyDid", "amountUsdMillicents"):
        assert field in req, f"G3/G4: ledgerEntry must require {field}"
    rails = _known(doc, "chain")
    assert rails == ON_CHAIN_RAILS, f"G3/G4: ledger chain must be exactly the on-chain rails {ON_CHAIN_RAILS}, got {rails}"


# ── G8 — no fiat asset is representable ──
def test_ledger_asset_is_non_fiat():
    assets = _known(_load("ledgerEntry.json"), "nativeAsset")
    assert assets == NON_FIAT_ASSETS, f"G8: nativeAsset must be exactly {NON_FIAT_ASSETS}, got {assets}"
    for tok in FIAT_TOKENS:
        assert tok not in assets, f"G8: fiat asset '{tok}' must not be representable"


# ── G8 — commercial accounting software + fiat leak are surfaced as audit observations ──
def test_audit_surfaces_commercial_software_and_fiat_leak():
    cats = _known(_load("auditObservation.json"), "observationCategory")
    for c in ("commercial-accounting-software-integration-attempt", "fiat-leak-attempt", "tithe-split-mismatch"):
        assert c in cats, f"G8: auditObservation must be able to flag '{c}'"


# ── G12 — no payroll: no salary/wage category exists ──
def test_no_payroll_category():
    cats = _known(_load("ledgerEntry.json"), "category")
    low = {c.lower() for c in cats}
    for tok in PAYROLL_TOKENS:
        assert not any(tok in c for c in low), f"G12: ledger category must not include payroll term '{tok}'"
    # subsistence/vocation/liberation/care flows ARE the volunteer-economy categories
    assert "subsistence-flow" in cats and "vocation-flow" in cats, "G12: volunteer-economy flow categories must exist"


# ── tithe 90/10 split is structural ──
def test_tithe_split_categories_present():
    cats = _known(_load("ledgerEntry.json"), "category")
    assert "tithe-split-90pct-operational" in cats, "tithe: 90% operational split category must exist"
    assert "tithe-split-10pct-public-fund" in cats, "tithe: 10% Public Fund split category must exist"


# ── donor-PII protection ──
def test_financial_attestation_protects_donor_pii():
    doc = _load("financialAttestation.json")
    assert "publishedDonorPii" in _required_union(doc), "donor-PII: financialAttestation must declare publishedDonorPii"
    enum = _known(doc, "publishedDonorPii")
    assert enum == {"none", "aggregated-only", "opt-in-explicit"}, \
        f"donor-PII: publishedDonorPii must be exactly the protected set, got {enum}"


# ── Council attestation on annual + external-auditor records ──
def test_council_attestation_required():
    assert "councilAttestations" in _required_union(_load("annualReport.json")), "annualReport must require councilAttestations"
    assert "councilAttestations" in _required_union(_load("externalAuditorEngagement.json")), \
        "externalAuditorEngagement must require councilAttestations"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"toritate/charter_gates: {len(fns)} tests passed (lex dir: {os.path.relpath(LEX)})")


if __name__ == "__main__":
    _run()
