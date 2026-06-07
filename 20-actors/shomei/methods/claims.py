"""claims.py — 証明 (shomei) identityClaim structural model + gate enforcement. ADR-2606072100.

Builds + validates a SELF-SOVEREIGN external-identity binding. The structural gates here are
the Python mirror of the lexicon `:const`/`:enum`; touching one means touching the lexicon too
(test_charter_invariants guards the pair). Validation RAISES (never silently drops) — keizu pattern.

Stdlib only.
"""
from __future__ import annotations

import hashlib
import json

from factors import (
    ALLOWED_PROOFS,
    CLASSES,
    FACTOR_CLASS,
    FACTOR_KINDS,
    GOV_FACTORS,
    PUBLIC_HANDLE_FACTORS,
    factor_class,
)

# The exact fields the subject signs over (order-significant for the canonical message).
SIGNED_FIELDS = (
    "subjectDid",
    "factorKind",
    "factorClass",
    "proofKind",
    "challengeNonce",
    "externalSubjectHash",
    "verified",
    "issuedAt",
)

# G7 no-server-key: a claim may NEVER carry a server signature. If any of these appear the
# record is rejected — the substrate has no place for a platform-held key (ADR-2605231525).
FORBIDDEN_SERVER_FIELDS = frozenset({"serverSig", "platformSig", "operatorSig", "adminSig"})


def external_subject_hash(salt: str, identifier: str) -> str:
    """Blake2b-256(salt || canonical-identifier) → base64url, privacy-preserving linkage (G3)."""
    import base64

    digest = hashlib.blake2b(
        (salt + "\x1f" + identifier.strip().lower()).encode("utf-8"), digest_size=32
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def canonical_claim_bytes(claim: dict) -> bytes:
    """Deterministic message the subject's Ed25519 key signs (G7: only the subject)."""
    payload = {k: claim[k] for k in SIGNED_FIELDS}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_claim(
    *,
    subject_did: str,
    factor_kind: str,
    proof_kind: str,
    challenge_nonce: str,
    external_subject_hash: str,
    issued_at: int,
    subject_sig: str,
    verified: bool = False,
    external_handle: str | None = None,
    encrypted_payload_cid: str | None = None,
    verifier_did: str | None = None,
) -> dict:
    claim = {
        "subjectDid": subject_did,
        "factorKind": factor_kind,
        "factorClass": factor_class(factor_kind),
        "proofKind": proof_kind,
        "challengeNonce": challenge_nonce,
        "externalSubjectHash": external_subject_hash,
        "verified": bool(verified),
        "issuedAt": int(issued_at),
        "subjectSig": subject_sig,
    }
    if external_handle is not None:
        claim["externalHandle"] = external_handle
    if encrypted_payload_cid is not None:
        claim["encryptedPayloadCid"] = encrypted_payload_cid
    if verifier_did is not None:
        claim["verifierDid"] = verifier_did
    validate_claim(claim)
    return claim


def validate_claim(claim: dict) -> dict:
    """Structural gate enforcement. Raises ValueError on any violation. Returns claim on success."""
    # G7 — no server-held signature field may exist.
    bad = FORBIDDEN_SERVER_FIELDS & set(claim)
    if bad:
        raise ValueError(f"G7 no-server-key: forbidden server signature field(s) {sorted(bad)}")

    required = (
        "subjectDid",
        "factorKind",
        "factorClass",
        "proofKind",
        "challengeNonce",
        "externalSubjectHash",
        "verified",
        "issuedAt",
        "subjectSig",
    )
    missing = [f for f in required if f not in claim]
    if missing:
        raise ValueError(f"identityClaim missing required field(s): {missing}")

    did = claim["subjectDid"]
    if not isinstance(did, str) or not did.startswith("did:"):
        raise ValueError(f"G1/G2: subjectDid must be a DID, got {did!r}")

    kind = claim["factorKind"]
    if kind not in FACTOR_KINDS:
        raise ValueError(f"unknown factorKind: {kind!r}")
    if claim["factorClass"] not in CLASSES:
        raise ValueError(f"unknown factorClass: {claim['factorClass']!r}")
    if claim["factorClass"] != FACTOR_CLASS[kind]:
        raise ValueError(
            f"factorClass {claim['factorClass']!r} != canonical {FACTOR_CLASS[kind]!r} for {kind!r}"
        )

    proof = claim["proofKind"]
    if proof not in ALLOWED_PROOFS[kind]:
        raise ValueError(
            f"G4: proofKind {proof!r} not allowed for {kind!r} (allowed {sorted(ALLOWED_PROOFS[kind])})"
        )

    if not isinstance(claim["challengeNonce"], str) or not claim["challengeNonce"]:
        raise ValueError("challengeNonce must be a non-empty string (anti-replay)")
    if not isinstance(claim["externalSubjectHash"], str) or not claim["externalSubjectHash"]:
        raise ValueError("externalSubjectHash must be a non-empty string")
    if not isinstance(claim["verified"], bool):
        raise ValueError("verified must be a boolean")
    if not isinstance(claim["issuedAt"], int):
        raise ValueError("issuedAt must be an integer unix timestamp")
    # G7: the SUBJECT must sign (only the subject); empty subject sig is invalid.
    if not isinstance(claim["subjectSig"], str) or not claim["subjectSig"]:
        raise ValueError("G7: subjectSig (subject-signed) is mandatory")

    # G3 PII-never-plaintext — government factors.
    has_handle = "externalHandle" in claim and claim["externalHandle"] not in (None, "")
    has_cid = "encryptedPayloadCid" in claim and claim["encryptedPayloadCid"] not in (None, "")
    if kind in GOV_FACTORS:
        if has_handle:
            raise ValueError(
                f"G3: gov factor {kind!r} MUST NOT carry a plaintext externalHandle (PII)"
            )
        if not has_cid:
            raise ValueError(
                f"G3: gov factor {kind!r} MUST carry an encryptedPayloadCid (XChaCha20, ADR-2605181100)"
            )
    else:
        if has_handle and kind not in PUBLIC_HANDLE_FACTORS:
            raise ValueError(
                f"G3: factor {kind!r} may not carry a plaintext externalHandle "
                f"(only public wallet/sns factors may)"
            )
    return claim
