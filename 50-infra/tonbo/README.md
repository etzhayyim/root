# tonbo

**tonbo** is a Lance/DataFusion-backed analytical query server that exposes:

- **Arrow Flight SQL** — the primary analytical wire protocol
- **LanceDB-style REST API** — a small HTTP surface compatible with the LanceDB REST spec

It uses [DataFusion](https://github.com/apache/datafusion) as the query planner and [Lance](https://github.com/lancedb/lance) as the storage/table engine. Object storage (S3/B2-compatible) is the durable backend.

## Repository layout

```
server/    Rust — Flight SQL + HTTP server binary
go/        Go  — LanceDB REST client (TinyGo-compatible)
```

## server (Rust)

### Build

```bash
cd server
cargo build --release
```

### Docker

```bash
docker build -t tonbo server/
```

### Configuration (environment variables)

| Variable | Default | Description |
|---|---|---|
| `LISTEN_ADDR` | `0.0.0.0:8084` | HTTP listen address |
| `FLIGHT_SQL_ADDR` | `0.0.0.0:50050` | Flight SQL gRPC listen address |
| `TONBO_LANCE_URI` | — | Lance dataset URI, e.g. `s3://bucket/prefix` |
| `TONBO_S3_ACCESS_KEY` | — | S3/B2 access key |
| `TONBO_S3_SECRET_KEY` | — | S3/B2 secret key |
| `TONBO_S3_ENDPOINT` | — | S3-compatible endpoint URL |
| `TONBO_S3_REGION` | — | S3 region |
| `TONBO_S3_BUCKET` | — | S3 bucket name |
| `TONBO_S3_VIRTUAL_HOSTED_STYLE` | `false` | Use virtual-hosted-style S3 URLs |
| `TONBO_READ_THROUGH_CACHE_BYTES` | `128MB` | Read-through cache size (set `0` to disable) |
| `TONBO_EAGER_TABLE_REGISTRATION` | `true` | Register all S3 tables at startup; set `false` for lazy load |
| `RUST_LOG` | `tonbo=info` | Log filter |

Runtime thread tuning is derived automatically from `available_parallelism()` and can be overridden via `TOKIO_WORKER_THREADS`, `LANCE_CPU_THREADS`, `LANCE_IO_CORE_RESERVATION`, `TONBO_TOKIO_MAX_BLOCKING_THREADS`.

### REST API

```
GET  /health
GET  /v1/table
POST /v1/table/{table}/create
POST /v1/table/{table}/insert
POST /v1/table/{table}/query
POST /v1/table/{table}/merge_insert
POST /v1/table/{table}/delete
POST /v1/table/{table}/count_rows
POST /v1/table/{table}/describe
POST /v1/table/{table}/drop
POST /v1/table/{table}/optimize
POST /v1/table/{table}/create_scalar_index
POST /v1/table/{table}/create_index
```

### Kubernetes

See `server/k8s/deployment.yaml` for a reference Deployment + Service + PodDisruptionBudget.

Create the S3 credentials secret before deploying:

```bash
kubectl create secret generic tonbo-s3-credentials \
  --from-literal=TONBO_S3_ACCESS_KEY=<key> \
  --from-literal=TONBO_S3_SECRET_KEY=<secret> \
  --from-literal=TONBO_S3_ENDPOINT=<endpoint> \
  --from-literal=TONBO_S3_REGION=<region> \
  --from-literal=TONBO_S3_BUCKET=<bucket>
```

## go — Go client

The `go/` package is a LanceDB REST + SQL compatibility client for Go and TinyGo.

### Import

```go
import "github.com/gftdcojp/tonbo/go"
```

### Usage

```go
client := lancedbrest.New(&lancedbrest.Config{
    BaseURL: "http://localhost:8084",
})

// SQL query
rows, err := client.QuerySQL(`SELECT * FROM my_table WHERE status = 'active' LIMIT 100`)

// Upsert
err = client.UpsertOneAny("my_table", docID, map[string]any{
    "name": "hello",
    "value": 42,
})

// Fluent query builder
rows, err = client.Table("my_table").
    Select("id", "name").
    WhereEq("status", "active").
    OrderBy("created_at", "DESC").
    Limit(20).
    Rows()
```

The client resolves the base URL from (in priority order):
1. `Config.BaseURL`
2. `LANCEDB_BASE_URL` env var
3. `SPIN_VARIABLE_LANCEDB_BASE_URL` env var
4. `Config.Endpoint` (port-converted from 50050 → 8084)
5. `http://localhost:8084`

### TinyGo

The package is TinyGo-compatible. The `compat_tinygo.go` file provides a fallback implementation for the Arrow IPC surface that does not depend on `reflect`-heavy packages.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
