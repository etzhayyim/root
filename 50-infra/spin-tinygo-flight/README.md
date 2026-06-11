# spin-tinygo-flight

TinyGo-oriented gRPC, Arrow Flight, and Flight SQL client packages for Spin components.

This module is extracted from local extensions made on top of `spin-go-sdk` and keeps the package layout intentionally small:

- `grpc`: minimal TinyGo gRPC client over Spin outbound HTTP/2
- `grpc/flight`: Arrow Flight and Flight SQL transport plus Arrow IPC decode helpers
- `grpc/flightsql`: high-level `sql -> batches/rows` wrapper

## Scope

Supported now:

- Spin outbound HTTP/2 transport for TinyGo
- unary and server-streaming gRPC
- Flight RPCs: `Handshake`, `GetFlightInfo`, `DoAction`, `DoGet`, low-level `DoPut`
- Flight SQL: statement query, prepared statement create/query/close
- Arrow IPC decode for primitive columns, dictionary encoding, `list`, `struct`, `map`
- row materialization to `[]map[string]any`

Current constraints:

- runtime target is Spin; this is not a generic WASI gRPC client
- non-TinyGo builds expose unsupported stubs for transport calls
- generic client/bidi streaming is not implemented
- Flight SQL metadata APIs and polling flows are not implemented
- Arrow write-path is intentionally narrow and aimed at prepared statement binding

## Example

```go
import (
    "context"

    flightsql "github.com/etzhayyim/spin-tinygo-flight/grpc/flightsql"
)

func query(ctx context.Context, endpoint, username, password string) ([]map[string]any, error) {
    return flightsql.Query(ctx, "select 1 as value", flightsql.Options{
        Endpoint: endpoint,
        Username: username,
        Password: password,
    })
}
```

## TinyGo

The transport implementation is behind `//go:build tinygo` and expects Spin's `wasi:http@0.2.0` outbound host support.

## Provenance

The transport layer and surrounding package shape originated from `github.com/spinframework/spin-go-sdk/v2`, with the Flight and Flight SQL layers added locally for TinyGo.

## Publishing

This directory is intended to be split into its own repository as-is. The minimum repo contents are already present:

- `go.mod` / `go.sum`
- `LICENSE`
- `NOTICE`
- `.github/workflows/ci.yml`

After copying this directory into a new repository root, the expected first checks are:

```sh
go test ./...
tinygo build -target=wasip1 -gc=leaking -buildmode=c-shared -no-debug -o /tmp/spin-tinygo-flight-smoke.wasm ./examples/smoke
```
