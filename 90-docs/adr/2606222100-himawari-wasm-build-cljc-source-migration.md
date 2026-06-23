---
id: adr-2606222100-himawari-wasm-build-cljc-source-migration
title: "ADR-2606222100: himawari WASM build — cljc source migration design"
status: proposed
doc_type: adr
topic: himawari-wasm-build-cljc-source-migration
authoritative: true
last_verified: 2026-06-23
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

## Option F spike (2026-06-23)

**Empirical validation** of the kotoba-clj compiler against the actual himawari cljc cells.
Full detail in `90-docs/spikes/2606230000-himawari-kotoba-clj-option-f-spike.md`.

### What kotoba-clj is

- A **Clojure/EDN-subset → WebAssembly compiler** (NOT an interpreter). Emits real WASM bytes.
- `cargo check -p kotoba-clj` exits 0 in 14s. The `factorial` example builds and runs:
  `compiled 223 bytes of wasm … n=5 fact=120`.
- Langgraph workstream steps A–E all ✅ as claimed in the Option F description.
- Stack values are i64; strings are packed `(offset << 32) | len` handles into linear memory.

### Spike methodology

Wrote 15 construct tests drawn directly from `cell_process/state_machine.cljc` and
`panel_loading/state_machine.cljc` and compiled them through `kotoba_clj::compile_str`.
Built and ran under `cargo run -p kotoba-clj --example himawari_spike`. A compile failure is
a **finding**, not an error to suppress.

### Constructs that PASS (compile OK)

| Construct | Himawari use |
|---|---|
| `map-make`/`map-get`/`map-assoc!` (prelude) | All 7 cells — core state |
| `loop`/`recur` | `run-sequential` in cell_process |
| `case` | `transition-junction` arch dispatch |
| `defgraph` DSL + `if-edge` conditional routing | Graph execution |
| `vec-make`/`vec-conj!`/`vec-count` (prelude) | flags/signatures arrays |
| `assoc` (lowers to `assoc!`) | state merging |
| `count`, `into`, `keys`, `vals`, `contains-key?` | general prelude ops |
| `abs` / `Math/abs` | `content-ref` (abs in subset) |
| `cond->` threading macro | conditional flag building |
| `=`, `>`, `>=`, `if`, `when`, `cond`, `let` | throughout |

### Constructs that FAIL (blockers)

| Construct | Error | Himawari use | Gap type |
|---|---|---|---|
| `str/join` | `unknown function clojure.string/join` | `content-ref`, gas error msgs, liberation-cid | Missing namespace |
| `for` comprehension | `unknown function for` | gas-lines in transition-gas-abatement | Missing syntax |
| `merge` | `unknown function merge arity 2` | `default-cell-state`, ALL transition results | Missing builtin |
| `hash` | `unknown function hash` | `content-ref`, `liberation-cid` (ALL cells) | Missing JVM fn |
| `bit-and`, `bit-or`, `bit-shift-*` | `unknown function bit-and` | Masking in `content-ref` | Bitwise ops absent from subset |
| `mapv`, `map` (HOF), `filter` | `unbound symbol inc/pos?` | `transition-emit-record`, attesting-robots | HOF closures unsupported |
| `str` multi-arg concat | `unknown function str arity 3` | Error/flag message building | Arity limit |
| Set literal `#{}` | Reader error at `#` | `METALLIZATION_KNOWN`, `CELL_ARCH_KNOWN` | Reader not implemented |
| `throw`/`ex-info` | (not tested, known missing) | G12 violations in panel_loading | JVM exception |
| `sort` | `unknown function sort` | `liberation-cid` | Missing builtin |

**Note**: `Math/abs` PASSES (abs is in the subset). `assoc` immutable PASSES (lowers to assoc!).
`bit-and` FAILS with arity-2 error — bitwise ops are entirely absent from the current subset.

### Gap coverage

The current kotoba-clj subset covers **~40–50%** of the constructs actually present in the
himawari cljc cells. The blockers fall into three categories:

1. **kotoba-clj missing builtins** (tractable to add): `bit-and`/`bit-or`, multi-arg `str`,
   `merge`, `str/join`. Estimated 2–4 days of Rust/wasm-encoder work per group.

2. **HOF closures** (`filter`/`map`/`mapv` with lambda or named-fn reference): Not in the
   subset. Requires either: (a) loop-unrolled rewrite in cljc, or (b) kotoba-clj extending to
   support first-class function values (significant compiler work, 1–2 weeks).

3. **JVM-only constructs** (`hash`, `throw`/`ex-info`, `for`, set literals): Require either
   reimplementation in the kotoba subset or structural rewrites in the cljc cells.

### Effort estimate

To fully migrate all 7 himawari cells to compile under kotoba-clj:

| Work item | Estimate |
|---|---|
| kotoba-clj: add `bit-and`/`bit-or`/`bit-shift-*` | 0.5–1 day |
| kotoba-clj: add multi-arg `str` concat | 0.5 day |
| kotoba-clj: add `merge` | 1 day |
| kotoba-clj: add `filter`/`map`/`mapv` HOF | 2–3 days |
| kotoba-clj: add set literal `#{}` | 1 day |
| kotoba-clj: add `str/join` (clojure.string) | 0.5–1 day |
| himawari cljc: rewrite all `merge` patterns | 2 days (structural — all 7 cells) |
| himawari cljc: rewrite `for` → `loop/recur` | 1 day |
| himawari cljc: replace set literals with maps | 0.5 day |
| himawari cljc: rewrite string building | 1 day |
| himawari cljc: rewrite `hash`/`bit-and` in content-ref | 0.5 day |
| himawari cljc: replace `throw`/`ex-info` | 1 day |
| himawari cljc: rewrite `mapv`/`filter` | 1.5 days |
| Integration: compile + run all 7 cells on kotoba-runtime | 2 days |
| **Total** | **~15–18 engineering days** |

### Verdict

**Option F is FEASIBLE but NOT cheap.** The kotoba-clj compiler is real, builds and runs,
and the core subset covers loop/map/defgraph/conditional-routing patterns cleanly.

**But:** 50–60% of the actual himawari cljc patterns hit hard blockers — most critically:
`merge` (used in ALL 7 cells × N transitions), `filter`/`map`/`mapv` HOFs, `str/join`,
`hash`, `bit-and`, set literals, and `throw`/`ex-info`. These are genuine compiler gaps,
not configuration issues.

**Recommended next step**: The blocking constructs (especially `bit-and`/`str`-concat/`merge`)
should be added to kotoba-clj as part of its normal roadmap (a separate PR, not tied to
himawari). Once those 3 blockers are addressed, re-run the spike — the gap narrows to HOFs
and JVM-idioms only, which may be acceptable via loop-rewrites.

**In the meantime: Option D (keep Python for WASM build, cljc for bb-native) remains the
correct and only practical decision.** The prune-blocker is real, Option D explicitly accepts
the duplication, and Option F requires ~15–18 engineering days of compiler + cell-rewrite
work before it becomes viable.

---


---

## Post-PR #184 real compile experiment (2026-06-23)

**Objective**: empirically measure how far the `supply_procurement` cell (the most complex of
the 7) can be compiled by kotoba-clj after PR #184 landed (adding `bit-and`/`bit-or`/`bit-xor`/
`bit-shift-left`/`bit-shift-right` builtins, multi-arg `str` desugaring, `merge` prelude).

**Test file**: `40-engine/kotoba/crates/kotoba-clj/tests/himawari_compile_test.rs`
**Cell measured**: `20-actors/himawari/cells/supply_procurement/state_machine.cljc` (269 lines)
**Compiler commit**: post-PR-#184 (kotoba submodule HEAD at time of experiment)

### Raw cell blockers (11 found against `supply_procurement`)

| # | Blocker | EXACT error from `compile_str` | Fix applied in rewrite |
|---|---------|-------------------------------|------------------------|
| A | `.hashCode` not in subset | `Codegen("call to unknown function \`hashCode\` with arity 1")` | djb2 loop (`loop`/`recur`/`byte-at`) |
| B | `format "%08x"` not in subset | `Codegen("call to unknown function \`format\` with arity 2")` | `int-to-hex8` manual digit-by-digit loop |
| C | `str/lower-case` not in subset | `Codegen("call to unknown function \`str/lower-case\` with arity 1")` | removed (all EXCLUDED_TERMS already lowercase) |
| D | `str/trim` not in subset | `Codegen("call to unknown function \`str/trim\` with arity 1")` | removed (inputs assumed clean) |
| E | `str/blank?` not in subset | `Codegen("call to unknown function \`str/blank?\` with arity 1")` | `(= 0 (str-len s))` |
| F | `str/includes?` not in subset | `Codegen("call to unknown function \`str/includes?\` with arity 2")` | `(str-includes? haystack needle)` (prelude) |
| G | `contains?` on set | (set literal itself fails first — see I) | `(vec-contains? v x)` after set→vec rewrite |
| H | `pr-str` not in subset | `Codegen("call to unknown function \`pr-str\` with arity 1")` | `(str x)` |
| I | Hex literals (`0xFFFFFFFF` etc.) | `Read("invalid number \"0xFFFFFFFF\" at offset …")` | Replaced with decimal: `4294967295`, `15`, `9223372036854775807` |
| J | `def` initializer holding vector/set/string | `` Codegen("`let` is not supported in a `def` initialiser") `` | All constant `def` forms → `(defn- const [] ...)` getter functions |
| K | `(long x)` coercion | `Codegen("call to unknown function \`long\` with arity 1")` | Removed `(long ...)` wrapper — all values are i64 |

### Rewrite strategy

All 11 blockers were resolved in a PoC rewrite (`SUPPLY_PROCUREMENT_REWRITE` constant in the
test file). The rewritten source:

- Replaces all constant `def` forms with `(defn- …)` getter functions (Blocker J)
- Implements `djb2` hash via `loop`/`recur`/`byte-at` (Blocker A)
- Implements `int-to-hex8` via digit-extraction loop (Blocker B)
- Uses only prelude functions: `str-includes?`, `str-len`, `str-cat`, `vec-contains?`,
  `map-get`, `byte-at` (Blockers C–H)
- Uses decimal integer literals only (Blocker I)
- Removes `(long ...)` type coercions — all values are i64 in kotoba-clj (Blocker K)

### Test results (9/9 pass)

```
test rewritten_supply_procurement_compiles ... ok   (REWRITE COMPILE: SUCCESS — 12572 bytes)
test raw_supply_procurement_compile_result ... ok   (informational — raw cell fails as expected)
test probe_xuar_refusal ... ok                     (scenario 1: XUAR origin → refused)
test probe_non_solar_grade_refused ... ok           (scenario 2: non-solar-grade → refused)
test probe_valid_solar_grade_accepted ... ok        (scenario 3: valid inputs → accepted)
test probe_bit_and_hash_pr184 ... ok               (scenario 4: bit-and from PR#184)
test probe_tithe_calculation ... ok                (scenario 5: tithe = gross * rate / 10000)
test probe_merge_pr184 ... ok                      (scenario 6: merge from PR#184)
test probe_multi_arg_str_pr184 ... ok              (scenario 7: 3-arg str from PR#184)
```

**WASM output size**: **12,572 bytes** (rewritten `supply_procurement`; debug profile unoptimized).

### Compiler: `def` initializer constraint (CRITICAL — applies to ALL cells)

kotoba-clj enforces that `def` forms hold only compile-time i64 integer constants (`codegen.rs`
`eval_const`). The exact error when a string, vector, set, or function-call appears:

```
Codegen("`let` is not supported in a `def` initialiser")
```

Fix pattern:
```clojure
;; BEFORE (fails):
(def ^:private EXCLUDED_ORIGIN_TERMS ["xuar" "xinjiang" ...])

;; AFTER (compiles):
(defn- excluded-origin-terms [] ["xuar" "xinjiang" ...])
;; Call site: (vec-contains? (excluded-origin-terms) term)
```

### PR #184 builtins verified live

| Builtin | Test | Verified result |
|---------|------|-----------------|
| `(bit-and x mask)` | `probe_bit_and_hash_pr184` | djb2 hash `"test" & 4294967295 = 1936946164` |
| `(merge m1 m2)` | `probe_merge_pr184` | `{:b 3 :c 4}` overrides `{:a 1 :b 2}` |
| `(str a b c)` multi-arg | `probe_multi_arg_str_pr184` | `"abc"` from 3-arg `str` |

### Gap summary vs original Option F spike

| Gap category | Before PR #184 | After PR #184 |
|---|---|---|
| `bit-and`/`bit-or`/bitwise | BLOCKER | **RESOLVED** (PR #184) |
| multi-arg `str` | BLOCKER | **RESOLVED** (PR #184) |
| `merge` | BLOCKER | **RESOLVED** (PR #184) |
| `str/lower-case`, `str/trim`, `str/blank?`, `str/includes?` | BLOCKER | **Workaround feasible** |
| `pr-str`, `long`, `.hashCode`, `format` | BLOCKER | **Workaround feasible** |
| `def` holding non-i64 | BLOCKER | **Workaround feasible** (getter `defn`) |
| Hex literals | BLOCKER | **Workaround feasible** (decimal) |
| Set literal `#{}` | BLOCKER | **Workaround feasible** (vec + `vec-contains?`) |
| `filter`/`map`/`mapv` HOF closures | BLOCKER | **Still a blocker** |
| `for` comprehension | BLOCKER | **Still a blocker** |
| `throw`/`ex-info` | BLOCKER | **Still a blocker** |
| `str/join` (clojure.string) | BLOCKER | **Still a blocker** (other cells) |

**For `supply_procurement` specifically**: all 11 blockers were resolved via workarounds.
`supply_procurement` is the one himawari cell **without** `filter`/`map`/`mapv` HOFs in its
hot path — it uses explicit `loop/recur` patterns — which is why full compilation was achievable.

### Conclusion (post-#184 measurement)

**`supply_procurement` compiles to 12,572 bytes under kotoba-clj (post-PR #184).** This is a
real WASM module that passes 7 functional scenario probes and 2 structural tests.

The remaining 6 cells all use `filter`/`map`/`mapv` with HOF closures, which still block
full compilation. Option F remains feasible but requires either:
- (a) kotoba-clj adding HOF closure support (~1–2 weeks compiler work), or
- (b) loop-rewriting all HOF patterns in the 6 remaining cells (~2–3 days cell work)

**Option D (keep Python for WASM build, cljc for bb-native) remains the operative decision.**
This measurement closes the PR #184 gap-tracking obligation.

---

## Post-PR #185 real compile experiment: 7/7 cell PoC (2026-06-23)

**Objective**: close the remaining 6-cell gap that post-#184 left open by PoC-compiling all 6
HOF-using himawari cells under kotoba-clj via systematic rewrite patterns.

**Test file**: `40-engine/kotoba/crates/kotoba-clj/tests/himawari_compile_test.rs`
**PR**: `com-junkawasaki/kotoba#185` (`kotoba-clj-inline-hof` branch)
**All 59 himawari_compile_test tests green. All -p kotoba-clj suites green (0 failures).**

### Approach

Rather than adding HOF closure support to the compiler itself, applied a systematic PoC-rewrite
pattern (the "inline lambda + getter-defn" approach) to each of the 6 remaining cells. No
compiler changes were required — the existing prelude and HOF infrastructure in the compiler
(introduced during earlier waves) was sufficient.

### Rewrite substitution patterns

| Raw cljc construct | kotoba-clj PoC replacement | Reason |
|---|---|---|
| `(def ^:private S "string")` | `(defn- s [] "string")` | `def` = i64 integers only |
| `#{...}` set literals | getter-defn returning vector + `vec-contains?` | Set reader not implemented |
| `(mapv named-fn coll)` | `(mapv (fn [x] (named-fn x)) coll)` | Named fn refs unbound at HOF call site |
| `(or (get m k) default)` | `(get m k default)` | `or` returns boolean 1/0, NOT first truthy value |
| `Math/PI` | `31415927` (integer × 1e-7) | No float math |
| `Math/abs` | `(if (< n 0) (- n) n)` | No stdlib abs for subset |
| `str/blank?` | `(= 0 (str-len s))` | clojure.string ns absent |
| `throw`/`ex-info` | return `{"error" "…"}` map | JVM exceptions unrepresentable |
| `.hashCode`/`hash` | djb2 loop | JVM intrinsics |
| `(format "%08x" n)` | `int-to-hex8` digit-extraction loop | JVM format string |

The `or` → 3-arg-get pattern was the most subtle: confirmed by diagnostic test
`diag_filterv_map_get` that `(or (get g k) 0)` evaluates to `1` (boolean true) in kotoba-clj,
not the map value. `(get g k 0)` (3-arg form) is the correct substitute.

### Cells compiled and probe results

| Cell | PoC compile | Functional probes | Notable pattern |
|---|---|---|---|
| `supply_procurement` | ✅ 12,572 B | 7/7 | PR #184 baseline |
| `ingot_wafer` | ✅ | 6/6 | `mapv (fn [r] (normalize-robot r)) robots` |
| `polysilicon_refine` | ✅ | 5/5 | `some #(str-starts-with? ...)` inline |
| `panel_loading` | ✅ | 5/5 | `f10-loader-did` getter-defn for DID string |
| `cell_process` | ✅ | 7/7 | 3-arg get in `filterv` instead of `or` |
| `module_assembly` | ✅ | 7/7 | `internal-did-prefix` getter-defn + literal lambda |
| `outbound_logistics` | ✅ | 5/5 | `allowed-consignee-prefix` getter-defn |

**7/7 himawari cells compile to valid WASM under kotoba-clj** via the PoC rewrite patterns.

### What this proves

- The kotoba-clj compiler (with `mapv`/`filterv`/`some`/`every?` + lambda lifting already in
  the prelude) is sufficient to compile all 7 himawari cells without further compiler changes.
- The HOF closure support (`call_indirect` + lambda lifting) was already present and works
  correctly — the gap was purely PoC patterns, not compiler capability.
- The critical semantic difference (`or` = boolean) is now documented with a diagnostic test
  and proven by probe scenarios.

### Gap comparison

| Gap category | Before PR #184 | Post PR #184 (1/7) | Post PR #185 (7/7) |
|---|---|---|---|
| `bit-and`/`bit-or`/bitwise | BLOCKER | RESOLVED | — |
| multi-arg `str` | BLOCKER | RESOLVED | — |
| `merge` | BLOCKER | RESOLVED | — |
| `filter`/`map`/`mapv` HOFs | BLOCKER | BLOCKER | **RESOLVED (literal lambda wrapper)** |
| `def` holding non-i64 | BLOCKER | Workaround | **RESOLVED (getter-defn pattern)** |
| Named fn refs as HOF args | BLOCKER | BLOCKER | **RESOLVED (literal lambda wrapper)** |
| `or` returns boolean, not value | Latent | Latent | **DOCUMENTED + diagnostic test** |
| `throw`/`ex-info` | BLOCKER | BLOCKER | **RESOLVED (return error map)** |
| Set literal `#{}` | BLOCKER | Workaround | RESOLVED |
| `for` comprehension | BLOCKER | BLOCKER | Not needed in any cell PoC |

### Conclusion (7/7 measurement)

**All 7 himawari cells compile to valid WASM under kotoba-clj via PoC rewrites.** The compiler
already has the necessary HOF + lambda-lifting infrastructure. No further compiler changes are
required for this milestone.

**Option D (keep Python for the production WASM build; cljc for bb-native) remains the
operative decision** for the actual `deploy/agent.wasm` build — the PoC rewrites are compile
tests, not production cljc sources. Converting the PoC rewrites to production `.cljc` replacements
is the next tracked work item (a successor spike/ADR), but it is not blocked on the compiler.

The `himawari_compile_test.rs` regression suite (59 tests, PR #185) is the long-term gate: any
future kotoba-clj compiler change that causes a compile failure here signals a regression against
the himawari PoC subset.

---

## Deployable component build (2026-06-23)

**Objective**: produce a deployable WASM Component Model binary (`assert_loads()` passes under
wasmtime) from the production `.cljc` cell sources via `compile_component_str()`, without
faking results.

**Test file**: `40-engine/kotoba/crates/kotoba-clj/tests/himawari_component_build.rs`
**bb safety gate**: `20-actors/himawari/run_tests.sh` — 75 tests, 155 assertions, 0 failures.
This gate was verified green before and after every source edit.

### STEP 1: Safe rewrites applied to all 7 cells (bb-green throughout)

The following semantics-preserving rewrites were applied to make the production `.cljc` files
pass as much of the kotoba-clj compilation pipeline as possible. Every intermediate state
was verified against the bb test suite.

| Rewrite pattern | Reason | Cells affected |
|---|---|---|
| `(def ^:private S "str")` → `(defn- s [] "str")` + call sites | `def` accepts only i64 constants in kotoba-clj | All 7 |
| `#{...}` set literals → `[...]` vectors + `contains?` → `(some #(= % x) coll)` | Set reader not implemented | `cell_process`, `supply_procurement`, `polysilicon_refine` |
| `0.0`, `11.0`, `10.4`, `81.5` etc. → integer equivalents | Float literals unsupported | `outbound_logistics`, `cell_process` |
| `(def ^:private MIN_DRE 0.99)` → `9900` (basis points) + all use sites updated | Float literal | `cell_process` |
| `(defn- kerf-fraction [] {"diamond-wire" 0.40 ...})` → `40`, `55` (integer pct) + arithmetic adjusted | Float literals | `ingot_wafer` |
| `wafer-mass-g` rewritten with integer approximation (π ≈ 355/113, density as mg/cm³) | `Math/PI`, float division | `ingot_wafer` |
| `0xFFFFFFFFFFFF` → `281474976710655` | Hex literals unsupported | `panel_loading`, `cell_process` |
| `(mapv named-fn coll)` → `(mapv (fn [x] (named-fn x)) coll)` | Named fn as HOF arg unbound | `panel_loading`, `outbound_logistics`, `supply_procurement` |
| `(last (str/split name #":"))` → `(get (robot-roles) name)` | Regex literal `#"..."` unsupported | `module_assembly` |

**bb gate result after all STEP 1 rewrites**: 75 tests, 155 assertions, 0 failures. ✓

### STEP 2: Component build attempt

**Test**: `kotoba_clj::component::compile_component_str()` called with
`prelude() + cell_source + "(defn run [input] (solve input))"`.

**Key finding (session): prelude must be prepended manually.** `compile_component_str()` calls
`compile_core()` directly, which does NOT include the standard prelude (vec-make, into, mapv,
etc.). The test was updated to prepend `kotoba_clj::prelude()` explicitly.

### Result: 0/7 cells produce a deployable component

The revised test (`himawari_component_build.rs`, current session) compiles and runs. All 7
cell tests fail at the codegen phase with **missing function** errors. The production `.cljc`
cells use Clojure standard library functions that are not in the kotoba-clj prelude:

| Missing function | Error message | Cells affected |
|---|---|---|
| `str` (arity 1, 3, …) | `Codegen("call to unknown function 'str' with arity N")` | All 7 |
| `merge` (arity 2) | `Codegen("call to unknown function 'merge' with arity 2")` | `cell_process`, `module_assembly`, others |
| `int` (arity 1) | `Codegen("call to unknown function 'int' with arity 1")` | `ingot_wafer`, `supply_procurement` |
| `assoc` (arity 5) | `Codegen("call to unknown function 'assoc' with arity 5")` | `outbound_logistics` |

Note: `str` is used 12–45 times per cell. This is a systemic gap, not a configuration issue.

### Honest finding

**0 of 7 production `.cljc` cells produce a loadable WASM component today.** The gap is
systemic: the production cells use `str`, `merge`, `int`, multi-arity `assoc`, `cond->`,
`boolean`, `long`, `for`, `ex-info`, `Math/abs`, `Math/round`, `format`, `hash`, `sort`,
and other Clojure stdlib functions not present in the kotoba-clj prelude.

The earlier post-PR-#185 PoC (see above) DID compile all 7 cells — but those were carefully
hand-rewritten PoC stubs in the test file, NOT the production `.cljc` sources. The production
sources require additional rewrites (eliminating `str` calls, `merge`, `int`, multi-arity
`assoc`, etc.) or additional functions being added to the kotoba-clj prelude.

### Gap between PoC and production sources

| Category | PoC (PR #185) | Production sources (this session) |
|---|---|---|
| `str` multi-arg concat | Uses `(str a b c)` via PR#184 | Still uses `(str ...)` — available via PR#184 but prelude must be included |
| `merge` | Uses `merge` via PR#184 prelude | Same — needs prelude |
| `int` coercion | Removed (all i64) | Still uses `(int x)` |
| Multi-arity `assoc` | Not used in PoC | Used: `(assoc m k1 v1 k2 v2)` → needs 5-arg form |
| **Critical: prelude not included** | N/A (test used `compile_str_with_prelude`) | `compile_component_str` does NOT auto-include prelude |

The root cause of the 0/7 failure in this session's compile attempt is that
`compile_component_str` uses `compile_core` (no prelude). Once the prelude is manually
prepended (as in the updated test), the `vec-make` and `into`/`mapv` errors disappear, but
`str`, `merge`, and `int` errors surface because those are in the prelude (PR#184) but `int`
is NOT.

### Remaining blockers for production source compilation

1. **`int` coercion**: `(int x)` is not in the prelude. Workaround: remove all `(int ...)` wrappers since kotoba-clj is i64-native.
2. **Multi-arity `assoc`**: `(assoc m k1 v1 k2 v2)` not supported. Workaround: chain single-arity calls.
3. **`Math/abs`, `Math/round`, `Math/ceil`**: Not in prelude subset. Workaround: `(if (< n 0) (- n) n)` etc.
4. **`cond->`**: threading macro — may or may not be supported (untested).
5. **`for`**: not in prelude. Workaround: loop/recur.
6. **`ex-info`/`throw`**: Not in prelude. Workaround: return error map.
7. **`str/trim`, `str/blank?`, `str/join`, `str/starts-with?`, `str/lower-case`**: Not in prelude.

These are the same categories identified in the post-PR-#185 PoC analysis (see above). The
PoC demonstrated that all 7 cells CAN be compiled with systematic rewrites. Converting the
production sources to the kotoba-clj subset is the next tracked work item.

### Next step

Estimated additional work to make all 7 production `.cljc` cells produce `assert_loads()` ✓:
- Remove `(int ...)` / `(long ...)` / `(boolean ...)` wrappers: ~1 hour across all cells
- Rewrite multi-arity `assoc`: ~0.5 hours
- Replace `Math/*` calls: ~0.5 hours  
- Replace `str/blank?`, `str/starts-with?`, `cond->`, `for`, `ex-info`: ~3 hours
- Verify bb tests remain green after each change: ongoing
- Re-run cargo test until `assert_loads()` passes: ~1 hour

**Estimated total**: ~6–8 additional engineering hours to reach a `assert_loads()`-verified
deployable component from production `.cljc` sources.

---

## References

- `20-actors/himawari/deploy/agent.py` — WASM build entrypoint; imports 7 Python cell classes
- `20-actors/himawari/deploy/README.md` — build instructions; verified 2026-06-02
- `20-actors/himawari/deploy/deploy.sh` — build orchestration
- `40-engine/kotoba/crates/kotoba-clj/` — Clojure/EDN-subset → WASM compiler (Option F source)
- `40-engine/kotoba/crates/kotoba-clj/tests/himawari_compile_test.rs` — post-#184 experiment (9/9)
- `40-engine/kotoba/crates/kotoba-clj/src/codegen.rs` — `eval_const` enforces `def`=i64-only
- `40-engine/kotoba/crates/kotoba-clj/src/lib.rs` — prelude: `str-includes?`/`str-len`/`merge`
- `40-engine/kotoba/crates/kotoba-edn/src/parser.rs` — decimal-only integer parser
- `40-engine/kotoba/crates/kotoba-runtime/wit/world.wit` — kotoba-node WIT world
- `20-actors/shionome/wasm/shionome-core/src/lib.rs` — T1 Rust actor pattern (Option E ref)
- `20-actors/kadode/wasm/app.cljc` — parallel cljc WIT-world design artifact
- `20-actors/rasen/wasm/README.md` — pywasm dual-source pattern (Option D ref)
- `50-infra/etzhayyim-did-web/public/organism/scittle.js` — SCI (browser-UI only)
- ADR-2606014500 — One Worker, many WASM actors
- ADR-2606014600 — WASM-actor runtime (gateway + loader + componentize-py)
- ADR-2605302356 — kotoba LangGraph LLM verified + durable routing
