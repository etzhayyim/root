---
id: adr-2606066000-kotoba-content-addressed-head-ipns-commit
title: "ADR-2606066000: content-addressed feed head — kotoba IPNS commit-head resolves the 2606065500 open question (no Durable Object)"
status: accepted
doc_type: adr
topic: kotoba-content-addressed-head
authoritative: true
last_verified: 2026-06-06
priority: 4.6
axis: architecture
weight: 0.46
priority_note: "Closes the ADR-2606065500 OPEN question: the authoritative published head is the kotoba IPNS commit-head (member-signed IpnsRecord → content-addressed DistributedDatomCommit), not a Cloudflare Durable Object and not a trusted apex KV value."
authoritative_for:
  - kotoba-feed-head-primitive
depends_on:
  - adr-2606065500-kotoba-browser-only-social-feed
  - adr-2606013600-kotoba-persistent-ipns-graph-heads
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605231525-no-server-key
related:
  - "40-engine/kotoba/crates/kotoba-ipfs/src/ipns.rs"
  - "40-engine/kotoba/crates/kotoba-datomic/src/distributed.rs"
  - "50-infra/etzhayyim-did-web/src/kotoba-publish.ts"
supersedes: []
superseded_by: []
---

# ADR-2606066000: content-addressed feed head — kotoba IPNS commit-head (no Durable Object)

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

ADR-2606065500 shipped the browser-only kotoba social feed but left its head
primitive **explicitly unresolved**:

> "head primitive under reconciliation — deployed Durable Object vs charter-aligned
> KV-CAS / content-addressed head (no operated server-state, ADR-2605262130 /
> 2605312345)."

Two failed/interim directions existed:

1. **Cloudflare Durable Object** (`KotobaRoot`) — true single-threaded atomic CAS,
   but an **operated, stateful, trusted server component**, in direct tension with
   ADR-2605262130 / 2605312345 (kotoba Datom log is the canonical state; no operated
   server-state) and ADR-2605231525 (no-server-key). It was deployed briefly, then
   **removed** (a `deleted_classes = ["KotobaRoot"]` migration in `wrangler.toml`,
   *"intentionally NO `[[durable_objects.bindings]]`"*). A PR that re-introduced it
   was closed not-merged for this reason.
2. **Apex KV `kroot:<graph>`** — the current interim: a mutable JSON value in
   Cloudflare KV, advanced under optimistic concurrency on `prevRoot`. Better than
   the DO (no single-threaded server object), but it is still a **trusted operated
   mutable value**: a consumer that reads `GET root` is trusting the apex Worker to
   report the real head. The member only signs the *root CID bytes* (kotoba-wasm
   `commitSigned` → `{root, did, sig}`), not a sequenced, self-describing head
   record — so the apex KV value, not a member-signed object, is the authority.

Meanwhile the **canonical substrate already implements exactly the right
primitive** (ADR-2606013600):

- `kotoba-ipfs::IpnsRecord` — a **member-signed** (Ed25519 over a ciborium-CBOR
  payload, base58btc multibase) mutable head pointer with a monotonic `sequence`
  (stale-guard = the CAS ordering), `valid_until`, and a **DID-derived name**
  (`did_document_ipns_name(did)`); `value` = the CID of the latest commit block.
- `kotoba-datomic::DistributedDatomCommit` — the **content-addressed DAG-CBOR
  commit block** the IPNS value points to: it carries a `parent` commit (the
  hash-linked DAG / stale-parent CAS) and the five covering ProllyTree
  `index_roots` (eavt/aevt/avet/vaet/tea).

That **is** "IPNS + signed DAG record": `IpnsRecord` is the signed mutable pointer;
`DistributedDatomCommit` is the content-addressed DAG node. Inventing a parallel
signed-head format in the apex Worker would be a parallel substrate, forbidden by
ADR-2605262130.

# Decision

**The authoritative published head is the kotoba IPNS commit-head** — a
member-signed `IpnsRecord` whose `value` is a content-addressed
`DistributedDatomCommit` CID — reusing the existing kotoba implementation
(ADR-2606013600). The Durable Object is rejected; the apex KV head is demoted to a
**non-authoritative cache/relay**.

Concretely:

1. **Authority = the member-signed `IpnsRecord`.** The member's Ed25519 `did:key`
   signs the kotoba IPNS payload (name, value, sequence, valid_until, …). `sequence`
   replaces `prevRoot` as the monotonic stale-guard / CAS ordering. The record is
   **self-verifying**: any reader checks the signature against the DID's key, so no
   server needs to be trusted (no-server-key, ADR-2605231525).
2. **Integrity = the content-addressed commit DAG.** `value` points to a
   `DistributedDatomCommit` whose `parent` hash-links the previous head; readers
   verify each CID and walk the DAG. Optimistic concurrency = "advance only if your
   parent/sequence matches the current head".
3. **Apex Worker = non-authoritative relay.** `block.put` stores the commit blocks
   (content-addressed; already idempotent) **and the signed `IpnsRecord`** (replacing
   the ad-hoc `kroot:` JSON); `GET root` returns that record. Because the record is
   self-verifying, the apex/KV holding it is **not trusted** — worst case it serves a
   stale `sequence`, which the client detects. This keeps reads fast (the head is
   read once per session, then immutable blocks hydrate the feed — head latency is
   not the hot path) while removing the *trusted* operated-state property.
4. **Discovery layering (DID → IPNS → commit DAG).** The IPNS name is DID-derived
   (kotoba `did_document_ipns_name`), tying the head to the actor's existing
   self-certifying DID (ADR-2606015600). Global, apex-independent discovery is the
   `KOTOBA_IPNS=kubo` path (republish to Kubo IPNS) — **operator-gated**, optional,
   and additive: the head is verifiable from any IPFS gateway because the record is
   signed.

# Consequences

- **The charter tension is resolved.** The head is a member-signed, content-addressed
  object; neither the DO nor a trusted KV value is the authority. ADR-2605262130 /
  2605312345 / 2605231525 hold.
- **Implementation gap (the real follow-on work).** kotoba-wasm today exposes only
  `commitSigned` → `{root, did, sig}` (a signature over the root CID), **not** a full
  `IpnsRecord` nor a commit-with-parent. Closing this needs:
  - **(upstream kotoba-wasm)** a binding that emits a member-signed `IpnsRecord`
    (using kotoba's own `IpnsRecord::sign_ed25519`, so the CBOR/signature are
    byte-identical to the Rust verifier) over a `DistributedDatomCommit` with the
    correct `parent`. This belongs in the canonical engine, NOT re-implemented in TS
    (avoids a parallel CBOR/sign path and guarantees interop).
  - **(apex)** `block.put` stores + `GET root` serves the `IpnsRecord`; the SW
    verifies it. `kroot:` JSON migrates to the stored record (still in KV, now as an
    untrusted cache).
- **Migration is non-breaking.** `kroot:` remains readable during cutover; the new
  path adds the signed record alongside, then the reader switches to verifying it.
- **Gating.** Live apex/SW deploy + Kubo IPNS republish are operator-gated
  (ADR-2606065500 deploy posture). The upstream wasm binding ships + is
  cross-verified (TS-produced record accepted by the Rust verifier, and vice-versa)
  before the apex switches authority to it.

# Alternatives Considered

- **Cloudflare Durable Object (`KotobaRoot`).** Rejected: operated trusted
  server-state; violates ADR-2605262130 / 2605312345 / 2605231525. Already removed
  from `wrangler.toml`; a re-introducing PR was closed.
- **Keep apex KV `kroot:` as authority.** Rejected as the *authority*: it is a
  trusted mutable value. Kept only as a **non-authoritative cache** of the signed
  record.
- **A new signed-head format in the apex Worker (TS).** Rejected: a parallel
  substrate (ADR-2605262130). The browser already runs kotoba-wasm and must emit the
  canonical `IpnsRecord` / `DistributedDatomCommit`.
- **DNSLink TXT → /ipfs/<headCID>.** Rejected: relocates the operated mutable state
  to operator-held DNS — no better (arguably worse) than KV on charter grounds.
- **Base L2 per-post head.** Rejected for the hot path (cost/latency); a periodic
  L2 anchor over the commit-DAG root remains available as finality (ADR-2605312345)
  and is orthogonal to this head primitive.

# References

- ADR-2606065500 (browser-only kotoba social feed; the OPEN question this closes)
- ADR-2606013600 (kotoba persistent IPNS graph heads — the mechanism reused here)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605262130 (kotoba storage substrate unification; no parallel substrate)
- ADR-2605231525 (no-server-key)
- `40-engine/kotoba/crates/kotoba-ipfs/src/ipns.rs` (`IpnsRecord`, registries)
- `40-engine/kotoba/crates/kotoba-datomic/src/distributed.rs` (`DistributedDatomCommit`)
- `50-infra/etzhayyim-did-web/src/kotoba-publish.ts` (apex publish handlers; `kroot:` interim)
