---
id: adr-2606015400-mesh-runner-serving-and-ipfs-did-retrieval
title: "ADR-2606015400: Mesh-runner serving surface + IPFS-based DID retrieval"
status: accepted
doc_type: adr
topic: mesh-runner-serving-and-ipfs-did-retrieval
authoritative: true
last_verified: 2026-06-02
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Turns the T2 mesh runner into a real service + makes did.json content-addressed (IPFS-retrievable), not only TLS-served."
authoritative_for:
  - mesh-runner-serving-surface
  - ipfs-based-did-retrieval
depends_on:
  - 2606015200
  - 2606014600
  - 2606013800
  - 2605212030
  - 2605231525
related:
  - 2606014500
  - 2605262130
supersedes: []
superseded_by: []
---

# ADR-2606015400: Mesh-runner serving surface + IPFS-based DID retrieval

**Status**: accepted
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

Two follow-ups to ADR-2606015200: (a) the T2 mesh runner only ran as a CLI — a
donated node should *serve* results; (b) the question *「did を IPFS ベースでの取得に
できる?」* — can a DID document be retrieved content-addressed (IPFS), not only
over did:web TLS?

# Decision

## D1 — Mesh-runner serving surface
`50-infra/e7m-wasm-runner/serve.mjs` exposes the runner as an HTTP service:
```
GET /xrpc/com.etzhayyim.actor.run?actor=<did|handle>[&cid=<cidv1>]
GET /healthz
```
It resolves → CID/CAR-verifies → runs (core or jco component) → returns JSON, and
**caches by CID** (content-addressed → immutable). Trust is unchanged (bytes
verified before execution, no server key). This is the HTTP bridge the apex Worker
can proxy and a libp2p `/x/etzhayyim/xrpc/1.0` handler will wrap next. 3 tests
(real HTTP requests against a stubbed gateway: healthz, run+cache, bad-actor 502).

## D2 — IPFS-based DID retrieval
did:web stays the canonical, discoverable form (TLS trust root, ADR-2605212030).
On top of it, every actor's DID document is now **content-addressed**:

- **canonical did.json** = `toDidDoc(rec)` with the one request-tier-volatile field
  (`_meta.source`) normalized to `"ipfs"`, so the bytes — and the CID — are
  identical no matter which tier (KV / kotoba / compiled) served the record
  (`canonicalDidDoc` / `canonicalDidDocBytes` / `didDocCid` in `actor-profiles.ts`).
- **the CID is advertised, not embedded** (embedding would be circular): the
  `/actor/<h>/did.json` response carries `x-etzhayyim-did-doc-cid` +
  `Link: <…/ipfs/<cid>>; rel="canonical"`; `/.well-known/actors.json` lists
  `didDocumentCid` / `didDocumentIpfs` / `didDocumentGateway` per actor.
- **retrieval**: a client gets the authentic CID for a handle from `etzhayyim.com`
  (TLS) — or, later, Base L2 / IPNS — then fetches the did.json from **any IPFS
  gateway** and verifies it by CID (the apex `/ipfs/<cid>` trustless gateway, or a
  third-party one). The handle→CID *binding* stays anchored; IPFS makes the
  *bytes* tamper-evident, mirrorable, and offline-verifiable.
- **publisher** materializes the canonical did.json, computes the CID (`--pin-did`
  → `ipfs add`), and **the worker (TS) and publisher (JS) compute byte-identical
  canonical did.json CIDs** (verified for tsumugi/kanae/watatsuna), so the
  advertised CID always matches the pinned content.

# Consequences

- A donated node serves CID-verified actor results over HTTP (libp2p next).
- did.json is retrievable + verifiable from any IPFS gateway, decoupling document
  availability from the apex's uptime (mirror-anywhere), while did:web TLS remains
  the trust anchor for the handle→CID binding.
- Worker `tsc` clean + 10 tests (3 did-doc-cid via esbuild-bundled TS, 4 car, 3
  erc725); runner 6 tests (3 serve + 3 run).

# Honest scope (R0)

- The handle→CID binding is still anchored by `etzhayyim.com` (TLS) — full
  did:ipfs/IPNS self-certifying resolution (CID signed by the actor key) is future
  work; this ships content-addressed *bytes*, not yet a chain/IPNS-anchored
  binding.
- Pinning the canonical did.json (`--pin-did`) + serving from the etzhayyim pin
  are operator-gated (the default gateway uses public IPFS gateways).
- Mesh-runner libp2p transport not yet wired (HTTP serving is the bridge).
- The canonical CID changes whenever the did.json changes (e.g. on-chain vm
  landing) — re-pin on update, as with any content-addressed artifact.

# Alternatives Considered

- **Switch the DID method to did:ipfs/did:ipid.** Rejected (for now): breaks the
  did:web canonical form (ADR-2605212030) + atproto compatibility; content-
  addressing the bytes under did:web gets most of the benefit without the churn.
- **Embed the CID inside the did.json.** Impossible — self-referential (the CID is
  of the document). Advertised via header / actors.json instead.
- **Serve the runner only as a CLI.** Rejected — a donated node must serve.

# References

- `50-infra/e7m-wasm-runner/serve.mjs` + `tests/serve.test.mjs`
- `50-infra/etzhayyim-did-web/src/registry/actor-profiles.ts` (canonicalDidDoc / didDocCid) + `worker.ts` (header + actors.json) + `scripts/publish-actor-records.mjs` (--pin-did) + `scripts/diddoc-cid.test.mjs`
- ADR-2606015200 (#6 mesh runner), ADR-2606014600 (gateway + CAR), ADR-2606013800 (dynamic did.json), ADR-2605212030 (did:web canonical), ADR-2605231525 (no-server-key)
