# etzhayyim-project-yabai 設計

Date: 2026-03-03
Scope: 反社会性勢力、AML、メールアドレス、法人、ウェブサイト、個人名の分析と公開を行う基盤設計。

## 1. 目的

- 社会的に有害な行為主体と関連シグナルを継続収集し、`well-becoming` を基準にリスクを定量化する。
- 制裁対象、違法行為、反社会活動、犯罪行為をペナルティとして評価し、説明可能なスコアとして公開する。
- 誤判定を抑えるため、根拠・信頼度・更新履歴・異議申し立てフローを組み込む。

## 2. 対象エンティティ

- `Person` (個人名、別名、SNS/連絡先)
- `Organization` (法人、団体、関連会社)
- `WebSite` / `WebPage` (ドメイン、URL、決済導線)
- `ContactPoint` (メールアドレス、電話番号、ウォレット)

エンティティは `canonical_id` と複数の `alias` を持ち、同一性は証拠リンクで管理する。

## 3. データ入力

- 規制・制裁リスト: sanctions/PEP/監督当局公開データ
- 公知情報: 判決、官報、報道、警告リスト
- 技術シグナル: ドメイン登録情報、メール/サイトのレピュテーション
- 運用入力: 内部通報、審査結果、手動レビュー

各入力は `source_reliability` (A-D) と `jurisdiction` を必須化する。

## 4. パイプライン

1. Ingest: ソース取得、署名・取得日時記録
2. Normalize: JSON-LD正規化 (`Person/Organization/WebSite/ContactPoint`)
3. Resolve: 同一性解決 (name/email/domain/company graph)
4. Enrich: 関係グラフ生成 (所有、取引、連絡、共起)
5. Score: well-becoming軸 + penalty軸でスコア算出
6. Publish: 公開APIとスナップショットを配信
7. Review: 異議申立、再評価、監査ログ保存

## 5. スコア設計

### 5.1 基本スコア

- `WellBecomingScore` (0-100, 高いほど健全)
- `PenaltyScore` (0-100, 高いほど有害)
- `YabaiRiskScore` (0-100, 高いほど要警戒)

算出例:

`YabaiRiskScore = clip(100 - WellBecomingScore + PenaltyScore * 0.8, 0, 100)`

### 5.2 Well-Becoming 評価軸 (正方向)

- 社会的信頼維持: 透明性、説明責任、改善履歴
- 法令遵守成熟度: KYC/AML体制、監査対応、再発防止
- 被害低減行動: 是正措置、返金/補償、協力姿勢

### 5.3 Penalty 評価軸 (負方向)

- `SanctionHit`: 制裁対象一致
- `CriminalEvidence`: 犯罪・違法行為の確度
- `AntiSocialAssociation`: 反社会勢力との関係性
- `AMLPattern`: マネロン/資金洗浄の疑義パターン
- `FraudSignal`: 詐欺・なりすまし・偽装サイト等

各軸は `severity(1-5) * confidence(0-1) * recency_decay` で寄与度を計算。

## 6. シャノン的評価軸 (情報理論)

目的: 単純件数ではなく、「どれだけ情報的に異常/有意か」を反映する。

- 事象 `e` の情報量: `I(e) = -log2(P(e))`
- 稀で重大な事象 (例: 制裁一致) は高い情報量を持つ。
- 総合情報リスク:
  - `InfoRisk = Σ (I(e) * confidence * severity_weight)`
- 情報エントロピー:
  - 低エントロピー (同種ノイズのみ) は過剰反応を抑制
  - 高情報量かつ多様な独立ソース一致は強い警戒に反映

`WellBecomingScore` 側は、再発防止や透明化による「不確実性低減」を正方向に評価し、
`PenaltyScore` 側は有害事象の情報量増加を負方向に評価する。

## 7. 公開モデル

- 公開レベル:
  - `Public`: スコア、根拠カテゴリ、更新日、異議窓口
  - `Partner`: 詳細根拠、関係グラフ要約
  - `Internal`: 生データ、調査ノート、非公開情報
- API:
  - `GET /xrpc/yabai.v1.EntityRisk/Get`
  - `GET /xrpc/yabai.v1.EntityRisk/Search`
  - `POST /xrpc/yabai.v1.Appeal/Submit`

## 8. データモデル(最小)

- `Entity`
  - `entity_id`, `type`, `canonical_name`, `aliases[]`, `contacts[]`, `websites[]`
- `Evidence`
  - `evidence_id`, `entity_id`, `category`, `source`, `source_reliability`, `occurred_at`, `confidence`, `jurisdiction`
- `RiskScore`
  - `entity_id`, `well_becoming_score`, `penalty_score`, `yabai_risk_score`, `info_risk`, `scored_at`
- `Disclosure`
  - `entity_id`, `public_summary`, `appeal_url`, `last_reviewed_at`

## 9. ガバナンス

- 説明可能性: 公開スコアには必ず根拠カテゴリと更新日時を付与
- 最小化: 個人情報は公開最小限、必要時マスキング
- 再評価: 新証拠、時間経過、異議でスコアを自動再計算
- 監査: 変更履歴・承認者・差分理由を永続保存

## 10. 実装フェーズ

1. `Phase 1`: Ingest/Normalize + entity graph
2. `Phase 2`: PenaltyScore + Shannon InfoRisk 実装
3. `Phase 3`: WellBecomingScore 実装と説明可能性UI
4. `Phase 4`: 公開API、異議申立、運用SLO

## 11. 成果指標 (KPI)

- 高リスク検知の適合率/再現率
- 誤検知率 (False Positive Rate)
- 再評価リードタイム
- 異議申立に対する訂正率と応答時間
- 公開根拠付き判定率 (Explainability Coverage)
