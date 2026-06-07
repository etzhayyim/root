#!/usr/bin/env python3
"""talent — kotoba-native cohort-first talent registry langgraph actor (kotoba WASM cell).

ADR-2606072600 (Phase A of the substrate remediation wave, ADR-2606071800). Replaces the legacy
RisingWave-backed registry with self-sovereign, hard-deletable profiles + k-anonymous cohort
stats on the kotoba Datom log. Handlers over one kotoba EAVT graph:

  register_self     self-sovereign write guard (G1) + plaintext-PII rejection (G3) → cohort assign
  ingest_external   refuse prohibited commercial sources (G1)
  cohort_stats      k-anonymity aggregate (G2) — the only thing recruit may read
  forget_self       GDPR Art 17 hard cascade delete (G4) — no soft delete

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - self-sovereign (G1): a profile write requires caller DID == subject DID; a third-party or
    prohibited-source write is refused (no third-party registration path exists).
  - signal-e2e (G3): identifying fields must be `signal:v1:{ciphertext}`; a plaintext write is
    refused — the function cannot persist plaintext PII.
  - k-anonymity (G2): a cohort below k members is suppressed; there is no individual public read.
  - hard-delete (G4): forget_self removes the Datom; there is no `_alive`/soft-delete flag to set.

Murakumo-only for any normalization (G7). R1 computes registrations + cohort stats; on-chain
anchoring is downstream.
"""
from __future__ import annotations

import hashlib

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# Identifying fields that MUST be Signal-E2E ciphertext (G3).
IDENTIFYING_FIELDS = ("fullName", "email", "phone", "address", "dateOfBirth", "governmentId")
ENC_PREFIX = "signal:v1:"

ALLOWED_ENRICHMENT = {"orcid", "github-public", "public-credential-registry"}
PROHIBITED_SOURCES = {"linkedin", "indeed", "glassdoor", "purchased-list", "scraped-db"}

K_ANONYMITY = 5  # a cohort below this many members is suppressed (G2)


def is_encrypted(value: str) -> bool:
    """True iff a field value is Signal-E2E ciphertext (G3)."""
    return isinstance(value, str) and value.startswith(ENC_PREFIX)


def subject_hash(subject_did: str) -> str:
    """Deterministic hash of the subject DID — the self path profile:{hash}."""
    return hashlib.sha256(subject_did.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# register_self (G1 self-sovereign, G3 signal-e2e)
# --------------------------------------------------------------------------- #
def register_self(caller_did: str, subject_did: str, profile: dict) -> dict:
    """Register a SELF-SOVEREIGN profile. Refuses unless caller == subject (G1). Refuses any
    plaintext identifying field (G3). Refuses a prohibited enrichment source (G1). Returns a
    registered profile keyed by the subject-DID hash."""
    if caller_did != subject_did:
        return {"state": "refused", "reason": "third-party registration forbidden — caller must be the subject (G1)"}
    for f in IDENTIFYING_FIELDS:
        v = profile.get(f)
        if v and not is_encrypted(v):
            return {"state": "refused", "reason": f"identifying field {f!r} must be signal:v1: ciphertext (G3)"}
    src = profile.get("enrichmentSource")
    if src and src not in ALLOWED_ENRICHMENT:
        return {"state": "refused", "reason": f"enrichment source {src!r} not in public-consent allowlist (G1)"}
    h = subject_hash(subject_did)
    return {
        "state": "registered",
        "profile": {**profile, "subjectDidHash": h, "registeredBy": caller_did},
    }


def ingest_external(source: str) -> dict:
    """Any attempt to ingest from a commercial/scraped candidate source is refused (G1) — there
    is no code path that writes a profile the subject did not register themselves."""
    if source in PROHIBITED_SOURCES:
        return {"state": "refused", "reason": f"prohibited candidate source {source!r} (G1) — license notwithstanding"}
    if source not in ALLOWED_ENRICHMENT:
        return {"state": "refused", "reason": f"source {source!r} not in public-consent allowlist (G1)"}
    return {"state": "allowed", "source": source, "note": "enrichment only attaches to a self-registered profile"}


# --------------------------------------------------------------------------- #
# cohort_stats (G2 k-anonymity) — the only read recruit may consume
# --------------------------------------------------------------------------- #
def cohort_stats(isco: str, country: str, profiles: list, k: int = K_ANONYMITY) -> dict:
    """Aggregate a cohort (ISCO × country). If the cohort has fewer than k members it is
    SUPPRESSED (G2) — no count, no individuals. Otherwise returns size + top non-identifying
    skills. There is no individual-profile field in the output."""
    members = [p for p in profiles if p.get("isco") == isco and p.get("country") == country]
    n = len(members)
    if n < k:
        return {"suppressed": True, "reason": f"cohort below k={k} (G2 k-anonymity)", "count": None}
    skill_counts: dict[str, int] = {}
    for p in members:
        for s in p.get("skills", []):
            skill_counts[s] = skill_counts.get(s, 0) + 1
    top = sorted(skill_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return {"suppressed": False, "count": n, "topSkills": [s for s, _ in top],
            "cohortDid": f"did:web:talent.etzhayyim.com:cohort:{isco}:{country}"}


# --------------------------------------------------------------------------- #
# forget_self (G4 GDPR Art 17 hard delete)
# --------------------------------------------------------------------------- #
def forget_self(caller_did: str, subject_did: str, store: list) -> dict:
    """GDPR Art 17 cascade HARD delete (G4). Refuses unless caller == subject. Removes the
    profile Datom entirely — it does NOT set a soft-delete flag (there is none). Returns the
    new store and the count removed."""
    if caller_did != subject_did:
        return {"state": "refused", "reason": "only the subject may forget their own profile (G1/G4)"}
    h = subject_hash(subject_did)
    kept = [p for p in store if p.get("subjectDidHash") != h]
    return {"state": "forgotten", "store": kept, "hardDeleted": len(store) - len(kept)}
