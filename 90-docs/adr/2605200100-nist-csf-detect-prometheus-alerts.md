---
id: adr-2605200100-nist-csf-detect-prometheus-alerts
title: "NIST CSF 2.0 DETECT — Prometheus Alert Rules Adoption"
status: active
doc_type: adr
topic: security-monitoring
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - Prometheus alert rule SSoT (PrometheusRule CRDs)
  - RisingWave operational alert thresholds
  - defense cluster security alert thresholds
  - NIST CSF 2.0 DETECT function implementation
priority: 7.5
axis: security
weight: 0.75
depends_on:
  - adr-2605200000-nist-csf-respond-irp
  - adr-0048-risingwave-vultr-b2-primary
  - adr-2605190100-defense-cluster-topology
related:
  - adr-2605200200-nist-csf-recover-rto-rpo   # 将来 ADR
supersedes: []
superseded_by: []
---

# NIST CSF 2.0 DETECT — Prometheus Alert Rules Adoption

## Context

分析 (2026-05-20) で NIST CSF 2.0 DETECT function の実装状況:
- Prometheus metrics は `pydefense/metrics.py` に存在する (clearance rejections, risk score, EVM audit)
- RisingWave のインシデント事後分析 (`260425-postmortem.md §6.4`) でアラートルールが提案されたが **未コミット**
- kube-prometheus-stack は Vultr VKE に導入済み (`helmfile.yaml`, `monitoring` namespace)
- `ruleSelectorNilUsesHelmValues: false` + `ruleNamespaceSelector: matchLabels: {}` → 全 namespace の PrometheusRule を自動収集

本 ADR は「Prometheus PrometheusRule CRD を DETECT の SSoT として採択する」決定を記録する。

## Decision

### PrometheusRule SSoT パス

| ファイル | 対象 | namespace |
|---|---|---|
| `50-infra/vultr/risingwave/alerts/rw-critical.yaml` | RisingWave インフラ | `risingwave` |
| `50-infra/vultr/ops/defense-alerts.yaml` | defense actor セキュリティ | `murakumo-system` |

追加のアラートは対象サービスの `50-infra/vultr/<service>/alerts/` 配下に置く。
グローバルなセキュリティアラートは `50-infra/vultr/ops/` に集約する。

### RisingWave 重要アラート (postmortem §6.4 実装)

| Alert | 閾値 | Severity | 根拠 |
|---|---|---|---|
| `RWB2SlowDownCritical` | `rate(opendal_s3_http_status_total{status="503"}[1m]) > 0.5` | critical | postmortem §6.4 — 11:06 に発火すれば 7 分早期検知 |
| `RWB2SlowDownWarning` | `> 0.1` | warning | 早期警戒 |
| `RWComputePodRestarting` | restarts > 2 | critical | OOM / Hummock recovery 検知 |
| `RWComputeMemoryHigh` | > 85% | warning | OOM 予防 |
| `RWFoyerColdStart` | pod age < 1800s AND SlowDown > 0.05 | critical | 2026-04-25 再発防止パターン |
| `RWBulkIngestUncapped` | rows/s > 2000 for 3m | warning | `rw-bulk-insert-throttle` convention 検知 |
| `RWMetaServiceDown` | meta pod up == 0 | critical | DDL + checkpoint 全停止 |

### Defense セキュリティアラート

| Alert | 閾値 | NIST CSF | Severity |
|---|---|---|---|
| `DefenseClearanceRejectionBurst` | rejections/s > 0.5 for 2m | DE.AE | critical |
| `DefenseClearanceRejectionElevated` | > 0.1 for 5m | DE.AE | warning |
| `DefenseHighRiskSupplierDetected` | P95 risk_score > 75 | ID.SC | warning |
| `DefenseCriticalRiskSupplier` | P99 risk_score > 90 | ID.SC | critical |
| `DefenseAuditChainErrors` | on-chain error rate > 0 | DE.CM | warning |
| `DefenseMCPDown` | up == 0 for 2m | — | critical |

### NIST CSF 2.0 DETECT カテゴリ マッピング

| CSF Category | 実装 |
|---|---|
| DE.AE (Anomalies & Events) | clearance rejection burst アラート |
| DE.CM (Continuous Monitoring) | RisingWave health + EVM audit chain monitoring |
| DE.AE-4 (Impact) | supply chain risk score histogram |

### pydefense ServiceMonitor

defense-langgraph-server の `/metrics` エンドポイントを Prometheus が scrape するため
`50-infra/vultr/ops/defense-service-monitor.yaml` を別途追加 (同 PR)。

### アラート routing (Alertmanager)

P0/P1 severity=critical → PagerDuty (IC へ即時)
P2 severity=warning → Slack `#alerts-infra` / `#alerts-security`

Alertmanager routing config は `helmfile.yaml` の `alertmanager:` セクションに追記する。
現時点では Slack webhook URL を macOS Keychain `etzhayyim.slack/ALERT_WEBHOOK_URL` から取得する。

## Consequences

- postmortem §6.4 の観測ギャップが閉じる
- NIST CSF 2.0 DETECT function の DE.AE / DE.CM が実装される
- defense clearance 異常が P1 IRP (ADR-2605200000) を自動トリガー可能になる
- 追加メトリクス (SIEM 統合、ML 異常検知) は別 ADR で対応

## References

- `90-docs/260425-vultr-cache-refill-drift-postmortem.md §6.4`
- `20-actors/defense/py/src/pydefense/metrics.py`
- `50-infra/vultr/helmfile.yaml` (`kube-prometheus-stack`)
- `50-infra/vultr/risingwave/alerts/rw-critical.yaml`
- `50-infra/vultr/ops/defense-alerts.yaml`
