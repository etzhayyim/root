# tsubasa 翼 — MATURITY

> ADR-2606072800. Honest framing: unfinished items say so. The flight-route / fare
> discovery commons — the Skyscanner inversion (affiliate-stripped, member self-books,
> emissions-honest, no person fare-tracking).

| Phase | Scope | Status |
|---|---|---|
| **R0** | manifest + lexicons (fare / searchResult) + kotoba EAVT schema | ✅ landed |
| **R1** | clj-native live query handlers (`py/agent.cljc`): `search-fares` (true total cost + emissions surfaced) / `compare` (cheapest·greenest·fastest first-class) / `strip-affiliate` / `self-book-handoff` (no commission, member principal) | ✅ landed |
| **R2 — observatory + persistence** | canonical `flight-fare-ontology` (00-contracts) + rich `:representative` seed (13 airports / 9 regions / 13 carriers / 11 routes / 23 fares); `analyze.cljc` (per-route carrier-HHI concentration → competition reading → :opening route + cheapest/greenest/fastest + coverage gap worklist + EAVT datom-emit); `kotoba.cljc` content-addressed append-only commit-DAG (tx-cid / verify-chain, tamper-evident, no-server-key); `autorun.cljc` deterministic idempotent-by-content heartbeat; DID registered (INFRA_ACTORS + static did.json/profile) | ✅ landed |
| **R3 — gate unlock + live leg** (2026-06-21) | **G8 UNLOCKED** (founder Lv7+ attested via PR review, charter-bounded): `ingest.cljc` live fare ingest — `:public`/`:member-principal` sources only (`:paid-terminal` refused, Rider §2(e)/§2(i)), no network in the loop (no-server-key), G1/G4/G5 enforced at ingest (poisoned / no-CO₂ rows dropped), accepted fares → `:authoritative` + provenance; `digest.cljc` Murakumo-narrated digest (loopback-only `127.0.0.1:4000`, fail-open anti-dark template, G6); `wasm/` compute-only Component scaffold (`world.wit`+`build.sh`, no `wasi:sockets/clocks/random`) | ✅ code-complete (live pull + WASM artifact = operator step) |
| R3+ | fleet cell registration (cell-runner); the actual operator/member live pull with real sources; compiled WASM artifact + pinned CID | ⏳ operator step |

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
bb --classpath 20-actors 20-actors/tsubasa/methods/test_ingest.cljc          #  9 tests /  31 assertions (R3 live ingest + G8 bound + G1/G4/G5)
bb --classpath 20-actors 20-actors/tsubasa/methods/test_digest.cljc          #  6 tests /  16 assertions (R3 Murakumo fail-open + anti-dark)
bash 20-actors/tsubasa/run_tests.sh                                          # + handlers (test_agent: 10 tests / 157 assertions)
```

**54 tests / 579 assertions green** (incl. G1 no-commission/affiliate, G3 no-urgency/scarcity,
G4 co2 required + greenest first-class, G5 stateless/no-searcher, G8 paid-terminal refused —
the charter bounds proven *structurally*: the forbidden attribute / source does not exist, so it
cannot be emitted or ingested).

## Invariants held

- **G1 no-affiliate-no-inflow** — onward links affiliate-stripped; member self-books; `commission`/`affiliate`/`merchant` datoms unrepresentable (no such input, no such field — tested).
- **G3 anti-dark** — no `urgency`/`scarcity`/`price-will-rise` attribute exists.
- **G4 emissions-honest** — `:fare/co2-kg` REQUIRED + positive on every fare; greenest is a first-class result; ranking uses true total cost (fare + baggage).
- **G5 no-person-tracking** — analysis takes fares only; no `:searcher`/`:person` attribute; search stateless.
- **G7 kotoba-EAVT-native** — fares/routes/observations are kotoba Datoms; no RisingWave/SQL.
- **G8 outward UNLOCKED (R3, charter-bounded)** — founder Lv7+ attested via PR review; live ingest is `:public`/`:member-principal` only (`:paid-terminal` refused by `assert-clean-source`, Rider §2(e)/§2(i)), the loop does no network (no-server-key), G1/G3/G4/G5 enforced at ingest (poisoned / no-CO₂ dropped); tsubasa transacts no booking.
- **G6 Murakumo-only** — digest inference is loopback `127.0.0.1:4000` (external LLM unrepresentable); fail-open to a deterministic anti-dark template.
- clj-native + kotoba-Datom-native (derived datoms flagged `:tsubasa/derived`).
- observation ledger: content-addressed, tamper-evident (verify-chain), deterministic/resume-safe, no-server-key, gitignored.
- heartbeat idempotent-by-content: an unchanged beat is a no-op (`:appended false`) — a recurring loop never bloats the chain.
- competition reading is a map routed to **:opening** (surface alternatives), NEVER a paid ranking and NEVER a target-list (the report says so, in those words).
