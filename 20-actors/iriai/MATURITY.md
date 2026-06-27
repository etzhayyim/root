# iriai 入会 — MATURITY

**ADR-2606272200** · clj-native R0 · `did:web:etzhayyim.com:iriai`

## R0 checklist (15/15)

- [x] manifest.edn — actor id/glyph/tier/purpose/gates G1–G8/non-goals N1–N5/composes
- [x] ontology — `kotoba/ontology.iriai.edn` (entities/lifelines/verdicts/instruments/attributes + NEGATIVE SPACE)
- [x] synthetic seed — `kotoba/seed.edn` (6 regions × 4 lifelines = 24 cells, all six verdicts)
- [x] infra layer — `methods/infra.cljc` (commons-gap + resilience → verdict → assess → datoms → report)
- [x] 資金 funding layer — `methods/fund.cljc` (§1.16 in-kind proposal, cash≡0, give-only, imputed value)
- [x] 管理 management layer — `methods/manage.cljc` (1 SBT=1 vote + :intent + no-server-key)
- [x] gates — `methods/gates.cljc` (ex-info assertions + structural `forbidden-absent?`)
- [x] persistence — `methods/kotoba.cljc` (content-addressed append-only commit-DAG, verify-chain)
- [x] heartbeat — `methods/autorun.cljc` (deterministic, idempotent-by-content, resume-safe)
- [x] seed loader — `methods/iriai_edn.cljc`
- [x] tests — 6 suites, **40 tests / 311 assertions green** (bb)
- [x] runner — `run_tests.clj` (bb-native, no shell, ADR-2606072802)
- [x] docs — README.md + CLAUDE.md + this MATURITY.md
- [x] ADR — `90-docs/adr/2606272200-iriai-lifeline-commons-infra-funding-management.md`
- [x] gitignore — `data/persisted/` (generated ledger never committed)

## Verdict distribution (synthetic seed)

| verdict | count | example |
|---|---|---|
| :provision | 4 | kibou (off-grid rural, all four lifelines) |
| :redundancy | 2 | shima (single-source island power + telecom) |
| :reinforce | 4 | saigai (disaster-degraded) |
| :maintain | 9 | midori / machi / shima water+gas |
| :await-consent | 4 | yama (high need, no consent) |
| :monitor | 1 | machi gas (below adequate, low burden) |

Funding plan: **10 proposals** (provision + reinforce + redundancy) · imputed §1.16 income value
aggregate · **cash to consumer $0**. Governance: **10 decisions**, all `:intent`-only, all keyless,
2 escalated to Council Lv7+ (critical-infra provision).

## R0 → R1 → R2

- **R1 (G7-gated)**: real region/utility-coverage ingest from public open data (World Bank / IEA /
  WHO-JMP / ITU — read-only, no key); inochi/jinushi land-sovereignty grounding for consent; amime
  N-1 energy-mesh join for the electric layer.
- **R2**: fleet registration (cell-runner cells.edn + healthz, the kaname/kafun track);
  Murakumo-narrated commons digest; live kotoba-engine bridge (ibuki-R3); lexicon JSON.

Live production + actuation stays the producer actors' (hikari/mizuho/kamado/noroshi) under
Council Lv7+, never iriai.
