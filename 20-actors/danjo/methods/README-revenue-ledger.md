# danjo revenue-ledger — module map

Navigational index for reviewers. Full design + the honest answer: `../REVENUE-LEDGER.md`.
ADR: `90-docs/adr/2606151200-danjo-revenue-ledger-clj.md` (on danjo master 2605301600).
Run all tests: `../run_tests_clj.sh` (bb) · `CLJ_RUNNER=clojure ../run_tests_clj.sh` (JVM). 253 checks.
Script suites live in `methods/revenue-ledger-suite/` (a hyphen-dir) so the repo-wide `bb test:actors`
auto-discovery skips them — they are owned by `run_tests_clj.sh`, exactly as mimamori/yobel/ibuki own
theirs. `test_analyze.cljc` (danjo's clojure.test suite) stays in `methods/` and runs under `bb test:actors`.

## Pipeline (load order: each `load-file`s the ones below it)

```
ingest ─┐                         data/ (all :representative, NOT authoritative)
taxes ──┤→ revenue_ledger ─┐       ├ gov-revenue-{seed,corpus}.jp.edn   歳入 corpus
        │   (trace + EAVT  │       ├ gov-fiscal-seed.jp.json            danjo budgetRecord (JSON)
transfers┤    + local log) │       ├ jp-general-budget.jp.edn          一般会計 主要経費 (COFOG)
discrepancy┘               │       ├ jp-national-taxes.edn / jp-local-taxes.edn   29税
org_actor                  │       ├ jp-fiscal-transfers.edn           国→地方 交付税/譲与税
   ↓                       ↓       ├ jp-fiscal-orgs.edn                9 org mirror-actors
coverage → maturity → cofog_xcheck   └ actors/*.profile.json + REVENUE-{COVERAGE,MATURITY}.md (generated)
   ↓
autorun (heartbeat) · kotoba_bridge (live transact)
```

## Methods (`*.clj` = code, `test_*.clj` = its suite)

| module | role | honesty anchor |
|---|---|---|
| `revenue_ledger` | model + `trace` + EAVT `[:db/add]` + local commit-DAG log (`run-cycle!`/`verify-chain`) | `outlay-datoms` RAISES on funded-by-tax through 一般会計 (G4 analogue); G5 ≥2 CIDs |
| `ingest` | passive (G3) projection of `gov.dataset.*` EDN+JSON → model; `full-model` (single SoT) | dep-free `parse-json`; account-earmark is law, not data |
| `taxes` | 29-tax registry (国+地方) + honest 3-way `classify` (general/statutory-purpose/special-account) | per-yen IFF `:special-account` |
| `transfers` | 国→地方 法定率繰入 (交付税) + 譲与税, per-yen-traceable | portion-honesty (a fungible tax's legal portion is traceable without flipping the whole) |
| `discrepancy` | appropriation↔outlay reconciliation → `:danjo.obs/*` (danjo derived_datoms shape) | non-adjudicating; category enum verdict-free (G4); method-note (G6) |
| `org_actor` | real fiscal orgs → keyless mirror-actors + `did:web` profiles (`->json`) | `keyless`, empty `verificationMethod` (no-server-key, ADR-2606042330) |
| `coverage` | honest coverage report + `full-md` scorecard | non-traceable taxes counted, not hidden (G5) |
| `cofog_xcheck` | validates COFOG codes vs matsurigoto's canonical standard | cross-actor correctness |
| `maturity` | executable gate: 10 honesty invariants across ALL data → `REVENUE-MATURITY.md` | a regressed invariant turns the scorecard ❌ |
| `autorun` | offline fleet heartbeat — whole pipeline → 1 content-addressed tx/cycle | deterministic, resume-safe, tamper-evident, no I/O |
| `kotoba_bridge` | local log → live kotoba `datomic.transact` (ibuki R3) | host-allowlisted, dry-run default, no-server-key |
| `test_freshness` | committed generated artifacts must match the generators (no drift) | — |
| `test_honesty_adversarial` | 16 attacks on the guarantees, all must fail | — |

Lexicons: `00-contracts/lexicons/com/etzhayyim/danjo/{taxClassification,fiscalOrg,reconciliationObservation}.json`.
Manifest: `../manifest.jsonld` → `revenueLedger` block.
