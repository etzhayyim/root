# junkan 循環 — maturity scorecard (governance-asymmetry substrate)

ADR-2605290927 · clj-native, kotoba-Datom-native · updated 2026-06-21

## What this substrate answers

全世界の政府で **国民と政府を構造的に不均衡にしている具体的な法律・制度・思想・
価値観** を、5 つの asymmetry STOCK と feedback LOOP の system-dynamics で読み取る。
各 instrument に **誰が定めたか (enactor) / 経緯 (origin) / 関係者 (stakeholders)**
を記録。**分析専用 (G4) · 仮説のみ (G5) · 集計のみ (G6) · MAP であって target-list
ではない (G7)。**

## R0 → R1 checklist

| # | item | status |
|---|---|---|
| 1 | ontology (EAVT schema, 5 stocks, loops, Meadows, negative space) | ✅ `kotoba/ontology.junkan-gov.edn` |
| 2 | global instrument seed (laws/institutions/doctrines/values) | ✅ 35 instruments · 17 jurisdictions |
| 3 | 誰が (enactor) on every instrument | ✅ test-enforced |
| 4 | 経緯 (origin) on every instrument | ✅ test-enforced |
| 5 | 関係者 (stakeholders) on every instrument | ✅ test-enforced |
| 6 | all 5 asymmetry stocks covered | ✅ test-enforced |
| 7 | both polarities present (widen + narrowing/balancers) | ✅ test-enforced |
| 8 | analysis read-off (stock regimes + loops + leverage + coverage) | ✅ `methods/analyze.cljc` |
| 9 | EAVT datom emission (flagged :derived + :hypothesis) | ✅ 550 datoms |
| 10 | content-addressed findings ledger (commit-DAG, verify-chain) | ✅ `methods/kotoba.cljc` |
| 11 | deterministic idempotent-by-content heartbeat | ✅ `methods/autorun.cljc` |
| 12 | G4 analysis-only (no outward channel; by absence) | ✅ test-enforced |
| 13 | G5 hypothesis-only (no proven causation) | ✅ test-enforced |
| 14 | G6 aggregate-only (no person/PII attr) | ✅ test-enforced |
| 15 | G11 candidates-not-directives | ✅ test-enforced |
| 16 | datalad dataset (snapshot + provenance + report) | ✅ `80-data/junkan-governance/` |
| 17 | tests green | ✅ 33 tests / 564 assertions |
| 18 | live passive-data ingest (Tier-A public archives) | ⏳ R1, Council-gated |
| 19 | kotoba-kqe live-engine binding | ⏳ R1 |
| 20 | Murakumo-only LLM-assisted loop-naming | ⏳ R1 |

## Current read-off (HYPOTHESIS — see report.md)

- **participation-barrier** stock reads **vicious** (net +0.23): widening
  instruments dominate; the **B-participation** balancing loop is being overwhelmed.
- information / coercion / paradigm / economic stocks read **transitioning**
  (contested — strong widening and narrowing forces both present).
- Deepest amplify-candidates: Magna Carta (L1), UDHR (L2), Swiss direct democracy
  (L4). Most-tractable flip-candidates: statutory surveillance/foreign-agent laws (L5).

## Coverage worklist (grows each /loop iteration)

- broaden jurisdiction coverage — Global South / small states under-represented
- (auto-generated; see `analyze/coverage`): add balancers for any stock lacking one
