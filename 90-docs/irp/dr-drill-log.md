---
id: dr-drill-log
title: "DR Drill Log — Kotoba/Datomic Meta Snapshot Restore"
status: active
doc_type: reference
topic: disaster-recovery
authoritative: true
last_verified: 2026-05-20
---

# DR Drill Log

記録形式: `dr-restore-drill.sh` の実行結果を追記する。
四半期 full drill は手動で実施し IC が署名する。

## 合格基準

| 種別 | 頻度 | 基準 |
|---|---|---|
| Dry-run | 毎月 (CronJob 自動) | snapshot 可読 + exit 0 |
| Full restore | 四半期 (手動) | catalog table 数 ≥ 前回実績 |

## 実施記録

| 日時 (UTC) | Snapshot ID | Catalog Tables | 種別 | 結果 |
|---|---|---|---|---|
| 2026-04-15T00:00:00Z | 3 | 1211 | --full | PASS (Linode 環境, baseline) |

<!-- dr-restore-drill.sh --full が自動追記する -->
