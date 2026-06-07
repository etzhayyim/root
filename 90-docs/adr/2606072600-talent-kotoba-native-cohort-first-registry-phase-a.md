---
id: adr-2606072600-talent-kotoba-native-registry
title: "ADR-2606072600: talent — kotoba-native cohort-first talent registry (Indeed/LinkedIn-Recruiter inversion); remediation Phase A"
status: proposed
doc_type: adr
topic: talent-kotoba-native
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/talent
depends_on:
  - 2606071800   # substrate remediation wave (Phase A)
  - 2606072000   # business-manager (Phase A recipe)
  - 2605181100   # encrypted envelope / Signal
related:
  - 2606072200   # yotei
  - 2606072400   # organizer
supersedes: []
superseded_by: []
---

# ADR-2606072600: talent — kotoba-native cohort-first talent registry (Indeed/LinkedIn-Recruiter inversion); remediation Phase A

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

`talent` (the Indeed/LinkedIn-Recruiter equivalent, PII Tier 3) existed only as a **legacy T1
MCP-Compose scaffold** persisting `TalentCohort`/`TalentProfile` the pre-kotoba way (RisingWave-
via-Hyperdrive). Phase-A category of the remediation wave (ADR-2606071800).

Its design is already the charter-clean inversion of a recruiter DB (cohort-first, Signal E2E,
self-sovereign, GDPR Art 17, no commercial candidate DB). The conversion's job is to make those
rules **structural in code on the kotoba Datom log**, not policy text in a manifest.

# Decision

Rewrite `talent` as a **kotoba-EAVT-native cohort-first registry**, mirroring the Phase-A recipe.
R0→R1. The four privacy rules become code-level invariants:

| Recruiter-DB term | talent invariant | gate |
|---|---|---|
| scrape/buy candidate resumes (LinkedIn/Indeed/lists) | **self-sovereign only**: a profile write requires caller DID == subject DID; third-party / prohibited-source ingest refused | G1 self-sovereign |
| individual profiles publicly searchable | **cohort-first + k-anonymity**: default read = cohort aggregate; a cohort below k is suppressed; individual read is consent-gated | G2 cohort-first-k-anon |
| plaintext PII columns | identifying fields (fullName/email/phone/address/dateOfBirth/governmentId) MUST be `signal:v1:{ciphertext}`; a plaintext write is refused | G3 signal-e2e |
| soft delete / retention | **GDPR Art 17 hard cascade delete** via forgetSelf; no soft-delete / `_alive` flag exists | G4 hard-delete |
| mutable rows in a vendor DB | append-then-hard-delete kotoba Datoms; no RisingWave/SQL | G5 kotoba-eavt-native |

**Preserved semantics:** ISCO-08 cohort keys (`cohort:{isco}:{country}`), self path
(`profile:{subjectDid-hash}`), enrichment allowed only from public-consent sources (OrcID,
GitHub public, public credential registries); recruit consumes cohort stats only.

**Deliverables:** `manifest.edn`, `lex/{talentProfile,talentCohort}.edn`, `kotoba/schema.edn`,
`py/agent.py` (self-sovereign write guard, plaintext-PII rejection, k-anonymity cohort stats,
hard-delete forgetSelf, prohibited-source refusal), `py/test_agent.py`, `DEPRECATED-jsonld.md` +
CLAUDE.md banner. talent has no code on the substrate frozen-allowlist (manifest-only) → zero new
debt.

# Consequences

- Makes the PII-Tier-3 rules structural (a third-party or plaintext or sub-k read cannot be
  expressed) rather than manifest policy; removes a substrate-boundary violation.
- Fourth proof of the Phase-A recipe.

# Alternatives Considered

1. **Keep the JSON-LD scaffold** — rejected: forbidden RisingWave path; rules remain mere text.
2. **Allow licensed commercial candidate DB ingest** — rejected: prohibited dataSources are a
   constitutional gate (no third-party subject registration), license notwithstanding.

# References

- ADR-2606071800 — substrate remediation wave (Phase A)
- ADR-2606072000 — business-manager (Phase A recipe)
- ADR-2605181100 — encrypted envelope / Signal
