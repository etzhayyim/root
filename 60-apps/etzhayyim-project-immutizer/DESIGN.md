# etzhayyim-project-immutizer Design

## 1. Goal

`etzhayyim-project-immutizer` に登録されている SaaS / mailing list / vendor account に対して、
以下を一元実行する Kotodama app を設計する。

- 配信停止 (`unsubscribe`)
- 契約解約 (`cancel`)
- コンプライアンスに基づく情報削除依頼 (`erasure-request`)

既存のアンチウイルス用途 `etzhayyim-wasm-immutizer-i8m2t9zr` は維持し、本機能は別 component として追加する。

## 2. Proposed Component

- component folder
  - `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/`
- app role
  - vendor offboarding orchestrator
- public interaction
  - Matrix protocol only
- deployment hostname
  - operator UI: `immutizer.etzhayyim.com`
  - direct app endpoint: `https://<nanoid>.etzhayyim.com`

## 3. Scope

この app は「削除そのもの」を直接保証するのではなく、以下を保証対象にする。

- 対象サービスの特定
- 依頼根拠と法域の判定
- 実行経路の選択
- 実行証跡の保存
- 再試行と期限管理
- 未完了案件のエスカレーション

## 4. Component Split

- `immutizer-retirement-ui`
  - Svelte + static delivery
  - 管理対象、案件、証跡、期限、失敗理由の確認
- `immutizer-retirement-orchestrator`
  - Matrix event consumer
  - case lifecycle 管理
  - provider dispatch
- `immutizer-retirement-policy`
  - 法域別 policy evaluation
  - 削除理由テンプレート選択
  - SLA / legal deadline 算出
- `immutizer-retirement-executor`
  - 実行アダプタ
  - API 解約、メール送信、ブラウザ自動化、手動タスク生成
- `immutizer-retirement-evidence`
  - cypher graph/cypher graph projection
  - 原文、レスポンス、タイムライン、添付証跡の保存

初期実装では 1 Kotodama app 内の内部 module として開始し、負荷や責務分離が必要になった時点で component 分割する。

## 5. Domain Model

### `service_accounts`

- `service_account_id`
- `org_id`
- `user_id`
- `actor_id`
- `service_name`
- `service_category`
- `account_identifier`
- `contact_email`
- `contract_owner`
- `legal_entity_name`
- `jurisdiction`
- `status`
- `retention_policy_ref`
- `created_at`
- `updated_at`

### `retirement_cases`

- `case_id`
- `org_id`
- `user_id`
- `actor_id`
- `service_account_id`
- `request_type`
- `legal_basis`
- `priority`
- `status`
- `due_at`
- `requested_at`
- `completed_at`
- `last_error`

### `retirement_actions`

- `action_id`
- `org_id`
- `user_id`
- `actor_id`
- `case_id`
- `channel`
- `provider`
- `attempt`
- `request_payload`
- `response_payload`
- `result`
- `executed_at`

### `retirement_evidence`

- `evidence_id`
- `org_id`
- `user_id`
- `actor_id`
- `case_id`
- `evidence_type`
- `blob_key`
- `sha256`
- `captured_at`

全 table は `org_id`, `user_id`, `actor_id` を必須とし、read path は projection-first で実装する。

## 6. Request Types

- `unsubscribe`
  - newsletter / product update / sales outreach 停止
- `cancel`
  - subscription 解約、seat 停止、billing 終了
- `erasure_request`
  - 個人情報削除依頼、利用停止、匿名化要求
- `combined_retirement`
  - 上記 3 種を一案件で束ねる標準モード

`combined_retirement` を既定値にし、サービスごとに可能な action のみ実行する。

## 7. Execution Channels

- provider API
  - vendor API で unsubscribe / cancel / delete を実行
- transactional email
  - 削除依頼メールを規定テンプレートで送付
- browser automation
  - 公開 API がない SaaS の設定画面を Playwright 系 provider で操作
- human review queue
  - CAPTCHA、法務確認、本人確認が必要な案件を手動化

選定順序は `API > email > browser automation > human review`。

## 8. Matrix Contract

新規 public REST / Connect API は追加しない。以下の Matrix event を正規入口とする。

- `etzhayyim.immutizer.retirement.case.create`
  - service account と request type を投入
- `etzhayyim.immutizer.retirement.case.dispatch`
  - policy 判定後の実行開始
- `etzhayyim.immutizer.retirement.case.retry`
  - 失敗案件の再送
- `etzhayyim.immutizer.retirement.case.complete`
  - 完了通知
- `etzhayyim.immutizer.retirement.case.escalate`
  - 手動対応へ移行

UI は Matrix client として room/thread に参加し、一覧表示は projection table から読む。

## 9. Provider Strategy

優先利用 provider は以下。

- `notify` / `resend`
  - 依頼メール送信
- `playwright` / `yorishiro-*`
  - vendor console 操作
- `provider-vault`
  - SaaS 認証情報、送信元 mailaddress、法務テンプレート secret 管理
- `authn` / `authz`
  - 実行者検証

vendor ごとの adapter は `adapter/<vendor>.go` として分離し、共通 interface は以下に揃える。

- `Plan(case) -> execution_plan`
- `Execute(step) -> action_result`
- `Verify(case) -> verification_result`

## 10. Compliance Policy

法務判断を app に埋め込まず、policy data として外出しする。

- jurisdiction
  - `JP`, `EU`, `US-CA`, `OTHER`
- legal basis examples
  - `consent_withdrawal`
  - `contract_termination`
  - `gdpr_art_17`
  - `ccpa_delete_request`
  - `act_on_specified_commercial_transactions_opt_out`
- output
  - 使用テンプレート
  - 本人確認要否
  - 返信期限
  - 再送回数
  - escalation 先

policy engine は deterministic rule set とし、LLM は文面候補生成の補助までに留める。

## 11. Workflow

1. `service_account` を登録する。
2. app が vendor category と法域を判定する。
3. `combined_retirement` case を生成する。
4. policy engine が required actions を展開する。
5. executor が API / email / browser automation を順次試行する。
6. action ごとに request/response/screenshot/mail copy を証跡化する。
7. verification で unsubscribe / cancel / delete の完了状態を確認する。
8. 未完了なら retry、閾値超過なら human review queue に送る。
9. 全 step 完了で case を `completed` に遷移する。

## 12. UI Requirements

- AppShell v2 / UIKit 必須
- mobile-first
- 一覧は `Inbox`, `In Progress`, `Awaiting Reply`, `Escalated`, `Completed`
- 各 case で以下を表示
  - target service
  - request type
  - legal basis
  - due date
  - latest action result
  - evidence count
- 重要操作
  - `Start`
  - `Retry`
  - `Escalate`
  - `Mark Verified`
  - `Export Dossier`

## 13. Evidence and Storage

- 構造化データ
  - cypher graph/cypher graph
- 添付証跡
  - Nata Blob
- 保存対象
  - 送信メール本文
  - vendor response
  - screenshot
  - PDF / CSV / receipt
  - operator note

`Export Dossier` は案件単位で証跡一式をまとめ、法務・監査提出用に生成する。

## 14. Failure Handling

- `blocked_login`
  - secret 失効 or MFA 要求
- `manual_identity_check`
  - 本人確認が自動処理不能
- `legal_hold`
  - vendor 側が削除不能理由を返却
- `unknown_endpoint`
  - 実行経路不明
- `rate_limited`
  - 後で再試行

失敗理由は正規化 enum で保存し、UI 上はベンダー別 runbook にリンクする。

## 15. Minimal Phase-1 Delivery

Phase 1 は以下に限定する。

- service account registry
- `combined_retirement` case 作成
- email-based request execution
- evidence capture
- retry / deadline dashboard

Phase 2 で以下を追加する。

- SaaS API adapter
- browser automation
- vendor-specific verification
- dossier export

## 16. Proposed Files

- `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/main.go`
- `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/db_schema.go`
- `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/policy.go`
- `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/executor.go`
- `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/svelte/src/routes/+page.svelte`
- `60-apps/etzhayyim-project-immutizer/wasm/etzhayyim-wasm-immutizer-retirement-<nanoid>/<repo-deploy-config>`

## 17. Non-Goals

- vendor deletion 成否の法的最終判断
- 外部 SaaS 全種への初期フル対応
- 個人情報の自動収集拡大
- uncontrolled LLM autonomous action
