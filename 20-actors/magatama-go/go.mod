// Package magatama-go provides WIT Component Model bindings for magatama:runtime@0.1.0.
//
// Replaces github.com/etzhayyimcojp/spincompat.
//
// Migration from spincompat:
//
//	// Before:
//	import spincompat "github.com/etzhayyimcojp/spincompat"
//	func init() { spincompat.Handle(myHandler) }
//
//	// After (one line change):
//	import magatama "github.com/etzhayyim/root/20-actors/magatama-go"
//	func init() { magatama.Handle(myHandler) }
//
// Build pipeline (replaces spin build):
//
//	tinygo build -target=wasip1 -o core.wasm .
//	wasm-tools component embed \
//	    --world magatama-component \
//	    path/to/magatama/wit \
//	    core.wasm -o embedded.wasm
//	wasm-tools component new embedded.wasm \
//	    --adapt wasi_snapshot_preview1=wasi_preview1_component_adapter.wasm \
//	    -o component.wasm
//
// wasi_preview1_component_adapter.wasm is from:
//   https://github.com/bytecodealliance/wasmtime/releases/latest
//   (wasi_snapshot_preview1.reactor.wasm for library components)
module github.com/etzhayyim/root/20-actors/magatama-go

go 1.23.0

require github.com/etzhayyimcojp/performer v0.0.0-00010101000000-000000000000

require (
	github.com/apache/arrow/go/v17 v17.0.0 // indirect
	github.com/goccy/go-json v0.10.3 // indirect
	github.com/google/flatbuffers v24.3.25+incompatible // indirect
	github.com/klauspost/compress v1.17.9 // indirect
	github.com/klauspost/cpuid/v2 v2.2.8 // indirect
	github.com/nats-io/nats.go v1.39.1 // indirect
	github.com/nats-io/nkeys v0.4.9 // indirect
	github.com/nats-io/nuid v1.0.1 // indirect
	github.com/pierrec/lz4/v4 v4.1.21 // indirect
	github.com/zeebo/xxh3 v1.0.2 // indirect
	golang.org/x/crypto v0.41.0 // indirect
	golang.org/x/exp v0.0.0-20240222234643-814bf88cf225 // indirect
	golang.org/x/mod v0.26.0 // indirect
	golang.org/x/net v0.42.0 // indirect
	golang.org/x/sync v0.16.0 // indirect
	golang.org/x/sys v0.35.0 // indirect
	golang.org/x/text v0.28.0 // indirect
	golang.org/x/tools v0.35.0 // indirect
	golang.org/x/xerrors v0.0.0-20231012003039-104605ab7028 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20240318140521-94a12d6c2237 // indirect
	google.golang.org/grpc v1.64.0 // indirect
	google.golang.org/protobuf v1.34.2 // indirect
)

replace github.com/etzhayyimcojp/performer => ../../../go/performer
