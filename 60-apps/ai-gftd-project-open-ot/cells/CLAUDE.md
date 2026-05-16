# cells — IEC 61499 BFB cells (Rust → wasm32-wasi → WAMR AOT)

This directory holds gftd-native open-ot **Basic Function Block (BFB) cells** in Rust. Each cell is a Cargo crate that compiles to `wasm32-wasi` and is AOT-compiled by `wamrc` into a `.aot` artefact, pinned by content hash via `ai.gftd.apps.openOt.pinModule`.

## Layout

| Crate | Role |
|---|---|
| `openot-bfb-rs/` | shared trait crate — `BasicFunctionBlock`, `TickResult`, marker traits, `heapless` re-export, `#[panic_handler]` for wasm32 no-std |
| `pid-limited/` | reference BFB #1 — IEC 61499 `PID_LIMITED` (saturating PI with anti-windup, 4 ECC states, i64 intermediate). 5 tests. Used for Risk-1 Gate A |
| `droop-p-f/` | reference BFB #2 — IEC 61499 `DROOP_P_F` (P-f frequency droop with deadband, 5 ECC states, i128 intermediate). 10 tests. Used by `:loop:freq-droop` per `PROTOTYPE-MICROGRID.md` §2.3 |
| `anti-islanding-rocof/` | reference BFB #3 — IEC 61499 `ANTI_ISLANDING_ROCOF` (multi-event-input REQ + RESET, multi-event-output CNF + TRIP + ALM, latched Tripped state, ROCOF time-derivative, 3-counter N-sample debounce). 14 tests. Used by `:loop:islanding-decision` per `PROTOTYPE-MICROGRID.md` §2.5 |
| `pid-stack-100/` | Risk-1 Gate A workload BFB — 100 independent PI controllers per tick, shared params + per-instance state. ~3 KB scratch per tick. Not deployed in microgrid loops; exercises the SPEC §14.1 100-in/100-out memory-access pattern. 5 tests. Manifest schemas omit array fields (current schema doesn't model `[T; N]`); codegen emits Params class only |

Workspace: `cells/Cargo.toml` declares all five crates. `cargo test --workspace` runs all 34 unit tests in one shot.

Future cells go alongside the existing three and depend on `openot-bfb-rs`.

## Build constraints (CRITICAL — Risk-1 Gate A blocking)

Per ADR-2605151200 §LangGraph + Pregel binding determinism contract and SPEC §3:

- **No `alloc` after `init`.** Tick-path collections use `heapless::Vec` with const-generic capacity.
- **No `gc` feature, no `Box<dyn Trait>` in `tick`.** Static dispatch only.
- **No `std::time` / `Instant` / `SystemTime`.** `super_step: u64` and any required wall time arrive as data inputs.
- **No RNG.** Randomness arrives as a data input (replay-deterministic).
- **No `f32` / `f64` in the tick path.** Use fixed-point `i32` micro-units (1e-6) and `i64` intermediate. AT Lexicon prohibits float at the wire boundary (per root CLAUDE.md), and integer-only math gives a tighter WCET.
- **`#![no_std]` for embedded targets** (`#[cfg(not(test))] no_std`). Tests may use `std`.
- **`#[no_mangle] extern "C"` ABI** at the crate boundary so WAMR can call directly.

## Build pipeline

```bash
# 1. Compile to wasm32-wasi (no_std — embedded path, opts out of std feature)
cd 60-apps/ai-gftd-project-open-ot/cells/pid-limited
cargo build --release --no-default-features --target wasm32-wasi
# Host-side `cargo check` / `cargo test` use the default-on `std` feature.

# 2. AOT-compile for Cortex-M7 (Giemon Mimi / Te)
wamrc \
  --target=thumbv7em \
  --target-abi=eabihf \
  --opt-level=3 \
  --enable-aot \
  --disable-bulk-memory \
  -o pid_limited.aot \
  target/wasm32-wasi/release/pid_limited.wasm

# 3. Sign + upload + pin via XRPC
cid=$(b3sum pid_limited.aot | awk '{print $1}')
sig=$(gftd builder sign pid_limited.aot)
curl -X POST https://open-ot.gftd.ai/xrpc/ai.gftd.apps.openOt.pinModule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"cellCode\": \"PID_LIMITED_V1\",
    \"moduleCid\": \"$cid\",
    \"moduleSig\": \"$sig\",
    \"moduleSizeBytes\": $(wc -c < pid_limited.aot),
    \"builderDid\": \"did:web:builder.gftd.ai\",
    \"wasmTarget\": \"wasm32-wasi\",
    \"aotTarget\": \"thumbv7em-none-eabi\",
    \"compilerName\": \"wamrc\",
    \"compilerVersion\": \"$(wamrc --version 2>&1)\",
    \"sourceCommit\": \"$(git rev-parse HEAD)\"
  }"
```

## Test policy

- **Pure Rust unit tests** (`cargo test`) cover ECC transitions, saturation, anti-windup, quality gating.
- **Replay test** is the determinism contract: given a recorded super-step stream `(event_in, data_in, ecc_state, internal_pre, params)_n`, replaying `tick` MUST reproduce `(next_state, emitted, neighbor_msgs, internal_post)_n` byte-identical. CI gate; rig is `cells/<cell>/tests/replay_*.rs`.
- **WCET test** (`cargo bench --target wasm32-wasi` + WAMR runtime + DWT counter on Mimi) gates Risk-1 Gate A — see SPEC §14.1.
