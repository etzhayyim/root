# tsubasa 翼 — MATURITY

> ADR-2606072800. Honest framing: unfinished items say so. The flight-route / fare
> discovery commons — the Skyscanner inversion (affiliate-stripped, member self-books,
> emissions-honest, no person fare-tracking).

| Phase | Scope | Status |
|---|---|---|
| **R0** | manifest + lexicons (fare / searchResult) + kotoba EAVT schema | ✅ landed |
| **R1** | clj-native live query handlers (`py/agent.cljc`): `search-fares` (true total cost + emissions surfaced) / `compare` (cheapest·greenest·fastest first-class) / `strip-affiliate` / `self-book-handoff` (no commission, member principal) | ✅ landed |
| **R2 — observatory + persistence** | canonical `flight-fare-ontology` (00-contracts) + rich `:representative` seed (13 airports / 9 regions / 13 carriers / 11 routes / 23 fares); `analyze.cljc` (per-route carrier-HHI concentration → competition reading → :opening route + cheapest/greenest/fastest + coverage gap worklist + EAVT datom-emit); `kotoba.cljc` content-addressed append-only commit-DAG (tx-cid / verify-chain, tamper-evident, no-server-key); `autorun.cljc` deterministic idempotent-by-content heartbeat; DID registered (INFRA_ACTORS + static did.json/profile) | ✅ landed |
| R3 | live GDS/airline fare ingest (G7/G8 Council Lv7+ + operator) replacing the seed; Murakumo-narrated digest; fleet cell registration; content-addressed WASM build (shionome pattern) | ⏳ gated |

## Coverage (current seed)

| dimension | count |
|---|---:|
| airports | 13 |
| world regions | 9 |
| carriers | 13 |
| O–D routes | 11 |
| fares | 23 |
| routes flagged :opening (thin competition) | computed each run |

Coverage is honestly thin — the seed is `:representative`, NOT exhaustive. `analyze coverage`
emits a per-region airport gap worklist each run (airport target ≈ 36, carrier target 40).

## Tests

```
bb --classpath 20-actors 20-actors/tsubasa/methods/test_analyze.cljc         # 10 tests / 45 assertions
bb --classpath 20-actors 20-actors/tsubasa/methods/test_kotoba.cljc          #  5 tests / 15 assertions (ledger)
bb --classpath 20-actors 20-actors/tsubasa/methods/test_autorun.cljc         #  4 tests / 13 assertions (heartbeat + idempotency)
bb --classpath 20-actors 20-actors/tsubasa/methods/test_seed_integrity.cljc  # 10 tests / 302 assertions (seed ↔ ontology + data-layer gates)
bash 20-actors/tsubasa/run_tests.sh                                          # + handlers (test_agent: 10 tests / 157 assertions)
```

**39 tests / 532 assertions green** (incl. G1 no-commission/affiliate, G3 no-urgency/scarcity,
G4 co2 required + greenest first-class, G5 stateless/no-searcher — all proven *structurally*:
the forbidden attributes do not exist, so they cannot be emitted).

## Invariants held

- **G1 no-affiliate-no-inflow** — onward links affiliate-stripped; member self-books; `commission`/`affiliate`/`merchant` datoms unrepresentable (no such input, no such field — tested).
- **G3 anti-dark** — no `urgency`/`scarcity`/`price-will-rise` attribute exists.
- **G4 emissions-honest** — `:fare/co2-kg` REQUIRED + positive on every fare; greenest is a first-class result; ranking uses true total cost (fare + baggage).
- **G5 no-person-tracking** — analysis takes fares only; no `:searcher`/`:person` attribute; search stateless.
- **G7 kotoba-EAVT-native** — fares/routes/observations are kotoba Datoms; no RisingWave/SQL.
- **G8 outward-gated** — live GDS/airline ingest = Council Lv7+ + operator; R0/R1 ship `:representative`; tsubasa transacts no booking.
- clj-native + kotoba-Datom-native (derived datoms flagged `:tsubasa/derived`).
- observation ledger: content-addressed, tamper-evident (verify-chain), deterministic/resume-safe, no-server-key, gitignored.
- heartbeat idempotent-by-content: an unchanged beat is a no-op (`:appended false`) — a recurring loop never bloats the chain.
- competition reading is a map routed to **:opening** (surface alternatives), NEVER a paid ranking and NEVER a target-list (the report says so, in those words).
