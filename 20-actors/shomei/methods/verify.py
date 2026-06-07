"""verify.py — 証明 (shomei) VERIFY WIRING. ADR-2606072100.

This is the heart of the actor's G4 (cryptographic-proof-mandatory) discipline: it routes each
`proofKind` to the canonical kotoba-auth verification surface and enforces the verification POLICY
(challenge binding, single-use nonce, freshness, gov gate, subject-signature) in pure Python.

The cryptographic signature math itself lives in the canonical engine (`kotoba-auth`, ADR-2605262130)
— already implemented + tested in Rust. shomei NEVER reimplements secp256k1 / Ed25519 (Shannon: no
JS/Py reimplementation of an engine primitive). A `SignatureVerifier` is INJECTED:

  * `KotobaAuthVerifier`  — production: documents + delegates to the exact kotoba-auth fn (below).
  * `ReferenceVerifier`   — hermetic test double (HMAC-over-nonce) so the policy is fully testable.

PROOF_ROUTING is the wiring table: proofKind → canonical kotoba-auth call.

Stdlib only.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Protocol

import claims as claims_mod
from factors import GATED_PROOFS

# ── The wiring table (proofKind → canonical kotoba-auth verification call) ──────────────
# kotoba-auth fns confirmed present: eth::{personal_sign_hash, recover_eth_address, parse_address,
# to_checksum_address}; btc::{verify_message, signed_message_hash, recover_pubkey_from_message};
# cacao::DelegationChain::{verify_signature, verify_signature_eip191_smart}.
PROOF_ROUTING: dict[str, str] = {
    "eip191": (
        "kotoba_auth::eth::recover_eth_address("
        "kotoba_auth::eth::personal_sign_hash(siwe_msg), sig) "
        "== kotoba_auth::eth::parse_address(claimed_addr)"
    ),
    "eip1271": (
        "kotoba_auth::cacao::DelegationChain::verify_signature_eip191_smart(rpc)  "
        "# ERC-1271/4337 smart-wallet (ECDSA recover fails → isValidSignature)"
    ),
    "bip322": (
        "kotoba_auth::btc::verify_message(siwe_msg, sig, "
        "kotoba_auth::btc::address::BtcAddress::parse(claimed_addr))  # legacy signmessage R0"
    ),
    "oauth-sub": (
        "OIDC id_token verify against provider JWKS; bind `sub` + `nonce` claim "
        "(google/apple/github IdP); shomei stores only blake2b(salt||provider:sub)"
    ),
    "dns-txt": (
        "resolve TXT _etzhayyim-shomei.<domain> == proof token over nonce; "
        "host-controlled domain attests SNS/site ownership"
    ),
    "signed-gist": (
        "fetch member-hosted gist/file at the SNS handle; must contain subjectDid + nonce "
        "(GitHub/X profile-link gist convention)"
    ),
    "webauthn-assertion": (
        "WebAuthn P-256 ECDSA assertion verify over (clientDataJSON||challenge) "
        "(ADR-2605260000 §3 gov_auth)"
    ),
    "nfc-jpki": (
        "JPKI X.509 chain validate + local one-way NFC read (ADR-2605260000 Trust L2, "
        "Council-gated); plaintext encrypted XChaCha20 before substrate (G3/G6)"
    ),
    "base-l2-event": (
        "Base L2 read: EtzhayyimMembership Joined(subjectDid) event present (ADR-2605172600)"
    ),
    "erc5192-sbt": (
        "geth-private read: AdherentRegistry ERC-5192 ownerOf(tokenForSubject)==subject "
        "(ADR-2605172700)"
    ),
    "at-record-sig": (
        "AT oath record Ed25519 sig verify (com.etzhayyim.apps.etzhayyim.oath, ADR-2605172600)"
    ),
}


class GatedError(RuntimeError):
    """Raised when a Council-gated proof (gov L2) is attempted at R0."""


class SignatureVerifier(Protocol):
    def verify_proof(self, proof_kind: str, claim: dict, proof_material: dict) -> bool: ...

    def verify_subject_sig(self, claim: dict) -> bool: ...


class KotobaAuthVerifier:
    """Production verifier. Delegates to kotoba-auth (Rust, ADR-2605262130).

    R0: the Rust crate is not callable from this pure-Python scaffold, so each path raises with
    the EXACT canonical call to wire at R1 (honest — no fake 'success'). PROOF_ROUTING is the map.
    """

    def verify_proof(self, proof_kind: str, claim: dict, proof_material: dict) -> bool:
        target = PROOF_ROUTING.get(proof_kind, "<unknown>")
        raise NotImplementedError(
            f"KotobaAuthVerifier.verify_proof({proof_kind!r}): wire to → {target}"
        )

    def verify_subject_sig(self, claim: dict) -> bool:
        raise NotImplementedError(
            "KotobaAuthVerifier.verify_subject_sig: wire to → kotoba-auth Ed25519 "
            "verify over claims.canonical_claim_bytes(claim) with subjectDid's signing key"
        )


class ReferenceVerifier:
    """Hermetic test double. 'Control' is simulated as knowing a per-(subject,factor) secret:
    proof_material['proof'] must equal HMAC(secret, nonce || externalSubjectHash). subjectSig must
    equal HMAC(secret, canonical_claim_bytes). Lets the verification POLICY be tested without a
    crypto lib while preserving the nonce-binding + subject-sig structure of the real path.
    """

    def __init__(self, secrets: dict[tuple[str, str], str], *, allow_gated: bool = False):
        self._secrets = secrets  # (subjectDid, factorKind) → secret
        self.allow_gated = allow_gated

    def _tok(self, secret: str, msg: bytes) -> str:
        return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

    def verify_proof(self, proof_kind: str, claim: dict, proof_material: dict) -> bool:
        key = (claim["subjectDid"], claim["factorKind"])
        secret = self._secrets.get(key)
        if secret is None:
            return False
        msg = (claim["challengeNonce"] + "|" + claim["externalSubjectHash"]).encode()
        return hmac.compare_digest(self._tok(secret, msg), proof_material.get("proof", ""))

    def verify_subject_sig(self, claim: dict) -> bool:
        key = (claim["subjectDid"], claim["factorKind"])
        secret = self._secrets.get(key)
        if secret is None:
            return False
        return hmac.compare_digest(
            self._tok(secret, claims_mod.canonical_claim_bytes(claim)), claim["subjectSig"]
        )


def verify_claim(
    claim: dict,
    challenge: dict,
    verifier: SignatureVerifier,
    *,
    proof_material: dict | None = None,
    now: int,
    seen_nonces: set[str] | None = None,
) -> dict:
    """Run the full verification POLICY for one claim. Returns a result dict
    {verified, factorKind, factorClass, reason}. Marks the nonce consumed in seen_nonces.

    Policy (all enforced before any crypto): structural gate (claims.validate_claim) → challenge
    binding (subject + factor + nonce match) → freshness (now ≤ expiresAt) → single-use →
    gov-gate (nfc-jpki Council-gated at R0) → crypto proof → subject Ed25519 signature.
    """
    proof_material = proof_material or {}
    seen_nonces = seen_nonces if seen_nonces is not None else set()

    claims_mod.validate_claim(claim)  # structural gates G1/G2/G3/G4/G7

    # Challenge binding (anti-relay): the signed nonce must be the one issued to THIS subject+factor.
    if challenge.get("subjectDid") != claim["subjectDid"]:
        return _fail(claim, "challenge subjectDid mismatch")
    if challenge.get("factorKind") != claim["factorKind"]:
        return _fail(claim, "challenge factorKind mismatch")
    if challenge.get("nonce") != claim["challengeNonce"]:
        return _fail(claim, "challenge nonce mismatch")
    if now > int(challenge.get("expiresAt", 0)):
        return _fail(claim, "challenge expired")
    if claim["challengeNonce"] in seen_nonces:
        return _fail(claim, "nonce already consumed (replay)")

    # G11 gov gate — Council-gated proofs raise at R0 (ADR-2605260000).
    if claim["proofKind"] in GATED_PROOFS and not getattr(verifier, "allow_gated", False):
        raise GatedError(
            f"proofKind {claim['proofKind']!r} (gov L2) is Council-gated; "
            f"R0 shomei_gov_attest cell .solve() raises (ADR-2605260000 R1 activation required)"
        )

    proof_ok = verifier.verify_proof(claim["proofKind"], claim, proof_material)
    if not proof_ok:
        return _fail(claim, "proof verification failed")

    sig_ok = verifier.verify_subject_sig(claim)
    if not sig_ok:
        return _fail(claim, "subject signature invalid")

    seen_nonces.add(claim["challengeNonce"])  # single-use consumption
    return {
        "verified": True,
        "factorKind": claim["factorKind"],
        "factorClass": claim["factorClass"],
        "reason": "ok",
    }


def _fail(claim: dict, reason: str) -> dict:
    return {
        "verified": False,
        "factorKind": claim.get("factorKind"),
        "factorClass": claim.get("factorClass"),
        "reason": reason,
    }
