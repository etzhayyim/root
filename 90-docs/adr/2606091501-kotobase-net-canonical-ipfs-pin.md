---
id: adr-2606091501-kotobase-net-canonical-ipfs-pin
renumbered_from: "2606091500"
title: "ADR-2606091501: kotobase.net is the canonical IPFS pin service (repo-wide); supersedes the kotobase.etzhayyim.com naming"
status: active
doc_type: adr
topic: ipfs-pin-canonicalization
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Names the single canonical remote IPFS pin endpoint for the whole repo. The kotoba node is its own IPFS node (self-pins its local block tier); kotobase.net is the durable, content-addressed remote pin that survives pod GC and holds >1 GB extended pins. Pins the endpoint into structured config (deps.toml [platform.kotobase_pin]) + the e7m-dataset pinner + the kotoba-store remote-pin client, so it is no longer carried only in prose. Supersedes the older kotobase.etzhayyim.com domain (kotoba.etzhayyim.com is pruned / read-only)."
authoritative_for:
  - canonical remote IPFS pin endpoint (kotobase.net)
  - deps.toml [platform.kotobase_pin] config block
  - kotoba-store IpfsPinClient remote-pin default (KOTOBA_IPFS_PIN_ENDPOINT)
  - e7m-dataset publish-ipfs remote-pin fanout (ETZ_KOTOBASE_PIN)
  - ipfs-pinner kotobase provider (MST-CAR remote pin, ETZ_PINNER_PROVIDERS=kubo,kotobase)
depends_on:
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2606011330
related:
  - adr-2606041130-kotoba-b2-blockstore-cold-pin
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
supersedes: []
superseded_by: []
---

# ADR-2606091501: kotobase.net is the canonical IPFS pin service (repo-wide)

**Status**: active
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

# Context

The pin layer was named inconsistently across the repo:

- The kotoba node **is its own IPFS node** — `kotoba-store` self-pins its
  local block tier (`TieredBlockStore` + `KuboBlockStore` + a fire-and-forget
  `IpfsPinClient` against the pod-local Kubo-compatible API, default
  `http://localhost:5001`). It is NOT dependent on an external Kubo daemon for
  the hot path.
- A **separate durable remote pin** holds CIDs beyond the node's own ~1 GB
  free allowance and guarantees retention across pod GC. The most recent
  decision (session note in `deps.toml`) settled this as **`kotobase.net`**:
  the apex `com.etzhayyim.apps.kotoba.block.put` path pins member-signed,
  content-addressed blocks to `kotobase.net` as the canonical store, and
  `kotoba.etzhayyim.com` was pruned to read-only.

But `kotobase.net` lived only in prose `status_note`s. Structured config and
code still pointed elsewhere:

- `deps.toml` `[platform.ipfs]` + `[platform.dataset_substrate]` named only the
  **local** Kubo (`simeonnomac-mini.local:5001` / `127.0.0.1:5001`); there was
  no canonical remote-pin block.
- `70-tools/e7m-dataset` (the dataset-CID pinner, ADR-2605241500) ran
  `ipfs add` against local Kubo and **never pushed to a remote pin** at all.
- `40-engine/kotoba/crates/kotoba-store` (`ipfs_pin.rs` / `kubo_store.rs`) and
  `kotoba-server` (`server.rs`) still referred to **`kotobase.etzhayyim.com`**
  in comments, and the remote-pin client was opt-in-only
  (`from_pin_env()` returned `None` unless `KOTOBA_IPFS_PIN_ENDPOINT` was set).

IPFS is a **subordinate cold/interop backstop** under the kotoba Datom log
(ADR-2605262130 + ADR-2605312345 + ADR-2606011330) — durability authority is
`kotoba-dht`, not IPFS. This ADR does not change that ordering; it only fixes
*which remote pin endpoint* the repo names, and pins that name into config +
code so it stops drifting.

# Decision

**`kotobase.net` is the canonical remote IPFS pin service, repo-wide.**

1. **deps.toml** gains a canonical `[platform.kotobase_pin]` block (endpoint,
   Kubo-compatible API surface, role, env vars, this ADR id). `[platform.ipfs]`
   role note and `[platform.dataset_substrate]` reference it.

2. **kotoba-store** (`IpfsPinClient::from_pin_env`) defaults its remote-pin
   endpoint to `https://kotobase.net` when `KOTOBA_IPFS_PIN_ENDPOINT` is unset —
   so the kotobase pin fanout is **on by default**, opt-out via
   `KOTOBA_IPFS_PIN_ENDPOINT=off|none|disabled`. The remote pin remains
   fire-and-forget/best-effort (a pin failure only warns; it never fails a
   `put`). Comments renamed `kotobase.etzhayyim.com` → `kotobase.net`.

3. **e7m-dataset** `publish-ipfs` gains a remote-pin fanout: after the local
   `ipfs add`, every object CID + the map CID is pinned to `kotobase.net`
   (`ETZ_KOTOBASE_PIN`, default `https://kotobase.net`) via the existing
   Kubo-compatible `/api/v0/pin/add`. Best-effort: a remote-pin failure is
   logged and recorded in the audit map, never aborting the local publish.

4. The **two-tier model** is the invariant: kotoba node self-pin (local, hot,
   ≤~1 GB) **+** kotobase.net (durable canonical remote pin, content-addressed,
   >1 GB extended). kotobase.net is a Kubo-compatible pin service
   (`POST /api/v0/pin/add?arg=<cid>&recursive=true`).

The older `kotobase.etzhayyim.com` name is **superseded** by `kotobase.net`.
Historical `status_note` prose in `deps.toml` (a point-in-time record) is left
as-is; new config + code use `kotobase.net`.

# Consequences

- One canonical pin name, pinned into structured config + both pinner code
  paths (Rust node + Python dataset tool); no more prose-only endpoint.
- Remote pin is **on by default** to kotobase.net for kotoba nodes; dev/test
  opt out with `KOTOBA_IPFS_PIN_ENDPOINT=off`. Best-effort semantics mean a
  down/again pin endpoint degrades to local-only, never a hard failure.
- The e7m-dataset publish path now actually lands canonical pins remotely
  (previously local-Kubo-only), closing the durability gap for the
  `law/` + `baien/` dataset buckets (ADR-2605241500 / 2605262800).
- No change to the substrate ordering: IPFS stays the cold/interop backstop;
  the kotoba Datom log remains first-class canonical state.

# Alternatives Considered

- **Keep kotobase.etzhayyim.com** → rejected: that host is pruned/read-only;
  the live pin service is kotobase.net.
- **Replace local Kubo self-pin with kotobase.net entirely** → rejected: the
  node's local IPFS tier is the hot/add path; kotobase.net is the durable
  *remote* pin on top of it (two-tier), not a replacement.
- **Leave the e7m-dataset pinner local-only** → rejected: that left dataset
  CIDs undurable beyond a single workstation Kubo.

# Update — ipfs-pinner kotobase provider (2026-06-11, PR #1606)

Per the operator instruction 「pin は kotobase.net を使って」, the third consumer of this
canonical endpoint landed: a real **kotobase provider** in `50-infra/ipfs-pinner/`
(ADR-2605171800 Stage 4). It is the MST-CAR side of pinning — the prior two consumers
(`kotoba-store` `IpfsPinClient`, `e7m-dataset publish-ipfs`) cover the Datom-node and
dataset paths; the pinner covers AT-Protocol MST shard CARs.

- `src/providers/kotobase.ts` pins **by CID** via the standard **IPFS Pinning Service API**
  (`POST {ETZ_KOTOBASE_URL}/pins`, default `https://kotobase.net`) — note this is the PSA
  surface, complementary to the Kubo-compatible `/api/v0/pin/add` surface the kotoba node
  uses; both are exposed by kotobase.net. The root CID is the CAR filename stem
  (`mst-projector` writes `<rootCid>.car`), submitted and verified against the returned
  `PinStatus`; receipt carries the gftd gateway URL (`https://ipfs.gftd.ai/ipfs/<cid>`).
- **Auth — no platform key held** (no-server-key, ADR-2605231525): `ETZ_KOTOBASE_JWT`
  (Bearer) OR `ETZ_KOTOBASE_CACAO` + `ETZ_KOTOBASE_DID` (a self-signed CACAO granting
  `kotobase:pin`) — the SAME self-signed-CACAO leash mechanism ibuki uses for its kotoba
  write capability (ADR-2606111400), here scoped to pinning rather than `datom:transact`.
- Enable with `ETZ_PINNER_PROVIDERS=kubo,kotobase` (kubo provides blocks locally, kotobase
  is the durable remote — the Stage-4 replication-factor ≥ 2 pairing). 21/21 tests green.

This is a new *consumer*, not a change to the canonical-endpoint decision: kotobase.net
remains the single canonical remote pin; the substrate ordering is unchanged.
