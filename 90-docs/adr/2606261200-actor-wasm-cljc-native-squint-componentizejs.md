---
id: adr-2606261200-actor-wasm-cljc-native-squint-componentizejs
title: "ADR-2606261200: actor WASM cljc-native via squint + ComponentizeJS (replaces componentize-py)"
status: proposed
doc_type: adr
topic: actor-wasm-cljc-native-squint-componentizejs
authoritative: true
last_verified: 2026-06-26
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "実装/engineering convention (changeable at the impl layer; not a charter invariant)"
authoritative_for:
  - 20-actors WASM build toolchain (cljc-native actors)
depends_on:
  - adr-2606251200-apps-ts-to-cljs-edn-migration
  - adr-2606014600-wasm-actor-runtime
related:
  - adr-2606161630-busshi-grounding
  - adr-2606222000-etzhayyim-py-cli-bb-migration
supersedes: []
superseded_by: []
---

# ADR-2606261200: actor WASM cljc-native via squint + ComponentizeJS (replaces componentize-py)

**Status**: proposed
**Date**: 2026-06-26
**Deciders**: Jun Kawasaki

# Context

The repo's substrate→actor→app layers are converging on **one language (Clojure)**:
state = kotoba EDN Datom log; operational code = clj/bb; actors port py→cljc; the
60-apps frontend is migrating TS→cljs+edn (ADR-2606251200, squint PoC verified).

The remaining Python island is the **actor WASM runtime**. Many Tier-B actors are
built as **componentize-py** components: `methods/*.py` (+ `wasm/app.py`) are compiled
to a WASI Component Model component (ADR-2606014600 / 2606161630). The cljc ports
(`methods/*.cljc`, tested green) sit **beside** the `.py` as additive ports — but the
`.py` is the **declared/built runtime**: `tools/build.clj` (`bb <actor>:build-wasm`)
copies `methods/*.py` into componentize-py, and `tools/publish.clj`
(`bb <actor>:publish`) builds that wasm + pins its CID + deploys it. So the `.py`
**cannot be removed** without a cljc-native replacement for the wasm build — there was
no Clojure→WASI-Component toolchain in the repo. (Measured 2026-06-26: 22 actors /
104 `methods/*.py` with a `.cljc` twin; ibuki alone has 42.)

This blocked completing the py→cljc migration at the wasm layer and removing the
redundant `.py`.

# Decision

Adopt **squint + ComponentizeJS (jco)** as the **cljc-native actor WASM toolchain**,
replacing componentize-py per actor:

```
methods/*.cljc  →  squint  →  ESM JS  →  jco componentize (ComponentizeJS / StarlingMonkey)  →  WASI Component
```

This is the exact Clojure analogue of componentize-py (Python → CPython-in-wasm):
ComponentizeJS embeds the StarlingMonkey JS engine, and squint emits the plain ESM the
engine runs. The JS module's exports satisfy the actor's existing `wasm/wit/world.wit`
**unchanged** — the WIT contract (e.g. `export analyze: func() -> string`) is the stable
interface; only the implementation language under it changes.

**PoC-verified (2026-06-26, `90-docs/poc/2606261200-cljc-wasm/`)** against aburi's real
`aburi-actor` world:

| step | result |
|---|---|
| `squint compile app.cljs` → ESM | ✓ |
| `jco componentize app.js --wit world.wit --world-name aburi-actor` | ✓ "Successfully written aburi-actor.wasm" |
| `wasm-tools validate` | ✓ valid WASI Component |
| component exports | ✓ exactly `analyze: func()->string`, `datoms: func(tx:u32)->string`, `coverage: func()->string` |
| component size | 12.5 MB (StarlingMonkey JS engine — comparable to componentize-py's bundled CPython) |

Toolchain availability confirmed: `wasm-tools 1.245`, `jco 1.24.3`,
`@bytecodealliance/componentize-js 0.21`.

**Per-actor migration** (the unit of work that completes py→cljc and removes the `.py`):
1. cljc methods already green (testcase gate — the existing `test_*.cljc` suite).
2. Rewrite `tools/build.clj` (`<actor>:build-wasm`): componentize-py → `squint compile` +
   `jco componentize` against the unchanged `wasm/wit/world.wit`; keep `wasm-tools validate`
   + CID-pin (CIDv1, `ipfs add` parity) + jco transpile, identical downstream.
3. Update `manifest.jsonld` (cell `:method` `*.py`→`*.cljc`; runtime "pywasm/componentize-py"
   → "cljc-native (squint+ComponentizeJS)") and the docs.
4. Remove `methods/*.py` + `wasm/app.py` (the componentize-py scaffold).
5. Verify: cljc tests green + `bb <actor>:build-wasm` produces a valid component.

**Classification**: 実装/engineering convention — changeable at the implementation layer
without a charter amendment. WASI-sandbox guarantees (no ambient network/FS, host owns the
log, no-server-key) are **toolchain-independent** and preserved.

# Consequences

- **+** Completes the single-language stack: substrate→actor→app→**wasm** all Clojure;
  `methods/*.py` becomes removable (the migration's last island closes).
- **+** WIT contract is unchanged → the actor's *interface* and any consumers are stable;
  only the impl language swaps.
- **+** cljc methods are shared (`.cljc`) between the bb/clj test+runtime side and the wasm
  side — write once.
- **−** Per-actor `build.clj` rewrite (22 actors / 104 files; ibuki = 42) — a real,
  staged program, not a blanket delete. Do it one actor at a time, testcase-gated.
- **−** Component size ~12 MB (StarlingMonkey), comparable to componentize-py's CPython —
  fine for the server/mesh-side actor tier; NOT the baien edge-32 target (which stays a
  separate carve-out).
- **−** Adds the squint + jco toolchain to the actor build path (Node + wasm-tools already
  required by componentize-py's jco/wasm-tools steps).

# Alternatives Considered

- **Keep componentize-py, keep `.py`** — rejected: leaves the Python island, blocks
  removing the redundant `.cljc`/`.py` duplication, and contradicts the clj/bb direction.
- **Blanket-delete `methods/*.py`** — rejected (and surfaced, not done): the `.py` is the
  *built/deployed* runtime (`build-wasm`→`publish`→CID→deploy); deletion breaks the
  ADR-backed pipeline. Removal requires this cljc-native replacement first.
- **GraalVM / direct Clojure→wasm** — rejected: no mature WASI-Component toolchain; squint→
  ComponentizeJS reuses the same Bytecode Alliance stack (jco/wasm-tools) already in use.

# References

- ADR-2606251200 — 60-apps TS→cljs+edn migration + squint PoC (the app-layer analogue)
- ADR-2606014600 / 2606161630 — WASM-actor runtime + componentize-py (the path replaced)
- ADR-2606222000 — py-CLI → bb migration (prior language-cutover wave)
- PoC + reproduce steps: `90-docs/poc/2606261200-cljc-wasm/` (this ADR's evidence)
- Toolchain: `@bytecodealliance/{jco,componentize-js}`, `wasm-tools`
