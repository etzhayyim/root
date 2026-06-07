---
id: adr-2605312345-kotoba-datom-first-class-canonical-state
title: "ADR-2605312345: kotoba Datom as First-Class Canonical State — IPFS reframed as block backend, MST as ingress/interop wire, Base L2 as trust anchor"
status: proposed
doc_type: adr
topic: storage-substrate
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.65
priority_note: "Doctrine-clarifying successor to ADR-2605262130. Elevates the kotoba Datom log (content-addressed, immutable EAVT Datalog — Datomic-isomorphic) to the FIRST-CLASS canonical state primitive, resolving the mismatch between kotoba's own self-definition ('the distributed Datom DB is the source of truth') and the root-repo doctrine that listed MST+IPFS+L2 as 'State' with the Datom as a regenerable projection. No constitutional invariant is changed — only the layering/authority direction is made explicit. IPFS/MST/Base L2 are retained but reframed as subordinate physical/interop layers under the Datom."
authoritative_for:
  - "canonical state primitive = kotoba Datom log (content-addressed EAVT Datalog)"
  - "reframing of IPFS as Datom block backend (cold tier / DHT)"
  - "reframing of AT Protocol MST as ingress + interop wire format (not canonical state home)"
  - "reframing of Base L2 as trust anchor over the Datom commit-DAG root"
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231500-kotoba-datomic-projection
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605192245-etzhayyim-global-land-sovereignty
supersedes: []
superseded_by: []
---

# ADR-2605312345: kotoba Datom as First-Class Canonical State

**Status**: proposed
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605262130 named **kotoba** the canonical storage substrate engine and removed
the projection layer (kotoba-kqe arrangements serve hot-path reads directly over
content-addressed blocks). But it left the *layering authority* ambiguous, and the
downstream doctrine inherited the older kotoba-datomic framing:

- **`CLAUDE.md` substrate-boundary table** lists the canonical **State** as
  `AT Protocol MST + IPFS + Base L2 anchor` — the kotoba Datom log does **not** appear
  in the State row at all; kotoba shows up only as the "Substrate engine" / "Read path".
- **`deps.toml`** declares `state_substrate = ["AT Protocol MST", "IPFS", "Base L2 anchor"]`
  and describes the kotoba-kqe arrangement indexer as **"regenerable from MST + IPFS +
  Base L2 anchor"** — i.e. MST/IPFS are the primary source and the Datom is a derived cache.
- Yet **kotoba's own README** states the opposite: *"the distributed Datom DB is the
  source of truth; SPARQL 1.1 reads the same projection… Datomic/Datalog primary."*

This is a genuine contradiction in the authority direction. Actors already built on the
correct mental model — `junkan` (ADR-2605290927) and `tadori` (ADR-2605301400) both
treat the **datom/EAVT log as the durable source of record** and MST/IPFS as transport —
so the doctrine is lagging the implementation, not the other way around.

# Decision

**The kotoba Datom log is the first-class canonical state primitive of the religious-corp
substrate.** A *Datom* is the immutable 5-tuple `(E, A, V, T, Added)`, content-addressed
(IPFS-compatible CIDv1), Datomic-isomorphic, indexed by the kotoba-kqe arrangements
(EAVT / AEVT / AVET / VAET / TEA). The Datom log is the authority for query, consistency,
as-of/history, and cross-store joins.

IPFS, AT Protocol MST, and Base L2 are **retained** but reframed as **subordinate layers
under the Datom**:

| Layer | Role under the Datom | Was (pre-this-ADR) |
|---|---|---|
| **kotoba Datom log** (EAVT, content-addressed) | **canonical state** — source of truth for query/consistency/history | absent from State row; "read path" only |
| **IPFS** | **block backend** — content-addressed cold tier / DHT for Datom blocks (CIDv1, Bitswap, Kubo) | co-equal "State" |
| **AT Protocol MST** | **ingress + interop wire** — records enter as Datoms via the commit DAG and are re-emitted as MST for AT Proto federation; MST is transport, not the canonical home | co-equal "State" |
| **Base L2 anchor** | **trust anchor** — periodic on-chain anchoring of the Datom commit-DAG root | co-equal "State" |

Equivalently: the Datom log is the *logical* state; MST commits and IPFS blocks are its
*physical* materialization, co-derivable with it, but the Datom is the authority. The
directionality "regenerable from MST + IPFS" is **inverted** to "MST/IPFS materialize
the Datom log"; for disaster recovery the Datom log remains deterministically
reconstructible from MST+IPFS+L2 (that property is preserved, not the authority claim).

**Carve-outs preserved unchanged (no weakening):**

- **C1 — On-chain records stay on-chain.** Land registry / SBT roster / Council
  attestation / Public Fund accounting / Tithe ledger / Force Authorization records
  remain authoritative on geth-private + Base L2 + IPFS + `LANDS.md`/`MEMBERS.md`
  (ADRs 2605192245 / 192300 / 192315 / 192145 / 192130, and 2605262130 D4/N3). The Datom
  log indexes/mirrors them; it does **not** become their write home.
- **C2 — Encrypted wire format unchanged.** `com.etzhayyim.encrypted.*` (ADR-2605181100/181200)
  is the bit-identical envelope; Datoms carry ciphertext, never plaintext private records on MST.
- **C3 — RW-free preserved.** No Kotoba/Datomic / Postgres / Lance / DuckDB / SQLite as
  projection, cache, or read backend (ADR-2605172000 + 2605262130 D7/N8).
- **C4 — No-server-key preserved.** etzhayyim-operated infra holds no signing key; the
  Datom-log indexer is a read-only surface (ADR-2605231525). MST commits are member-signed.
- **C5 — Murakumo-only inference preserved** (ADR-2605215000); `kotoba-llm` stays a routing
  facade, local inference disabled in religious-corp paths.
- **C6 — Substrate boundary preserved.** Apps reach the Datom log only via `@etzhayyim/sdk`;
  no direct `kotoba-*` import from `60-apps/*` (ADR-2605172000 + 2605262130 D5).

# Consequences

- **`CLAUDE.md` substrate-boundary table**: the **State** row is rewritten to name the
  kotoba Datom log as canonical, with IPFS/MST/Base L2 as subordinate layers. The
  Substrate-engine and Read-path rows are updated to cross-reference this ADR.
- **`deps.toml`**: `state_substrate` is reordered to lead with the kotoba Datom log;
  `state_canonical` + `state_canonical_adr` keys added; the `server_key_allowed_surfaces`
  indexer note is reworded from "regenerable from MST+IPFS" to "materializes/indexes the
  canonical Datom log".
- **`feed-discover`** (ADR-2605231902) is unaffected: it remains the first L1-projection app
  and still migrates its read backend to kotoba-kqe at Phase 2.5; the only change is that the
  *target* (the Datom log) is now named the canonical state rather than a cache.
- **No code change** is required by this ADR; it is a doctrine/layering clarification. The
  ADR-2605262130 phased rollout (R0..R7) is the implementation vehicle and is unchanged.
- **Disaster recovery** guarantee preserved: Datom log reconstructible from MST + IPFS +
  Base L2; only the *authority direction* for live query/consistency is reassigned to the Datom.

# Alternatives Considered

- **A — Datom-only canonical (remove MST/IPFS from substrate boundary).** Rejected: MST is
  required for AT Proto federation/interop and IPFS for content-addressed DHT distribution;
  dropping them from the boundary would weaken the blockchain-self-contained / decentralization
  guarantees for no benefit. The Datom does not replace them; it sits above them.
- **B — Co-equal (list Datom alongside MST/IPFS/L2 with no hierarchy).** Rejected: leaves the
  README-vs-doctrine contradiction unresolved — "source of truth" cannot be four co-equal
  things with different consistency models. A single authority for query/consistency is required.
- **C — Status quo (kotoba stays "engine/read-path" only).** Rejected: perpetuates the
  contradiction and the wrong directionality ("Datom regenerable from MST"), which already
  conflicts with how `junkan` and `tadori` are designed.

# References

- ADR-2605262130 — Kotoba as Canonical Storage Substrate (parent; this ADR clarifies its layering)
- ADR-2605172000 — RW-free substrate
- ADR-2605181100 / 181200 — `com.etzhayyim.encrypted.*` wire format
- ADR-2605215000 — Murakumo-only inference
- ADR-2605231525 — no-server-key religious-corp architecture
- ADR-2605231902 — feed-post membrane + feed-discover projection (Phase 2.5 migration target)
- ADR-2605192245 — Land Trust 4-layer (on-chain-stays-on-chain carve-out)
- `40-engine/kotoba/README.md` — "Datomic/Datalog primary… the distributed Datom DB is the source of truth"
