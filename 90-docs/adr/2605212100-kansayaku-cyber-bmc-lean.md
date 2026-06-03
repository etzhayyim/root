---
id: adr-2605212100-kansayaku-cyber-bmc-lean
title: "ADR-2605212100: サイバーセキュリティ特化 監査役人材紹介事業 — Business Model Canvas + Lean Canvas"
status: active
doc_type: adr
topic: kansayaku-cyber-placement-bmc
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - サイバーセキュリティ特化 監査役紹介事業のビジネスモデル定義 (BMC + Lean Canvas)
  - etzhayyim ネットワーク連携チャネル戦略 (lawfirm / kaisya / recruit 連携)
  - 成果報酬型フィー体系
  - 顧客セグメント (非上場スタートアップ + 上場企業)
related:
  - adr-2605180000-lawfirm-product-focus-bmc-lean
  - adr-2605190000-yatabase-bmc-lean
  - adr-0027-recruit-talent-public-feed-first
  - adr-0018-pii-tier3-cohort-first
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
supersedes: []
superseded_by: []
---

# ADR-2605212100: サイバーセキュリティ特化 監査役人材紹介事業 — Business Model Canvas + Lean Canvas

**Status**: accepted
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

企業のサイバーセキュリティガバナンス強化ニーズが急騰している。
2025 年改正会社法・金融商品取引法 対応、経産省「サイバーセキュリティ経営ガイドライン v3.0」、
東証プライム上場基準強化を受け、**サイバーセキュリティの知見を持つ社外監査役**の需要が急拡大している一方、
適格候補者はほぼ市場に出回らない (供給不足)。

### 3-Axis OR-Test (ADR-2605172400)

| 軸 | 判定 | 理由 |
|---|---|---|
| Liability (法的責任) | **vendor** | 職業安定法 第 30 条 有料職業紹介事業許可が必要。etzhayyim Japan株式会社 名義で申請 |
| Custody (データ保管) | **vendor** | 候補者個人情報 (PII Tier 3) を RisingWave に保管 |
| Settlement (決済) | **vendor** | 成果報酬 (金銭取引) = Stripe Invoice 経由 |

→ 3 軸 OR-test で vendor 判定。**etzhayyim Japan株式会社 (vendor)** が事業主体。

### 市場背景

| 項目 | 数値 |
|---|---|
| 東証プライム上場企業数 | 約 1,650 社 |
| サイバーセキュリティ専門の社外監査役在任者 (推定) | < 200 名 |
| IPO 準備中企業 (直前期〜申請期) | 年間 約 80〜120 社 |
| 監査役報酬 (上場中小) | ¥2M〜¥8M/年 |
| 監査役報酬 (IPO 準備スタートアップ) | ¥600K〜¥2M/年 |
| 成果報酬フィー相場 (人材紹介全般) | 年収の 30〜35% |

---

## Decision

### 1. ビジネス定義

```
事業名   : etzhayyim Cyber Board — サイバーセキュリティ監査役紹介
事業主体 : etzhayyim Japan株式会社 (vendor)
収益モデル: 成果報酬型 (年収の 30〜35%)
顧客     : 非上場スタートアップ (IPO 準備・直前期) + 上場企業 (プライム/スタンダード)
特化軸   : サイバーセキュリティ知見を持つ社外監査役 × AI マッチング
チャネル : lawfirm.etzhayyim.com / kaisya.etzhayyim.com / recruit.etzhayyim.com 連携 + 直販
```

---

### 2. Business Model Canvas — etzhayyim Cyber Board

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ KEY PARTNERS              │ KEY ACTIVITIES             │ VALUE PROPOSITIONS    │ CUST REL      │ CUSTOMER SEGMENTS        │
│                           │                            │                       │               │                          │
│ • recruit.etzhayyim.com         │ • 候補者発掘・エンリッチ    │ 【上場企業 / IPO準備】 │ • 担当制 RM    │ 【Primary A】              │
│   (talent cohort registry │   (ISCO-08 × cyber cert    │ • CISO 経験者 × 監査役 │   (企業側)     │ 東証プライム/スタンダード   │
│   21,373 行, ORCID連携)   │   × board 実績でスコア)   │   適格者を最短 30 日   │ • AI マッチ    │ 上場企業 (IT/金融/製造)    │
│ • lawfirm.etzhayyim.com         │ • AI マッチング            │   で提示              │   レポート     │ サイバーインシデント後の    │
│   (法律事務所ネットワーク  │   (LangGraph 候補者スコア  │ • 会社法適合 + 独立性  │   (月次)       │ ガバナンス強化ニーズ        │
│   → 顧客企業紹介)         │   リング → 上位 3 名提示) │   要件チェック自動化   │               │                          │
│ • kaisya.etzhayyim.com          │ • デュー・ディリジェンス    │ • AT Protocol DID で  │ • 候補者向け   │ 【Primary B】              │
│   (企業ガバナンスデータ    │   (候補者独立性・利益相反   │   ポートフォリオ検証   │   プロフィル   │ 非上場スタートアップ        │
│   + 役員変遷 track)       │   + cyber cert 検証)       │                       │   (self-       │ (Series B〜 / IPO直前期)  │
│ • 情報処理安全確保支援士   │ • SOW 締結・候補者推薦     │ 【候補者 (人材側)】    │   sovereign    │ 上場審査でガバナンス指摘    │
│   (登録者 2万+ のコミュ    │ • 入社後フォローアップ     │ • 希少ポジションへの   │   DID)         │ を受けた企業               │
│   ニティ × 副業ニーズ)    │   (90日・180日チェック)    │   優先紹介 (副業可)   │               │                          │
│ • 公認会計士協会           │ • lawfirm / kaisya から   │ • DID ネイティブな    │               │ 【Secondary】              │
│   (監査法人経由の          │   インバウンドリード受付   │   実績透明開示         │               │ 上場準備中 VC ポートフォリオ │
│   候補者ソーシング)        │                            │                       │               │ 企業 (VC 経由一括紹介)     │
├───────────────────────────┼────────────────────────────┴───────────────────────┴───────────────┴──────────────────────────┤
│ KEY RESOURCES             │ CHANNELS                                                                                      │
│                           │                                                                                               │
│ • recruit.etzhayyim.com 候補者  │ • lawfirm.etzhayyim.com 経由: 法律事務所が企業クライアントにガバナンス強化を提案 → etzhayyim 紹介       │
│   コホート (21,373 行)    │ • kaisya.etzhayyim.com 経由: 役員変遷分析で監査役空席を検出 → アウトリーチ自動化                  │
│ • LangGraph マッチング    │ • 直販: IPO 準備企業に直接アプローチ (Wantedly / LinkedIn / 東証 IPO カレンダー)           │
│   エンジン (候補者スコア   │ • VC ネットワーク: Series B+ 投資家経由のポートフォリオ企業一括紹介                         │
│   リング + 独立性チェック) │ • 情報処理安全確保支援士コミュニティ: Slack / 勉強会 (副業監査役マッチング)                  │
│ • 有料職業紹介事業許可     │                                                                                               │
│   (etzhayyim Japan名義)        │                                                                                               │
│ • AT Protocol DID 候補者  │                                                                                               │
│   ポートフォリオ (実績改   │                                                                                               │
│   ざん不可)               │                                                                                               │
├───────────────────────────┴────────────────────────────────────────────────────┬──────────────────────────────────────────┤
│ COST STRUCTURE                                                                  │ REVENUE STREAMS                          │
│                                                                                 │                                          │
│ Fixed:                                                                          │ 【成果報酬 (主・100%)】                    │
│  • 有料職業紹介事業許可取得 + 更新費 (~¥150,000 初回)                           │                                          │
│  • recruit / kaisya / lawfirm infra: 共有 (追加コストほぼゼロ)                  │   上場企業: 年収 × 35%                    │
│  • LangGraph / RisingWave: 共有インフラ                                         │     監査役年収 ¥3M → fee ¥1,050,000      │
│                                                                                 │     監査役年収 ¥6M → fee ¥2,100,000      │
│ Variable:                                                                       │     監査役年収 ¥10M → fee ¥3,500,000     │
│  • RM (リレーションシップマネージャー) 人件費: 主要コスト                        │                                          │
│  • 候補者評価 (CISA/CISSP/情報処理安全確保支援士 cert 確認)                    │   非上場スタートアップ: 年収 × 30%         │
│  • 法務 (委任状・推薦書・SOW レビュー)                                          │     監査役年収 ¥800K → fee ¥240,000      │
│                                                                                 │     監査役年収 ¥2M → fee ¥600,000        │
│ Unit Economics 目標:                                                             │                                          │
│   CAC < ¥100,000 / 平均フィー ¥1,200,000                                      │ 【リテーナー (将来・上場企業向け)】         │
│   LTV:CAC > 12x (リピート企業 = 役員改選毎に再依頼)                            │   ¥200,000/月 × 6ヶ月 = ¥1,200,000       │
│                                                                                 │   (成果報酬と相殺)                        │
└─────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────┘
```

---

### 3. Lean Canvas — etzhayyim Cyber Board

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ PROBLEM                       │ SOLUTION                  │ UNIQUE VALUE PROPOSITION        │
│                               │                           │                                 │
│ 1. サイバーセキュリティ知見    │ • recruit.etzhayyim.com の      │「サイバー監査役を 30 日で」        │
│    を持つ社外監査役が           │   コホートデータ +         │                                 │
│    市場にほぼ存在しない         │   ISCO-08 × cert × board  │ CISO 経験 × 監査役適格 × 独立性  │
│    (供給不足 × 需要急増)        │   実績でスコアリング       │ を AI で一括検証し提示            │
│                               │                           │                                 │
│ 2. 上場企業 / IPO準備企業      │ • 独立性・利益相反を       │ AT Protocol DID でポートフォリオ  │
│    は監査等委員会設置で          │   会社法に沿って自動チェック│ 改ざん不可                       │
│    サイバー専門家を急募         │                           │                                 │
│    しているが紹介会社が         │ • lawfirm / kaisya から   │ ターゲット:                      │
│    対応できていない             │   インバウンドリードを     │ 東証上場企業 IT/金融/製造          │
│                               │   受け取り企業にマッチング  │ + Series B〜IPO準備スタートアップ  │
│ 3. 候補者 (CISO OB等) は      │                           │                                 │
│    副業・社外役員ニーズが        │ • 90/180 日フォロー        │                                 │
│    あるが接点がない             │   (定着支援)               │                                 │
├───────────────────────────────┴───────────────────────────┤                                 │
│ EXISTING ALTERNATIVES         │ KEY METRICS               │                                 │
│                               │                           │                                 │
│ • ヘッドハンティング大手        │ Month 3:                  ├─────────────────────────────────┤
│   (JAC / Spencer Stuart)      │   初回 SOW 成約件数        │ UNFAIR ADVANTAGE                │
│   → サイバー特化なし           │                           │                                 │
│ • 監査役協会コミュニティ        │ Month 6:                  │ • recruit.etzhayyim.com 21,373行       │
│   → ネットワーク紹介のみ        │   累計成約数 / MRR換算     │   コホートデータ × ORCID 連携     │
│   (AI マッチングなし)          │                           │   (他社が 6ヶ月で追いつけない)    │
│ • 会計士事務所 OB 紹介         │ Month 12:                 │ • lawfirm.etzhayyim.com 経由の          │
│   → 会計専門で cyber 弱い      │   リピート企業率 / NPS     │   法律事務所インバウンドチャネル   │
│                               │   平均フィー単価            │ • AT Protocol DID ポートフォリオ  │
│                               │                           │   (実績改ざん不可 = 信頼担保)     │
│                               │                           │ • 有料職業紹介事業許可 (参入障壁)  │
├───────────────────────────────┴───────────────────────────┴─────────────────────────────────┤
│ CHANNELS                      │ COST STRUCTURE            │ REVENUE STREAMS                 │
│                               │                           │                                 │
│ • lawfirm.etzhayyim.com 法律事務所  │ Fixed: 許可取得 ¥150K      │ 成果報酬: 年収 × 30〜35%         │
│ • kaisya.etzhayyim.com 空席検出     │ Variable: RM 人件費 主要   │                                 │
│ • 情報処理安全確保支援士コミュ │                           │ 上場企業 avg fee: ¥1,500,000     │
│ • LinkedIn / Wantedly 直販    │ 目標: CAC < ¥100,000       │ スタートアップ avg fee: ¥450,000 │
│ • VC ポートフォリオ一括紹介   │                           │                                 │
│                               │ Month 6 target:            │ Month 3: 2件 ≈ ¥2,400,000      │
│                               │   成約 1 件/月 ペース確立   │ Month 6: ¥1,200,000 MRR換算     │
│                               │                           │ Month 12: ¥3,000,000 MRR換算    │
└───────────────────────────────┴───────────────────────────┴─────────────────────────────────┘
```

---

### 4. Lean 実験ロードマップ

#### Sprint 0 (2026-05-21 〜 06-01): 法的基盤 + 候補者コホート確認

**Riskiest Assumption 0**: 有料職業紹介事業許可なしでは事業開始不可

| タスク | 担当 | 期限 |
|---|---|---|
| 有料職業紹介事業許可 申請書類確認 (厚労省 ハローワーク) | Jun | 05-28 |
| recruit.etzhayyim.com コホートから cyber cert (CISA / CISSP / 情報処理安全確保支援士) 保有者抽出 | LangGraph | 05-25 |
| 情報処理安全確保支援士 登録者リスト (IPA 公開) → 副業意向アンケート設計 | Jun | 05-28 |
| lawfirm.etzhayyim.com にガバナンス強化相談 intake NSID 追加検討 | backlog | Sprint 1 |

#### Sprint 1 (2026-06-01 〜 07-01): 最初の SOW 成約

**Riskiest Assumption 1**: 企業が成果報酬 ¥1,000,000+ を払う意思がある

**実験**:
- kaisya.etzhayyim.com の役員変遷データから監査役ポスト空席候補企業 10 社を特定
- lawfirm.etzhayyim.com 経由の企業クライアント 3 社にヒアリング
- 候補者 3 名をクローズドで提示 → SOW 1 件署名

**判定基準**:
- `PASS`: SOW 1 件署名 (2026-07-01 まで)
- `FAIL`: 需要仮説・フィー水準を見直し

#### Sprint 2 (2026-07-01 〜 09-01): 月 1 件ペース確立

**Riskiest Assumption 2**: lawfirm チャネルがリードを安定供給する

**実験**:
- lawfirm.etzhayyim.com の requestConsult XRPC に「ガバナンス強化」カテゴリを追加
- IPO 準備企業 (東証 IPO カレンダー + kaisya.etzhayyim.com) へのアウトリーチ自動化
- 候補者プールを 50 名に拡大 (情報処理安全確保支援士コミュニティ + LinkedIn)

**判定基準**:
- `PASS`: 成約 2〜3 件 (¥3,000,000〜 累計フィー)
- `FAIL` → VC ポートフォリオ一括紹介に軸足を移す

#### Sprint 3 (2026-09-01 〜 12-01): ¥3,000,000 MRR換算

**Riskiest Assumption 3**: リピート企業化 (役員改選ごとに再依頼)

**実験**:
- 成約企業の 90 日・180 日フォロー → NPS 計測
- 「IPO 後 1 年以内の監査役改選」は自動リマインド (kaisya actor)
- VC 経由ポートフォリオ一括紹介プログラム開始

---

### 5. etzhayyim プラットフォーム連携設計

| 連携先 | 連携内容 | 実装形態 |
|---|---|---|
| `recruit.etzhayyim.com` | 候補者コホートからサイバー cert × board 実績スコアリング | `com.etzhayyim.apps.recruit.matchStats` + LangGraph |
| `kaisya.etzhayyim.com` | 役員変遷データで監査役空席・改選タイミング検出 | `kaisya` actor query (既存) |
| `lawfirm.etzhayyim.com` | 法律事務所クライアント企業からのインバウンドリード | `requestConsult` XRPC に category=governance 追加 |
| `vault.etzhayyim.com` | 候補者 PII (連絡先・職歴) の E2E 暗号化保管 | `signal:v1:` field-encrypt (ADR-0018 Tier 3) |
| `recruit.etzhayyim.com` DID | 候補者ポートフォリオを AT Protocol DID で改ざん不可に | `com.etzhayyim.apps.recruit.talentCohort` record |

**PII 管理 (ADR-0018 Tier 3 遵守)**:
- 候補者個人情報は `vault.etzhayyim.com` + `signal:v1:` field-encrypt 必須
- 企業側への開示は候補者の consent record URI 確認後のみ
- 成約後の個人情報は GDPR Art.17 準拠で hard delete

---

### 6. KPI ダッシュボード

| KPI | 計測頻度 | 2026-07 Target | 2026-12 Target |
|---|---|---|---|
| 累計成約件数 | 月次 | 1 件 | 12 件 |
| 平均フィー | 月次 | ¥800,000 | ¥1,200,000 |
| 累計フィー収入 | 月次 | ¥800,000 | ¥14,400,000 |
| 候補者プール数 | 月次 | 20 名 | 100 名 |
| 企業 NPS | 180 日後 | — | +40 |
| リピート企業率 | 四半期 | — | 30% |
| lawfirm チャネル経由率 | 月次 | 50% | 40% |
| CAC | 四半期 | < ¥150,000 | < ¥100,000 |

KPI は `projector.update_status` (ADR-2605130000) で毎スプリント末に記録する。

---

## Consequences

### 即時アクション (今週)

1. **有料職業紹介事業許可**: 厚労省様式確認 + 弁護士 (lawfirm 連携) に申請代行相談
2. **候補者コホート初期抽出**: `recruit.etzhayyim.com` から情報処理安全確保支援士 × 副業可能者を LangGraph で抽出
3. **kaisya.etzhayyim.com 監査役空席検出**: 役員変遷データクエリで IPO 準備企業 + 直近 2 年監査役未変更企業リスト作成
4. **lawfirm.etzhayyim.com 連携**: `requestConsult` XRPC に `category: "governance"` フィールド追加を backlog に積む

### トレードオフ

- **特化 (サイバー監査役のみ) vs 汎用 (役員紹介全般)**: 汎用は JAC/Spencer Stuart と競合し差別化が困難。
  サイバー特化により希少性を担保し、単価・成約率ともに高位安定を狙う。
- **成果報酬のみ vs リテーナー併用**: リテーナーは上場企業には受け入れられやすいが、
  初期はシンプルな成果報酬のみで信頼構築し Sprint 3 以降で展開する。
- **スピード vs 許可取得**: 有料職業紹介事業許可なしで「紹介料」を取ることは職業安定法違反。
  許可取得まで (通常 2〜3 ヶ月) は無償マッチングテスト (PoC) として実施する。

### 制約

- **有料職業紹介事業許可 (職業安定法 第 30 条)** 取得必須。無許可での報酬受取は禁止。
- 候補者 PII は ADR-0018 Tier 3 準拠 (`signal:v1:` field-encrypt + consent gate)
- 成果報酬の請求は `com.etzhayyim.apps.stripe.*` XRPC 経由 (Worker 直 Stripe call 禁止)
- 候補者の AT Protocol DID ポートフォリオは self-sovereign (本人以外の書き込み禁止)

## Alternatives Considered

| 案 | 却下理由 |
|---|---|
| 役員紹介全般 (汎用) | JAC / Spencer Stuart と真正面競合。差別化困難 |
| 上場企業のみ | IPO 準備スタートアップはフィー単価は低いが成約速度が速く学習機会が大きい |
| 月額定額 SaaS 化 | 候補者マッチングは高単価・低頻度。SaaS 化は MRR 安定後の展開オプション |
| VC ファンド経由一括契約のみ | 初期は関係構築コストが高い。Sprint 2 以降でスケールチャネルとして活用 |

## References

- `90-docs/adr/2605180000-lawfirm-product-focus-bmc-lean.md` — lawfirm BMC (チャネル連携)
- `90-docs/adr/0027-recruit-talent-public-feed-first.md` — recruit コホート設計
- `90-docs/adr/0018-pii-tier3-cohort-first.md` — PII Tier 3 設計
- `90-docs/adr/2605172400-etzhayyim-vendor-three-axis-split-rule.md` — 3-axis split rule
- `60-apps/etzhayyim-project-kaisya/CLAUDE.md` — kaisya 役員変遷データ
- `60-apps/etzhayyim-project-recruit/CLAUDE.md` — recruit コホート実装
- 経産省「サイバーセキュリティ経営ガイドライン v3.0」(2023)
- 厚労省「有料職業紹介事業の許可申請」(職業安定法 第 30 条)
