# 20-actors/tsubasa 翼

**Flight-route / fare discovery commons — the Skyscanner inversion. ADR-2606072800. Status: R3.**

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
- `methods/ingest.cljc` — **R3** live fare ingest: a parsed fetch-leg payload → `:authoritative`
  `:fare` rows. Charter-bounded source (`:public`/`:member-principal`; `:paid-terminal` refused),
  no network in the loop (no-server-key), G1/G4/G5 enforced (poisoned / no-CO₂ rows rejected).
- `methods/digest.cljc` — **R3** Murakumo-narrated digest, loopback-only (`127.0.0.1:4000`),
  fail-open to a deterministic anti-dark template (G6).
- `wasm/` — **R3** compute-only WASM Component scaffold (`world.wit` + `build.sh`); no
  `wasi:sockets/clocks/random` (absence = G1/G5/G6); artifact build = operator step.
- `methods/test_*.cljc` — analyze / kotoba / autorun / seed-integrity / ingest / digest suites.

## Run
```
bash 20-actors/tsubasa/run_tests.sh                                   # 54 tests / 579 assertions
bb --classpath 20-actors 20-actors/tsubasa/methods/analyze.cljc      # competition + fare map + coverage
bb --classpath 20-actors 20-actors/tsubasa/methods/autorun.cljc      # one heartbeat → append to the ledger
bb --classpath 20-actors 20-actors/tsubasa/methods/digest.cljc       # Murakumo digest (fail-open template)
# live ingest (operator/member fetch leg writes payload.edn in their OWN runtime):
bb --classpath 20-actors 20-actors/tsubasa/methods/ingest.cljc payload.edn "<source-url>" "<as-of>" [member]
```

## Gating (G8 — UNLOCKED R3, charter-bounded)
Live GDS/airline fare ingest is **UNLOCKED** (R3, 2026-06-21) — founder Lv7+ attested via PR review
(Bootstrap Council attestation premise). The unlock is **structurally bounded**: source is
`:public` or `:member-principal` ONLY (a `:paid-terminal` is refused — Rider §2(e)/§2(i)); the loop
does **no network** (operator/member runs the fetch leg; no-server-key); **G1/G3/G4/G5 unchanged**
and enforced at ingest (poisoned / no-CO₂ rows rejected); tsubasa transacts no booking (member
self-books). See ADR-2606072800 §R3 for the full gate-unlock record.

## DID
`did:web:etzhayyim.com:actor:tsubasa` — registered in `50-infra/.../registry/infra-actors.ts`
(+ static `public/actor/tsubasa/{did,profile}.json`). primaryLexicon `com.etzhayyim.tsubasa.fare`,
primarySchema `flight-fare-ontology.kotoba.edn`.
