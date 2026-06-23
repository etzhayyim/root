---
id: spike-2606230001-kototama-compile-clj-himawari
title: "Spike 2606230001: kototama compile_clj vs himawari cells — can kototama close the component-prelude gap?"
status: completed
doc_type: explanation
topic: kototama-compile-clj-himawari-spike
authoritative: false
last_verified: 2026-06-23
related:
  - adr-2606222100-himawari-wasm-build-cljc-source-migration
---

# Spike 2606230001: kototama compile_clj — himawari cell compilation test

**Date**: 2026-06-23
**Status**: COMPLETED (honest negative)

## Hypothesis

`com-junkawasaki/kototama`'s `compile_clj` / `compile_game` API unifies the prelude and closes
the "component-prelude gap" that prevented himawari cells from producing a deployable WASM
Component under bare `kotoba_clj::compile_str`.

## Setup

```
/tmp/kototama-spike/
  kototama/          (cloned from com-junkawasaki/kototama)
  kotoba -> symlink  (symlink to in-repo 40-engine/kotoba)
  kami-engine/       (cloned from com-junkawasaki/kami-engine)
```

`cargo build` in kototama: 4.24s, succeeded.

## Test file

`/tmp/kototama-spike/kototama/tests/himawari_spike.rs` — 13 tests covering:
- All kototama compile paths (compile_clj, compile_game, kotoba_clj re-export)
- All himawari blocker patterns (ns-qualified calls, set literals, .hashCode, def constraints)
- PoC rewrite pattern via compile_str_with_prelude

## Key source findings (before tests ran)

From `/tmp/kototama-spike/kototama/src/lib.rs`:
```rust
pub fn compile_clj(src: &str) -> Result<Vec<u8>, String> {
    kotoba_clj::compile_str(src).map_err(|e| e.to_string())  // NO prelude
}
pub fn compile_game_typed(src: &str) -> Result<Vec<u8>, CljError> {
    kami_engine_clj::compile_str_with_prelude(src)  // GAME_PRELUDE only
}
```

From `kototama/Cargo.toml`:
```toml
kotoba-clj = { path = "../kotoba/crates/kotoba-clj", default-features = false }
```
The `component` feature is not enabled → `compile_component_str` is unavailable.

GAME_PRELUDE (kami-engine-clj): `vec-make`/`vec-conj!`/`map-make`/`map-put!`/vec3/timer.
Does NOT contain `get`/`assoc`/`merge`/`hash-map` (those are in kotoba-clj's PRELUDE).

## Test results

```
running 10 tests
T1 compile_clj simple: 195 bytes OK                          PASS
T2 compile_str_with_prelude: 10366 bytes OK                  PASS
T3 compile_game simple: 1695 bytes OK                        PASS
T4 compile_game with stdlib: FAIL — call to undefined function 'hash-map'   FAIL
T5 ns-qualified call: FAIL — unknown function 'clojure.string/lower-case'   FAIL (expected)
T6 set literal: FAIL — `let` is not supported in a `def` initialiser        FAIL (expected)
T7 .hashCode: FAIL — call to unknown function 'int' with arity 1            FAIL (expected)
T8 PoC rewrite: FAIL — `let` is not supported in a `def` initialiser        FAIL (see below)
T9 kototama::kotoba_clj::compile_str_with_prelude: PASS 10241 bytes         PASS
T10 def constraint informational test                                        PASS (info)
```

T8 failure root cause: `(def SOLAR_GRADES ["solar-grade-6N" ...])` — vector literal in `def`.
Fix: `(defn solar-grades [] ...)` getter.

```
T12 PoC v3 final (getter-defn pattern):
  compile_str_with_prelude: PASS 10561 bytes
T13 wasm-tools validate: PASS
T13 output type: CORE MODULE (not a Component)
```

## Findings

1. **`compile_clj` = bare `compile_str` (NO prelude)**. Identical to what the "WASM build status"
   section already used. kototama adds no prelude on this path.

2. **GAME_PRELUDE does NOT have Clojure stdlib compat aliases**. T4 FAILS on `hash-map` — proving
   GAME_PRELUDE has its own map API (`map-make`/`map-put!`) but not the Clojure-style aliases.

3. **`component` feature unavailable via kototama**. `compile_component_str` gated behind the
   `component` feature which kototama disables (`default-features = false`).

4. **`compile_str_with_prelude` produces a valid CORE MODULE (10,561 bytes)**. `wasm-tools
   validate` PASS. But it is NOT a Component.

5. **`def` initializer constraint applies to string literals too** (not just vectors/sets):
   `(def TRANSPORT "giemon-agv")` fails with "string literals are not allowed in a `def`
   initialiser". Integer defs work. Fix: getter-defn pattern.

## Conclusion

**Hypothesis is WRONG.** kototama does not close the component-prelude gap.

The correct path for him awari cell compilation:
- **Core module**: `kotoba_clj::compile_str_with_prelude` → valid core WASM (10,561 bytes, wasm-tools green)
- **Deployable component**: requires a new `compile_component_str_with_prelude()` in kotoba-clj's `component.rs`, OR f64 support + production cells as-is

**Option D holds**: Python for WASM build; cljc for bb-native.

## Artifacts

- Test file: `/tmp/kototama-spike/kototama/tests/himawari_spike.rs`
- WASM output: `/tmp/kototama-spike/himawari-supply.wasm` (10,561 bytes, core module)
- ADR section: `90-docs/adr/2606222100-himawari-wasm-build-cljc-source-migration.md`
  §"kototama compile_clj spike (2026-06-23)"
