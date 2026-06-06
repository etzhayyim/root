---
id: adr-2605190900-kg-as-lexicon-ipld-oxigraph-appview
title: "ADR-2605190900: Knowledge Graph as Lexicon — com.etzhayyim.kg.{node,edge} + IPLD payload + ephemeral OxiGraph AppView"
status: proposed
doc_type: adr
topic: kg-as-lexicon-ipld-oxigraph-appview
authoritative: true
last_verified: 2026-05-19
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Defines the substrate-native knowledge graph layer for dependency / ADR / module / actor / capability relations. Reuses the MST → IPFS → L2 spine from ADR-2605171800 as KG persistence. Activates once first KG records land in 30-graph/."
authoritative_for:
  - knowledge graph data model on etzhayyim substrate
  - Lexicons com.etzhayyim.kg.node and com.etzhayyim.kg.edge
  - IPLD payload convention for KG records (DAG-CBOR, CID-linked)
  - ephemeral AppView convention (in-memory triplestore, replayable, RW-free)
  - relationship to deps.toml SSoT (deps.toml stays canonical; KG is projected view)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-rw-free-substrate
related:
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
supersedes: []
superseded_by: []
---

# ADR-2605190900: Knowledge Graph as Lexicon — `com.etzhayyim.kg.{node,edge}` + IPLD payload + ephemeral OxiGraph AppView

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

`etzhayyim/root` accumulates a growing set of structured relations:

- **Dependencies** declared in `deps.toml` (modules, ADRs, L2 contracts, DNS records, substrate rules)
- **ADR graph**: `depends_on`, `related`, `supersedes`, `superseded_by` between ~25 ADRs (and growing)
- **Module graph**: `20-actors/magatama` cells, `60-apps/*` apps, `50-infra/*` substrate services, `00-contracts/*` lexicons — and edges between them (e.g. "app uses lexicon", "actor reads contract")
- **Capability graph** (per ADR-2605180900): UNSPSC / ISIC actor lexicon → XRPC method → MCP tool surface
- **Member / institution / referral graphs** (e.g. UHL-R medical institution registry, ADR-2605181040)

These relations are currently siloed: some in TOML, some in lexicon `refs`, some in ADR front-matter, some implicit in directory layout. There is no single queryable view, and no substrate-compliant store for them.

A naive answer would be "put them in a graph DB" — but ADR-2605172000 (RW-free substrate) prohibits centralized off-chain DBs in this monorepo. The remaining question is: **what is the substrate-native shape of a knowledge graph here?**

## Survey of alternatives considered

| Option | IPFS-native? | content-addressed? | Substrate fit | Verdict |
|---|---|---|---|---|
| **ATProto Lexicon (custom KG schema)** | n/a (MST is the store) | ✅ (CIDs in MST) | ◎ | **Selected** |
| **IPLD + DAG-CBOR** alone | ✅ | ✅ | ◎ as **payload format**, not as discovery layer | Selected as payload format |
| **Ceramic / ComposeDB** | ○ (built on IPFS) | ✅ | △ — introduces a parallel substrate (Ceramic network) alongside ours | Rejected |
| **OrbitDB (graph mode)** | ◎ | ✅ | △ — libp2p pubsub layer parallel to ours; maintenance volatility | Rejected |
| **Fluree** | △ (IPFS as optional backend) | ✅ | △ — independent ledger / consensus, even on IPFS backend | Rejected |
| **TerminusDB** | ✗ | ✅ (git-like) | ✗ — local files only, distribution via clone/push | Rejected |
| **Kotoba/Datomic + graph extensions** | ✗ | ✗ | ✗ — explicitly prohibited by ADR-2605172000 | Prohibited |
| **Neo4j / Postgres + AGE** | ✗ | ✗ | ✗ — prohibited centralized DB | Prohibited |

Two observations drove the decision:

1. **The MST + IPFS + L2 pipeline (ADR-2605171800) already gives us a verifiable, content-addressed, replayable store.** Adding a second substrate (Ceramic, OrbitDB, Fluree) would split state across two trust roots. The cheapest correct move is to **express the KG as ATProto records** in that pipeline.
2. **Query is a separate concern from storage.** SPARQL / Cypher engines do not need to be the system of record. They can be **ephemeral indexes** rebuilt from MST replay — which keeps RW-free intact (no durable off-chain state).

## What this ADR is and is not

**Is:**

- A data model (two Lexicons) + payload convention (IPLD DAG-CBOR) + query layer convention (ephemeral OxiGraph SPARQL)
- A projection target for existing SSoTs (`deps.toml`, ADR front-matter, lexicon refs)

**Is not:**

- A replacement for `deps.toml` as SSoT. `deps.toml` remains canonical; the KG is a **projected view** of it (plus other sources).
- A new long-term-stateful service. The AppView holds no durable state of its own.
- A semantic-web (OWL/reasoner) commitment. We use RDF triples as a serialization, not as an ontology obligation.

# Decision

Adopt a three-layer knowledge graph:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Sources (SSoTs)                                                    │
│  ─ deps.toml  ─ ADR front-matter  ─ Lexicon refs  ─ module manifests │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  projector (30-graph/projector/)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1 — KG as ATProto records                                    │
│  ─ com.etzhayyim.kg.node      (record)                              │
│  ─ com.etzhayyim.kg.edge      (record)                              │
│  ─ payload blobs as IPLD DAG-CBOR (CID-linked from records)         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  reuses ADR-2605171800 pipeline
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2 — Persistence (already built)                              │
│  MST  →  mst-projector  →  IPFS (ipfs-pinner)  →  Base L2 anchor    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  replay
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3 — Ephemeral AppView (OxiGraph in-memory triplestore)       │
│  ─ subscribes to MST commits or replays from IPFS                   │
│  ─ exposes SPARQL endpoint over XRPC                                │
│  ─ holds NO durable state; rebuildable from MST/IPFS at any time    │
└─────────────────────────────────────────────────────────────────────┘
```

## Layer 1 — Lexicon definitions

Placed under `00-contracts/lexicons/com/etzhayyim/kg/`.

### `com.etzhayyim.kg.node`

```jsonc
{
  "lexicon": 1,
  "id": "com.etzhayyim.kg.node",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["nodeId", "nodeType", "createdAt"],
        "properties": {
          "nodeId":    { "type": "string", "format": "uri",
                         "description": "Stable identifier: AT-URI, DID, did:plc, http(s) URL, urn:*, or app-defined (e.g. 'adr:2605190900')." },
          "nodeType":  { "type": "string",
                         "description": "Type IRI or short token. Examples: 'adr', 'module', 'lexicon', 'l2-contract', 'dns-record', 'actor-cell', 'capability', 'institution'." },
          "label":     { "type": "string", "maxLength": 256 },
          "payload":   { "type": "blob", "accept": ["application/cbor", "application/json"], "maxSize": 1048576,
                         "description": "Optional IPLD DAG-CBOR or JSON payload. CID is the natural content address." },
          "tags":      { "type": "array", "items": { "type": "string", "maxLength": 64 }, "maxLength": 32 },
          "source":    { "type": "string",
                         "description": "Projection source: 'deps.toml', 'adr-frontmatter', 'lexicon-refs', 'manual', etc." },
          "createdAt": { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}
```

### `com.etzhayyim.kg.edge`

```jsonc
{
  "lexicon": 1,
  "id": "com.etzhayyim.kg.edge",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["subject", "predicate", "object", "createdAt"],
        "properties": {
          "subject":   { "type": "string", "format": "uri",
                         "description": "AT-URI of a kg.node record, or a node.nodeId." },
          "predicate": { "type": "string",
                         "description": "Predicate IRI or short token. Examples: 'depends_on', 'supersedes', 'uses-lexicon', 'projects-from', 'anchored-at'." },
          "object":    { "type": "string", "format": "uri",
                         "description": "AT-URI / nodeId for object-typed edges. Literal-typed edges use 'literal' instead." },
          "literal":   { "type": "string", "maxLength": 1024,
                         "description": "For literal-typed edges (e.g. 'has-version' → '1.2.3'). Mutually exclusive with object — but spec allows both empty when object set." },
          "weight":    { "type": "number" },
          "context":   { "type": "string", "format": "uri",
                         "description": "Optional named graph / provenance pointer (e.g. ADR AT-URI that asserts this edge)." },
          "createdAt": { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}
```

**Mapping to RDF:** `(subject, predicate, object | literal, context)` is an RDF quad. SPARQL queries work natively. We are not committing to OWL semantics; users may layer them.

## Layer 2 — Persistence reuses ADR-2605171800

No new substrate. KG records are ordinary ATProto records — they flow through the existing pipeline:

```
kg.node / kg.edge records  →  MST  →  mst-projector  →  IPFS  →  Base L2 anchor (anchor-cron)
```

This means **the KG inherits all properties of that pipeline**: durability, replayability, third-party verifiability, content-addressing, on-chain finalization.

## Layer 3 — Ephemeral OxiGraph AppView

New module: `30-graph/kg-appview/` (Rust).

**Stack:**

- **OxiGraph** (Rust) — embeddable W3C-compliant RDF triplestore + SPARQL 1.1 engine. Used in **in-memory mode** (`MemoryStore`). Optional disk-backed mode is **explicitly disabled** to keep RW-free.
- **XRPC façade**: `com.etzhayyim.kg.query` (read-only SPARQL endpoint) and `com.etzhayyim.kg.describe` (DESCRIBE shorthand). Definitions live in `00-contracts/lexicons/com/etzhayyim/kg/`.
- **Ingestion**:
  - **Live**: subscribe to MST commits via Jetstream-equivalent firehose (per ADR-2605171800) filtered to `com.etzhayyim.kg.*` records.
  - **Cold start / disaster recovery**: replay from latest L2-anchored MST root via IPFS, rehydrate triplestore from scratch.

**RW-free guarantee:**

- AppView state is held only in process memory.
- On restart, AppView **MUST** rehydrate from MST/IPFS. It is a fatal error to read from a persisted disk cache.
- AppView **MUST NOT** be the system of record for any user-visible state.
- AppView writes? None. SPARQL UPDATE is disabled. The only way to add facts is to write `kg.node` / `kg.edge` records to MST.

## Projection from deps.toml (and other SSoTs)

`30-graph/kg-projector/` (TypeScript, runs alongside `mst-projector`):

1. Read SSoTs: `deps.toml`, all ADR front-matter, all lexicon `refs`, module manifests.
2. Emit `kg.node` records for each entity (ADR, module, lexicon, L2 contract, DNS record, ...).
3. Emit `kg.edge` records for each relation (`depends_on`, `supersedes`, `uses-lexicon`, ...).
4. Idempotent: same input → same records (deterministic rkey from content hash).
5. Runs in CI on PR and on a cron (reuse `anchor-cron` cadence or a sub-cron).

`deps.toml` remains the SSoT. The KG is a **lossless-or-better view**.

# Consequences

## Positive

- **Zero new substrate.** Reuses MST + IPFS + L2 pipeline already in production scaffold (Stages 1–5 per ADR-2605171800).
- **Substrate boundary preserved.** No Kotoba/Datomic, no Postgres, no Ceramic, no Fluree, no parallel network.
- **Replayability for free.** Any historical KG state is reconstructible from L2-anchored MST root + IPFS.
- **Verifiability for free.** Every edge / node is a content-addressed record whose existence can be proven against the on-chain anchor.
- **SPARQL on day one.** OxiGraph gives W3C-compliant SPARQL 1.1 without custom query language design.
- **Composable.** Other apps can publish their own `kg.node` / `kg.edge` records under their DIDs and our AppView indexes them automatically.
- **Provenance native.** The `context` field on edges encodes which record asserted the edge — built-in named graphs.

## Negative

- **Write amplification.** Each TOML row may become multiple ATProto records (one node + several edges). Mitigated by deterministic rkey + idempotent projector.
- **Cold-start time.** Full IPFS replay to rehydrate AppView memory could take minutes-to-hours at scale. Mitigated by anchoring snapshot CIDs and starting from latest snapshot, not from genesis.
- **No SPARQL UPDATE.** Mutations require writing ATProto records, not SPARQL `INSERT DATA`. This is intentional but trips users used to triplestores.
- **In-memory bound.** For very large KGs we may eventually need a disk-backed but **process-local, rebuild-on-start, never-shared** cache. Out of scope here; a follow-up ADR if/when needed.
- **Two projections of same fact.** A relation declared both in `deps.toml` and as a manually-authored `kg.edge` record could disagree. Convention: TOML-declared relations are projected with `source: "deps.toml"`, manual ones with `source: "manual"`; conflicting predicates raise a CI warning.

## Neutral

- Encryption (ADRs 2605181100 / 2605181200): KG records are **public by default** (they describe public structure). Edges whose endpoints are private records use the encrypted-record envelope; the predicate itself remains public. Padding/blinding rules from ADR-2605181200 apply.
- Payment (ADR-2605172100): KG queries are free / unmetered for now; if metered SPARQL endpoint is ever offered, the metering rides ERC-4337 like everything else.

# Implementation plan

| Stage | Deliverable | Owner |
|---|---|---|
| **K0** | This ADR merged; lexicon files committed under `00-contracts/lexicons/com/etzhayyim/kg/` | done by this PR |
| **K1** | `30-graph/kg-projector/` TS package: `deps.toml` + ADR front-matter → `kg.node` / `kg.edge` records, idempotent | next PR |
| **K2** | `30-graph/kg-appview/` Rust crate: in-memory OxiGraph + Jetstream firehose subscriber + XRPC SPARQL endpoint | follow-up |
| **K3** | Cold-start replay: rehydrate AppView from latest L2-anchored MST root + IPFS | follow-up |
| **K4** | Helm chart / K8s manifest for AppView; deploy at `kg.etzhayyim.com` (read-only SPARQL) | follow-up |
| **K5** | Federation: index third-party DIDs that publish `kg.*` records under our AppView | future |

Stages K0–K1 are the MVP. K2 onwards activates the query side.

# Alternatives Considered

## A. Ceramic / ComposeDB

GraphQL-native KG on IPFS. Schema-driven, mature. **Rejected** because it introduces the Ceramic network as a parallel substrate with its own consensus and identity rules — we would have two substrate trust roots to operate. Our ADR-2605172000 substrate is the canonical one; we keep one.

## B. OrbitDB (graph mode)

IPFS-native, P2P, content-addressed. Conceptually a strong fit. **Rejected** on three counts: (1) libp2p pubsub parallel to our Jetstream-equivalent firehose duplicates the eventing layer; (2) maintenance cadence has been volatile through 2023–2025; (3) no SPARQL — we'd be writing query plumbing ourselves.

## C. Fluree

JSON-LD / SPARQL native, supports IPFS as backend. **Rejected** because Fluree is an independent ledger with its own consensus even when blobs sit on IPFS — we already have a ledger (Base L2 anchor). Doubling up adds confusion without adding verifiability we don't already have.

## D. TerminusDB

Git-like semantics on graphs is genuinely beautiful for ADR evolution. **Rejected** because it is not content-addressed in a network-distributable way — distribution requires `clone/push/pull` to a TerminusDB peer, which is yet another substrate.

## E. RDF triples stored directly as DAG-CBOR in IPFS (no Lexicon layer)

Skip ATProto records; store the whole KG as IPLD blobs anchored on L2. **Rejected** because we lose:
- Per-record discoverability via AT-URI
- Native firehose subscription (no Jetstream-equivalent)
- Identity binding to DIDs (every record is signed by an actor)

The Lexicon layer is cheap and buys all three.

## F. Property graph (Cypher) instead of RDF (SPARQL)

Property graphs are ergonomic for app developers. **Rejected** because:
- No equivalent of OxiGraph in Rust for property graphs that is W3C-stable
- RDF triples are trivially serializable; property graphs require choosing between several incompatible serializations
- We can still expose a Cypher facade later (e.g. via [Kuzu](https://kuzudb.com)) if needed, layered on the same record store

## G. Stay with `deps.toml` and stop here

Simplest option. **Rejected** because cross-cutting queries (e.g. "which modules depend on prohibited substrate?", "which ADRs supersede an ADR that an active module depends on?", "what is the capability surface reachable from actor X?") are impractical in TOML and we already write ad-hoc grep scripts. The KG is the structural answer.

# References

- ADR-2605170900 — etzhayyim/root canonical home
- ADR-2605171800 — LangGraph → MST → IPFS → Base L2 anchor pipeline (persistence spine reused here)
- ADR-2605172000 — etzhayyim/root open apps MUST be RW-free
- ADR-2605172100 — etzhayyim payments on-chain only
- ADR-2605180900 — UNSPSC / ISIC LangServer Actor Lexicon / XRPC / MCP (capability graph source)
- ADR-2605181100 — MST encrypted records with Signal key wrap
- ADR-2605181200 — MST encrypted-record metadata-leak reduction
- OxiGraph — https://github.com/oxigraph/oxigraph
- ATProto Lexicon spec — https://atproto.com/specs/lexicon
- IPLD DAG-CBOR — https://ipld.io/specs/codecs/dag-cbor/spec/
- SPARQL 1.1 — https://www.w3.org/TR/sparql11-query/
