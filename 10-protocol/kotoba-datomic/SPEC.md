> **DEPRECATED 2026-05-26** — Superseded by ADR-2605262130 (Kotoba as
> Canonical Storage Substrate). Retained as historical reference for one
> R-cycle, then archived. No new code references this spec.

# kotoba-datomic — Protocol Specification v0.0.0

Layer-by-layer spec for the Holochain-isomorphic substrate composition defined in
[ADR-2605231400](../../90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md).

> **Status**: scaffold. Every section below has either a stable underlying ADR
> (cited inline) or a `TBD` marker that points to the follow-up implementation
> task. No section is implemented in this directory — kotoba-datomic *is* the
> composition; implementations live in `50-infra/`, `20-actors/`, and
> `00-contracts/` per the [README](README.md) "Implementation surface" table.

## Vocabulary

| Symbol | Definition |
|---|---|
| `Agent` | A DID-bound identity capable of signing. Always `did:web:*` or `did:plc:*` |
| `Record` | A serializable value with a Lexicon-defined schema |
| `CID` | Content identifier (IPFS / Blake3 / SHA-256 form depending on layer) |
| `Cell` | A LangGraph Pregel cell registered in `50-infra/murakumo/fleet.toml` |
| `Membrane` | The composition (Lexicon + Rego + LangGraph determinism) that gates writes |
| `Attestation` | A signed witness verdict on a single record's membrane conformance |
| `Quorum` | The minimum number of matching attestations required for record validity (default 3-of-5) |

## §1 kotoba-datomic-agent

**Status**: stable. Implementation: `50-infra/etzhayyim-did-web/` (live since
2026-05-17), `50-infra/etzhayyim-membership-contract/` (anvil-validated).

An `Agent` is the triple `(did, passkey, sbt_level)`:

- `did` — `did:web:etzhayyim.com` for the operating entity; `did:plc:*` or
  `did:web:*` for individuals (per [ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md))
- `passkey` — WebAuthn credential bound to the DID document; used for all signing
- `sbt_level` — Adherent SBT level 1–7 (誓 / 修 / 献 / 証 / 護 / 議 / 老) per
  `EtzhayyimMembership` contract

**Holochain mapping**: `agent_pub_key` ≡ DID-bound passkey. Holochain's "agent
sovereignty" property holds via DID document control.

## §2 kotoba-datomic-chain

**Status**: stable. Implementation: `50-infra/k8s/atproto-pds/` (live), MST
projection via `50-infra/mst-projector/` (scaffold).

Each `Agent` has exactly one `kotoba-datomic-chain` = an atproto PDS repo MST:

- append-only
- hash-chained (each commit references the previous MST root CID)
- DID-signed (every commit signed by the agent's DID key)
- partition: one chain per agent, no shared chains

Records are addressed as `at://{did}/{collection}/{rkey}`.

**Holochain mapping**: Holochain source chain ≡ PDS MST repo. Holochain's
"every write is signed and ordered per-agent" invariant holds via atproto's
commit log.

## §3 kotoba-datomic-dht

**Status**: partial. IPFS live (`50-infra/ipfs/`), L2 anchor `EtzhayyimAnchor`
anvil-validated, Base Sepolia deploy pending.

A two-tier content-addressed store:

| Tier | Substrate | Function |
|---|---|---|
| **Hot** | IPFS (cluster pin on Murakumo fleet) | Content-addressed payload lookup by CID |
| **Cold / consensus** | Base L2 `EtzhayyimAnchor` | Periodic batch anchor of MST root CIDs |

Anchor cadence: per `50-infra/anchor-cron/` schedule (TBD — default proposal
every 6 h or every 1024 commits, whichever first).

**Holochain mapping**: Holochain DHT ≡ IPFS for content addressing + L2 anchor
for global root agreement. Holochain's random shard ownership is replaced by
full-replication IPFS pin within Murakumo cluster (justified by current data
volume; revisit when total pin set > 1 TiB).

## §4 kotoba-datomic-membrane

**Status**: spec scaffold. Components stable individually; composition rule TBD.

A record passes the membrane iff **all three** layers accept it:

| Layer | Source | Failure mode |
|---|---|---|
| **L1 schema** | Lexicon JSON in `00-contracts/lexicons/{nsid path}/*.json` | malformed input — rejected immediately, no witness consulted |
| **L2 policy** | Rego module in `00-contracts/policies/{nsid path}/*.rego` | Charter Rider §2 violation, doctrinal-position violation, capability scope mismatch — rejected, audit logged |
| **L3 determinism** | LangGraph cell in `20-actors/magatama/cells/{cell-id}/` returning the same `(record, ctx) → verdict` for the same inputs | non-deterministic verdict — escalation to Council Lv6+ ≥3 |

A new record kind is kotoba-datomic-mountable when (L1, L2, L3) are all populated and
the lexicon manifest is signed. See `00-contracts/lexicons/CLAUDE.md` for the
NSID registration ritual.

**TBD**:

- formal grammar for the `(L1, L2, L3)` triple manifest
- bootstrap rule for cells that have no prior record history (cold-start)

**Holochain mapping**: Holochain DNA ≡ `(L1, L2, L3)` triple. Holochain's
"validation function compiled into DNA" property holds via the deterministic-LangGraph
requirement on L3.

## §5 kotoba-datomic-witnesses

**Status**: scaffold shipped 2026-05-23 at `20-actors/etzhayyim-sdk/src/kotoba-datomic/`
(witness-selector + quorum). Cell-side attestation publishing is per-cell
implementation work and not yet shipped.

### Witness selection (planned)

```
witnesses = sorted(fleet.cells, key=cell.id)
selected  = [witnesses[(hash(record_cid) + i) % len(witnesses)] for i in 0..4]
```

Five cells per record. Stable mapping from `record_cid` → witness set so
re-validation is deterministic.

### Quorum (planned)

```
attestations = [c.attest(record) for c in selected]
verdict      = majority(attestations.map(a => a.verdict))
if count(attestations.filter(a => a.verdict == verdict)) >= 3:
    record.witnessed = (verdict, attestations.sigs)
    persist_alongside(record)
else:
    escalate_to_council(record, attestations)
```

Default quorum is 3-of-5; configurable per-NSID in `00-contracts/policies/kotoba-datomic-quorum.rego`.

### Escalation

Witness quorum failure → Council Lv6+ ≥3 multisig per [ADR-2605192300](../../90-docs/adr/2605192300-council-bootstrap.md). The Council either:

- ratifies the write (Council attestation replaces witness quorum), or
- rejects (record CID tombstoned in `vertex_repo_record` audit log)

**Holochain mapping**: Holochain's random validator selection by neighborhood
distance ≡ deterministic `hash(record_cid) % N_cells` selection. The
neighborhood property is sacrificed (we don't have a DHT topology to neighbor
across) in exchange for verifier reproducibility.

## §6 kotoba-datomic-cap

**Status**: stable. Implementation: atproto standard + WebAuthn passkey via
`@etzhayyim/sdk`.

Capability tokens are atproto session JWTs scoped by:

- `aud` — target DID (which PDS / appview the token is valid for)
- `scope` — list of NSID prefixes the bearer may invoke
- `cnf.jkt` — JWK thumbprint of the WebAuthn passkey that minted the token
- `exp` — expiry (default 1 h)

A token is kotoba-datomic-valid iff:

1. signature verifies against the DID document's `authentication` key, AND
2. the `cnf.jkt` matches a WebAuthn credential currently registered in the DID
   document, AND
3. the `scope` claim covers the target NSID

**Holochain mapping**: Holochain capability tokens ≡ atproto JWT-cap with the
`cnf.jkt` confirmation method binding to a hardware-backed key.

## §7 kotoba-datomic-cells (zomes)

**Status**: stable catalog. Implementation: `20-actors/magatama/cells/`,
deployment via `50-infra/murakumo/fleet.toml`.

A `Cell` is a LangGraph Pregel subgraph with:

- a stable `cell_id` (string)
- a `placement` (which Murakumo node hosts the replica set)
- a `replicas` count (default 3 for non-validation cells, 5 for validation cells)
- a `nsid_prefixes` array (which Lexicon namespaces this cell handles)
- a deterministic `(input, ctx) → output` step function (LangGraph node)

The full cell catalog (15 cells as of [ADR-2605192415](../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md)) is the authoritative
zome registry for kotoba-datomic. Adding a kotoba-datomic-cell = adding a row to
`50-infra/murakumo/fleet.toml` + a directory under `20-actors/magatama/cells/`.

**Holochain mapping**: Holochain zomes ≡ Pregel cells. The "WASM-compiled
validation function" property is replaced by "deterministic LangGraph cell";
the property is preserved as long as cells avoid nondeterministic operations
(network calls without idempotency keys, time-of-day branching, etc. — enforced
by lint rule TBD).

## Conformance levels

Two parallel ladders: **primary** (the canonical write/read path) and
**projection** (derived read-path cache, per [ADR-2605231500](../../90-docs/adr/2605231500-kotoba-datomic-projection.md)).

### Primary (canonical state)

| Level | Requirements |
|---|---|
| **L0 nominal** | Writes via `@etzhayyim/sdk`; reads via `@etzhayyim/sdk`; no direct RW/Postgres import |
| **L1 witnessed** | L0 + every write is membrane-validated by ≥3-of-5 witnesses before being marked visible in appview |
| **L2 anchored** | L1 + the MST root containing the write has been anchored to Base L2 within the SLA window (default 6 h) |

The current `60-apps/etzhayyim-project-open-isic/rw-free/` reference implementation
is **L0**. The first **L1** target is the maps `AdminArea` / source-DID
registration commands. **L2** is the maps `vertex_spatial` Building / Mountain
registration commands (low write rate, high durability requirement).

### Projection (derived read path)

A projection is a cache / index / MV that is **deterministically rebuildable
from `kotoba-datomic-chain + kotoba-datomic-dht`** and is **never the only place a write
lives**. Per [ADR-2605231500](../../90-docs/adr/2605231500-kotoba-datomic-projection.md):

| Level | Requirements |
|---|---|
| **L0-projection nominal** | Rebuildable in principle; marked with `// kotoba-datomic-projection` line comment or `kotoba-datomic-projection.edn` manifest; documented rebuild runbook |
| **L1-projection automated** | L0-projection + rebuild tool exists and is exercised in CI + projection consumer subscribes to MST firehose (refuses out-of-order writes) |
| **L2-projection verified** | L1-projection + cross-validation tool that replays a randomly-chosen 1% slice and asserts byte-identical projection contents (modulo intentionally enumerated non-determinism) |

The current maps Tier C reads (`tileGeoJson`, `getChunk`, `realtimeDelaysAtStop`
etc., per [`MIGRATION-TODO.md`](../../60-apps/etzhayyim-project-maps/MIGRATION-TODO.md))
are **pre-L0-projection** — they read from RW without a manifest or rebuild
runbook. Phase 4 of the maps migration brings them to L0-projection; Phase 5
to L1-projection.

The first concrete **L1-projection** in the monorepo is **feed-discover**
(`50-infra/mst-projector/src/feed-discover.ts`, manifest at
`50-infra/mst-projector/projection/kotoba-datomic-projection.edn`, CI smoke at
`50-infra/mst-projector/test/feed-discover.replay.test.ts`). It indexes
`app.bsky.feed.post` records cross-DID and emits
`com.etzhayyim.projection.feedDiscover` snapshots; the lexicon's `verdict`
field carries the membrane attestation observed via the
`com.etzhayyim.membrane.verdict` sidecar. Per
[ADR-2605231902](../../90-docs/adr/2605231902-feed-post-membrane-and-feed-discover-projection.md).

### Combined claim

A module's full kotoba-datomic conformance claim is a pair `(primary L?, projection
L?)` per surface. Example: maps `register_region` is primary-L1 (witnessed
write), no projection. Maps `tileGeoJson` is primary-L0 (write went through
SDK) + projection-L0 (read from manifest-marked RW MV). Maps `nextDeparturesAtStop`
is primary-L1 (timetable write witnessed) + projection-L1 (CI-tested rebuild
of the GTFS index).

## Open questions

- **OQ-1**: should kotoba-datomic-witnesses operate on plaintext or ciphertext for
  `com.etzhayyim.encrypted.*` records? Plaintext requires witness cells to be
  inside the recipient set, which violates the encryption model. Ciphertext
  requires the membrane to validate envelope structure only (not payload). See
  ADR-2605181100 for the encryption envelope; the witness extension is TBD.
- **OQ-2**: bootstrapping the first cell without prior witnesses — how does
  cell #1 get attested? Founder-only override during bootstrap, transitions to
  full quorum at first epoch (TBD ADR).
- **OQ-3**: does kotoba-datomic-dht require IPFS to be globally addressable, or can
  intra-cohort use a private cluster swarm? Probably the latter, with global
  IPFS as a publish surface only — TBD.
- ~~**OQ-4**: how does kotoba-datomic-projection (regenerable cache for hot-path
  queries like maps bbox / GTFS-RT) interact with conformance levels?~~ —
  **resolved** by [ADR-2605231500](../../90-docs/adr/2605231500-kotoba-datomic-projection.md)
  (the L0/L1/L2-projection ladder, defined above in §"Projection (derived
  read path)") and first instantiated by feed-discover per
  [ADR-2605231902](../../90-docs/adr/2605231902-feed-post-membrane-and-feed-discover-projection.md).

## Versioning

This SPEC follows the etzhayyim docs versioning convention (semantic version in
the document header). Breaking changes to layer mappings or conformance
requirements require a new ADR; additive clarifications can be made in-place
with a bumped patch version.

Current: **v0.0.0** (scaffold, no implementation yet).
