# shinogi 鎬 — maturity scorecard

ADR-2606291200 · R0 scaffold · generated from the substrate (do not hand-drift).

## R0 checklist

- [x] ADR authored (`90-docs/adr/2606291200-…`)
- [x] manifest.edn (id/glyph/tier/domain/kind/purpose/status/gates/non-goals/composes-with)
- [x] ontology (`kotoba/ontology.shinogi-exam.edn`) — 6 stocks · 6 loops · Meadows 12 · negative space
- [x] seed (`kotoba/seed.exam-involution.edn`) — 18 drivers / 6 jurisdictions (China-primary)
- [x] loader (`methods/shinogi_edn.cljc`)
- [x] analysis-only read-off (`methods/analyze.cljc`) — stocks/loops/failure-cycle/leverage/coverage/datoms/report
- [x] content-addressed append-only ledger (`methods/kotoba.cljc`, verify-chain)
- [x] idempotent-by-content heartbeat (`methods/autorun.cljc`)
- [x] tests green — `bb 20-actors/shinogi/run_tests.clj` → 26 tests / 256 assertions
- [x] gates pinned (G4/G5/G6/G7/G8/G9/G11 — manifest + ontology negative space + analyze emission)
- [x] static did.json/profile (`50-infra/etzhayyim-did-web/public/actor/shinogi/`, verificationMethod [])

## Coverage (seed iteration 1)

- drivers: 18
- jurisdictions: 6 (CN primary · KR · JP · IN · FI · DE)
- stocks covered: 6 / 6
- China drivers: 11 (gaokao, 985/211/双一流, 户籍 quota, 双减, 复读, 衡水模式, 内卷 norm, 躺平 counter-norm, 普职分流, one-child legacy, 考研/考公, mental-health plan)

## Next /loop worklist (from analyze coverage)

- add relieving drivers for `effort-inflation` + `credential-signaling`
- deepen the thinnest stock (`failure-penalty`)
- broaden jurisdiction coverage (more Asian + Global-South exam systems)

## R1+ (not yet)

- child repo `etzhayyim/com-etzhayyim-shinogi` + west `manifest/repos.edn` entry + RAD identity journal
- DataLad dataset `80-data/shinogi-exam/` (findings snapshot + ledger + provenance)
- live public-data ingest (MOE/KICE/MEXT/NTA aggregate statistics) — G7/operator-gated (the loop does no network I/O)
- hakoniwa coupling (forward-sim of synthetic student cohorts over the mapped loops)
