"""Tests: the moyai lexicons parse and carry the structural const invariants in-schema."""

from __future__ import annotations

import json
import os

from _harness import run_suite

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_LEX = os.path.join(_ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "moyai")


def _load(name):
    with open(os.path.join(_LEX, name), encoding="utf-8") as f:
        return json.load(f)


def _props(doc):
    return doc["defs"]["main"]["record"]["properties"]


def test_contribution_parses():
    doc = _load("contributionAttestation.json")
    assert doc["id"] == "com.etzhayyim.moyai.contributionAttestation"


def test_draw_parses():
    doc = _load("drawReceipt.json")
    assert doc["id"] == "com.etzhayyim.moyai.drawReceipt"


def test_contribution_const_invariants():
    p = _props(_load("contributionAttestation.json"))
    # the five structural locks that make a *reward* charter-clean
    assert p["redeemableUsdMicros"]["const"] == 0          # non-monetary / cash≡0
    assert p["transferable"]["const"] is False             # non-transferable / anti-sybil
    assert p["affectsBasicHighIncome"]["const"] is False   # BHI firewall
    assert p["grantsGovernanceWeight"]["const"] is False   # 1 SBT = 1 vote untouched
    assert p["grantsBenefitOrStage"]["const"] is False     # anti-class (G4 carve-out scoped)


def test_draw_const_invariants():
    p = _props(_load("drawReceipt.json"))
    assert p["redeemableUsdMicros"]["const"] == 0          # cash≡0
    assert p["essentialGuaranteed"]["const"] is True       # essential info always served


def test_contribution_required_fields_present():
    doc = _load("contributionAttestation.json")
    req = set(doc["defs"]["main"]["record"]["required"])
    for must in ("redeemableUsdMicros", "transferable", "affectsBasicHighIncome",
                 "grantsGovernanceWeight", "grantsBenefitOrStage"):
        assert must in req, f"invariant field {must} must be required"


def test_nodeclass_matches_compute_donation_forms():
    p = _props(_load("contributionAttestation.json"))
    assert set(p["nodeClass"]["knownValues"]) == {"ameno", "e7m", "kotoba"}


run_suite("test_lexicons", [
    ("contribution_parses", test_contribution_parses),
    ("draw_parses", test_draw_parses),
    ("contribution_const_invariants", test_contribution_const_invariants),
    ("draw_const_invariants", test_draw_const_invariants),
    ("contribution_required_fields", test_contribution_required_fields_present),
    ("nodeclass_matches_donation_forms", test_nodeclass_matches_compute_donation_forms),
])
