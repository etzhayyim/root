# risk1 — Risk-1 prototype gates

Risk-1 quantitative gates per ADR-2605151200 §R4. Three gates A / B / C with PASS/FAIL thresholds; outcome drives the Q3 2026 implementation go/no-go decision.

## Layout

| Path | Gate | Purpose |
|---|---|---|
| `gate-a-rig/` | A — WAMR AOT WCET | Wasmtime simulator: harness validation now, embedded measurement on Mimi HW in Q3 |
| `gate-b-rig/` | B — Pregel super-step latency | (future) 3× Atama + 12× Mimi/Te integration test |
| `gate-c-estimate/` | C — Toolchain qualification cost | (future) IEC 62443-3-3 SL-2 effort estimate doc |
| `gate-*-report.md` | reports | per-gate measurement output, committed |

## Scope discipline

risk1 tools are **harness / measurement only** — they must not be confused with production runtime. The `cells/` workspace is the production code path; `risk1/` is the *measurement* path that consumes `cells/` outputs.

## Workspace separation

`risk1/` is its own Cargo workspace (heavy host deps like wasmtime). Keep separate from `cells/` so embedded-target builds stay lean.
