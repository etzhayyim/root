# busshi 物資 — MATURITY

| Phase | Scope | Status |
|---|---|---|
| **R0** (ADR-2606161730) | clj-native scaffold: loader + analyze/datoms/coverage + `:representative` seed (25 commodities / 5 classes) + tests | ✅ landed |
| R1 | per-commodity depth (stocks/curve as facts, recycling-loop linkage to kanayama); Murakumo-narrated resilience digest; lexicons | ⏳ |
| R2 | primary-source live ingest behind G7 (USGS / EIA / public exchanges — public-info only, no paid terminal G8); fleet heartbeat → append-only kotoba log | ⏳ |
| R3 | content-addressed publish + WASM build (rare-earth-coverage/shionome pattern) | ⏳ |

## Tests (R0)

```
bb --classpath 20-actors 20-actors/busshi/methods/test_busshi_edn.cljc   # 3 tests / 9 assertions
bb --classpath 20-actors 20-actors/busshi/methods/test_analyze.cljc      # 9 tests / 55 assertions
```

12 tests / 64 assertions green (incl. G1 no-trade, G3 no-signal/no-forecast, G5 not-a-target-list invariants).

## Invariants held

- G1 取引しない · N1 採掘しない · G3 never forecasts · G2/G5 resilience map not a target-list
- clj-native + kotoba-Datom-native (EAVT EDN, derived datoms flagged)
- R0 seed `:representative` (live ingest = G7 operator step)
