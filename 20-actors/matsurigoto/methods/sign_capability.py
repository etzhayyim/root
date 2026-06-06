#!/usr/bin/env python3
"""matsurigoto 政 — R1.C: the sign / authority layer (verify-only, NO server key).

ADR-2606062300 + ADR-2605231525. R0 artifacts are unsigned by construction (G1). This layer
attaches a signature WITHOUT matsurigoto ever holding a private key: the signature is produced
EXTERNALLY by the governing organ —

  principal A (:sovereign-governance) : the Council 5-of-7 Safe / 1 SBT=1 vote, an etzhayyim
                                        constitutional organ (did:web:etzhayyim.com:council:*).
  principal B (:supplied-to-state)    : the adopting state's OWN key (its ICAO-PKD CSCA/DS for
                                        passports, its tax-authority cert, etc.) — NOT an
                                        etzhayyim did.

matsurigoto only (a) emits the canonical payload to be signed and (b) ATTACHES a signature the
caller brings back, after checking the signer is a legitimate authority for the principal. It
NEVER mints a signature. This mirrors okaimono's member-principal checkout (server-sig refused).

  SIGNER_HELD_PRIVATE_KEY = False  — there is no key here; `sign_server_side` always RAISES.

HONEST R1: this verifies the STRUCTURE (legitimate signer for the principal + payload integrity
via sha256). Real ed25519 / Safe-threshold cryptographic verification is R2 (needs the live key
infra + Council ratification). stdlib only.
"""
from __future__ import annotations

import hashlib
import json

SIGNER_HELD_PRIVATE_KEY = False  # G1 / ADR-2605231525 — matsurigoto holds no private key

_ETZHAYYIM_COUNCIL_PREFIX = "did:web:etzhayyim.com:council"


def canonical_payload(obj) -> str:
    """Deterministic bytes-to-be-signed for an artifact or datom batch (sha256 over canonical JSON)."""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _payload(artifact: dict) -> str:
    """Hash the SUBSTANTIVE content only — excluding `proof` and the `status` lifecycle marker
    (which flips unsigned→signed) so the digest is stable across signing."""
    return canonical_payload({k: v for k, v in artifact.items() if k not in ("proof", "status")})


def _legitimate_signer(signer_did: str, authority_mode: str) -> bool:
    """principal A must be signed by an etzhayyim Council organ; principal B by a NON-etzhayyim
    (the adopting state's own) did — etzhayyim never holds the state's key."""
    is_council = signer_did.startswith(_ETZHAYYIM_COUNCIL_PREFIX)
    if authority_mode == ":sovereign-governance":
        return is_council
    if authority_mode == ":supplied-to-state":
        return not signer_did.startswith("did:web:etzhayyim.com")
    return False


def sign_server_side(*_args, **_kwargs):
    """STRUCTURAL no-server-key: there is no path for matsurigoto to sign. Always raises
    (the okaimono `authorize_payment` server-sig-refused pattern, ADR-2605231525)."""
    raise RuntimeError(
        "no-server-key (ADR-2605231525): matsurigoto holds no signing key and signs nothing. "
        "The Council Safe (principal A) or the adopting state (principal B) signs externally; "
        "use attach_external_proof() to attach their signature."
    )


def attach_external_proof(artifact: dict, *, signer_did: str, authority_mode: str,
                          signature: str, signed_at: str) -> dict:
    """Attach an EXTERNALLY-produced signature to an unsigned artifact. Pure; returns a NEW dict.

    Raises if the artifact is already signed (G1: a module artifact must arrive unsigned), the
    signer is illegitimate for the principal, or the signature is empty.
    """
    if artifact.get("proof") is not None:
        raise ValueError("artifact already signed — a module artifact must arrive unsigned (G1)")
    if not signature:
        raise ValueError("no external signature supplied — matsurigoto mints none (no-server-key)")
    if not _legitimate_signer(signer_did, authority_mode):
        raise ValueError(f"illegitimate signer {signer_did!r} for {authority_mode}")
    out = dict(artifact)
    out["proof"] = {
        "signer_did": signer_did,
        "authority_mode": authority_mode,
        "signature": signature,
        "signed_at": signed_at,
        "payload_sha256": _payload(artifact),
    }
    out["status"] = out["status"].replace("unsigned", "signed")
    out["server_held_authority"] = False  # unchanged — still no operator key
    return out


def verify_proof(signed_artifact: dict) -> bool:
    """Structural verification: a proof is present, by a legitimate signer, over the matching
    payload. (Cryptographic ed25519/Safe-threshold check is R2.)"""
    proof = signed_artifact.get("proof")
    if not proof or not proof.get("signature"):
        return False
    if not _legitimate_signer(proof["signer_did"], proof["authority_mode"]):
        return False
    return proof.get("payload_sha256") == _payload(signed_artifact)


if __name__ == "__main__":
    from modules import credential_issue as P  # type: ignore
    doc = P.issue_passport("L898902C3", "UTO", "UTO", "ERIKSSON", "ANNA", "740812", "F",
                           "120415", "did:x")["document"]
    signed = attach_external_proof(doc, signer_did="did:web:etzhayyim.com:council:safe",
                                   authority_mode=":sovereign-governance",
                                   signature="0xCOUNCIL_SAFE_SIG", signed_at="2026-06-06T00:00:00Z")
    print("verify:", verify_proof(signed), "| status:", signed["status"])
