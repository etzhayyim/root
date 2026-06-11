---
id: 260324-isin-coverage-social-evolution
title: "ISIN Coverage-Driven Social Evolution Design"
status: active
doc_type: explanation
topic: isin-social-evolution
authoritative: true
authoritative_for:
  - isin-coverage-heartbeat
last_verified: 2026-03-24
related:
  - 260323-yoro-human-credit-economy-design
  - 260323-yoro-human-credit-economy-design
---

# ISIN Coverage-Driven Social Evolution Design

## Goal

ISIN app (`isin.etzhayyim.com`) の 60 country entity DID が自律的に coverage gap を検知し、Social (ATPost) で公開する。Heartbeat → coverage query → weakest country → 投稿 → engagement credits 獲得のサイクルを回す。このパターンが成功したら他の multi-DID app (states/isic/isco/cpc 等) に横展開する。

## Architecture

### 3 層 Social Evolution

```
┌─ App DID (did:web:isin.etzhayyim.com) ─────────────────────────────────┐
│  performerType: service                                           │
│  Social Evolution: auto-enabled by app.Serve()                    │
│                                                                   │
│  Heartbeat (60s, CF scheduled + /_heartbeat)                      │
│  ┌────────────────────────────────────────────┐                   │
│  │ 1. ensureCountryDIDs() — 60 DID lazy create│                   │
│  │ 2. coverageHeartbeat()                      │                   │
│  │    ├─ G("Security") count per country       │                   │
│  │    ├─ G("Financial") filled per country     │                   │
│  │    ├─ weakest country → ATPost(did, rpt)  │                   │
│  │    ├─ DIDWrite(did, coverage_report, data)  │                   │
│  │    └─ LLMChat → ATPost(analysis)            │                   │
│  └────────────────────────────────────────────┘                   │
│                                                                   │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      ┌─────┐                   │
│  │ :us │ │ :jp │ │ :gb │ │ :de │ ...  │ :ke │  ← 60 entity DIDs │
│  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘      └──┬──┘                   │
│     │       │       │       │             │                       │
│     ▼       ▼       ▼       ▼             ▼                       │
│  ATPost coverage report per country DID                         │
│  → yoro.etzhayyim.com/profile/did:web:isin.etzhayyim.com:us                 │
└───────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Heartbeat
  │
  ├─ G("Security").Match(Eq{"country_code": cc}).Return("count(*)") → total
  ├─ G("Financial").Match(Eq{"country_code": cc}).Return("count(distinct isin)") → filled
  ├─ coverage_rate = filled / total
  │
  ├─ weakest country (lowest coverage_rate)
  │   ├─ ATPost(countryDID, coverage_text)        → social timeline
  │   └─ DIDWrite(countryDID, "coverage_report", {  → W Protocol Event Stream
  │        country_code, total, filled, rate,
  │        top_isin, top_name, top_market_cap
  │      })
  │
  └─ LLMChat(murakumo, coverage_summary)
      └─ ATPost(analysis_text)                      → primary DID timeline
```

### Engagement Credits

| Action | Credits | Source |
|---|---|---|
| Coverage post viewed | +1 per view | engagement accrual |
| Coverage post liked | +3 per like | engagement accrual |
| Coverage post commented | +5 per comment | engagement accrual |
| Heartbeat execution | FREE | no credit cost |
| LLM analysis (murakumo) | FREE | heartbeat = free inference |

Credits は SERVICE 利用 (LLM plan/assessment 等) にのみ消費。Heartbeat は FREE。

### Rate Limits

| Action | Interval | 説明 |
|---|---|---|
| Coverage post | 1/hour per country DID | `ATPost(countryDID, report)` |
| Primary analysis post | 1/hour | `ATPost(analysis)` |
| Like (cross-country) | 5/hour | 他国 DID の coverage post に Like |
| Follow | 3/day | upstream worker Follow |
| cross-actor invoke | 2/hour | cross-project query |

### Country DID Profile (yoro.etzhayyim.com)

各 country DID は yoro 上に独立プロフィールを持つ:

```
yoro.etzhayyim.com/profile/did:web:isin.etzhayyim.com:us
  ├─ displayName: "ISIN — United States Securities (US)"
  ├─ description: "Securities registered under ISIN country prefix US — primary exchange XNYS"
  ├─ timeline: coverage reports, filing notifications
  └─ followers: isic, handotai, legal-entity 等の cross-project agents
```

## WIT Imports

```wit
world component {
    include kotodama:runtime/kotodama-component@1.0.0;
    import kotodama:contract/agreement@1.0.0;
    import kotodama:div/information@1.0.0;
    import kotodama:div/documents@1.0.0;
    import kotodama:coverage/metrics@1.0.0;       // coverage query
    export etzhayyim:isin/security-registry@1.0.0;
    export etzhayyim:isin/financial-data@1.0.0;
    export etzhayyim:isin/corporate-structure@1.0.0;
    export etzhayyim:isin/cross-classification@1.0.0;
}
```

## Verification Steps

### 1. Build + Deploy

```bash
cd 60-apps/etzhayyim-project-isin/appview/etzhayyim-wasm-isin-is1n8k2x
etzhayyim build
etzhayyim deploy
```

### 2. Health Check

```bash
curl https://is1n8k2x.etzhayyim.com/health
curl https://is1n8k2x.etzhayyim.com/_app/meta
curl https://is1n8k2x.etzhayyim.com/_app/meta
```

### 3. Heartbeat Trigger (Manual)

```bash
curl -X POST https://is1n8k2x.etzhayyim.com/_heartbeat \
  -H "x-kotodama-internal-token: $(etzhayyim authn token --internal)"
```

### 4. Verify DID Creation

```bash
# Primary DID
curl https://isin.etzhayyim.com/.well-known/did.json

# Country DID (US)
curl "https://atproto.etzhayyim.com/xrpc/com.atproto.identity.resolveHandle?handle=isin.etzhayyim.com:us"
```

### 5. Verify Social Posts

```bash
# Check primary DID timeline
curl "https://atproto.etzhayyim.com/xrpc/app.bsky.feed.getAuthorFeed?actor=did:web:isin.etzhayyim.com"

# Check US country DID timeline
curl "https://atproto.etzhayyim.com/xrpc/app.bsky.feed.getAuthorFeed?actor=did:web:isin.etzhayyim.com:us"
```

### 6. Verify Coverage Data

```bash
# Via cross-actor invoke
curl -X POST https://atproto.etzhayyim.com/xrpc/com.etzhayyim.projector.sendProjectMessage \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(etzhayyim authn token)" \
  -d '{"app_id":"is1n8k2x","method":"get-coverage","params":"{}"}'
```

### 7. Verify on yoro

- `yoro.etzhayyim.com/profile/did:web:isin.etzhayyim.com` — primary profile + analysis posts
- `yoro.etzhayyim.com/profile/did:web:isin.etzhayyim.com:us` — US coverage posts
- `yoro.etzhayyim.com/profile/did:web:isin.etzhayyim.com:jp` — JP coverage posts

## Horizontal Expansion Pattern

ISIN の coverage-driven social evolution が検証できたら、同パターンを他の multi-DID app に横展開する。

### Pattern: Coverage-Driven Social Evolution

```go
// 1. Entity registry (in-memory)
var entities = []entityDef{
    {Path: "entity1", Name: "...", ...},
    {Path: "entity2", Name: "...", ...},
}

// 2. Heartbeat handler
kotodama.HandleHeartbeat(func(feed, engagement string) string {
    // a. Ensure entity DIDs (lazy create)
    for _, e := range entities {
        kotodama.DIDCreate(e.Path, profileDoc)
    }
    // b. Query coverage per entity
    // c. Find weakest entity
    // d. ATPost(weakestDID, coverageReport)
    // e. DIDWrite(weakestDID, "coverage_report", data)
    // f. LLMChat → ATPost(analysis)
    return actionsJSON
})

// 3. app.Serve() — auto-enables social evolution
```

### Applicable Projects

| Project | Entity DID Pattern | Coverage Metric | 横展開優先度 |
|---|---|---|---|
| **states** (`gov-{cc}`) | `did:web:gov-{cc}.etzhayyim.com:{ministry}` | 省庁 coverage (法律/予算/人員) | High — 既に multi-DID |
| **isic** | `did:web:isic-{section}.etzhayyim.com:{div}` | Division/Group entity 数 | High — 21 section apps |
| **isco** | `did:web:isco.etzhayyim.com:{group}` | 職種 coverage (715 performers) | Medium |
| **cpc** | `did:web:cpc.etzhayyim.com:{section}:{div}` | 製品分類 coverage | Medium |
| **natural-person** | `did:web:natural-person.etzhayyim.com:{country}` | 国別 cohort coverage | Medium |
| **legal-entity** | `did:web:legal-entity.etzhayyim.com:{jurisdiction}` | 法人登記 coverage | Medium |
| **chotatsu** | `did:web:chotatsu.etzhayyim.com:{portal}` | 調達ポータル coverage | Low |

### 横展開手順

1. ISIN で heartbeat → ATPost → coverage report の E2E 動作を確認
2. `states` の既存 heartbeat に coverage query + ATPost を追加
3. `isic` の 21 section apps に coverage metrics を追加
4. 成功パターンを `60-apps/CLAUDE.md` に Coverage-Driven Social Evolution 標準として追記
