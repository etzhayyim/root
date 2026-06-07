# Real WASM component build (componentize-py)

Proves the production path for the "kotoba-wasm browser/mesh" runtime: a clean-room
actor compiled to an actual WebAssembly **Component** (WIT world
`etzhayyim:cleanroom/actor`), not just the JS reference (`../kotoba-runtime.mjs`).

## Files

| file | role |
|---|---|
| `wit/actor.wit` | the actor WIT world — `handle-request` / `list-tools` / `call-tool` / `healthz` (JSON in/out) |
| `app.py` | self-contained Python guest (in-memory kotoba Datom store + CRUD + MCP); **no host imports** |
| `build.sh` | reproducible `componentize-py` build + `wasm-tools validate` |
| `build-record.json` | recorded artifact evidence (sha256, size, tooling) |

The built `*.wasm` is **gitignored** — it bundles CPython (~18 MB) and is a build
artifact. Rebuild it locally:

```sh
python3 -m venv .venv && .venv/bin/pip install componentize-py
CZPY=.venv/bin/componentize-py ./build.sh app stripe-compat
```

## Verified (this build)

- `componentize-py 0.23.0` → `stripe-compat.actor.wasm` **built successfully**.
- `wasm-tools validate` → **VALID component**; exports the `actor` world (plus the
  standard WASI 0.2 runtime imports componentize-py injects).
- sha256 `994d06ab…c018`, 18 518 811 bytes (see `build-record.json`).

## CID tier

This component is **multi-block** → its IPFS CID is **dag-pb** → `x-exec:
donated-mesh` per ADR-2606014600 (a full IPFS node verifies/loads it; not the raw
single-block `bafkrei` browser-local tier). A compact **Rust/AssemblyScript**
actor build would yield a raw single-block CID for the browser-local tier; that
is the follow-up. Pinning to IPFS (operator step, needs an IPFS daemon) yields
the dag-pb CID that replaces the source-bundle stand-in in `:actor/wasm-cid`.

## Contract parity

`app.py` implements the same contract as `../kotoba-runtime.mjs` (CRUD + cursor
pagination + filtering + `?expand=` + MCP dispatch), so the WASM component and the
JS reference are interchangeable behind the actor's manifest.
