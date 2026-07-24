# mst-projector

**Stage 3 module of [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md).** Consumes the PDS firehose (`com.atproto.sync.subscribeRepos`), projects each commit into the public **MST shard set**, and emits the root CIDs that downstream modules (ipfs-pinner, anchor-cron) consume.

## What it does

```
PDS firehose ──▶ mst-projector ──▶ MST shard set (local) ──▶ root CIDs ──▶ ipfs-pinner + anchor-cron
                  │
                  ├─ partition by collection NSID
                  ├─ apply MST insert/update/delete to in-memory tree
                  ├─ snapshot tree to disk (one CAR per shard) at flush boundary
                  └─ emit { shardKey, rootCid, recordCount, byteSize, flushedAt }
```

## Why a projector at all

PDS already stores commits in its own repo MST. But:

1. The PDS MST is **per-actor**, optimized for personal-data-server use. A public open-* app like `open-isco` needs a **per-collection cross-actor** MST so any client can traverse `com.etzhayyim.apps.openIsco.occupation` records without DID-by-DID enumeration.
2. The PDS firehose is **write-only stream**; clients can't do efficient range scans on it. The projected MST is a **queryable read structure**.
3. IPFS pinning needs **stable content addresses**; the projector freezes shards on flush boundaries (every N records or T seconds) and hands those CIDs to ipfs-pinner.

The projection is **append-only deterministic**: the same firehose replay yields the same root CIDs. Anyone can run a second projector and reach the same state, eliminating the single-operator trust assumption.

## Status

**Phase 2 (ADR-2605191358 step 5 + ADR-2605191655)** — working firehose
consumer + per-shard CAR flush (root + unstored MST blocks via
`@atproto/repo`) + IPFS pin (best-effort) + `com.etzhayyim.substrate.shardSnapshot`
AT record publish with `phase: 2`, true `rootCid`, and `snapshotCid`.
Tests: 10/10 (`pnpm test`, node:test under tsx).

Phase 1's counter-derived `snapshotHash` + JSON manifest path is
removed; the lexicon's 4-week deprecation grace for the
`snapshotHash` field starts at the first Phase 2 emission.

## Layout

```
mst-projector/
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts       # CLI entry — runs the firehose consumer
│   ├── firehose.ts    # subscribeRepos client
│   ├── mst.ts         # per-shard @atproto/repo MST (key=`<did>/<rkey>`, value=record CID)
│   ├── mst.test.ts    # node:test — root determinism + CAR roundtrip (10 tests)
│   ├── shard.ts       # shard partitioning (per-collection) + flush policy + CAR file writer
│   └── emit.ts        # IPFS pin + writes com.etzhayyim.substrate.shardSnapshot (phase=2) records via @atproto/api
└── Dockerfile          # K8s deployment image
```

## Configuration

| env | default | purpose |
|---|---|---|
| `ETZ_PDS_FIREHOSE_URL` | `wss://pds.etzhayyim.com/xrpc/com.atproto.sync.subscribeRepos` | upstream firehose |
| `ETZ_PROJECTOR_DID` | `did:web:projector.etzhayyim.com` | own DID for emitted snapshot records |
| `ETZ_PROJECTOR_PDS_URL` | `https://pds.etzhayyim.com` | PDS where snapshot records are written |
| `ETZ_PROJECTOR_PDS_SESSION` | — | JSON `{did,handle,accessJwt,refreshJwt}` (preferred) |
| `ETZ_PROJECTOR_PDS_AUTH` | — | JSON `{handle,password}` (fallback when session missing) |
| `ETZ_PROJECTOR_DATA_DIR` | `/data/mst-projector` | local CAR file storage (`<dataDir>/<urlencoded shardKey>/<rootCid>.car`) |
| `ETZ_PROJECTOR_FLUSH_RECORDS` | `1000` | flush threshold by record count |
| `ETZ_PROJECTOR_FLUSH_SECONDS` | `60` | flush threshold by wall-clock seconds |
| `ETZ_PROJECTOR_COLLECTIONS` | `com.etzhayyim.,com.etzhayyim.apps.` | NSID prefix filter (comma list) |
| `ETZ_PROJECTOR_IPFS_API_URL` | — | optional Kubo HTTP API, e.g. `http://localhost:5001`. If unset, snapshotCid is omitted from emitted records. |

## Operational guarantees

- **At-least-once**: cursor stored after each flush; restart resumes from last flushed seq.
- **Deterministic**: same firehose replay → same root CIDs (modulo PDS commit ordering, which is itself deterministic).
- **Crash-safe**: in-memory tree reconstructed from on-disk CAR snapshots on startup; any post-snapshot events replayed from firehose cursor.

## Future

- Multi-replica (each projector pulls firehose independently; consensus = identical root CIDs at the same seq).
- Shard sharding (sub-trees per major-version of a collection, e.g., `com.etzhayyim.apps.openIsco.occupation/major=2`).

## See also

- [ADR-2605171800](../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — pipeline spec
- [ADR-2605172000](../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — substrate posture
- `../ipfs-pinner/` — next stage
- `../anchor-cron/` — next-next stage
