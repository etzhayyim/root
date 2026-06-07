"""test_aggregate.py — personhoodCredential + W3C VC (G3 no-PII, G8 no social-credit). ADR-2606072100."""
from __future__ import annotations

from _t import run
from aggregate import aggregate, assurance_label, did_hash, is_covenant_bound, to_w3c_vc

SUB = "did:web:etzhayyim.com:actor:agg"


def test_did_only_ial0():
    c = aggregate(SUB, set(), issued_at=1)
    assert c["assuranceLevel"] == 0 and c["proofOfPersonhood"] is False


def test_single_factor_ial1():
    c = aggregate(SUB, {"wallet-evm"}, issued_at=1)
    assert c["assuranceLevel"] == 1 and c["distinctClasses"] == 1


def test_multi_class_ial2_is_pop():
    c = aggregate(SUB, {"wallet-evm", "sns-github"}, issued_at=1)
    assert c["assuranceLevel"] == 2 and c["proofOfPersonhood"] is True


def test_two_wallets_one_class_not_pop():
    c = aggregate(SUB, {"wallet-evm", "wallet-btc"}, issued_at=1)
    assert c["distinctClasses"] == 1 and c["assuranceLevel"] == 1 and c["proofOfPersonhood"] is False


def test_covenant_bound_ial3_self_issued():
    c = aggregate(SUB, {"webauthn", "etz-adherent-sbt"}, issued_at=1)
    assert c["assuranceLevel"] == 3 and c["issuer"] == SUB  # self-issued ≤ IAL3


def test_gov_ial4_council_issued():
    c = aggregate(SUB, {"webauthn", "gov-mynumber"}, issued_at=1)
    assert c["assuranceLevel"] == 4 and c["issuer"].endswith("council:attestor")


def test_no_pii_in_credential():
    # G3: no EXTERNAL identifiers (handles/addresses/gov numbers/names). The subject's own DID
    # legitimately appears as `issuer` of a self-issued VC; linkage uses subjectDidHash.
    c = aggregate(SUB, {"wallet-evm", "sns-x"}, issued_at=1)
    blob = repr(c)
    assert "0x" not in blob and "@" not in blob  # no handles/addresses
    assert c["subjectDidHash"] == did_hash(SUB)
    assert c["issuer"] == SUB  # self-issued ≤ IAL3


def test_no_social_credit_fields():
    c = aggregate(SUB, {"wallet-evm", "sns-x"}, issued_at=1)
    for forbidden in ("score", "rank", "reputation", "trustScore", "worth", "behavior"):
        assert forbidden not in c, f"G8: {forbidden} must not exist in a personhoodCredential"


def test_w3c_vc_shape():
    c = aggregate(SUB, {"wallet-evm", "sns-x"}, issued_at=1)
    vc = to_w3c_vc(SUB, c)
    assert vc["type"] == ["VerifiableCredential", "EtzhayyimPersonhoodCredential"]
    assert vc["credentialSubject"]["id"] == SUB
    assert "proofOfPersonhood" in vc["credentialSubject"]


def test_helpers():
    assert assurance_label(4) == "government-verified"
    assert is_covenant_bound({"etz-at-oath"}) is True
    assert is_covenant_bound({"wallet-evm"}) is False


CASES = [
    ("did_only_ial0", test_did_only_ial0),
    ("single_factor_ial1", test_single_factor_ial1),
    ("multi_class_ial2_pop", test_multi_class_ial2_is_pop),
    ("two_wallets_one_class", test_two_wallets_one_class_not_pop),
    ("covenant_ial3_self", test_covenant_bound_ial3_self_issued),
    ("gov_ial4_council", test_gov_ial4_council_issued),
    ("no_pii", test_no_pii_in_credential),
    ("no_social_credit", test_no_social_credit_fields),
    ("w3c_vc_shape", test_w3c_vc_shape),
    ("helpers", test_helpers),
]

if __name__ == "__main__":
    run("aggregate", CASES)
