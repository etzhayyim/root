---
id: adr-2606072400-organizer-kotoba-native-file-commons
title: "ADR-2606072400: organizer — kotoba-native auto-organize file commons (Google Drive inversion); remediation Phase A"
status: proposed
doc_type: adr
topic: organizer-kotoba-native
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/organizer
depends_on:
  - 2606071800   # substrate remediation wave (Phase A)
  - 2606072000   # business-manager (Phase A recipe)
  - 2605181100   # encrypted envelope
related:
  - 2606072200   # yotei (sibling Phase-A conversion)
supersedes: []
superseded_by: []
---

# ADR-2606072400: organizer — kotoba-native auto-organize file commons (Google Drive inversion); remediation Phase A

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

`organizer` (the Google Drive + auto-organize equivalent) existed only as a **legacy single-
Worker scaffold** persisting item/classification/tag/collection records the pre-kotoba way
(RisingWave-via-Hyperdrive). It is the Phase-A category of the substrate remediation wave
(ADR-2606071800): rewrite kotoba-native, cheap, no data migration.

A faithful Drive clone is a charter conflict: cloud-drive economics are **paid storage tiers**
plus **mining file content** (for search ads / model training). The underlying need — store my
files and have them auto-organized — is fine; the inversion drops the tiers and the mining and
makes storage **content-addressed + per-user-vault-isolated + un-mined**.

# Decision

Rewrite `organizer` as a **kotoba-EAVT-native auto-organize file commons**, mirroring the
`business-manager`/`yotei` recipe. R0→R1. Scope this conversion to the **Drive core** (item
ingest → dedup → classify → auto-organize into collections); the separate subscription-discovery
pipeline (mailer → organizer → kaiyaku) is retained as a follow-up and not part of this core.

**Charter-clean inversions / invariants (gates, see manifest.edn):**

| Google Drive term | organizer dual | gate |
|---|---|---|
| paid storage tiers | **free**, no tiers/subscription (no external inflow §1.3) | G1 no-tier |
| mine file content for search-ads / training | **no content mining**: classification emits category/labels for the OWNER only; never a profile, ad signal, or cross-vault aggregate | G2 no-mining |
| one big multi-tenant store | **per-user vault DID isolation**: an item belongs to exactly one vault; cross-vault read is refused | G3 vault-isolation |
| duplicate uploads stored N times | **content-addressed dedup**: identical Blake3 content → one item (no redundant storage, no re-upload leak) | G4 content-addressed |
| plaintext blobs at rest | blob via `com.etzhayyim.encrypted.*` envelope | G5 encrypted-at-rest |
| platform-held keys | member-signed mutations; server holds no key | G6 no-server-key |
| vendor LLM classifier | Murakumo-only classification | G7 murakumo-only |

**Preserved domain semantics:** item (blob ref, filename, content-type, size, blake3, vault);
classification (category, subcategory, labels, confidence, model); collection + organize rule
(condition → action auto-organize).

**Deliverables:** `manifest.edn`, `lex/{item,classification,collection}.edn`,
`kotoba/schema.edn`, `py/agent.py` (content-addressed dedup, deterministic+Murakumo
classification, organize-rule → collection assignment, vault-isolation guard), `py/test_agent.py`,
`DEPRECATED-jsonld.md` + CLAUDE.md banner. organizer has no code files on the substrate frozen-
allowlist (manifest-only), so this adds zero new debt.

# Consequences

- Closes the Drive slot charter-clean (free, un-mined, vault-isolated, dedup) and removes a
  substrate-boundary violation.
- Third proof of the Phase-A recipe; net-new is the dedup + classify + organize-rule logic.

# Alternatives Considered

1. **Keep the legacy scaffold** — rejected: forbidden RisingWave path + no inversion stance.
2. **Drive-faithful with a free tier + content search** — rejected: content search over a
   multi-tenant store is the mining the inversion removes (G2/G3).
3. **Include the subscription-discovery pipeline now** — deferred: it is a distinct mailer→kaiyaku
   flow; folding it in would bloat this core conversion.

# References

- ADR-2606071800 — substrate remediation wave (Phase A)
- ADR-2606072000 — business-manager (Phase A recipe)
- ADR-2605181100 — encrypted envelope (blobs at rest)
