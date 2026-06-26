# PoC: cljc-native actor WASM via squint + ComponentizeJS (ADR-2606261200)

**Question:** is there a Clojure→WASI-Component toolchain that can replace
**componentize-py** for the Tier-B actors — so `methods/*.cljc` (not `*.py`) is the
built wasm runtime, and the redundant `.py` can be removed? (componentize-py = the
blocker that kept `methods/*.py` alive: `bb <actor>:build-wasm`→`publish`→deploy.)

**Answer: yes — `cljc → squint(JS) → jco componentize (ComponentizeJS) → WASI Component`.**
The exact Clojure analogue of componentize-py (StarlingMonkey JS engine ≈ CPython-in-wasm).

## Reproduce

```
npm i squint-cljs
./node_modules/.bin/squint compile app.cljs                 # cljc → app.mjs (ESM)
npx esbuild app.mjs --bundle --format=esm --outfile=app.js  # self-contained module
npx @bytecodealliance/jco componentize app.js \
    --wit wit/world.wit --world-name aburi-actor -o aburi-actor.wasm
wasm-tools validate aburi-actor.wasm
wasm-tools component wit aburi-actor.wasm                    # exports = the WIT contract
```

## Results (2026-06-26)

| step | result |
|---|---|
| squint compile (cljc → ESM) | ✓ |
| jco componentize (JS → wasm) | ✓ "Successfully written aburi-actor.wasm" |
| wasm-tools validate | ✓ valid WASI Component |
| component exports | ✓ `analyze: func()->string` · `datoms: func(tx:u32)->string` · `coverage: func()->string` (aburi-actor world, unchanged) |
| size | 12.5 MB (StarlingMonkey engine; comparable to componentize-py's CPython) |

Tooling: `wasm-tools 1.245` · `jco 1.24.3` · `@bytecodealliance/componentize-js 0.21`.

> Note: `jco transpile`+run-in-node needs a version-matched `@bytecodealliance/preview2-shim`
> (a packaging detail shared with componentize-py output); the **component validity + exact
> WIT exports** are the toolchain proof. Deploy uses the same jco/wasm-tools/wrangler path
> componentize-py already uses.

## Conclusion

The WIT world (`wasm/wit/world.wit`) is the stable interface; only the impl language under
it changes. `app.cljs` (3 exports, squint) componentizes to a valid WASI Component satisfying
aburi's real world. → the per-actor migration is: rewrite `tools/build.clj`
(componentize-py → squint+jco), keep `wasm-tools validate`+CID-pin, then remove `methods/*.py`.
Files: `app.cljs` (the squint source) · `wit/world.wit` (aburi's contract).
