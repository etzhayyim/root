"""test_verify.py — verify wiring policy (challenge binding, single-use, gov gate, crypto, sig).
ADR-2606072100."""
from __future__ import annotations

import hashlib
import hmac

from _t import expect_raises, run
from claims import build_claim, canonical_claim_bytes, external_subject_hash
from verify import (
    PROOF_ROUTING,
    GatedError,
    KotobaAuthVerifier,
    ReferenceVerifier,
    verify_claim,
)
from factors import PROOF_KINDS

SUBJECT = "did:web:etzhayyim.com:actor:t"
SALT = "salt-t"
TS = 1781000000


def _ref(secret: str, msg: bytes) -> str:
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def _mint(factor_kind, proof_kind, identifier, secret, *, handle=None, cid=None, nonce="nonce-t"):
    esh = external_subject_hash(SALT, identifier)
    from factors import FACTOR_CLASS

    skel = {
        "subjectDid": SUBJECT, "factorKind": factor_kind, "factorClass": FACTOR_CLASS[factor_kind],
        "proofKind": proof_kind, "challengeNonce": nonce, "externalSubjectHash": esh,
        "verified": True, "issuedAt": TS,
    }
    claim = build_claim(
        subject_did=SUBJECT, factor_kind=factor_kind, proof_kind=proof_kind, challenge_nonce=nonce,
        external_subject_hash=esh, issued_at=TS, subject_sig=_ref(secret, canonical_claim_bytes(skel)),
        verified=True, external_handle=handle, encrypted_payload_cid=cid,
    )
    challenge = {"subjectDid": SUBJECT, "factorKind": factor_kind, "nonce": nonce,
                 "issuedAt": TS, "expiresAt": TS + 600}
    pm = {"proof": _ref(secret, (nonce + "|" + esh).encode())}
    return claim, challenge, pm


def test_routing_table_covers_every_proof_kind():
    for p in PROOF_KINDS:
        assert p in PROOF_ROUTING, f"proofKind {p} not in PROOF_ROUTING wiring table"


def test_valid_claim_verifies():
    claim, ch, pm = _mint("wallet-evm", "eip191", "0xabc", "sec1", handle="0xabc")
    v = ReferenceVerifier({(SUBJECT, "wallet-evm"): "sec1"})
    res = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10)
    assert res["verified"] and res["reason"] == "ok"


def test_bad_proof_fails():
    claim, ch, pm = _mint("wallet-evm", "eip191", "0xabc", "sec1", handle="0xabc")
    pm["proof"] = "deadbeef"
    v = ReferenceVerifier({(SUBJECT, "wallet-evm"): "sec1"})
    res = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10)
    assert not res["verified"] and res["reason"] == "proof verification failed"


def test_wrong_subject_secret_fails_signature():
    claim, ch, pm = _mint("wallet-evm", "eip191", "0xabc", "sec1", handle="0xabc")
    v = ReferenceVerifier({(SUBJECT, "wallet-evm"): "WRONG"})
    res = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10)
    assert not res["verified"]


def test_challenge_subject_mismatch():
    claim, ch, pm = _mint("wallet-evm", "eip191", "0xabc", "sec1", handle="0xabc")
    ch["subjectDid"] = "did:web:someone-else"
    v = ReferenceVerifier({(SUBJECT, "wallet-evm"): "sec1"})
    res = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10)
    assert res["reason"] == "challenge subjectDid mismatch"


def test_challenge_expired():
    claim, ch, pm = _mint("wallet-evm", "eip191", "0xabc", "sec1", handle="0xabc")
    v = ReferenceVerifier({(SUBJECT, "wallet-evm"): "sec1"})
    res = verify_claim(claim, ch, v, proof_material=pm, now=TS + 999999)
    assert res["reason"] == "challenge expired"


def test_nonce_single_use():
    claim, ch, pm = _mint("wallet-evm", "eip191", "0xabc", "sec1", handle="0xabc")
    v = ReferenceVerifier({(SUBJECT, "wallet-evm"): "sec1"})
    seen: set[str] = set()
    first = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10, seen_nonces=seen)
    assert first["verified"]
    second = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10, seen_nonces=seen)
    assert second["reason"] == "nonce already consumed (replay)"


def test_gov_proof_gated_raises():
    claim, ch, pm = _mint("gov-mynumber", "nfc-jpki", "MY", "sec1", cid="bafyenc")
    v = ReferenceVerifier({(SUBJECT, "gov-mynumber"): "sec1"})  # allow_gated=False
    expect_raises(
        lambda: verify_claim(claim, ch, v, proof_material=pm, now=TS + 10),
        contains="Council-gated",
    )


def test_gov_proof_passes_when_gate_open():
    claim, ch, pm = _mint("gov-mynumber", "nfc-jpki", "MY", "sec1", cid="bafyenc")
    v = ReferenceVerifier({(SUBJECT, "gov-mynumber"): "sec1"}, allow_gated=True)
    res = verify_claim(claim, ch, v, proof_material=pm, now=TS + 10)
    assert res["verified"]


def test_kotoba_auth_verifier_documents_canonical_call():
    v = KotobaAuthVerifier()
    claim, ch, pm = _mint("wallet-btc", "bip322", "bc1q", "s", handle="bc1q")
    expect_raises(
        lambda: v.verify_proof("bip322", claim, pm),
        contains="kotoba_auth::btc::verify_message",
    )


CASES = [
    ("routing_table_covers_all", test_routing_table_covers_every_proof_kind),
    ("valid_claim_verifies", test_valid_claim_verifies),
    ("bad_proof_fails", test_bad_proof_fails),
    ("wrong_secret_fails_sig", test_wrong_subject_secret_fails_signature),
    ("challenge_subject_mismatch", test_challenge_subject_mismatch),
    ("challenge_expired", test_challenge_expired),
    ("nonce_single_use", test_nonce_single_use),
    ("gov_proof_gated_raises", test_gov_proof_gated_raises),
    ("gov_proof_passes_when_open", test_gov_proof_passes_when_gate_open),
    ("kotoba_auth_documents_call", test_kotoba_auth_verifier_documents_canonical_call),
]

if __name__ == "__main__":
    run("verify", CASES)
