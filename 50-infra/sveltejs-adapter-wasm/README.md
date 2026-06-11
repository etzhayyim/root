# sveltejs-adapter-wasm

SvelteKit adapter for WebAssembly (WASI 0.2) targeting wasmCloud.

## Architecture

Two wasmCloud components communicate via a custom WIT interface (`etzhayyim:svelte-adapter/js-runtime`) over wRPC:

```
Browser
  -> HTTP Server Provider (ghcr.io/wasmcloud/http-server)
    -> TinyGo Runtime (svelte-server)
         |-- static asset?  -> serve from embedded build/client/
         |-- prerendered?   -> serve from embedded build/prerendered/
         |-- otherwise      -> call js-engine via wRPC
    -> JS Engine (js-engine)
         |-- evaluate(code, request-json) -> response-json
```

### WIT Interface

```wit
package etzhayyim:svelte-adapter;

interface js-runtime {
    evaluate: func(code: string, request-json: string) -> string;
}
```

The TinyGo runtime **imports** `js-runtime`, and the Rust engine component **exports** it. wasmCloud links them via wRPC/NATS at deploy time.

## Features

- **Hybrid Serving**: Static assets (client JS/CSS), prerendered pages (SSG), and SSR in a single deployment
- **Component Model**: Two independent wasm components linked via WIT interface over wRPC
- **WASI 0.2**: TinyGo runtime exports `wasi:http/incoming-handler@0.2.0`
- **Embedded Assets**: SvelteKit `build/` output is embedded into the TinyGo runtime via `//go:embed`
- **Multiple Runtimes**: Javy (single-component) and TinyGo+Engine (two-component) patterns

## Execution Patterns

### 1. TinyGo + JS Engine (Recommended)

Two-component pattern with SSR + SSG + static asset support.

- **Runtime**: `tinygo-qjs`
- **Components**: TinyGo runtime + Rust JS engine
- **Logic**:
  1. Checks `build/client/` for static assets (JS, CSS, images)
  2. Checks `build/prerendered/` for SSG pages
  3. Falls back to SSR via `js-runtime.evaluate()` over wRPC

### 2. Javy Pattern (Pure SSR)

Single-component pattern using Javy (QuickJS compiled to Wasm).

- **Runtime**: `javy`
- **Output**: Single wasm component with SSR only

### 3. Pure SSG Pattern

Static-only sites packaged as a wasm component.

- **Runtime**: `tinygo-qjs`
- **Setup**: Set `export const prerender = true` in SvelteKit

## Quick Start

```bash
# 1. Build the SvelteKit demo
cd demos/demo-tinygo-qjs
pnpm install && pnpm build

# 2. Build the TinyGo runtime (embeds build/ artifacts)
cd ../../projects/sveltejs-adapter-wasm/wasm/runtime
wash build

# 3. Build the JS engine
cd ../quickjs-engine
cargo component build --release

# 4. Deploy to wasmCloud
wash up
cd ../../../../demos/demo-tinygo-qjs
wash app deploy wadm.yaml

# 5. Test
curl http://localhost:8080/          # SSR
curl http://localhost:8080/about     # Prerendered SSG
```

## Usage

Add to your `svelte.config.js`:

```javascript
import adapter from '@etzhayyim/sveltejs-adapter-wasm';

export default {
    kit: {
        adapter: adapter({
            runtime: 'tinygo-qjs', // or 'javy'
            out: 'build'
        })
    }
};
```

## Structure

```
projects/sveltejs-adapter-wasm/
  adapter/              # SvelteKit adapter (TypeScript)
  wasm/
    runtime/            # TinyGo host runtime (imports js-runtime)
      main.go           # HTTP handler, static serving, SSR delegation
      wit/world.wit     # svelte-performer world definition
      wasmcloud.toml    # wash build config
    quickjs-engine/     # Rust JS engine (exports js-runtime)
      src/lib.rs        # evaluate() implementation
      wit/world.wit     # engine world definition
      Cargo.toml
demos/
  demo-tinygo-qjs/      # TinyGo + Engine demo (SSR + SSG)
    wadm.yaml           # WADM deployment manifest
  demo-javy/            # Javy demo (pure SSR)
  demo-ssg/             # Pure SSG demo
```

## Requirements

| Tool | Version |
|------|---------|
| TinyGo | 0.40+ |
| wash | 0.37+ |
| cargo-component | latest |
| pnpm | 10+ |
| wasmCloud | 1.4+ |
