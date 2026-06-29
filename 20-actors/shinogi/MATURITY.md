# shinogi 鎬 — maturity scorecard

ADR-2606291200 · R0 scaffold · generated from the substrate (do not hand-drift).

## R0 checklist

- [x] ADR authored (`90-docs/adr/2606291200-…`)
- [x] manifest.edn (id/glyph/tier/domain/kind/purpose/status/gates/non-goals/composes-with)
- [x] ontology (`kotoba/ontology.shinogi-exam.edn`) — 9 stocks · 10 loops · Meadows 12 · negative space
- [x] seed (`kotoba/seed.exam-involution.edn`) — 33 drivers / 6 jurisdictions (China-primary)
- [x] loader (`methods/shinogi_edn.cljc`)
- [x] analysis-only read-off (`methods/analyze.cljc`) — stocks/loops/failure-cycle/youth-withdrawal/leverage/coverage/datoms/report
- [x] time-series stock-flow simulation + intervention what-if (`methods/simulate.cljc`)
- [x] wellbecoming energy-flow design (`methods/energy_flow.cljc`, two-ledger discipline)
- [x] social-protocol activity membrane (`methods/social.cljc`, dry-run / no-server-key / live-gated)
- [x] content-addressed append-only ledger (`methods/kotoba.cljc`, verify-chain)
- [x] idempotent-by-content heartbeat (`methods/autorun.cljc`)
- [x] tests green — `bb 20-actors/shinogi/run_tests.clj` → 43 tests / 446 assertions
- [x] gates pinned (G4/G5/G6/G7/G8/G9/G11/G13/G14 — manifest + ontology negative space + analyze/social/energy enforcement)
- [x] static did.json/profile (`50-infra/etzhayyim-did-web/public/actor/shinogi/`, verificationMethod [])

## Coverage (seed iteration 1)

- drivers: 33
- jurisdictions: 6 (CN primary · KR · JP · IN · FI · DE)
- stocks covered: 9 / 9 (exam A–F + labor G + withdrawal H–I)
- lifecycle phases: 1 EXAM (A–F) · 2 LABOR (G 卒業即失業) · 3 WITHDRAWAL (H 頑張れない, I 躺平)
- China drivers: ~21 across all phases (exam: gaokao/985-211/户籍/双减/复读/衡水/内卷/躺平/普职分流/one-child/考研考公/mental-health; labor: 高校扩招/毕业即失业/学历贬值/35岁/996; withdrawal: 985废物/慢就业/全职儿女/摆烂/润/稳就业)
- comparative siblings: JP 就職氷河期/さとり/ひきこもり + KR N포세대/헬조선 (lost-generation precedents)

## Next /loop worklist (from analyze coverage)

- add relieving drivers for `effort-inflation` + `credential-signaling`
- deepen the thinnest stocks; balance the large withdrawal-cycle relief-gap with more relief drivers (G/H/I)
- broaden jurisdiction coverage (more Asian + Global-South exam + youth-labor systems)

## R1+ (not yet)

- child repo `etzhayyim/com-etzhayyim-shinogi` + west `manifest/repos.edn` entry + RAD identity journal
- DataLad dataset `80-data/shinogi-exam/` (findings snapshot + ledger + provenance)
- live public-data ingest (MOE/KICE/MEXT/NTA aggregate statistics) — G7/operator-gated (the loop does no network I/O)
- hakoniwa coupling (forward-sim of synthetic student cohorts over the mapped loops)
