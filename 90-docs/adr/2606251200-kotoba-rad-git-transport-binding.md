---
id: adr-2606251200-kotoba-rad-git-transport-binding
title: "ADR-2606251200: kotoba-rad ⇄ git transport — rad-rooted push auth, sigref⇄ref attestation, gossip phases"
status: proposed
doc_type: adr
topic: kotoba-rad-git-transport-binding
authoritative: true
last_verified: 2026-06-25
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Wires the kotoba-rad sovereign identity (RID / did:key / sigref) into the EXISTING kotoba-git smart-HTTP transport so a member key — not the node operator — governs push, and stages the p2p (gossip) path that the original kotoba-rad ADR left as its one open gap."
authoritative_for:
  - kotoba-rad-git-transport-binding
  - rad-rooted-git-push-auth
  - rad-sigref-git-ref-attestation
depends_on:
  - adr-2606231200  # kotoba-rad — sovereign per-actor repo identity (RID/did:key/sigref schema)
  - adr-2605312345  # member-signed block CAS / Datom-first-class state (sigref = signed CAS head)
  - adr-2606015000  # git ↔ kotoba bridge (git objects as CID blocks + :git/* Datom projection)
  - adr-2606036400  # libp2p webrtc-direct transport phases (browser ↔ node, no signaling)
related:
  - adr-2605231525  # did:web multi-controller / no-server-key
supersedes: []
superseded_by: []
---

# ADR-2606251200: kotoba-rad ⇄ git transport — rad-rooted push auth, sigref⇄ref attestation, gossip phases

**Status**: proposed
**Date**: 2026-06-25
**Deciders**: Jun Kawasaki

# Context

ADR-2606231200 implemented the **Radicle-shaped identity model** (`kotoba-rad`:
RID / `did:key` / sigref / identity journal) in `70-tools/src/etzhayyim/
kotoba_rad.cljc`, and explicitly deferred the one missing Radicle capability —
**p2p gossip replication** — while noting code distribution (A-axis) would run
through josh + GitHub. That ADR framed `kotoba-rad` as "the Radicle data model
*without* the Radicle network."

Re-survey (2026-06-25) shows the picture is better than that framing implied:
a **real git transport already exists**, as a *separate* stack from the cljc
identity layer, and the two are simply **not wired together**.

- **`com-junkawasaki/kotoba/crates/kotoba-git`** stores every git object's exact
  framed bytes (`<type> <size>\0<body>`) as a `KotobaCid` block (SHA-1 ↔ CID
  round-trip byte-exact) and projects `:git/*` datoms. It implements **git
  smart-HTTP v0**: `wire::{advertise_refs, upload_pack, receive_pack}`, pkt-line,
  pack encode/ingest — with integration tests that drive the **real `git`
  binary** through clone / fetch / push.
- **`crates/kotoba-server/src/git_http.rs`** mounts those over HTTP:
  `GET /git/:repo/info/refs`, `POST …/git-upload-pack`, `POST …/git-receive-pack`.
  Reads are gated by the node read policy; **push** by `push_gate`, which today
  roots authority at the node's single `state.operator_did` via three tiers:
  (1) `KOTOBA_GIT_ALLOW_ANON_PUSH=1`, (2) a CACAO granting `git.receive/push` on
  scope `git/repo/<repo>` **rooted at `operator_did`**, (3) an operator Bearer JWT.
- **`crates/kotoba-net`** already has `gossipsub`, `bitswap`
  (`/kotoba/bitswap/1.0.0`), a sync protocol, and a libp2p swarm; the
  `70-tools/kotoba-webrtc-poc` proved browser ↔ rust **webrtc-direct** with no
  signaling server (ADR-2606036400).

So the real gaps are narrow and specific:

1. **`<repo>` is an arbitrary string**, not the rad **RID**. Per-repo connection
   key and auth scope are a human name, unmoored from the sovereign identity.
2. **Push authority is the node operator**, not the repo's **rad delegates**.
   A repo's `did:key` holders cannot authorize their own pushes; the node owner
   can. This is the inverse of "sovereign."
3. **The git head and the rad sigref are disconnected.** A successful push
   updates `:git/*` refs but mints no sigref, so the rad journal's signed head
   does not track the actual repo head — and all 164 existing
   `80-data/kotoba-rad/*.identity.journal.edn` are **unsigned** (`:rad/sig` ∅).
4. **Replication is centralized** (one HTTP node), not gossip.

Items 1–3 are the **git-transport binding** (this ADR's Decision). Item 4 is the
**gossip** path, staged here and carried forward.

# Decision

**Bind `kotoba-rad` identity to the existing `kotoba-git` transport so a member's
`did:key` (via CACAO), rooted in the repo's rad delegates, governs push — and the
resulting head is recorded as a signed rad sigref. Then stage p2p replication on
top, reusing that same auth.** No new ledger, no second auth scheme, no
`radicle-node`.

## (a) The binding — three connection points

### A-1. Repo identity = RID

The git `:repo` path segment resolves to a rad **RID** (`= cid/cid-of-edn` of the
genesis block). The per-repo `kotoba_datomic::Connection` key and the CACAO scope
become `git/repo/<RID>` (was `git/repo/<name>`). The human name
`com-etzhayyim-<name>` resolves to its RID through a **rad registry** projected
from `80-data/kotoba-rad/*.identity.journal.edn` (genesis + delegates +
threshold). RID is the canonical key; the name is a convenience alias.

### A-2. Push authority root = rad delegates (not node operator)

Replace `push_gate`'s `&state.operator_did` root with the **repo's rad delegate
set**. A new gate

```
verify_cacao_rad_push(cacao_b64, rid, delegates, threshold) -> Result<…>
```

(built on the existing `graph_auth::verify_cacao_for_capability` /
`kotoba_auth::DelegationChain`) accepts the push iff the CACAO grants
`git.receive/push` on scope `git/repo/<RID>`, its delegation chain **roots at one
of `:rad/delegates`**, and `:rad/threshold` (m-of-n) is met. The node operator
tier is kept only as a fallback for un-bound repos.

**did:key reconciliation — already solved.** `kotoba-rad` uses the in-repo
`did:key:z<hex>` form (kotoba.cljs verifier); `kotoba-auth` uses the W3C
multibase `z6Mk…` form. ADR-2606231200 deferred a converter as "a later add" —
but it **already exists, fully tested**, in `kotoba-auth/src/did_key.rs`:
`parse_ed25519_did_key` accepts *both* forms and `did_keys_equal` /
`to_canonical_did_key` compare by key across encodings. So A-2 reuses it; no new
converter is built. (Verified 2026-06-25 — the rad `z<hex>` form is exactly the
"kotoba-wasm hex form" that module already round-trips.)

**Status (2026-06-25): A-1 + A-2 are implemented and wired.** In `kotoba-server`:
- `graph_auth::verify_cacao_rad_push(cacao_b64, rid, delegates, aud, nonce_store)`
  — the rad-rooted verify primitive. 6 unit tests (accept delegate in standard
  form; **accept a delegate listed in rad `z<hex>` form against a standard-form
  issuer**; reject non-delegate / wrong capability / wrong repo scope / empty
  delegate set) — green.
- `rad_registry::RadRegistry` — projects `80-data/kotoba-rad/*.identity.journal.edn`
  (read with `kotoba_edn::parse_all`) into a RID-keyed map of `:rad/delegate`
  holders, resolving a git repo segment by RID / `rad:<RID>` / name /
  `com-<org>-<name>` slug (delegate-source decision: **journal → node datom
  projection**). Loaded once from `KOTOBA_RAD_JOURNAL_DIR`. 4 unit tests green
  (projects delegates + skips `sigref:*`; resolution forms; hyphenated-name via
  org-prefix strip; missing dir → empty).
- `git_http::push_gate` — now tries the **sovereign path first**: if the repo
  resolves to a rad identity *with delegates*, authorize via `verify_cacao_rad_push`
  rooted in those delegates; otherwise fall through to the existing operator path.
  Purely additive — the `git_cacao_push` integration test (operator-rooted) still
  passes.

**A-3 is implemented and proven end-to-end.** `rad_registry::attest_sigref`
appends a five-datom signed sigref (`:rad/type :sigref` / `:rad/rid` / `:rad/head`
/ `:rad/by` / `:rad/sig`) to the repo's journal, re-reading the file to bump `tx`;
`git_http::rad_attest_push` calls it from `receive_pack` on success (best-effort —
a write-back failure never fails the push). The `:rad/head` is the KotobaCid of
the new git head; `:rad/by` is the CACAO issuer; `:rad/sig` is the push CACAO
itself (the member signature — no-server-key). Integration test
`tests/git_rad_sigref.rs` drives the real `git` CLI: a **non-delegate CACAO is
rejected**, a **delegate's CACAO authorizes the push** (delegate listed in rad
`z<hex>`, issuer in `z6Mk…` — cross-encoding through the live HTTP gate), and a
signed sigref with the correct `:rad/by` / `:rad/sig` lands in the journal.

**Delegate provisioning (cljc) is implemented.** Two paths now populate
`:rad/delegate`:
- **fresh publishes** — `actor_publish.cljc::manifest->genesis` already threads
  `--pubkey=<hex>` into `:delegates`, so `bb actor:publish <name> --apply
  --pubkey=<hex>` bakes the delegate into genesis.
- **retrofit (RID-stable)** — `kotoba_rad.cljc::add-delegate!` APPENDS a
  `:rad/delegate` datom to an existing journal **without touching the genesis**
  (so the RID is unchanged — ADR-2606231200's "delegate 追加は追記"), plus a fresh
  member-signed sigref. Driven by `bb actor:delegate-add <name> (--keygen |
  --pubkey=<hex>) [--apply]` (`kotoba_rad_sign.clj::-delegate-add`, DRY-RUN by
  default, key in macOS Keychain — no-server-key). Verified: RID-stable,
  idempotent-by-value, append-only; `bb test:kotoba-rad` 25/25 green.

This closes the retrofit gap for the 164 delegate-less pilot journals — running
`actor:delegate-add` makes a repo's sovereign git push (a)/(A-2) live.

**Remaining:** (b) gossip phases G1–G4 (sigref announce → bitswap object fetch →
browser peers → kad discovery), which reuse (a)'s did:key/CACAO delegate model.

### A-3. sigref ⇄ git ref attestation

On a successful `receive_pack`, after `git_persist`, append a rad **sigref
datom** to the RID's journal:

```clojure
{:rad/type :sigref
 :rad/rid  "<RID>"
 :rad/head "<new git head CID>"
 :rad/by   "<pusher did:key>"
 :rad/sig  "<the push CACAO>"}      ; the CACAO IS the signature
```

The **push CACAO itself is the member signature** — no-server-key is preserved
(the server only *verifies*, never mints). This closes the loop: the rad
journal's signed head now equals the git ref head, signed by a rad delegate.
`70-tools/.../kotoba_rad.cljc`'s `:sign-fn` seam flips from "publish UNSIGNED +
warn" to "emit a `git.receive/push` CACAO for scope `git/repo/<RID>`," fed by the
member key in Keychain / 1Password; `actor_publish.cljc` uses it.

### Net effect

```
member key (Keychain/1Password)
  → CACAO { cap: git.receive/push, scope: git/repo/<RID>, iss rooted in :rad/delegates }
  → git -c http.extraHeader="x-kotoba-cacao: <b64>" push http://node/git/<RID>
  → push_gate: verify_cacao_rad_push(rid, delegates, threshold)   ✅ sovereign
  → receive_pack → git objects land as CID blocks (+ :git/* datoms)
  → rad_attest: append signed :rad/sigref { head, by, sig }       ✅ signed head
```

The previously-true statement "signatures are **un-wired**" becomes false:
signing is now the push path, not a separate ceremony.

## (b) Gossip — staged, reusing (a)'s auth

The substrate already carries both halves of Heartwood-style gossip (announce
**signed refs** + fetch **objects by CID**). Stage it; do **not** invent a second
auth model — gossip payloads are exactly the (a) signed sigrefs.

| Phase | Scope | Builds on |
|------|-------|-----------|
| **G0** (today) | central smart-HTTP transport; sigref in journal. R3 / `--no-network` degenerate. **Works.** | — |
| **G1 — sigref announce** | gossipsub topic `kotoba/rad/sigref/<RID>`; publish the signed sigref datom on push. Subscribers verify the sig against the genesis delegates and record the head. **No object transfer yet.** CAS conflict resolved by the existing member-signed-CAS rule. | (a) A-2/A-3, `kotoba-net::gossipsub` |
| **G2 — object fetch** | for a head CID a peer lacks, walk the commit DAG (kotoba-git reachability) and `want` missing object CIDs over the existing `/kotoba/bitswap/1.0.0`. Git objects are already CID blocks → full p2p replication, no HTTP node. | G1, `kotoba-net::bitswap` |
| **G3 — browser peers** | fold webrtc-poc into `kotoba-net` (ADR-2606036400 Phase 1: multi-listen + certhash advertise); browser subscribes + bitswap-fetches; in-frame CACAO auth (`/kotoba/mcp/1.0.0`) **reuses (a)'s did:key delegate model**. | (a), G2, ADR-2606036400 |
| **G4 — discovery** | Kademlia/DHT provider records keyed by RID for bootstrap-free peer discovery. **kad is not yet in `kotoba-net` — new dependency.** | G3 |

Ordering is forced: **(a) first**, because G1/G3 authorization *is* (a)'s
`did:key`/CACAO delegate check, and the gossip payload *is* (a)'s signed sigref.

# Consequences

**正**
- Push authority is **sovereign**: a repo's `did:key` delegates authorize their
  own pushes; loss of the node operator (or the node) does not revoke them.
- **Signing becomes the default path**, not an unused seam — the 164 unsigned
  journals get a signing route (re-attest on first authenticated push).
- One auth model spans HTTP push *and* p2p gossip (no divergence).
- Reuses the entire existing transport (kotoba-git smart-HTTP + kotoba-net
  gossipsub/bitswap); net-new code is the binding glue + the did:key converter.

**負 / リスク**
- **Genesis-delegate provenance / bootstrap**: the node must read each RID's
  genesis (delegates, threshold) to authorize. Open question — replicate the
  journal through the same mechanism, or project it into the node datom DB. Until
  resolved, the operator tier remains the fallback.
- **Concurrent CAS under m-of-n**: today `:rad/threshold` is 1, which sidesteps
  two delegates racing distinct heads. Real m-of-n needs the conflict/quorum rule
  pinned before G1 goes multi-delegate.
- **did:key converter** is now on the trust path for both (a) and (b); a bug
  there is an auth bug. Must be exhaustively round-trip tested.
- **G4 adds Kademlia** to `kotoba-net` — a real dependency/compatibility surface
  on the pinned libp2p line.
- This remains **not wire-compatible with radicle.xyz**; we still do not claim
  "Radicle compatible" (per ADR-2606231200).

# Alternatives Considered

- **Keep operator-rooted push, record sovereignty only in `alsoKnownAs`** (R3
  anchor-only). Rejected: push authority stays with the node owner — not
  sovereign; the sigref/head loop stays open.
- **A second, git-specific signing scheme** (e.g. sign refs separately from the
  push). Rejected: duplicates the CACAO/`did:key` machinery and forks gossip auth
  from HTTP auth. The push CACAO already is a member signature; reuse it.
- **Run a real `radicle-node` for transport.** Rejected for the same reason as
  ADR-2606231200 R1 — a second DAG/ledger beside ATProto + kotoba-git.
- **Gossip before binding.** Rejected: gossip would have no signed payload and no
  auth root to verify against; it must carry (a)'s sigrefs.

# References

- `com-junkawasaki/kotoba/crates/kotoba-git/src/{lib,wire/smart_http,pack}.rs` — git smart-HTTP transport + CID-block object store
- `com-junkawasaki/kotoba/crates/kotoba-server/src/git_http.rs` — HTTP mount + `push_gate` (auth root to be moved rad-ward)
- `com-junkawasaki/kotoba/crates/kotoba-server/src/graph_auth.rs` — `verify_cacao_for_capability` / `require_operator_auth` (reused by A-2)
- `com-junkawasaki/kotoba/crates/kotoba-server/tests/git_cacao_push.rs` — existing CACAO `git.receive/push` test (to extend rad-rooted)
- `com-junkawasaki/kotoba/crates/kotoba-net/src/{gossipsub,bitswap,swarm}.rs` — G1/G2 substrate
- `70-tools/src/etzhayyim/kotoba_rad.cljc` — genesis / RID / did:key / sigref / `:sign-fn` seam
- `70-tools/kotoba-webrtc-poc/` — G3 transport PoC (ADR-2606036400)
- ADR-2606231200 — kotoba-rad sovereign identity (the model this ADR binds to transport)
