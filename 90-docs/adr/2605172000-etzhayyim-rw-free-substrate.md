---
id: adr-2605172000-etzhayyim-rw-free-substrate
title: "ADR-2605172000: etzhayyim/root open apps MUST be RW-free — AT MST + IPFS + Base L2 as primary substrate"
status: proposed
doc_type: adr
topic: etzhayyim-rw-free-substrate
authoritative: true
last_verified: 2026-05-17
priority: 8.0
axis: architecture
weight: 0.80
priority_note: "Defines the hard architectural boundary that justifies the etzhayyim/etzhayyim org split. Without this constraint, the split is just license labeling. With it, etzhayyim is genuinely decentralized and verifiable from outside any single operator."
authoritative_for:
  - hard rule: open religious-corp apps MUST NOT depend on RisingWave or any centralized DB
  - primary substrate: AT Protocol MST + IPFS + Base L2
  - SDK pattern: PDS write + IPFS pin + L2 batch anchor as one operation
  - per-app-pattern migration guide off RisingWave
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
supersedes: []
superseded_by: []
---

# ADR-2605172000: etzhayyim/root open apps MUST be RW-free — AT MST + IPFS + Base L2 as primary substrate

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

ADR-2605152100 split the GitHub org along principal/upstream lines (etzhayyim = open religious-corp activities; upstream business stays elsewhere). The criterion was originally "open vs proprietary" — a license/branding distinction.

That criterion is **too soft**. An "open" app that internally requires a centralized RisingWave cluster (operated by one party, behind one set of credentials) is structurally indistinguishable from a proprietary app — the only difference is the README license header. External contributors, peer cells, and auditors still have to trust the RW operator to honor the open framing.

A stronger criterion: **etzhayyim/root apps MUST be verifiable and operable without depending on any centralized off-chain database**. They run on AT Protocol MST + IPFS + Base L2 as the primary substrate. The same data, the same compute, the same verification are reachable from any client with internet access, no privileged operator credentials.

This is the meaningful definition of "open" for the religious-corp activities: open = self-hostable, censorship-resistant, third-party verifiable, no central point of trust.

ADR-2605171800 already established the LangGraph Pregel → PostgresSaver → MST → IPFS → Base L2 anchor pipeline. That ADR treats Postgres as the durable home and MST/IPFS/L2 as a verifiability layer on top. **This ADR inverts that priority**: MST + IPFS + L2 are the durable substrate, and any Postgres/RW usage is restricted to ephemeral in-flight run state that can be reconstructed from MST event log.

# Decision

**Hard rule**: every app under `etzhayyim/root/60-apps/` and every actor under `etzhayyim/root/20-actors/` (excluding the SDK itself) MUST NOT depend on RisingWave, Postgres, or any other centralized off-chain database for durable state.

## Primary substrate (5 layers)

```
┌──────────────────────────────────────────────────────────┐
│ L5  Verification  — Base L2 (Merkle proof against root)  │
├──────────────────────────────────────────────────────────┤
│ L4  Finality      — Base L2 anchor (batched MST root)    │
├──────────────────────────────────────────────────────────┤
│ L3  Storage       — IPFS (content-addressed blobs + MST) │
├──────────────────────────────────────────────────────────┤
│ L2  State         — AT Protocol MST (event log + tree)   │
├──────────────────────────────────────────────────────────┤
│ L1  Identity      — did:web + did:plc + did:etzhayyim    │
└──────────────────────────────────────────────────────────┘
```

| Old (RW-backed) | New (RW-free substrate) |
|---|---|
| `vertex_<actor>_<kind>` SQL INSERT | AT Record create → PDS commit |
| streaming MV / dashboard | client-side reducer over MST subtree (CRDT-style) |
| `SELECT ... WHERE` | MST collection traverse (key-prefixed) |
| large blobs (model weights, video, raw PDF) | IPFS CID, referenced in AT Record body |
| auth (JWT signed by operator) | DID + WebAuthn signature, DID-bound |
| tamper-evidence / audit log | L2 anchor batch + Merkle proof, public verifier |
| cross-app composition | Lexicon NSID federation; no central dispatcher |
| compute (RW UDF, server-side) | LangGraph Pregel cell with ephemeral checkpoint; pure reducer over MST events for derived views |

## SDK: `etzhayyim-sdk` (`20-actors/etzhayyim-sdk/`)

A single TypeScript package wraps the substrate as one ergonomic API. Apps depend on this SDK; the SDK depends on `@atproto/api` (PDS write/read), `ipfs-http-client` or `helia` (IPFS pin/fetch), and `viem` (Base L2 anchor).

```typescript
import { Etzhayyim } from '@etzhayyim/sdk';

const e = new Etzhayyim({
  did: 'did:web:etzhayyim.com',
  pdsUrl: 'https://pds.etzhayyim.com',     // (or per-actor PDS host)
  ipfsGateway: 'https://ipfs.etzhayyim.com',
  l2RpcUrl: 'https://mainnet.base.org',
  anchorContract: '0xANCHOR_ETZHAYYIM',     // ADR-2605171800 Stage 5
});

// Domain write — replaces SQL INSERT
const receipt = await e.write({
  collection: 'com.etzhayyim.apps.openIsco.occupation',  // NSID
  record: { code: '2511', name: 'Software Developer', major: '2' },
  blobs: { handbookPdf: pdfBlob },  // optional, pinned to IPFS
});
// receipt: { uri, cid, blobCids: { handbookPdf: 'Qm...' }, pendingAnchor: 42n }

// Domain read — replaces SQL SELECT
const occ = await e.read({
  collection: 'com.etzhayyim.apps.openIsco.occupation',
  filter: { major: '2' },     // key-prefix traversal of MST
  limit: 50,
});

// Verify — replaces audit trail
const proof = await e.verify(receipt.uri);
// proof: { included: true, anchoredAt: { txHash, blockNumber }, merklePath: [...] }
```

The SDK is the **only** module in `etzhayyim/root` allowed to import database clients. Every other module imports the SDK.

## Per-app-pattern migration guide

| App pattern | RW dependency today | RW-free pattern |
|---|---|---|
| Government data wrapper (`open-jpn-gov`, `open-isco`, `open-isic`, `open-hs`, `open-naics`) | RW MV → query API | each entity as AT Record, browsed via MST traverse; original gov-source PDFs pinned to IPFS; L2 anchor batched per ingestion run |
| Public banking ledger (`open-banking`) | RW double-entry table | smart contract on Base L2 (open-source) + AT Record summary per posting; client reconciles by traversing both |
| AppView (`yoro`, `atproto`) | RW MV for feed | browser-local MST subtree + WebGPU pure-function ranking; IPFS for media; L2 anchor for moderation appeals |
| AI inference (`ameno`, `baien`) | RW for prompt/result cache | WebGPU model loaded from IPFS-pinned weights; inference logged as AT Record; no central state |
| Lexicon registry | generated bundle from RW | Lexicon JSON tree in IPFS; registry root anchored on L2; SDK fetches and validates |
| Open data API (`open-*` 22 本) | RW + materialized view + query worker | static MST snapshot pinned to IPFS per release; client fetches snapshot once, traverses locally |

## Carve-out: upstream backend services

If an open app legitimately needs an upstream backend (paid-tier features, M365 integration, regulated workflows), that backend lives in a separate upstream monorepo and exposes its surface via:

- XRPC over HTTPS at an upstream-controlled DID (or sub-DIDs)
- Lexicon JSON declared in the upstream's `00-contracts/`
- Called from open app only via the user's explicit opt-in (consent capability)

The open app remains operational without the upstream backend — paid features are progressive enhancement, not the substrate.

# Consequences

## 正の効果

- **Real decentralization, not just license labeling.** etzhayyim/root apps survive the operator going dark; AT data lives in PDS, blobs in IPFS, finality on L2.
- **Third-party verifiable.** Anyone can reconstruct app state from MST + IPFS, check the L2 anchor, and proceed without trusting our infrastructure.
- **Censorship-resistant.** No single takedown vector. PDS can be self-hosted; IPFS pins can be replicated; L2 anchor is public.
- **Forkable.** A contributor can fork etzhayyim/root, point at their own PDS / IPFS / L2 contract, and run the entire ecosystem.
- **Aligned with Bonsai/Cultivar metaphor** (ADR-2605091300): each cell carries its own DNA (MST) replicated to the substrate; no central greenhouse.

## 負の効果 / コスト

- **Query performance.** MST traversal is slower than SQL. Mitigations: secondary indexes also stored as MST nodes; client-side caching with IndexedDB; pagination; aggressive use of CRDT-style reducers.
- **Cardinality limits.** Browser memory caps practical MST size. Apps with O(100M) records need sharding strategies (per-time-bucket, per-region, per-tag MSTs).
- **L2 gas costs.** Even at Base's ~$0.001/tx, anchoring every record is too expensive. Batch anchoring (one root every N records or T minutes) is mandatory; the SDK schedules this.
- **Real-time updates.** PDS firehose gives push, but high-volume apps need an event-streaming abstraction. The SDK provides a `subscribe()` over PDS subscribeRepos.
- **SDK is a single point of design coupling.** Every app depends on the SDK API surface; changes need versioning + migration guidance.
- **Refactor cost.** Every existing `60-apps/etzhayyim-project-*` currently uses RW. Each one needs a refactor to MST + IPFS. Estimate: small reference-data app = 1-2 days; AppView like yoro = 1-2 weeks; full open-banking = 1-2 months.

## Migration rollout (incremental, low-risk)

1. **SDK skeleton (this commit alongside ADR)**: `20-actors/etzhayyim-sdk/` with API surface + stub impls. No actual PDS/IPFS/L2 calls yet — just shape and types.
2. **Reference impl**: pick smallest open-* app (e.g., `open-isco` — ~525 occupations, low write rate, no auth, no real-time). Refactor end-to-end as the substrate proof.
3. **Substrate infra** (parallel): `50-infra/{mst-projector, ipfs-pinner, l2-anchor-contract, anchor-cron}` per ADR-2605171800 Stages 3-5.
4. **SDK v0.1.0 release**: based on reference impl learnings, freeze the API surface.
5. **App migration sweep**: refactor remaining open-* / public-* / yoro / atproto / ameno one at a time. Each PR is one app.
6. **Audit pass**: grep for any `risingwave`, `kysely`, `postgres`, `RW`, `vertex_`, `mv_` imports/refs in etzhayyim/root. CI hook to fail PR if any new ones land.

# Alternatives Considered

## A. Keep RW dependency, just label "open"

Per Context — too soft. License-only distinction does not deliver the verifiability the open framing promises.

## B. Self-hosted Postgres per app (no RW, but still central DB)

Each app runs its own Postgres. Still requires trusting the app operator's DB; not third-party verifiable. No improvement over RW from the openness perspective.

## C. Smart contract everything on L2

Pure on-chain. Defeats by gas cost (every read costs money) and by storage cost (L2 storage > IPFS by 100-1000x). MST + IPFS sandwich is the right granularity.

## D. CRDT-only (no MST anchor)

Pure client-side CRDT with peer-to-peer sync. Works for collaboration apps but loses the "third-party verifiable history" property and lacks censorship-resistance against client-side coordinated attacks. MST + L2 anchor is strictly stronger.

# References

- `etzhayyim/root/20-actors/etzhayyim-sdk/` — SDK scaffold (this commit)
- ADR-2605171800 [LangGraph Pregel → PostgresSaver → atproto MST → IPFS → Base L2 anchor pipeline](./2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — pipeline this ADR inverts
- ADR-2605170900 [etzhayyim/root as canonical home](./2605170900-etzhayyim-root-adr-canonical-home.md)
- ADR-2605091300 Bonsai Cultivar Layer — open ecosystem metaphor
- ADR-2605091400 MCP-as-Cell-Membrane / Lexicon Dual-Wire SSoT — Lexicon as contract
- ADR-2605111200 CF Worker Edge-Only — RW Connection K8s-Pod Only — upstream RW topology (contrast)
- AT Protocol MST spec — https://atproto.com/specs/repository
- IPFS spec — https://github.com/ipfs/specs
- Base L2 — https://base.org
