# Cell mesh-deploy gaps — empirical findings (2026-06-24)

> Memo for the ADR-2606230001 actor-to-kotoba-mesh pipeline. Records what
> **actually** blocks cell-bearing actors from deploying, measured end-to-end
> with the real mesh CLI (`kotoba component build` / `kotoba app deploy`), not
> the static readiness heuristic.

## TL;DR

The `mesh-ready.edn` readiness tiers are computed by **static text-pattern
search** (per ADR-2606230001 §Decision). That heuristic does **not** reflect
actual mesh-compilability. When the generated `kotoba.app.edn` manifests are run
through the real CLI, **every cell-bearing manifest fails to deploy** — including
the already-landed `yamabiko` / `gov_municipality` / `kanayama` manifests.

Two independent causes:

### 1. Manifest `:src` path convention mismatch
`bb actor:mesh` writes some `:src` values **repo-root-relative**
(`20-actors/<actor>/cells/…`), but `kotoba app deploy` resolves `:src`
**relative to the manifest directory** → doubled path
`20-actors/<actor>/20-actors/<actor>/cells/…` → `No such file or directory`.
(yamabiko's merged manifest uses the correct manifest-relative `cells/…` form,
so this one is inconsistent, not universal.)

### 2. Cells are state-machine libraries, not mesh components — AND use clojure
### features outside the kotoba-clj mesh subset
- A mesh component **must** define `(defn run [ctx] …)` (or `on-http`/`on-kse`).
  The cells define `init` / `transition-to-*` / `run-chain` only — **no mesh
  entry export**. An entry wrapper is necessary but **not sufficient**:
- Even with a passthrough `(defn run [ctx] ctx)` appended, the **cell bodies do
  not compile** under `compile_kais_mesh_component_str`. Measured across all 23
  cells of `yamabiko` (9) + `sarutahiko` (9) + `wadachi` (5):

  | real compiler error | # cells |
  |---|---|
  | `let` is not supported in a `def` initialiser (`(def x (let […] …))`) | 14 |
  | `assoc` arity 7 / 9 — variadic `(assoc m k1 v1 k2 v2 …)` (subset is arity-3) | 9 |

  → **0 / 23 cells compile.** The static heuristic flagged all of these
  "mesh-ready" / "cells-clean".

## Real unblock = two kotoba-clj compiler enhancements (NOT a bb-tool fix)

In `com-junkawasaki/kotoba` (crate `kotoba-clj`):

1. **Variadic `assoc`** — accept `(assoc m k1 v1 k2 v2 …)` (desugar to a left
   fold of arity-3 `assoc`, like the existing `str`/`merge` multi-arg handling).
2. **`let` in a `def` initialiser** — allow `(def x (let […] body))` (the value
   form already compiles elsewhere; the `def` initialiser path rejects it).

These two cover 23/23 of the sampled blockers. They are likely already in scope
for the concurrent kotoba-clj mesh work (`himawari_compile_test.rs` /
`actor_mesh_compile_test.rs`) — coordinate there rather than double-implement.

Secondary (mechanical, in `bb actor:mesh`):
3. Emit `:src` **manifest-relative** uniformly.
4. Append a per-cell mesh **entry wrapper** — `(defn run [ctx] …)` /
   `(defn on-kse [topic payload] …)` decoding ctx → calling the cell's
   `run-chain` → encoding the result — once (1)+(2) make the bodies compile.

## How to reproduce

```bash
BIN=…/kotoba/target/…/kotoba ; WIT=…/kotoba/crates/kotoba-runtime/wit
cell=orgs/etzhayyim/com-etzhayyim-yamabiko/cells/bogie_assembly/state_machine.cljc
cat "$cell" > /tmp/c.clj; printf '\n(defn run [ctx] ctx)\n' >> /tmp/c.clj
"$BIN" component build /tmp/c.clj --wit-dir "$WIT"   # → Codegen("call to unknown function `assoc` with arity 7")
```

## Status by track
- **Observatory actors (no cells)** — hand-authored `run` + `on-kse` slices
  compile + deploy green today (24 migrated as of 2026-06-24). Unaffected by the
  above.
- **Cell-bearing manufacturing actors** — blocked on kotoba-clj (1)+(2). Parked
  until those land upstream.
