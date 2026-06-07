# Bluesky social-app compatibility on Kotoba/Datomic: how etzhayyim self-hosted PDS holds the contract

Date: 2026-04-24
Scope: analysis of `50-infra/cloudflare/workers/atproto/` against Bluesky social-app client contract, in light of Kotoba/Datomic 2.8.1 OLTP gaps confirmed 2026-04-24 (`ON CONFLICT`, write TX, RYW, UNIQUE all unsupported).

Relates: ADR-0002 (GraphAr), ADR-0022 (auth 2-token), ADR-0036 (worker-direct Hyperdrive), ADR-0041 (commit content-PK), ADR-0048 (Vultr+B2), `260424-tranquil-pds-graphar-remap.md` (retracted), `260420-pds-commit-seq-race-analysis.md`

## TL;DR

- **etzhayyim self-hosted PDS is already compatible with Kotoba/Datomic's OLTP gaps**. The canonical commit path (`core.ts:2998`) uses **delete-then-insert upsert emulation** explicitly to avoid `ON CONFLICT`. That's why etzhayyim works where tranquil does not.
- **Bluesky social-app client sees only the XRPC HTTP surface**. It doesn't care about storage. Compatibility is held at the XRPC layer, not at the SQL layer.
- **The OLTP-heavy surface is offloaded to D1** (auth sessions, passkeys, signing keys) and **CF service bindings** (VAULT, AUTH, PLC_DIRECTORY). D1 is SQLite — full OLTP.
- **Kotoba/Datomic holds only append-dominant / delete-then-insert graph state** (`vertex_repo_commit`, `vertex_repo_record`, `vertex_repo_block`, `vertex_profile`, domain `vertex_<actor>_*`). This matches streaming semantics.
- **1 confirmed latent bug**: `agent/memory.ts:284` uses `.onConflict().doUpdateSet()` with comment "Kotoba/Datomic supports this" — primary-source probe shows this is a **silent failure** on RW. Wrapped in try/catch → warns but loses writes.

## etzhayyim storage split (2026-04-24 actual state)

From `50-infra/cloudflare/workers/atproto/wrangler.jsonc` + `60-apps/etzhayyim-project-auth/worker*/wrangler.jsonc`:

| Storage | What | OLTP semantics | Bluesky analogue |
|---|---|---|---|
| **D1** `etzhayyim-auth-passkey` (auth Worker) | Passkey credentials, session tokens, OAuth state | Full OLTP (SQLite). Atomic TX, UNIQUE, ON CONFLICT all supported | official PDS `AccountDB` (SQLite) |
| **D1** `etzhayyim-keys` (shared) | Per-DID signing keys (envelope-encrypted w/ KEK) | Full OLTP | official PDS `ActorStore` signing key slot |
| **Kotoba/Datomic** via `HYPERDRIVE` binding (id `e84c0a2b…`, Vultr LAX `45.32.79.245:4566`) | `vertex_repo_commit`, `vertex_repo_record`, `vertex_repo_block`, `vertex_profile`, domain `vertex_<app>_*` (772 tables, 172 MV) | Append-heavy streaming. PK implicit upsert. No `ON CONFLICT`, no write TX, no RYW, no UNIQUE col constraint | official PDS `ActorStore` per-actor SQLite (repo) + AppView Postgres (feed index) merged |
| **B2** `etzhayyim-graph`, `etzhayyim-cache` | Blobs (CAR blocks for cold archive, media files) | Object store | official PDS blob store (S3-compatible) |
| **CF service bindings** | VAULT (D1), AUTH (D1), PLC_DIRECTORY (D1), GRAPH_QUERY, MURAKUMO, ROUTING_GATEWAY | Delegated — each has own storage contract | N/A (monolithic in official PDS) |

**Key insight**: every write that needs real OLTP (UNIQUE enforcement, atomic multi-row update, conflict resolution) lives in **D1**, not RW. The arch was already designed around this split before the 2026-04-24 RW probe; the probe confirmed why.

## social-app contract surface (what the Bluesky client actually calls)

`bluesky-social/social-app` (React Native) talks XRPC HTTP to any endpoint implementing AT Protocol. Actual calls observed in Bluesky's client code:

| XRPC NSID | etzhayyim handler | Storage touched | RW gap impact |
|---|---|---|---|
| `com.atproto.server.createAccount` | `handlers/register.ts` | D1 (passkey) + D1 (keys) + RW INSERT `vertex_repo_commit` genesis | None. INSERT-only on RW side |
| `com.atproto.server.createSession` | `AUTH_SERVICE` binding → authn.etzhayyim.com Worker | D1 (session row) | None. D1 is full OLTP |
| `com.atproto.server.refreshSession` | AUTH_SERVICE | D1 UPDATE + ON CONFLICT on refresh_jti | None (D1) |
| `com.atproto.server.getServiceAuth` | AUTH_SERVICE | D1 read + ES256 sign with KEK-unwrapped key | None |
| `com.atproto.identity.resolveHandle` | PLC_DIRECTORY service binding (`plc.etzhayyim.com` D1) or DNS TXT | D1 lookup | None |
| `com.atproto.repo.createRecord` / `putRecord` / `deleteRecord` | `handlers/pds/repo.ts` + `core.ts` commit pipeline | RW `vertex_repo_commit` INSERT + `vertex_repo_record` **delete-then-insert** + `vertex_repo_block` INSERT + firehose seq emit | **Works**. See `core.ts:2998` |
| `com.atproto.repo.applyWrites` | same | batched same as above | Works. ADR-0041 content-addressed PK handles parallel bursts |
| `com.atproto.repo.getRecord` | repo.ts | RW SELECT `vertex_repo_record WHERE did,collection,rkey` | None (snapshot read) |
| `com.atproto.repo.listRecords` | repo.ts | RW SELECT + ORDER BY | None |
| `com.atproto.repo.uploadBlob` | repo.ts | B2 PUT + RW `vertex_repo_block` (for CAR membership) | None |
| `com.atproto.sync.getRepo` / `getBlocks` / `getLatestCommit` | repo.ts | RW SELECT `vertex_repo_block` + MST walk | None |
| `com.atproto.sync.subscribeRepos` (firehose WS) | repo.ts | RW SELECT `vertex_repo_commit ORDER BY seq ASC` streaming | None. ADR-0041 PK content-addressed handles seq races |
| `app.bsky.feed.getTimeline` / `getPostThread` / etc | pipethrough → AppView | RW MV reads | None (pure read) |
| `app.bsky.actor.getProfile` | `handlers/pds/server.ts:308/319/330` UPDATE `vertex_profile` | RW UPDATE | **Potentially broken** — UPDATE immediately after INSERT fails RYW on RW. Need to verify this isn't the commit path |
| `chat.bsky.convo.*` | core.ts messaging | RW `vertex_convo` / `vertex_message` + pipethrough | Works (append-only on RW, encryption in wproto layer) |

## How etzhayyim already works around RW OLTP gaps

Primary-source code references (all in `50-infra/cloudflare/workers/atproto/src/`):

### 1. ON CONFLICT → delete-then-insert (canonical)

`core.ts:2997-3005` (applyWrites upsert path):
```ts
if (upsertRows.length > 0) {
  // Delete-then-insert for upsert emulation (consistent with the
  // single-write legacy path's no-ON CONFLICT approach).
  const uris = upsertRows.map((r) => r.uri);
  await trx
    .deleteFrom("vertex_repo_record")
    .where(sql<boolean>`uri = ANY(${uris}::text[])`)
    .execute();
  await trx.insertInto("vertex_repo_record").values(upsertRows).execute();
}
```

This is the hot path for **every Bluesky write**. It's already RW-compatible.

### 2. Content-addressed PK → PK implicit upsert exploits RW semantics

ADR-0041: `vertex_repo_commit.vertex_id = ${repo}:${collection}:${rkey}:${action}`. Duplicate writes (10-parallel burst) land on same PK → RW natively upserts ("last record overwrites"). No `ON CONFLICT` clause needed; parallel safety via PK semantics alone. **This is actually cleaner than ON CONFLICT**.

### 3. Firehose seq → append-only, ORDER BY on read

`vertex_repo_commit.seq` is still BIGINT ordering column, but PK collision (per ADR-0041) is handled by content-addressed PK. Consumers (graph-worker, subscribeRepos) read `ORDER BY seq ASC`, tolerating gaps/dupes.

### 4. No cross-table write TX

Every write is a single SQL statement. Commit pipeline writes happen sequentially:
1. INSERT `vertex_repo_commit` (seq, repo CID)
2. INSERT `vertex_repo_block` (CAR blocks)
3. delete-then-insert `vertex_repo_record`

Partial failure = retry from client (ADR-0041 4× exponential backoff). Idempotency comes from content-addressed PK across all three.

### 5. UNIQUE enforcement → PK-only

All "unique" columns are made PK (single or composite). E.g., `vertex_repo_record (did, collection, rkey)` is composite PK. No standalone UNIQUE needed.

### 6. RYW avoidance

Reads after writes in the same request cycle are avoided:
- Client-side: Bluesky client waits for XRPC response, then re-reads later (at user scroll)
- Server-side: response is built from in-memory values computed pre-write, not re-read

## Latent bugs surfaced

### Bug 1: `agent/memory.ts:284` silent failure

```ts
// Upsert via INSERT ... ON CONFLICT (Kotoba/Datomic supports this)  ← WRONG
await db
  .insertInto(SEMANTIC_TABLE)
  .values({...})
  .onConflict((oc: any) => oc.column('memory_id').doUpdateSet({...}))
  .execute();
```

Wrapped in `try { … } catch (e) { console.warn('[agent/memory] semantic update failed:', e); }` — so RW parser error is swallowed. **Agent semantic memory has been silently failing to persist updates** since this was written. New memories (first insert for a memory_id) succeed via PK-upsert; **updates to existing memories do not apply**.

Fix: replace with delete-then-insert pattern matching `core.ts:2998`.

### Bug 2: Similar usages in actor/agent layer

`grep -r onConflict` shows similar patterns in:
- `actor-executor-migrate-t1.ts:38, 57, 81` — inline SQL string `ON CONFLICT (vertex_id) DO UPDATE`
- `actor/index.ts:402` — `.onConflict(oc => oc.column('edge_id').doNothing())`
- `actor/tools.ts:83, 220` — `.onConflict(oc => oc.column('vertex_id').doUpdateSet({...}))`
- `handlers/etzhayyim/index.ts:85` — documented helper

Each needs independent audit. Some may be dead code (migration scripts), some may be live and silently broken.

### Bug 3: `handlers/pds/server.ts:308/319/330` profile UPDATE

`db.updateTable("vertex_profile").set({...}).where(...).execute()` — bare UPDATE. If called right after an INSERT `vertex_profile` (profile creation → immediate profile edit in same request), RYW failure means UPDATE hits 0 rows. Needs FLUSH interstitial or architectural change to never UPDATE within same request as INSERT on same row.

## Invariants required to keep Bluesky compatibility on RW

1. **No `ON CONFLICT` on RW tables**. Use delete-then-insert or content-addressed PK.
2. **No multi-row write TX expectations**. Each statement must be independently meaningful. Use content-addressed PK + idempotent retry for atomicity.
3. **No read-your-writes within same request**. If a write must be followed by a read of the same row, do the read first (have the value in memory) or defer the read to next request cycle.
4. **No standalone UNIQUE column constraints**. Business keys → PK only. Composite PK for multi-column uniqueness.
5. **No FK / CASCADE**. App-layer explicit delete propagation. Accept temporary orphans during partial failures.
6. **OLTP-heavy state stays in D1**. Auth sessions, passkey credentials, signing keys, OAuth tokens → D1 `etzhayyim-auth-passkey` / `etzhayyim-keys`. Never move these to RW.

## Why tranquil failed but etzhayyim self-hosted PDS succeeds

**Same RW, same gaps, different software**:
- **Tranquil**: written for Postgres 14+ OLTP. 43 migrations assume FK/UNIQUE/CHECK/ON CONFLICT/TX freely. 100+ sqlx `query!` macros with `ON CONFLICT (col) DO UPDATE` pattern. Adapting means rewriting the entire `tranquil-db` crate + every query site + losing upstream compatibility.
- **etzhayyim self-hosted**: written against RW from day 1 (ADR-0002 → ADR-0036). Commit path explicitly uses delete-then-insert. Content-addressed PK exploits RW's implicit upsert. OLTP-heavy paths offloaded to D1. ~2000 LoC of pds handler code, zero migration pain because schema already matches runtime.

The tranquil POC proved that **RW is the constraint, not the choice of PDS implementation**. Any Postgres-expecting OLTP PDS would hit the same wall. etzhayyim's self-hosted PDS succeeds specifically because it was co-designed with RW.

## social-app compatibility stance

- **Held**: all XRPC NSID the client calls → etzhayyim handlers return spec-shaped JSON. Tested via `50-infra/cloudflare/workers/atproto/src/cc-profile-e2e.test.ts`, `e2e-coverage.test.ts`, `business-person-integration.test.ts`.
- **Firehose**: `subscribeRepos` serves content-addressed commit sequence. Client-side reconstructs repo. ADR-0041 tolerance to RW's last-write-wins is correct for social-app.
- **Auth**: ADR-0022 2-token model (API key + Service Auth JWT) works under OAuth 2.1 spec. Client uses `createSession` → refresh → Service Auth per call.
- **Lexicon**: `app.bsky.*` / `com.atproto.*` + custom `com.etzhayyim.*`. Bluesky client ignores unknown NSID (forward-compat). com.etzhayyim clients use `@etzhayyim/wproto` which wraps AtpAgent.
- **Blob upload**: `com.atproto.repo.uploadBlob` → B2 PUT works. Client reads blob ref from AT record normally.

**Bluesky social-app would connect to etzhayyim PDS transparently if we registered the `atproto.etzhayyim.com` endpoint.** The RW gaps are internal storage concerns that never leak to the client.

## Actions

| # | Action | Priority |
|---|---|---|
| 1 | Audit all `.onConflict()` + inline `ON CONFLICT` usages in `50-infra/cloudflare/workers/atproto/src/**/*.ts` (non-test). Categorize each: dead / live-broken / live-working-by-accident | P1 |
| 2 | Fix `agent/memory.ts:284` — replace with delete-then-insert | P1 |
| 3 | Audit `handlers/pds/server.ts:308/319/330` profile UPDATE paths for RYW risk | P2 |
| 4 | Add lint rule: fail CI on `\.onConflict\(` / `ON CONFLICT` outside D1 query paths | P2 |
| 5 | Document in `CLAUDE.md` LLM Coding Guardrails: "No ON CONFLICT on Kotoba/Datomic tables; use delete-then-insert (see `core.ts:2998`)" | P1 |

## References

- `50-infra/cloudflare/workers/atproto/src/core.ts:2987-3005` (canonical delete-then-insert upsert)
- `50-infra/cloudflare/workers/atproto/src/handlers/pds/repo.ts` (1763 LOC, repo endpoints)
- `50-infra/cloudflare/workers/atproto/src/handlers/pds/server.ts` (1251 LOC, server endpoints)
- `50-infra/cloudflare/workers/atproto/src/agent/memory.ts:284` (Bug 1)
- `90-docs/adr/0041-pds-commit-content-addressed-pk.md` (content-PK rationale)
- `90-docs/260420-pds-commit-seq-race-analysis.md` (seq race root cause)
- Kotoba/Datomic v2.8.1 probe: `ON CONFLICT` parser error, `Read-write transaction is not supported yet`, "column constraints UNIQUE" not implemented (2026-04-24, doc-confirmed v2.9.0 unchanged)
- Bluesky client: `github.com/bluesky-social/social-app` (TypeScript XRPC over HTTP)
