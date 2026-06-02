---
id: yoro-superapp-oembed-design
title: yoro.etzhayyim.com SuperApp-Only Architecture + oEmbed (Lexicon Web)
status: active
doc_type: explanation
topic: yoro-superapp-oembed
authoritative: true
last_verified: 2026-03-23
authoritative_for:
  - yoro URL routing (Bluesky-compatible)
  - oEmbed / Lexicon Web endpoint design
  - channel concept removal
  - SSR OG tag strategy
  - yoro SEO (robots.txt, sitemap.xml, JSON-LD, OGP)
related:
  - yoro-w-protocol-messenger-design
  - data-gateway-consolidation
  - atprotocol-signal-design
supersedes:
  - (yoro legacy channel-based routing)
superseded_by: []
---

# yoro.etzhayyim.com SuperApp-Only Architecture + oEmbed (Lexicon Web)

## Goal

yoro.etzhayyim.com を **唯一の UI host** として全 App のコンテンツを表示する。個別 app の Svelte UI (`fullapp`) を廃止し、`canvas` + `miniapp` の 2 モードに統一。URL は Bluesky (`bsky.app`) と互換。

## Scope

- yoro.etzhayyim.com の URL routing 設計
- oEmbed endpoint (AT Protocol Lexicon Web 提案準拠)
- SSR OG tags (crawler 対応)
- channel 概念の除去

## Executive Summary

### AT Protocol の設計思想との整合

AT Protocol は **data (PDS records) と rendering (client) の完全分離** を前提とする。

- **Record**: PDS に保存される signed data。AT URI (`at://{did}/{collection}/{rkey}`) で一意に識別
- **View**: AppView が records を加工して client に返すもの
- **Client**: views を独自に rendering する

yoro.etzhayyim.com を唯一の client とし、全 app のコンテンツを rendering するのは AT Protocol の想定された使い方。

### AT URI スキーム (RFC 準拠)

```
at://AUTHORITY/COLLECTION/RKEY
```

- **Authority**: DID (推奨、durable) or handle (human-readable だが変更可能)
- **Collection**: NSID (e.g. `app.bsky.feed.post`, `com.etzhayyim.w.message`)
- **RKEY**: Record key (TID format `3jzfcijpj2z2a` 等)

例:
```
at://did:plc:vwzwgnygau7ed7b7wt5ux7y2/app.bsky.feed.post/3k5nobkf2w72g
at://retr0.id/app.bsky.feed.post/3k5nobkf2w72g
```

DID を authority に使うのが AT Protocol の **標準かつ推奨**。handle は display 用途。

### Legacy Routing 概念の除去

Bluesky は convo-less。投稿は user の repo 内の collection (`app.bsky.feed.post`) に入る。

| Before (legacy) | After (Bluesky-compatible) |
|---|---|
| Post = convo + rkey | Post = author DID + rkey |
| `/post/{convoId}/{rkey}` | `/profile/{handle}/post/{rkey}` |
| `/channel/{convoId}` | `/messages/{convoId}` |
| Convo = public/private container | DM = `chat.bsky.convo.*` |

Public timeline は feed generator で構成 (convo で分離しない)。

## Decision

### 1. URL Routing (Bluesky 互換)

| bsky.app | yoro.etzhayyim.com | AT URI |
|---|---|---|
| `/profile/{handle}` | `/profile/{handle}` | — |
| `/profile/{handle}/post/{rkey}` | `/profile/{handle}/post/{rkey}` | `at://{did}/app.bsky.feed.post/{rkey}` |
| `/profile/{handle}/feed/{name}` | `/profile/{handle}/feed/{name}` | — |
| `/messages` | `/messages` | — |
| `/messages/{convoId}` | `/messages/{convoId}` | — |
| `/notifications` | `/notifications` | — |
| `/search` | `/search` | — |
| — | `/oembed?url=...` | — |
| — | `/embed/post/{handle}/{rkey}` | — |

### 2. Legacy Route Redirects

| Old path | → New path | Method |
|---|---|---|
| `/post/{convoId}/{rkey}` | `/profile/{author}/post/{rkey}` | Client redirect (author resolved from post) |
| `/channel/{convoId}` | `/messages/{convoId}` | Client redirect |
| `/apps/{did}` | `/profile/{did}` | Client redirect |
| `/talk` | `/messages` | Client redirect |

### 3. SSR OG Tags + SEO

`adapter-cloudflare` (Cloudflare Workers) で server-side rendering。root layout は `ssr = false` だが、特定 route で `ssr = true` を override。

| Route | SSR | OG Tags Source |
|---|---|---|
| `/profile/{handle}` | `+page.server.ts` (ssr=true) | `atproto.etzhayyim.com/xrpc/app.bsky.actor.getProfile` |
| `/profile/{handle}/post/{rkey}` | `+page.server.ts` (ssr=true) | `atproto.etzhayyim.com/xrpc/app.bsky.feed.getPostThread` |
| `/` (home) | Client-side | Static OG tags |
| `/hashtag/{tag}` | Client-side | Static OG tags |

Server-side fetch は `$lib/server/pds.ts` helper 経由。3s timeout、null fallback (Service Binding 優先)。

#### SEO Infrastructure

| 項目 | ファイル | 内容 |
|---|---|---|
| `robots.txt` | `static/robots.txt` | Private routes Disallow + AI training crawlers (GPTBot, CCBot, ClaudeBot 等) Disallow。Rate limit 600 req/min 明示 |
| `sitemap.xml` | `routes/sitemap.xml/+server.ts` | **Sitemap Index** → 3 sub-sitemaps: `static.xml` (7 routes, 24h cache), `profiles.xml` (PDS searchActors, 1h cache), `posts.xml` (PDS Timeline, 1h cache) |
| JSON-LD (Home) | `routes/+page.svelte` | `WebApplication` schema (name, description, applicationCategory, publisher) |
| JSON-LD (Profile) | `routes/profile/[handle]/+page.server.ts` | `Person` or `Organization` (agent=Organization) + `InteractionCounter` (followers, posts) |
| JSON-LD (Post) | `routes/profile/[handle]/post/[rkey]/+page.server.ts` | `SocialMediaPosting` + engagement counters (likes, reposts, replies) + author + publisher |
| Global meta | `app.html` | `theme-color`, `application-name`, `og:locale=ja_JP`, `og:site_name=YORO`, `twitter:site=@etzhayyim` |

#### OG Tags Coverage

全 public ページに以下を設定:

- `og:title`, `og:description`, `og:type`, `og:url`, `og:image`, `og:image:alt`
- `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`
- `<link rel="canonical">`
- Post: `article:published_time`, `article:author`
- Profile: `at:did` meta、Post: `at:uri` meta

### 4. oEmbed Endpoint (Lexicon Web)

```
GET /oembed?url={url}&format=json&maxwidth=600&maxheight=400
```

AT Protocol コミュニティの **Lexicon Web 提案** に準拠:

```json
{
  "$type": "com.atproto.lexicon.web",
  "scope": "com.etzhayyim.w",
  "urlTemplate": "https://yoro.etzhayyim.com/record/{did}/{collection}/{rkey}",
  "oembedEndpoint": "https://yoro.etzhayyim.com/oembed"
}
```

#### Profile URL → type: "link"

```json
{
  "version": "1.0",
  "type": "link",
  "provider_name": "YORO",
  "provider_url": "https://yoro.etzhayyim.com",
  "title": "Display Name (@handle) — YORO",
  "author_name": "Display Name",
  "author_url": "https://yoro.etzhayyim.com/profile/handle",
  "thumbnail_url": "https://...",
  "cache_age": 3600
}
```

#### Post URL → type: "rich" (iframe embed)

```json
{
  "version": "1.0",
  "type": "rich",
  "provider_name": "YORO",
  "html": "<iframe src=\"https://yoro.etzhayyim.com/embed/post/{handle}/{rkey}\" ...></iframe>",
  "width": 600,
  "height": 400,
  "author_name": "Display Name",
  "cache_age": 3600
}
```

#### oEmbed Discovery (HTML `<link>`)

```html
<link rel="alternate" type="application/json+oembed"
  href="https://yoro.etzhayyim.com/oembed?url={encoded-url}&format=json"
  title="Post title" />
```

### 5. Lexicon Extension Model

| Layer | Namespace | Purpose |
|---|---|---|
| **Base** | `app.bsky.*` | Bluesky 100% 互換 (190/190 lexicons) |
| **Extended** | `com.etzhayyim.w.*` | W Protocol (cards, E2E, cross-actor, MDAG) |
| **oEmbed bridge** | Lexicon Web | External clients → yoro.etzhayyim.com rich preview |

Bluesky client が `com.etzhayyim.w.*` record を見た場合:
1. `text` field fallback (plain text 表示)
2. Lexicon Web → `yoro.etzhayyim.com/oembed` → rich preview / iframe embed

### 6. Open Union Embed Pattern

AT Protocol の post embed は **open union** (`$type` discriminator)。Custom embed types:

```json
{
  "$type": "com.etzhayyim.w.card",
  "content_type": "application/vnd.etzhayyim.card.chart",
  "payload": { "title": "...", "data": [...] }
}
```

- yoro.etzhayyim.com: Protocol Canvas card renderer (15 standard + custom types)
- bsky.app: Empty embed (unknown type fallback)
- Lexicon Web 対応 client: oEmbed → iframe embed

### 7. fullapp 廃止 → canvas + miniapp 統一

| 現在の fullapp | 移行先 | 理由 |
|---|---|---|
| handotai.etzhayyim.com (ニュース) | canvas | list + table + chart cards |
| kuruma.etzhayyim.com (車情報) | canvas | list + carousel + map-pin |
| chotatsu.etzhayyim.com (調達) | canvas | table + form + metric-dashboard |
| kami.etzhayyim.com (ゲーム) | miniapp | wgpu 3D rendering |
| society6.etzhayyim.com (COFOG) | canvas | metric-dashboard + chart |
| oshi.etzhayyim.com (動画) | canvas + miniapp | timeline=card, 編集=miniapp |

個別 `*.etzhayyim.com` ドメインは API-only (XRPC backend)。UI は `yoro.etzhayyim.com/profile/{did}` に集約。

### 8. Subdomain → yoro Redirect + iframe Embed

nanoid subdomain への browser 直接アクセスは yoro profile に redirect し、AgentProfile 内で iframe embed する。

```
{nanoid}.etzhayyim.com/ (browser, Accept: text/html)
  → 301 yoro.etzhayyim.com/profile/did:web:{nanoid}.etzhayyim.com?app=1
    → AgentProfile.svelte: ?app=1 → autoEmbed=true → showAppEmbed=true
      → <iframe src="{nanoid}.etzhayyim.com/?embed=1" sandbox="allow-scripts allow-same-origin allow-forms allow-popups">
```

| Request | Redirect? | Destination |
|---|---|---|
| `GET /` + `Accept: text/html` | Yes | `yoro.etzhayyim.com/profile/did:web:{host}?app=1` |
| `GET /api/*`, `/_*`, `/?embed=1`, static | No | dispatch to user Worker |

**Shannon 根拠**: shell/state/routing が yoro 1 箇所に集約。subdomain は API + iframe content (embed mode) のみ提供。冗長度 0%。

## Comparison

### vs. Bluesky (bsky.app)

| 機能 | bsky.app | yoro.etzhayyim.com |
|---|---|---|
| URL structure | `/profile/{handle}/post/{rkey}` | 同一 |
| AT URI | `at://{did}/app.bsky.feed.post/{rkey}` | 同一 |
| Custom lexicons | `app.bsky.*` only | `app.bsky.*` + `com.etzhayyim.w.*` |
| E2E encryption | 計画中 | Signal Protocol 実装済み |
| oEmbed | 計画中 (2024 roadmap) | 実装済み |
| Card system | なし | 15 standard + custom types |
| MiniApp embedding | なし | dynamic import from B2 |

### vs. WeChat Mini Programs

| 機能 | WeChat | yoro.etzhayyim.com |
|---|---|---|
| App hosting | WeChat SuperApp | yoro.etzhayyim.com SuperApp |
| App identity | WeChat AppID | AT Protocol DID |
| Data model | Proprietary | AT Protocol (open, portable) |
| Encryption | Server-side | Signal Protocol E2E (client-side) |
| Interop | WeChat only | Any AT Protocol client |

## Exceptions

- yoro.etzhayyim.com 自身は `fullapp` のまま (SuperApp host として SvelteKit SSR が必要)
- KAMI Engine (wgpu) は appview mode (iframe embed)

## References

- [AT Protocol Overview](https://atproto.com/guides/overview)
- [AT URI Scheme](https://atproto.com/specs/at-uri-scheme)
- [AT Protocol Lexicon](https://atproto.com/specs/lexicon)
- [Bluesky Custom Schemas](https://docs.bsky.app/docs/advanced-guides/custom-schemas)
- [Lexicon Embeds Discussion](https://discourse.atprotocol.community/t/lexicon-embeds-overview/133)
- [2025 Protocol Roadmap](https://docs.bsky.app/blog/2025-protocol-roadmap-spring)
- `90-docs/260317-yoro-w-protocol-messenger-design.md`
- `90-docs/260321-data-gateway-consolidation.md`
- `90-docs/260315-atprotocol-signal-design.md`
