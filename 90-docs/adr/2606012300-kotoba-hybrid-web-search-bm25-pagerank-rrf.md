---
id: adr-2606012300-kotoba-hybrid-web-search
title: "ADR-2606012300: kotoba hybrid web search — BM25 + PageRank + RRF fusion over the Datom log"
status: accepted
doc_type: adr
topic: kotoba-hybrid-web-search
authoritative: true
last_verified: 2026-06-01
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the keyword/authority gap in kotoba's Common Crawl search; makes it Google-shaped (lexical+semantic+authority) while staying datom-native."
authoritative_for:
  - kotoba global/web search architecture
  - lexical (BM25) inverted index in kotoba
  - link-authority (PageRank) index in kotoba
  - hybrid rank fusion (RRF)
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605250006-kotoba-common-crawl-ingestion
supersedes: []
superseded_by: []
---

# ADR-2606012300: kotoba hybrid web search — BM25 + PageRank + RRF fusion over the Datom log

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The question that prompted this ADR: *"is a Google-like global search designed/implemented in the kotoba server?"*

The honest pre-ADR answer was **partially**. kotoba already had, end-to-end:

- **Web-scale corpus ingestion** — `kotoba-ingest::cc` reads Common Crawl parquet into the `cc:2026-12:{pages,chunks,links}` named graphs as `cc/*` datoms (ADR-2605250006).
- **Semantic (vector) search** — `kotoba-ingest::ivf` (pure-Rust IVF flat index, farthest-first + Lloyd) + `cc/embed/*` embeddings via the Murakumo-only embed client; exposed at `com.etzhayyim.apps.kotoba.cc.search` / `.rag`.
- **Cross-modal search** — `media_xrpc` over the shared embedding space.

But the three pillars that make Google *Google* were missing or inert:

1. **No keyword/full-text (lexical) search.** Every query was embedding-cosine only. A user searching an exact token, a rare identifier, or a phrase had no BM25-style leg.
2. **IVF was not actually wired at query time.** `cc_search` detected a persisted IVF index but fell back to brute-force cosine with a `let _ = ivf;` — even though the per-chunk cluster assignment (`cc/ivf/cluster`) *was* being written at ingest.
3. **No authority ranking.** `cc/outlink_count` was ingested but no PageRank was computed or used.

Hard constraint: this must stay inside kotoba's architecture — **the Datom log is first-class canonical state** (ADR-2605312345), **pure Rust, no external search engine / vector DB**, and **Murakumo-only for any inference** (ADR-2605215000). So we cannot bolt on Elasticsearch/tantivy/Lucene or a hosted vector DB; every index must materialize as `cc/*` datoms in the same named graph and round-trip through `to_quads()` / `from_datoms()`, exactly like `IvfIndex`.

# Decision

Add a **hybrid retrieval stack** to kotoba, all datom-native and dependency-free, fusing three independent signals at query time.

## New pure-Rust index modules (`kotoba-ingest`)

- **`bm25.rs` — lexical inverted index.** Okapi BM25 (`k1=1.2`, `b=0.75`), CJK-aware tokenizer (ASCII words lowercased; CJK runs → overlapping bigrams, so Japanese CC text is searchable with no external segmenter). Persists as `cc/bm25/*` datoms (`n`, `avgdl`, `k1`, `b`, per-doc `len`, per-term `df` + packed `postings` blob). `build()` / `search()` / `search_cids()` / `to_quads()` / `from_datoms()`.
- **`pagerank.rs` — link-authority index.** Pure power iteration with dangling-mass redistribution (Σ=1 guaranteed), damping 0.85, L1 early-stop. CID-keyed `PageRankIndex::compute(edges)` over the `cc:2026-12:links` graph; persists `cc/rank/score` (Float) per page subject. `score()` / `normalized_score()` / `top()` / `from_datoms()`.
- **`fusion.rs` — rank fusion.** Reciprocal Rank Fusion (`RRF_K=60`, scale-free — only needs each signal's *ordering*, perfect for combining unbounded BM25, cosine ∈[-1,1], PageRank ∈(0,1]) plus a min-max weighted-linear fuser with multiplicative authority boost. Returns `FusedHit` with a per-signal rank/score breakdown.

## Server wiring (`kotoba-server::cc_xrpc`)

- **Fixed the IVF fallback.** New `semantic_ranking()` reads the persisted `cc/ivf/cluster` assignments + `cc/ivf/*` centroids, builds the `(cluster, embedding)` candidate set, and calls `IvfIndex::search(query, candidates, nprobe, top_k)` — probing only the `nprobe` nearest centroids. `cc_search` now uses it (brute-force only when no index is present). This removes the `let _ = ivf;` dead path.
- **New endpoint `com.etzhayyim.apps.kotoba.search.web`** (`web_search`, GET). Pipeline:
  1. Load chunk datoms (canonical Datom view via `current_db_for_graph`).
  2. **Lexical**: build BM25 over `cc/chunk/text`, search → ranking.
  3. **Semantic** *(optional)*: if `KOTOBA_EMBED_URL` is configured, embed the query (Murakumo) and run `semantic_ranking` (IVF or brute-force). Absent backend ⇒ leg dropped, search degrades to lexical+authority.
  4. **Authority** *(optional)*: load `PageRankIndex` from the links graph; a chunk's authority = its parent page's (`cc/chunk/page`) normalised PageRank. Empty links graph ⇒ leg dropped.
  5. **Fuse** present signals via RRF (weights `wLex`/`wSem`/`wAuth`, defaults 1.0/1.0/0.5), apply `lang` filter, return `top_k` with per-signal rank breakdown.
- **New endpoint `com.etzhayyim.apps.kotoba.search.reindex`** (`search_reindex`, POST). Rebuilds the corpus-global BM25 (`cc/bm25/*` → chunks graph) and PageRank (`cc/rank/score` → links graph) from the canonical Datom view and commits them. The `cc.ingest` job invokes the same `rebuild_search_indexes` pass automatically after ingest, and the pages-ingest path additionally calls `CcPageIngestor::ingest_links_dir_datoms` to populate `cc:2026-12:links` from the parquet `outlinks` column.
- Operator-auth gated, same `MAX_QUERY_LEN` / `MAX_NPROBE` / `MAX_TOP_K` limits as `cc_search`.

# Consequences

**Done & tested** (105 `kotoba-ingest` lib tests incl. `cc-parquet`, 22 `cc_xrpc` tests, both crates build green in default + `cc-parquet` configs; pre-existing `server::tests` env-var flake unrelated):

- kotoba now has a true keyword search leg (BM25), CJK-aware, datom-persisted.
- IVF ANN is actually exercised at query time (probes nearest centroids; brute-force only as the no-index fallback).
- PageRank authority computed + persisted; demonstrably ranks hubs above leaves, conserves mass.
- All three signals fuse robustly via RRF; the endpoint degrades gracefully when the embed backend or link graph is absent.
- Every index round-trips through the canonical Datom log; **no external search engine, vector DB, or non-Murakumo inference introduced** — substrate invariants preserved.

**Index precompute now wired (2nd increment, this ADR):**

- **BM25 precompute.** A corpus-global BM25 build pass (`build_bm25_datoms` — global df/N/avgdl over the whole chunk graph, so it runs post-ingest, never per-file) persists `cc/bm25/*` and is committed back into the chunks graph. `web_search` now **prefers the persisted index** (`Bm25Index::from_datoms`) and only rebuilds query-time as a fallback. The `cc.ingest` job triggers the rebuild automatically after ingest; `com.etzhayyim.apps.kotoba.search.reindex` (POST) rebuilds on demand.
- **Outlink edges + PageRank.** `CcPageIngestor::ingest_links_dir_datoms` / `read_page_links` parse an optional `outlinks` (`List<Utf8>`) column from the pages parquet into `cc/link/to` Cid edges in the `cc:2026-12:links` graph (self-loops dropped). `build_pagerank_datoms` runs PageRank over those edges and persists `cc/rank/score`; the ingest job + reindex endpoint do this automatically. `web_search` already consumes the authority leg. `cc.status` now reports `bm25_terms` / `link_edges` / `pagerank_nodes`.

**Honest limitations / deferred (R0):**

- **Outlink column dependency.** Edge extraction reads an `outlinks` list column **if the pages parquet provides one**. Datasets carrying only the scalar `outlink_count` yield no edges — the links graph stays empty, PageRank produces nothing, and the fuser drops the authority leg (honest degradation, logged at ingest). Sourcing/attaching the CC host-level webgraph (or a links parquet) to populate real edges at scale is the next data increment; the full ingest→PageRank→fuse pipeline is in place and unit-tested with synthetic + persisted-roundtrip edges.
- **Full-rebuild reindex.** `search.reindex` recomputes both indexes from scratch (no incremental/delta update). Fine at current scale; incremental maintenance is a later optimisation.
- **No crawler.** kotoba ingests Common Crawl, it does not crawl the open web itself (by design).
- **Not a public search engine.** All endpoints are operator-auth gated; this is internal religious-corp infrastructure, not an ad-supported public index (Charter: ad-free, donation-only).

# Alternatives Considered

- **Elasticsearch / OpenSearch / tantivy / Lucene** — rejected: violates the no-external-engine substrate invariant (ADR-2605262130) and the Datom-log-as-canonical-state rule (ADR-2605312345).
- **Hosted vector DB (Pinecone/Weaviate/pgvector)** — rejected: same substrate violation; IVF-over-datoms already covers ANN.
- **Semantic-only (status quo)** — rejected: misses exact-token / rare-identifier / phrase queries that lexical search nails; hybrid is strictly more robust.
- **Weighted linear fusion as the default** — kept as `weighted_score_fusion` for callers who trust raw magnitudes, but RRF is the endpoint default because it is scale-free across the three incomparable score distributions.

# References

- `40-engine/kotoba/crates/kotoba-ingest/src/{bm25,pagerank,fusion,ivf}.rs`
- `40-engine/kotoba/crates/kotoba-server/src/cc_xrpc.rs` (`web_search`, `semantic_ranking`)
- ADR-2605262130 (kotoba storage substrate unification — no external engine)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605215000 (Murakumo-only inference)
