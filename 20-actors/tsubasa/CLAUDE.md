# 20-actors/tsubasa 翼

**Flight-route / fare discovery commons — the Skyscanner inversion. ADR-2606072800. Status: R2.**

Honest fare/route meta-search; closes the last named-app coverage gap (uber→ainori, airbnb/
hotels→shukubo, salesforce→business-manager, calendly→yotei, drive→organizer, indeed→talent,
shopify→omise, **flight-scanner→tsubasa**). Sibling of `watari` (live position) — tsubasa plans,
watari tracks; both observational, neither an OTA.

## Hard prohibitions (structurally unrepresentable, not policy)
- **No affiliate / no inflow** (G1): onward links affiliate-stripped; member self-books on the
  airline's OWN site; tsubasa is never merchant-of-record (`commissionMinor`/`titheMinor` ≡ 0,
  `principal` = member). No commission/affiliate/merchant field in any lexicon, ontology, or datom.
- **Emissions-honest** (G4): `co2Kg` / `:fare/co2-kg` is REQUIRED on every fare/result; `compare`
  exposes the greenest option as a first-class result — a high-CO₂ option cannot be ranked-away
  invisibly. Rank by true total cost (fare + baggage), not headline fare.
- **Anti-dark** (G3): no urgency / "price will rise" / scarcity field exists.
- **No person fare-tracking** (G5): search is stateless w.r.t. the searcher; no `:searcher`/`:person` field.

These are enforced *structurally* — the forbidden attributes are absent from the ontology, the
seed, and the datom emitter — and proven by `test_analyze` + `test_seed_integrity`.

## Layout
- `py/agent.cljc` / `py/agent.clj` — live query handlers: `search-fares` (true total cost +
  emissions surfaced) · `compare` (cheapest·greenest·fastest first-class) · `strip-affiliate` ·
  `self-book-handoff` (no commission, member principal). py→clj port (`py/agent.py`).
- `00-contracts/schemas/flight-fare-ontology.kotoba.edn` — canonical EAVT ontology (with the
  constitutional boundary in its header). `kotoba/schema.edn` is the legacy R0 schema (subset).
- `data/seed-fares.kotoba.edn` — `:representative` seed (13 airports / 9 regions / 13 carriers /
  11 routes / 23 fares). Committed input; `data/persisted/` is the generated ledger (gitignored).
- `methods/analyze.cljc` — per-route carrier-HHI concentration → competition reading → `:opening`
  route + cheapest/greenest/fastest + coverage gap worklist + EAVT `datoms` + markdown report.
- `methods/kotoba.cljc` — content-addressed append-only commit-DAG (`tx-cid` / `verify-chain`,
  tamper-evident, no-server-key) — the busshi/meisai/kakaku family machinery.
- `methods/autorun.cljc` — deterministic, idempotent-by-content heartbeat (analyze → append on
  change; a no-op when unchanged; resume-safe).
- `methods/test_*.cljc` — analyze / kotoba / autorun / seed-integrity suites.

## Run
```
bash 20-actors/tsubasa/run_tests.sh                                   # 39 tests / 532 assertions
bb --classpath 20-actors 20-actors/tsubasa/methods/analyze.cljc      # competition + fare map + coverage
bb --classpath 20-actors 20-actors/tsubasa/methods/autorun.cljc      # one heartbeat → append to the ledger
```

## Gating
Live GDS/airline fare ingest = **Council Lv7+ + operator** (G8). R0/R1 ship `:representative` data;
tsubasa transacts no booking (member self-books). See ADR-2606072800 for the full gate table.

## DID
`did:web:etzhayyim.com:actor:tsubasa` — registered in `50-infra/.../registry/infra-actors.ts`
(+ static `public/actor/tsubasa/{did,profile}.json`). primaryLexicon `com.etzhayyim.tsubasa.fare`,
primarySchema `flight-fare-ontology.kotoba.edn`.
