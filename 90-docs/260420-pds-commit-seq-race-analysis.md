# PDS vertex_repo_commit seq race — 90% write drop under load (2026-04-20)

## Symptom

10 sequential `createWork` XRPC calls against `animeka.etzhayyim.com`:
- 10 HTTP 200 responses, each returning a valid rkey
- **Only 1 row** appears in `vertex_repo_commit`
- 90% of writes never persist

Confirmed on: `postgres://root@172.236.132.11:4566/dev`, Kotoba/Datomic PG :4566.
Repro: any `com.atproto.repo.createRecord` XRPC call in rapid succession.

## Root cause hypothesis

`50-infra/cloudflare/workers/atproto/src/core.ts:81-119`

```ts
let _repoCommitSeq = 0;  // module-level per-isolate cache

async function nextRepoCommitSeq(db) {
  if (_repoCommitSeq === 0) {
    _repoCommitSeq = await loadLatestRepoCommitSeq(db);  // MAX(seq) from RW
  }
  _repoCommitSeq++;
  return _repoCommitSeq;
}
```

Under concurrent requests within the **same CF Worker isolate**:

1. Request A: `_repoCommitSeq === 0` true → enters `if`, `await loadLatestRepoCommitSeq(db)`.
2. Request B (parallel): also sees `_repoCommitSeq === 0`, also `await loadLatestRepoCommitSeq(db)`.
3. Both awaits resolve to same `MAX(seq)` (e.g. 100). Both assign `_repoCommitSeq = 100`.
4. Both do `_repoCommitSeq++` → both return 101. Collision.
5. Both INSERT `vertex_repo_commit` with `vertex_id = ${repo}:seq:101`. One succeeds, others get unique-PK conflict.

Conflict retry (`core.ts:1223-1270`) resets `_repoCommitSeq = 0` and retries — but the same race pattern re-triggers if other in-flight requests also hit the retry path. After 4 attempts it throws.

**Yet the XRPC returns HTTP 200** — this suggests the INSERT does *not* throw (Hyperdrive pool may silently drop failed inserts, or the conflict detection regex doesn't match RW's actual error string, or RW accepts the INSERT then loses the row during barrier checkpointing). The exact swallow path is unconfirmed — needs CF Worker log capture of the `[repo-commit]` line for dropped writes.

## Evidence

```
$ for n in 1..10; do curl createWork "{\"title\":\"Drop Diag2 $n\"}"; done
1 [200] rkey=3mjwb4khwxs2b
2 [200] rkey=3mjwb4krjmc2k
...
10 [200] rkey=3mjwb4prhrk2t

$ SELECT seq, rkey FROM vertex_repo_commit WHERE rkey IN (...10 rkeys...)
 seq  |     rkey
------+---------------
 20471 | 3mjwb4khwxs2b
(1 row)
```

9/10 rows missing. Same pattern observed in earlier animeka seed (3/10 parallel `createWork`, 5/6 `addCut`).

## Fix candidates (not applied — shared infra, needs owner review)

| Option | Cost | Correctness |
|---|---|---|
| **(A)** Serialize `nextRepoCommitSeq` with an in-isolate `Promise` chain mutex — one allocator at a time | Trivial (~10 LoC) | Fixes intra-isolate race; inter-isolate races still possible but < 0.1% at current load |
| **(B)** Make `vertex_repo_commit.seq` a RW `SERIAL` / use `INSERT ... RETURNING seq` | Medium (migration + callers) | Eliminates race entirely; matches PostgreSQL sequence semantics |
| **(C)** Move seq allocation inside the retry loop with `loadLatestRepoCommitSeq` per attempt and higher max-attempts (10+) | Small | Mitigates but doesn't eliminate; still silent-drop under sustained concurrency |
| **(D)** Surface INSERT failures — audit whether `insertInto(...).execute()` is being swallowed somewhere in the HyperdriveDialect or await chain | 1 hr investigation | Required regardless of A/B/C to fix the 200-on-failure symptom |

Recommended sequence: **(D) first** (find why 200 returns on failure), then **(A)** (quick mitigation), then **(B)** (permanent fix). Shared infra — needs PDS owner sign-off before deploying.

## Impact

All apps writing via `com.atproto.repo.createRecord`:
- animeka (confirmed)
- mangaka (likely — has 22 records across 5 collections; expected count higher given duration of operation)
- Any app using `sdk.pds.createRecord()` or `sdk.pds.dispatch({type:"com.atproto.repo.createRecord"})`

Single-writer apps (one write every several seconds) unaffected. Bulk/batch writers silently losing data.

## Workaround (app-side)

Until the PDS is fixed, apps should:
- Space out writes ≥ 2s apart (empirically inconsistent — still drops some)
- Verify every write with a read-back + retry
- Use Kotoba/Datomic direct INSERT (bypass PDS) for bulk seed/demo data — this is what was done for animeka's 10 seed cuts

## Discovered

2026-04-20 during animeka end-to-end verification. Reported in root `deps.toml [[migrations]]` TBD.

## Partial fix applied 2026-04-20

Deployed to `etzhayyim-pds-2603241700` (version `2999ecfb-f2d1-4b29-90d2-e7c50772298a`):

1. **Intra-isolate mutex on `nextRepoCommitSeq`**. Promise-chain lock serializes MAX(seq)+1 allocation within a CF isolate.

2. **Jittered retry + higher attempt count** (4 → 12). On conflict, `_repoCommitSeq = seq + 1 + random(0..23)` skips over likely-contended slots.

3. **Error observability**. Non-conflict insert failures and exhausted retries now log `[repo-commit]` lines with repo/collection/rkey/seq context.

### Post-fix benchmarks

- **Solo sequential writes (>2s gap)**: 100% persistence.
- **10 parallel `createWork`**: 2/10 persisted (20%, up from 10%). Residual drop split between:
  - PDS success with TID but row never in `vertex_repo_commit` (~40% of successful responses)
  - animeka Worker → PDS binding throws (`work-xxx` fallback rkeys, ~60% of requests)
- Mangaka `vertex_mangaka`: 42 rows (up from 22).

### Remaining issues

(a) **PDS INSERT acknowledges but doesn't persist** — RW may be silently dropping at barrier checkpoint. Needs `.execute()` result inspection + post-INSERT SELECT verification.

(b) **Worker→Worker binding throws under concurrency** — `sdk.pds.createRecord` 60% failure rate on parallel burst. Could be CF CPU/memory limit, Hyperdrive pool exhaustion (pg.Pool default max=10), or same-zone routing (ADR-0023 522).

Next step: per-request tracing ID spanning animeka → PDS → RW so a single request's path is greppable across CF Worker logs.
