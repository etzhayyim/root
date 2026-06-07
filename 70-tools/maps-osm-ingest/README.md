# maps-osm-ingest

Rust binary that streams an OSM planet PBF into RisingWave
(`vertex_osm_element` + `edge_osm_way_node` + `edge_osm_relation_member`).

Source DID: `did:web:maps.etzhayyim.com:planet`.

## Pipeline

```
PBF (URL or file)
  → osmpbf::ElementReader::for_each (blocking tokio task, rayon-backed decode)
      → transform (Node/DenseNode/Way/Relation → typed rows)
          → mpsc<Batch> depth-16   ← bounded backpressure; never OOM
              → 3 parallel writers (node / way / relation)
                  → COPY ... FROM STDIN (FORMAT csv) into *_stage
                      → DELETE+INSERT merge into primary (idempotent)
```

## Usage

```bash
maps-osm-ingest \
  --pbf-url "https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf" \
  --db "postgres://root@risingwave-frontend:4566/dev" \
  --source-did did:web:maps.etzhayyim.com:planet \
  --batch-size 100000 \
  --parallelism 4 \
  --scratch-dir /scratch \
  --checkpoint-key planet-ingest/last-complete.json \
  --r2-endpoint "https://<acct>.r2.cloudflarestorage.com/<bucket>"
```

## Environment variables

| Var | Default | Notes |
|---|---|---|
| `PBF_URL` | — | Mutually exclusive with `PBF_PATH` |
| `PBF_PATH` | — | Local path |
| `KOTOBA_URL` | — | Postgres URL (:4566) |
| `SOURCE_DID` | `did:web:maps.etzhayyim.com:planet` | |
| `OWNER_DID` | = `SOURCE_DID` | |
| `BATCH_SIZE` | 100000 | Rows per writer flush |
| `PARALLELISM` | 4 | Decoder rayon threads |
| `SCRATCH_DIR` | `/scratch` | 200 GiB emptyDir |
| `CHECKPOINT_KEY` | — | Optional B2 marker object |
| `R2_ENDPOINT` | — | Optional B2 base URL |
| `S2_LEVEL` | 16 | |
| `GEOHASH_LEN` | 8 | |

## Idempotency

`vertex_id = osm:{n|w|r}:{id}:{version}` is unique. A second run over the
same PBF re-COPYs into staging and merges; any rows already present are
deleted and re-inserted. Net graph state is unchanged.

## Staging tables

The schema migration (`0048_vertex_osm_element.ts`) creates both the primary
and `_stage` tables with identical columns. RisingWave does not support
`INSERT ... ON CONFLICT`, so we emulate via `DELETE` + `INSERT` inside
`batch_execute` (single implicit transaction).

## Signals

- `SIGTERM` / `SIGINT` → flush in-flight batches, merge staging, exit 0.

## Build

```bash
cargo build --release
```

Image: `ghcr.io/etzhayyim/maps-osm-ingest:<tag>`.

## Observability

All logs are JSON (`tracing-subscriber::fmt().json()`), compatible with the
LKE fluent-bit collector. Adjust verbosity via `RUST_LOG=info|debug`.
