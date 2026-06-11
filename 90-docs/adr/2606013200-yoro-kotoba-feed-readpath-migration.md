---
id: adr-2606013200-yoro-kotoba-feed-readpath-migration
title: "ADR-2606013200: yoro feed read-path migration to kotoba Datom log (Phase 2.5) + public yoro-social graph"
status: active
doc_type: adr
topic: yoro-feed-kotoba-readpath
authoritative: true
last_verified: 2026-06-01
priority: 4.5
axis: architecture
weight: 0.45
priority_note: "Makes etzhayyim.com show posts/follows by reading the kotoba Datom log (canonical state) instead of the superseded kotoba-datomic-projection."
authoritative_for:
  - yoro-appview-feed-read-backend
  - yoro-social-kotoba-graph-schema
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2605311310-yoro-black-screen-spa-recursion-fix-and-ipfs-deploy-feasibility
related:
  - "00-contracts/schemas/yoro-feed-ontology.kotoba.edn"
  - "60-apps/etzhayyim-project-yoro/rw-free/src/kotoba.ts"
supersedes: []
superseded_by: []
---

# ADR-2606013200: yoro feed read-path migration to kotoba Datom log (Phase 2.5)

**Status**: active
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

After the black-screen fix (ADR-2605311310), `https://etzhayyim.com/` renders but
shows **no posts and no following**. Empirical trace:

- `etzhayyim-did-web` worker aliases `app.bsky.feed.*` → `com.etzhayyim.yoro.feed.*`
  and routes to the `yoro-xrpc-adapter` (service binding `YORO_XRPC`).
- The adapter delegates to `@etzhayyim/yoro-rw-free`, whose feed reads
  (`getDiscoverFeed` / `getTimeline` / `getAuthorFeed`) hit the **single-actor
  PDS MST + optional kotoba-datomic-projection** (`PROJECTION_DISCOVER_DID`, empty),
  and whose `getFollows` / `getFollowers` / `getProfile` / `getPostThread` /
  `searchActors` are **empty stubs**.
- The canonical design (ADR-2605262130 + 2605312345) makes the **kotoba Datom
  log the first-class canonical state**, read via `kotoba-kqe`; the
  kotoba-datomic-projection (ADR-2605231500) is **superseded**. The adapter never
  references kotoba, and no public kotoba endpoint exists.

So the feed is empty because (a) the read path was never migrated to kotoba
(Phase 2.5), and (b) there is no public kotoba endpoint to read from.

The running kotoba node (`127.0.0.1:8077`, launchd `com.etzhayyim.kotoba`)
exposes generic Datomic primitives over XRPC — `datomic.transact`,
`datomic.datoms` (indexes `:eavt/:aevt/:avet/:vaet`), `datomic.entity`, etc.
(`com.etzhayyim.apps.kotoba.datomic.*`). A graph is addressed by a multibase CID
(`KotobaCid::from_bytes(name).to_multibase()`); writes need operator-Bearer
auth (`sub == operator_did`, signature not verified); reads are gated by
per-graph visibility (`Public` / `Authenticated` / `Private`), default private.

# Decision

**Migrate the yoro feed read path to kotoba; ingest etzhayyim-internal content
as Datoms; expose only the yoro graph publicly.** Scope (chosen with the
operator): full migration of all 8 read functions, etzhayyim-internal content
only, public (no-auth) reads of the yoro graph.

1. **Schema** — a dedicated kotoba graph `yoro-social-v1`
   (CID `bafyreibljg5gzye47fldkfq6m4vgy55kcjyez2vx432dubttou36g5yryq`) holding
   `:yoro.post/* :yoro.profile/* :yoro.follow/*` Datoms. Unique-identity
   attributes (`:yoro.post/uri`, `:yoro.profile/did`, `:yoro.follow/uri`) make
   ingest idempotent. Schema SSoT:
   `00-contracts/schemas/yoro-feed-ontology.kotoba.edn`.

2. **Reader** — `@etzhayyim/yoro-rw-free` gains `src/kotoba.ts` (a thin HTTP
   client over `datomic.datoms`) and reads `kotobaUrl` + `yoroGraphCid` from
   `EtzhayyimConfig`. All 8 functions project from the Datom log; when
   `kotobaUrl` is unset they fall back to the existing PDS/projection path
   (graceful degrade — no behaviour change for non-kotoba callers).

3. **Ingest** — `rw-free/scripts/ingest-to-kotoba.ts` reads etzhayyim member
   repos (`app.bsky.feed.post` / `graph.follow` / `actor.profile`) from the
   etzhayyim PDS and `datomic.transact`s them as `:yoro/*` Datoms (operator
   Bearer). Continuous ingest (`KOTOBA_SUBSCRIBE_REPOS`, etzhayyim relay only)
   is a future replacement; this iteration is manual/cron.

4. **Public exposure** — the yoro graph is registered **Public** at
   kotoba-server boot (`NamedGraph::new("yoro-social-v1", Public)`, mirroring
   the kg graph) so reads need no auth; all other graphs on the node stay
   private. kotoba is published at `kotoba.etzhayyim.com` via the existing
   `etzhayyim-anvil` Cloudflare Tunnel. The adapter sets
   `KOTOBA_URL=https://kotoba.etzhayyim.com` + `YORO_GRAPH_CID`.

# Consequences

- The worker (`etzhayyim-did-web`) is unchanged — the alias path already routes
  feed NSIDs to the adapter.
- Reads become public for the yoro graph only; the node's other substrate
  graphs (cc / kg / email) remain `Private` (CACAO-gated) even though the node
  is now publicly reachable.
- **Availability** = the dev Mac's launchd daemon + tunnel (same posture as
  `geth.etzhayyim.com` / `pds.etzhayyim.com`). Not yet an HA service.
- **Content** is etzhayyim-internal only; the feed shows whatever member repos
  contain. Empty member repos ⇒ empty (but error-free) feed.
- Write auth is a soft gate (operator DID in `sub`, no signature check) — the
  current kotoba dev posture (ADR-2605231525 "no server key" tracked
  separately). Ingest runs operator-side.
- The two-line kotoba-server boot change lives in the `40-engine/kotoba`
  subrepo and requires a rebuild + binary reinstall + daemon restart
  (operator-gated).

# Alternatives Considered

- **Set `KOTOBA_DEFAULT_VISIBILITY=public` on the node.** Rejected: exposing the
  whole node's reads (cc/kg/email) publicly when it is tunnel-published. Per-graph
  Public is the least-broad option.
- **Adapter sends a CACAO for private-graph reads.** Rejected: requires the
  owner signing key in the Worker (no-server-key violation); the feed graph is
  public content anyway.
- **Keep reading the atproto AppView (`atproto.etzhayyim.com`).** Rejected: it
  contradicts ADR-2605262130 (kotoba = canonical state) and its discover feed is
  also empty; this migration is the canonical fix, not a detour.
- **Register the yoro graph at runtime via XRPC.** No such endpoint exists;
  registration is boot-time code (`graph_registry`). Hence the subrepo change.

# References

- ADR-2605262130 (kotoba storage substrate unification — canonical state)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605231902 (feed-post membrane + feed-discover projection — superseded read leg)
- ADR-2605311310 (yoro black-screen fix + IPFS-deploy feasibility)
- `00-contracts/schemas/yoro-feed-ontology.kotoba.edn` (schema SSoT)
- kotoba XRPC: `40-engine/kotoba/crates/kotoba-server/src/xrpc.rs` (`datomic.*`)
