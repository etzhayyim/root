# sveltejs-adapter-wasm (Design Document)

## Overview
`sveltejs-adapter-wasm` is a SvelteKit adapter designed to run on **wasmCloud** using **QuickJS** as the JavaScript engine within a **Wasm Component**. It mimics the approach of `adapter-node` but targets the WebAssembly Component Model (WASI 0.2).

## Architecture

### 1. The Adapter (TypeScript)
The adapter package (`@etzhayyim/sveltejs-adapter-wasm`) handles the SvelteKit build process.
- **Client Assets**: Client-side code and prerendered files are output to the `build/client` directory.
- **Server Bundle**: Server-side code is bundled into a single self-contained `index.js` using `esbuild`.
- **Component Packaging**: The adapter wraps the `index.js` into a wasmCloud component source (TinyGo).

### 2. The Runtime (TinyGo + QuickJS)
The wasmCloud component is written in **TinyGo** and serves as the "host" for the SvelteKit application.
- **WASI Interface**: Implements `wasi:http/incoming-handler`.
- **JS Engine**: Embeds **QuickJS** compiled to WebAssembly.
- **Request Bridge**: Translates incoming `wasi-http` requests to standard JavaScript `Request` objects.
- **Server Instance**: Initializes SvelteKit's `Server` object with the bundled manifest and calls `server.respond()`.

### 3. Build Workflow
1. `npm run build` (SvelteKit)
2. `adapter.adapt()`:
   - Generates `build/index.js` (Server bundle).
   - Generates `build/wasm/main.go` (TinyGo source embedding the bundle).
   - Executes `wash build` (via shell command) to produce `build/component.wasm`.

## Why QuickJS?
- **Small Footprint**: QuickJS is extremely lightweight (~200KB) and easy to embed in Wasm.
- **Performance**: While slower than V8, it is sufficient for many server-side rendering tasks and fits well within Wasm memory limits.
- **ES Modules**: Supports modern JS features required by SvelteKit.

## wasmCloud Integration
- Uses `@wasmcloud/component-sdk-go` for the `wasi-http` implementation.
- Deployed as a wasmCloud component with the `http-server` capability provider.

## Comparison with `adapter-node`
| Feature | `adapter-node` | `adapter-wasm` |
| --- | --- | --- |
| **Runtime** | Node.js (V8) | wasmCloud (QuickJS) |
| **Packaging** | Files in `build/` | Single `.wasm` component |
| **Deployment** | Docker / Bare Metal | wasmCloud Lattice |
| **Interface** | HTTP (Node `http`) | WASI (wasi-http) |
| **Cold Start** | Seconds | Milliseconds |

## Key Components
- `adapter/src/index.ts`: The SvelteKit adapter logic.
- `adapter/src/runtime/handler.js`: The JS entry point that imports `Server`.
- `wasm/runtime/main.go`: The TinyGo host for QuickJS.
- `PROJECT.jsonld`: Metadata for the etzhayyim.com ecosystem.
