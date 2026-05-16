# Risk-1 Gate A — Wasmtime harness report

**Cell**: `pid_stack_100`

**Wasm artefact**: `../../cells/target/wasm32-unknown-unknown/release/pid_stack_100.wasm`

**Iterations**: 50000

**Cycle period**: 1 ms

**Layout**: params=20 B  internal=1300 B  data_in=1000 B  data_out=1000 B

**Total wall-clock**: 0.054 s

## Tick latency (host, x86_64 / aarch64 — not embedded)

| Stat | Value (ns) |
|---|---|
| n        | 50000 |
| min      | 583 |
| mean     | 884 |
| p50      | 833 |
| p90      | 1209 |
| p99      | 1458 |
| p99.9    | 1500 |
| p99.99   | 8792 |
| max      | 12875 |

## Counters

- ALM-emitting ticks: 0
- Unexpected `out_event`: 0

## Notes

- This is **host harness validation**, not Mimi WCET measurement.
- Real Gate A criteria (per SPEC §14.1): STM32H753 @ 480 MHz, Zephyr LTS, WAMR AOT, 1 ms cycle, 10 h continuous. **PASS**: p99.9 tick latency ≤ 200 µs, zero deadline misses, observed heap delta = 0 bytes.
- Host run validates: artefact load, ABI surface, struct layouts (cell ⇄ rig), determinism, report pipeline.
