# GD Accountability Framework (v0.1)

## 0. Scope and Assumptions
- GD = Government Domain (行政ドメイン)
- Target: `etzhayyim-project-government-body`
- Goal: 政策・サービス・AI実行の説明責任を、設計時点から運用監査可能にする

## 1. Accountability Principles
1. Traceability by default
   すべての意思決定・自動実行は一意IDで追跡可能にする。
2. Human-over-AI control
   高リスク判断は必ず人間承認を通す。
3. Explainability at decision boundary
   最終判断点で「入力・根拠・責任者・時刻」を説明可能にする。
4. Proportional governance
   リスクに応じて統制強度を変える（低/中/高）。
5. Public accountability
   公開可能情報は市民向けに要約公開する。

## 2. Accountability Model
## 2.1 RACI Layers
- Policy Owner: 政策目的・成功基準の最終責任
- Service Owner: サービス品質・SLO責任
- Data Steward: データ品質・分類・保持責任
- AI Operator: モデル運用・監視責任
- Compliance Officer: 規制適合・監査責任
- Incident Commander: 障害/事故対応責任

## 2.2 Decision Classes
- Class A (Low): 定型通知、低影響自動化
- Class B (Medium): 予算配分提案、優先順位付け
- Class C (High): 権利義務に影響する判断、対外公表

Approval Rules:
- Class A: 自動実行 + 監査ログ必須
- Class B: 担当者承認 1名
- Class C: 2名承認（業務責任者 + コンプライアンス）

## 3. Evidence and Logging Standard
Each decision/event must include:
- `event_id` (ULID)
- `decision_class` (A/B/C)
- `actor_type` (human/ai/system)
- `actor_id`
- `input_refs` (document/data hash)
- `policy_refs` (rule id/version)
- `output_summary`
- `risk_score`
- `approved_by` (for B/C)
- `timestamp_utc`

Storage:
- Operational log: near-real-time (searchable)
- Immutable audit ledger: append-only (tamper-evident hash chain)

## 4. Control Framework
## 4.1 Preventive Controls
- Policy-as-code gate (schema + rule validation)
- Access control by role and environment
- PII/機微情報の分類タグ必須化
- High-risk prompt/action deny-list

## 4.2 Detective Controls
- Drift detection (policy/model/data)
- Anomaly detection (volume, latency, outcome bias)
- Approval bypass detection

## 4.3 Corrective Controls
- Automatic rollback playbook
- Kill switch (service/model/action)
- Incident severity policy (SEV1-3)

## 5. Metrics (KPI/KRI)
KPI:
- `decision_trace_coverage` >= 99%
- `approval_sla_b` <= 4h
- `approval_sla_c` <= 24h
- `public_disclosure_latency` <= 7d

KRI:
- `unapproved_high_risk_actions` = 0
- `audit_log_gap_rate` < 0.1%
- `policy_violation_rate` trend non-increasing

## 6. Governance Cadence
- Daily: operational review (errors, anomalies)
- Weekly: accountability review (KPI/KRI, exceptions)
- Monthly: compliance committee (policy updates, incident retros)
- Quarterly: external audit readiness check

## 7. Incident and Accountability Workflow
1. Detect incident/event
2. Classify severity + decision class
3. Contain (kill switch/rollback)
4. Assign accountable owner
5. Evidence freeze (logs, snapshots, hashes)
6. Root cause analysis
7. Corrective action + policy patch
8. Public/internal postmortem publication

## 8. Implementation Plan (90 days)
Phase 1 (0-30d):
- Event schema確定
- RACI割当
- Decision class tagging導入

Phase 2 (31-60d):
- Approval workflow実装 (B/C)
- Immutable audit ledger連携
- KPI/KRIダッシュボード

Phase 3 (61-90d):
- Incident playbook演習
- External audit dry-run
- Public accountability reportテンプレート運用開始

## 9. Minimum Definition of Done
- 全Class B/Cイベントに承認証跡が存在
- 監査ログ欠損率 < 0.1%
- 重大インシデントの再発防止策がポリシー反映済み
- 市民向け説明文（非機密）が7日以内に公開可能
