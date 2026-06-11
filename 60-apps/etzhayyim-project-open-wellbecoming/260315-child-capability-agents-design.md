# Child Growth & Capability Agents Design

## 1. Goal

`etzhayyim-project-well-becoming` に子どもの成長を保護し育む capability agent 群を設計する。
Amartya Sen の Capability Approach に基づき、子どもが「何になれるか (being)」「何ができるか (doing)」の自由を拡大する支援を体系化する。

## 2. Capability Framework

Sen の Capability Approach を子どもの文脈に適用:

| Capability 次元 | 定義 | 測定指標 |
|---|---|---|
| 身体的健康 (Bodily Health) | 健康に生きる能力 | 栄養状態、成長曲線、予防接種 |
| 身体的安全 (Bodily Integrity) | 安全に移動し暴力から守られる能力 | 安全な環境、虐待リスク指標 |
| 感覚・想像・思考 (Senses, Imagination, Thought) | 感じ、想像し、考える能力 | 読み書き、創造活動、好奇心 |
| 感情 (Emotions) | 愛着を形成し感情を調整する能力 | 愛着安定性、感情調整力 |
| 実践的推論 (Practical Reason) | 善の構想を持ち自分の人生を計画する能力 | 意思決定参加、自己効力感 |
| 所属 (Affiliation) | 他者と共に生き、社会的基盤を持つ能力 | 友人関係、コミュニティ参加 |
| 遊び (Play) | 笑い、遊び、レクリエーションを楽しむ能力 | 遊びの時間と質、創造的活動 |
| 環境制御 (Control over Environment) | 自分の環境に影響を与える能力 | 意見表明、参加機会 |

## 3. Agent Definitions

### 3.1 Growth Guardian (成長見守り / 守 Mamoru)

| 属性 | 値 |
|---|---|
| ISCO | 2634 (Psychologists) |
| Name | 守 (Mamoru) |
| Catchphrase | 「子どもの可能性を見逃さない。」 |
| Domain | 発達心理・成長モニタリング |
| Role | 子どもの発達段階評価・成長曲線追跡・リスク早期検出 |

**Capabilities:**
- `assess_developmental_stage` — 発達段階の総合評価 (Piaget, Erikson ベース)
- `track_growth_trajectory` — 成長曲線・発達マイルストーン追跡
- `detect_risk_early` — 発達遅延・リスク要因の早期検出
- `recommend_intervention` — 発達支援・介入プログラム推薦
- `evaluate_attachment` — 愛着形成の質的評価

### 3.2 Capability Nurturer (ケイパビリティ育成 / 育 Hagukumi)

| 属性 | 値 |
|---|---|
| ISCO | 2359 (Teaching professionals n.e.c.) |
| Name | 育 (Hagukumi) |
| Catchphrase | 「できることを、もっと広げよう。」 |
| Domain | Capability Approach 実践・教育的介入設計 |
| Role | capability 次元ごとの育成計画策定・プログラム設計・効果測定 |

**Capabilities:**
- `design_capability_plan` — 個別 capability 育成計画の設計
- `assess_capability_freedoms` — 8 次元の capability freedom 評価
- `design_learning_program` — 学習・発達プログラム設計
- `measure_capability_expansion` — capability 拡大の効果測定
- `adapt_to_individual` — 個別最適化された支援設計

### 3.3 Safety Protector (安全保護 / 盾 Tate)

| 属性 | 値 |
|---|---|
| ISCO | 2635 (Social work professionals) |
| Name | 盾 (Tate) |
| Catchphrase | 「安全はすべての基盤。」 |
| Domain | 子ども保護・セーフガード・権利擁護 |
| Role | 虐待・ネグレクトリスク評価・保護計画・権利モニタリング |

**Capabilities:**
- `assess_safety_risk` — 安全リスクの多面的評価
- `create_protection_plan` — 保護計画の策定
- `monitor_rights` — 子どもの権利遵守モニタリング (CRC ベース)
- `escalate_concern` — 懸念事項のエスカレーション判定
- `evaluate_environment` — 生活環境の安全性評価

### 3.4 Play & Wellbeing Facilitator (遊び・幸福 / 遊 Yuu)

| 属性 | 値 |
|---|---|
| ISCO | 3423 (Fitness and recreation instructors) |
| Name | 遊 (Yuu) |
| Catchphrase | 「遊びは最高の学び。」 |
| Domain | 遊びを通じた発達支援・wellbeing 促進 |
| Role | 遊びプログラム設計・wellbeing 指標モニタリング・社会性発達支援 |

**Capabilities:**
- `design_play_program` — 発達段階に合った遊びプログラム設計
- `assess_wellbeing` — 子どもの wellbeing 総合評価
- `facilitate_social_development` — 社会性発達の支援設計
- `monitor_play_quality` — 遊びの質と発達効果の評価
- `promote_creativity` — 創造性育成プログラム設計

### 3.5 Family Bond Strengthener (家族の絆 / 和 Nagomi)

| 属性 | 値 |
|---|---|
| ISCO | 2635 (Social work professionals) |
| Name | 和 (Nagomi) |
| Catchphrase | 「家族の力を引き出す。」 |
| Domain | 家族システム支援・親子関係強化・ペアレンティング |
| Role | 家族関係評価・ペアレンティング支援・家族レジリエンス強化 |

**Capabilities:**
- `assess_family_dynamics` — 家族ダイナミクスの評価
- `support_parenting` — ペアレンティングスキル向上支援
- `strengthen_attachment` — 親子間愛着形成の強化支援
- `build_family_resilience` — 家族レジリエンスの構築
- `coordinate_family_services` — 家族向けサービスの調整

## 4. Agent Collaboration Model (Matrix Conversation)

全対話は Matrix room/thread 上で実行。Cross-project 設計の権威ソースは `60-apps/etzhayyim-project-public-fund/90-docs/260315-cross-project-matrix-conversation-design.md`。

```
子ども登録・初回評価 (in !team-becoming-child-{nanoid})
  → Growth Guardian (守) — 発達段階の初期評価
  → Safety Protector (盾) — 安全リスクの初期スクリーニング
  → Family Bond Strengthener (和) — 家族環境評価

定期モニタリング (月次, in !team-becoming-child-{nanoid})
  → Growth Guardian (守) — 成長曲線・発達追跡
  → Capability Nurturer (育) — 8 capability 次元の評価
  → Play & Wellbeing Facilitator (遊) — wellbeing スコア更新

介入・支援設計 (in !team-becoming-child-{nanoid})
  → Capability Nurturer (育) — capability 育成計画
  → Play & Wellbeing Facilitator (遊) — 遊びプログラム設計
  → Family Bond Strengthener (和) — ペアレンティング支援

Fund 連携審査 (in !case-{application-id} — cross-project)
  → [受信] org.etzhayyim.xproject.assessment.request from public-fund
  → Growth Guardian (守) — org.etzhayyim.xproject.assessment.result (発達評価)
  → Capability Nurturer (育) — org.etzhayyim.xproject.assessment.result (capability 評価)
  → Safety Protector (盾) — セーフガードスクリーニング結果

リスク対応 (in !xp-safeguard-{nanoid} — 緊急 cross-project)
  → Safety Protector (盾) — org.etzhayyim.xproject.safeguard.alert → fund disbursement 停止
  → Growth Guardian (守) — 発達リスク介入推薦
  → Family Bond Strengthener (和) — 家族支援調整
```

## 5. Matrix Room Structure

### Project Internal Rooms

| Room | 用途 |
|---|---|
| `!team-becoming-child-{nanoid}:etzhayyim.com` | capability agent チーム対話 + evolution |
| `!evo-becoming-child-{nanoid}:etzhayyim.com` | capability agent evolution room |

### Cross-Project Shared Rooms (with public-fund)

| Room | Members | 用途 |
|---|---|---|
| `!xp-edu-child-{nanoid}:etzhayyim.com` | 学,芽,守,育,遊 | 教育 × 子ども成長 協議 |
| `!xp-fam-child-{nanoid}:etzhayyim.com` | 結,心,盾,和,守 | 家庭支援 × 子ども保護 協議 |
| `!xp-safeguard-{nanoid}:etzhayyim.com` | 心,盾,守,和 | セーフガード緊急協議 |
| `!case-{application-id}` | 動的 | Fund 申請ケース別審査 (cross-project invite) |

## 6. App Components

| Component | Folder | 役割 |
|---|---|---|
| `etzhayyim-wasm-becoming-guardian-{nanoid}` | `wasm/` | Growth Guardian (守) |
| `etzhayyim-wasm-becoming-nurturer-{nanoid}` | `wasm/` | Capability Nurturer (育) |
| `etzhayyim-wasm-becoming-protector-{nanoid}` | `wasm/` | Safety Protector (盾) |
| `etzhayyim-wasm-becoming-play-{nanoid}` | `wasm/` | Play & Wellbeing Facilitator (遊) |
| `etzhayyim-wasm-becoming-family-{nanoid}` | `wasm/` | Family Bond Strengthener (和) |

## 7. Data Schema

### 7.1 Child Profile

| Column | Type | Description |
|---|---|---|
| `child_id` | String | 子ども識別子 |
| `org_id` | String | RLS: テナント |
| `user_id` | String | RLS: 登録者 |
| `actor_id` | String | RLS: 操作者 |
| `birth_date` | Date | 生年月日 |
| `developmental_stage` | String | 発達段階 (Piaget) |
| `erikson_stage` | String | 心理社会的段階 (Erikson) |
| `capability_scores_json` | String | 8 capability 次元スコア (JSON) |
| `risk_level` | String | リスクレベル (low/medium/high/critical) |
| `created_at` | Timestamp | 作成日時 |
| `updated_at` | Timestamp | 更新日時 |

### 7.2 Capability Assessment

| Column | Type | Description |
|---|---|---|
| `assessment_id` | String | 評価識別子 |
| `child_id` | String | 対象子ども |
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `dimension` | String | capability 次元 |
| `score` | Float64 | 0.0-1.0 スコア |
| `evidence_json` | String | 根拠 (JSON) |
| `assessor_agent_id` | String | 評価 agent |
| `assessed_at` | Timestamp | 評価日時 |

### 7.3 Intervention Plan

| Column | Type | Description |
|---|---|---|
| `plan_id` | String | 介入計画識別子 |
| `child_id` | String | 対象子ども |
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `target_dimensions` | String | 対象 capability 次元 (comma-separated) |
| `plan_json` | String | 介入計画詳細 (JSON) |
| `status` | String | planned/active/completed/cancelled |
| `designed_by_agent_id` | String | 設計 agent |
| `created_at` | Timestamp | 作成日時 |

## 8. Integration with Public Fund (Matrix Protocol)

権威ソース: `60-apps/etzhayyim-project-public-fund/90-docs/260315-cross-project-matrix-conversation-design.md`

### Command Path (Matrix Events)

- **Fund Application 審査**: `org.etzhayyim.xproject.assessment.request` を受信 → capability agent が `!case-{application-id}` room で評価結果を conversation として返す
- **セーフガード**: `org.etzhayyim.xproject.safeguard.alert` を `!xp-safeguard-{nanoid}` room に送信 → fund 側が disbursement 停止
- **成果報告**: `org.etzhayyim.xproject.outcome.report` を fund 側 room に送信

### Query Path (XRPC)

- `CapabilityQueryService/GetChildProfile` — 子どもプロフィール照会
- `CapabilityQueryService/GetCapabilityAssessment` — capability 評価結果照会
- `CapabilityQueryService/ListInterventionPlans` — 介入計画一覧照会

## 9. Privacy & Consent

子どもデータは最高レベルの保護を適用:

- `information_classification: restricted` — 子ども個人データ
- `clearance: confidential` — agent 間協議データ
- 保護者の明示的同意なしにデータ収集・評価を開始しない
- 子ども本人の意見表明権 (CRC Article 12) を尊重する仕組みを組み込む
- データ最小化原則: 評価に必要な最小限のデータのみ収集
