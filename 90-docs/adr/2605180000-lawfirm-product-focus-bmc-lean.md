---
id: adr-2605180000-lawfirm-product-focus-bmc-lean
title: "ADR-2605180000: lawfirm.etzhayyim.com 選択と集中 — Business Model Canvas + Lean Canvas"
status: active
doc_type: adr
topic: lawfirm-product-focus
authoritative: true
last_verified: 2026-05-18
authoritative_for:
  - etzhayyim プロダクトポートフォリオの選択と集中方針 (2026-05〜)
  - lawfirm.etzhayyim.com のビジネスモデル定義 (BMC + Lean Canvas)
  - shinshi.etzhayyim.com / animeka.etzhayyim.com のリソース配分方針
  - lawfirm 収益化ロードマップと KPI
  - Sprint 1 技術ゲート状況 (バックエンド接続完了 2026-05-18)
related:
  - adr-0079-lawfirm-india-intake-auto-route
  - adr-0016-legal-cluster-topology
  - adr-0018-pii-tier3-cohort-first
  - adr-2605072300-open-source-cloud-business-model
  - adr-2605130000-projector-mcp-project-management
  - adr-2605181200-lawfirm-nri-backend-connection-dispatcher-inline
supersedes: []
superseded_by: []
---

# ADR-2605180000: lawfirm.etzhayyim.com 選択と集中 — Business Model Canvas + Lean Canvas

**Status**: accepted
**Date**: 2026-05-18
**Deciders**: Jun Kawasaki

## Context

etzhayyim は現在 3 プロダクトを並行開発している:

| プロダクト | モデル | 状態 |
|---|---|---|
| lawfirm.etzhayyim.com | B2B SaaS (法律事務所向け AI case management) | D-Day チェックリスト実行中、CEO D1-D9 全承認済 |
| shinshi.etzhayyim.com | B2C トークン課金 (AI キャラクターハブ 18+) | v2 開発中、未出荷 |
| animeka.etzhayyim.com | B2B2C クリエイターツール (AI アニメ制作) | ep-1 公開済、収益モデル未確定 |

リソース分散が進み、いずれも「着火点」に達していない。
選択と集中の基準として「**キャッシュポイントの速さ × 成長可能性**」を採用し、
**lawfirm を主軸**に絞ることを正式決定する。

## Decision

### 1. プロダクト優先順位

```
Priority 1 (主軸)   : lawfirm.etzhayyim.com  ── 全エンジニアリングリソースの 70%
Priority 2 (維持)   : shinshi.etzhayyim.com   ── 20% (v2 最小出荷後に評価)
Priority 3 (自動運転): animeka.etzhayyim.com  ── 10% (CronJob + NATS 自動運転、収益モデル確定まで保留)
```

**判断根拠 (5 軸)**

| 軸 | lawfirm | shinshi | animeka |
|---|---|---|---|
| キャッシュ最短パス | **数週間 (SOW署名)** | 2〜3ヶ月 | 未確定 |
| 収益の性質 | **月次サブスク (予測可能)** | 変動トークン | なし |
| インフラ完成度 | **MVP 完成** (170 成果物, 73 test green) | v2 未完 | 27 graph live, KAMI Phase 2 未完 |
| 競合優位の持続性 | **高** (22言語ルーティング+peer firm連携) | 低 (candy.ai/character.ai 競合多数) | 中 (KAMI Engine 独自) |
| 規制リスク | 低 | **高** (NSFW/18+/国別差異) | 低 |

---

### 2. Business Model Canvas — lawfirm.etzhayyim.com

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ KEY PARTNERS          │ KEY ACTIVITIES        │ VALUE PROPOSITIONS  │ CUSTOMER REL  │ CUSTOMER SEGMENTS    │
│                       │                       │                     │               │                      │
│ • Kunal Bakshi /      │ • AI 案件管理 (intake  │ 【JP 法律事務所】     │ • SaaS セルフ  │ 【Primary】           │
│   lawyer.etzhayyim.com      │   →conflict→engaged   │ • AI で事務負担 80%  │   サービス     │ JP 中小法律事務所     │
│   (India peer firm)   │   →filed→hearing)     │   削減              │ • CSM (年払い  │ (弁護士 2〜20名規模)  │
│ • 日弁連 / 各単位     │ • India 22言語自動     │ • conflict check    │   テナント)    │                      │
│   弁護士会            │   ルーティング         │   自動化            │               │ 【Secondary】         │
│ • Murakumo LLM fleet  │ • 文書 vault (E2E      │ • 外部弁護士グラント  │               │ India SME 法律事務所  │
│   (翻訳・ドラフト)    │   暗号化)              │   管理              │               │ (Kunal 経由 partner)  │
│ • Zeebe / AT Protocol │ • BPMN process        │                     │               │                      │
│   infra               │   orchestration       │ 【India 法律事務所】  │               │ 【Tertiary】          │
│                       │ • SOW 管理・請求      │ • Hindi / 22言語     │               │ US 企業法務チーム     │
│                       │                       │   ネイティブ intake  │               │ (JP/US cross-border)  │
│                       │                       │ • JP peer firm 自動  │               │                      │
│                       │                       │   接続              │               │                      │
├───────────────────────┼───────────────────────┴─────────────────────┴───────────────┴──────────────────────┤
│ KEY RESOURCES         │ CHANNELS                                                                            │
│                       │                                                                                     │
│ • AT Protocol PDS     │ • 直接営業 (chikada / tanaka / a-nakamura contact 経由)                             │
│ • 22言語 LLM pipeline  │ • LinkedIn / Bluesky (etzhayyim actor 発信)                                        │
│ • lawfirm actor 170   │ • India: Kunal Bakshi 紹介ネットワーク                                              │
│   成果物 (MVP完成)    │ • 法律事務所向け SaaS 比較サイト (弁護士ドットコム / Legal Cloud Japan)              │
│ • Vault Zero-Knowledge │ • 無料 pilot (3ヶ月) → 有償転換                                                   │
│   (ADR-0074)          │                                                                                     │
├───────────────────────┴─────────────────────────────────────────────┬───────────────────────────────────────┤
│ COST STRUCTURE                                                       │ REVENUE STREAMS                       │
│                                                                      │                                       │
│ • Vultr VKE (Kotoba/Datomic, Zeebe): $241/月                            │ 【月額サブスクリプション (主)】          │
│ • RunPod Serverless (ComfyUI): ~$22/月                              │   Starter: ¥15,000/月 (〜5ユーザー)    │
│ • Cloudflare Workers: 従量 (現状ほぼ無料枠)                          │   Growth:  ¥35,000/月 (〜20ユーザー)   │
│ • Murakumo LLM fleet (Keiei): $0 追加 (共有インフラ)               │   Scale:   ¥80,000/月 (無制限)         │
│ • エンジニアリング人件費 (主要コスト)                                │                                       │
│                                                                      │ 【従量課金 (従)】                      │
│ Unit Economics 目標:                                                  │   案件翻訳: ¥500/件                   │
│   CAC < ¥50,000 / LTV > ¥500,000 / LTV:CAC > 10x                  │   外部弁護士グラント: ¥2,000/件         │
│                                                                      │                                       │
│                                                                      │ 【India ルーティング手数料 (将来)】      │
│                                                                      │   Kunal firm への案件紹介料            │
│                                                                      │   (成果報酬 or 月額 partnership fee)   │
└──────────────────────────────────────────────────────────────────────┴───────────────────────────────────────┘
```

---

### 3. Lean Canvas — lawfirm.etzhayyim.com

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ PROBLEM                    │ SOLUTION               │ UNIQUE VALUE PROPOSITION        │
│                            │                        │                                 │
│ 1. 事務処理で弁護士の可処  │ • AI intake + triage   │ 「脱出できる法務 SaaS」          │
│    分時間の 40〜60% が消費 │   (conflict check 自動) │ AT Protocol ネイティブで         │
│ 2. India ← → JP/US の      │ • 22言語自動ルーティン  │ データポータビリティ保証          │
│    cross-border 案件は     │   グ + peer firm 連携  │                                 │
│    言語障壁で取りこぼし多  │ • E2E Vault 文書管理    │ India 案件はボタン1つで           │
│ 3. 既存ツール (弁護士ドッ  │ • BPMN プロセス自動化  │ Kunal に自動配送                 │
│    トコム等) は事務管理    │                        │                                 │
│    に特化、AI 活用なし     │                        │ ターゲット:                      │
│                            │                        │ JP 弁護士 2〜20名事務所         │
├────────────────────────────┴────────────────────────┤ India partner firm              │
│ EXISTING ALTERNATIVES      │ KEY METRICS            ├─────────────────────────────────┤
│                            │                        │ UNFAIR ADVANTAGE                │
│ • 弁護士ドットコム (事務管  │ Week 1:                │                                 │
│   理、AI なし)             │   初回 SOW 署名件数     │ • ADR-0019 path DID による       │
│ • CLIO / MyCase (US)       │                        │   recursive DID 案件管理         │
│   (JP 対応なし)            │ Month 1:               │ • 22言語 Murakumo pipeline       │
│ • 手動 Excel + メール      │   MRR / テナント数      │   (他社が6ヶ月で追いつけない)    │
│                            │                        │ • Vault Zero-Knowledge (GDPR /   │
│                            │ Month 3:               │   弁護士秘匿特権 準拠)           │
│                            │   NPS / churn rate     │ • Kunal Bakshi 独占 partner       │
│                            │   CAC 回収月数          │   (India ルーティング独占)       │
├────────────────────────────┴────────────────────────┴─────────────────────────────────┤
│ CHANNELS                   │ COST STRUCTURE         │ REVENUE STREAMS                 │
│                            │                        │                                 │
│ • 直販 (chikada/tanaka     │ Fixed: $263/月 (infra) │ Starter ¥15,000 →               │
│   既存コンタクト)          │ Variable: LLM tokens   │ Growth  ¥35,000 →               │
│ • India: Kunal 紹介        │ People: 主要コスト      │ Scale   ¥80,000                 │
│ • LinkedIn / Bluesky       │                        │                                 │
│ • 無料 3ヶ月 pilot         │ Target MRR:            │ Month 3 target: ¥300,000 MRR    │
│                            │   Month 3: ¥300K       │ (10テナント × avg ¥30,000)      │
│                            │   Month 6: ¥1M         │ Month 6 target: ¥1,000,000 MRR  │
└────────────────────────────┴────────────────────────┴─────────────────────────────────┘
```

---

### 4. Lean 実験ロードマップ

#### Sprint 1 技術ゲート — バックエンド接続完了 (2026-05-18 DONE)

| 項目 | 状態 | 詳細 |
|---|---|---|
| 4 NSID (requestConsult / createCase / translateToLang / translateFromLang) 404 解消 | ✅ DONE | `dispatcher_main.py` `lawfirm_direct_handler()` inline handler。lf1rm8k0.etzhayyim.com LIVE |
| NRI booking form → requestConsult XRPC wiring | ✅ DONE | `/services/nri/book` が consultDid を booking ref として返す |
| India auto-route fail-loud (NotConfigured) | ✅ DONE | createCase は案件 record を作成 + autoRouteError=NotConfigured を返す |
| LAWYER_FIRM_DID_HINT + KUNAL_LEAD_DID_HINT 設定 | ⏳ PENDING | migration `lawfirm-india-auto-route-secrets` 参照 |
| billing migration (vertex_lawfirm_billing_tenant + Stripe) | ⏳ Sprint 1 内 | ADR-2605180000 §4 Consequences 参照 |

ADR: `90-docs/adr/2605181200-lawfirm-nri-backend-connection-dispatcher-inline.md`

#### Sprint 1 (2026-05-18 〜 06-01): 最初の SOW 署名

**Riskiest Assumption**: 日本の中小法律事務所が ¥15,000/月 を払う意思がある

**実験**:
- a-nakamura / chikada / tanaka との次のコール設定 → デモ実施
- SOW 下書き 10 本のうち最も有望な 2〜3 社を絞り込む
- 3ヶ月無料 pilot として提案 → 署名

**判定基準**:
- `PASS`: 2026-06-01 までに SOW 1 件署名
- `FAIL`: 署名ゼロ → 価格帯・提案内容を見直し

#### Sprint 2 (2026-06-01 〜 07-01): ¥300,000 MRR

**Riskiest Assumption**: pilot テナントが有償転換する

**実験**:
- pilot テナントの weekly NPS 計測 (Google Form + XRPC 記録)
- India 案件の自動ルーティング実証 → Kunal からの紹介フロー確立
- 有償転換 CTA を D+60 にインアプリ表示

**判定基準**:
- `PASS`: 有償テナント 10 社 (¥300,000 MRR)
- `FAIL`: 有償転換率 < 20% → UX / feature gap 分析

#### Sprint 3 (2026-07-01 〜 09-01): ¥1,000,000 MRR + India チャネル確立

**Riskiest Assumption**: Kunal ネットワーク経由で India 事務所が有償化する

**実験**:
- India 法律事務所 Starter plan (USD $99/月 = INR ~8,300 に相当) を別建てで設定
- Kunal に紹介手数料 (¥5,000/テナント/月) 提案
- JP/India cross-border 案件の実績 2〜3 件を marketing case study 化

**判定基準**:
- `PASS`: MRR ¥1,000,000 (JP 25 社 + India 5 社)
- `FAIL` → shinshi v2 への追加リソースを検討

---

### 5. shinshi / animeka のリソース配分方針

#### shinshi.etzhayyim.com (Priority 2)

v2 の **must-have のみ** でファーストリリースする:
- キャラクター 247 体のプロフィール閲覧 (read-only は完成済)
- トークン購入 (Stripe) + 1:1 LLM チャット (Gemma E4B)
- これ以外 (scene generation, free tier, analytics) は lawfirm ¥300K MRR 達成後

NSFW 規制リスクは各 geo の age verification 法制 (英 AVSA 2023 / 仏 LCEN 改正 / 米 KOSA) が確定するまでは
marketing push を抑制し、organic discovery のみ。

#### animeka.etzhayyim.com (Priority 3)

自動運転モード:
- animeka-autopilot CronJob + NATS JetStream で ep 継続発行 (人的介入なし)
- Bluesky コミュニティ反応 (likes / quotes) を 4 週ごとにトレースし 100 likes/ep を超えたら収益モデル議論を再開
- 収益モデル候補: アニメスタジオへのホワイトラベル B2B SaaS (¥300,000〜/月/スタジオ)

---

### 6. KPI ダッシュボード

| KPI | 計測頻度 | 2026-06 Target | 2026-09 Target |
|---|---|---|---|
| MRR (lawfirm) | 週次 | ¥300,000 | ¥1,000,000 |
| 有償テナント数 | 週次 | 10社 | 30社 |
| 有償転換率 (pilot→paid) | スプリント末 | 40% | 50% |
| NPS (lawfirm) | 月次 | +30 | +40 |
| India 案件ルーティング数 | 月次 | 5件 | 30件 |
| CAC | スプリント末 | < ¥80,000 | < ¥50,000 |
| LTV:CAC | 四半期 | > 5x | > 10x |
| shinshi DAU | 週次 | (v2出荷後) | 200 |
| animeka ep likes | 4週 | 30/ep | 100/ep |

KPI は `projector.update_status` (ADR-2605130000) で毎スプリント末に記録する。

## Consequences

### 即時アクション (今週)

1. **a-nakamura / chikada / tanaka** への next step コール設定 → 最有望 2〜3 社に SOW 最終化提案
2. **lawfirm billing migration**: `vertex_lawfirm_billing_tenant` + Stripe webhook を Sprint 1 内に実装
3. **shinshi v2 scope freeze**: must-have 3 機能に絞り、残りを backlog に移動
4. **animeka autopilot 確認**: CronJob + NATS が人的介入なしで動いていることを verify

### トレードオフ

- **lawfirm 集中 (選択) vs 3プロダクト並走**: shinshi のトークン収入機会を短期的に逃す可能性。
  ただし lawfirm B2B の LTV は shinshi B2C の 10〜50x と推定されるため期待値は正。
- **India 価格帯 (USD $99/月 vs JP ¥35,000/月)**: India は購買力調整が必要。
  Kunal の紹介手数料モデルと組み合わせて unit economics を別計算する。

### 制約

- PII は ADR-0018 Tier 3 (Preferences) に隔離。billing テナント情報も `signal:v1:` field-encrypt
- lawfirm billing actor が Stripe API を直接呼ぶ場合は `com.etzhayyim.apps.stripe.*` XRPC 経由
- 価格変更は本 ADR を amendment として更新 (直接 deps.toml 書き換えは不可)

## Alternatives Considered

| 案 | 却下理由 |
|---|---|
| shinshi 優先 | v2 未完 + NSFW 規制リスク + lawfirm に比べ LTV 低 |
| animeka 優先 | 収益モデル未確定。エンジニアリング投資に対するキャッシュ回収が最も長い |
| 3プロダクト均等投資継続 | 全て「着火点」未到達のまま分散し、いずれも失速するリスク |
| Enterprise-first (大手法律事務所のみ) | 日本の大手は IT 調達が遅く、最初の収益まで 6〜12ヶ月かかる。SME 中心で speed を優先 |

## References

- `deps.toml [etzhayyim_agent.project_management]` — projector MCP
- `90-docs/adr/0079-lawfirm-india-intake-auto-route.md` — India routing 実装
- `90-docs/adr/0016-legal-cluster-topology.md` — 法務クラスター設計
- `90-docs/adr/2605072300-open-source-cloud-business-model.md` — OSS収益モデル (参考)
- `60-apps/etzhayyim-project-lawfirm/CLAUDE.md` — lawfirm 実装詳細
- `60-apps/etzhayyim-project-shinshi/CLAUDE.md` — shinshi 実装詳細
- `60-apps/etzhayyim-project-animeka/CLAUDE.md` — animeka 実装詳細
- D-DAY-checklist.md (lawfirm pilot pipeline, iter111〜119)
- CEO-REPLY-DECISION-TREE.md (D1-D9 承認記録)
- `90-docs/adr/2605212100-kansayaku-cyber-bmc-lean.md` — サイバー監査役紹介事業 BMC (lawfirm チャネル連携 P5)
