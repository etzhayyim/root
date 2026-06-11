---
id: adr-2606015600-self-certifying-did-attestation
title: "ADR-2606015600: Self-certifying DID-document attestation (did:key signs the did.json CID)"
status: accepted
doc_type: adr
topic: self-certifying-did-attestation
authoritative: true
last_verified: 2026-06-02
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Makes the handle→CID binding trustless: the actor's own ed25519 key (did:key) signs the did.json CID; no TLS anchor needed."
authoritative_for:
  - self-certifying-did-attestation
  - did-key-ed25519
depends_on:
  - 2606015400
  - 2606013800
  - 2605212030
  - 2605231525
related:
  - 2606014500
  - 2606014600
supersedes: []
superseded_by: []
---

# ADR-2606015600: Self-certifying DID-document attestation

**Status**: accepted
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

ADR-2606015400 made the did.json *bytes* content-addressed (IPFS-retrievable), but
the **handle→CID binding** was still anchored only by `etzhayyim.com` TLS. The
remaining step: make that binding trustless — provable by the actor's own key,
not by who serves it.

# Decision

Each actor's DID document is bound to its CID by a signature from the actor's
**own ed25519 key, expressed as a `did:key`** — so verification is
**self-certifying** (the key IS the identifier; no external anchor consulted).

- **`src/diddoc-attest.ts` (worker, verify-only)**: base58btc + `did:key`
  derivation (`ed25519PubToDidKey` / `didKeyToEd25519Pub`, multicodec `0xed01`)
  and `verifyDidDocAttestation(att, expectedCid?)` (WebCrypto Ed25519). The server
  NEVER signs — it only verifies (ADR-2605231525).
- **Attestation** = `{ did, didDocCid, signedAt, sequence, proof: { type:
  Ed25519Signature2020, verificationMethod: did:key:z…, proofValue: z… } }`. The
  signed message is the deterministic payload; `sequence` lets a later attestation
  supersede.
- **`scripts/sign-diddoc.mjs` (operator tool)**: the actor/operator generates or
  loads their ed25519 key, takes the canonical did.json CID
  (`out/actor-records/<h>.diddoc.cid`, ADR-2606015400), and emits a signed
  attestation. The private key is the actor's — printed once, never the server's.
- **Cross-link**: `toDidDoc` adds `did:key:<publicKeyMultibase>` to `alsoKnownAs`
  whenever the actor has an `Ed25519VerificationKey2020` vm, tying the did:web
  handle to the self-certifying key.

**Trustless chain (resolving by key):** `did:key:z6Mk…` → verify the attestation's
signature against the key in its proof → trust `didDocCid` → fetch + CID-verify
the did.json from any IPFS gateway (apex `/ipfs/<cid>`, ADR-2606014600) → confirm
`doc.id` + that the doc lists this `did:key`. **TLS is no longer required for the
binding.**

# Consequences

- The handle↔CID binding is cryptographically provable by the actor's key — a
  client can verify did.json authenticity with no trusted server.
- did:web (TLS) remains as the discoverable form + handle anchor; did:key adds the
  trustless verification path. Both coexist in `alsoKnownAs`.
- Verified end-to-end: the signing tool produced a `did:key` + attestation binding
  kanae's real canonical did.json CID; `verifyDidDocAttestation` confirmed it.
  Worker `tsc` clean + 15 tests (5 attestation, 3 did-doc-cid, 4 car, 3 erc725).

# Honest scope (R0)

- This ships the **signed attestation** (key → CID). The **mutable pointer**
  transport (IPNS record published under the key's name, so the latest CID is
  discoverable without TLS) is the next increment; today the authentic CID is
  still discovered via `etzhayyim.com` (or a handed-out attestation).
- No DID-method change (did:web stays canonical, ADR-2605212030); did:key is an
  `alsoKnownAs` + the attestation's signing identity, not a new resolver.
- Actors don't yet have keys in the seed (`vm: []`) — registering each actor's
  `Ed25519VerificationKey2020` (client-self-custodied) is operator work; the demo
  generates a key. Pinning the attestation alongside the did.json is operator-gated.

# Alternatives Considered

- **Trust TLS for the binding (status quo).** Rejected as the end state — it makes
  document authenticity depend on the apex, not the actor.
- **Switch to did:key as the canonical DID.** Rejected: loses human-readable
  handles, services, and atproto compatibility; did:key as an alias + signer keeps
  both.
- **Sign the did.json itself (embedded proof).** Rejected: the did.json is dynamic
  + content-addressed; signing the *CID* (an external attestation) keeps the
  document canonical and the signature stable.

# References

- `50-infra/etzhayyim-did-web/src/diddoc-attest.ts` + `scripts/sign-diddoc.mjs` + `scripts/diddoc-attest.test.mjs`
- `src/registry/actor-profiles.ts` (`toDidDoc` did:key alsoKnownAs)
- ADR-2606015400 (IPFS-based DID retrieval), ADR-2606013800 (dynamic did.json), ADR-2605212030 (did:web canonical), ADR-2605231525 (no-server-key)
