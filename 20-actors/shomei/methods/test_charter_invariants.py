"""test_charter_invariants.py — the load-bearing gates, enforced in THREE places each
(factors SSoT + lexicon enum + Python ValueError). Touch one, this suite fails. ADR-2606072100."""
from __future__ import annotations

from _t import expect_raises, run
from aggregate import aggregate
from claims import build_claim, validate_claim
from factors import GATED_PROOFS, PROOF_KINDS
from verify import PROOF_ROUTING, GatedError, ReferenceVerifier, verify_claim


def _g(**kw):
    base = dict(
        subject_did="did:web:etzhayyim.com:actor:i", factor_kind="wallet-evm", proof_kind="eip191",
        challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
    )
    base.update(kw)
    return build_claim(**base)


# G1 self-sovereign / DID-primary
def test_g1_did_required():
    expect_raises(lambda: _g(subject_did="aaron"), contains="must be a DID")


# G2 own-identity-only is structural: there is NO field to assert a THIRD party's identity.
def test_g2_no_third_party_subject_field():
    c = _g(external_handle="0xabc")
    assert "assertedAboutDid" not in c and "targetDid" not in c
    # the only identity field is subjectDid (== the signer)
    assert c["subjectDid"] == "did:web:etzhayyim.com:actor:i"


# G3 PII-never-plaintext
def test_g3_gov_requires_encrypted_cid():
    expect_raises(
        lambda: _g(factor_kind="gov-mynumber", proof_kind="nfc-jpki"),
        contains="encryptedPayloadCid",
    )


def test_g3_gov_rejects_plaintext_handle():
    expect_raises(
        lambda: _g(factor_kind="gov-license", proof_kind="nfc-jpki",
                   encrypted_payload_cid="bafy", external_handle="DL-123"),
        contains="plaintext externalHandle",
    )


# G4 cryptographic-proof-mandatory — every proofKind is wired to a kotoba-auth call
def test_g4_routing_total():
    assert set(PROOF_ROUTING) >= set(PROOF_KINDS)


def test_g4_wrong_proof_for_factor_unrepresentable():
    expect_raises(lambda: _g(factor_kind="wallet-btc", proof_kind="eip191"), contains="G4")


# G7 no-server-key — no server signature field can exist on a claim
def test_g7_server_sig_unrepresentable():
    c = _g(external_handle="0xabc")
    c["operatorSig"] = "x"
    expect_raises(lambda: validate_claim(c), contains="G7 no-server-key")


# G8 identity-assurance-not-social-credit — credential never carries a worth/score field,
# and assurance is a deterministic function of factor classes (no behavioral input).
def test_g8_no_score_field_and_deterministic():
    a = aggregate("did:web:x", {"wallet-evm", "sns-x"}, issued_at=1)
    b = aggregate("did:web:x", {"sns-x", "wallet-evm"}, issued_at=1)  # order-independent
    assert a["assuranceLevel"] == b["assuranceLevel"]
    for forbidden in ("score", "rank", "reputation", "worth", "behavior"):
        assert forbidden not in a


# G11 gov gate — gov L2 proof is Council-gated; verify raises at R0
def test_g11_gov_gate_in_force():
    assert GATED_PROOFS == frozenset({"nfc-jpki"})
    c = _g(factor_kind="gov-passport", proof_kind="nfc-jpki", encrypted_payload_cid="bafy")
    ch = {"subjectDid": c["subjectDid"], "factorKind": "gov-passport",
          "nonce": "n", "issuedAt": 1, "expiresAt": 10_000_000_000}
    v = ReferenceVerifier({}, allow_gated=False)
    expect_raises(
        lambda: verify_claim(c, ch, v, proof_material={}, now=2), contains="Council-gated"
    )


CASES = [
    ("g1_did_required", test_g1_did_required),
    ("g2_no_third_party_field", test_g2_no_third_party_subject_field),
    ("g3_gov_requires_cid", test_g3_gov_requires_encrypted_cid),
    ("g3_gov_rejects_handle", test_g3_gov_rejects_plaintext_handle),
    ("g4_routing_total", test_g4_routing_total),
    ("g4_wrong_proof", test_g4_wrong_proof_for_factor_unrepresentable),
    ("g7_server_sig_unrepresentable", test_g7_server_sig_unrepresentable),
    ("g8_no_score_deterministic", test_g8_no_score_field_and_deterministic),
    ("g11_gov_gate", test_g11_gov_gate_in_force),
]

if __name__ == "__main__":
    run("charter_invariants", CASES)
