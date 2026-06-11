---
id: adr-2606072000-business-manager-kotoba-native-erp
title: "ADR-2606072000: business-manager — kotoba-native internal ERP (Salesforce/SAP inversion); remediation Phase A"
status: proposed
doc_type: adr
topic: business-manager-kotoba-native
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/business-manager
depends_on:
  - 2606071800   # substrate remediation wave (this is its Phase A worked conversion)
  - 2606071400   # omise kotoba-native (template)
  - 2605262130   # kotoba storage substrate
related:
  - 2605262900   # toritate (accounting + audit, on-chain) — business-manager feeds it
supersedes: []
superseded_by: []
---

# ADR-2606072000: business-manager — kotoba-native internal ERP (Salesforce/SAP inversion); remediation Phase A

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

`business-manager` (the Salesforce/SAP-ERP equivalent in the app-coverage audit) existed only
as a **legacy T1 MCP-Compose scaffold**: `actor-manifest.jsonld` + `CLAUDE.md`, with its read/
write path expressed as **Cypher `MATCH`/`CREATE` over RisingWave-via-Hyperdrive** (the
`graph.query`/`graph.write` pipeline functions). That is a substrate-boundary violation
(ADR-2605262130: kotoba EAVT only, no RisingWave/SQL as canonical) and it is exactly the
**Phase A** category of the remediation wave (ADR-2606071800): a manifest-only legacy actor to
rewrite kotoba-native, cheap, no data migration.

A faithful Salesforce/SAP clone would also be a **multi-tenant external SaaS** — billed seats,
external customers' books — which conflicts with the charter (no external `subscription`/
`purchase` inflow). So we take the same inversion stance used elsewhere.

# Decision

Rewrite `business-manager` as a **kotoba-EAVT-native internal ERP** for etzhayyim's own
producing-actor operations (mitsuho, yakushi, makura, … run real operations that need a general
ledger, purchase orders, and budgets), with **double-entry bookkeeping on the kotoba Datom log**
that `toritate 執帳` (ADR-2605262900) audits. Mirrors the `okaimono`/`omise` structure
(manifest.edn + lex + kotoba/schema.edn + py agent + tests). R0→R1.

**Charter-clean inversions / invariants (gates, see manifest.edn):**

| Salesforce/SAP term | business-manager dual | gate |
|---|---|---|
| multi-tenant external SaaS, billed seats | **internal-only** ledger for etzhayyim producing-actors; no external tenant; no subscription | G1 internal-only |
| mutable DB rows, admin override | **append-only double-entry Datoms**; every entry balances (Σdebit = Σcredit) by construction | G2 double-entry-balanced |
| RisingWave/Cypher graph store | **kotoba EAVT Datoms**; no RW/SQL/Cypher (corrects the legacy manifest) | G3 kotoba-eavt-native |
| platform-held admin credentials | **member-signed** postings; server holds no key | G4 no-server-key |
| HR PII in plaintext rows | employee identifying fields → `com.etzhayyim.encrypted.*` | G5 pii-encrypted |
| opaque internal approvals | approval thresholds explicit (journal >1M JPY, PO >5M JPY); on-chain audit trail for `toritate` | G6 approval-thresholds + G7 audit-trail |
| vendor LLM copilots | Murakumo-only narration | G8 murakumo-only |

**Preserved domain semantics** (from the legacy manifest): JP fiscal year (Apr 1 – Mar 31);
journal entry (debit/credit/amount/currency/fiscalYear/approved); purchase order
(vendor/amount/items/approved); invoice; employee; budget allocation; approval thresholds
(journal >1,000,000 JPY, PO >5,000,000 JPY → `approval-required`).

**Concrete deliverables:** `manifest.edn`, `lex/{journalEntry,purchaseOrder}.edn`,
`kotoba/schema.edn`, `py/agent.py` (double-entry balance validation, fiscal-year derivation,
approval-threshold routing, member-signed posting), `py/test_agent.py` (tested invariants), and
a `DEPRECATED-jsonld.md` marker. The legacy `actor-manifest.jsonld` is retained one R-cycle then
removed. **business-manager has no code files on the substrate frozen-allowlist** (it was
manifest-only), so this conversion adds zero new debt and establishes the Phase-A recipe.

# Consequences

- Removes a substrate-boundary violation and gives the Salesforce/ERP slot a charter-clean,
  on-chain, double-entry implementation that `toritate` can audit.
- Establishes the **Phase-A conversion recipe** (legacy jsonld → kotoba-native, mirror omise)
  for the remaining manifest-only legacy actors (yotei, organizer, talent, …).
- Overlap with `toritate` is resolved by role split: business-manager = operational ERP (the
  books); toritate = audit + attestation over those books.

# Alternatives Considered

1. **Keep the JSON-LD scaffold** — rejected: it encodes the forbidden RisingWave/Cypher path; a
   Phase-A actor is precisely what the remediation wave converts.
2. **Fold into `toritate`** — rejected: operational bookkeeping (posting entries, POs, budgets)
   and independent audit are different roles; merging removes the separation that makes the
   audit meaningful.
3. **Multi-tenant external ERP SaaS** — rejected: external billed tenancy is value inflow the
   charter forbids (§1.3).

# References

- ADR-2606071800 — substrate remediation wave (this is its Phase A)
- ADR-2606071400 — omise kotoba-native (conversion template)
- ADR-2605262900 — toritate (accounting + audit, on-chain)
- ADR-2605262130 — kotoba storage substrate
