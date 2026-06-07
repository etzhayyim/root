"""test_lexicons.py — the 4 shomei lexicons parse + their enums match factors.py (one SSoT).
ADR-2606072100."""
from __future__ import annotations

import json
import pathlib

from _t import run
from factors import CLASSES, FACTOR_KINDS, PROOF_KINDS, REVOCATION_REASONS

LEX_DIR = pathlib.Path(__file__).resolve().parents[3] / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "shomei"


def _load(name: str) -> dict:
    return json.loads((LEX_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def test_all_four_present_and_well_formed():
    for n in ("verificationChallenge", "identityClaim", "personhoodCredential", "bindingRevocation"):
        lex = _load(n)
        assert lex["lexicon"] == 1
        assert lex["id"] == f"com.etzhayyim.shomei.{n}"
        assert lex["defs"]["main"]["type"] == "record"


def test_identity_claim_enums_match_factors():
    p = _props(_load("identityClaim"))
    assert set(p["factorKind"]["enum"]) == set(FACTOR_KINDS)
    assert set(p["proofKind"]["enum"]) == set(PROOF_KINDS)
    assert set(p["factorClass"]["enum"]) == set(CLASSES)


def test_identity_claim_required_subject_sig_no_server_sig():
    lex = _load("identityClaim")
    req = lex["defs"]["main"]["record"]["required"]
    assert "subjectSig" in req
    p = _props(lex)
    for forbidden in ("serverSig", "platformSig", "operatorSig", "adminSig"):
        assert forbidden not in p, f"G7: {forbidden} must not be a lexicon field"


def test_challenge_factor_enum_matches():
    p = _props(_load("verificationChallenge"))
    assert set(p["factorKind"]["enum"]) == set(FACTOR_KINDS)


def test_personhood_enums_and_no_social_credit():
    p = _props(_load("personhoodCredential"))
    assert set(p["verifiedFactors"]["items"]["enum"]) == set(FACTOR_KINDS)
    assert p["assuranceLevel"]["enum"] == [0, 1, 2, 3, 4]
    for forbidden in ("score", "rank", "reputation", "trustScore", "worth", "socialCredit"):
        assert forbidden not in p, f"G8: {forbidden} must not be a credential field"


def test_revocation_reason_enum_matches():
    p = _props(_load("bindingRevocation"))
    assert set(p["reason"]["enum"]) == set(REVOCATION_REASONS)


CASES = [
    ("all_four_present", test_all_four_present_and_well_formed),
    ("identity_claim_enums", test_identity_claim_enums_match_factors),
    ("identity_claim_required_sig", test_identity_claim_required_subject_sig_no_server_sig),
    ("challenge_factor_enum", test_challenge_factor_enum_matches),
    ("personhood_enums_no_social_credit", test_personhood_enums_and_no_social_credit),
    ("revocation_reason_enum", test_revocation_reason_enum_matches),
]

if __name__ == "__main__":
    run("lexicons", CASES)
