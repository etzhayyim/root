---
id: adr-0084-yoro-ads-integration
title: "ADR-0039: yoro Ads Integration — Placement Registry + House-Ad Fallback"
status: active
doc_type: adr
topic: yoro-ads
authoritative: true
last_verified: 2026-04-20
related: []
supersedes: []
superseded_by: []
---

# ADR-0039: yoro Ads Integration — Placement Registry + House-Ad Fallback

- Status: active
- Date: 2026-04-20
- Scope: `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/`
- Supersedes: (prior ad-hoc `<AdSlot slot="AUTO" />` usage)

## Context

yoro は既に 3 つのアドネットワーク script を app.html に宣言していた (AdSense active, AdPushup / Ezoic / Media.net は approval 待ちで comment out)。しかし 2026-04 時点で:

1. Feed 内に 1 箇所 `<AdSlot slot="AUTO" format="auto" />` があるだけで、`"AUTO"` は実 AdSense ad unit id ではない
2. Placement ごとの slot id / format / min-height / frequency を管理する SSoT が無い
3. Consent declined 時に ad 枠が空になり layout が崩れる
4. Sidebar / post-detail / profile / search など他の placement 実装無し
5. House ad (自社広告) fallback 無し

この ADR は yoro の広告統合をシンプルに最低限の形に設計する。AI Agent-First 世界観と AT Protocol 親和性は保ちつつ、まず AdSense 系の placement を正しく敷く。

## Decision

### 1. Placement-Driven Slot Registry (SSoT)

`src/lib/ads/config.ts` を SSoT とし、7 placement を定義:

| Placement | 用途 | Format | Min height |
|---|---|---|---|
| `feed-inline` | `/` vibes feed の投稿間 (5 post ごと) | `fluid` | 120 |
| `feed-top` | guest / cold load 時の feed 先頭 | `horizontal` | 90 |
| `post-detail` | `/profile/[handle]/post/[rkey]` 本文と replies の間 | `rectangle` | 250 |
| `post-thread` | thread 内 reply 間 | `fluid` | 120 |
| `profile-header` | `/profile/[handle]` ActorHero 直下 | `horizontal` | 90 |
| `search-results` | `/search` 結果一覧 | `auto` | 120 |
| `sidebar` | デスクトップ右 rail (未配置) | `vertical` | 600 |

各 placement の `id` は初期 `UNPROVISIONED` sentinel。AdSense 管理画面で ad unit を作成したら config に貼る。

### 2. `AdSlot.svelte` の責務

- `placement` prop を受け、`AD_SLOTS[placement]` から slot id / format / label / minHeight を解決
- `IntersectionObserver` で viewport 200px 手前まで来た時に lazy-load (描画コスト削減)
- Consent declined または `UNPROVISIONED` の場合は **house ad fallback** を描画 (etzhayyim.com 自己宣伝)
- Media.net 経路は cookie consent 不要 (DPDPA 準拠、contextual)
- `<div class="ad-label">Sponsored</div>` を常時表示 (transparency; AdSense policy §Ad placement)

### 3. Network Activation Flow

| Network | Status | Activate after |
|---|---|---|
| AdSense | **pending (審査中)** | script は `app.html` で load 済 (verification crawler 用)、`providers.adsense = false` のため runtime push はしない。承認後に flip |
| AdPushup | pending | AdSense approval 後に有効化 (header bidding wrapper) |
| Media.net | pending | approval 後 script ロード + `providers.medianet = true` |
| Ezoic | pending | approval 後 gatekeeper + sa.min.js 解除 |
| ExoClick | **active (primary)** | AdSense 審査中の primary fill network。`EXOCLICK_ZONES` に placement → zone id を記入。`a.magsrv.com/ad-provider.js` は `AdSlot` が需要時に動的ロード |

### Current Runtime State (2026-04-20)

- `providers.adsense = false` / `providers.exoclick = true` → AdSlot は ExoClick path を使用
- **ExoClick site**: `yoro.etzhayyim.com` (site id 1094566), category Entertainment & Lifestyle
- **Provisioned zones** (all banner, ad_type=2 / media_type=2):

| Placement | Zone id | Size |
|---|---|---|
| feed-inline | 5905260 | 300x250 |
| feed-top | 5905262 | 728x90 |
| post-detail | 5905264 | 300x250 |
| post-thread | 5905266 | 300x250 |
| profile-header | 5905268 | 728x90 |
| search-results | 5905270 | 300x250 |
| sidebar | 5905272 | 160x600 |

- API token is stored in macOS Keychain: `security find-generic-password -s "etzhayyim.exoclick" -a "API_KEY" -w`
- AdSense approval が降りた後は `providers.adsense = true` に flip するだけで AdSense が primary になる (ExoClick と併用する場合は placement 単位で排他 — 同一 page に AdSense + ExoClick は content policy 抵触リスク)

AdPushup は AdSense と header bidding で共存 (同じ `<ins class="adsbygoogle">` を wrap する)、Media.net は contextual で cookie 不要、Ezoic は AI optimization layer。どれも AdSense を置き換えるのでは無く重ねる構成。

### 4. Consent 連携

`CookieConsent.svelte` の `yoro-cookie-consent` localStorage key が唯一の source。`hasAdConsent()` helper を `$lib/ads/config.ts` が export し、AdSlot + CookieConsent 両者が参照。Declined 時は AdSense request せず house-ad を出す (枠が空白にならない = layout shift 防止)。

### 5. AI Agent-First 整合性

- 広告 creative は第三者の AdSense ネットワーク側にあるので yoro の AT Repo / federation には **一切** 流れない (ADR-0036 Repo Record Minimization 準拠、そもそも record 化していない)
- Impression / click 等の個人広告 metrics も yoro 側で保持しない (Google が所有)
- 将来の 1st-party sponsored post (advectors project) は別 ADR で扱う。advectors は `com.etzhayyim.apps.advectors.*` lexicon で federable sponsored post を出す設計の余地を残すが、本 ADR では対象外

### 6. Shannon 観点

Placement registry は 1 箇所の config 変更で全 slot に波及 (O(1) change)、ad-hoc `slot="AUTO"` 散在だと O(N) で drift 不可避。house-ad fallback は consent declined user に対しても inventory の自己利用を 100% 取り戻す (η 改善)。

## Consequences

### 🟢 Good

- Slot id を 1 箇所で管理、AdSense 管理画面と 1:1 対応
- Consent declined でも layout が崩れない (house ad fallback)
- Lazy-load で初期ページロードの広告 request 回避 (LCP / CLS 改善)
- Placement ごとに最適な format / min-height を宣言的に設定
- AI Agent-First / Repo Minimization 原則を維持 (広告は Repo 外)
- 新 network 追加は `providers` フラグと script タグ解除だけ

### 🟡 Trade-off

- Slot id 未 provision の間は house-ad しか出ない (= まだ revenue ゼロ)。AdSense 側で ad unit を作って config に貼る運用 step が必要
- `post-thread` / `search-results` / `sidebar` / `feed-top` は実装済みだがまだ UI に差し込まれていない (本 ADR では feed-inline / post-detail / profile-header のみ wire)

### 🔴 Risk

- AdSense policy 違反リスク — 1 page 上の ad unit 数、sensitive content 隣接禁止等。`post-detail` は本文と reply の境界に置いたので separation OK。feed-inline は `frequency = 5` で clustering 回避。監査必要
- Media.net / AdPushup / Ezoic は approval 必要。approval 前に flag を true にしない

## Implementation

| File | 変更 |
|---|---|
| `src/lib/ads/config.ts` | **new** — SSoT (slot registry + providers + house ad + consent helper) |
| `src/lib/components/AdSlot.svelte` | refactor — placement-driven, lazy-load, house-ad fallback, Sponsored label |
| `src/routes/+page.svelte` | `<AdSlot placement="feed-inline" />` に置換 |
| `src/routes/profile/[handle]/post/[rkey]/+page.svelte` | post 本文と replies の境界に `placement="post-detail"` を追加 |
| `src/routes/profile/[handle]/+page.svelte` | ActorHero 直下に `placement="profile-header"` を追加 |
| `src/app.html` | (変更なし) AdSense loader は既存、他 network は provision 後に activate |

## Sponsored Feed (Native Posts, Option A — federable)

2026-04-20 追記: feed-inline を iframe-based creative から **AT Record として発行する native sponsored post** に転換。ExoClick iframe は pool が空のときの fallback として残す。

### Decision

広告主アカウント (path-DID per campaign per ADR-0019) が **通常の `app.bsky.feed.post`** を投稿し、self-label `!ad` を付与する。投稿は firehose に乗って federate する。他 AppView は labeler 経由で `!ad` を除外可能 (Bluesky standard flow)。

ADR-0036 allowlist: `app.bsky.feed.post` は federable に含まれているため違反なし。Ad metadata (impression / click / campaign bid) は AT Repo に書かず **RisingWave direct** (ADR-0036 §graph-first write path)。

### Architecture

```
Advertiser DID ──app.bsky.feed.post (with !ad label)──→ PDS firehose ──→ 全 AppView
                                                                            │
                                                                            ├─→ yoro: loadSponsoredCandidates
                                                                            │     → rank per viewer → merge
                                                                            │     → 通常の post UI で render
                                                                            │     + "Sponsored" pill
                                                                            │
                                                                            └─→ other AppView: labeler で filter
```

### Components

| File | 役割 |
|---|---|
| `src/lib/ads/config.ts` | `SPONSORED_DIDS[]` (ad account pool) + `SPONSORED_RANK` knobs + `SPONSORED_LABEL = '!ad'` |
| `src/lib/ads/sponsored-feed.ts` | `loadSponsoredCandidates()` → 各 DID の最新 `!ad` post 取得 / `scoreCandidate()` / `mergeSponsored()` |
| `src/routes/+page.svelte` | `blendSponsored()` helper, feed 描画時に `sponsoredUris` set を参照して "Sponsored" pill 表示。既存 post UI を流用、新 component 不要 |

### Ranker (client-side heuristic v0)

```
score = 0.5 · (viewer follows advertiser)
      + 0.2 · (recent-liked author overlap)
      + 0.3 · 2^(-ageHours / halfLife)
```

- Threshold gate: `score < 0.15` なら挿入しない (低関連度の広告を無理に押し込まない)
- Frequency: organic 7 投稿ごとに 1 枠 (config で調整可)
- Session cap: `sessionStorage` で 1 セッション最大 5 impressions (ad stuffing 防止)
- Viewer follow graph は将来 yoro API から供給 (v0 では空 set → recency + like-overlap のみで採点)

### Fallback

- `SPONSORED_DIDS` 空 or 全 candidate が threshold 未満 → ExoClick AdSlot (feed-inline) を挿入 (既存 iframe path を継続利用)
- 両方同時挿入はしない (`sponsoredUris.size === 0` の条件で排他)

### Differences from AdSense/ExoClick iframe path

| 項目 | iframe creative | Native sponsored post |
|---|---|---|
| Transport | 3rd party JS | AT Repo + firehose |
| Personalization | AdSense cookie-based | viewer 側 client-side ranker (cookie 不要) |
| Revenue model | CPM / CPC via Google or ExoClick | 将来 advectors でオークション実装、v0 は未計装 |
| Federate? | No (iframe) | Yes (`app.bsky.feed.post` + `!ad` label) |
| UI | 矩形 creative | 通常 post UI + "Sponsored" pill |
| Filter | Cookie consent decline | Labeler で `!ad` 除外 |
| Ad click telemetry | 3rd party | RisingWave direct (将来 advectors backend) |

### User Control

- `!ad` label を購読 labeler で除外可能 (Bluesky 互換)
- Per-advertiser mute は Tier 3 Preferences に将来格納 (v0 未実装、"Why this ad?" link も stub)
- Frequency cap は sessionStorage (session 境界でリセット)

## A/B/C Delivery (2026-04-20)

### A — `post-sponsored.mjs` (CLI seeder) ✅

`70-tools/scripts/ads/post-sponsored.mjs` — `etzhayyim agent-token --lxm com.atproto.repo.createRecord` で 60s scoped JWT を mint し、任意 DID から `app.bsky.feed.post` を投稿 (self-label `!ad` + 任意 external embed)。pool に素の DID を seed して end-to-end 動作確認する用。

### B — `etzhayyim-project-ads` (clearing Worker) ✅

`60-apps/etzhayyim-project-ads/appview/ads-adsm4d5c/` に T3 TS Native Worker を scaffold:

| Path | 役割 |
|---|---|
| `magatama.jsonld` | DID `did:web:ads.etzhayyim.com`, nanoid `adsm4d5c`, performerType `service`, profile, governance |
| `src/app.ts` | 3 XRPC command (`createCampaign` / `postSponsored` / `listCampaigns`) |
| `wrangler.jsonc` | Stub (`etzhayyim deploy` で regenerate) |
| `CLAUDE.md` | project runbook + deploy flow |

Lexicons at `00-contracts/lexicons/com/etzhayyim/apps/ads/`:
- `createCampaign.json` — procedure → path-DID `did:web:ads.etzhayyim.com:campaign:{id}` を issue
- `postSponsored.json` — procedure → campaign DID で `app.bsky.feed.post` + `!ad` self-label を発行
- `listCampaigns.json` — query → caller-owned campaign 一覧

内部 collection (ADR-0036 § non-federable Tier 2):
- `com.etzhayyim.apps.ads.campaign` — campaign metadata (name / budget / advertiser)
- `com.etzhayyim.apps.ads.sponsoredPost` — post URI ↔ campaign linkage (analytics 用)

### C — `/ads/compose` (yoro UI) ✅

`60-apps/etzhayyim-project-yoro/.../svelte/src/routes/ads/compose/+page.svelte` — 3-step composer:

1. Campaign 作成 (name / description / advertiser / budget)
2. Campaign 選択 (既存 campaign の dropdown)
3. Sponsored post 投稿 (text + external embed URL/title/desc)

B の 3 XRPC を `atQuery` / `atProcedure` で叩く。Auth は yoro セッション (wproto token provider)。投稿後 URI を表示。全 post に `!ad` self-label が自動付与される。

## Follow-ups

1. Campaign DID を `SPONSORED_DIDS[]` に登録する運用フロー (手動 or `ads.listCampaigns` を yoro 起動時に fetch して動的注入)
2. advectors backend (別 project) — `com.etzhayyim.apps.advectors.listCandidates` (AppView-side auction + ML ranker) で client-side heuristic を置換
4. Ad click telemetry pipeline — click event → RisingWave direct (ADR-0036)
5. Per-advertiser mute — Tier 3 Preferences に格納、"Why this ad?" link を `/settings/ads` に接続
6. Labeler 対応 — yoro labeler が `!ad` を既知 label として登録、他 AppView もこれを購読すれば除外可能
7. AdSense 管理画面で各 placement に対応する ad unit を作成し `AD_SLOTS[*].id` を埋める
2. AdPushup / Media.net / Ezoic の approval を取り、script + `providers` flag を有効化
3. Sidebar placement を desktop layout に配置 (まだ yoro に desktop right rail 無し — `40-engine/svelte` の responsive grid 改修時に合わせて)
4. Feed-top / search-results / post-thread の配置決定
5. 1st-party sponsored post (advectors) 設計は別 ADR で

## References

- `60-apps/etzhayyim-project-advectors/PROJECT.jsonld` — 将来の 1st-party ad platform
- ADR-0036 Repo Record Minimization — 広告 metadata は Repo に書かない根拠
- `docs/260321-consent-gated-data-sharing-design.md` — cookie consent と personalized ads
