---
id: cohort-identity-posterior-mv-draft-260414
title: "Cohort Identity Posterior MV — Kotoba/Datomic DDL Draft (ADR-0026 Iter 2)"
status: active
doc_type: how-to
topic: cohort-evaluation
authoritative: false
last_verified: 2026-04-14
related:
  - adr-0026-agent-only-reverse-identity-topology
  - cohort-coverage-evaluation-baseline-260414
supersedes: []
superseded_by: []
---

# Goal

ADR-0026 Phase B/C の fission 判定に必要な `identity_posterior_mv` を設計ドラフトで固定。
runnable migration は本番適用済みで、最終採番は `30-graph/graph-schema/migrations/0054_cohort_identity_posterior_mv.ts`。

# Pre-flight checks

graph-schema CLAUDE.md §MV Memory Safety Guardrails 準拠:

| 項目 | 見積 | 判定 |
|---|---|---|
| `GROUP BY cohort_did` cardinality | 初期 31、スケール後 ~10k | ✅ < 500k |
| MV backfill row count | `vertex_repo_record WHERE collection='com.etzhayyim.cohort.evidence'` 初期 0 | ✅ 問題なし |
| MAX(varchar) 列数 | 0 (数値 aggregate のみ) | ✅ 回避 |
| payload columns fan-out | なし (narrow MV; cohort_did + posterior + evidence_count のみ) | ✅ |

→ MATERIALIZED VIEW で安全。

# Draft DDL

```sql
-- Migration: 0054_cohort_identity_posterior_mv.ts (applied)
-- Source collection: com.etzhayyim.cohort.evidence
-- Drives: ADR-0026 Phase C fission gate (posterior > 0.95 + judgeAgreement)

CREATE MATERIALIZED VIEW mv_cohort_identity_posterior AS
SELECT
  cohort_did,
  COUNT(*)::BIGINT                                              AS evidence_count,
  AVG(posterior)::DOUBLE PRECISION                              AS avg_posterior,
  MAX(posterior)::DOUBLE PRECISION                              AS max_posterior,
  SUM(CASE WHEN judge_agreement THEN 1 ELSE 0 END)::BIGINT      AS judge_agree_count,
  SUM(CASE WHEN posterior > 0.95 AND judge_agreement
           THEN 1 ELSE 0 END)::BIGINT                           AS fission_ready_count,
  MAX(observed_at)                                              AS last_evidence_at
FROM vertex_repo_record
WHERE collection = 'com.etzhayyim.cohort.evidence'
GROUP BY cohort_did;

-- Index for hot read (fission decision path)
-- Kotoba/Datomic MV auto-indexes the GROUP BY key; no explicit CREATE INDEX needed.
```

## Required promoted columns (insert pipeline)

`vertex_repo_record` は promoted column 設計 (graph-schema CLAUDE.md §Schema Design)。`com.etzhayyim.cohort.evidence` 用に追加する列:

| Column | Type | Nullable | Source (lexicon path) |
|---|---|---|---|
| `cohort_did` | VARCHAR | NOT NULL | `$.cohortDid` |
| `evidence_hash` | VARCHAR | NOT NULL | `$.evidenceHash` |
| `signal_kind` | VARCHAR | NOT NULL | `$.signalKind` |
| `posterior` | DOUBLE PRECISION | NULL | `$.posterior` |
| `judge_agreement` | BOOLEAN | NULL | `$.judgeAgreement` |
| `tier` | VARCHAR | NOT NULL | `$.tier` (const 'tier1-hashed') |
| `observed_at` | TIMESTAMP | NOT NULL | `$.observedAt` |

`50-infra/cloudflare/workers/atproto/src/insert-columns.ts` の allowlist 拡張が前提。

# Fission Decision Query (application-layer)

```typescript
const ready = await db.selectFrom('mv_cohort_identity_posterior' as any)
  .select(['cohort_did', 'fission_ready_count', 'max_posterior', 'evidence_count'])
  .where('max_posterior', '>', 0.95)
  .where('fission_ready_count', '>=', 1)
  .execute();
// → com.etzhayyim.cohort.fission procedure を cohort_did ごとに呼ぶ
```

# k-anonymity Re-evaluation (companion MV, Phase B scheduler)

```sql
-- MV #2: cohort k-anonymity drift detection
CREATE MATERIALIZED VIEW mv_cohort_k_drift AS
SELECT
  cohort_did,
  COUNT(DISTINCT signal_kind)::BIGINT AS distinct_signal_kinds,
  COUNT(*)::BIGINT                    AS evidence_count,
  -- k proxy = evidence_count / distinct signal_kinds (rough anonymity set size)
  CASE WHEN COUNT(DISTINCT signal_kind) = 0 THEN 0
       ELSE COUNT(*) / COUNT(DISTINCT signal_kind)
  END::BIGINT                         AS k_proxy
FROM vertex_repo_record
WHERE collection = 'com.etzhayyim.cohort.evidence'
GROUP BY cohort_did;
```

`k_proxy < 50` 検出時 → Path F `scheduler` middleware が `cohortKReevaluate` task を enqueue。

# Process Mining 連携 (ADR-0025 OCEL)

Evidence write が `vertex_repo_record` に commit → PDS commit pipeline → `onCommit` handler が下記 OCEL event を `com.etzhayyim.apqc.apqcEvent` に emit:

| MV 状態遷移 | OCEL eventType | APQC L1 DID 経路 |
|---|---|---|
| 新 cohort 登場 (evidence_count 0→1) | `cohort.genesis` | segment_hash.pcfL1 → `did:web:kyber-projector.etzhayyim.com:apqc:{L1}` |
| evidence 追加 | `cohort.evidence.accrued` | 同上 |
| k_proxy < 50 | `cohort.kReevaluated` (violation) | 同上 |
| fission_ready_count ≥ 1 && fission_enabled | `cohort.fission` | 同上 |

OCEL object list: `cohort` (cohort_did), `evidence` (evidence_hash), 条件により `individual` (post-fission did:plc)。

# Migration Plan (completed 2026-04-14)

1. `insert-columns.ts` に 7 列追加
2. `migrations/0052_vertex_repo_record_cohort_columns.ts` / `0053_vertex_cohort_actor.ts` / `0054_cohort_identity_posterior_mv.ts` として確定
3. `30-graph/graph-schema/CLAUDE.md` §Migration History を更新
4. 本番 Kotoba/Datomic に apply 完了
5. `src/database.ts` に `MvCohortIdentityPosteriorRow` / `MvCohortKDriftRow` 型追加済

# References

- `30-graph/graph-schema/CLAUDE.md` §MV Memory Safety Guardrails
- `50-infra/cloudflare/workers/atproto/src/insert-columns.ts`
- `00-contracts/lexicons/com/etzhayyim/cohort/evidence.json`
- `00-contracts/lexicons/com/etzhayyim/cohort/fission.json`
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
