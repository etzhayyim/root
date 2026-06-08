# cleanroom-browser-runtime

Browser-**local** runtime for the clean-room actor corpus (ADR 260607).

Every registered clean-room actor runs in the browser with **no server and no
network**: this is the "one Worker, many WASM actors" model (ADR-2606014500),
where each actor is a content-addressed kotoba-WASM component on IPFS
(`EtzhayyimWasmComponent`, `ipfs://<wasm-cid>`) executed browser-local.

## What this is

`kotoba-runtime.mjs` is the **JavaScript reference implementation** of the
contract that each actor's WASM component compiles to:

- an in-memory **kotoba Datom store** (entity → records),
- the actor's **REST `api`** surface (CRUD + cursor pagination
  `limit`/`starting_after`/`has_more` + filtering + relationship expansion
  `?expand=`), driven by the actor's `manifest.json`,
- the actor's **MCP `mcp`** surface (`listTools()` / `callTool(name, args)`),
  mirroring the same ops.

The compiled WASM is the production drop-in for the *same* contract; this JS
runtime lets the corpus run today and serves as the executable spec.

## Run

```sh
# from the repo root, so fetch() can read the registry + manifests:
python3 -m http.server 8080
# open http://localhost:8080/60-apps/cleanroom-browser-runtime/
```

Pick any of the 1,000 actors; the page loads its manifest, shows its four
capabilities (`api` / `supplychain` / `socialpost` / `mcp`), and lets you run
live requests against the in-browser Datom store.

## Test

```sh
node 60-apps/cleanroom-browser-runtime/runtime.test.mjs   # 16 assertions
```

Exercises CRUD, pagination, filtering, relationship expansion, MCP dispatch and
`/healthz` against a real L4 manifest (`stripe-compat`) and an L3 manifest
(`aadhaar-compat`).

## Boundaries

- No server key, no network, no fiat path (Charter substrate boundary).
- The Datom store is in-memory per page load; persistence is the canonical
  kotoba Datom log (ADR-2605312345), not this reference shim.
