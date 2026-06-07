"""revoke.py — 証明 (shomei) append-only binding revocation. ADR-2606072100.

G5 consent-bound + revocable: only the subject unlinks their own factor. G10 + Tier-0 永久記憶:
a revocation is an APPEND-ONLY retraction Datom, NEVER a deletion — the original claim's history
is permanently retained (no right to erasure). Aggregation recomputes assurance EXCLUDING revoked
claims; the as-of record that the binding once existed never disappears.

Stdlib only.
"""
from __future__ import annotations

from factors import FACTOR_KINDS, REVOCATION_REASONS


def validate_revocation(rev: dict, claim: dict | None = None) -> dict:
    """Structural gate for a bindingRevocation. Raises ValueError on violation."""
    required = ("subjectDid", "claimRef", "factorKind", "reason", "revokedAt", "subjectSig")
    missing = [f for f in required if f not in rev]
    if missing:
        raise ValueError(f"bindingRevocation missing required field(s): {missing}")
    if not isinstance(rev["subjectDid"], str) or not rev["subjectDid"].startswith("did:"):
        raise ValueError("revocation subjectDid must be a DID")
    if rev["factorKind"] not in FACTOR_KINDS:
        raise ValueError(f"unknown factorKind: {rev['factorKind']!r}")
    if rev["reason"] not in REVOCATION_REASONS:
        raise ValueError(f"unknown revocation reason: {rev['reason']!r}")
    if not isinstance(rev["revokedAt"], int):
        raise ValueError("revokedAt must be an integer unix timestamp")
    if not isinstance(rev["subjectSig"], str) or not rev["subjectSig"]:
        raise ValueError("G7: subjectSig (subject-signed) is mandatory on a revocation")
    # G5 — only the binding's owner may revoke it.
    if claim is not None and claim.get("subjectDid") != rev["subjectDid"]:
        raise ValueError(
            "G5: revocation subjectDid must equal the claim's subjectDid (only the owner revokes)"
        )
    return rev


def active_verified_factors(claims: list[dict], revocations: list[dict]) -> set[str]:
    """The set of factorKinds with ≥1 verified, NON-revoked claim (append-only as-of semantics).

    A claim is inactive iff a revocation references it by claimRef (or, lacking a claimRef link,
    matches subjectDid+factorKind with revokedAt ≥ the claim's issuedAt).
    """
    revoked_refs = {r["claimRef"] for r in revocations if r.get("claimRef")}
    revoked_kinds = {
        (r["subjectDid"], r["factorKind"], int(r["revokedAt"]))
        for r in revocations
    }
    out: set[str] = set()
    for c in claims:
        if not c.get("verified"):
            continue
        ref = c.get("cid") or c.get("claimRef")
        if ref is not None and ref in revoked_refs:
            continue
        if any(
            sd == c["subjectDid"] and fk == c["factorKind"] and ra >= int(c["issuedAt"])
            for (sd, fk, ra) in revoked_kinds
        ):
            continue
        out.add(c["factorKind"])
    return out
