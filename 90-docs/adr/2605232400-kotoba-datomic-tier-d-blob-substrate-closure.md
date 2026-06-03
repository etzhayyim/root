---
id: adr-2605232400-kotoba-datomic-tier-d-blob-substrate-closure
title: "ADR-2605232400: kotoba-datomic Tier D blob primitive + gsplat IPFS swap + yoro substrate-facade closure (SUPERSEDED by 2605262130 for substrate; SDK API surface preserved bit-identically)"
status: superseded
doc_type: adr
topic: kotoba-datomic-tier-d-blob
authoritative: true
last_verified: 2026-05-23
priority: 7.5
axis: substrate-boundary
weight: 0.7
authoritative_for:
  - "kotoba-datomic Tier D blob path (content-addressed IPFS pin primitive)"
  - "gsplat trainer B2 → IPFS swap protocol"
  - "yoro substrate-facade migration (@atproto/api → @etzhayyim/sdk/atproto)"
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231500-kotoba-datomic-projection
  - adr-2605241500-etzhayyim-dataset-cid-substrate
related:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605231525-no-server-key-religious-corp-architecture
supersedes: []
superseded_by:
  - adr-2605262130-kotoba-storage-substrate-unification
---

# ADR-2605232400: kotoba-datomic Tier D blob primitive + gsplat IPFS swap + yoro substrate-facade closure

**Status**: active
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

ADR-2605231400 enumerates the kotoba-datomic 7-layer mapping; ADR-2605231500 names the
four conformance levels (L0/L1/L2-projection plus the implicit blob tier). The maps
migration plan in [`60-apps/etzhayyim-project-maps/MIGRATION-TODO.md`](../../60-apps/etzhayyim-project-maps/MIGRATION-TODO.md)
classifies each surface into one of four tiers; Tier A (pure MST) and Tier B
(L1 witnessed) shipped in earlier 2026-05-23 waves alongside the Phase 1 golden-file
integration test. Two remaining gaps blocked an end-to-end substrate stack:

1. **Tier D blob primitive missing in both SDKs.** Apps that produce large
   payloads (gsplat PLY/GLB from the Mapillary trainer, vision frames, satellite
   COG slabs) had no SDK-mediated way to pin content-addressed bytes — the
   `bulk-ingest/workers/gsplat_train_dumper.py` pod still wrote to B2 directly
   via boto3 (`_b2_put` / `_b2_head`), violating the ADR-2605172000 boundary at
   the blob layer even after the MST writes had been ported.

2. **yoro app still imported `@atproto/api` directly.** Six callsites in the
   yoro SvelteKit appview (atproto-agent, messaging-client, translate/client,
   mcp/client, ActorEmbed.svelte, blocked-accounts/+page.svelte) bypassed the
   `@etzhayyim/sdk/atproto` facade required by ADR-2605172000 ("Substrate
   client imports — Only via `@etzhayyim/sdk`"). Each carried a
   `TODO(substrate-boundary)` marker referring to this same ADR.

## Decision

Ship a cross-language **Tier D blob upload primitive** in both SDKs, wire it
through `gsplat_train_dumper.py` behind an env flag, and complete the yoro
facade migration so the substrate-boundary rule is enforceable in CI again.

### 1. Tier D blob primitive (cross-language, bit-identical receipt shape)

| Language | Surface | Underlying call |
|---|---|---|
| TypeScript | [`Etzhayyim.uploadBlob({data, mediaType?})`](../../20-actors/etzhayyim-sdk/src/index.ts) | `pinBlob()` → `POST /api/v0/add?pin=true&cid-version=1` (Kubo HTTP API) |
| Python | [`Etzhayyim.upload_blob(data, media_type=?)`](../../20-actors/magatama/py/src/pymagatama/substrate/__init__.py) | `httpx` multipart POST to same Kubo endpoint |

**Receipt shape (bit-identical across languages)**:

```ts
interface UploadBlobReceipt {
  cid: string;          // CIDv1 base32 lowercase (raw codec 0x55, sha2-256)
  sizeBytes: number;    // as reported by Kubo
  mediaType: string;    // echoed for downstream lexicon embedding
}
```

```py
@dataclass
class UploadBlobReceipt:
    cid: str
    size_bytes: int
    media_type: str
```

**Boundary semantics**:

- Empty payload rejected before any HTTP (deterministic on both sides).
- Missing `ipfsApiUrl` / `ipfs_api_url` rejected before any HTTP.
- Kubo NDJSON response parsed by picking the LAST non-blank line (Kubo emits
  one JSON object per added file; the root is always last).
- 5xx responses are surfaced as typed errors (`Error("[etzhayyim-sdk] pin failed: 503")`
  on TS side, `SubstrateError("Kubo /api/v0/add returned 503: ...")` on Python).
- `mediaType` defaults to `application/octet-stream`; on TS it can also be
  derived from `Blob.type` when no override is given.

**Test coverage**: 7 vitest + 6 pytest (13 total) covering the boundary
semantics above plus trailing-slash normalisation on the API URL and the
multipart envelope sanity check.

### 2. gsplat trainer B2 → IPFS swap (feature-flagged, transitional)

`60-apps/etzhayyim-project-maps/bulk-ingest/workers/gsplat_train_dumper.py` gains:

- `_ipfs_pin_via_substrate(blob, content_type) -> str` — sync wrapper around
  `pymagatama.substrate.Etzhayyim.upload_blob()` (the dumper owns its event
  loop for the duration of one training job).
- `_blob_upload(prefix, blob, ext, content_type) -> (stored_ref, sha_hex, new_upload)` —
  dispatches on `USE_PYMAGATAMA_SUBSTRATE_BLOB=1`: with the flag, calls
  `_ipfs_pin_via_substrate` and returns `("ipfs://{cid}", sha_hex, True)`;
  without the flag, falls back to the legacy `_content_addressed_upload`
  (B2 PUT path) with bit-identical behaviour. SHA-256 is computed both ways
  for audit symmetry.
- `_ipfs_gateway_fetch(cid)` + `_blob_download(stored_ref)` — bake-side
  companion that dispatches on the `ipfs://` scheme so train rows produced
  with the flag enabled can still feed the bake pipeline without operator
  intervention. Plain B2 keys keep working unchanged.

The `vertex_maps_gsplat_{asset,mesh}.b2_key` column then carries either a
legacy B2 object key or an `ipfs://{cid}` URI — downstream readers branch
on the `ipfs://` scheme. Boot guard relaxed: `B2_*` env becomes optional
when `USE_PYMAGATAMA_SUBSTRATE_BLOB=1`, replaced by an `ETZ_IPFS_API_URL`
requirement.

### 3. yoro substrate-facade closure (six callsites)

All six remaining `@atproto/api` direct imports in
`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/` rewritten
to import from `@etzhayyim/sdk/atproto`:

| File | Import |
|---|---|
| `lib/atproto-agent.ts` | `AtpAgent`, `AppBskyActorDefs`, `AppBskyFeedDefs`, `AppBskyRichtextFacet` (type) |
| `lib/superapp/messaging-client.ts` | `AtpAgent` |
| `lib/translate/client.ts` | `AtpAgent` |
| `lib/mcp/client.ts` | `AtpAgent` |
| `lib/actor/ActorEmbed.svelte` | `AtpAgent` |
| `routes/moderation/blocked-accounts/+page.svelte` | `AppBskyActorDefs` (type) |

The `@etzhayyim/sdk` workspace dependency is added to
`appview/yoro-ui-g00h5zto/svelte/package.json`; `@atproto/api` stays in the
dependency list because the SDK transitively re-exports its types and a future
ADR may want to lock a specific version range without dropping the upstream
package outright. `pnpm check:ts` passes clean post-migration.

## Consequences

**Positive**:

- The substrate stack is now Tier A + Tier B + Tier D end-to-end SDK-mediated.
  (Tier C / projection remains a Charter Rider §2 carve-out per
  ADR-2605222330 until the projection ADR follow-up ships.)
- `e7m verify --no-server-key` (ADR-2605231525) can scan for direct
  `@atproto/api` imports in the yoro tree and now finds zero — the
  ninth-invariant grep stays green.
- The gsplat dumper is the first production-shape worker to swap an
  external-service blob (B2) for an etzhayyim-operated IPFS pin without
  losing the bake-side replay path. Pattern is reusable for the vision /
  satellite / mapraly Tier D follow-ups.
- Two language-side SDKs now have bit-identical Tier D receipts, which makes
  it possible to write cross-language Phase-1 golden-file tests asserting
  that a TS-pinned blob is byte-identical when re-pinned from Python
  (deferred to a follow-up — not part of this ADR).

**Negative / risk**:

- The trainer-side dispatch on `b2_key` carrying `ipfs://{cid}` rather than a
  bare key is a semantic overload of an existing column. A schema migration
  to rename the column or add a dedicated `payload_ref` column is desirable
  but deferred — the dispatch is a 6-character `startswith("ipfs://")` check
  and the column comment is updated in the dumper docstring.
- Kubo HTTP API surface (`/api/v0/add`, `/api/v0/cat`) is treated as stable
  per ADR-2605241500's existing reliance, but a Kubo major version that
  breaks NDJSON shape would break both SDKs simultaneously. Mitigation: the
  test suite asserts the "last non-blank line is the root" rule explicitly.
- Charter Rider Cache-Control invariant (`public, max-age=86400, immutable`)
  on B2 was a browser-side optimisation; the IPFS gateway equivalent is
  intrinsic (CID is content-addressed by definition). Browser-side loader
  swap remains a follow-up in the maps MIGRATION-TODO Phase 2 list.

**Migration / rollout**:

- Dumper continues to default to the B2 path. Operator opts into the swap
  per pod by setting `USE_PYMAGATAMA_SUBSTRATE_BLOB=1` + `ETZ_IPFS_API_URL`.
- Backfill of existing B2 blobs into IPFS pins is explicitly out of scope
  for this ADR; a separate `rewrite_gsplat_cache_control.py`-analog operator
  tool tracks that work in MIGRATION-TODO Phase 2.
- yoro re-deploy is required to ship the facade migration to production,
  but the change is source-only — no schema, no XRPC, no behaviour change.

## Alternatives Considered

1. **Add `uploadBlob` only to TS, port Python later.** Rejected: the
   bulk-ingest fleet is Python-side; without the Python primitive the maps
   dumpers cannot port off B2 without re-implementing the Kubo HTTP layer
   per pod (which the geonames / wikidata / satellite pods would each copy
   independently).

2. **Replace B2 with IPFS unconditionally in the gsplat dumper.** Rejected
   in favour of the env-flag dispatch: the existing browser-side loader
   still reads B2 URLs (Cache-Control immutable), and a blue/green-style
   cutover requires both paths to coexist for at least one operator cycle.

3. **Defer the yoro migration until the projection-sweep ADR.** Rejected:
   the six files are mechanically rewritten in seconds and the
   substrate-boundary rule is otherwise unenforceable in the most-visible
   first-party app. The projection sweep ADR can layer on top of a
   facade-clean tree.

## References

- ADR-2605172000 — RW-free substrate hard rules
- ADR-2605231400 — kotoba-datomic Holochain-iso composition
- ADR-2605231500 — kotoba-datomic-projection conformance levels
- ADR-2605241500 — DataLad + IPFS dataset CID substrate (Kubo HTTP API contract source)
- ADR-2605231525 — no-server-key architecture (9th invariant enforcement target)
- [`60-apps/etzhayyim-project-maps/MIGRATION-TODO.md`](../../60-apps/etzhayyim-project-maps/MIGRATION-TODO.md) — Phase 2 Tier D rows ticked by this ADR
- [`20-actors/etzhayyim-sdk/src/index.ts`](../../20-actors/etzhayyim-sdk/src/index.ts) — TS `uploadBlob` implementation
- [`20-actors/magatama/py/src/pymagatama/substrate/__init__.py`](../../20-actors/magatama/py/src/pymagatama/substrate/__init__.py) — Python `upload_blob` implementation
- [`60-apps/etzhayyim-project-maps/bulk-ingest/workers/gsplat_train_dumper.py`](../../60-apps/etzhayyim-project-maps/bulk-ingest/workers/gsplat_train_dumper.py) — `_blob_upload` / `_blob_download` dispatch
