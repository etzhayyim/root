# yoro rw-free

Phase E Option B reference implementation of yoro (federated social feed actor) on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md), yoro migrates from vendor's `createKyselyDb` pattern (RW direct write) to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **23 of 23 (100%)** yoro canonical XRPC commands ported.

| Namespace | Commands | Count |
|---|---|---|
| Root | projectEntity, productResearch, activitySeen, health, listApps, shinkaEvolution, stats, ingestProductCategory, shinkaKnowledge, listProductResearch, listPosts | 11 |
| activity/ | listActivities, getActivityTrace, markSeen | 3 |
| feed/ | getTimeline, getAuthorFeed, getPostThread, getRankedFeed, getDiscoverFeed | 5 |
| graph/ | getFollowers, getFollows | 2 |
| actor/ | getProfile, searchActors | 2 |

All 23 canonical yoro lexicons now have rw-free reference impl. Wire-up to a Worker / LangServer pod XRPC handler is the next operator task per ADR-2605203000.

## Authority-chain DIDs (per yoro design)

```
did:web:yoro.etzhayyim.com                         — controller
did:web:yoro.etzhayyim.com:project:{projectId}    — Project
did:web:yoro.etzhayyim.com:research:{jobId}       — Product Research
did:web:yoro.etzhayyim.com:seen:{objectId}        — Activity Seen
did:web:yoro.etzhayyim.com:app:{appId}            — App
did:web:yoro.etzhayyim.com:evolution:{nanoid}     — Shinka Evolution
did:web:yoro.etzhayyim.com:knowledge:{nanoid}     — Shinka Knowledge
did:web:yoro.etzhayyim.com:post:{postId}          — Post
did:web:yoro.etzhayyim.com:activity:{activityId}  — Activity
```

## Storage

Yoro metadata is stored on PDS. No IPFS pointers. Phase 3 mst-projector may add aggregate views for feed ranking / graph traversal.

## Pattern translation (Option B)

| Vendor (`yoro.etzhayyim.com`) | etzhayyim (this PR) |
|---|---|
| `const db = createKyselyDb();` | `import type { Etzhayyim } from "@etzhayyim/sdk"` |
| `db.insertInto("vertex_yoro_*").values({...}).execute()` | `e.write({ collection: "com.etzhayyim.yoro.*", record, rkey })` |
| `db.selectFrom("vertex_yoro_*").where(...).execute()` | Read query methods (getTimeline, getProfile, etc.) stub to pod LangServer |

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import { projectEntity, health, getTimeline, getProfile } from "@etzhayyim/yoro-rw-free";

const e = new Etzhayyim({
  did: "did:web:yoro.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
});

// Register a project entity
const projectResp = await projectEntity(e, {
  projectId: "project-123",
  entityType: "brand",
  entityId: "entity-456",
});
// → { uri: "at://...", rkey: "entity-project-123-entity-456" }

// Check health
const healthResp = await health(e);
// → { ok: true, app: "yoro", ts: "2026-05-21T..." }

// Get personalized timeline (stub to pod)
const timelineResp = await getTimeline(e, { limit: 50 });
// → { feed: [], cursor: undefined } (queries pod on wire-up)

// Get actor profile (stub to pod)
const profileResp = await getProfile(e, { actor: "did:plc:..." });
// → { profile: {...} } (queries pod on wire-up)
```

## Why Option B for yoro

Per ADR-2605203000 Phase E decision matrix:
- **Catalog**: federated social metadata (posts / profiles / follows) — open standard (AT Protocol)
- **Write cadence**: high — feed composition + actor follows + product research ingests
- **Query pattern**: complex (timeline / ranking / search) — indexed by RisingWave mst-projector Phase 3

Option A (vendor RW mirror) rejected — ADR-2605172000 mandates rw-free.
Option C (IPFS-only) N/A — no blob storage needed for metadata.

## What this package IS / ISN'T

**IS**:
- Reference impl of 23 yoro commands on Option B (PDS XRPC).
- Documentation of the createKyselyDb → e.write() translation.
- Scaffold for all yoro XRPC namespaces (root, activity, feed, graph, actor).

**ISN'T**:
- A deployed Worker (scaffold-only).
- Full implementation of feed ranking / recommendation engine (stubs for pod integration).

## Related

- [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md) — Phase E write-target options
- [ipaddress rw-free](../../etzhayyim-project-ipaddress/rw-free/) — sibling Option B reference (37+ commands)
- [anime rw-free](../../etzhayyim-project-anime/rw-free/) — Option B reference (10/10 ✓)
- [hanrei rw-free](../../etzhayyim-project-hanrei/rw-free/) — Option B reference (31/31 ✓)
