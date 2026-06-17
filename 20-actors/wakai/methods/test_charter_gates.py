#!/usr/bin/env python3
"""wakai 和会 — structural charter-gate conformance tests over the central lexicons.

ADR-2605263500. wakai is a member-to-member SOLIDARITY POOL, **NOT insurance**: no
premium-as-contract, no actuarial pricing, no claim adjudication, no policy denial, no
underwriting, no investment-return promise, no commercial (re)insurance software, no DeFi
speculation. That discipline is operationalized **at the schema layer** via const fields
(lexicons/com/etzhayyim/wakai/README.md §Schema Discipline + §NOT-Insurance Boundary);
this is the first executable check that pins those exact values so a future edit cannot
silently turn the mutual-aid pool into an insurer or a yield vehicle.

wakai had NO dedicated charter-gate test before this file (verified 2026-06-16; the only
prior mentions are sibling cross-references in mimamori / kawase-yui).
Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import json
import os


def _lex_dir():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        cand = os.path.join(d, "00-contracts", "lexicons", "com", "etzhayyim", "wakai")
        if os.path.isdir(cand):
            return cand
        d = os.path.dirname(d)
    raise FileNotFoundError("could not locate 00-contracts/lexicons/com/etzhayyim/wakai")


LEX = _lex_dir()


def _load(name):
    with open(os.path.join(LEX, name)) as f:
        return json.load(f)


def _consts(doc):
    """field-name -> const value, for every const declared in the lexicon tree."""
    out = {}

    def walk(o, parent=None):
        if isinstance(o, dict):
            if "const" in o and isinstance(parent, str):
                out[parent] = o["const"]
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, parent)
    walk(doc)
    return out


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


# ── G6 — no investment-return promise / no speculation ──
def test_g6_no_investment_return_promise():
    c = _consts(_load("mutualAidContributionAttestation.json"))
    assert c.get("investmentReturnPromised") is False, "G6: investmentReturnPromised must be const false"
    assert "investmentReturnPromised" in _required_union(_load("mutualAidContributionAttestation.json"))


def test_g6_pool_is_stable_only_no_defi_speculation():
    c = _consts(_load("mutualAidPoolStateReport.json"))
    assert c.get("poolAssetClass") == "usdc-stable-only", "G6: pool must be usdc-stable-only"
    assert c.get("defiYieldFarmingActiveCount") == 0, "G6: no DeFi yield farming"
    assert c.get("tokenSpeculationActiveCount") == 0, "G6: no token speculation"


# ── G3 — NOT insurance: no claim adjudication / no denial ──
def test_g3_not_insurance_no_claim_adjudication():
    c = _consts(_load("mutualAidDistributionAttestation.json"))
    assert c.get("claimAdjudicated") is False, "G3: claimAdjudicated must be const false (community discernment, not adjudication)"


# ── G7 — no pre-existing-condition exclusion / no underwriting ──
def test_g7_no_pre_existing_condition_exclusion():
    doc = _load("mutualAidDistributionAttestation.json")
    c = _consts(doc)
    assert c.get("noPreExistingConditionExclusion") is True, "G7: noPreExistingConditionExclusion must be const true"
    assert "noPreExistingConditionExclusion" in _required_union(doc)


# ── G9 — community discernment distribution (Council ≥3) ──
def test_g9_distribution_requires_community_and_council_attestations():
    req = _required_union(_load("mutualAidDistributionAttestation.json"))
    assert "communityDiscernmentAttestations" in req, "G9: distribution must carry community discernment attestations"
    assert "councilAttestations" in req, "G9: distribution must carry Council attestations"


# ── L5 silenWakaiReview — the full anti-insurance / anti-speculation const ledger ──
def test_silen_review_const_ledger_exact():
    c = _consts(_load("silenWakaiReview.json"))
    expected = {
        "commercialInsuranceSoftwarePenetrationPct": 0,           # G4
        "commercialReInsurancePenetrationPct": 0,                 # G5
        "defiYieldFarmingActiveCount": 0,                         # G6
        "tokenSpeculationActiveCount": 0,                         # G6
        "claimDenialEventsCount": 0,                              # G3 anti-insurance
        "preExistingConditionExclusionEventsCount": 0,            # G7
        "administratorVocationFlowCompliantRatioPctIntegerHundredths": 10000,  # G11 (=100.00%)
    }
    for field, want in expected.items():
        assert c.get(field) == want, f"silenWakaiReview.{field} must be const {want}, got {c.get(field)!r}"


def test_silen_review_requires_its_const_fields():
    req = _required_union(_load("silenWakaiReview.json"))
    for field in ("commercialInsuranceSoftwarePenetrationPct", "claimDenialEventsCount",
                  "preExistingConditionExclusionEventsCount"):
        assert field in req, f"silenWakaiReview must require {field}"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"wakai/charter_gates: {len(fns)} tests passed (lex dir: {os.path.relpath(LEX)})")


if __name__ == "__main__":
    _run()
