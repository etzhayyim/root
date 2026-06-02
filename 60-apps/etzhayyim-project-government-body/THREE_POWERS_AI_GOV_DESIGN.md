# etzhayyim-project-government-body: AI三権分立（Legislative / Executive / Judicial）設計

## 1. 設計の前提（PROJECT / STRATEGY / COFOG / Capabilities）

本設計は、`etzhayyim-project-government-body` の以下方針を前提とする。

- 国家運営基盤は Kubernetes + legacy runtime + Blockchain（Ethereum L2）で構成される。
- 政府機能は COFOG 分類に基づく AI performer 群として実装される。
- 統治は DID/VC による市民性確認とオンチェーン投票・スマートコントラクト執行を中核とする。
- COFOG 01（行政・立法）、COFOG 03（司法）を中核に三権分立を構成する。

---

## 2. 三権の組織モデル

### 2.1 立法（Legislative Branch）

**目的**: ルール（法律・予算・制度）を制定/改廃する。

- 主体: `Legislative Assembly AI`（議案審査 AI + 市民投票ハンドラ）
- 主機能:
  - 議案受付（行政提案・市民提案）
  - 憲法適合性の一次チェック
  - DID 認証された住民投票
  - 可決時の `Law Contract` 発効
- 主な能力マッピング:
  - `act-legislative-proposal-vote`
  - `act-constitution-amendment-vote`
  - COFOG `01.1.1`

### 2.2 行政（Executive Branch）

**目的**: 可決済み法令と予算に基づき政策執行を行う。

- 主体: `Executive Council AI`（各省 performer オーケストレータ）
- 主機能:
  - 政策立案（ドラフト）
  - 省庁 performer への執行命令
  - 予算執行・徴税・給付の自動実行
  - KPI/監査ログの公開
- 主な能力マッピング:
  - `act-executive-policy-generation`
  - `act-treasury-gcc-management`
  - `act-tax-collection-automation`
  - COFOG `01.*` 全般（財政/外務/一般サービス含む）

### 2.3 司法（Judicial Branch）

**目的**: 紛争解決・違憲/違法審査・権利救済。

- 主体: `Judicial Panel AI`（審理 AI + 上訴審 AI + 判例ナレッジ）
- 主機能:
  - スマートコントラクト紛争の裁定
  - 行政処分に対する審査
  - 法令/政策の違憲審査
  - 判例蓄積と再利用
- 主な能力マッピング:
  - `act-smart-contract-dispute-resolution`
  - `cap-gov-0330`（Judicial Services）
  - COFOG `03.3`（Law courts）

---

## 3. チェック・アンド・バランス（相互抑制）

### 3.1 立法 → 行政
- 予算上限、執行期限、目的外利用禁止を `Appropriation Contract` として拘束。
- 行政命令は法令 ID と予算 ID を必須参照。

### 3.2 行政 → 立法
- 緊急命令（期限付き）を提案可能。ただし失効期限後は立法追認が必須。
- 実績データ（税収・失業率・健康指標）を定期提出し、法改正材料を提供。

### 3.3 司法 → 立法・行政
- 司法は違憲判決で法令の執行停止フラグを立てられる。
- 行政処分（アカウント制限・罰則）に対し、是正命令/取消命令を出せる。

### 3.4 立法・行政 → 司法
- 立法は裁判手続法（期限、証拠基準）を定義可能。
- 行政は判決執行を担当するが、判決本文改変は禁止（ハッシュ固定）。

---

## 4. 主要コンポーネント設計（既存資産との接続）

### 4.1 gov-mcp-component（政策・法令・裁定オーケストレーション）
- 追加責務:
  - `submit_bill`, `run_vote`, `enact_law`
  - `issue_executive_order`, `execute_policy`
  - `file_case`, `render_judgement`, `file_appeal`

### 4.2 gov-ui-mcp-component（市民・議会・裁判UI）
- 追加画面:
  - 議案一覧/投票画面
  - 政策執行ダッシュボード
  - 裁判進行・判決閲覧・上訴申立フォーム

### 4.3 gov-planning-mcp-component（制度設計と資源制約）
- 追加責務:
  - 立法案件の実行可能性評価（予算・人員・計算資源）
  - 行政執行計画と司法負荷予測

### 4.4 gov-chain（スマートコントラクト層）
- `ConstitutionContract`: 権限境界、改憲手順、非常時条項。
- `LegislationContract`: 法令版管理、発効/失効、条文ハッシュ。
- `ExecutionContract`: 行政命令の追跡、執行証跡、予算消化。
- `JudiciaryContract`: 訴訟受付、証拠ハッシュ、判決・上訴管理。

---

## 5. 権限モデル（RBAC + DID/VC）

- `CitizenDID`: 投票、提訴、情報開示請求。
- `LegislativeAgent`: 議案審査、投票集計、法令発効。
- `ExecutiveAgent`: 執行命令、予算実行、行政処分。
- `JudicialAgent`: 裁定、差止、是正命令。
- `AuditorAgent`（独立）: 全ログ検証、改ざん検出、透明性レポート。

**原則**: 同一 agent key による複数権限兼務を禁止（三権分立破壊の防止）。

---

## 6. 標準フロー（例）

1. 行政 AI が政策案を起案（法令案 + 予算要求）。
2. 立法 AI が形式審査後、市民投票を実施。
3. 可決後、`LegislationContract` に法令を登録し発効。
4. 行政 AI が `ExecutionContract` 経由で各 COFOG performer に執行命令。
5. 紛争発生時、司法 AI が証拠・法令を参照して裁定。
6. 上訴があれば上訴審 AI に移送、確定判決をチェーンに固定。
7. 監査 AI が全過程を検証し transparency report を公開。

---

## 7. 監査・安全設計

- すべての決定イベントに `decision_id`, `authority_branch`, `legal_basis`, `evidence_hash` を付与。
- 立法・行政・司法ごとに独立した署名鍵と監査ログストリームを使用。
- 高リスク行政処分は「司法レビュー待ち」状態をサポート。
- 非常時権限は time-lock + 事後立法承認 + 司法レビューを必須化。

---

## 8. 導入ロードマップ（最小実装）

### Phase A（MVP）
- 立法: 議案登録・投票・発効
- 行政: 執行命令・実行記録
- 司法: 紛争登録・一次裁定

### Phase B（実運用）
- 上訴審、違憲審査、予算拘束強化
- 監査自動化、透明性ダッシュボード公開

### Phase C（高度化）
- 判例ベース推論、政策シミュレーション
- cross-jurisdiction API（外部司法/治安機関連携）

---

## 9. 成功指標（KPI）

- 立法: 可決までの中央値時間、投票参加率、違憲判決率。
- 行政: 執行 SLA、予算逸脱率、政策KPI達成率。
- 司法: 裁定時間、上訴率、覆審率、公平性指標（偏り検知）。
- 全体: 三権越境操作の検出件数（理想値 0）、監査完全性（100%）。

---

## 10. 実装上の注意

- AI は提案・審査・裁定を行うが、**法的有効性の最終根拠はオンチェーン手続き**に置く。
- 三権の責務境界をコード（コントラクト）で固定し、運用判断で越境できないようにする。
- 説明可能性のため、各判断に「根拠条文 + 根拠データ + 推論要約」を添付する。
