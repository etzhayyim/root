"""aggregate.py — 証明 (shomei) personhoodCredential aggregation. ADR-2606072100.

Rolls a DID's VERIFIED, ACTIVE identityClaims into an Identity Assurance Level + proof-of-personhood
+ a W3C-Verifiable-Credential-shaped record. G3: no PII (kinds + counts + DID hash only). G8: this
is identity-assurance, NEVER a social-credit / worth / reputation score.

Stdlib only.
"""
from __future__ import annotations

import base64
import hashlib

from factors import COVENANT_FACTORS, FACTOR_CLASS, assurance_level, proof_of_personhood

W3C_VC_CONTEXT = [
    "https://www.w3.org/2018/credentials/v1",
    "https://etzhayyim.com/ns/shomei/v1",
]
COUNCIL_ATTESTOR_DID = "did:web:etzhayyim.com:council:attestor"  # IAL-4 issuer (gated)


def did_hash(did: str) -> str:
    digest = hashlib.blake2b(did.encode("utf-8"), digest_size=32).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def aggregate(
    subject_did: str,
    active_verified_factors: set[str],
    *,
    issued_at: int,
    expiration_date: int | None = None,
) -> dict:
    """Build a personhoodCredential from the SET of distinct verified+active factorKinds."""
    factors = sorted(f for f in active_verified_factors if f in FACTOR_CLASS)
    classes = {FACTOR_CLASS[f] for f in factors}
    count = len(factors)
    level = assurance_level(classes, count)
    pop = proof_of_personhood(level, len(classes))
    issuer = subject_did if level <= 3 else COUNCIL_ATTESTOR_DID

    cred = {
        "subjectDidHash": did_hash(subject_did),
        "assuranceLevel": level,
        "verifiedFactors": factors,
        "distinctClasses": len(classes),
        "factorCount": count,
        "proofOfPersonhood": pop,
        "issuer": issuer,
        "issuanceDate": int(issued_at),
    }
    if expiration_date is not None:
        cred["expirationDate"] = int(expiration_date)
    return cred


def to_w3c_vc(subject_did: str, cred: dict) -> dict:
    """Render the credential as a W3C VC data-model JSON-LD object for presentation (G3: no PII)."""
    subject = {
        "id": subject_did,
        "assuranceLevel": cred["assuranceLevel"],
        "verifiedFactors": cred["verifiedFactors"],
        "distinctClasses": cred["distinctClasses"],
        "factorCount": cred["factorCount"],
        "proofOfPersonhood": cred["proofOfPersonhood"],
    }
    vc = {
        "@context": W3C_VC_CONTEXT,
        "type": ["VerifiableCredential", "EtzhayyimPersonhoodCredential"],
        "issuer": cred["issuer"],
        "issuanceDate": cred["issuanceDate"],
        "credentialSubject": subject,
    }
    if "expirationDate" in cred:
        vc["expirationDate"] = cred["expirationDate"]
    return vc


def assurance_label(level: int) -> str:
    return {
        0: "did-only",
        1: "self-attested",
        2: "multi-factor",
        3: "covenant-bound",
        4: "government-verified",
    }[level]


def is_covenant_bound(active_verified_factors: set[str]) -> bool:
    return bool(active_verified_factors & COVENANT_FACTORS)
