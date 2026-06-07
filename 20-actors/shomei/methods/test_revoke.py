"""test_revoke.py — append-only revocation (G5 owner-only, G10 as-of). ADR-2606072100."""
from __future__ import annotations

from _t import expect_raises, run
from revoke import active_verified_factors, validate_revocation

SUB = "did:web:etzhayyim.com:actor:rev"


def _claim(kind, cid, issued=100, verified=True):
    return {"subjectDid": SUB, "factorKind": kind, "verified": verified,
            "issuedAt": issued, "cid": cid}


def _rev(kind, claim_ref, at=200, reason="key-rotated", subject=SUB):
    return {"subjectDid": subject, "claimRef": claim_ref, "factorKind": kind,
            "reason": reason, "revokedAt": at, "subjectSig": "sig"}


def test_valid_revocation():
    validate_revocation(_rev("wallet-evm", "claim:1"))


def test_g5_only_owner_revokes():
    claim = _claim("wallet-evm", "claim:1")
    expect_raises(
        lambda: validate_revocation(_rev("wallet-evm", "claim:1", subject="did:web:other"), claim),
        contains="only the owner revokes",
    )


def test_unknown_reason_raises():
    expect_raises(lambda: validate_revocation(_rev("wallet-evm", "c", reason="nuke")),
                  contains="unknown revocation reason")


def test_active_excludes_revoked_by_ref():
    claims = [_claim("wallet-evm", "claim:1"), _claim("sns-x", "claim:2")]
    revs = [_rev("wallet-evm", "claim:1")]
    assert active_verified_factors(claims, revs) == {"sns-x"}


def test_active_excludes_unverified():
    claims = [_claim("wallet-evm", "claim:1", verified=False)]
    assert active_verified_factors(claims, []) == set()


def test_revocation_does_not_delete_history():
    # The claim object is untouched; only aggregation excludes it (as-of, 永久記憶).
    claims = [_claim("wallet-evm", "claim:1")]
    revs = [_rev("wallet-evm", "claim:1")]
    _ = active_verified_factors(claims, revs)
    assert claims[0]["factorKind"] == "wallet-evm" and claims[0]["verified"] is True


def test_revoke_by_kind_when_no_ref_link():
    claims = [_claim("sns-github", None, issued=100)]
    revs = [_rev("sns-github", "missing-ref", at=150)]
    assert active_verified_factors(claims, revs) == set()


CASES = [
    ("valid_revocation", test_valid_revocation),
    ("g5_only_owner", test_g5_only_owner_revokes),
    ("unknown_reason", test_unknown_reason_raises),
    ("active_excludes_revoked", test_active_excludes_revoked_by_ref),
    ("active_excludes_unverified", test_active_excludes_unverified),
    ("revocation_keeps_history", test_revocation_does_not_delete_history),
    ("revoke_by_kind", test_revoke_by_kind_when_no_ref_link),
]

if __name__ == "__main__":
    run("revoke", CASES)
