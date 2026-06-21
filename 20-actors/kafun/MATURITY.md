# kafun 花粉 — MATURITY

| Phase | Scope | Status |
|---|---|---|
| **R0** (ADR-2606211712) | clj-native 花粉撲滅 remediation gate: loader + pollen-burden/verdict/assess/datoms/report + 12-stand synthetic seed + content-addressed REMEDIATION LEDGER (`kotoba.cljc`, verify-chain) + deterministic idempotent-by-content heartbeat (`autorun.cljc`) + tests | ✅ landed |
| **ie-flow embedding** (ADR-2606212030) | `ie_flow.cljc`: kafun assessment → measured ie-flow events folded through the SHARED `etzhayyim.ie-flow.metrics` (not a fork); energy-flow viz `viz/energy-flow.html` (整流 = scattered burden → prioritized restoration order; order-index 0.320 / η 6.58× / non-parasitic) | ✅ landed |
| **score + organism reward** (ADR-2606212200) | kafun is scored as an information-control actor (`etzhayyim.ie-flow.score`): info-control-score = its active-inference 利得, gated by 子孫 (:descendant 0.85); contributes to the colony-order negentropy source feeding ibuki's metabolic reward. Real scoreboard entry (score 0.452) | ✅ landed |
| R1 — inochi grounding | `bridge.cljc`: ground `:protected`/habitat-sensitivity in inochi 命's ecological observation (ugachi/busshi bridge pattern) — a stand in a high-biodiversity biome favors `:protected-selective` over clearcut, never fabricates protection | ⏳ |
| R1 — heartbeat record! | wire `autorun` to also `record!` kafun's ie-flow events to `80-data/ie-flow/kafun/flow.kotoba.edn` each beat (the ie-flow ADR-2606212200 live-record follow-up) so kafun's scoreboard entry is heartbeat-produced | ⏳ |
| R1 — Murakumo digest | Murakumo-narrated remediation digest (fail-open template, G6) | ⏳ |
| R1 — fleet + lexicons | cell-runner registration (+ healthz, the ugachi/kaname maturity track); lexicon JSON under `00-contracts/lexicons/com/etzhayyim/kafun/` | ⏳ |
| R1 — real stands (G7) | real cadastral + Sentinel-2/ALOS canopy → kotoba (the legacy ADR-2605100100 scout→cadastral→envoy pipeline, behind an operator flip) | ⏳ (operator/Council step) |
| R2+ | live forestry — a SEPARATE landowner + operator/Council step, NEVER kafun (G5/G7) | ⏳ (out of kafun scope by G5) |

## Tests

```
bb --classpath 20-actors 20-actors/kafun/methods/test_kafun_edn.cljc    # 3 tests / 9 assertions
bb --classpath 20-actors 20-actors/kafun/methods/test_remediate.cljc    # 12 tests / 29 assertions
bb --classpath 20-actors 20-actors/kafun/methods/test_kotoba.cljc       # 3 tests / 11 assertions (ledger)
bb --classpath 20-actors 20-actors/kafun/methods/test_autorun.cljc      # 4 tests / 13 assertions (heartbeat + idempotency)
# the SoS embedding suite needs the shared ie-flow lib on the classpath:
bb -cp "20-actors:70-tools/src:20-actors/kotodama/src" \
   20-actors/kafun/methods/test_ie_flow.cljc                            # 6 tests / 22 assertions (ie-flow + viz)
# or all five at once:
./20-actors/kafun/run_tests.sh
```

28 tests / 84 assertions green.

## Invariants held

- **G1 撲滅 = restoration** — 主伐 without 再造林 → `:refuse :clearcut-without-reforest`; `:kafun/clearcut` + `:kafun.stand/eradicate-species` unrepresentable (test-enforced)
- **G5 never-acts** — no `:kafun/actuate`; assessment + R0 design only; live forestry is the landowner's + operator/Council step
- **G2 map-not-cut-list / no person data** — restoration worklist, never a cut-list/target-list; `:kafun.person/health` unrepresentable (cohorts aggregate)
- hard refusals precede every other route (no `replant=false` / net-carbon-positive stand returns a permit — meta-test)
- consent/land-sovereignty (G3) → `:await-consent` · protected (watershed/steep) → `:protected-selective` (never 皆伐) · carbon-balance §2(d) (G4) → `:refuse :carbon-positive`
- clj-native + kotoba-Datom-native; verdict datoms flagged `:kafun/derived` + `:kafun/sourcing`
- remediation ledger: content-addressed, tamper-evident (verify-chain), deterministic/resume-safe, no-server-key, gitignored (never committed)
- heartbeat idempotent-by-content: an unchanged beat is a no-op (`:appended false`) — a recurring loop never bloats the chain; it grows only on real change
- ie-flow: embeds the SHARED metrics (not a fork); kafun moves INFORMATION-energy only (a prioritized map), never physical forestry
- score: a parasitic / 子孫-harming kafun would be vetoed to 0 — it cannot feed the organism reward by predation (G-parasitism / G-subordinate as a scalar)
- R0 seed `:synthetic` (real cadastral/satellite ingest + live actuation = operator/Council steps)
