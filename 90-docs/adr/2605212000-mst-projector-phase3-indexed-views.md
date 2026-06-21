---
id: adr-2605212000-mst-projector-phase3-indexed-views
title: "ADR-2605212000: mst-projector Phase 3 — indexed materialized views for kotoba actors"
status: active
doc_type: adr
topic: mst-projector-phase3-indexed-views
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: performance
weight: 0.85
priority_note: "Closes Phase 2 O(N) scan bottleneck in 25 kotoba actors. Phase 3 enables production-scale queries: kiyo.searchPapers (10k papers) from >500ms to <50ms via IVF index; hanrei.coverageStats from O(N) scan to O(1) aggregate lookup. Hard blocker for lawfirm P1 query latency SLA."
authoritative_for:
  - mst-projector architecture and update latency SLA
  - Text search index strategy (IVF embedding + DuckDB inverted)
  - Aggregate materialization pattern (streaming MV)
  - Per-actor ProjectorConfig interface
  - Phase 3 reference impl scope (kiyo starter actor)
depends_on:
  - adr-2605203000-kotoba-write-target-options
  - adr-2605210000-search-etzhayyim-ai-internal-only
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-0019-atproto-native-identifier-topology
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605111300-pds-to-pod-bun-container
  - adr-2605092500-reasoning-as-sap-flow-walk
supersedes: []
superseded_by: []
---

# ADR-2605212000: mst-projector Phase 3 — indexed materialized views for kotoba actors

**Status**: active
**Date**: 2026-05-21
**Decider**: Claude Opus 4.7

# Context

[ADR-2605210000](./2605210000-phase-e-reference-impl-completion.md) records the completion of Phase E kotoba reference impl scaffolds for 25 etzhayyim actors, replacing vendor's `createKyselyDb()` direct-write pattern with `@etzhayyim/sdk e.write()` → PDS XRPC → AT firehose.

Phase 2 query functions emit `truncated: boolean` honesty flags when data exceeds scan limits:

- `hanrei.coverageStats` — scans up to 10,000 records across 3 collections (case/law/gazette), returns truncated flag
- `ipaddress.searchProviders` — O(N) text match on name/slug across 50k+ providers
- `kiyo.searchPapers` — O(N) client-side text match across title/abstract/tags (10k+ papers)
- `kiyo.getCitationGraph` — single O(N) paper scan + BFS traversal
- `narou.searchNovels`, `manga.searchTitles`, `anime.searchTitles` — O(N) full-collection scans
- `houbun.listStatutes` — cursor pagination with post-fetch filter
- `isbn.coverage`, `isin.getDashboard`, `kiyo.getStats` — aggregate counts with max-scan caps

These patterns are honest about truncation but block production use:
- `kiyo.searchPapers` at 10k papers: >500ms latency, p99 >1s
- `hanrei.coverageStats` across 3 collections: O(3N) scans, p50 >200ms
- `ipaddress.searchProviders` at 50k+ ASNs: p99 >5s without index

Phase 3 mst-projector closes this gap by maintaining indexed materialized views server-side, enabling:
- **Text search**: O(log N) IVF vector similarity (sentence-transformers embeddings)
- **Attribute inverted index**: O(1) attribute → record list (e.g., countryIso3 → [IPs], cveId → [vulnMatches])
- **Aggregate counts**: O(1) pre-computed aggregates (by-status/by-language/by-month)

# Decision

## Architecture

**mst-projector** is a TypeScript microservice running in K8s pod (per ADR-2605111200 CF Worker edge-only mandate). It:

1. **Subscribes to PDS firehose** via `com.atproto.sync.subscribeRepos` WebSocket
2. **Filters by actor DID + collection NSID** — only events relevant to configured actors
3. **Maintains 3 index types** per actor (optional, per ProjectorConfig):
   - **Text search index** — document → embedding vector (sentence-transformers `all-MiniLM-L6-v2` or `bge-large-en-v1.5`), stored in LanceDB
   - **Inverted attribute index** — attribute value → set of record DIDs (DuckDB hash table)
   - **Aggregate counts** — group key → count (e.g., `status:published` → 1234, `language:ja` → 567)
4. **Updates atomically on commit** — receive record, compute vector/attributes/groups, write to LanceDB + DuckDB in single txn
5. **Materializes back to PDS** — writes `com.etzhayyim.projector.<actor>View` records so clients can read indexed results via `e.read()`

## Update latency SLA

- **p50**: ≤ 1 second from PDS commit to view index update (typical: 100-300ms)
- **p99**: ≤ 10 seconds (under heavy firehose load or embedding compute spike)
- **Availability**: 99.5% (outages acceptable during PDS maintenance; client fallback to Phase 2 O(N) scan)

## Per-actor projector configuration

Each actor declares its indexes via a TypeScript `ProjectorConfig`:

```ts
export interface ProjectorConfig {
  /** Actor DID (PDS identity). */
  actorDid: string;
  /** Collections to project, keyed by collection NSID. */
  collections: Record<string, CollectionProjection>;
}

export interface CollectionProjection {
  /** AT collection NSID (e.g., "com.etzhayyim.kiyo.paper"). */
  collection: string;

  /** Text search config — null if collection is not searchable. */
  textIndex?: {
    /** Record fields to concatenate and embed (e.g., ["title", "abstract", "tags"]). */
    fields: string[];
    /** Embedding model name. */
    model: "all-MiniLM-L6-v2" | "bge-large-en-v1.5";
  };

  /** Inverted attribute indexes. Each field creates attribute → [DIDs] mapping. */
  attributes?: string[];

  /** Aggregate breakdown fields (e.g., ["status", "language", "field"]). */
  aggregates?: string[];
}
```

## Storage

- **LanceDB** — vector storage for text indexes (zero-copy, local file `<actor>-vectors.db`)
- **DuckDB** — aggregate counts + inverted attribute indexes (local file `<actor>-attributes.db`)
- Both are **file-based, stateless** — no persistent network dependencies
- Checkpointing via PDS subscription cursor; recovery by replaying firehose from last checkpoint

## Reference impl scope

**Phase 3 reference implementation**: `kiyo` actor (smallest data, IVF embedding most demonstrative for `searchPapers`).

1. **Scaffold**: types + class skeleton + kiyo example config (this PR)
2. **Implementation** (Phase 3 work):
   - LanceDB client + embedding model loader
   - DuckDB cursor for incremental aggregate updates
   - Firehose subscription loop
   - Query methods (`queryTextSearch`, `queryAttribute`, `queryAggregate`)
   - Materialization back to PDS as `com.etzhayyim.projector.kiyoPaperView` records

## Migration path for kotoba functions

Phase 2 functions with `truncated` flag can opportunistically query the projector via a new SDK method (v0.2):

```ts
// Phase 2: O(N) scan with truncated flag
const out = await kiyo.searchPapers(e, { query: "machine learning", maxScan: 10_000 });
// Returns { papers: [...], truncated: out.papers.length >= 10_000 }

// Phase 3: O(log N) indexed query, no truncation
const out = await e.queryView({
  actor: "did:web:kiyo.etzhayyim.com",
  viewName: "paperTextSearch",
  params: { query: "machine learning", limit: 100 }
});
// Returns { papers: [...], truncated: false } — full result set
```

Backward compatibility: kotoba falls back to local O(N) scan if projector unavailable (via env var or catch block).

## Examples

### kiyo (starter)

```ts
export const kiyoProjector: ProjectorConfig = {
  actorDid: "did:web:kiyo.etzhayyim.com",
  collections: {
    paper: {
      collection: "com.etzhayyim.kiyo.paper",
      textIndex: {
        fields: ["title", "titleLocal", "abstract", "abstractLocal"],
        model: "all-MiniLM-L6-v2"
      },
      attributes: ["status", "field", "language"],
      aggregates: ["status", "language", "field"]
    },
    review: {
      collection: "com.etzhayyim.kiyo.review",
      textIndex: { fields: ["conclusion"], model: "all-MiniLM-L6-v2" },
      attributes: ["status"],
      aggregates: ["status"]
    }
  }
};
```

### hanrei

```ts
export const hanreiProjector: ProjectorConfig = {
  actorDid: "did:web:hanrei.etzhayyim.com",
  collections: {
    case: {
      collection: "com.etzhayyim.hanrei.case",
      textIndex: { fields: ["title", "summary", "tags"], model: "all-MiniLM-L6-v2" },
      attributes: ["jurisdiction", "court"],
      aggregates: ["jurisdiction", "court"]
    },
    law: {
      collection: "com.etzhayyim.hanrei.law",
      attributes: ["jurisdiction", "type"],
      aggregates: ["jurisdiction"]
    },
    gazetteEntry: {
      collection: "com.etzhayyim.hanrei.gazetteEntry",
      attributes: ["jurisdiction"],
      aggregates: ["jurisdiction"]
    }
  }
};
```

### ipaddress

```ts
export const ipaddressProjector: ProjectorConfig = {
  actorDid: "did:web:ipaddress.etzhayyim.com",
  collections: {
    provider: {
      collection: "com.etzhayyim.ipaddress.provider",
      textIndex: { fields: ["name", "slug"], model: "all-MiniLM-L6-v2" },
      attributes: ["countryIso3", "abuseType"],
      aggregates: ["countryIso3"]
    },
    scan: {
      collection: "com.etzhayyim.ipaddress.scan",
      attributes: ["providerDid"],
      aggregates: ["providerDid", "scanType"]
    }
  }
};
```

## Phase 3 completion criteria

- [ ] Reference impl for kiyo deployed in K8s pod (LanceDB + DuckDB + firehose loop)
- [ ] `kiyo.searchPapers` latency drops from >500ms (O(N) at 10k records) to <50ms (O(log N) IVF)
- [ ] Aggregate functions (`kiyo.getStats`, `hanrei.coverageStats`) respond <10ms from disk cache
- [ ] Truncated flag never appears in production traffic for projected actors (fallback to Phase 2 only on projector downtime)
- [ ] Query interface documented in `@etzhayyim/sdk` v0.2 (`e.queryView()`)
- [ ] Per-actor ProjectorConfig files checked into `20-actors/mst-projector/configs/` for all 25 actors

## Phase 3 implementation notes (2026-05-21)

Initial reference impl shipped as two layered packages:

1. **In-memory baseline** (always-available, dependency-free):
   - `InMemoryTextIndex` — token-frequency text search (TF-lite, no IDF)
   - `InMemoryAttributeIndex` — attribute → value → Set<rkey> inverted map
   - `InMemoryAggregateIndex` — groupBy → value → count with diff-aware upsert
   - `InMemoryProjector` (orchestrator) — `processCommit` + `queryTextSearch` / `queryAttribute` / `queryAggregate`
   - Vitest suite covers all 3 index types + delete + state transitions.

2. **Production backends** (deploy-time configured):
   - LanceDB (IVF embedding via `@lancedb/lancedb`) for text search at O(log N).
   - DuckDB-async for aggregates + inverted attributes at O(1) hash lookup.
   - HF Inference (or local `@xenova/transformers`) for embedding generation.
   - Adapter stubs in `src/adapters.ts` declare the interface; real impls land
     as `src/adapters/{lancedb,duckdb,embedding}.ts` per ops install.

Firehose subscriber (`src/firehose.ts`):
- `PollingFirehose` reads collections via `e.read()` paginate + diff against
  in-memory snapshot. Suitable for tests + low-volume actors.
- Production swaps the poll loop for a WebSocket client to
  `com.atproto.sync.subscribeRepos`. Same `onCommit(event)` handler signature.

Materialization (`src/materialize.ts`):
- Writes projector outputs back to PDS as `com.etzhayyim.projector.aggregate` and
  `com.etzhayyim.projector.textSearch` records so any client can read indexed
  results via the standard `e.read()` API without coupling to LanceDB/DuckDB.

## Related

- [ADR-2605203000](./2605203000-kotoba-write-target-options.md) — Phase E write-target options (Option B = PDS XRPC foundation)
- [ADR-2605210000](./2605210000-phase-e-reference-impl-completion.md) — Phase E scaffold completion (25 actors, truncated flags)
- [ADR-2605111200](./2605111200-cf-worker-edge-only-no-rw-connection.md) — CF Worker edge-only (projector runs in K8s pod)
- [ADR-2605092500](./2605092500-reasoning-as-sap-flow-walk.md) — Reasoning as sap-flow walk (embedding search metaphor)

---

**ADR-2605212000 adopted 2026-05-21T21:30Z**.
