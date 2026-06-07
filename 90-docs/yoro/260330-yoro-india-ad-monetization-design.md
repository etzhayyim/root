# India Ad Monetization Design — yoro.etzhayyim.com

**Date**: 2026-03-30
**Status**: `[DESIGN]`

## Problem

Google AdSense 単体でのインド CPM は $0.30-$1.50。US/UK の 5-10 分の 1。India をメインターゲットにする場合、AdSense 単体では収益の 30-60% を取りこぼす。

## Solution: Multi-Provider Header Bidding Stack

AdSense をベースラインとして維持しつつ、Header Bidding (AdPushup/Ezoic) で Google AdX demand を追加。Media.net (contextual) + InMobi (mobile) で補完。

### Provider Stack

| Priority | Provider | Role | India CPM (USD) | Registration |
|---|---|---|---|---|
| **1** | **AdPushup** (Delhi HQ) | Header Bidding + AdX access | $0.60-$2.50 | `adpushup@etzhayyim.com` |
| **2** | **Ezoic** (US, India-optimized) | AI layout optimization + AdX | $0.80-$3.00 | `ezoic@etzhayyim.com` |
| **3** | **Media.net** (Mumbai HQ) | Contextual ads (Yahoo/Bing demand) | $0.50-$2.00 | `medianet@etzhayyim.com` |
| **4** | **Google AdSense** (current) | Baseline fill rate 95-99% | $0.30-$1.50 | existing `ca-pub-8017914559680125` |

**Expected combined RPM**: $1.00-$4.00 (vs $0.30-$1.50 AdSense-only, 2-3x uplift)

### Registration Plan

DID-based email: `{provider}@etzhayyim.com` → mailer.etzhayyim.com で受信。

| Step | Provider | Email DID | URL | Requirements |
|---|---|---|---|---|
| 1 | AdPushup | `did:web:mailer.etzhayyim.com:adpushup` | https://www.adpushup.com/signup | Website URL, monthly pageviews, current revenue |
| 2 | Ezoic | `did:web:mailer.etzhayyim.com:ezoic` | https://www.ezoic.com/signup | Website URL, Google Analytics access |
| 3 | Media.net | `did:web:mailer.etzhayyim.com:medianet` | https://www.media.net/signup | Website URL, English content, traffic stats |

### Integration Architecture

```
Browser (India user)
  → CookieConsent.svelte (DPDPA 2023 consent)
  → AdSlot.svelte (multi-provider)
      ├─ AdPushup/Ezoic Header Bidding (highest bid wins)
      │   ├─ Google AdX demand
      │   ├─ AdPushup demand partners
      │   └─ Ezoic AI-optimized demand
      ├─ Media.net contextual (non-competing, parallel)
      └─ Google AdSense (fallback, highest fill rate)
```

### AdSlot.svelte Refactor

Current: AdSense-only (`adsbygoogle.push()`).
Target: Multi-provider with priority cascade.

```
Phase 1: AdPushup integration (tag-based, minimal code change)
Phase 2: Ezoic integration (site-level optimization)
Phase 3: Media.net contextual (sidebar/in-content)
```

AdPushup と Ezoic は tag-based integration — `app.html` に script tag を追加し、既存 AdSense slot を wrap する形で動作。AdSlot.svelte の大幅変更は不要。

### India-Specific Considerations

| Factor | Impact | Mitigation |
|---|---|---|
| 75%+ mobile traffic | Mobile-first ad formats essential | AdSlot `format="auto"` (responsive, current) |
| DPDPA 2023 | Consent required for personalized ads | CookieConsent.svelte (existing) + contextual fallback (Media.net) |
| Tier-1 vs Tier-2/3 city CPM gap (2-3x) | Tier-1 optimization | AdPushup geo-targeting |
| Hindi/regional < English CPM (30-50%) | English content priority | yoro は English-first UI |
| SPA route changes | Ad re-render needed | AdSlot `onMount` re-push (existing) |

### CookieConsent.svelte Update

DPDPA 2023 (India) 対応として、Cookie 同意バナーのテキストを多言語化:
- Japanese (current)
- English (India primary)
- Hindi (India secondary)

Consent state は `localStorage('yoro-cookie-consent')` で統一管理 (変更不要)。

### Revenue Projection (India 100K monthly pageviews)

| Scenario | RPM (USD) | Monthly Revenue (USD) |
|---|---|---|
| AdSense only (current) | $0.50 | $50 |
| AdSense + AdPushup | $1.20 | $120 |
| AdSense + AdPushup + Ezoic | $1.80 | $180 |
| Full stack (all 4) | $2.50 | $250 |

### Implementation Phases

#### Phase 1: Account Registration (Week 1)

1. Create DID emails via mailer.etzhayyim.com
   - `kotodama.DIDCreate("adpushup", {displayName: "AdPushup", description: "Ad monetization provider"})`
   - `kotodama.DIDCreate("ezoic", {displayName: "Ezoic", description: "Ad optimization provider"})`
   - `kotodama.DIDCreate("medianet", {displayName: "Media.net", description: "Contextual ad provider"})`
2. Register at each provider with `{name}@etzhayyim.com` email
3. Submit yoro.etzhayyim.com for review
4. Await approval (AdPushup: 2-5 days, Ezoic: 1-3 days, Media.net: 5-10 days)

#### Phase 2: AdPushup Integration (Week 2-3)

1. AdPushup dashboard でad layout configuration
2. `app.html` に AdPushup header bidding script 追加
3. AdPushup が既存 AdSense slot を自動 wrap (AdX demand を追加)
4. A/B テストで最適配置を検証

#### Phase 3: Ezoic Integration (Week 3-4)

1. Ezoic nameserver integration または Cloudflare plugin
   - yoro は CF Workers — Ezoic Cloudflare integration を使用
2. Ezoic AI が ad placement/size/density を自動最適化
3. AdSense + AdPushup + Ezoic の competition で最高 CPM を自動選択

#### Phase 4: Media.net Contextual (Week 4-5)

1. Media.net ad units を in-content / sidebar に配置
2. `AdSlot.svelte` に `provider` prop 追加 (optional)
3. Cookie 拒否時でも contextual ad を表示可能 (DPDPA compliant)

#### Phase 5: Monitoring & Optimization (Ongoing)

1. RPM/CPM tracking per provider per geo
2. India Tier-1 vs Tier-2/3 performance 分析
3. Ad density 最適化 (UX vs revenue balance)
