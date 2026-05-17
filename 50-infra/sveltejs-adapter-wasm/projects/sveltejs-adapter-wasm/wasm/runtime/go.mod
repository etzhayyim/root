module github.com/etzhayyim/root/50-infra/sveltejs-adapter-wasm/wasm/runtime

go 1.25.7

require go.wasmcloud.dev/component v0.0.5

require go.bytecodealliance.org v0.4.0

require (
	github.com/samber/lo v1.47.0 // indirect
	github.com/samber/slog-common v0.17.1 // indirect
	golang.org/x/text v0.18.0 // indirect
)

replace github.com/etzhayyim/root/50-infra/sveltejs-adapter-wasm/wasm/runtime/gen => ./gen
