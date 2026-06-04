---
id: adr-2605231400-kotoba-datomic-holochain-iso-substrate
title: "ADR-2605231400: kotoba-datomic — Holochain-isomorphic substrate over LangGraph + IPFS + atproto (SUPERSEDED by 2605262130)"
status: superseded
doc_type: adr
topic: kotoba-datomic-substrate
authoritative: true
last_verified: 2026-05-23
priority: 8.5
axis: substrate-boundary
weight: 0.9
authoritative_for:
  - "kotoba-datomic protocol family (10-protocol/kotoba-datomic/)"
  - "Holochain-iso reference architecture name"
  - "validation membrane + witness quorum spec"
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605222330-etzhayyim-com-substrate-violation-transition-window
supersedes: []
superseded_by:
  - adr-2605262130-kotoba-storage-substrate-unification
---

# ADR-2605231400: kotoba-datomic — Holochain-isomorphic substrate over LangGraph + IPFS + atproto

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

ADR-2605172000 mandates RW-free substrate (`AT Protocol MST + IPFS + Base L2 anchor`)
for all `etzhayyim/root` apps, but the spec is layered as a stack of primitives —
not as a named architecture pattern. In session 2026-05-23 the following gap was
surfaced while triaging the `60-apps/etzhayyim-project-maps/` migration (whose
`MIGRATION-TODO.md` is empty as of this writing):

- the RW-free stack maps **isomorphically** to Holochain's agent-centric architecture
  (source chain + DHT + DNA + validation witnesses + capability tokens + zomes), and
- etzhayyim already has every Holochain primitive present in different layer names
  (PDS MST = source chain, IPFS+L2 = DHT, Lexicon+Rego+LangGraph = DNA, Pregel cells
  on Murakumo fleet = validators, atproto JWT-cap+passkey = capabilities,
  ADR-2605192415 Pregel cell catalog = zomes), but
- there is no single name for the composed architecture, so apps cannot reason about
  "am I doing this the right way" beyond per-primitive ADR conformance.

A naming-and-scoring exercise produced 11 candidate topologies. The Holochain-iso
variant scored 70/100 on a 10-axis evaluation, ranking #3 behind "MST + RW AppView
regenerable projection" (74) and "Iroh P2P" (72). It scores **first** on D1 Charter
alignment, D2 censorship resistance, D8 E2E encryption fit, and D9 anti-individualism
ontology — the four axes most load-bearing for the religious-corp mission per
ADR-2605192100.

`kotoba-datomic` was chosen as the canonical name after candidates `yata`, `yatabase`,
`musubi`, `torii`, `harae`, `ukehi`, `yashima`, `kotoage`, and `nakaima` were all
either collision-bound or semantically narrow. `kotoba-datomic`:

- continues the 八- (eight-span / sacred) family already heavily used in the repo
  (八咫 `yata`, 八岐 `yamata`, 八百万 `yaoyorozu`)
- distinguishes itself from `yata` (LanceDB graph engine in `50-infra/yata/`) and
  `yatabase` (commercial BaaS in `60-apps/etzhayyim-project-yatabase/`) by suffix
- `chain` names the per-agent append-only MST source chain — Holochain layer 2 —
  which is the load-bearing structural primitive

`kotoba-datomic` is **not** a blockchain. It is the name of the *composed* substrate.

## Decision

Adopt **kotoba-datomic** as the canonical name for the Holochain-isomorphic composition
of substrate primitives mandated by ADR-2605172000. Place the protocol family at
`10-protocol/kotoba-datomic/` as a peer of `atproto`, `wproto`, `xrpc`, and `signal`.

### 7-layer mapping (canonical)

| # | Holochain primitive | kotoba-datomic term | Existing etzhayyim implementation |
|---|---|---|---|
| 1 | `agent_pub_key` | kotoba-datomic-agent | `did:web` / `did:plc` + WebAuthn passkey + Adherent SBT (`50-infra/etzhayyim-membership-contract/`) |
| 2 | Source chain (per-agent append-log) | kotoba-datomic-chain | atproto PDS MST repo (`50-infra/k8s/atproto-pds/`) — append-only, hash-chained, DID-signed |
| 3 | DHT (shared content store) | kotoba-datomic-dht | IPFS (`50-infra/ipfs/`) + Base L2 anchor (`50-infra/l2-anchor-contract/`) — content-addressed graph + global Merkle root agreement |
| 4 | DNA (validation membrane) | kotoba-datomic-membrane | Lexicon (`00-contracts/lexicons/`) + Rego policy (`00-contracts/policies/`) + LangGraph cell catalog (`20-actors/magatama/cells/`) |
| 5 | Validation by random witnesses | kotoba-datomic-witnesses | Pregel cell instances on Murakumo fleet (`50-infra/murakumo/fleet.toml`, 10 nodes × 15 cells), selected by `hash(record_cid) % N_cells`, quorum ≥3-of-5 |
| 6 | Capability tokens | kotoba-datomic-cap | atproto JWT-cap + WebAuthn DID-bound passkey |
| 7 | Zomes (application modules) | kotoba-datomic-cells | Pregel cells per ADR-2605192415, with cell catalog at `20-actors/magatama/cells/README.md` |

### Membrane proof

A record is **kotoba-datomic-valid** iff:

1. signed by the originating kotoba-datomic-agent's DID-bound key
2. appended to that agent's kotoba-datomic-chain (PDS MST commit succeeds)
3. content pinned to kotoba-datomic-dht (IPFS pin confirmed + CID embedded)
4. validated by ≥3-of-5 kotoba-datomic-witnesses, where:
   - 5 cells are selected by `hash(record_cid) % len(fleet.cells)`
   - each cell evaluates the kotoba-datomic-membrane (Lexicon schema + Rego policy +
     LangGraph determinism check) and returns a signed attestation
   - ≥3 matching attestations are persisted alongside the record CID
5. (within batching window) anchored into a Base L2 kotoba-datomic-dht root via
   `EtzhayyimAnchor.anchor(rootHash, ipfsCid, batchSize)`

Council Lv6+ ≥3 multisig (ADR-2605192300) is the **L2 escalation path** invoked
when witness quorum fails or when the membrane itself is being amended.

### What kotoba-datomic is NOT

- **not a blockchain** — there is no global ledger of all writes; L2 anchor records
  only the Merkle root of batched MST commits
- **not a replacement for `@etzhayyim/sdk`** — kotoba-datomic *is* what `@etzhayyim/sdk`
  composes; the SDK remains the sole import seam per ADR-2605172000
- **not a replacement for `yata` (graph engine) or `yatabase` (commercial BaaS)** —
  the name 八咫 is shared (`yata-` family) but kotoba-datomic has no LanceDB or BaaS
  dependency
- **not currently the substrate for hot-path spatial / GTFS-RT / WHERE-bbox
  queries** — those continue to violate ADR-2605172000 transiently per the
  in-flight `60-apps/etzhayyim-project-maps/` migration; a follow-up ADR will
  define the regenerable-projection escape hatch (see Future Work below)

### Naming rules

- Public spelling: **`kotoba-datomic`** (single token, lowercase)
- Hyphenated form `yata-chain` is **prohibited** because it shadows the `yata-*`
  Cargo workspace crate naming convention in `50-infra/yata/`
- All sub-primitives use `kotoba-datomic-{term}` form (e.g., `kotoba-datomic-witnesses`,
  `kotoba-datomic-dht`)
- Japanese gloss: 八咫鎖 (kotoba-datomic). Reading on second character: `kusari` or
  `chēn` (English borrowing); the Latin spelling is canonical and the kanji
  appears only in explanatory prose

## Consequences

### Positive

- Apps get one architecture name to refer to (e.g., "this is kotoba-datomic-compliant")
  instead of enumerating four primitive ADRs each time
- The witness quorum spec (≥3-of-5) becomes implementable as `20-actors/magatama/src/validation/{witness-selector,quorum}.ts` without inventing a new
  abstraction — the ADR-2605192415 Pregel cell catalog already enumerates the
  witness pool
- Charter §1 anti-individualism alignment improves: kotoba-datomic frames every record
  as requiring community validation (witness quorum), not just individual signature
- The maps migration gets a target architecture name; `MIGRATION-TODO.md`
  can be written as a kotoba-datomic-conformance checklist

### Negative

- Brand confusion risk with `yata` (engine) and `yatabase` (BaaS) — mitigated by
  the spelling rule above
- Performance: bbox spatial queries and GTFS-RT 30s polling remain unaddressed;
  the regenerable-projection escape hatch is a follow-up ADR, not in scope here
- The witness quorum spec adds a fanout of 5 to every write, which doubles
  Murakumo fleet validation load (estimate based on current write rate ~10/s
  → 50 validation tasks/s, well within 10-node fleet capacity)

### Neutral

- Holochain (the actual Rust implementation in `50-infra/holochain/`) remains a
  seeded sibling, not used. kotoba-datomic is *isomorphic to* Holochain but built on
  the etzhayyim substrate stack and intentionally does not consume any Holochain
  binary or library
- This ADR does not deprecate or supersede ADR-2605172000; it *names* the
  architecture that ADR-2605172000 mandates

## Implementation plan

| # | Step | Owner | Target |
|---|---|---|---|
| 1 | This ADR + `10-protocol/kotoba-datomic/{README.md,SPEC.md}` + `deps.toml` + root `CLAUDE.md` updates | session 2026-05-23 | shipped with this commit |
| 2 | `20-actors/etzhayyim-sdk/src/kotoba-datomic/witness-selector.ts` — `hash(record_cid) % len(fleet.cells)` returning 5 cell IDs | shipped 2026-05-23 | — |
| 3 | `20-actors/etzhayyim-sdk/src/kotoba-datomic/quorum.ts` — collect ≥3 matching attestations, persist alongside record | shipped 2026-05-23 | — |
| 4 | `00-contracts/lexicons/com/etzhayyim/kotoba-datomic/{attestation,membraneRule}.json` — DNA-equivalent rule spec lexicons | shipped 2026-05-23 | — |
| 5 | `60-apps/etzhayyim-project-maps/MIGRATION-TODO.md` rewritten as kotoba-datomic conformance checklist (replaces current empty file) | follow-up | 0.5-day |
| 6 | ADR for the regenerable-projection escape hatch (RW AppView as "kotoba-datomic-projection", Iroh as "kotoba-datomic-sync") | follow-up | 1-day |

## Future Work

- **Regenerable projection ADR**: define when a RW AppView (or Iroh-synced doc, or
  in-memory index) qualifies as a kotoba-datomic-projection — i.e., a cache that is
  *deterministically rebuildable* from kotoba-datomic-chain + kotoba-datomic-dht — so hot-path
  queries (maps bbox, GTFS-RT) can use SQL/index acceleration without violating
  ADR-2605172000. Working name: `kotoba-datomic-projection` (ADR TBD)
- **Sync layer ADR**: Iroh P2P sync as a `kotoba-datomic-sync` accelerator that does not
  require L2 anchor round-trip for intra-cohort propagation (ADR TBD)
- **Encrypted membrane**: extend the witness validation to operate on
  `com.etzhayyim.encrypted.*` ciphertext (ADR-2605181100) via zero-knowledge
  attestation — witnesses validate envelope structure + signature without
  decrypting payload (ADR TBD, depends on libsignal capability)
- **Council escalation handoff**: formalize when witness quorum failure escalates
  to Council Lv6+ ≥3 multisig vs. when the write is simply rejected (operator
  choice per `00-contracts/policies/kotoba-datomic-escalation.rego`, follow-up)
