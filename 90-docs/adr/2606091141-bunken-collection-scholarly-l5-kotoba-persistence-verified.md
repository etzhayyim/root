---
id: adr-2606091141-bunken-collection-scholarly-l5-kotoba-persistence-verified
title: "ADR-2606091141: bunken CDX collection pipeline, scholarly actors → L5, and kotoba persistence/query verified live"
status: approved
doc_type: adr
topic: knowledge-ingestion-substrate
authoritative: true
last_verified: 2026-06-09
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Closes the world-papers ingest gap (bunken) + raises scholarly-API fidelity to L5 + confirms the kotoba persistence/query substrate works end-to-end on real hardware."
authoritative_for:
  - 60-apps/etzhayyim-project-bunken
  - 20-actors/{arxiv_api,crossref,doi_system,ietf_rfcs,ncbi,orcid,pubmed,w3c_specs}-compat
  - kotoba persistence/query verification (40-engine/kotoba submodule)
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related: []
supersedes: []
superseded_by: []
---

# ADR-2606091141: bunken CDX collection pipeline, scholarly actors → L5, and kotoba persistence/query verified live

**Status**: approved
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

# Context

A status review of the "fetch world papers → kotoba Datomic → IPFS" stack found three layers at uneven maturity:

1. **World-paper ingestion (bunken 文献書誌)** — the design (Common Crawl CDX discovery → enrich → multi-DID → SAME_AS) existed, plus a TS app skeleton (`registerRecord`/`getRecord`/`search`/`stats`), but the **collection pipeline itself was unimplemented**. The corpus could store records but had no way to actually discover/ingest them at scale.
2. **Scholarly clean-room actors** — 8 of the 1000-actor corpus (arxiv_api, crossref, doi_system, ietf_rfcs, ncbi, orcid, pubmed, w3c_specs) were built to L4 but their `schema/*.kotoba` were **generic templates** (`Work/Author/Citation/Standard/Record/Subject`), not their real APIs — exactly the mismatch the L5 gate is designed to reject.
3. **kotoba persistence/query** — claimed to be the canonical Datomic-over-IPFS substrate, but not freshly confirmed end-to-end.

# Decision

## 1. bunken CDX collection pipeline (60-apps/etzhayyim-project-bunken/rw-free)

Implemented `src/collection.ts` — the five-stage pipeline from the bunken CLAUDE.md:

- `collectFromCdx` → one `BunkenCollectionJob` per scheme (CDX url-pattern; `isbn` delegated to isbn.etzhayyim.com).
- `fetchCdxBatch` → process one pending job: CDX fetch → `extractIdFromUrl` (9-scheme regex: NDL/CiNii/LoC/WorldCat/VIAF/DOI/ARK) → dedup → MERGE discovered-only nodes; resumable via `page` cursor.
- `enrichBatch` → Murakumo metadata extraction over discovered-only records + `classifyEra(year)` auto-classification.
- `registerDids` → path-based DID registration for enriched records (idempotent).
- `linkSameAs` → immutable `SAME_AS` edges between same-title/author records of **differing** scheme.

All network + Murakumo LLM I/O is injected via `CollectionDeps` so the parse/classify logic is unit-testable offline; **no external LLM is wired by default** (Murakumo-only rule preserved). **23/23 vitest pass** (9 existing + 14 new); `tsc --noEmit` clean.

## 2. Scholarly clean-room actors → L5 (Verified)

Each of the 8 actors' `schema/*.kotoba` was **remodeled to faithful real-API resources**, reconciled field-for-field against the platform's OFFICIAL public docs (WebFetch provenance), e.g. crossref `Work/Reference/Funder/...` + 30-value `WorkType`; ietf_rfcs verified against `rfc-index.xsd` (status 9 / stream 6 enums); pubmed traced to the PubmedArticle DTD; ncbi to Entrez E-utilities. Manifests + `cleanroom-actors.index.json` tier L4→L5; `cleanroom-l5-verification.json` +8 provenance entries (**49→57 L5**). `verify_cleanroom_system.py`: **PASS (0 errors / 0 warnings, 1000 actors coherent)**. Honesty gate held — only doc-confirmed fields enter `verifiedFields`; unconfirmable enums recorded as `gaps`, never fabricated (e.g. PubMed `PublicationType` is DTD `#PCDATA` → kept `json`, no enum asserted; W3C API returns full status strings, not the WD/CR/REC abbreviations).

Landed via **PR #1491 (merged 2026-06-09, mergeCommit `bf28f7e3`)**.

## 3. kotoba persistence/query — verified live on real hardware

- **Library**: `kotoba-datomic` **142 tests pass** (transact / `unique` upsert / schema+valueType enforcement / content-addressed tx-CID / Datalog `q`); `kotoba-ipfs` **27 tests** (own IPFS node: block+pin repo persistence, two-node exchange, GC-respects-pins, IPNS survives reopen); durable set — `crash_recovery_without_journal_replay_via_commit_dag`, `survives_reopen`, `tiered_over_fs_is_durable`, `shelf_persistence_survives_restart`; `ipfs_e2e` example (content-addressed persist → empty-node reconstruct → SPARQL BGP/ASK/DESCRIBE/CONSTRUCT/SERVICE + CACAO).
- **Live binary** (built from source with the SovereignCrypto re-genesis fix): `serve` → ingest → SELECT/ASK/DESCRIBE/CONSTRUCT → `commit` (durable seal to ProllyTrees + Kubo blocks) → **kill** → restart → server B boot log `warm: resident db_before cache seeded graph=kotobase-kg-v1 head=<server-A-commit-CID>` — **the committed graph head survived the restart and was reloaded** from the disk-persistent IPNS head + Kubo blocks.

# Consequences

- **Positive** — bunken can now actually discover/ingest world bibliographic records (the corpus gains an inflow path); 8 scholarly APIs are L5-faithful; the kotoba Datomic-over-IPFS persistence/query substrate is confirmed working end-to-end (write → durable content-addressed commit → process restart → committed head reloaded).
- **kotoba has its own IPFS** — `KotobaIpfsNode` (Kubo-compatible: block addressing, pin state, repo persistence, peer block exchange, dht/provide, IPNS) is self-contained; Kubo is an optional cold-tier backend, not a dependency.
- **Limitations recorded** (see deps.toml):
  - The installed/brew `kotoba` (`d6815…`, behind upstream `d3086…`) **bricks on startup** with a Keychain identity + Kubo (stale SovereignCrypto key-block pointer); the upstream re-genesis fix resolves it — **brew tap needs a refresh**.
  - Durable cross-restart requires a **persisted operator identity** (`kotoba init`) + the **Kubo cold tier** (`KOTOBA_IPFS=off` keeps blocks in memory = not durable).
  - The `kotoba sparql` CLI subcommand resolves the default graph differently than `kotoba demo`'s internal `sparql_req`, returning empty against the wrong graph — a **client-side quirk**, not a substrate fault (file upstream).

# Alternatives Considered

- **Promote scholarly actors via the generic template (no remodel).** Rejected — that is precisely what the L5 gate rejects (real-API fidelity, not just CRUD completeness).
- **Wire a real LLM into bunken enrich for the demo.** Rejected — violates the Murakumo-only rule; instead enrich I/O is injected so the pipeline is testable offline and Murakumo is wired only in deployment.
- **Demonstrate durability with `KOTOBA_IPFS=off`.** Rejected — the memory cold tier is not durable across restart; the real Kubo cold tier is the production-representative path.

# References

- PR #1491 (merged) — bunken collection + 8 scholarly L5.
- `60-apps/etzhayyim-project-bunken/rw-free/src/collection.ts` + `test/collection.test.ts`.
- `00-contracts/schemas/cleanroom-l5-verification.json` (49→57), `cleanroom-actors.index.json`.
- `70-tools/verify_cleanroom_system.py` — PASS 0/0.
- kotoba: `crates/kotoba-datomic`, `crates/kotoba-ipfs`, `crates/kotoba-graph/examples/ipfs_e2e.rs`, `crates/kotoba-kse/src/sovereign_key.rs` (re-genesis fix).
- ADR-2605262130 (kotoba storage substrate), ADR-2605312345 (Datom first-class canonical state).
