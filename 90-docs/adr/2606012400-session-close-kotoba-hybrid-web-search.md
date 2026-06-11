---
id: adr-2606012400-session-close-kotoba-hybrid-web-search
title: "ADR-2606012400: Session close — kotoba hybrid web search (BM25 + PageRank + RRF) shipped"
status: active
doc_type: adr
topic: kotoba-hybrid-web-search
authoritative: false
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-01 session that added the missing Google-shaped legs (lexical BM25 + link-authority PageRank + RRF fusion) to kotoba's Common Crawl search, fixed the inert IVF query path, and wired the ingest-time precompute. Authoritative design lives in ADR-2606012300."
authoritative_for:
  - session-close record for the 2026-06-01 kotoba hybrid web search session
depends_on:
  - adr-2606012300-kotoba-hybrid-web-search
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606012400: Session close — kotoba hybrid web search (BM25 + PageRank + RRF) shipped

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The originating question for this session was: *「google のような global な検索は設計実装されている? kotoba server で」*
— is a Google-like global search designed and implemented in the kotoba server?

The audit verdict was **partial**. kotoba already had, end-to-end: Common Crawl parquet
ingestion (`kotoba-ingest::cc` → `cc/*` datoms), semantic (vector) search via a pure-Rust IVF
index + Murakumo-only embeddings (`com.etzhayyim.apps.kotoba.cc.search` / `.rag`), and cross-modal
search. But the three pillars that make Google *Google* were missing or inert:

1. **No keyword / full-text (lexical) search** — every query was embedding-cosine only.
2. **The IVF query path was dead** — `cc_search` detected a persisted index then fell back to
   brute-force with a literal `let _ = ivf;`, even though per-chunk cluster assignments
   (`cc/ivf/cluster`) were already written at ingest.
3. **No authority ranking** — `cc/outlink_count` was ingested but no PageRank existed.

Hard constraint: stay inside kotoba's architecture — the Datom log is first-class canonical
state (ADR-2605312345), pure Rust, **no external search engine / vector DB**, Murakumo-only for
any inference (ADR-2605215000). The user then directed both follow-ups: **(1)** wire the BM25
precompute, **(2)** extract CC outlink edges so PageRank runs on real data.

# Decision

Ship the hybrid retrieval stack per **ADR-2606012300** (the authoritative design record). Two
increments landed in this session:

**Increment 1 — the three legs + IVF fix:**

- `kotoba-ingest::bm25` — Okapi BM25 lexical inverted index (`k1=1.2`, `b=0.75`), CJK-aware
  bigram tokenizer (Japanese CC text searchable with no external segmenter), `cc/bm25/*`
  datom persistence (`to_quads` / `from_datoms`).
- `kotoba-ingest::pagerank` — pure power-iteration link-authority (Σ=1 dangling-mass
  redistribution, damping 0.85), `cc/rank/score` datoms.
- `kotoba-ingest::fusion` — Reciprocal Rank Fusion (`RRF_K=60`, scale-free across the three
  incomparable score distributions) + a min-max weighted-linear fuser.
- `kotoba-server::cc_xrpc` — fixed the dead IVF fallback (`semantic_ranking()` probes `nprobe`
  nearest centroids via the persisted `cc/ivf/cluster` assignments) and added
  `com.etzhayyim.apps.kotoba.search.web` (GET) fusing lexical + semantic + authority via RRF with
  graceful degrade.

**Increment 2 — precompute wiring (the two follow-ups):**

- BM25 precompute: a corpus-global build pass persists `cc/bm25/*` into the chunks graph;
  `web_search` prefers it; `com.etzhayyim.apps.kotoba.search.reindex` (POST) rebuilds on demand; the
  `cc.ingest` job triggers the rebuild automatically.
- Outlink edges: `CcPageIngestor::ingest_links_dir_datoms` / `read_page_links` parse an optional
  `outlinks` `List<Utf8>` column into `cc/link/to` edges in `cc:2026-12:links`; the PageRank pass
  runs over them and persists `cc/rank/score`. `cc.status` now reports
  `bm25_terms` / `link_edges` / `pagerank_nodes`.

# Consequences

**Shipped & verified:**

- kotoba search is now hybrid (lexical + semantic + authority), datom-native, with **no external
  search engine, vector DB, or non-Murakumo inference introduced** — every index round-trips
  through the canonical Datom log.
- Tests: **105 `kotoba-ingest` lib tests** (incl. `cc-parquet`) + **22 `cc_xrpc` tests** green;
  both crates build in default + `cc-parquet` configs. Clippy clean on the new code.
- Commits: kotoba submodule `f14cef2` (feature code, 8 files; pre-existing unrelated working-tree
  changes left untouched) → root `3e47cb7ab` (ADR-2606012300 + README + CLAUDE.md + regenerated
  docs.json/graph.jsonld sidecars + submodule bump), committed via a path-limited commit to avoid
  entangling a concurrent background loop's staged files on the same branch.
- `deps.toml` `[[adrs]]` registry updated with ADR-2606012300 (this session-close ADR's
  authoritative design parent).

**Honest residual (R0, carried in ADR-2606012300):**

- Outlink-edge extraction depends on the pages parquet carrying an `outlinks` list column;
  datasets with only the scalar `outlink_count` yield no edges → empty link graph → authority leg
  dropped at runtime (logged at ingest). The full ingest→PageRank→fuse pipeline is in place and
  unit-tested with synthetic + persisted-roundtrip edges; sourcing the CC host-level webgraph is
  the next *data* increment.
- `search.reindex` is a full rebuild (no incremental/delta maintenance).
- No crawler (kotoba ingests Common Crawl); all endpoints operator-auth gated (Charter ad-free /
  donation-only — not a public ad-supported index).

**Loop stopped here**: the remaining gap (real link-graph data at scale) is a dataset-sourcing
task, not a buildable code increment, so the session is closed.

# Alternatives Considered

See ADR-2606012300 (Elasticsearch/tantivy, hosted vector DB, semantic-only — all rejected for
substrate-invariant or completeness reasons).

# References

- ADR-2606012300 (kotoba hybrid web search — authoritative design)
- `40-engine/kotoba/crates/kotoba-ingest/src/{bm25,pagerank,fusion,ivf,cc}.rs`
- `40-engine/kotoba/crates/kotoba-server/src/cc_xrpc.rs`
- ADR-2605262130 / 2605312345 / 2605215000 (substrate invariants preserved)
