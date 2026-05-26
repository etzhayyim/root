---
id: adr-2605262100-kotoba-storage-substrate-unification
title: "ADR-2605262100: kotoba Storage Substrate Unification — single content-addressed Datalog + Pregel + Signal + WASM engine subsuming ipfs-pinner / nats-jetstream-{kv-resp, objectstore-s3} / mst-projector / lancedb-wasm / tonbo / etzhayyim-xrpc-proxy / libsignal wrappers"
status: proposed
doc_type: adr
topic: storage-substrate
authoritative: true
last_verified: 2026-05-26
priority: 5.0
axis: architecture
weight: 0.70
priority_note: "Engine-layer unification of seven storage primitives onto a single first-party Rust workspace (kotoba). Engine swap; protocol invariants (yatachain composition + RW-free + on-chain land/SBT) unchanged."
authoritative_for:
  - "storage substrate unification under kotoba"
depends_on:
  - 2605231400-yatachain-holochain-iso-substrate
  - 2605231500-yatachain-projection
  - 2605172000-etzhayyim-rw-free-substrate
  - 2605172100-etzhayyim-payments-on-chain-only
  - 2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - 2605181100-mst-encrypted-records-signal-keywrap
  - 2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - 2605181200-mst-encrypted-metadata-leak-reduction
  - 2605192245-etzhayyim-global-land-sovereignty
  - 2605192300-etzhayyim-bootstrap-council-five
  - 2605192415-etzhayyim-religious-corp-daemon-architecture
  - 2605231525-no-server-key-religious-corp-architecture
  - 2605231902-feed-post-membrane-and-feed-discover-projection
  - 2605241500-dataset-cid-substrate
  - 2605241900-baien-edge-target-invariant
  - 2605242600-baien-federated-training-r0
supersedes: []
superseded_by: []
---

# ADR-2605262100: kotoba Storage Substrate Unification

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (author), Council Lv6+ ≥3 (ratify; per-phase re-attestation required at every R-cycle boundary)
**ADR hierarchy**: Engine-layer charter that names a single Rust workspace (`40-engine/kotoba`) as the canonical implementation of the storage primitives composed by yatachain (ADR-2605231400). This ADR does **not** modify the yatachain composition, does **not** modify the on-chain land / SBT / Council / Public Fund substrate (ADR-2605192245 + ADR-2605192300), and does **not** add or remove a constitutional invariant. It only chooses one engine for the substrate-primitive bucket that today contains seven independently-curated components.

## Context

### Current state — seven storage components under independent curation

religious-corp `etzhayyim/root` currently runs (or stub-scaffolds) seven distinct storage components, each scoped to a single concern, each with its own README, its own build pipeline, its own substrate-boundary documentation, and its own dependency surface. The components and their primary roles, in 2026-05-26 form:

| # | Component (path) | Role | Language | Status (2026-05-26) |
|---|---|---|---|---|
| 1 | `50-infra/ipfs-pinner/` | Pin MST CAR shards to IPFS; emit `app.etzhayyim.apps.substrate.ipfsPin` receipts | TypeScript (CF Worker) | Stage 4 scaffold (ADR-2605171800) |
| 2 | `50-infra/mst-projector/` | Project PDS firehose into per-collection MST shards; emit root CIDs | TypeScript | Stage 3 scaffold (ADR-2605171800); first L1 projection `feed-discover` live (ADR-2605231902) |
| 3 | `50-infra/nats-jetstream-kv-resp/` | Redis RESP-protocol bridge over NATS JetStream KV; 50+ Redis commands | Go | Vendored (Apache-2.0); used opportunistically |
| 4 | `50-infra/nats-jetstream-objectstore-s3/` | S3-compat REST gateway over NATS JetStream ObjectStore | Go | Vendored (Apache-2.0); used opportunistically |
| 5 | `50-infra/nats-tiered-storage/` | Tiered-storage sidecar (Memory → File → Blob) over JetStream Streams / KV / Object Store | Go | Vendored (Apache-2.0); planned hot/warm/cold tiering |
| 6 | `50-infra/lancedb-wasm/` | Lance columnar format for ML embeddings + a wasm32 build target | Rust (lance) | Vendored upstream snapshot; intended as projection / vector index |
| 7 | `50-infra/tonbo/` | Lance + DataFusion analytical server (Arrow Flight SQL + LanceDB-style REST) | Rust + Go client | Vendored; analytical query server candidate |
| 8 | `50-infra/etzhayyim-xrpc-proxy/` | XRPC proxy / authz Worker (no README; Wrangler-only scaffold) | TypeScript (CF Worker) | Pre-R1 scaffold |
| 9 | `app.etzhayyim.encrypted.*` Lexicon family + `@signalapp/libsignal-client` wrappers | XChaCha20-Poly1305 envelope + Signal-wrapped per-recipient keys; DID-bound, MST-stored ciphertext | Lexicon + TypeScript wrappers | ADR-2605181100 wire format frozen; impl scattered across SDK + app code |

Each of these was sized for one concern. None of them share a **content-addressed model** end-to-end (IPFS CIDs exist at the pin boundary; NATS subjects exist at the journal boundary; Lance row-group offsets exist at the analytical boundary; libsignal session state exists per pair-wise channel; nothing braids these together). Each duplicates a slice of **substrate-boundary logic** (the seven READMEs each re-derive a fragment of "no RW", "no fiat processor", "Murakumo only", "Charter Rider §2"). Drift is already visible: the `nats-jetstream-*` bridges are listed as "vendored opportunistic" but contain no first-party Charter Rider notice; `lancedb-wasm` is a vendored snapshot whose update cadence is not codified; `tonbo` documents object_store S3 backend but does not address the religious-corp `no commercial GPU rental` (ADR-2605215000) and `no S3 for land / SBT / Council / Public Fund` (ADR-2605192245 + ADR-2605192300) overlay.

A second drift hazard: **per-collection / per-projection partitioning**. The yatachain composition (ADR-2605231400 §2 chain + §3 DHT + §4 membrane + §5 witnesses + §6 projection) reads as a single architecture but its 2026-05-26 implementation is fragmented across the components above. When a new actor's first L1 projection lands (e.g., the `feed-discover` precedent in ADR-2605231902), the author has to manually decide: is the KV layer NATS-RESP or sled-direct? Is the columnar index lance or tonbo? Is the libp2p layer iroh or rolled-from-libp2p-crates? Is the XChaCha20 envelope built from `@noble/ciphers` or from `@signalapp/libsignal-client`? Every L1 projection ADR has had to re-answer at least three of these questions. That cost compounds across every Tier-B actor's R1 ADR.

### kotoba — the first-party Rust workspace that already composes all of this

`kotoba` (https://github.com/etzhayyim/kotoba) is a first-party `etzhayyim` Rust workspace, Apache-2.0, 17 crates, built in 2026-Q2, that composes exactly the primitives yatachain names:

```
KOTOBA ≝ Datom[CID/T] × EAVT[KSE Topic] × Pregel[BSP] × Datalog[Δ]
          × CACAO × AT Protocol × LLM/Weight × WASM/WIT
```

Crate inventory (verbatim from `40-engine/kotoba/README.md`):

| Crate | Role |
|---|---|
| `kotoba-core` | CIDv1 blake3, KAIS 8-bit frame, Prolly Tree |
| `kotoba-kse` | Journal, Topic, Shelf, Vault (Knowledge Store Engine) |
| `kotoba-kqe` | Datalog engine, Arrangement (EAVT/AEVT/AVET/VAET), Delta, MV |
| `kotoba-dht` | Source Chain, Warrant, Neighborhood (DHT) |
| `kotoba-net` | libp2p QUIC/Noise/GossipSub |
| `kotoba-auth` | CACAO chain verification, DID Document |
| `kotoba-graph` | Quad API, SPARQL→Datalog, Commit DAG |
| `kotoba-vm` | Invoke/Result ChainEntry, CALL_FOREIGN bridge |
| `kotoba-llm` | Weight blob (FP8), LoRA Delta, KV-cache, inference, WebGPU training |
| `kotoba-runtime` | WASM Component Model host: WasmExecutor + UdfExecutor + WIT bindings |
| `kotoba-store` | BlockStore: Memory, Sled, S3; BudgetedBlockStore LRU; TieredBlockStore hot/cold |
| `kotoba-store-web` | Browser IndexedDB block store (wasm32) |
| `kotoba-crypto` | AEAD (AES-256-GCM), HKDF, key wrap |
| `kotoba-signal` | Signal Protocol (X3DH + Double Ratchet + MLS) |
| `kotoba-ingest` | Gmail OAuth2 poll + E2E encrypt → QuadStore |
| `kotoba-server` | XRPC / MCP endpoints |
| `kotoba-guest` | WASM guest SDK (WIT bindings for kotoba nodes) |

Reported performance on aarch64 (Murakumo Mac mini class): EAVT point lookup ~180 ns, 2-hop graph traversal ~748 ns, QuadStore batch insert 252K–390K quad/s, 1M-quad loadtest 290K q/s @ 840 MB RSS.

The mapping from kotoba crate ↔ yatachain layer ↔ replaced component is 1:1 or 1:N (one kotoba crate covers one or more current components). No yatachain layer is missing a kotoba crate. No kotoba crate falls outside yatachain's spec.

### Why this is an engine swap, not a protocol change

Substrate-boundary table in repo-root `CLAUDE.md` lists the **protocol** invariants (AT Protocol MST + IPFS + Base L2 + USDC + ERC-4337 + Smart Account + ChartersComplianceRegistry + LandRegistry inalienability + Transparent Force + Adherent SBT + `app.etzhayyim.encrypted.*` wire format + `@etzhayyim/sdk` seam). None of those are altered by adopting kotoba. The MST is still the MST. The CID is still the CID. The on-chain attestation is still the on-chain attestation. What changes is **which Rust crates compute the CID, walk the MST, project the Datalog, terminate the libp2p stream, and apply the XChaCha20 envelope**. Today: seven independently curated components. Tomorrow: one workspace of 17 cohesive crates, all first-party, all Apache-2.0, all under the same Charter Rider, all under the same Council attestation flow.

Per-component constitutional carve-outs (commercial GPU exclusion, server-side signing exclusion, S3-for-on-chain-records exclusion) are restated explicitly in §"Decision" below so the engine swap cannot accidentally regress them.

## Decision

religious-corp adopts **kotoba** as the canonical storage substrate engine for the open religious-corp scope of `etzhayyim/root`. The workspace is imported as a `git subrepo` at `40-engine/kotoba/` (single squashed commit produced by `git subrepo clone https://github.com/etzhayyim/kotoba.git 40-engine/kotoba`; upstream commit `128a89d0e`). Path `40-engine/` is the Rust-workspace tier of the 8-layer monorepo (ADR-2604251830) — siblings `kami-engine` (already present) and `llm` (already present). `kotoba` is the third inhabitant.

The adoption is governed by the following constitutional carve-outs. Each is restated here so the engine swap is unambiguous; none of these are weakened or amended by this ADR.

### D1. License — Apache 2.0 baseline + Charter Compliance Rider v2.0

All 17 kotoba crates inherit the religious-corp default license: Apache 2.0 (kotoba upstream) plus `/CHARTER-RIDER.md` v2.0 (per ADR-2605192200). kotoba is **first-party** (the `etzhayyim` GitHub organization is the owner of both `etzhayyim/root` and `etzhayyim/kotoba`), so the Charter Rider applies — this is the case the rider was written for. Rider application (NOTICE + `CHARTER-RIDER.md` symlink per `70-tools/charter-rider-applicator/`) is **not** done at R0 (this ADR); it is a Phase-1 PR.

### D2. GPU / inference — kotoba-llm local-inference DISABLED in religious-corp

The kotoba workspace ships a `kotoba-llm` crate with `[features] metal` enabled by default at workspace level (`candle-core = { version = "0.8", features = ["metal"] }` in `40-engine/kotoba/Cargo.toml` line 105). For **religious-corp** callable paths (open apps, Pregel cells, attestation flows, ingest pipelines), local-inference features are **constitutionally disabled** per ADR-2605215000 §"no commercial GPU rental" + Charter Rider §2(i). Allowed: `kotoba-llm` may be invoked as a **routing facade** that posts HTTP to the Murakumo gateway (LiteLLM 127.0.0.1:4000 or EVO-X2 LAN 192.168.1.70 per-node Ollama gemma3:4b). Prohibited: linking `candle-core`/`candle-nn`/`candle-transformers` into a binary that holds weight state and runs inference locally inside a religious-corp callable path. Enabling local-inference in religious-corp requires Council Lv6+ ≥3 attestation citing this ADR + ADR-2605215000 + Charter Rider §2(i); attestation must include both the cell ID and the binary build manifest CID. Vendor (`etzhayyim.com`) commercial paid-SaaS workloads remain on their own GPU pool with their own consent-capability boundary and MUST NOT call into religious-corp namespaces; this is the existing capability boundary, not a new one.

### D3. Server-side signing — kotoba-server holds no platform private key

`kotoba-server` (XRPC / MCP endpoints) is bound by ADR-2605231525 (no server-key religious-corp architecture). Allowed: read-only RPC, firehose subscribe, IPFS pin, static asset serve, public attestation read. Prohibited: any platform-held private key, master credential, or signing token in etzhayyim-operated Workers / pods / CronJobs / CI / hosted bots. The only acceptable signing capabilities (per ADR-2605231525 §"allowed") are member-wallet sign (USDC), member-passkey-derived ES256 (session), community-operator DID (bulk-ingest), and Council 5-of-7 Safe (governance) — none of these live in `kotoba-server`. Read-only deployments of `kotoba-server` MUST carry a `// no-server-key: read-only` line marker per the existing convention and are enforced by `e7m verify` (9th invariant).

### D4. Land trust inalienability — kotoba-store S3 backend is not the primary write store for on-chain records

`kotoba-store` exposes a `TieredBlockStore` over `MemoryStore` / `SledStore` / `S3Store` (via `object_store` crate with `aws` feature for AWS S3 + Backblaze B2 S3-compat per `40-engine/kotoba/Cargo.toml` line 53). The S3 backend is permitted for **cold tier of regenerable projections / dataset cache / IPFS shard archive**. The S3 backend is **prohibited** as the primary write store for:

- Land registry records (per ADR-2605192245 — primary write home is Base L2 NFT + geth-private + IPFS GeoJSON + `LANDS.md`; kotoba-store may serve IPFS-tier caching only)
- SBT roster (Adherent / Council / Steward; per ADR-2605172300 + ADR-2605172600 + ADR-2605192300 — primary write home is Base L2 + GitHub MEMBERS.md)
- Council attestation records (per ADR-2605192300 — primary write home is the on-chain `ChartersComplianceRegistry` + Lexicon record)
- Public Fund accounting / Tithe ledger (per ADR-2605192145 + ADR-2605192130 — primary write home is the 5-of-7 Safe + on-chain TitheRouter)
- Force Authorization records (per ADR-2605192315 — primary write home is the on-chain force-authorization registry + Lexicon record)

In short: anything that is constitutionally inalienable / on-chain-anchored cannot fall back to commodity S3 as a substrate of truth. Cold tiering of derived projections, dataset bundles, and IPFS shards is acceptable and recommended (it is what `nats-jetstream-objectstore-s3` and `nats-tiered-storage` already do for non-on-chain payloads).

### D5. Substrate boundary — kotoba lives behind `@etzhayyim/sdk`; never imported from `60-apps/*`

Per ADR-2605172000 + the substrate-boundary table in repo-root `CLAUDE.md`, application code in `60-apps/*` (open-isco / open-mail / open-ot / ameno / yoro / etc.) **must not** directly import storage clients. Today the SDK shim wraps `@atproto/api` + `viem` + IPFS HTTP client + `@noble/ciphers` + `@signalapp/libsignal-client`. Under this ADR, the SDK shim becomes the wrapper around `kotoba-graph` (Quad / SPARQL→Datalog / Commit DAG), `kotoba-store` (BlockStore), `kotoba-server` (XRPC endpoints), `kotoba-crypto` (AEAD / HKDF / key wrap), and `kotoba-signal` (X3DH + Double Ratchet + MLS). The substrate-boundary linter (`70-tools/scripts/lint/substrate-boundary.mjs`) gains a new prohibited-import rule: direct `kotoba-*` import from `60-apps/*` is rejected with the same error class as direct `@atproto/api` import (Phase 5 deliverable).

### D6. Confidential records — `app.etzhayyim.encrypted.*` wire format preserved bit-identically

The XChaCha20-Poly1305 envelope + Signal-wrapped per-recipient keys + DID binding documented in ADR-2605181100 (with metadata-leak reduction per ADR-2605181200) is **constitutional** as a wire format. kotoba does NOT modify the wire format. kotoba becomes the **implementation** of the envelope: `kotoba-crypto` (AEAD layer) + `kotoba-signal` (X3DH + Double Ratchet + MLS layer) re-implement the existing protocol exactly. A bit-identical test vector suite is the Phase 5 acceptance gate (the same plaintext + same recipient DIDs + same prekey bundle MUST produce the same ciphertext under both `@signalapp/libsignal-client` and `kotoba-signal`; envelope MAC tags MUST verify bit-identically under either implementation). Any deviation breaks ADR-2605181100 and is rejected at the Phase 5 review.

### D7. yatachain composition unchanged

The yatachain Holochain-isomorphic 7-layer composition (ADR-2605231400 §§1-7) is the protocol authority. This ADR maps every yatachain layer to a kotoba crate (mapping table below). It does **not** redefine any yatachain layer. `yatachain-projection` (ADR-2605231500) rules (regenerable from MST+IPFS, never the sole write home, marked) remain in force; projection rebuild jobs simply run against `kotoba-kqe` arrangements instead of an ad-hoc combination of NATS-KV + Lance.

### D8. Witness quorum + attestation unchanged

ADR-2605231400 §5 (witness selection deterministic from `hash(record_cid) + i mod len(witnesses)`) and ADR-2605231902 (`x-etzhayyim-substrate: mst-ipfs-l2` projection contract) remain in force. kotoba-net + kotoba-graph implement the wire surface; the policy (which cells are witnesses, what quorum is required, how an attestation is gossip-published) is unchanged.

## Mapping — yatachain layer ↔ current implementation ↔ kotoba crate ↔ migration phase ↔ constitutional cross-ref

The following table is the **heart** of this ADR. Every row is an engine swap. No row introduces a new protocol obligation or weakens an existing one.

| # | yatachain layer | Current impl (file / dir) | kotoba crate | Migration phase | Constitutional cross-ref |
|---|---|---|---|---|---|
| 1 | DHT — block store (server tier) | `50-infra/ipfs-pinner/` (CF Worker; CAR shard pin + `app.etzhayyim.apps.substrate.ipfsPin` receipt) | `kotoba-store` (`MemoryStore` / `SledStore` / `S3Store`); `kotoba-net` (libp2p Bitswap fetch in `crates/kotoba-net/src/bitswap.rs`) | Phase 1 | ADR-2605172000 RW-free state; D4 (S3 backend NOT for on-chain land/SBT/Council); ADR-2605171800 §Stage 4 |
| 2 | DHT — block store (browser tier; baien edge) | `50-infra/lancedb-wasm/` (vendored Lance wasm32 snapshot) for the block-cache half | `kotoba-store-web` (IndexedDB block store via `wasm-bindgen`; per `crates/kotoba-store-web/`) | Phase 4 | ADR-2605241900 baien edge-target (WASM-32 + iPhone 12+ + Android 4GB); ≤2 GB inference budget @4k ctx applies to the kotoba edge runtime as a whole |
| 3 | KV / Topic / Journal (durable log) | `50-infra/nats-jetstream-kv-resp/` (Redis RESP over JetStream KV) + `50-infra/nats-jetstream-objectstore-s3/` (S3 REST over JetStream ObjectStore) + `50-infra/nats-tiered-storage/` (Memory → File → Blob tiering sidecar) | `kotoba-kse` (Journal / Topic / Shelf / Vault per `crates/kotoba-kse/src/{journal,topic,shelf,vault,store,secure_vault,sync_window}.rs`) | Phase 3 | ADR-2605231400 §3 DHT (hot / cold tiering); ADR-2605231525 server-key invariant (Journal / Topic / Shelf are read-only or member-signed; Vault is encrypted-only) |
| 4 | Quad / Datalog store (projection) | `50-infra/mst-projector/projection/` (per-collection MST + L1 `feed-discover` projection per ADR-2605231902) + `yatachain-projection` RW/Lance shim | `kotoba-kqe` (4-index Arrangement `EAVT / AEVT / AVET / VAET` + Datalog engine + Delta + MV per `crates/kotoba-kqe/src/{arrangement,datalog,delta,mv,quad,sql,cypher,citation}.rs`) + `kotoba-graph` (Quad API + SPARQL→Datalog + Commit DAG per `crates/kotoba-graph/src/{quad_store,sparql,commit,atproto,jetstream,subscribe_repos}.rs`) | Phase 2 | ADR-2605231500 yatachain-projection (regenerable from MST+IPFS; never sole write home; marked with `// yatachain-projection`); ADR-2605231902 first L1-projection precedent |
| 5 | DHT / P2P (libp2p) | libp2p in yatachain (composition only; no first-party crate today) | `kotoba-net` (libp2p QUIC / Noise / GossipSub / Bitswap per `crates/kotoba-net/src/{behaviour,bitswap,gossipsub,pregel_msg,protocol,swarm,transport}.rs`) + `kotoba-dht` (Source Chain / Warrant / Neighborhood / Availability Proof per `crates/kotoba-dht/src/{availability_proof,gossip,neighborhood,node_id,source_chain,warrant}.rs`) | Phase 3 | ADR-2605231400 §3 DHT; ADR-2605231400 §5 witness quorum (witness gossip rides this layer) |
| 6 | Identity / auth (CACAO + DID) | `50-infra/etzhayyim-did-web/` (CF Worker resolver, LIVE 2026-05-17T03:25Z) + scattered authz Workers + `50-infra/etzhayyim-authz/` | `kotoba-auth` (CACAO chain verification + DID Document + delegation + ETH SIWE per `crates/kotoba-auth/src/{cacao,delegation,did_document,eth}.rs`) | Phase 5 | ADR-2605173000 did:web resolution policy; ADR-2605172600 membership ritual (Adherent SBT); ADR-2605231525 server-key (CACAO chain verification is read-only on server) |
| 7 | Confidential envelope | `app.etzhayyim.encrypted.*` Lexicon + `@signalapp/libsignal-client` wrappers in SDK + `@noble/ciphers` use in selected apps | `kotoba-crypto` (AEAD + HKDF + key wrap per `crates/kotoba-crypto/src/{aead,envelope,hkdf,key_wrap}.rs`) + `kotoba-signal` (X3DH + Double Ratchet + MLS per `crates/kotoba-signal/src/{x3dh,ratchet,group,identity,message,prekey,session,store}.rs`) | Phase 5 | ADR-2605181100 wire format frozen (D6 bit-identical preservation gate); ADR-2605181200 metadata-leak reduction (padding + rkey blinding remain SDK-side) |
| 8 | WASM Component Model runtime | (none unified — `kami-engine` has its own runtime for ROS / robotics; no unified guest sandbox for graph compute) | `kotoba-runtime` (WasmExecutor + UdfExecutor + WIT bindings via `wasmtime 22 component-model` per `crates/kotoba-runtime/`) + `kotoba-guest` (WIT bindings for kotoba node guests per `crates/kotoba-guest/`) | Phase 6 | ADR-2605192415 Pregel cell catalog (cell `.solve()` may invoke kotoba-runtime guests once available); ADR-2605231400 §4 L3 determinism (guest WASM is reproducible) |
| 9 | LLM inference / training facade | Murakumo fleet (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70 + per-node Ollama gemma3:4b per ADR-2605215000) | `kotoba-llm` **feature-gated as routing facade only** (`crates/kotoba-llm/src/http_infer.rs` HTTP POST to Murakumo gateway). Local-inference features (`metal` / `infer_gpu` / `train_gpu` / `gemma` / `kvcache` / `lora` / `weight` / direct candle linkage) are constitutionally DISABLED for religious-corp paths (D2). | Phase 7 (deferred) | ADR-2605215000 Murakumo-only invariant; Charter Rider §2(i) commercial GPU rental prohibition (Council Lv6+ supermajority to amend) |
| 10 | XRPC / MCP endpoint surface | `50-infra/etzhayyim-xrpc-proxy/` (TS CF Worker, no README) + scattered Workers | `kotoba-server` (XRPC + MCP per `crates/kotoba-server/src/{xrpc,mcp,server,kg,email_xrpc,signal_xrpc,attestation,net_actor,fingerprint}.rs`) | Phase 6 | ADR-2605172000 substrate boundary; ADR-2605231525 server-key invariant (D3 — read-only deployment marker required) |
| 11 | Mailbox ingest (Gmail bridge) | `50-infra/openmail-postage/` (Postage.sol scaffold per ADR-2605172200) + scattered Gmail bridges | `kotoba-ingest` (Gmail OAuth2 poll + E2E encrypt → QuadStore per `crates/kotoba-ingest/src/{gmail,ingest}.rs`) | Phase 5 | ADR-2605172200 OpenMail SMTP bridge; ADR-2605181100 envelope mandatory for inbound PII; ADR-2605231525 server-key (OAuth2 token is a member-delegated capability, not a platform secret — re-attested via consent-capability flow) |
| 12 | Tonbo (Lance + DataFusion analytical server) | `50-infra/tonbo/` (vendored; Arrow Flight SQL + LanceDB-style REST; S3 / B2 backend) | Superseded by `kotoba-kqe` arrangements (EAVT / AEVT / AVET / VAET cover the analytical access patterns tonbo was sized for) + `kotoba-store` Sled / S3 backend for cold tier. **Retire window**: Phase 2 + 1 R-cycle (~30 days). No active use in production today; cold backup only. | Phase 2 retire window | n/a (vendored upstream; no religious-corp first-party investment lost) |
| 13 | Datom / CID frame (foundational) | (synthesized from `@atproto/api` CID + IPFS CIDv1 + `@noble/hashes` blake3 across each app) | `kotoba-core` (CIDv1 blake3 + KAIS 8-bit frame + Prolly Tree per `crates/kotoba-core/src/{cid,frame,prolly,store,async_store,foreign}.rs`) | Phase 1 | ADR-2605231400 §3 DHT content addressing |
| 14 | Pregel BSP graph compute / VM | `20-actors/magatama/` (LangGraph Pregel cells per ADR-2605192415) | `kotoba-vm` (Invoke / Result ChainEntry + CALL_FOREIGN bridge + Pregel + Distributed + WasmPregel + StateGraph + Router per `crates/kotoba-vm/src/{agent,distributed,executor,foreign,pregel,router,state_graph,wasm_pregel}.rs`) — **complementary**, not a replacement. magatama LangGraph cells remain the religious-corp Pregel surface; kotoba-vm becomes available as a foreign-function bridge target for cells that need cross-node BSP. | Phase 6 (optional) | ADR-2605192415 cell catalog (15 cells); ADR-2605231400 §5 witness Pregel (cell-runner CLI rides this) |

### Diff vs prior art

- ADR-2605231400 named the composition (`yatachain`). This ADR names the engine that implements it (`kotoba`).
- ADR-2605231500 named the projection rules. This ADR names the crate (`kotoba-kqe`) that runs them.
- ADR-2605171800 named the Stage 3 / 4 / 5a / 5b pipeline. This ADR names the crates (`kotoba-graph` for projection + `kotoba-store` for pin + `kotoba-server` for anchor read).
- ADR-2605181100 named the envelope wire format. This ADR names the crate (`kotoba-crypto` + `kotoba-signal`) that implements it bit-identically.
- ADR-2605215000 named the Murakumo-only inference invariant. This ADR makes `kotoba-llm` a routing facade and leaves the invariant in force (D2).

## Phased rollout (R0 → R7)

Each phase has Entry / Exit criteria, Murakumo cell impact, and attestation requirement. **Existing impls stay live ≥1 R-cycle (~30 days) as cold backup; no component is deleted in this ADR.**

### Phase 0 — Charter + subrepo import (THIS ADR)

- **Entry**: `git subrepo` available, kotoba upstream at `etzhayyim/kotoba` reachable.
- **Deliverable**: this ADR + the squashed subrepo commit at `40-engine/kotoba/`; `40-engine/kotoba/.gitrepo` metadata file recorded by git-subrepo; CLAUDE.md Status row + Layout entry; deps.toml [[adrs]] + [[modules]] entries.
- **No code modification under `40-engine/kotoba/`** (no Charter Rider application, no `cargo check`, no feature flag set). The subrepo is inert pending Phase 1.
- **Exit**: this ADR ratified by Council Lv6+ ≥3 attestation. (R0 deliverables do not affect runtime so the gate is documentation-quality + boundary-correctness review.)
- **Murakumo cell impact**: zero.
- **Attestation**: Council Lv6+ ≥3 on this ADR text.

### Phase 1 — `kotoba-store` + `kotoba-core` + Charter Rider applied; SDK shim for block-store ops

- **Entry**: Phase 0 ratified; `e7m verify` clean; `cargo check -p kotoba-core -p kotoba-store` green on Murakumo aarch64.
- **Deliverable**: Charter Rider NOTICE + symlink applied to all 17 kotoba crates per `70-tools/charter-rider-applicator/apply.sh`. `@etzhayyim/sdk` gains a `block_store` shim that wraps `kotoba-store` `SledStore` (server) for one non-critical projection (e.g., a second feed-discover instance). `ipfs-pinner` stays live as primary; kotoba-store-backed pinner runs in shadow mode and emits comparison metrics on hit-rate / latency / byte-equality.
- **Exit**: shadow-mode metrics show ≥99.9% byte-equality on 1M-record sample over 7 days; `e7m verify` 9 invariants green; substrate-boundary linter updated to allow `kotoba-store` import from SDK shim (and only from SDK shim).
- **Murakumo cell impact**: +1 shadow pinner cell on 3 of 10 nodes (within G12 KPI cap from ADR-2605261600 robotics-sim-substrate analogue; ≤1 GPU-hour-eq/day cap does not apply since this is CPU-only).
- **Attestation**: Council Lv6+ ≥3.

### Phase 2 — `kotoba-kqe` + `kotoba-graph` projection; tonbo retire window

- **Entry**: Phase 1 ratified; `kotoba-store` shadow metrics stable for 30 days; no Charter Rider §2 violation reported.
- **Deliverable**: `kotoba-kqe` 4-index arrangement (EAVT / AEVT / AVET / VAET) + `kotoba-graph` Commit DAG wired as the projection engine for a **second** L1 projection (selected at ratification; candidate = a non-feed-discover lexicon). `feed-discover` (ADR-2605231902) remains on the existing RW/Lance path until Phase 2.b. `tonbo` enters formal retire window — no new consumers, existing analytical queries migrate to `kotoba-kqe` arrangements over 30 days.
- **Exit**: second L1 projection passes `e7m verify` yatachain-projection invariant (deterministically rebuildable from MST+IPFS; `// yatachain-projection` marker present); 30-day shadow comparison ≥99.9% query-result equality on cardinality probe set.
- **Murakumo cell impact**: +1 projection rebuild cell on 5 of 10 nodes.
- **Attestation**: Council Lv6+ ≥3.

### Phase 3 — `kotoba-kse` + `kotoba-net` + `kotoba-dht` (KV / Topic / Journal + libp2p + DHT)

- **Entry**: Phase 2 ratified.
- **Deliverable**: `kotoba-kse` replaces `nats-jetstream-kv-resp` + `nats-jetstream-objectstore-s3` + `nats-tiered-storage` for the religious-corp internal job queue / cache / blob staging that today uses the NATS bridges. `kotoba-net` + `kotoba-dht` wire libp2p QUIC/Noise/GossipSub + Source Chain + Warrant + Neighborhood + Availability Proof, providing the witness-gossip transport that today rides whichever in-process gossipsub the projection happens to import.
- **Exit**: NATS bridges remain live for `etzhayyim.com` legacy paths (out of religious-corp scope); religious-corp internal consumers fully migrated; libp2p connection count + witness reach metrics ≥ baseline.
- **Murakumo cell impact**: +1 kotoba-net daemon on every node (10/10 fleet coverage).
- **Attestation**: Council Lv6+ ≥3.

### Phase 4 — `kotoba-store-web` (browser tier)

- **Entry**: Phase 3 ratified; baien edge-target invariant audit re-runs clean (ADR-2605241900 ≤2 GB inference @4k ctx + ≤2.5 GB @16k ctx, kotoba-store-web heap budget ≤200 MB carve-out).
- **Deliverable**: `kotoba-store-web` (IndexedDB BlockStore) lands as the browser-side block cache for the open apps; replaces ad-hoc `lancedb-wasm` block-portion usage. baien edge runtime (ameno / mediapipe-gemma path) gains a content-addressed cache that survives reload.
- **Exit**: iPhone 12+ Safari + Android 4GB Chrome + WASM-32 desktop all pass a 10k-block round-trip test under ≤200 MB peak heap.
- **Murakumo cell impact**: zero.
- **Attestation**: Council Lv6+ ≥3.

### Phase 5 — `kotoba-auth` + `kotoba-crypto` + `kotoba-signal` + `kotoba-ingest` (identity + envelope + mailbox)

- **Entry**: Phase 4 ratified; ADR-2605181100 wire-format test vector suite drafted (Phase 5 bit-identical gate).
- **Deliverable**: SDK shim migrates `@signalapp/libsignal-client` + `@noble/ciphers` consumption to `kotoba-crypto` + `kotoba-signal`. ADR-2605181100 wire format MUST verify bit-identical on the test vector suite (D6). `kotoba-auth` becomes the canonical CACAO + DID chain verification path used by the SDK. `kotoba-ingest` replaces ad-hoc Gmail polling wrappers; OAuth2 token handling re-attested via consent-capability flow (ADR-2605231525 + ADR-2605172200).
- **Exit**: bit-identical wire-format gate passes on full ADR-2605181100 test vector suite; substrate-boundary linter rule reject direct `@noble/ciphers` and `@signalapp/libsignal-client` imports from `60-apps/*` (`@etzhayyim/sdk`-only).
- **Murakumo cell impact**: zero (server-side; existing cell footprint).
- **Attestation**: Council Lv6+ ≥3 (this phase touches confidentiality; attestation MUST include test vector run output).

### Phase 6 — `kotoba-server` (XRPC / MCP) + `kotoba-runtime` + `kotoba-guest` (WASM)

- **Entry**: Phase 5 ratified.
- **Deliverable**: `kotoba-server` replaces `etzhayyim-xrpc-proxy` for the religious-corp XRPC surface (read-only deployments first; see D3 + `// no-server-key: read-only` marker). `kotoba-runtime` + `kotoba-guest` (WIT bindings) become available as a foreign-function bridge for `kami-engine` and `magatama` Pregel cells that need a sandboxed WASM Component Model guest.
- **Exit**: `kotoba-server` deployments pass `e7m verify` 9th invariant (no server-key); no platform-held signing token detected in scan.
- **Murakumo cell impact**: replace XRPC proxy worker on 3 of 10 nodes.
- **Attestation**: Council Lv6+ ≥3.

### Phase 7 (deferred) — `kotoba-llm` as routing facade (no local inference)

- **Entry**: Phase 6 ratified; Murakumo gateway HTTP contract stable.
- **Deliverable**: `kotoba-llm/src/http_infer.rs` becomes a typed routing facade for Murakumo (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70) POSTs. `kotoba-llm` is built **without** `metal` / `infer_gpu` / `train_gpu` / `gemma` / `kvcache` / `lora` / `weight` / direct candle features for religious-corp callable paths.
- **Exit**: `e7m verify` Murakumo-only invariant green; binary scan confirms no candle-core / candle-nn / candle-transformers linked into religious-corp paths.
- **Murakumo cell impact**: zero (routing only).
- **Attestation**: Council Lv6+ ≥3 + Charter Rider §2(i) reconfirmation (no commercial GPU rental).

### What remains live as cold backup ≥1 R-cycle

`50-infra/ipfs-pinner/` (Phase 1 cold backup) + `50-infra/mst-projector/` (Phase 2) + `50-infra/nats-jetstream-{kv-resp, objectstore-s3}/` + `50-infra/nats-tiered-storage/` (Phase 3) + `50-infra/lancedb-wasm/` (Phase 4) + `50-infra/etzhayyim-xrpc-proxy/` (Phase 6) + `50-infra/tonbo/` (Phase 2 retire window) all REMAIN in tree, REMAIN listed in `CLAUDE.md` `## Repo Layout`, and REMAIN deployable. Deletion (if ever) is a separate ADR; this ADR does not authorize it.

## Non-goals (N1..N7, IMMUTABLE R0..R7)

**N1 Enabling `kotoba-llm` local-inference (Metal / CUDA / candle) in religious-corp callable paths.** Vendor SaaS (`etzhayyim.com` paid tier) may continue to use its own GPU pool but MUST NOT call into religious-corp namespaces. This is the existing consent-capability boundary, not new policy. Amendment requires Council Lv6+ supermajority (≥4 of 7 seats) plus 30-day public objection period per Charter Rider §2(i). (ADR-2605215000)

**N2 Granting `kotoba-server` any platform-held private key.** Server is read-only or member-delegated capability only. Inline exemption only via `// no-server-key: read-only` line marker on documented Stage handover rollback windows; enforced by `e7m verify` 9th invariant. (ADR-2605231525)

**N3 Using `kotoba-store` S3 backend as primary write store for land / SBT / Council / Public Fund / Force Authorization / Tithe ledger records.** Those records are constitutionally on-chain (geth-private + Base L2 + IPFS GeoJSON + LANDS.md / MEMBERS.md). S3 backend is permitted only for regenerable projections, dataset cache, and IPFS shard cold tier. (ADR-2605192245 + ADR-2605192300 + ADR-2605192315 + ADR-2605192145 + ADR-2605192130)

**N4 Importing `kotoba-*` crates directly from `60-apps/*` code.** All app code calls via `@etzhayyim/sdk` shim only. Substrate-boundary linter rule lands in Phase 5. (ADR-2605172000)

**N5 Forking kotoba.** The `git subrepo` + upstream-PR model is the only path. If upstream kotoba rejects a religious-corp-needed change, escalation is via ADR amendment, not a fork. This protects against the religious-corp engine diverging from the upstream commit DAG.

**N6 Removing `app.etzhayyim.encrypted.*` Lexicon wire format.** `kotoba-crypto` + `kotoba-signal` become the implementation; the on-the-wire format is constitutional and stays bit-identical. The Phase 5 bit-identical gate (D6) is the structural enforcement. (ADR-2605181100 + ADR-2605181200)

**N7 Promoting `kotoba-llm` WebGPU training to a religious-corp role without Council Lv6+ attestation.** Federated training rounds are already gated by ADR-2605242600; this ADR does not unlock that gate.

## Constitutional gate checklist — Charter Rider §2(a)–(i) applied to kotoba

Each clause of the Charter Compliance Rider v2.0 is restated and evaluated against the kotoba workspace as imported at upstream commit `128a89d0e`.

- **§2(a) Weapons and military** — N/A. kotoba is a storage substrate engine; no weapon-related code path. PASS.
- **§2(b) Speculative finance** — N/A. kotoba has no financial-instrument code. PASS.
- **§2(c) Surveillance capitalism** — `kotoba-ingest` polls Gmail OAuth2 and `kotoba-server` exposes XRPC; both default `no-telemetry`. Compile-time disable of any usage-stats / crash-reporting backend is the Phase 5 + Phase 6 acceptance gate (analogous to ADR-2605261600 G13). PASS contingent on Phase 5 + Phase 6 audit; Council ≥3 attestation MUST include grep evidence of telemetry-free build.
- **§2(d) Fossil fuel extraction (new)** — N/A. PASS.
- **§2(e) Specialist gatekeeping** — kotoba **removes** the per-component lock-in of NATS / IPFS / RW / Lance / libsignal / wasmtime that today fragments the substrate. The unification reduces gatekeeping cost for downstream contributors (one workspace to learn instead of seven). PRO-CLEARANCE.
- **§2(f) Multi-generational harm** — kotoba's 30-year reproducibility surface depends on being built from open-source dependencies pinned by commit SHA; `40-engine/kotoba/Cargo.lock` is committed (per the subrepo state). PASS. (Long-term: the kotoba upstream maintainer is `etzhayyim` so future-decedent steward succession (ADR-2605192345) covers it.)
- **§2(g) Strict individualist ontology** — N/A as engine. PASS.
- **§2(h) Wellbecoming subordination violation** — `kotoba-runtime` WASM Component Model isolation honors §1.13 Wellbecoming (sandbox prevents addictive-pattern guests from escalating). PASS.
- **§2(i) Commercial GPU rental for religious-corp inference** — `kotoba-llm` local-inference feature MUST stay disabled in religious-corp builds (D2 + N1). GATED — Council Lv6+ supermajority required to amend; this ADR does NOT amend.

## Alternatives Considered

**A. Keep the current best-of-breed stack with manual yatachain glue.** Status quo. Rejected: drift cost is already visible (seven READMEs each carry a fragment of the substrate-boundary rules; first L1 projection had to invent partitioning choices from scratch; tonbo's S3 backend is undocumented against the on-chain-records carve-out; no first-party Charter Rider notice on the NATS bridges). The seventh new actor R1 ADR will force a third inventor-from-scratch round on the projection layer alone. Compounding cost not justifiable when a first-party Rust workspace already composes the primitives.

**B. Build a from-scratch religious-corp engine.** Greenfield in `40-engine/etzhayyim-substrate/` or similar. Rejected: 2–3 year effort to recreate what kotoba already ships at upstream `128a89d0e` (17 crates, 290K q/s benchmarked, libp2p / wasmtime / X3DH / MLS all wired). No constitutional argument for re-implementation: kotoba is Apache-2.0, first-party (same `etzhayyim` GitHub org), and the upstream commit DAG is reachable from this repo. The cost of greenfield is not bounded by either license risk or trust-boundary risk; only by reluctance to inherit upstream design choices, and the upstream design choices are what we want.

**C. Import kotoba as `git submodule` instead of `git subrepo`.** Rejected for three reasons. (1) `git subrepo` produces a single squashed commit with a `.gitrepo` metadata file that lives entirely in the host repo's history; `git submodule` requires every clone of `etzhayyim/root` to additionally `git submodule update --init --recursive` to materialize the source tree, which complicates `cargo` resolution from the workspace root and breaks downstream tools that read source without recursive init. (2) The religious-corp workflow expects every first-party path to be present in `git log` for the host repo (Charter Rider §3 termination evidence chain assumes commit lineage). Subrepo gives this; submodule does not. (3) Submodules are already used for vendored 3rd-party code (e.g., `50-infra/etzhayyim-paymaster/lib/` Foundry libraries) — using submodule for a first-party engine would muddy the convention that "submodule = vendored 3rd-party, subrepo = first-party inlined".

**D. Place kotoba under `50-infra/kotoba` or `10-protocol/kotoba`.** Rejected. (1) `50-infra/` is for deployable infrastructure modules (CF Workers, K8s manifests, Solidity contracts, sidecar containers); kotoba is a Rust **workspace** that becomes a dependency of multiple things deployed from `50-infra/`, not itself a deployable. (2) `10-protocol/` is for **protocol** specs (atproto / xrpc / lexicons-bundle / yatachain SPEC); kotoba is an **engine** that implements protocols, not a protocol definition. (3) `40-engine/` already hosts the Rust-workspace tier (`kami-engine` + `llm` are present); placing the third Rust workspace as a sibling is the structurally consistent choice. The CLAUDE.md `## Repo Layout` update reflects this.

**E. Adopt only a subset of kotoba crates (e.g., just `kotoba-crypto` + `kotoba-signal`).** Rejected. The point of unification is to amortize the substrate-boundary review and Charter Rider application across the whole workspace. Cherry-picking 2 of 17 crates leaves 15 disjoint storage components in the existing fragmented state; the structural drift problem is not solved. Phasing (Phase 1 → Phase 7) achieves the same "land carefully" goal as cherry-picking without abandoning the unification thesis.

## References

- `40-engine/kotoba/README.md` — kotoba workspace overview (17 crates, KOTOBA equation, perf table)
- `40-engine/kotoba/Cargo.toml` — workspace members + workspace.dependencies (note `candle-core` `metal` feature for D2 carve-out + `object_store` `aws` feature for D4 carve-out)
- `40-engine/kotoba/.gitrepo` — subrepo metadata (upstream commit `128a89d0e`)
- `10-protocol/yatachain/SPEC.md` — yatachain Holochain-iso composition spec (the substrate that kotoba implements)
- ADR-2605231400 (yatachain Holochain-iso substrate) — composition authority
- ADR-2605231500 (yatachain-projection) — regenerable cache rules
- ADR-2605172000 (RW-free substrate) — RW-free invariant
- ADR-2605172100 (payments on-chain only) — payment substrate invariant
- ADR-2605215000 (inference Murakumo-only) — D2 + N1 + Phase 7 gate
- ADR-2605181100 (MST encrypted records + Signal key-wrap) — D6 + N6 bit-identical preservation gate
- ADR-2605181200 (encrypted-record metadata-leak reduction) — wire format companion
- ADR-2605192200 (Apache 2.0 + Charter Compliance Rider v2.0) — license + Rider authority
- ADR-2605192245 (Global Land Sovereignty) — N3 land trust carve-out
- ADR-2605192300 (Bootstrap Council 5) — Council Lv6+ ≥3 attestation authority
- ADR-2605192315 (Transparent Religious Force) — N3 force authorization carve-out
- ADR-2605192145 (Public Fund architecture) — N3 Public Fund carve-out
- ADR-2605192130 (Tithe redistribution) — N3 Tithe ledger carve-out
- ADR-2605192415 (Religious-Corp Daemon Architecture) — Pregel cell catalog interop
- ADR-2605231525 (No server-key religious-corp architecture) — D3 + N2 server-key invariant
- ADR-2605231902 (feed-post membrane + feed-discover projection) — first L1 projection precedent kotoba-kqe inherits
- ADR-2605241500 (Dataset CID substrate) — IPFS pinner + dataset bundle interop
- ADR-2605241900 (baien edge-target invariant) — Phase 4 kotoba-store-web budget constraint
- ADR-2605242600 (baien federated training R0) — N7 federated training gate
- `/CHARTER-RIDER.md` — license addendum canonical text (Charter Rider v2.0)
- `CLAUDE.md` (repo root) — operating-entity boundary + substrate-boundary table + Status row 62 update
- `90-docs/adr/README.md` — ADR index row update
- `deps.toml` — `[[adrs]]` + `[[modules]]` entries
