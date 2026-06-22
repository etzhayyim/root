---
id: adr-2606222100-himawari-wasm-build-cljc-source-migration
title: "ADR-2606222100: himawari WASM build — cljc source migration design"
status: proposed
doc_type: adr
topic: himawari-wasm-build-cljc-source-migration
authoritative: true
last_verified: 2026-06-22
priority: 4.5
axis: architecture
weight: 0.40
priority_note: "Unblocks himawari py→cljc cell prune; no implementation change, design only."
authoritative_for:
  - himawari-wasm-build-strategy
  - himawari-python-cell-prune-gate
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2606014500-one-worker-many-wasm-actors
  - adr-2606014600-wasm-actor-runtime
related:
  - adr-2605302356-kotoba-langgraph-llm-verified
  - adr-2605301625-kotoba-actor-deploy-murakumo-live
supersedes: []
superseded_by: []
---

# ADR-2606222100: himawari WASM build — cljc source migration design

**Status**: proposed (design only; no implementation change in this ADR)
**Date**: 2026-06-22
**Deciders**: Jun Kawasaki (founder)

---

## Context

### The prune-blocker

During the py→cljc port waves, `20-actors/himawari/` had its cell logic partially ported to
Clojure (`.cljc` counterparts exist for `cell_process`, `ingot_wafer`, and `panel_loading` cells).
However, the Python cell files (`cells/*/cell.py`) could **not** be pruned because
`20-actors/himawari/deploy/agent.py` imports all 7 Python cell classes at module scope and feeds
them to `componentize-py` as WASM build inputs:

```python
# deploy/agent.py (abridged)
from himawari.cells.cell_process.cell import CellProcessCell
from himawari.cells.ingot_wafer.cell import IngotWaferCell
from himawari.cells.panel_loading.cell import PanelLoadingCell
from himawari.cells.string_assembly.cell import StringAssemblyCell
from himawari.cells.tabbing_stringing.cell import TabbingStringgingCell
from himawari.cells.lamination.cell import LaminationCell
from himawari.cells.iv_testing.cell import IVTestingCell
```

The build command (from `20-actors/himawari/deploy/README.md`, verified 2026-06-02) is:

```bash
componentize-py \
  -d <wit-dir> \
  -w kotoba-node \
  componentize agent \
  -p <deploy-dir> \
  -p <bindings-dir> \
  -p <kotoba/py-dir> \
  -p <20-actors-dir> \
  -p <site-packages-dir> \
  -o agent.wasm
```

componentize-py requires Python source files; it bundles all imported Python modules into a single
~20 MB WASM Component Model artifact. There is no mechanism within componentize-py to substitute
cljc sources in place of Python sources.

The result: **deleting `cells/*/cell.py` breaks the WASM build** even when equivalent `.cljc`
logic exists. The prune is gated on solving the build-source problem first.

### WASM build target: the kotoba-node WIT world

The WIT world (`40-engine/kotoba/crates/kotoba-runtime/wit/world.wit`, package
`kotoba:kais@0.1.0`) exports `kotoba:kais/{kqe,kse,auth,llm}`. The `kotoba-node` world is what
`agent.py` compiles against. It is a STATEFUL, LangGraph-style 7-cell manufacturing chain with
`KotobaLLM` and `KotobaCheckpointer` host bindings — not a simple stateless analysis function.

The `WitWorld.run` entry point receives a CBOR-encoded `InvokeContext`, dispatches through the
compiled `StateGraph`, and returns CBOR result bytes.

---

## Investigation findings

The following paths were surveyed in the repo to determine which cljc→WASM routes actually exist.

### Option A — Rust shim calling cljc at runtime

**Not feasible.** There is no FFI mechanism between Rust compiled to `wasm32-unknown-unknown` or
`wasm32-wasi` and Clojure/EDN logic at runtime inside the same WASM component. The T1 Rust actors
(`20-actors/shionome/wasm/shionome-core/`, `20-actors/kanae/wasm/`, `20-actors/tsumugi/wasm/`)
are fully self-contained Rust crates that embed seed data as Rust constants. They do not call out
to Clojure. Bridging a Rust WASM outer shell to cljc cell logic at runtime would require running
a Clojure interpreter inside WASM, which is option C.

### Option B — GraalVM native-image → wasm32

**Not feasible today.** No GraalVM toolchain exists anywhere in the repo. The upstream GraalVM
`native-image` WASM backend (`--target=wasm`) is not yet production-stable for complex Clojure
programs with dynamic dispatch and host-import plumbing. This is a multi-quarter toolchain
investment with no evidence of in-flight work here.

### Option C — SCI/scittle embedded in WASM

**Not feasible for this use case.** SCI (Small Clojure Interpreter) is present in the repo only
as `50-infra/etzhayyim-did-web/public/organism/scittle.js` (~888 KB), where it is used for
browser-side UI scripting. Bundling SCI into a kotoba-node WASM Component Model component would
require compiling SCI itself to `wasm32-wasi`, wiring its host imports (llm, kqe, kse) through
the WIT world, and loading `.cljc` sources at runtime. The resulting component would exceed 50 MB
and introduce an interpreted evaluation path incompatible with the componentize-py component
model. No prototype or spike of this exists.

### Option D — Keep Python for WASM build; cljc for bb-native execution

**Pragmatic and available today.** Python cells remain the WASM build source; `.cljc` cells are
the bb-native / test source. This is explicit duplication, but it:

1. **Unblocks the prune constraint**: making it explicit that `cells/*/cell.py` files serve a
   dual purpose — WASM build input AND runtime — means any future prune of the Python sources is
   gated on a separate, tracked WASM migration (this ADR or a successor). The git history + ADR
   document why Python was kept.
2. **Zero risk to the existing build**: `deploy/agent.py` and the verified ~20 MB `agent.wasm`
   are untouched.
3. **88 pure-logic tests remain green**: the `.cljc` cells are tested independently of the WASM
   build path.
4. **Alignment with rasen pattern**: `20-actors/rasen/wasm/` also keeps a `wasm/app.py` build
   entrypoint alongside `.cljc` methods; this is not himawari-specific.

The cost is permanent py↔cljc duplication until a future WASM migration (Option F) lands.

### Option E — Re-author as T1 Rust actor

**Technically viable for simple actors; not viable for himawari.** The T1 Rust pattern
(`wasm32-unknown-unknown`, no Component Model, raw `compute()` + `result_ptr()` export, see
`20-actors/shionome/wasm/shionome-core/src/lib.rs`) is designed for compact, stateless,
browser-local analysis actors. himawari is a STATEFUL 7-cell LangGraph manufacturing chain with:
- `KotobaLLM` inference calls (Murakumo host binding)
- `KotobaCheckpointer` durable-state semantics
- Per-cell `StateGraph` node dispatch
- CBOR `InvokeContext` decode + encode

Rewriting this in minimal Rust would require re-implementing the full `kotoba_langgraph` shim
(currently a Python package at `40-engine/kotoba/py/`) in Rust, along with the entire 7-cell
business logic. This is a major effort that effectively replaces himawari rather than migrating
it, and changes the programming model substantially. The T1 pattern is not the right target for
stateful actors.

### Option F — kotoba-clj compiler (newly discovered in this investigation)

**The architecturally aligned future path; not available today without a spike.**

`40-engine/kotoba/crates/kotoba-clj/` is a **real, in-repo Clojure/EDN-subset → WebAssembly
compiler** (ADR `40-engine/kotoba/crates/kotoba-clj/docs/ADR-clojure-wasm.md`, 2026-06-08).
Investigation of the crate confirms that the "langgraph workstream" steps are all complete:

| Step | Capability | Status |
|---|---|---|
| A | loops / recur | complete |
| B | heap vector / map | complete |
| C | host-import plumbing (llm-infer) | complete |
| D | CBOR decode/encode (InvokeContext) | complete |
| E | `defgraph` DSL, kqe builtins, Pregel BSP | complete |

From the crate README: "Compiled Clojure agent = langgraph defgraph × kqe Datom writes × Pregel
BSP, end-to-end — verified."

A comparable design artifact also exists: `20-actors/kadode/wasm/app.cljc` implements all 5 WIT
world exports as Clojure functions calling real method siblings. However, `kadode`'s actual
`build.sh` still calls `componentize-py ... componentize app` (Python `app.py` remains the live
build entrypoint), so the `.cljc` is a design/parallel-port artifact showing intent, not a
working replacement.

**What is not yet known for himawari specifically:**

1. The `kotoba-clj` compiler targets a Clojure subset. himawari's cell logic (`.cljc` files) uses
   Clojure data structures, `let`/`defn`/`cond`/`loop`, and protocol dispatch. Whether ALL of
   this falls within the supported subset requires a spike against the actual cell sources.
2. The `defgraph` DSL is structurally different from the Python `StateGraph` API that
   `agent.py` uses. The 7 cell nodes, the `_manufacture` node, the `_narrate` node, and the
   `HimawariState` TypedDict would need to be re-authored against `defgraph` — this is not a
   mechanical translation.
3. The `kotoba_langgraph` Python shim (`KotobaLLM`, `KotobaCheckpointer`, `handle_invoke`) must
   have exact Clojure equivalents within the compiled WASM. It is not clear these are covered
   by the existing kotoba-clj langgraph workstream beyond the hello-world level.

This path requires a **dedicated spike** (estimated: 2–3 days to prove out the cell compilation
pipeline and produce a working `agent.wasm`).

---

## Decision

**Adopt Option D as the immediate pragmatic path, with Option F tracked as the future migration.**

### D1 — Explicit dual-source classification

Classify `cells/*/cell.py` files in `20-actors/himawari/` as serving two purposes:
1. **WASM build inputs** (componentize-py, `deploy/agent.py` entry point)
2. **bb-test references** (currently superseded for logic by `.cljc` counterparts where they exist)

The Python cells are NOT to be pruned until the WASM build source is migrated. Add a `# wasm-build-input: do not prune until ADR-2606222100 migration` comment to `deploy/agent.py` as the machine-readable gate marker.

### D2 — Tracked gate: Python cell prune

The py→cljc port for himawari's remaining 4 cells (`string_assembly`, `tabbing_stringing`,
`lamination`, `iv_testing`) may proceed for the bb/test layer, but the Python cell files are NOT
deleted until Option F lands and the WASM build is validated against the new source.

### D3 — Option F spike, gated

A future ADR (successor to this one, suggested id prefix `2606`) SHALL document a spike that:
1. Takes one himawari cell (e.g. `cell_process`) through `kotoba-clj` compilation to a valid
   kotoba-node WASM Component.
2. Verifies that the compiled component passes the `WitWorld.run` CBOR round-trip test.
3. Reports the language-subset gaps (if any) and the `defgraph` migration cost.

That spike unlocks the full py→cljc prune for the WASM build layer.

---

## Consequences

### Immediate (this ADR)

- `20-actors/himawari/deploy/agent.py` receives a `# wasm-build-input` comment (operator action,
  not part of this ADR). No code changes are made in this ADR.
- The py→cljc cell port for himawari is explicitly **not blocked** — `.cljc` counterparts may be
  completed for the remaining 4 cells. Only the DELETE of the Python sources is blocked.
- The WASM build (`deploy/deploy.sh` → componentize-py → `agent.wasm`) is unchanged and continues
  to work exactly as verified 2026-06-02 (~20 MB component, valid WASM component magic).

### Future (Option F spike, tracked)

- When the kotoba-clj spike confirms feasibility, a successor ADR authorizes:
  - Re-authoring `deploy/agent.py` (or writing a new `deploy/agent.cljc`) against `defgraph`.
  - Building `agent.wasm` from Clojure sources via the kotoba-clj compiler toolchain.
  - Pruning `cells/*/cell.py` files once the new WASM build is validated.
- Possible outcome of spike: Option F is not feasible within the Clojure subset, in which case
  Option D remains permanent and the Python cells are kept as permanent WASM build inputs (no
  prune, explicit ADR acceptance of the duplication).

---

## Alternatives Considered

| Option | Verdict |
|---|---|
| A — Rust shim calling cljc | Not feasible: no FFI bridge between Rust WASM and cljc at runtime |
| B — GraalVM native-image | Not feasible today: no toolchain in repo, upstream wasm backend not production-stable |
| C — SCI/scittle in WASM | Not feasible: SCI is browser-UI-only in this repo; bundling into a kotoba-node component would produce a >50 MB artifact with an interpreted evaluation path |
| D — Keep Python for WASM (ADOPTED) | Pragmatic today: zero build risk, unblocks prune tracking, dual-source duplication accepted |
| E — T1 Rust rewrite | Wrong target: T1 is for stateless browser-local actors; himawari is a stateful 7-cell LangGraph chain with host bindings |
| F — kotoba-clj compiler (future) | Architecturally aligned: compiler exists and langgraph workstream is complete; but himawari-specific spike required to validate defgraph migration cost and Clojure-subset coverage |

---

## References

- `20-actors/himawari/deploy/agent.py` — WASM build entrypoint; imports 7 Python cell classes
- `20-actors/himawari/deploy/README.md` — build instructions; verified 2026-06-02
- `20-actors/himawari/deploy/deploy.sh` — build orchestration; documents why multi-path import is required
- `40-engine/kotoba/crates/kotoba-clj/` — Clojure/EDN-subset → WASM compiler (Option F source)
- `40-engine/kotoba/crates/kotoba-runtime/wit/world.wit` — kotoba-node WIT world (`kotoba:kais@0.1.0`)
- `20-actors/shionome/wasm/shionome-core/src/lib.rs` — T1 Rust actor pattern (Option E reference)
- `20-actors/kadode/wasm/app.cljc` — parallel cljc WIT-world design artifact (not yet a live build entrypoint)
- `20-actors/rasen/wasm/README.md` — pywasm component design; same dual-source pattern as Option D
- `50-infra/etzhayyim-did-web/public/organism/scittle.js` — SCI in repo (browser-UI only; not a WASM Component build path)
- ADR-2606014500 — One Worker, many WASM actors
- ADR-2606014600 — WASM-actor runtime (gateway + loader + componentize-py)
- ADR-2605302356 — kotoba LangGraph LLM verified + durable routing
