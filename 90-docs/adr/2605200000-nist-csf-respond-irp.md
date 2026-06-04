---
id: adr-2605200000-nist-csf-respond-irp
title: "NIST CSF 2.0 RESPOND — Formal Incident Response Plan Adoption"
status: active
doc_type: adr
topic: security-incident-response
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - incident severity taxonomy (P0–P3)
  - incident commander rotation policy
  - escalation matrix (paging thresholds)
  - stakeholder communication protocol
  - post-incident review cadence
priority: 8.0
axis: security
weight: 0.80
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2604261100-rego-dmn-policy-decision-layers
related:
  - adr-0018-pii-tier3-cohort-first
  - adr-0048-risingwave-vultr-b2-primary
  - adr-0095-simplified-3layer-identity-rw-vault
supersedes: []
superseded_by: []
---

# NIST CSF 2.0 RESPOND — Formal Incident Response Plan Adoption

## Context

分析 (2026-05-20) で NIST CSF 2.0 の PROTECT まで堅固だが、
**DETECT・RESPOND・RECOVER の右側 3 function が実装の空白地帯**と判明。

本 ADR は RESPOND function の中核決定である
**「正式な Incident Response Plan (IRP) を採択する」** を記録する。

IRP の詳細手順書は `90-docs/irp/` に別途置く。
本 ADR はその採択決定と設計原則のみを定める (1 ADR = 1 decision)。

## Decision

### 1. Severity Taxonomy

| Level | 名称 | 定義 | 例 |
|---|---|---|---|
| **P0** | Critical | データ平面完全停止 / PII 漏洩確定 / RisingWave データ損失 | vault 鍵素材漏洩、RW クラスタ全落ち |
| **P1** | High | 主要機能停止 (read-only 縮退含む) / clearance 認可バイパス疑い | atproto PDS 停止、Rego policy 誤判定 |
| **P2** | Medium | 部分機能劣化 / 潜在的セキュリティ影響 | 特定 actor MCP タイムアウト、B2 SlowDown 頻発 |
| **P3** | Low | 軽微な劣化 / 予防的対応 | 証跡ログ遅延、clearance rejection 急増 (攻撃未遂) |

分類基準:
- **データ損失リスク**: P0 確定
- **clearance level 逸脱**: P0/P1
- **AT Protocol federation 停止**: P1
- **単一 actor/worker 障害**: P2/P3

### 2. Incident Commander (IC) 制度

IC は **etzhayyim 運営主体の意思決定権者** が担う。
etzhayyim Japan (vendor) は IC になれない (Operating Entity Boundary — CLAUDE.md)。

| ロール | 権限 | P0/P1 時 |
|---|---|---|
| **Incident Commander** | 全対応決定権、外部通知承認 | 即時アクティブ化 |
| **Technical Lead** | 技術調査・修正実行 | IC 指名で確定 |
| **Communications Lead** | ステークホルダー通知 | IC が兼任可 |

**ローテーション**: 週単位 on-call。`deps.toml [etzhayyim_agent.oncall]` に当番記録。

### 3. エスカレーション・タイムライン

```
T+0    検知 (Prometheus alert / Slack 通知 / human report)
T+5m   初期トリアージ — severity 分類 + IC アクティブ化
T+15m  P0/P1: IC がステータスページ更新 + 社内通知
T+30m  P0/P1: 外部ステークホルダー (prime contractor 等) 通知判断
T+60m  全 severity: 対応状況を Slack #incidents に更新
T+4h   P0/P1: 解決または escalation to etzhayyim board
T+24h  全 severity: post-incident review 開始
T+72h  PIR 完了 + deps.toml [[migrations]] に follow-on items 登録
```

**ページング閾値 (PagerDuty / 電話)**:
- P0: 即時 (24/7)
- P1: 即時 (営業時間外含む)
- P2: 翌営業時間内
- P3: 次回スプリント

### 4. 通信プロトコル

#### 内部通信

| チャネル | 用途 |
|---|---|
| Slack `#incidents` | リアルタイム状況共有 |
| Teams channel (microsoft actor 経由) | 正式記録、エビデンス保存 |
| `etzhayyim projector` MCP | インシデントブロッカー追跡 |

#### 外部通信

- **P0/P1**: IC 承認後のみ。テンプレート: `90-docs/irp/templates/external-comms.md`
- **P2/P3**: 原則非公開。顧客影響がある場合のみ IC 判断で通知
- **禁止**: Slack/Teams の raw incident detail を外部転送。summary only

#### ステータスページ

`status.etzhayyim.com` (将来実装) — 現在は `90-docs/irp/status-log.md` で代替。
P0/P1 では T+15m 以内に更新必須。

### 5. NIST CSF 2.0 RESPOND カテゴリ マッピング

| CSF Category | 本 IRP での対応 |
|---|---|
| RS.MA (Incident Management) | severity taxonomy + IC 制度 (§1-2) |
| RS.AN (Incident Analysis) | T+5m トリアージ + RCA 義務 (§3) |
| RS.CO (Incident Response Reporting) | §4 通信プロトコル |
| RS.MI (Incident Mitigation) | Technical Lead による修正実行 (§2) |
| RS.IM (Improvements) | T+72h PIR + deps.toml 登録 (§3) |

### 6. 証跡・監査

- インシデント記録は `defAudit.logEvent` MCP tool で immutable 追記
  (`classification_level` = インシデント severity に対応)
- P0/P1: on-chain anchoring 自動 (`classification_level >= 2`)
- PIR 文書は `90-docs/irp/YYYYMMDD-<summary>.md` に永続保管
- 既存 postmortem 形式 (`90-docs/260425-vultr-cache-refill-drift-postmortem.md`) を
  標準テンプレートとして採用

### 7. Rego Policy 連携

インシデント中の clearance 緊急昇格は
`00-contracts/policies/etzhayyim/defense/clearance/policy.rego` の
`emergency_override` ルール (別 PR で追加) を通じてのみ実行。
口頭指示のみでの権限変更禁止。

## Consequences

- PIR 義務化により再発防止の追跡可能性が向上
- etzhayyim が IC = vendor に対する指揮権が明確化
- `defAudit.logEvent` を security incident 記録に再利用できる
- NIST CSF 2.0 RESPOND function の RS.MA/RS.AN/RS.CO/RS.MI/RS.IM が網羅される
- DETECT (Prometheus alert rules コミット) と RECOVER (RTO/RPO 定義) は別 ADR で対応

## References

- `90-docs/260425-vultr-cache-refill-drift-postmortem.md` — PIR テンプレート原型
- `00-contracts/policies/etzhayyim/defense/clearance/policy.rego` — clearance 制御 SSoT
- `20-actors/defense/py/src/pydefense/metrics.py` — Prometheus metrics (DETECT 基盤)
- `deps.toml [etzhayyim_agent.oncall]` — on-call ローテーション記録先
- NIST CSF 2.0: https://doi.org/10.6028/NIST.CSWP.29
