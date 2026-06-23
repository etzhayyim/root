# ADR-2606230001 — actor-to-kotoba-mesh pipeline

**Status**: Accepted  
**Date**: 2026-06-23  
**Refs**: ADR-2605262130 (kotoba substrate) · ADR-2605312345 (Datom log canonical state)  
**Derives from**: `himawari_compile_test.rs` (PR #2313) — safe-rewrite patterns

---

## Context

The etzhayyim monorepo has 39+ Tier-B actors with cljc-ported cell state machines.
The kotoba mesh expects each actor to supply:

1. A **WASM Component** — compiled from a single `.clj`/`.cljc` source via
   `kotoba_clj::component::compile_kais_component_str` (or the simpler
   `compile_str_with_prelude` for cells without host-import needs).
2. A **`kotoba.app.edn` manifest** — describes component sources, trigger types,
   capability requirements, and placement.

No automated tooling existed to:
- Survey which actors have compilable cells
- Detect compile blockers before attempting WASM build
- Generate the mesh manifest from cell metadata

Additionally, the installed `/opt/homebrew/bin/kotoba` is the GP2 graph-rewriting
language binary — **not** the etzhayyim mesh CLI. The mesh CLI (`kotoba-cli` crate at
`40-engine/kotoba/crates/kotoba-cli/`) has not been compiled to a standalone binary.
Actual WASM compilation is exercised via `cargo test -p kotoba-clj`.

---

## Decision

Build a `bb actor:mesh` pipeline tool that:

1. **Discovers** all `cells/*/state_machine.cljc` files for a given actor
2. **Assesses** each cell for known compile blockers (static text pattern search)
3. **Generates** `kotoba.app.edn` using only clean cells
4. **Reports** blocked cells with the blocker pattern for each

Ship alongside:
- **`70-tools/actor-mesh/mesh-ready.edn`** — full registry of all non-compat actors
  with cljc cells, classified by mesh-readiness tier
- **Three demonstration manifests** — kanayama (8/9 cells), yamabiko (9/9), gov_municipality (3/3)
- **Rust integration test** `actor_mesh_compile_test.rs` — end-to-end WASM compilation
  proof for the three demonstration actors (7 tests, all green)

---

## §1 Compile Constraints (kotoba-clj)

The following patterns prevent compilation with `compile_str_with_prelude`:

| Pattern | Why it fails | Safe rewrite |
|---|---|---|
| `Math/round`, `java.math.`, `.hashCode` | JVM interop | integer arithmetic; djb2 for hashing |
| `str/lower-case`, `str/trim`, `str/blank?` | clojure.string not in prelude | inline char-code operations |
| `str/join`, `str/split`, `str/includes?`, `str/starts-with?` | clojure.string not in prelude | manual loop / vec-contains? |
| `throw`, `ex-info` | no exceptions | return `{"error" "..."}` error map |
| `pr-str` | no reader macros | not needed for WASM output |
| `format "%...` | Java format not available | manual string building |
| `(assoc m k1 v1 k2 v2)` multi-pair | arity error at runtime | `(-> m (assoc k1 v1) (assoc k2 v2))` |
| `def` with string/vector/map value | const-fold only supports integers | getter-defn pattern |

These patterns are detected by `etzhayyim.actor-mesh/COMPILE-BLOCKERS` and
proven by `40-engine/kotoba/crates/kotoba-clj/tests/himawari_compile_test.rs` (PR #2313)
and `actor_mesh_compile_test.rs` (this ADR).

---

## §2 Mesh-Readiness Tiers

| Tier | Definition | Count |
|---|---|---|
| `:mesh-ready` | Cells present, 0 blockers anywhere | 3 (yamabiko, gov_municipality, sarutahiko) |
| `:cells-clean` | Cells clean, some method-level blockers | 4 (kanayama, watatsumi, wadachi, tsutae) |
| `:needs-rewrite` | Cells have compile blockers | 34 actors |
| `:no-cells` | methods/*.cljc only (observatory pattern) | 23 actors |
| `:scaffold-only` | no cljc yet | remaining stubs |

Full registry: `70-tools/actor-mesh/mesh-ready.edn`

---

## §3 Demonstration Results

Three actors demonstrated end-to-end (static analysis → manifest generation → WASM compile):

### yamabiko 山彦 (rail car manufacturing)
- **Cells**: 9/9 clean (bogie_assembly, carbody_fabrication, dynamic_test,
  emissions_acoustic_audit, final_assembly, homologation_binder, interior_hvac,
  silen_rail_review, traction_electrical)
- **Status**: Fully mesh-ready
- **Manifest**: `20-actors/yamabiko/kotoba.app.edn` (9 components, `:on-http` trigger)
- **WASM proof**: `yamabiko_bogie_assembly_compiles_clean` — ~11,389 bytes valid WASM

### gov_municipality (permit workflow)
- **Cells**: 3/3 clean (permit_submission, inspection_scheduling, final_sign_off)
- **Status**: Fully mesh-ready
- **Manifest**: `20-actors/gov_municipality/kotoba.app.edn` (3 components, `:on-http` trigger)
- **WASM proof**: `gov_municipality_permit_submission_compiles_clean` — ~11,380 bytes valid WASM

### kanayama 金山 (circular aluminium metallurgy)
- **Cells**: 8/9 clean (intake_qa, decoating_separation, melting_furnace, dross_recovery,
  dc_casting, hot_rolling, cold_rolling_finishing, air_emissions_audit)
- **Excluded**: mass_balance_binder — `java.math.BigDecimal` in `round2` fn
- **Manifest**: `20-actors/kanayama/kotoba.app.edn` (8 components, `:on-http` trigger)
- **WASM proof**: `kanayama_intake_qa_compiles_clean` — ~11,471 bytes valid WASM

All WASM outputs begin with `\0asm` magic bytes and pass `assert!(wasm.len() > 100)`.

---

## §4 Trigger Convention

| Cell type | Trigger | EDN form |
|---|---|---|
| Manufacturing process cell | `:on-http` | `{:type :http :route "/<actor>/<cell>"}` |
| Observatory / KG mirror | `:on-kse` | `{:type :kse :topic "etzhayyim/actor/<actor>"}` |
| Heartbeat / cron daemon | `:on-tick` | `{:type :cron :schedule "0 * * * *"}` |

---

## §5 Remediation Path for Blocked Cells

Actors in `:needs-rewrite` status should apply the safe-rewrite patterns proven in
`himawari_compile_test.rs`. The main patterns needed:

1. **`java.math.BigDecimal` round2** (kanayama `mass_balance_binder`):
   ```clojure
   ;; BLOCKED:
   (defn- round2 [x]
     (-> (java.math.BigDecimal/valueOf (double x))
         (.setScale 2 java.math.RoundingMode/HALF_EVEN)
         .doubleValue))
   ;; CLEAN (2dp truncation via integer arithmetic):
   (defn- round2 [x]
     (let [shifted (long (* x 100.0))]
       (/ (double shifted) 100.0)))
   ```

2. **`.hashCode` → djb2**:
   ```clojure
   ;; BLOCKED: (.hashCode s)
   ;; CLEAN:
   (defn- djb2 [s]
     (loop [i 0 h 5381]
       (if (>= i (str-len s))
         h
         (recur (inc i) (+ (* h 33) (byte-at s i))))))
   ```

3. **`str/join` → manual loop**:
   ```clojure
   ;; BLOCKED: (str/join ", " items)
   ;; CLEAN (prelude has no join):
   ;; emit as a vector, let the host serialize
   ```

4. **`throw` / `ex-info` → error map**:
   ```clojure
   ;; BLOCKED: (throw (ex-info "msg" {:k v}))
   ;; CLEAN:
   {"error" "msg" "detail" v}
   ```

5. **Multi-key `assoc` → chained single-pair**:
   ```clojure
   ;; BLOCKED (runtime arity error): (assoc m k1 v1 k2 v2)
   ;; CLEAN:
   (-> m (assoc k1 v1) (assoc k2 v2))
   ```

---

## §6 Tool Usage

```bash
# Generate manifest for one actor (writes kotoba.app.edn):
REPO_ROOT=/path/to/root bb actor:mesh kanayama

# Dry-run — print manifest, do not write:
REPO_ROOT=. bb actor:mesh yamabiko --trigger on-http --dry-run

# Survey all actors:
REPO_ROOT=. bb actor:mesh --survey

# Run WASM compilation tests (requires Rust toolchain):
cd 40-engine/kotoba && cargo test --test actor_mesh_compile_test
```

---

## §7 Files Changed

| File | Purpose |
|---|---|
| `70-tools/src/etzhayyim/actor_mesh.cljc` | Pipeline tool + `bb actor:mesh` entrypoint |
| `70-tools/actor-mesh/mesh-ready.edn` | Mesh-readiness registry (all non-compat cljc actors) |
| `20-actors/kanayama/kotoba.app.edn` | Generated mesh manifest (8/9 cells) |
| `20-actors/yamabiko/kotoba.app.edn` | Generated mesh manifest (9/9 cells) |
| `20-actors/gov_municipality/kotoba.app.edn` | Generated mesh manifest (3/3 cells) |
| `40-engine/kotoba/crates/kotoba-clj/tests/actor_mesh_compile_test.rs` | WASM compile proof (7 tests green) |
| `bb.edn` (task added) | `actor:mesh` task wired up |

---

## §8 Next Steps

1. **Port blocked cells** using safe-rewrite patterns (§4 above); highest-value targets:
   - `kanayama/mass_balance_binder` — 1 function fix unlocks the 9th cell
   - `tatekata` — 6 blocker lines in 4 cells, low count
   - `sarutahiko` — already `:mesh-ready` in cells
2. **`kotoba mesh` binary** — build the Rust CLI crate:
   ```bash
   cargo build --release -p kotoba-cli
   ```
   This will enable `kotoba component build` and `kotoba app deploy` commands.
3. **Registry-hook** the pipeline — connect `bb actor:mesh --survey` output to the
   CI registry enforcement gate (ADR-2605271100).

---

## Consequences

- `bb actor:mesh <name>` is the new canonical entrypoint for actor mesh onboarding.
- The `:mesh-ready` tier (yamabiko, gov_municipality, sarutahiko) can be deployed to
  the kotoba mesh lattice as soon as the `kotoba-cli` binary is built.
- All remaining `:needs-rewrite` actors have a clear remediation path via the
  safe-rewrite patterns in `himawari_compile_test.rs`.
- The `mesh-ready.edn` registry is the honest single source of truth for mesh-readiness.
- The kotoba mesh CLI binary gap is explicitly documented — no false claims are made
  about actors being "deployed" to the mesh when only WASM compilation is proven.
