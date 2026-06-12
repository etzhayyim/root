---
id: adr-2606065501-kotoba-browser-only-social-feed
renumbered_from: "2606065500"
title: "ADR-2606065501: etzhayyim.com browser-only kotoba social feed — browser read/write + member-signed block publish (no query node)"
status: accepted
doc_type: adr
topic: kotoba-browser-only-social-feed
authoritative: true
last_verified: 2026-06-06
priority: 4.0
axis: architecture
weight: 0.60
priority_note: "Production path for etzhayyim.com feed (read + write + propagation)."
authoritative_for:
  - etzhayyim.com social feed read/write path
  - member-signed kotoba block publish (apex)
depends_on:
  - "2605312345"
  - "2605262130"
  - "2605231525"
  - "2606013800"
  - "2606014600"
  - "2605215000"
related:
  - "2606041822"
  - "2606013800"
supersedes: []
superseded_by: []
---

# ADR-2606065501: etzhayyim.com browser-only kotoba social feed

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

`https://etzhayyim.com/` showed no posts. Root cause: the yoro SPA's feed/profile
reads (`app.bsky.feed.getTimeline` / `getDiscoverFeed` / `getAuthorFeed` /
`getPostThread`, `app.bsky.actor.getProfile`) were rewritten by the apex Worker's
`SUBSTRATE_NSID_ALIASES` to `com.etzhayyim.yoro.*` and forwarded to a
`yoro-xrpc-adapter` that did not implement them (404), while a direct hit to the
PDS returned 405 (GET vs POST). The posts existed in the AppView but never
reached the UI.

The directive was to serve these reads **browser-only via kotoba-wasm**, then to
extend the same model to **writes** (post/reply/comment/like), to **publish**
signed blocks so other browsers see updates, and to record **Wikipedia-style IP
attribution** — all without exposing a kotoba query node (kotoba stores data as
content-addressed IPFS blocks; a CID-verifying browser does not need the node).

# Decision

A browser-only social feed over the kotoba Datom log, with the apex Worker as a
thin, key-less publish/serve membrane.

**Read (browser).** The Service Worker `kotoba-sw.js` intercepts the same-origin
feed/profile NSIDs and assembles `app.bsky.feed.defs#feedViewPost` /
`#threadViewPost` / `actor profileView` from the in-page kotoba node. The node
hydrates by traversing the covering Prolly tree over **CID-verified IPFS blocks**
(`ingestBlock` re-hashes bytes → trustless), fetched from `/kotoba/blocks/<cid>`
(genesis = static asset; post-genesis = apex KV). Only a small **root pointer**
is published; the blocks are self-verifying. `atproto-agent.ts` routes the
handled NSIDs same-origin so the SW can see them; an SW miss falls through to the
AppView. Engagement counts (likes/reposts) are **derived from the append-only
like/repost datoms** (counts = a function of the log, not a mutable field).

**Write (browser).** post/reply/comment/like are computed and stored in the
in-page kotoba node, **member-signed** (ed25519 `did:key`, the server never signs
— ADR-2605231525), persisted to IndexedDB + an OPFS journal, and injected into
the live feed so the author sees them instantly. The signing key may be bound to
the member's passkey via the **WebAuthn PRF** extension (`setIdentity`).

**Publish (apex, key-less).** After a write the SW rebuilds the full merged tree,
signs the root, and POSTs root + signature + **delta** blocks (only those the
server lacks, via `block.has`). The apex **verifies** the ed25519 signature (it
can never mint a root), stores blocks in KV, and advances the published head
under **atomic check-and-set** in a single-threaded **Durable Object**
(`KotobaRoot`) — on a stale base the publisher gets 409, **rebases (CRDT union
of the two append-only Datom sets) and retries**, so no edit is lost. A **per-DID
token-bucket rate limit** caps sustained root churn (DoS hardening). Other
browsers resolve the latest root and hydrate the delta.

**IP attribution (Wikipedia-style, charter-clean).** The raw client IP is
captured server-side (the only place it is knowable) and stored in a
**suppressable** KV attestation (`kattest:<graph>:<root>`) as a salted hash +
coarse /24·/48 prefix, plus the **raw IP AES-GCM-encrypted** under an operator
oversight key (`KOTOBA_ATTEST_KEY`, Keychain-held) when configured. IP is **never
written into the immutable IPFS blocks** — keeping it erasable (GDPR/APPI
right-to-erasure) and honoring the charter PII-encryption invariant.

**Contract + observability.** The publish surface is formalized as AT-Protocol
lexicons (`com.etzhayyim.apps.kotoba.block.put` / `block.has` / `root` /
`stats`); `stats` exposes DO-tallied outcome counters (advances / conflicts /
rateLimited) for monitoring.

# Open question — authoritative head mechanism (DO vs no operated server-state)

The atomic head used here is a Cloudflare **Durable Object** (`KotobaRoot`),
which gives true single-threaded CAS but **is an operated, stateful server
primitive**. A concurrent design effort (branch `feat/kotoba-actors-datomic-blocks`)
argues this conflicts with the browser-complete / no-operated-server-state stance
of ADR-2605262130 + 2605312345 and reverts to a **KV check-and-set** head (no
DO). KV read-then-write only narrows the concurrency race (not fully atomic), but
keeps the apex free of operated state. The **deployed** production path currently
uses the DO; the KV-CAS variant is the more charter-aligned direction and may
supersede it. A fully content-addressed / commit-DAG-anchored head (no mutable
server pointer at all) is the long-term target. This ADR records the read/write/
publish/IP/lexicon decisions as settled; the **head-consistency primitive is under
reconciliation** and is the one part expected to change.

# Consequences

- etzhayyim.com renders its feed entirely in the browser from CID-verified
  blocks (`x-kotoba-src: blocks`); no kotoba query node is exposed.
- Writes are member-signed, locally durable, and propagate to other browsers via
  the apex; concurrent writers do not lose updates (DO CAS + client rebase/merge).
- The apex holds **no signing key**; it only verifies, stores, rate-limits, and
  attests. PII stays out of the immutable substrate.
- Test coverage: apex crypto + publish-handler integration tests (real DO,
  in-memory KV) and browser feed/merge unit tests (newest-first, derived counts,
  CRDT dedup-union, no-lost-update, profile resolve).
- Honest R0: full-tree re-publish per write (incremental Prolly mutation = future
  kotoba-engine work); WebAuthn-PRF page derivation needs a PRF-capable
  authenticator (the `setIdentity` hook is verified); a brief stale-bundle window
  after `wrangler secret put` can revert routes — always `wrangler deploy` after
  (RUNBOOK).

# Alternatives Considered

- **Server-side feed adapter** (implement `com.etzhayyim.yoro.feed.*`): rejected
  — keeps a server query path; the directive was browser-only.
- **Expose the kotoba node publicly** for the browser to query: rejected —
  unnecessary (IPFS blocks + CID + wasm suffice) and widens attack surface.
- **Bake IP into the immutable blocks** (literal Wikipedia history): rejected —
  unerasable PII on IPFS violates GDPR/APPI + the charter; encrypted suppressable
  KV attestation achieves the same accountability while remaining erasable.
- **KV-only CAS** for concurrency: kept as a fallback; the Durable Object gives
  true atomicity (KV read-then-write only narrows the race).

# References

- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605231525 (no-server-key)
- ADR-2606013800 (actor profile + dynamic did.json)
- ADR-2606014600 (WASM-actor runtime + trustless IPFS gateway)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2606041822 (apex etzhayyim.com kotoba query proxy)
- Lexicons: `00-contracts/lexicons/com/etzhayyim/apps/kotoba/{block/put,block/has,root,stats}.json`
- RUNBOOK: `50-infra/etzhayyim-did-web/RUNBOOK.md` (kotoba browser-publish ops)
