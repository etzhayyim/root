---
id: adr-2606013600-browser-kotoba-node-sovereign-tier2
title: "ADR-2606013600: browser kotoba node — kqe-in-wasm as the sovereign client-side apex tier-2"
status: proposed
doc_type: adr
topic: browser-kotoba-node
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - the browser kotoba node (kotoba-wasm) as the client-side actor-resolution path
  - the sovereignty layering of the apex DID-web resolver (kotoba canonical + compiled fallback; KV is an optional edge cache)
  - the "where to host kotoba" answer — the browser IS the node; IPFS pinning is the only durable, commodity tier
depends_on:
  - "2605262130"
  - "2605312345"
  - "2605215000"
  - "2605231525"
  - "2605241900"
  - "2606013800"
related:
  - "2606015400"
  - "2606015600"
  - "2606014500"
  - "2606051500"
supersedes: []
superseded_by: []
---

# ADR-2606013600: browser kotoba node — kqe-in-wasm as the sovereign client-side apex tier-2

**Status**: proposed
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

The apex DID-web Worker resolves an actor record (the backing for both `did.json`
and `app.bsky.actor.getProfile`) through a **3-tier fail-open** chain
(`worker.ts` `resolveActorRecordTiered`, ADR-2606013800):

1. **KV** (`actor:<handle>`) — a fast edge cache;
2. **kotoba pull** (`kg.entity`) — first-class canonical state;
3. **compiled `INFRA_ACTORS`** — baked into the Worker bundle.

Two facts make this layering subtler than it looks:

- **KV is not a source of truth.** Tier-2 writes it back with `expirationTtl: 300`,
  so KV is only a 300 s auto-populated cache of the kotoba pull. If the `ACTOR_KV`
  binding is absent the resolver falls straight through to kotoba → compiled and
  resolution stays live.
- **The edge is not sovereign.** etzhayyim owns the *domain* (CF Registrar) and the
  DID doc is content-addressed + TLS-anchored + keyless (ADR-2606015400/15600), but
  the CF Worker + KV currently run on a managed (etzhayyim) Cloudflare account. Routing
  *canonical* state or *auth* through vendor infra would violate the Ownership
  invariant + the Murakumo-only consent boundary (ADR-2605215000).

This raised the operative question: *if etzhayyim is to stand up its own kotoba so
that tier-2 is vendor-independent, where does that node live?* — and, more
pointedly, **can the kotoba node run as browser wasm so there is no node to host at
all?**

`kotoba` already answers this by construction. The `kotoba-wasm` crate is described
as the *"kotoba browser node — kqe read engine + CID-verified Prolly traversal over
wasm-bindgen"*, with three layers all targeting `wasm32-unknown-unknown`:

- **READ** — `kotoba-kqe` EAVT/AEVT/AVET/VAET arrangements + CID-verified Prolly
  traversal (`searchActors`, `datomicQ`);
- **WRITE (no-server-key)** — client-side `ed25519-dalek` commit signing +
  `aes-gcm` field encryption (`commitSigned`), per ADR-2605231525;
- **PERSIST** — `kotoba-store-web` IndexedDB block store (`commitToIdb` /
  `hydrateFromIdb`), with an OPFS journal for cold-restart durability.

A Service Worker (`kotoba-sw.js`) transparently intercepts the exact
`GET /xrpc/app.bsky.actor.searchActors?q=…` request the reader already makes and
answers it from the local wasm node (`x-kotoba-sw: local-wasm`) — no server pull.

# Decision

**The browser kotoba node is the sovereign client-side form of the apex tier-2.**
Actor resolution can run entirely in the user's browser: fetch content-addressed
Datom blocks from any IPFS gateway, verify CIDs locally, and run the kqe query
client-side. This dissolves the "where to host kotoba" question:

- **The browser IS the kotoba node** (ameno / baien edge envelope, ADR-2605241900).
- **The apex Worker is reduced to a content-verifying gateway** — it already ships
  the verify primitives (`cid.ts`, `car.ts`, `diddoc-attest.ts`). It is a
  convenience, not a trust root.
- **The only durable tier is IPFS block availability** — a commodity pinner
  (`50-infra/ipfs-pinner`), never an auth/trust root.
- **Base L2 anchors the commit-DAG root.**

A browser tab cannot *be* the Worker's inbound `KOTOBA_ENDPOINT` (browsers accept no
inbound HTTP) — but that is moot: when the read runs client-side, the server pull is
not needed. The sovereign server-side layering is therefore the **2-tier
kotoba → compiled `INFRA_ACTORS`**, with KV demoted to an optional, self-filling
edge cache (manual KV pre-seeding is discouraged — a no-TTL entry shadows
kotoba/compiled updates; see `20-actors/oil-refining/MIGRATION-NOTES.md`).

# Consequences

**Empirically verified 2026-06-06** (PoC: `50-infra/etzhayyim-did-web/poc-browser-node/`):

- `kotoba-wasm` compiles clean to `wasm32-unknown-unknown` (release + wasm-opt →
  `kotoba_wasm_bg.wasm` 2.1 MB, **gzip ≈ 790 KB**). Toolchain note: use the **rustup**
  stable toolchain, not Homebrew rust (Homebrew lacks the wasm32 std → `core/std`
  E0463).
- **Node-driven proof on the REAL 28-actor SSoT** (`actor-profile-seed.kotoba.edn`
  → `:yoro.profile/*` datoms): `searchActors("kamado")` resolves
  `did:web:etzhayyim.com:actor:kamado` client-side; `commitSigned` yields a
  client-side `did:key:z…` + content-addressed `bafyrei…` root + ed25519 signature;
  identical input → identical root (content-addressing determinism). 9/9 assertions.
- **Real-browser proof** (system Google Chrome 148 via playwright-core,
  `channel: 'chrome'`): the Service Worker answers `searchActors` from the
  in-browser wasm node (`x-kotoba-sw: local-wasm`), kamado resolves client-side, the
  node holds the seeded corpus. 4/4 assertions + screenshot.

Implications:

- **Sovereignty**: the trust path is content-addressing + did:web TLS + did:key
  attestation. etzhayyim edge and even etzhayyim's own Worker leave the trust path; the
  only thing to "host" is commodity IPFS pinning.
- **Edge envelope**: ~790 KB gzip is well within the baien edge target
  (ADR-2605241900) for a resolver; it is the read engine, not an LLM.
- **No invariant amendments.** Strengthens kotoba-canonical-state (ADR-2605262130 /
  2605312345), no-server-key (ADR-2605231525), and the Murakumo-only consent boundary
  (ADR-2605215000).

**Honest R0**: the build artifacts are reproducible, not committed (no git-lfs).
A dedicated etzhayyim CF account (edge sovereignty) + a standing etzhayyim IPFS
pinner remain tracked follow-ups; the in-Worker `KOTOBA_ENDPOINT` tier-2 still points
at etzhayyim's own node when one is designated (the PoC proves the client-side form,
which needs no such node). The kotoba submodule carries the same id for the upstream
engine ADR; this root ADR is the religious-corp-canonical record per ADR-2605170900.

# Alternatives Considered

- **Host a standing etzhayyim kotoba HTTP node for tier-2.** Works, but reintroduces
  a server to operate and an auth surface; the client-side form removes both for the
  read path. Kept as an option for bulk/server consumers, not the default.
- **Keep promoting records into CF KV.** Rejected — KV is a 300 s self-filling cache,
  and manual no-TTL writes shadow canonical updates on vendor-managed edge (the exact
  coupling being unwound).
- **Embed kqe-wasm inside the Worker (workerd runs wasm).** Viable and complementary
  (edge convenience with no external node), but still etzhayyim-managed compute; the
  browser form is strictly more sovereign. Recorded as a future edge optimization.

# References

- `50-infra/etzhayyim-did-web/poc-browser-node/` — build + Node + real-browser proofs
- `40-engine/kotoba/crates/kotoba-wasm/` — the browser kotoba node (+ `web/` Service-Worker harness)
- ADR-2606013800 — actor profile + dynamic did.json (the 3-tier resolver)
- ADR-2606015400 / 2606015600 — content-addressed + self-certifying did.json
- ADR-2605262130 / 2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605231525 — no-server-key; ADR-2605215000 — Murakumo-only consent boundary
- ADR-2605241900 — baien edge-target invariant
