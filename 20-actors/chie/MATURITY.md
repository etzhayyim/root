# chie 智慧 — maturity scorecard

**ADR-2606171200** · status **🟢 R0** (clj-native · kotoba/Datom-native · tests green).

## Scorecard

| Dimension | State | Evidence |
|---|---|---|
| Ontology | ✅ | `kotoba/schema.edn` — 11 node kinds · 8 edge kinds · 4 axes · forbidden set |
| Seed (representative) | ✅ | `data/seed-ai-ecosystem.kotoba.edn` — 39 nodes / 39 縁 (labs/cos/funders/states/policy/models/roles) |
| Analyzer (edge-primary) | ✅ | `methods/analyze.cljc` — opening / reach / fragility + 4-axis concentration, on-read |
| Datom emitter (EAVT) | ✅ | `methods/datom_emit.cljc` — GROUND `:add` + DERIVED `:derived` (transient), deterministic |
| Coverage / gap honesty | ✅ | `methods/coverage_report.cljc` — sourcing split + gap worklist, "~0 by design" |
| Tests | ✅ | 3 suites · 69 assertions green (`bb test:actors` auto-discovers) |
| Charter gates G1–G5 | ✅ | test-enforced: open→0 (G1), inbound-integral (G2), representative-only (G5), no-trade/no-score (G4) |
| Cross-actor bridge | ✅ (declared) | `:bridge` → kanjō/kabuto/handotai/kasa/kenkyusha/keizu/kosatsu/abaki |
| **常駐化 (resident heartbeat)** | ⏳ R1 | autorun cell + fleet.toml registration + kotoba commit-DAG bridge (ibuki/mimamori pattern) |
| Live ingest | ⏳ R2 (G7) | regulator texts (EU AI Act/広島/Bletchley) + disclosed rounds + Wikidata — Council+operator-gated |
| WASM (pywasm/componentize) | ⏳ R2 | clj source is the pywasm target; build = operator step |

## Roadmap (loop targets)

- **R1 — 常駐化**: `autorun.cljc` heartbeat → analyze → Murakumo digest (loopback, template
  fallback) → content-addressed Datom tx appended to the append-only kotoba commit-DAG
  (`verify-chain` tamper-evident, resume-safe). Register `ChieHeartbeatCell` in the
  cell-runner `cells.edn` + a fleet node (off-minute cron), mirroring mimamori/ibuki. The
  heartbeat is STATELESS → host owns the log.
- **R1 — coverage growth**: lift node coverage (more labs/funders/policy), add
  `:ai.invest/round` (per-round capital) and `:ai.asset/compute` (clusters → kasa) — both
  currently surfaced as gaps by `coverage_report`.
- **R2 — live leg**: G7/Council-gated ingest from primary sources (kanjō pattern); per-tx
  provenance + exactly-once cursor.

## Invariants the suite locks

1. open accumulator → opening-priority 0 (G1, not a winner-rank).
2. concentration = integral of incident inbound 縁 (G2, no stored score).
3. seed is 100% `:representative`; gaps named, never fabricated (G5).
4. `:trade` / `:forecast` / `:ai/score` never appear in the emitted Datom log (G4).
5. emit is deterministic (byte-identical for identical input).
