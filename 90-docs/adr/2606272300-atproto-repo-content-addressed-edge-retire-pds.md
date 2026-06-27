---
id: adr-2606272300-atproto-repo-content-addressed-edge-retire-pds
title: "ADR-2606272300: Serve the actor AT-repo content-addressed from the edge; retire the stateful PDS"
status: proposed
doc_type: adr
topic: atproto-repo-content-addressed-edge
authoritative: true
last_verified: 2026-06-27
priority: 7.0
axis: architecture
weight: 0.50
priority_note: "Realigns AT-Proto serving to the canonical browser-complete / edge-thin / no-server-state architecture; removes a server-state primitive the design forbids."
authoritative_for:
  - atproto-repo-serving
  - pds-retirement
depends_on:
  - 2605262130  # kotoba = canonical substrate; no RisingWave; browser-only kotoba
  - 2605312345  # kotoba Datom log = first-class canonical state; IPFS=block backend, MST=wire, L2=anchor
  - 2606242400  # GitHub-Pages CAR blockstore + CID query tier (content-addressed static serving)
  - 2606271400  # leash-everywhere + single consent gate (the member-signed-record discipline)
related:
  - 50-infra/etzhayyim-did-web/src/{car,cbor,kotoba,identity,xrpc-routes}.ts  # the edge machinery already present
  - 50-infra/etzhayyim-atproto-pds-clj/  # the stateful clj PDS being retired
  - deps.edn  # tier-0 "Cloudflare as thin CDN; persistent state in MST/IPFS/L2"
supersedes: []
superseded_by: []
---

# ADR-2606272300: Serve the actor AT-repo content-addressed from the edge; retire the stateful PDS

**Status**: proposed
**Date**: 2026-06-27
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

To make `atproto.etzhayyim.com` public (so etzhayyim's autonomous actor posts are world-readable),
a session on 2026-06-27 stood up the **independent clj PDS** (`50-infra/etzhayyim-atproto-pds-clj`)
as a stateful server — first on the founder's laptop, then migrated to the always-on `asher`
fleet node (`bb serve` + a Cloudflare Tunnel). It works: `did:web:atproto.etzhayyim.com` resolves
and serves the member-attributed records (author = the consenting member's `did:key`, via the
CACAO leash, no-server-key at the write layer).

**But a stateful PDS server contradicts the canonical etzhayyim architecture.** The substrate is
explicitly browser-complete / edge-thin / no-operated-server-state:

- `deps.edn` tier-0: **"Cloudflare Workers / Pages (CDN as thin layer; persistent state in
  MST/IPFS/L2)"**. State is content-addressed, not a server.
- ADR-2605262130 / 2605312345: the **kotoba Datom log is the first-class canonical state**
  (content-addressed EAVT); **IPFS = block backend, MST = ingress/interop wire, Base L2 =
  anchor**. kotoba is **browser-only** ("IPFS blocks + kotoba-wasm in the page/SW, **NOT a
  server**"); **Durable Objects are NOT used — no operated server-state primitive**.
- The apex `etzhayyim-did-web` Worker **already carries the content-addressed serving machinery**:
  `car.ts` (CARv1 + dag-pb/UnixFS verify), `cbor.ts` (dag-cbor), `cid.ts` (CID verify),
  `identity.ts` + `resolveActorRecord` (record-by-CID from `ACTOR_KV` / kotoba pull, **no central
  node**), the trustless `/ipfs/<cid>` gateway, `[assets] directory = "./public"` static serving,
  and the **Method-A `XRPC_PDS_UPSTREAM`** cutover var (currently **INERT**). The PDS is merely a
  **fallback upstream** the apex proxies to — and a server-state primitive the design avoids.
- did.json already advertises each actor's `#atproto_pds` service (`worker.ts:935`,
  `serviceEndpoint: https://pds.etzhayyim.com`) — i.e. the repo location is a *pointer*, freely
  re-aimable at a stateless edge endpoint.

So the founder's question — *"wasn't etzhayyim.com designed so Svelte runs on Cloudflare and
kotoba queries run in WASM? Isn't the PDS unnecessary?"* — is **correct**. The PDS is the wrong
end-state; the canonical model serves the AT-repo **content-addressed from the edge**, queried by
**kotoba-wasm**, with **no operated server**.

# Decision

Serve the actor AT-repo **content-addressed from the Cloudflare edge** (the apex did-web Worker),
and **retire the stateful clj PDS**. The four parts:

### D1 — Records are member-signed and content-addressed (no PDS write surface)
A member signs each record client-side (WebAuthn / their own key — the ADR-2606271400 leash
discipline, no platform key). The record lands on the **kotoba Datom log** and is packed to a
**content-addressed CARv1 / dag-cbor** artifact (the AT-Proto repo commit-DAG + MST), CID-pinned.
Publication targets the apex's content-addressed store: **`ACTOR_KV`** (record-by-CID) and/or the
**`./public` static CAR tier** (ADR-2606242400 pages-store, HTTPS-Range, no IPFS daemon) and/or an
**IPFS pin**. No stateful server holds a key or mutable repo state.

### D2 — The apex Worker serves the AT-repo families statelessly
The apex did-web Worker answers the repo/sync XRPC families
(`com.atproto.sync.{getRepo,getRecord,getLatestCommit,listRepos}` +
`com.atproto.repo.{getRecord,listRecords}`) by reading the **content-addressed store**, reusing
the machinery already in `src/{car,cbor,cid,identity}.ts` + `resolveActorRecord`. Each actor's
did.json `#atproto_pds` `serviceEndpoint` is flipped from `https://pds.etzhayyim.com` to
**`https://etzhayyim.com`** (the apex itself). No central node; verification is by CID. (Full
bsky-federation-grade `subscribeRepos` firehose stays out of scope — the goal is resolvable,
content-addressed, world-readable repos, not a relay.)

### D3 — Retire the stateful PDS + its tunnel
Decommission `50-infra/etzhayyim-atproto-pds-clj`'s running instances (the asher / laptop
`bb serve` + the `etzhayyim-pds` Cloudflare Tunnel + the LaunchAgents). Drop the
`XRPC_ATPROTO_UPSTREAM → PDS` proxying for the repo families (the apex serves them now). The
`atproto.etzhayyim.com` host is no longer a server — resolution moves to the apex
(`etzhayyim.com`) per the flipped service endpoint.

### D4 — Queries stay kotoba-wasm (unchanged)
Read/query of actor data is **kotoba-wasm in the browser / Service Worker** over the
content-addressed Datom log (the canonical read path, ADR-2605262130). The Svelte app on
Cloudflare Pages + kotoba-wasm needs no server.

# Consequences

- **No operated server-state primitive** — realigns with tier-0 (edge-thin) + the DO-free
  invariant. The org holds no mutable AT-repo server.
- **True durability, zero uptime dependency** — served by Cloudflare's global edge + the
  content-addressed store (KV / static CAR / IPFS). No always-on node, no laptop, no `asher`
  reboot to survive. This is *stronger* durability than "run a PDS on an always-on node."
- **no-server-key preserved structurally** — the member signs records client-side; the edge holds
  no signing key (it serves bytes, verified by CID).
- **Content-addressed + tamper-evident** — every record is fetched-and-verified by CID; the apex
  is a trustless gateway, not an authority.
- **Honest scope limit** — this serves *resolvable, readable* repos, not a full federating relay
  (`subscribeRepos`). External AT indexers that require a firehose are out of scope until a
  separate relay decision.
- **Migration risk** — the cutover must not drop `atproto.etzhayyim.com` resolution. Staged below
  so the PDS stays serving until the edge path is verified.

# Staged execution (atproto never goes down)

1. **Publish** — export the current member-signed records from the running PDS
   (`com.atproto.sync.getRepo` → CAR) → content-address → push to `ACTOR_KV` / `./public` /
   IPFS pin. (The records keep their member `:author`.)
2. **Wire + deploy (flagged)** — implement the apex repo/sync handlers reading the store; deploy
   the apex Worker (account `ai-gftd-cloud`, reachable). Keep the PDS as the unflipped fallback.
3. **Verify** — external AT resolution of `did:web:etzhayyim.com:actor:*` via the apex returns the
   member-attributed records (getRepo / listRecords / getRecord), CID-verified.
4. **Flip + retire** — set did.json `#atproto_pds` → `https://etzhayyim.com`; decommission the
   asher/laptop PDS + the `etzhayyim-pds` tunnel + LaunchAgents; remove the repo-family
   `XRPC_ATPROTO_UPSTREAM` proxy.

# Alternatives Considered

1. **Keep the stateful clj PDS on an always-on node (status quo of the 2026-06-27 session).**
   Rejected as the end-state: it is a server-state primitive the architecture forbids
   (tier-0 edge-thin, DO-free, browser-only kotoba), and its uptime depends on a node staying up.
   It remains useful as the *interim* serving + the migration source (Step 1).
2. **A managed / hosted bsky PDS.** Rejected: custodial, server-held key, off-substrate.
3. **Apex proxies to the PDS forever (`XRPC_ATPROTO_UPSTREAM`).** Rejected: still requires the
   always-on stateful PDS behind it; doesn't remove the server-state primitive.

# References

- `deps.edn` — tier-0 "Cloudflare as thin CDN; persistent state in MST/IPFS/L2"
- ADR-2605262130 / 2605312345 — kotoba canonical state; browser-only; IPFS/MST/L2 layering; DO-free
- ADR-2606242400 — GitHub-Pages CAR blockstore + CID query tier (content-addressed static serving)
- ADR-2606271400 — leash-everywhere + member-signed records (no-server-key write discipline)
- `50-infra/etzhayyim-did-web/src/{car,cbor,cid,identity,xrpc-routes}.ts` — the edge machinery
- `50-infra/etzhayyim-atproto-pds-clj/` — the stateful PDS being retired
