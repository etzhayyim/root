---
id: coverage-infer-statistical-entity-resolution-260416
title: "etzhayyim coverage infer — Statistical Entity Resolution via RisingWave Python UDF"
status: active
doc_type: how-to
topic: cohort-evaluation
authoritative: true
last_verified: 2026-04-16
related:
  - adr-0026-agent-only-reverse-identity-topology
  - cohort-identity-posterior-mv-draft-260414
  - cohort-coverage-evaluation-baseline-260414
supersedes: []
superseded_by: []
---

# Goal

多様な統計データ (ILOSTAT, 国勢調査, 業界統計等) から潜在的な entity を発見し (Phase B: Latent Discovery)、既存の cohort/actor と照合して同定していく (Phase A: Entity Resolution) CLI コマンド `etzhayyim coverage infer` を設計・実装する。

統計計算は **RisingWave Python UDF** (Arrow Flight protocol) で実行する。

# Scope

- **In**: CLI サブコマンド群、RisingWave Python UDF server、migration (tables + MV)、CSV/JSONL 入力
- **Out**: PDS magatama.jsonld derive rule の変更、frontend UI、Murakumo LLM judge 統合 (後続 iteration)

# Architecture

## Data Flow (B→A Sequential)

```
Input (CSV/JSONL)
  │
  ├─ Phase B: Latent Discovery ──────────────────────────┐
  │  etzhayyim coverage infer discover --input data.csv       │
  │    1. Go CLI: CSV parse → bulk INSERT                │
  │       → vertex_infer_input (features DOUBLE[])       │
  │    2. SQL: SELECT gmm_fit(features, k)               │
  │       → Python UDF server (Arrow Flight :8815)       │
  │    3. Results → vertex_infer_cluster INSERT           │
  │    4. k ≥ 50 validation per cluster                  │
  └──────────────────────────────────────────────────────┘
  │
  ├─ Phase A: Entity Resolution ─────────────────────────┐
  │  etzhayyim coverage infer match --threshold 0.7           │
  │    1. SELECT vertex_infer_cluster + vertex_cohort_actor│
  │    2. cosine_similarity() UDF for feature matching    │
  │    3. posterior_update() UDF for Bayesian update      │
  │    4. Evidence write → com.etzhayyim.cohort.evidence       │
  │       (Tier 1 hashed)                                │
  │    5. mv_cohort_identity_posterior auto-refresh       │
  └──────────────────────────────────────────────────────┘
  │
  └─ Phase C: Fission (auto) ───────────────────────────┐
     posterior > 0.95 && judge_agreement                 │
     → PDS magatama.jsonld derive rule                   │
     → etzhayyim cohort fission (existing)                    │
  └──────────────────────────────────────────────────────┘
```

## CLI Subcommands

| Subcommand | 動作 | Read/Write |
|---|---|---|
| `etzhayyim coverage infer` | サマリー (全 cohort の posterior + evidence + k 一覧) | Read |
| `etzhayyim coverage infer list` | 詳細テーブル (--grade, --locale, --apqc, --json) | Read |
| `etzhayyim coverage infer inspect --did X` | 特定 cohort の evidence 分布 + signal_kind 内訳 | Read |
| `etzhayyim coverage infer posterior` | mv_cohort_identity_posterior の streaming 状態 | Read |
| `etzhayyim coverage infer kdrift` | mv_cohort_k_drift の k-anonymity ドリフト検出 | Read |
| `etzhayyim coverage infer discover` | 統計データ → latent cluster 発見 (RisingWave UDF) | Write |
| `etzhayyim coverage infer match` | 発見 cluster ↔ 既存 entity マッチング | Write |
| `etzhayyim coverage infer fission --dry-run` | fission 候補一覧 + 実行 | Write |

## RisingWave Python UDF Server

Arrow Flight protocol で RisingWave と通信する外部 Python UDF server。

**Location**: `30-graph/risingwave-udf/`

**Functions**:

| UDF Name | Input | Output | 用途 |
|---|---|---|---|
| `gmm_fit` | `DOUBLE[], INT` | `JSONB` | Gaussian Mixture Model cluster assignment |
| `cosine_similarity` | `DOUBLE[], DOUBLE[]` | `DOUBLE` | Feature vector 類似度 |
| `posterior_update` | `DOUBLE, DOUBLE` | `DOUBLE` | Bayesian posterior update |
| `segment_hash` | `JSONB` | `VARCHAR` | Demographic vector hash for k-anonymity |

**Deploy**: Dockerfile → Linode LKE (alongside RisingWave cluster)。Port 8815。

## Tables & MVs (new)

| Object | Type | Purpose |
|---|---|---|
| `vertex_infer_input` | Table | 入力統計データの feature vector 格納 |
| `vertex_infer_cluster` | Table | 発見された latent cluster の centroid + metadata |
| `vertex_infer_match` | Table | cluster ↔ cohort のマッチ結果 |
| `mv_infer_cluster_summary` | MV | cluster 別 evidence count + avg posterior |

## Pre-flight Checks (graph-schema CLAUDE.md §MV Memory Safety Guardrails)

| 項目 | 見積 | 判定 |
|---|---|---|
| `GROUP BY cluster_id` cardinality | 初期 0、スケール後 ~1k | OK < 500k |
| MV backfill row count | 0 (writes start after discover) | OK |
| MAX(varchar) 列数 | 0 (数値 aggregate のみ) | OK |

# Deploy

## UDF Server (Linode LKE)

UDF server は `risingwave` namespace に Deployment + ClusterIP Service としてデプロイ。
RisingWave から `risingwave-python-udf.risingwave.svc:8815` でアクセス可能。

```bash
# 1. Build + push + apply (all-in-one)
cd 30-graph/risingwave-udf
./deploy.sh

# Or step-by-step:
./deploy.sh build     # docker build
./deploy.sh push      # ghcr.io/etzhayyim/risingwave-python-udf:latest
./deploy.sh apply     # kubectl apply + rollout wait
```

**K8s manifest**: `50-infra/linode/risingwave-iceberg/kustomize/base/python-udf.yaml`

| Resource | Value |
|---|---|
| Image | `ghcr.io/etzhayyim/risingwave-python-udf:latest` |
| Namespace | `risingwave` |
| Port | 8815 (Arrow Flight) |
| Node selector | `rw-role: compute` (co-locate with RisingWave) |
| CPU | 250m request / 2 limit |
| Memory | 512Mi request / 2Gi limit |
| Service DNS | `risingwave-python-udf.risingwave.svc:8815` |

## UDF Registration (after deploy)

```bash
# Apply migration (registers CREATE FUNCTION pointing to UDF server)
cd 30-graph/graph-schema
DATABASE_URL=postgres://root@<rw-host>:4566/dev pnpm db:migrate
```

Or manually:

```sql
CREATE FUNCTION cosine_similarity(DOUBLE PRECISION[], DOUBLE PRECISION[])
  RETURNS DOUBLE PRECISION LANGUAGE python AS cosine_similarity
  USING LINK 'risingwave-python-udf.risingwave.svc:8815';

CREATE FUNCTION posterior_update(DOUBLE PRECISION, DOUBLE PRECISION)
  RETURNS DOUBLE PRECISION LANGUAGE python AS posterior_update
  USING LINK 'risingwave-python-udf.risingwave.svc:8815';

CREATE FUNCTION segment_hash(JSONB)
  RETURNS VARCHAR LANGUAGE python AS segment_hash
  USING LINK 'risingwave-python-udf.risingwave.svc:8815';

CREATE FUNCTION gmm_fit(DOUBLE PRECISION[], INT)
  RETURNS JSONB LANGUAGE python AS gmm_fit
  USING LINK 'risingwave-python-udf.risingwave.svc:8815';
```

## Verification

```bash
# 1. UDF server running
kubectl get pods -n risingwave -l app=risingwave-python-udf

# 2. UDF callable
psql -h <rw-host> -p 4566 -U root -d dev -c \
  "SELECT cosine_similarity(ARRAY[1.0, 0.0], ARRAY[0.0, 1.0]);"
# Expected: 0.0

# 3. CLI read-only
etzhayyim coverage infer
etzhayyim coverage infer posterior
etzhayyim coverage infer kdrift
```

# Implementation Plan

1. RisingWave UDF server (`30-graph/risingwave-udf/`) -- DONE
2. K8s manifest (`50-infra/.../kustomize/base/python-udf.yaml`) -- DONE
3. Deploy script (`30-graph/risingwave-udf/deploy.sh`) -- DONE
4. Migrations (`20260416120000_infer_tables.ts`, `20260416120100_infer_udf_functions.ts`) -- DONE
5. Go CLI `coverage_infer.go` — all subcommands -- DONE
6. main.go routing -- DONE

# References

- `30-graph/graph-schema/CLAUDE.md` §MV Memory Safety Guardrails
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
- `90-docs/260414-cohort-identity-posterior-mv-draft.md`
- `70-tools/etzhayyim/etzhayyim/coverage_actors.go` (pattern reference)
