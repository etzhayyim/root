# Risk-1 Gate A — Wasmtime harness report

**Cell**: `pid_limited`

**Wasm artefact**: `../../cells/target/wasm32-unknown-unknown/release/pid_limited.wasm`

**Iterations**: 50000

**Cycle period**: 1 ms

**Layout**: params=20 B  internal=16 B  data_in=12 B  data_out=12 B

**Total wall-clock**: 0.009 s

## Tick latency (host, x86_64 / aarch64 — not embedded)

| Stat | Value (ns) |
|---|---|
| n        | 50000 |
| min      | 41 |
| mean     | 85 |
| p50      | 83 |
| p90      | 84 |
| p99      | 125 |
| p99.9    | 125 |
| p99.99   | 5125 |
| max      | 20167 |

## Counters

- ALM-emitting ticks: 0
- Unexpected `out_event`: 0

## Notes

- This is **host harness validation**, not Mimi WCET measurement.
- Real Gate A criteria (per SPEC §14.1): STM32H753 @ 480 MHz, Zephyr LTS, WAMR AOT, 1 ms cycle, 10 h continuous. **PASS**: p99.9 tick latency ≤ 200 µs, zero deadline misses, observed heap delta = 0 bytes.
- Host run validates: artefact load, ABI surface, struct layouts (cell ⇄ rig), determinism, report pipeline.
