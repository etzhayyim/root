---
id: adr-2605200200-nist-csf-recover-rto-rpo
title: "NIST CSF 2.0 RECOVER — RTO/RPO SLAs and DR Drill Cadence"
status: active
doc_type: adr
topic: disaster-recovery
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - Recovery Time Objective (RTO) per system tier
  - Recovery Point Objective (RPO) per system tier
  - DR drill cadence and acceptance criteria
  - backup integrity verification schedule
priority: 7.0
axis: security
weight: 0.70
depends_on:
  - adr-2605200000-nist-csf-respond-irp
  - adr-0048-kotoba-vultr-b2-primary
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
related:
  - adr-2605200100-nist-csf-detect-prometheus-alerts
  - adr-0021-phase4-cutover-runbook
supersedes: []
superseded_by: []
---

# NIST CSF 2.0 RECOVER — RTO/RPO SLAs and DR Drill Cadence

## Context

分析 (2026-05-20) で RECOVER function が最弱であると判明:
- Kotoba/Datomic hourly meta backup CronJob は存在するが RTO/RPO SLA 未定義
- DR drill スクリプトは Linode エンドポイント (`sg-sin-1.linodeobjects.com`) のまま (ADR-0048 以降未更新)
- バックアップ整合性テストの記録が 2026-04-15 (1ヶ月以上前) で停止
- セカンダリリージョンなし (single region: Vultr LAX)

本 ADR は「各システム tier の RTO/RPO を公式 SLA として採択し、
DR drill を定期実施する」決定を記録する。

## Decision

### 1. システム Tier 別 RTO / RPO

| Tier | システム | RTO | RPO | 根拠 |
|---|---|---|---|---|
| **T0-Edge** | CF Workers (edge proxy) | 5 min | 0 (stateless) | CF global PoP 自動 failover |
| **T0-Vault** | Cloudflare D1 (vault) | 15 min | 0 | CF managed replication |
| **T0-PDS** | AT Protocol PDS (K8s pod) | 30 min | 1 h | pod 再スケジュール + record-log replay |
| **T1-LangServer** | LangGraph Server pods | 10 min | 0 | stateless; checkpoint は RW に保存 |
| **T1-RW** | Kotoba/Datomic (domain data) | **2 h** | **1 h** | hourly meta snapshot + Foyer 30 min warm |
| **T1-Defense** | defense-langgraph-server | 30 min | 1 h | pod 再起動 + RW 依存 |
| **T2-AirGap** | (将来 T2) | 4 h | 1 h | on-prem cold-start |

**RTO の起点**: インシデント IC が「復旧開始」を宣言した時点。
**RPO の起点**: 最後の正常 write が確認できた時点。

### 2. Kotoba/Datomic DR 手順 (T1-RW の主シナリオ)

```
Step 1  rw-health-gate.sh で現状確認 (5 min)
Step 2  meta snapshot ID 確認: risectl meta list-meta-snapshots (2 min)
Step 3  meta pod に対して restore-meta --dry-run (5 min)
Step 4  compute/compactor 停止: kubectl scale sts kotoba-compute --replicas=0 (2 min)
Step 5  meta pod restart で catalog 上書き (10 min)
Step 6  compute 再起動: replicas=1 (5 min)
Step 7  Foyer warm-up 待機: pod age >= 1800s (30 min)
Step 8  health gate PASS 確認 + SELECT 1 (2 min)
Step 9  bulk ingest 再開 (SET dml_rate_limit 必須)
合計 RTO = ~60 min (目標 2 h 以内に十分余裕)
```

RPO = 最後の hourly backup 完了時刻。最大損失 = 1 h 分の write。
`vertex_defense_audit_event` の on-chain anchor (classification_level >= 2) は
blockchain に独立して存在するため RW 損失後も検証可能。

### 3. DR Drill 実施計画

| 種別 | 頻度 | 実施方法 | 合格基準 |
|---|---|---|---|
| **Dry-run drill** | 毎月 (CronJob 自動) | `dr-restore-drill.sh --dry-run` | snapshot 可読 + exit 0 |
| **Full restore drill** | 四半期 (手動) | `dr-restore-drill.sh --full` | catalog table 数 ≥ 前回実績 |
| **Failover simulation** | 半年 | 手動 + 段階的 | RTO 目標内に復旧 |

**DR drill の SSoT スクリプト**: `50-infra/vultr/kotoba/dr-restore-drill.sh`
(Linode 版 `50-infra/linode/kotoba-iceberg/helm/dr-restore-drill.sh` から
Vultr/B2 エンドポイントに移植済み)。

### 4. バックアップ整合性 KPI

| メトリクス | 目標 | 検知アラート |
|---|---|---|
| meta backup 成功率 | ≥ 99% (月次) | `RWMetaBackupFailed` PrometheusRule |
| 最新 snapshot 経過時間 | ≤ 2 h | `RWMetaBackupStale` PrometheusRule |
| dry-run drill 合格率 | 100% | CronJob failure → Slack `#alerts-infra` |
| full drill 実施記録 | 四半期ごと | `90-docs/irp/dr-drill-log.md` に記録 |

### 5. NIST CSF 2.0 RECOVER カテゴリ マッピング

| CSF Category | 実装 |
|---|---|
| RC.RP (Recovery Planning) | 本 ADR §2 DR 手順 + §3 drill 計画 |
| RC.IM (Improvements) | drill 結果 → PIR → deps.toml migrations |
| RC.CO (Recovery Communications) | IRP ADR-2605200000 §4 通信プロトコル準拠 |

## Consequences

- RTO 2h / RPO 1h が Kotoba/Datomic の公式 SLA になる
- 毎月の dry-run drill で backup 整合性を継続確認できる
- 四半期の full drill で実際の復旧手順を検証し rot を防ぐ
- セカンダリリージョンは Phase 2 (T1 Sovereign 移行時) に Sakura Cloud で追加予定

## References

- `50-infra/vultr/kotoba/dr-restore-drill.sh` — Vultr/B2 対応 DR drill スクリプト
- `50-infra/vultr/kotoba/rw-meta-backup-cronjob.yaml` — hourly backup CronJob
- `50-infra/vultr/kotoba/alerts/rw-critical.yaml` — backup stale アラート (追加済み)
- `50-infra/linode/kotoba-iceberg/paths/backup-restore.md` — Linode 版 (参考)
- `90-docs/irp/dr-drill-log.md` — drill 実施記録 (初回: 2026-04-15, Linode)
- ADR-0048: Kotoba/Datomic Vultr+B2 primary
