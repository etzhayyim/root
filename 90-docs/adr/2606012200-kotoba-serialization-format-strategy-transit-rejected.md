---
id: adr-2606012200-kotoba-serialization-format-strategy-transit-rejected
title: "ADR-2606012200: kotoba serialization-format strategy — JSON wire / EDN values / CBOR internal; Transit rejected"
status: accepted
doc_type: adr
topic: storage-substrate
authoritative: true
last_verified: 2026-06-01
priority: 4.0
axis: architecture
weight: 0.40
priority_note: "Records the kotoba serialization-format split (JSON = HTTP/XRPC wire, EDN = Datomic value/query syntax, CBOR/dag-cbor = internal block + P2P + CACAO + UDF) and the explicit decision NOT to adopt Cognitect Transit. Transit's two value-adds (EDN-rich semantics over a JSON/MessagePack transport + repeated-key caching) are each already covered by EDN and CBOR respectively, so adopting it is Shannon-redundant; it is also blocked by the dag-cbor CID lock-in (internal layer) and weak Rust support. One narrow exception is documented (Transit-JSON on the HTTP wire IF a polyglot Datomic-compatible client protocol is later required)."
authoritative_for:
  - "kotoba serialization-format roles: JSON (HTTP/XRPC wire) / EDN (Datomic value+query) / CBOR dag-cbor (internal block, P2P, CACAO, UDF)"
  - "decision: Cognitect Transit is NOT adopted in kotoba"
  - "condition under which the HTTP-wire Transit exception would be reconsidered"
depends_on:
  - adr-2606012000-kotoba-prolly-incremental-commit-diff-cbor
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2604251830-shannon-optimal-8-layer-architecture
supersedes: []
superseded_by: []
---

# ADR-2606012200: kotoba serialization-format strategy — Transit rejected

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

kotoba already uses three serialization formats, each with a distinct role
(verified by code audit of `crates/kotoba-server` + workspace):

| Layer | Format | Where |
|---|---|---|
| HTTP / XRPC wire (external API body) | **JSON** (`serde_json`, axum) | request/response bodies |
| Datomic value + query syntax | **EDN** (`kotoba-edn`) | tx-data, Datalog, VC/datom values, `*.kotoba.edn` |
| Internal binary: content-addressed blocks, P2P, envelopes | **CBOR / dag-cbor** (`ciborium`) | ProllyTree nodes, blocks, CAR, libp2p gossip/firehose (`net_actor.rs`), CACAO chains (DAG-CBOR + base64), WASM UDF invoke ctx |

The question raised: should kotoba also adopt **Cognitect Transit** (the
Clojure/Datomic ecosystem's format that carries EDN-rich types — keywords, sets,
instants, uuids, bytes, extensible types — over a JSON or MessagePack transport,
with repeated-key **caching** for compactness, and polyglot client libraries)?

# Decision

**Do not adopt Transit.** Keep the three-format split above.

Rationale — Transit's two genuine value-adds are each already covered, and two
hard blockers apply:

- **Rich EDN semantics over the wire → already EDN.** kotoba represents
  keyword/set/instant semantics with EDN at the Datomic value layer; the server
  processes EDN in Rust where parse cost is a non-issue.
- **Compact binary → already CBOR.** dag-cbor gives compact, self-describing,
  IPLD-canonical binary with first-class Rust support.
- **Blocker 1 — dag-cbor CID lock-in.** kotoba CIDs are SHA2-256 over dag-cbor
  bytes; content-addressing + IPFS compatibility *require* dag-cbor in the block
  layer. Transit cannot replace it (would break CID/IPFS compat) and adding it
  there is pure redundancy.
- **Blocker 2 — weak Rust support.** Transit is Clojure-centric; there is no
  maintained production-grade Rust Transit codec. kotoba is Rust-first; adopting
  Transit means owning a codec, for semantics EDN+CBOR already provide.
- **Shannon-minimality.** Per ADR-2604251830 and `90-docs/CLAUDE.md`, the repo
  minimizes redundant formats/decisions. A third overlapping format works against
  that.

# Consequences

- No new dependency, no Rust Transit codec to maintain; the format surface stays
  JSON (wire) + EDN (values) + CBOR (internal).
- Polyglot clients that want Datomic-style keyword/set fidelity over HTTP must
  use the existing paths (EDN strings in JSON, or — if added later — a CBOR body)
  rather than a Transit wire.
- This ADR is the authoritative reference for "why not Transit"; future asks are
  redirected here.

## Narrow exception (documented, not adopted)

The **only** place Transit would add real value is the **HTTP/XRPC wire**, as a
faithful Datomic-style client protocol: Transit-JSON carries keyword/set/instant
semantics *while staying JSON-compatible* (debuggable, CDN/proxy/browser-friendly)
and its key-caching shrinks large, attribute-repetitive datom result sets. This
exception is reconsidered **only if** kotoba decides to expose a Datomic-compatible
client protocol to polyglot (Clojure/JS/Python) clients and values that fidelity +
caching enough to maintain a Rust codec. Even then, cheaper near-substitutes exist
(EDN-over-the-wire, an `application/cbor` body — codec already present, or
zstd/gzip on JSON responses), so any adoption must first benchmark Transit-JSON
against those on real result sets.

# Alternatives Considered

- **Adopt Transit as the internal/block format (replace CBOR).** Rejected:
  breaks dag-cbor CID / IPFS compatibility — non-starter.
- **Adopt Transit-JSON as the HTTP wire now.** Deferred: marginal ROI vs. weak
  Rust support; near-substitutes (EDN-in-JSON already used, optional CBOR body,
  zstd) cover ~80% of the benefit.
- **Adopt Transit at the Datomic value layer (replace EDN).** Rejected: EDN is
  already the value/query syntax and round-trips faithfully; no gain.

# References

- ADR-2606012000 — kotoba ProllyTree incremental commit + diff + CBOR leaf values
- ADR-2605312345 — kotoba Datom as first-class canonical state
- ADR-2605262130 — kotoba storage substrate unification
- ADR-2604251830 — Shannon-Optimal 8-Layer Architecture (format minimality)
- `40-engine/kotoba/crates/kotoba-server/src/` — JSON wire, EDN (`kotoba_edn`), CBOR (`ciborium`) call sites; no Transit dependency anywhere in the workspace
