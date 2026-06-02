---
id: adr-2606015800-session-close-ipfs-did-and-self-certifying-resolution
title: "ADR-2606015800: Session close — IPFS-based + self-certifying DID resolution, mesh-runner serving"
status: active
doc_type: adr
topic: session-close-ipfs-did-and-self-certifying-resolution
authoritative: false
last_verified: 2026-06-02
priority: 5.0
axis: architecture
weight: 0.40
priority_note: "Documentation-only session-close record; authoritative designs are the referenced ADRs."
authoritative_for: []
depends_on:
  - 2606015200
  - 2606015400
  - 2606015600
related:
  - 2606014800
  - 2606013800
  - 2605212030
  - 2605231525
supersedes: []
superseded_by: []
---

# ADR-2606015800: Session close — IPFS-based + self-certifying DID resolution

**Status**: active (documentation-only)
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

Documentation-only closure for the 2026-06-01/02 continuation that followed
ADR-2606014800 (one-Worker WASM-actor runtime). It answered *「next step」* a few
times and *「did を IPFS ベースでの取得にできる?」*, ending with a fully trustless
DID-resolution path. This record indexes the three authoritative ADRs and states
what remains.

# What shipped (all merged to main)

1. **ADR-2606015200 — WASM-actor runtime round 2** (PR #702). dag-pb **CAR
   verification** (multi-block content is now trustless) + **e7m-wasm-runner** (T2
   mesh exec) + **kanae 鼎** 2nd T1 actor + **ameno wasm-actor-panel** + **ERC725
   vm mirror** (gated keccak256 + eth_call) + operator runbook.

2. **ADR-2606015400 — mesh-runner serving + IPFS-based DID retrieval** (PR #715).
   `e7m-wasm-runner/serve.mjs` HTTP service (`/xrpc/com.etzhayyim.actor.run`,
   CID-cached). **did.json is content-addressed**: `canonicalDidDoc`/`didDocCid`
   normalize the request-volatile field so the CID is stable across KV/kotoba/
   compiled; advertised via `x-etzhayyim-did-doc-cid` + `actors.json`; retrievable
   + CID-verifiable from any IPFS gateway. Worker (TS) ≡ publisher (JS) CID.

3. **ADR-2606015600 — self-certifying DID attestation** (PR #720). The actor's
   **own ed25519 key (`did:key`) signs the did.json CID** → the handle→CID binding
   is trustless (no TLS anchor). `diddoc-attest.ts` (verify-only) + `sign-diddoc.mjs`
   (operator signs with their own key) + `toDidDoc` cross-links `did:key` in
   `alsoKnownAs`. Verified end-to-end on kanae.

# The resolution picture now

```
discover   did:web:etzhayyim.com:actor:<h>            (handle, TLS, atproto-compat)
   │  alsoKnownAs → did:key:z6Mk… (self-cert key) + ipfs://<wasm-cid> + did:erc725 (pending)
retrieve   did.json by CID from ANY IPFS gateway      (apex /ipfs/<cid>, content-verified)
prove      attestation: did:key signs the did.json CID (trustless, no TLS)
execute    actor WASM (T1 browser-local / T2 mesh runner), CID/CAR-verified
```

No server-held key anywhere (ADR-2605231525); did:web stays canonical (ADR-2605212030).

# Verification (this session)

Worker `tsc` clean + 15 tests (5 attestation, 3 did-doc-cid, 4 car, 3 erc725);
runner 6 tests; ameno tsc + 9 tests; kanae runs (Prefectures top); real ipfs CAR
reassembles exactly; keccak256 known vectors; the self-certifying chain verified
on kanae's real CID. `e7m-verify` skipped where the local CLI lacked the `verify`
subcommand (environment gap).

# Next steps

- **IPNS mutable-pointer transport** — publish an IPNS record under the actor
  key's name pointing at the latest did.json CID, so the *whole* resolution path
  (not just the binding) is self-certifying with no TLS. Builds on ADR-2606015600.
- **Mesh-runner libp2p transport** — wrap the HTTP serving surface in a libp2p
  `/x/etzhayyim/xrpc/1.0` handler so a donated node serves over the mesh.
- **Register actor keys in the seed** — give each actor an
  `Ed25519VerificationKey2020` (client-self-custodied) so `did:key` aliases +
  attestations are real, not demo-generated.
- **Operator enablement** — `enable-kv` + pin canonical did.json (`--pin-did`) +
  pin attestations; set `IPFS_GATEWAYS` to the etzhayyim pin; deploy ERC725 to Base.

# References

- ADR-2606015200, ADR-2606015400, ADR-2606015600 (authoritative designs)
- PRs #702, #715, #720
- `50-infra/etzhayyim-did-web/` (cid/car/erc725/diddoc-attest + worker + scripts),
  `50-infra/e7m-wasm-runner/`, `20-actors/{kanae,ameno}/`
