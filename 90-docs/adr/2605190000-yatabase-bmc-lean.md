---
id: adr-2605190000-yatabase-bmc-lean
title: "ADR-2605190000: yatabase.etzhayyim.com — Business Model Canvas + Lean Canvas"
status: superseded
doc_type: adr
topic: yatabase-product-bmc
authoritative: false
last_verified: 2026-05-19
authoritative_for: []
related:
  - adr-2605080000-yatabase-yata-retail-cloud
  - adr-2605180000-lawfirm-product-focus-bmc-lean
  - adr-2605130000-projector-mcp-project-management
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-0048-risingwave-vultr-b2-primary
supersedes: []
superseded_by:
  - adr-2605210001-yatabase-minimax-pricing-bmc
---

# ADR-2605190000: yatabase.etzhayyim.com — Business Model Canvas + Lean Canvas

**Status**: accepted
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

## Context

yatabase.etzhayyim.com は etzhayyim platform の余剰能力 (B2 Bandwidth Alliance 実質ゼロ egress、RisingWave 共有クラスター、Murakumo 自己ホスト LLM) を **retail cloud product** として外部開発者に再販するプロダクトである。

| 項目 | 状態 |
|---|---|
| 製品フェーズ | v0.1.0 shipped (P1-P46 完了) |
| Stripe billing | LIVE (Free / Starter $13 / Developer $33 / Business $650 / Enterprise) |
| 自律エージェント | 4 体 稼働中 (sakamoto CS / nishino sales / tanaka QA / chikada dev) |
| リード獲得 | HN Algolia cron (0 */6) + GitHub stargazers cron (45 */6) 自律稼働 |
| BMC LangGraph | `bmc_iteration` cron 毎朝 07:00 UTC で自律計測 |

etzhayyim ポートフォリオ内での位置付け:

```
Priority 1 (主軸)     : lawfirm.etzhayyim.com   — 70% エンジニアリングリソース
Priority 2 (維持)     : shinshi.etzhayyim.com    — 20%
Priority 3 (自動運転) : animeka.etzhayyim.com    — 10%
Priority 4 (プラットフォーム・自律稼働) : yatabase.etzhayyim.com — 専用予算 + 自律 AI 運用
```

yatabase は他 3 製品を **支えるインフラ** (RisingWave per-tenant DB、B2 object storage、MCP surface) でもある。エンジニアリング人的介入は機能開発 sprint 時のみ、通常は自律エージェントが運営する。

## Decision

### 1. ポートフォリオ内の役割

```
プロダクト種別  : B2D / B2B — Developer Tool & Graph Database Cloud
収益モデル     : USD サブスク (Free → $13 → $33 → $650 → Enterprise)
営業モデル     : Product-Led Growth — セルフサービス + 自律 AI エージェント
主戦場         : AI-native devs / MCP ecosystem / Japan SaaS startups
差別化軸       : MCP-first の唯一の graph DB cloud + AT Protocol DID auth
                 + アノニマスサインアップ + 原価優位 (B2 BWA ゼロ egress)
自律度         : 高 (リード獲得・CS 対応・BMC 計測すべて自動)
```

---

### 2. Business Model Canvas — yatabase.etzhayyim.com

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ KEY PARTNERS           │ KEY ACTIVITIES          │ VALUE PROPOSITIONS   │ CUSTOMER REL  │ CUSTOMER SEGMENTS      │
│                        │                         │                      │               │                        │
│ • Cloudflare           │ • Lead 獲得 (HN Algolia  │ 【AI-native devs】    │ • セルフサービ  │ 【Primary】             │
│   (Workers/Hyper-      │   + GitHub stargazers、  │ • 1 API key で graph │   ス (/docs    │ AI-native devs          │
│   drive/R2/DNS)        │   自律 cron)             │   DB + object store  │   /quickstart  │ MCP 対応プロダクト開発   │
│ • Vultr VKE LAX        │ • Lead enrichment        │   + MCP を統合提供   │   /studio)     │ (primary)               │
│   (RisingWave cluster  │   (homepage scrape →     │ • MCP-native: 業界   │ • sakamoto     │                        │
│   per-tenant DB)       │   contact_email/         │   初の /mcp surface  │   CS agent が  │ 【Secondary】           │
│ • Backblaze B2         │   tech_stack)            │   付き graph DB cloud│   support@     │ Indie hackers / side    │
│   (content-addressed   │ • Outreach drafting      │ • Supabase Pro $25   │   etzhayyim.com を   │ projects (価格感度高)   │
│   object storage)      │   (nishino agent →       │   比 ~50% 安い       │   トリアージ    │                        │
│ • Stripe               │   operator 承認 →        │   Starter $13/月     │   + 下書き     │ 【Tertiary】            │
│   (US payments + Tax)  │   batch-send)            │ • アノニマスサインア  │ • nishino      │ Japan SaaS startups     │
│ • RunPod + Murakumo    │ • CS triage              │   ップ (email 不要)  │   sales agent  │ (適格請求書 T9007…)    │
│   (LLM for agents)     │   (sakamoto agent)       │                      │   が cold      │                        │
│ • Resend               │ • Daily BMC iteration    │ 【Japan SaaS】        │   outreach     │ 【Future】              │
│   (transactional email)│   (LangGraph cron 07:00  │ • 適格請求書 T9007…  │   下書き        │ Mid-market data teams   │
│                        │   UTC)                   │   対応 (JPY 課金)    │               │ (50-500名)              │
│                        │ • Stripe billing event   │ • AT Protocol DID    │               │                        │
│                        │   metering               │   auth (email/PW 代替)│              │                        │
├────────────────────────┼─────────────────────────┴──────────────────────┴───────────────┴────────────────────────┤
│ KEY RESOURCES          │ CHANNELS                                                                                  │
│                        │                                                                                           │
│ • CF Worker edge       │ • HN Algolia scrape → cold outreach (autonomous, cron 0 */6)                            │
│   (yatabase.etzhayyim.com    │ • GitHub stargazers (neo4j/supabase/hasura/dgraph/arangodb) (cron 45 */6)               │
│   API gateway)         │ • Organic SEO (sitemap.xml, JSON-LD SoftwareApplication + FAQPage)                       │
│ • RisingWave on Vultr  │ • /comparison page vs Supabase / Neo4j AuraDB / Hasura                                  │
│   (per-org yata_<hash> │ • /integrations: Cursor / Claude Desktop / Continue.dev MCP listings (手動)             │
│   DB isolation)        │ • Product Hunt launch (P10 予定)                                                         │
│ • B2 object storage    │ • Japan SaaS: 弁護士事務所 / スタートアップ向け LinkedIn + Bluesky                        │
│ • Stripe Live billing  │                                                                                           │
│ • 4 AI agents + 3      │                                                                                           │
│   autonomous crons     │                                                                                           │
│ • LangGraph bmc_iter   │                                                                                           │
├────────────────────────┴─────────────────────────────────────────────────┬────────────────────────────────────────┤
│ COST STRUCTURE                                                             │ REVENUE STREAMS                        │
│                                                                            │                                        │
│ Fixed (月次):                                                              │ 【サブスクリプション (主)】               │
│   Vultr VKE LAX (RisingWave shared): $241/月                              │   Free:       $0/月                    │
│   Cloudflare Workers: 従量 (現状ほぼ無料枠内)                              │   Starter:    $13/月 (~¥1,980)         │
│   Backblaze B2: ~$0.006/GB-month (BWA ゼロ egress)                        │   Developer:  $33/月 (~¥4,980)         │
│   Stripe: 2.9% + $0.30/transaction                                         │   Business:   $650/月 (~¥98,000)       │
│   Resend: $0 trial → $20/月 (50k emails、要 RESEND_API_KEY)               │   Enterprise: $6,700+/月 (custom)      │
│   RunPod 6000 Ada GPU: per ADR-2605010000                                  │                                        │
│                                                                            │ 【従量課金 (将来)】                      │
│ Unit Economics 目標:                                                        │   api_request 超過: $2.0/10K req       │
│   CAC < $30 / LTV > $500 (Starter avg) / LTV:CAC > 16x                   │   storage 超過: $10/GB-month           │
│   粗利率 86-94% (B2 BWA 原価 $0 + Vultr shared 按分)                      │   MCP tool call: $3.0/100 calls        │
│                                                                            │   Reasoning DL run: $5.00/run          │
│                                                                            │                                        │
│                                                                            │ 【JP 適格請求書 (補助)】                  │
│                                                                            │   T9007028460042 (etzhayyim)           │
│                                                                            │   JPY 課金 JP 顧客向け                  │
│                                                                            │                                        │
│                                                                            │ 【マーケットプレイス (将来)】              │
│                                                                            │   サードパーティ MCP tool 手数料          │
│                                                                            │   移行コンサル / professional services   │
└────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────┘
```

---

### 3. Lean Canvas — yatabase.etzhayyim.com

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ PROBLEM                      │ SOLUTION                 │ UNIQUE VALUE PROPOSITION          │
│                              │                          │                                   │
│ 1. Graph DB + object store   │ • RisingWave PG/SPARQL/  │ 「AI 時代の開発者が最初に選ぶ       │
│    + AI (MCP) を別々に契約   │   Cypher + B2 object +   │  graph database cloud」            │
│    すると請求 3〜5 本、       │   /mcp — 1 API key       │                                   │
│    latency 増、複雑性増大    │   で統合                 │ MCP-native × AT Protocol DID ×     │
│                              │                          │ アノニマス signup の三位一体        │
│ 2. Supabase/Neo4j AuraDB     │ • Starter $13/月:        │                                   │
│    は graph 機能が弱いか     │   Supabase Pro の半値    │ ターゲット:                         │
│    高い (AuraDB $65+)        │                          │ AI-native devs が MCP 製品を        │
│                              │ • アノニマス signup:     │ 作る時の「最初の DB 選択肢」         │
│ 3. MCP サーバーを自分で      │   email/CC 不要、即 start│                                   │
│    ホストする手間 (Cursor     │                          │                                   │
│    / Claude Desktop 連携)    │ • AT Protocol DID auth   │                                   │
│                              │                          │                                   │
├──────────────────────────────┴──────────────────────────┤                                   │
│ EXISTING ALTERNATIVES        │ KEY METRICS              ├───────────────────────────────────┤
│                              │                          │ UNFAIR ADVANTAGE                  │
│ • Supabase Pro $25/月        │ Week 1:                  │                                   │
│   (Postgres, MCP サポート弱) │   新規テナント数/週       │ • B2 BWA ゼロ egress               │
│ • Neo4j AuraDB Free→$65/月  │   (目標: HN cron 経由 5+) │   (競合は egress コストで値引き不可) │
│ • Hasura Cloud $99+/月       │                          │ • Murakumo 自己ホスト LLM          │
│ • PlanetScale $0→$39         │ Month 1:                 │   (AI agent 運営コストほぼ $0)      │
│ • 自前 Docker Compose        │   MRR / paid tenant 数   │ • etzhayyim platform 既存インフラ共用    │
│   (ops 負担重)               │   free→paid 転換率       │   (RisingWave shared $241/月は      │
│                              │                          │   他製品と按分)                     │
│                              │ Month 3:                 │ • AT Protocol DID mesh:            │
│                              │   CAC 回収月数           │   lawfirm/shinshi/animeka テナント  │
│                              │   NPS                    │   が内部顧客として自動転換           │
│                              │   MRR $2,500 target      │                                   │
├──────────────────────────────┴──────────────────────────┴───────────────────────────────────┤
│ CHANNELS                     │ COST STRUCTURE            │ REVENUE STREAMS                  │
│                              │                           │                                  │
│ • HN Algolia cron (自律)     │ Fixed: $241/月 (Vultr)    │ Starter $13 → Developer $33 →    │
│ • GitHub stargazers cron (自律)│ Variable: Stripe 2.9%+ │ Business $650                    │
│ • Organic SEO + /comparison  │ People: ops なし (AI 自律)│                                  │
│ • MCP listings (manual)      │                           │ Month 3 target: MRR $2,500       │
│ • Product Hunt (P10)         │ Target gross margin: 90%+ │ (200 paid tenants × avg $12.50)  │
└──────────────────────────────┴───────────────────────────┴──────────────────────────────────┘
```

---

### 4. Lean 実験ロードマップ

#### Sprint 0 (已完了) — v0.1.0 基盤 (P1-P46)

- Stripe billing LIVE (3 products: Starter/Developer/Business)
- per-tenant RW DB isolation (`yata_<sha256(did)[:16]>`)
- 4 AI agents 稼働 (sakamoto/nishino/tanaka/chikada)
- HN + GitHub stargazers 自律リード獲得 cron
- LangGraph `bmc_iteration` cron 毎日 07:00 UTC

#### Sprint 1 (2026-05-19 〜 06-15): MCP listing + 最初の有償テナント

**Riskiest Assumption**: Cursor / Claude Desktop の MCP listing がサインアップを 5x 加速する (仮説 H1)

**アクション**:
- Cursor MCP marketplace + Claude Desktop への yatabase MCP 登録 (手動、~2h)
- `/comparison` ページ強化 (Supabase / Neo4j AuraDB / Hasura と機能/価格比較表)
- 無料トライアルの day-7 retention hook: HTML welcome email (P45) 実装
- Anonymous signup → first paid plan の funnel 計測 (`vertex_audit_log_referrer_funnel` MV)

**判定基準**:
- `PASS`: MCP listing 経由 signup ≥ 25/週 (仮説 H1 threshold)
- `PASS`: 最初の paid Stripe テナント ≥ 1 件 (仮説 H4 baseline)
- `FAIL`: listing 登録後 2 週で signup < 5/週 → channel 戦略を見直し

#### Sprint 2 (2026-06-15 〜 07-15): MRR $500 + free→paid 転換率 5%

**Riskiest Assumption**: $13 Starter は free tier から 30 日以内に 5% が有償転換する (仮説 H4)

**アクション**:
- in-app conversion CTA を signup D+14 / D+30 に表示
- nishino agent の cold outreach batch を Japan SaaS 向けに拡張
- `/quickstart` 改善 (comparison ページ → quickstart CTR 計測、仮説 H2)

**判定基準**:
- `PASS`: MRR $500 (≈ 40 paid tenants × avg $12.50)
- `PASS`: free→paid 30d 転換率 ≥ 5% (仮説 H4)
- `FAIL`: 転換率 < 2% → pricing / onboarding を見直し

#### Sprint 3 (2026-07-15 〜 09-01): MRR $2,500 + Product Hunt launch

**Riskiest Assumption**: Product Hunt 掲載で 500+ upvotes → 1,000+ signup wave

**アクション**:
- Product Hunt launch (P10 ロードマップ)
- Cypher 言語アダプタ MVP (P6 ロードマップ、Neo4j 移行ターゲット)
- Resend 本番接続 + email sequence 自動化 (RESEND_API_KEY wire)
- Enterprise tier の日本語 DPA テンプレート作成

**判定基準**:
- `PASS`: MRR $2,500 (≈ 200 paid tenants)
- `PASS`: NPS ≥ +30
- `FAIL` → Business tier ($650) の先行販売に戦略転換

---

### 5. Lean 仮説 5 本 (BMC シード H1-H5 との対応)

| 仮説 | BMC ブロック | 命題 | 閾値 | 期限 |
|---|---|---|---|---|
| H1-cursor-mcp-listing | channels | Cursor/Claude Desktop MCP listing が signup を 5x 加速する | 25 signup/週 (MCP referer) | 2026-06-30 |
| H2-comparison-quickstart-ctr | valuePropositions | /comparison 経由ユーザーは /docs 比 2x 高い /quickstart CTR | CTR ratio ≥ 2.0 | 2026-06-30 |
| H3-html-welcome-day7-activation | customerRelationships | HTML welcome email で day-7 API calls が 1.5x 増加 | day7 avg ≥ 150 req | 2026-06-30 |
| H4-starter-13-conversion | revenueStreams | 30 日以内に free→paid 転換率 ≥ 5% | 0.05 (n ≥ 50) | 2026-06-30 |
| H5-anonymous-signup-velocity | customerSegments | アノニマス signup ユーザーは email 登録ユーザー比 2x 速く有償転換 | median_days ratio ≤ 0.5 | 2026-06-30 |

仮説のアクティベーションと計測は `bmc_iteration` LangGraph が毎朝 07:00 UTC に自律実行する。operator は Studio → BMC admin pane で H1 を `activate` する。

---

### 6. KPI ダッシュボード

| KPI | 計測頻度 | 2026-06-15 Target | 2026-09-01 Target |
|---|---|---|---|
| Weekly new signups | 週次 | 50 | 200 |
| Paid tenants (累積) | 週次 | 10 | 200 |
| MRR (USD) | 週次 | $500 | $2,500 |
| Free→paid 30d 転換率 | スプリント末 | 5% | 10% |
| NPS | 月次 | N/A (n < 10) | +30 |
| CAC (USD) | スプリント末 | < $30 | < $20 |
| LTV:CAC | 四半期 | > 5x | > 16x |
| H1 MCP signup/週 | 週次 | 25 (threshold) | 100 |
| bmc_iteration daily run | 日次 | 成功 100% | 成功 100% |

KPI は `projector.update_status` (ADR-2605130000) で毎スプリント末に記録する。

---

### 7. Projector 初期状態

```
# セッション開始時に projector.create_project を呼ぶ
projector.create_project {
  name: "yatabase.etzhayyim.com — MCP listing + 最初の有償テナント",
  orgId: "default",
  description: "Sprint 1: Cursor/Claude Desktop MCP 登録 + /comparison 強化 + free→paid 5% (〜2026-06-15)",
  targetDate: "2026-06-15"
}
```

**初期ブロッカー**:
- `RESEND_API_KEY` 未設定 (Resend 本番接続ブロック) — severity: medium / type: technical
- MCP listing 手動登録未実施 (Cursor / Claude Desktop) — severity: high / type: external
- `STRIPE_WEBHOOK_SECRET` 本番値 確認要 — severity: medium / type: technical

---

## Consequences

### 即時アクション (今週)

1. **MCP listing 登録** (手動 ~2h): Cursor marketplace + Claude Desktop `/integrations` に yatabase を登録
2. **H1 仮説 activate**: Studio → BMC admin pane で H1-cursor-mcp-listing を `active` に変更
3. **Resend 接続**: `RESEND_API_KEY` を macOS Keychain `etzhayyim.resend/RESEND_API_KEY` に追加 + Wrangler secret set
4. **projector.create_project**: 上記 §7 の初期プロジェクトと 3 ブロッカーを登録

### トレードオフ

- **自律運営 vs 機能開発**: AI エージェント (sakamoto/nishino) が日次運営を担うため、エンジニアリング介入は sprint 機能開発時のみ。通常稼働コストはほぼ $0 追加。
- **USD 主体 vs JPY 主体**: 国際市場はドル建て (AI-native devs)、日本 SaaS は円建て適格請求書。Stripe の multi-currency で両対応済み。
- **Free tier コスト**: free テナントも RisingWave DB を 1 個消費 → $241/月 の shared cluster に全テナントが乗る。Free テナント過多で超過すると cluster 増設が必要 (trigger: tenant 数 > 500)。

### 制約

- PII は ADR-0018 Tier 3 (Preferences) に隔離。billing テナント情報は `signal:v1:` field-encrypt
- yatabase billing actor が Stripe API を呼ぶ場合は `com.etzhayyim.apps.stripe.*` XRPC 経由
- B2 egress は BWA ゼロだが Cloudflare egress は従量 → CDN cache 率を 95%+ に維持

## Alternatives Considered

| 案 | 却下理由 |
|---|---|
| lawfirm/shinshi/animeka と同等の人的リソース投入 | yatabase は自律 AI 運営が成立している。人的介入を増やすと ROI が低下 |
| USD のみ (JPY 不要) | Japan SaaS startups は適格請求書要求が強い。JPY 対応は差別化要因 |
| Enterprise-first (SMB skip) | AI-native devs は個人 / 小チームが多い。Product-Led Growth が最速の実証経路 |
| MCP listing なし (inbound SEO のみ) | MCP エコシステムは現在急拡大中。listing タイミングを逃すと競合が先行する |

## References

- `90-docs/adr/2605080000-yatabase-yata-retail-cloud.md` — 製品設計・価格・ロードマップ全容
- `70-tools/scripts/yatabase-bmc-seed.sh` — BMC bootstrap + H1-H5 仮説 API seed スクリプト
- `70-tools/scripts/yatabase-customer-journey.mjs` — カスタマージャーニー計測
- `70-tools/scripts/yatabase-smoke.mjs` — デプロイ後スモークテスト
- `deps.toml [platform.products.yatabase]` — 製品 SSoT (pricing display, plan-quota, invoice)
- `deps.toml [etzhayyim_agent.product_portfolio.yatabase]` — ポートフォリオ位置付け
- `60-apps/etzhayyim-project-yatabase/CLAUDE.md` — 実装詳細
- ADR-2605130000 — projector MCP tools
- ADR-2605180000 — lawfirm 選択と集中 (ポートフォリオ親 ADR)
