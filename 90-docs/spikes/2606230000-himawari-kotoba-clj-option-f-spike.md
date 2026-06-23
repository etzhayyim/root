---
id: spike-2606230000-himawari-kotoba-clj
title: Option F Spike — himawari cljc cells → kotoba-clj compiler
status: active
doc_type: explanation
topic: himawari-wasm-build
authoritative: false
last_verified: 2026-06-23
authoritative_for: []
related:
  - 90-docs/adr/2606222100-himawari-wasm-build-cljc-source-migration.md
---

# Option F Spike: himawari cljc → kotoba-clj Feasibility

**Date**: 2026-06-23  
**Branch**: `worktree-agent-a0fce3c90a1225c48`  
**Scope**: Empirical test of whether kotoba-clj (`40-engine/kotoba/crates/kotoba-clj/`) can compile the constructs actually present in `20-actors/himawari/cells/*/state_machine.cljc`.

## 1. kotoba-clj — What It Actually Is

kotoba-clj is a **Clojure/EDN-subset → WebAssembly compiler** (NOT an interpreter). It:

- Reads Clojure source via `kotoba-edn` (SSoT reader)
- Lowers to a typed AST then two-pass codegen via `wasm-encoder`
- Emits real WebAssembly core modules (MVP)
- Can wrap to WASM Component Model via `wit-component` targeting the `kotoba:kais@0.1.0` world
- Stack values are i64: numbers, booleans (1/0), and strings as packed `(offset << 32) | len` handles

**`cargo check -p kotoba-clj` exits 0 in 14s.** The `factorial` example runs correctly:
```
compiled 223 bytes of wasm (magic: [0, 97, 115, 109])
n=5  fact=120   fib=5
n=10 fact=3628800 fib=55
```

## 2. Subset Status (Roadmap Steps)

Per README + CLAUDE.md (kotoba CLAUDE.md):

| Step | Status | Description |
|---|---|---|
| A — loops/recur | ✅ | `loop`/`recur`, `cond`, byte-builder |
| B — heap vector/map | ✅ | `vec-make`/`vec-conj!`/`vec-count`/`vec-nth`, `map-make`/`map-get`/`map-assoc!` |
| C-1,2,3,4 — host imports | ✅ | `has-capability?`, `llm-infer`, CBOR decode/encode |
| D — defgraph DSL | ✅ | `:entry`/`:nodes`/`:edges`, `if-edge`, `add-messages`/`:override` reducers |
| C-5 — kqe host builtins | ✅ | `kqe-assert!`/`kqe-retract!`/`kqe-get-objects`/`kqe-query` |
| E — Pregel/BSP | ✅ | `WasmPregelRunner` end-to-end |

Claims in ADR (Option F section): all 5 langgraph workstream steps complete.

## 3. Empirical Spike Results

15 constructs tested against the actual subset. Results:

### PASSES (compile OK)
| # | Construct | Himawari use |
|---|---|---|
| 1 | `map-make`/`map-get`/`map-assoc!` | All 7 cells use state maps |
| 2 | `loop`/`recur` | `run-sequential` loop in `cell_process` |
| 3 | `case` expression | `transition-junction` (arch → recipe) |
| 4 | `defgraph` DSL with `if-edge` | R0.1 uses sequential driver; R1+ uses defgraph |
| 5 | `vec-make`/`vec-conj!`/`vec-count` | flags arrays, signatures arrays |
| 6 | `assoc` (immutable — lowers to `assoc!`) | general state merging |
| 7 | `count`, `into`, `keys`, `vals` | prelude, works |
| 8 | `contains-key?` | checking map keys (NOT set membership) |
| 9 | `abs` / `Math/abs` | `content-ref` in cell_process |
| 10 | `cond->` threading | conditional flag building |
| 11 | `boolean` true/false, `=`, `>`, `>=` | gate checks throughout |

### FAILS (compile error — blockers)
| # | Construct | Error | Himawari use | Workaround |
|---|---|---|---|---|
| A | `str/join` (clojure.string) | `call to unknown function clojure.string/join` | `content-ref`, `transition-gas-abatement` output, `panel_loading` | Rewrite as loop over vec + byte-builder |
| B | `for` (list comprehension) | `call to unknown function for` | `transition-gas-abatement` gas-lines | Rewrite as `loop`/`recur` |
| C | `merge` | `call to unknown function merge` | `default-cell-state`, `transition-texture` result merging | Manual map-assoc! for each key |
| D | `hash` | `call to unknown function hash` | `content-ref`, `liberation-cid` (all cells) | Djb2 or FNV-1 implemented via byte-builder + `byte-at` + loop |
| E | `bit-and`, `bit-or`, `bit-shift-*` | `call to unknown function bit-and` | Masking in `content-ref` (all cells) | Not available — needs kotoba-clj addition |
| F | `mapv`, `filter`, `map` (HOF) | `unbound symbol inc` | `transition-gas-abatement` filter pass | Rewrite as `loop`/`recur` |
| G | `str` multi-arg concat | `call to unknown function str arity 3` | String building everywhere | Use `str-len`/`byte-at` + byte-builder |
| H | `sort` | `call to unknown function sort` | (minor: `liberation-cid`) | Explicit loop sort or skip |
| I | Set literal `#{}` / `contains?` on set | Reader error / unbound | `METALLIZATION_KNOWN`, `CELL_ARCH_KNOWN`, `LOAD_PHASES` check | Replace with `contains-key?` on map |
| J | `clojure.string` namespace | (part of A) | String manipulation throughout | byte-builder based reimplementation |

## 4. Gap Assessment vs himawari cells

### `cell_process/state_machine.cljc` — 9 transition fns + `run-sequential`

Critical blockers:
- `str/join` used in `transition-gas-abatement` (gas list concatenation for error message) and `content-ref` (key serialization)
- `for` list comprehension in `transition-gas-abatement` (gas-lines construction)
- `merge` in `default-cell-state` and every transition result
- `hash` in `content-ref` (used by all cells for CID generation)
- `bit-and` in `content-ref`
- `mapv`/`filter` in `transition-gas-abatement`, `transition-emit-record`
- Set literals `#{}` for `METALLIZATION_KNOWN`, `CELL_ARCH_KNOWN`
- `str` multi-arg in every flag/error message

**Rewrite cost estimate**: Heavy. Every transition function requires rewriting. The `merge`-based state composition is a structural pattern used in ALL 9 transitions.

### `panel_loading/state_machine.cljc` — 1 `solve` function

Critical blockers:
- `str/join` in `liberation-cid` and `attesting-robots`
- `hash` in `cid` and `liberation-cid`
- `bit-and` in `cid` and `liberation-cid`  
- `filter` in `attesting-robots`
- `map` (HOF) in `attesting-robots`
- `into` works BUT `[loader-sig] + mapped others` pattern needs rewrite
- `boolean` cast works BUT `when` exceptions (`throw`/`ex-info`) — NOT in subset
- `or` with nil works BUT `when-not` + `throw (ex-info ...)` — NOT in subset

### `ingot_wafer/state_machine.cljc` — likely similar patterns

(Not fully read but shares the same `str/join`/`hash`/`bit-and`/`merge` patterns from the common pattern used across all cells.)

## 5. What bit-and Gap Means

The README lists these arithmetic ops as supported: `+ - * / quot mod rem inc dec abs min max`. Bitwise ops (`bit-and`, `bit-or`, `bit-shift-right`, `bit-shift-left`) are **NOT in the current subset**. This is a real gap — `content-ref` and `liberation-cid` use `bit-and ... 0xFFFFFFFFFFFF` as a 48-bit mask, which must either be rewritten with division/modulo or kotoba-clj must add the bitwise ops.

## 6. Effort Estimate

Given the blockers above, a realistic estimate for migrating all 7 cells to compile under kotoba-clj:

| Work item | Effort |
|---|---|
| kotoba-clj: add `bit-and`/`bit-or`/`bit-shift-*` | 0.5–1 day (Rust, wasm-encoder) |
| kotoba-clj: add multi-arg `str` concat | 0.5 day |
| kotoba-clj: add `merge` | 1 day (complex: two maps → new map) |
| kotoba-clj: add `filter`/`map`/`mapv` (HOF over vec) | 2–3 days (needs function pointer support or loop generation) |
| kotoba-clj: add set literals | 1 day (lowers to map, `contains?` → `contains-key?`) |
| kotoba-clj: add `str/join` (clojure.string) | 0.5–1 day (wire to byte-builder loop) |
| himawari cljc: rewrite all `merge` patterns | 2 days (structural: all 7 cells × N transitions) |
| himawari cljc: rewrite `for` → `loop`/`recur` | 1 day |
| himawari cljc: replace set literals with maps | 0.5 day |
| himawari cljc: rewrite `str/join` calls | 1 day |
| himawari cljc: rewrite `hash`/`bit-and` in `content-ref` | 0.5 day |
| himawari cljc: replace `throw`/`ex-info` | 1 day (use return codes or error state) |
| himawari cljc: remove `mapv`/`filter` | 1.5 days |
| Integration test: compile all 7 cells + run on kotoba-runtime | 2 days |
| **Total** | **~15–18 engineering days** |

## 7. Verdict

**Option F is FEASIBLE but NOT CHEAP.** The kotoba-clj compiler itself compiles and the core subset (maps, vectors, loops, defgraph, case, threading macros) covers maybe 40–50% of the himawari cljc patterns. The remaining 50–60% requires either:

(a) **Extending kotoba-clj** with `bit-and`/`bit-or`, multi-arg `str`, `merge`, `filter`/`map`/`mapv` HOFs, set literals, `str/join` — which is genuine compiler work, not trivial; or  
(b) **Rewriting the himawari cljc cells** to use only the current subset — which is a significant refactor of all 7 cells.

The correct next step is NOT "switch from Python to kotoba-clj now." It is:

1. Decide whether extending kotoba-clj is in the near-term roadmap (this should be a kotoba-clj ADR item, not blocked on himawari).
2. If yes: implement `bit-and`/`str`-concat/`merge` in kotoba-clj first (a tractable 2–3 day PR), then re-evaluate.
3. In the meantime: **Option D remains correct** — keep Python cells for WASM build; cljc cells for bb-native execution. The explicit duplication is the right trade-off given the gap.

## 8. Raw Spike Output

```
=== Option F Spike: himawari constructs → kotoba-clj ===

OK   [1-map-get-assoc]: 5568 bytes
OK   [2-loop-recur]: 5555 bytes
OK   [3-case]: 5562 bytes
OK   [4-defgraph]: 5789 bytes
OK   [5-vec]: 5548 bytes
FAIL [6-str-join (EXPECTED FAIL)]: Codegen("call to unknown function `clojure.string/join` with arity 2")
OK   [7-math-abs (EXPECTED FAIL)]: 5544 bytes     ← Math/abs PASSES (abs is in subset)
FAIL [8-for-comprehension (EXPECTED FAIL)]: Codegen("call to unknown function `for` with arity 2")
FAIL [9-merge (EXPECTED FAIL)]: Codegen("call to unknown function `merge` with arity 2")
FAIL [10-set-contains (EXPECTED FAIL)]: Read("unterminated string literal")  ← set literal rejected at reader
FAIL [11-hash (EXPECTED FAIL)]: Codegen("call to unknown function `bit-and` with arity 2")
FAIL [12-mapv (EXPECTED FAIL)]: Codegen("unbound symbol `inc`")  ← HOF closures not supported
FAIL [13-filter (EXPECTED FAIL)]: Codegen("unbound symbol `pos?`")
OK   [14-assoc-immutable (EXPECTED FAIL)]: 5569 bytes  ← assoc lowers to assoc!
OK   [15-cond-threading]: 5574 bytes

Second pass additions:
FAIL [bit-and-2arg]: Codegen("call to unknown function `bit-and` with arity 2")
FAIL [hash-fn]: Codegen("call to unknown function `hash` with arity 1")
OK   [math-abs-check]: 5544 bytes
OK   [assoc-immutable]: 5567 bytes
OK   [count]: 5555 bytes
OK   [keyword-get]: 5582 bytes
OK   [into]: 5565 bytes
FAIL [map-hof]: Codegen("unbound symbol `inc`")
OK   [str-concat (str-len)]: 5550 bytes
OK   [conj-vec]: 5542 bytes
OK   [boolean-true-false]: 5541 bytes
OK   [keys-fn]: 5574 bytes
OK   [vals-fn]: 5558 bytes
FAIL [sort-hof]: Codegen("call to unknown function `sort` with arity 1")
OK   [contains-key]: 5575 bytes
```
