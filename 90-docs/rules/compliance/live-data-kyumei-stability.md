# Live Data / Kyumei Stability Rules

Last updated: 2026-04-02

## Scope

- PDS write/read path for domain collections
- `etzhayyim apps kyumei-koji` readiness computation
- sub-DID (`did:web:<nanoid>.etzhayyim.com:<path>`) gather/read consistency

## Mandatory Rules

1. `com.atproto.repo.listRecords` MUST remain resilient with this fallback order:
   - KV collection index (`cl:{label}:{repo}`)
   - KV label scan (`{label}:*`) with repo+collection filter
   - Yata Cypher query
2. `writeRecord` MUST await collection-index append (`kvCollectionAppend`) for read-after-write stability.
3. `_internal/batch-flush` MUST await `KAGAMI_RPC.writeBatch` when pending merges exist.
4. `etzhayyim apps kyumei-koji` sub-DID record metrics MUST be computed from `com.atproto.repo.listRecords` first, then Cypher fallback only when needed.
5. `etzhayyim apps kyumei-koji` live status (`status_records`, `completed_runs`, `records_hint`) SHOULD use `com.atproto.repo.listRecords` fallback when Cypher returns zero.
6. `live_data` critical (`No domain records`) MUST NOT be emitted when sub-DID list-based records are present.
7. App-level manual gather commands (e.g. `gatherSubDID`) SHOULD append `com.etzhayyim.liveData.status` with at least `status`, `sourceId`, `recordsCreated`, `updatedAt`.
8. `etzhayyim monitor shinka` SHOULD expose sub-DID freshness and stale-count based on `--freshness-hours` threshold.
9. `com.etzhayyim.liveData.status` SHOULD include `actorDid`; if app omits it, host/PDS MUST backfill with write repo DID.
10. `etzhayyim apps kyumei-koji` SHOULD return DID breakdown (`did_readiness`) in addition to app aggregate.

## Verification Commands

```bash
curl -sS "https://atproto.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:tnt4ib0d.etzhayyim.com:moon&collection=com.etzhayyim.apps.tentai.celestialBody&limit=5"
go run ./70-tools/etzhayyim/etzhayyim apps kyumei-koji -nanoid tnt4ib0d -dir ./60-apps -json
go run ./70-tools/etzhayyim/etzhayyim monitor shinka -nanoid tnt4ib0d -dir ./60-apps --freshness-hours 24 --json
```
