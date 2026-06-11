---
id: adr-2605072300-open-source-cloud-business-model
title: "ADR-2605072300: Open-Source Core + Cloud SaaS Business Model (Kotoba/Datomic Pattern)"
status: active
doc_type: adr
topic: open-source-cloud-business-model
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - open-* actors licensing and distribution model
  - kyber ERP commercialization strategy
  - etzhayyim Cloud pricing and metering architecture
  - OSS go-to-market strategy
related:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2604282300
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0018-pii-tier3-cohort-first
supersedes: []
superseded_by: []
---

# ADR-2605072300: Open-Source Core + Cloud SaaS Business Model

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

`etzhayyim-project-open-*` (20+ actors) と `etzhayyim-project-open-kyber` (ERP) は Apache-2.0
ライセンスで公開済みだが、正式な課金モデル・営業戦略・メーターアーキテクチャが未定義。

Kotoba/Datomic / Grafana / HashiCorp が実証した **OSS Core + Managed Cloud** パターンを
etzhayyim のアーキテクチャ (Cloudflare Workers + Kotoba/Datomic + Zeebe + AT Protocol) に適用し、
Developer Adoption → Cloud Conversion → Enterprise の3段階で収益化する。

既存 README (`open-kyber`) には「Fork this repo to run your own instance; the deployed SaaS
at kyber.etzhayyim.com is a managed tenancy of this codebase.」とすでに方向性が示されているが、
価格・メーター・セールスモーションを正式に決定する必要がある。

## Decision

### 1. ライセンス方針

| プロダクト | ライセンス | 根拠 |
|---|---|---|
| `open-*` actors (全 20+ actor) | Apache-2.0 | 公開データ基盤は完全 OSS が普及速度最大 |
| `open-kyber` ERP core | Apache-2.0 | セルフホスト可能・fork 奨励 |
| `kyber.etzhayyim.com` managed SaaS | Proprietary (closed) | クラウド付加価値部分 (billing/multi-tenant mgmt) |
| Murakumo LLM fleet | Proprietary | 推論インフラは競争優位の核心 |

BSL (Business Source License) は採用しない。AT Protocol エコシステムとの相性および
「データポータビリティ保証」ブランドと矛盾するため。

### 2. 製品ティア構成

```
┌─────────────────────────────────────────────────────────┐
│  Enterprise (T3)                                         │
│  オンプレ / プライベートクラウド + SLA 99.9% + 専任CSM   │
│  ¥5,000,000+/year カスタム契約                          │
├─────────────────────────────────────────────────────────┤
│  etzhayyim Cloud (T2) — 従量課金                             │
│  managed kyber + open-* hosted + Murakumo LLM           │
│  Developer(無料) → Starter → Growth → Scale             │
├─────────────────────────────────────────────────────────┤
│  OSS Self-Host (T1) — Apache-2.0                        │
│  open-kyber / open-banking / open-* 全 actor            │
│  要件: Cloudflare Workers + Kotoba/Datomic + Zeebe          │
└─────────────────────────────────────────────────────────┘
```

### 3. 従量課金メーター設計

アーキテクチャのコンポーネントが課金単位と 1:1 対応する:

| メーター | 単価 | 計測箇所 |
|---|---|---|
| XRPC リクエスト | ¥50 / 100万 req | CF Worker `request` event |
| Kotoba/Datomic ストリーム行 | ¥100 / 100万 rows inserted | `vertex_*` INSERT count |
| Murakumo LLM トークン | ¥200 / 100万 tokens | `resolveModelId()` 呼び出しラッパー |
| Zeebe プロセス実行 | ¥500 / 1000 instances | Zeebe process instance create |
| PDS レコード保管 | ¥100 / GB / 月 | `vertex_repo_record` byte sum |
| Hyperdrive 書き込み | ¥30 / 100万 writes | RW INSERT audit log |

**無料枠 (Developer Plan)**:
- XRPC 500万 req/月
- LLM 10万 tokens/月
- Zeebe 1000 instances/月
- PDS 1 GB
- クレジットカード登録不要

メーター実装: `vertex_kyber_usage_meter` テーブル (actor_did, org_did, meter_type,
period_month, count) + `mv_kyber_monthly_usage` ストリーミング MV → Stripe Meter API
webhook 月次送信。

### 4. kyber ERP 固有の月額プラン

freee (¥2,380〜) / MoneyForward Cloud (¥2,980〜) と直接競合する価格帯:

| Plan | 月額 | ユーザー | 取引数/月 | 機能 |
|---|---|---|---|---|
| Free | ¥0 | 1 | 100 | GL + AR/AP |
| Starter | ¥3,800 | 5 | 5,000 | + HR + 在庫 |
| Growth | ¥12,000 | 20 | 50,000 | + 調達 + 固定資産 + IFRS/JP-GAAP |
| Scale | ¥38,000 | 無制限 | 無制限 | + APQC 分析 + OCEL 監査証跡 |
| Enterprise | カスタム | — | — | オンプレ + SLA + ADR-0018 PII 分離 |

### 5. 競合ポジショニング

```
                  高機能・高価格
                      │
     SAP Business One │  Oracle NetSuite
                      │
OSS ──────────────────┼──────────────── Closed
(Apache-2.0)          │
 open-kyber ──────► kyber.etzhayyim.com
                      │
     freee            │  MoneyForward
                      │
                  低機能・低価格
```

**唯一の差別化軸 — AT Protocol ネイティブ**:
データポータビリティが設計上保証されている「脱出できる ERP」。
`etzhayyim export --format atproto-car` で全データを可搬形式に即時エクスポート可能。

### 6. Go-to-Market 3フェーズ

#### Phase 1: OSS Developer Adoption (2026 Q2〜Q3)

ターゲット: 日本のスタートアップ開発者、AT Protocol エコシステム参加者

- GitHub `etzhayyim/etzhayyim-project-open-kyber` でのアクティブ発信
  (Zenn, dev.to, Bluesky Technical)
- `etzhayyim deploy` 1コマンドセルフホスト手順の整備
- Bluesky 上で etzhayyim actor がリアルタイム動作するデモ (分散 ERP as AT agent)
- KPI: GitHub Stars 500、self-host installs 50

#### Phase 2: Cloud Conversion (2026 Q4〜2027 Q2)

ターゲット: インフラ管理コストを削減したい self-host ユーザー

- `etzhayyim migrate --to cloud` による 1コマンド移行ツール
- 30日間フル機能トライアル (クレジットカード不要)
- XRPC 上限到達時のインアプリ通知 + アップグレード CTA
- KPI: 有償テナント 20社、MRR ¥250,000

#### Phase 3: Enterprise + Vertical Expansion (2027 Q3〜)

既存 open-* actors を布石にした垂直統合:

| Vertical | 対応 actor | 追加価値 |
|---|---|---|
| 中堅製造業 | open-smartphone-{soc,bom,ems} | APQC SCM + OCEL 監査証跡 |
| 金融・証券 | open-banking, open-swift | JP-GAAP 連結、freee/MF 連携 |
| 医療・製薬 | open-seiyaku | 薬事コンプライアンス自動チェック |
| 法律事務所 | lawfirm actor | 証拠保全 E2E (Signal vault ADR-0074) |
| 農業協同組合 | nokyo actor | JA 向け営農 ERP (全国 600 JA) |

- KPI: ARR ¥100M (2028 Q1)、Enterprise 契約 10社

### 7. 収益シミュレーション (保守的)

| 期間 | ARR | 主要 KPI |
|---|---|---|
| 2026 Q3 | — | Stars 500, installs 50 |
| 2026 Q4 | ¥3M | Cloud 20社 × avg ¥12,500/月 |
| 2027 Q2 | ¥30M | Cloud 100社 + Enterprise 3社 |
| 2028 Q1 | ¥100M | Cloud 300社 + Vertical 拡張 5業種 |

## Consequences

### 必要な実装 (未対応)

1. **`vertex_kyber_billing_tenant`** + **`vertex_kyber_usage_meter`** テーブル新設
   → migration `20260508_kyber_billing.ts`
2. **Stripe Meter API** 統合 — CF Worker が月次 usage を Stripe に送信する webhook
3. **セルフサービスサインアップ** — `yoro.etzhayyim.com` signup → kyber テナント自動プロビジョニング
4. **`etzhayyim migrate --to cloud`** コマンド実装 (`70-tools/etzhayyim/`)
5. **OSS ライセンスヘッダー整備** — 全 `open-*` プロジェクトに Apache-2.0 ヘッダー追加

### トレードオフ

- **Apache-2.0 (選択) vs BSL**: Apache-2.0 は競合クラウドによる hosted 再販リスクがあるが、
  AT Protocol エコシステムの信頼とデータポータビリティブランドを優先する
- **Usage-based (選択) vs Seat-based**: 小チームほど有利で PLG と相性が良い。
  ただし収益予測が難しく、Free ユーザーが大量 LLM tokens を消費するリスクあり →
  Free 枠上限で Murakumo を throttle

### 制約

- Enterprise の PII 分離要件は ADR-0018 (PII Tier 3 cohort-first) に準拠
- オンプレ版でも Vault Zero-Knowledge Invariant (CLAUDE.md root rule) は維持
- Stripe 連携は `com.etzhayyim.apps.stripe.*` XRPC として実装 (直接 SDK call 禁止)

## Alternatives Considered

| 案 | 却下理由 |
|---|---|
| BSL (Business Source License) | AT Protocol コミュニティとの相性 ✗、fork 奨励ブランドと矛盾 |
| Seat-based のみ | PLG に不向き。SMB の初期採用障壁が高い |
| Freemium なし (有償のみ) | Developer Adoption フェーズをスキップすることになり OSS 普及が遅延 |
| Enterprise のみ (SMB 無視) | 日本の中小企業 380万社という TAM を無視することになる |

## References

- `60-apps/etzhayyim-project-open-kyber/README.md` — 既存 OSS宣言
- `deps.toml [[projects]] name="open-banking"` — Apache-2.0 公開済み参考実装
- Kotoba/Datomic Cloud pricing model (参考: kotoba.com/pricing)
- Grafana OSS → Grafana Cloud 移行パターン (参考)
- ADR-0018: PII Tier 3 Cohort-First (Enterprise PII 分離)
- ADR-0036: Worker-direct Hyperdrive Persistence (メーター実装基盤)
- ADR-0074: ERC725 Root Identity (Enterprise Vault 統合)
