"""test_claims.py — identityClaim structural gates (G1/G2/G3/G4/G7). ADR-2606072100."""
from __future__ import annotations

from _t import expect_raises, run
from claims import build_claim, canonical_claim_bytes, external_subject_hash, validate_claim


def _valid_evm() -> dict:
    return build_claim(
        subject_did="did:web:etzhayyim.com:actor:x",
        factor_kind="wallet-evm",
        proof_kind="eip191",
        challenge_nonce="nonce-1",
        external_subject_hash=external_subject_hash("salt", "0xabc"),
        issued_at=1781000000,
        subject_sig="sig",
        verified=True,
        external_handle="0xabc…",
    )


def test_valid_evm_claim_builds():
    c = _valid_evm()
    assert c["factorClass"] == "key"
    validate_claim(c)


def test_external_subject_hash_stable_and_case_insensitive():
    a = external_subject_hash("s", "0xABC")
    b = external_subject_hash("s", "0xabc ")
    assert a == b and "=" not in a


def test_g4_wrong_proof_for_factor_raises():
    expect_raises(
        lambda: build_claim(
            subject_did="did:web:x", factor_kind="wallet-evm", proof_kind="bip322",
            challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
        ),
        contains="G4",
    )


def test_g3_gov_requires_encrypted_cid():
    expect_raises(
        lambda: build_claim(
            subject_did="did:web:x", factor_kind="gov-mynumber", proof_kind="nfc-jpki",
            challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
        ),
        contains="encryptedPayloadCid",
    )


def test_g3_gov_must_not_carry_plaintext_handle():
    expect_raises(
        lambda: build_claim(
            subject_did="did:web:x", factor_kind="gov-passport", proof_kind="nfc-jpki",
            challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
            external_handle="PASSPORT-NO-123", encrypted_payload_cid="bafyenc",
        ),
        contains="plaintext externalHandle",
    )


def test_g3_gov_valid_with_cid_no_handle():
    c = build_claim(
        subject_did="did:web:x", factor_kind="gov-mynumber", proof_kind="nfc-jpki",
        challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
        encrypted_payload_cid="bafyenc", verified=True,
    )
    assert c["factorClass"] == "government"


def test_g3_covenant_factor_cannot_carry_handle():
    expect_raises(
        lambda: build_claim(
            subject_did="did:web:x", factor_kind="etz-at-oath", proof_kind="at-record-sig",
            challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
            external_handle="leak",
        ),
        contains="may not carry a plaintext externalHandle",
    )


def test_g7_no_server_sig_field():
    c = _valid_evm()
    c["serverSig"] = "platform-key-signed"
    expect_raises(lambda: validate_claim(c), contains="G7 no-server-key")


def test_g7_subject_sig_mandatory():
    expect_raises(
        lambda: build_claim(
            subject_did="did:web:x", factor_kind="wallet-evm", proof_kind="eip191",
            challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="",
        ),
        contains="subjectSig",
    )


def test_g1_did_required():
    expect_raises(
        lambda: build_claim(
            subject_did="aaron", factor_kind="wallet-evm", proof_kind="eip191",
            challenge_nonce="n", external_subject_hash="h", issued_at=1, subject_sig="s",
        ),
        contains="subjectDid must be a DID",
    )


def test_canonical_bytes_exclude_sig_and_handle():
    c = _valid_evm()
    b = canonical_claim_bytes(c)
    assert b"subjectSig" not in b and b"externalHandle" not in b
    assert b"externalSubjectHash" in b  # the hash IS signed


CASES = [
    ("valid_evm_claim_builds", test_valid_evm_claim_builds),
    ("external_subject_hash_stable", test_external_subject_hash_stable_and_case_insensitive),
    ("g4_wrong_proof_raises", test_g4_wrong_proof_for_factor_raises),
    ("g3_gov_requires_cid", test_g3_gov_requires_encrypted_cid),
    ("g3_gov_no_handle", test_g3_gov_must_not_carry_plaintext_handle),
    ("g3_gov_valid", test_g3_gov_valid_with_cid_no_handle),
    ("g3_covenant_no_handle", test_g3_covenant_factor_cannot_carry_handle),
    ("g7_no_server_sig_field", test_g7_no_server_sig_field),
    ("g7_subject_sig_mandatory", test_g7_subject_sig_mandatory),
    ("g1_did_required", test_g1_did_required),
    ("canonical_bytes_exclude_sig", test_canonical_bytes_exclude_sig_and_handle),
]

if __name__ == "__main__":
    run("claims", CASES)
