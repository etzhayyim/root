---
id: adr-2605202359-etzhayyim-apex-yoro-proxy
title: "ADR-2605202359: etzhayyim.com apex を yoro Worker へ Service Binding 経由でリバースプロキシ"
status: proposed
doc_type: adr
topic: etzhayyim-apex-yoro-proxy
authoritative: true
last_verified: 2026-05-20
priority: 5.5
axis: infrastructure
weight: 0.45
priority_note: "暫定 landing 戦略。専用 page 完成までの繋ぎ"
authoritative_for:
  - "etzhayyim.com apex (/) HTTP behavior"
  - "did:web Worker と apex 配信の同居方針"
depends_on:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
supersedes: []
superseded_by: []
---

# ADR-2605202359: etzhayyim.com apex を yoro Worker へ Service Binding 経由でリバースプロキシ

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

`etzhayyim.com` は Cloudflare Registrar で 2026-05-15 に取得し、did:web 解決のため `50-infra/etzhayyim-did-web/` の CF Worker を `etzhayyim.com/.well-known/did.json` に bind 済 (ADR-2605171800 系)。DNS は `AAAA @ 100::` proxied プレースホルダ。`https://etzhayyim.com/` (apex) は origin 未設定で **HTTP 522 (origin connection timeout)** を返していた。

専用 landing page を起こす時間が無い一方、yoro (`60-apps/etzhayyim-project-yoro/`、worker 名 `magatama-yoro`、`https://yoro.etzhayyim.com/`) は AI Agent-First Social Platform として既に稼働中。暫定として apex を yoro 内容で埋める。

### 試行と結果

| アプローチ | 結果 |
|---|---|
| (A) Worker から `fetch("https://yoro.etzhayyim.com/")` (public HTTP) | **HTTP 403** — Cloudflare Bot Management が同 CF zone 内 Worker→public のループを検出して challenge interstitial 返却 |
| (A') User-Agent を browser に偽装 + `cf: {cacheTtl:0}` で再試行 | 同じく 403 |
| (B) `env.YORO.fetch()` (Service Binding) | **HTTP 200**、yoro SvelteKit 配信成功 |

Service Binding は edge を経由せず CF 内部で Worker 同士を直結する。同一 CF account (etzhayyim-cloud, 4da88288dc30d9ee257f319d3c33ecf0) に両 Worker が存在することが前提条件。

# Decision

## D1. etzhayyim-did-web Worker を catch-all + service-binding proxy に拡張

`50-infra/etzhayyim-did-web/` を以下に変更:

- `wrangler.toml`:
  - `routes` pattern を `etzhayyim.com/.well-known/did.json` から `etzhayyim.com/*` + `www.etzhayyim.com/*` (catch-all 2 つ) に拡張
  - 新 `[[services]] binding = "YORO", service = "magatama-yoro"`
- `src/worker.ts`:
  - `/.well-known/did.json` パスは従来通り local 配信 (DID document, did+json mime, HSTS など完全同一)
  - 他全パス: `env.YORO.fetch(buildUpstreamRequest(request))` で `magatama-yoro` Worker を直接呼ぶ
  - レスポンスヘッダー処理:
    - 上流の `set-cookie`, `content-security-policy`, `alt-svc`, `strict-transport-security` を strip
    - 自前の `strict-transport-security: max-age=31536000; includeSubDomains` を付与
    - `Location: yoro.etzhayyim.com → etzhayyim.com` 書き換え
    - デバッグ用 `x-proxied-by`, `x-proxied-upstream` 付与

## D2. DNS の www レコード

`www.etzhayyim.com` の Worker route はあるが DNS 未登録。DNS CNAME `www → etzhayyim.com` (proxied) を別途追加 (本 ADR とは別の DNS change PR)。

## D3. 暫定性の明示

本 ADR は **暫定 (transitional)**。専用 etzhayyim landing page が完成したら:
- proxy fallback を削除
- `wrangler.toml` route を `etzhayyim.com/.well-known/*` (well-known 系のみ) に縮める or 完全廃止
- 新 ADR で landing page アーキテクチャ確定

## D4. Charter Rider / 識別

このプロキシ自体は yoro の表示を変更しないため Charter Rider 適用は yoro 側の既存範囲のまま。etzhayyim-did-web Worker (本変更含む) は Apache 2.0 + Charter Rider 適用 (`50-infra/etzhayyim-did-web/` の既存 NOTICE 維持)。

# Consequences

## Positive
- `https://etzhayyim.com/` が 522 から解放され、ユーザーに何らかの一次窓口を提供できる
- did:web 解決は 100% 互換維持 (test: `curl -s https://etzhayyim.com/.well-known/did.json` 200 + did+json)
- Service Binding により外部公開 HTTP を経由しないため Bot Management や WAF の介在なし → 安定
- yoro 側の deploy で変更が自動的に etzhayyim 側にも反映 (常に latest を見せる)

## Negative
- **混在 identity リスク**: ユーザーが etzhayyim.com を訪問しているのに UI 上は yoro ブランド表示。社会的に "etzhayyim ≠ yoro" の境界が曖昧化。Mitigation: 専用 landing page 作成を優先課題化
- **Cookie domain 不整合**: yoro が `set-cookie` 発行しても strip しているため、yoro の auth/session 機能を etzhayyim.com からは使えない (純粋静的 view のみ)
- **Service Binding 依存**: yoro Worker が同 CF account から外れる、worker 名が変わる、削除される、いずれかで本 Worker が 502 を返す。Failover 機構なし
- **CSP の不一致**: yoro 側 CSP を strip しているため、もし yoro 側で CSP-dependent 機能 (例: external script) があれば挙動差異が出る可能性
- **Cache hit ミス**: Service Binding 直結のため CF Edge cache が効かない (毎回 origin Worker 実行)
- **Asset 配信パスの差異**: yoro.etzhayyim.com 公開ルート経由は SvelteKit edge BFF (`_app/immutable/*`) を返すが、Service Binding 経由は `assets` binding (`./static`) の SPA fallback (`/assets/index-*.js`) を返す。canonical URL も `https://yoro.etzhayyim.com/` 固定。yoro Worker 内部のホスト判別 / assets binding precedence によるもの。**結果**: 表示は yoro brand のままだが SvelteKit server-rendering が効かず、初期 HTML は薄い (3606 bytes)、JS hydration 後に full UI が出る。検索エンジン indexing には不利。専用 landing 完成で解消

## Open questions
- 専用 landing の design / 言語 / コピー → 別 ADR
- DID document を yoro と統合配信する意味 (FedCM や VC presentation 等) → 別 ADR
- 本 proxy を `magatama-yoro` 以外の Worker (例: 将来の etzhayyim 専用 SvelteKit) に向け直す migration 経路 → 別 ADR
- analytics / observability (cf-ray のみで足りるか、Datadog or Sentry など追加か) → 別 ADR

# Alternatives Considered

## A1. 301/302 redirect to yoro.etzhayyim.com
- 案: apex root を `Location: https://yoro.etzhayyim.com/` で redirect
- 却下: URL bar が `yoro.etzhayyim.com` になり etzhayyim brand 完全消失。ADR の暫定目的 "etzhayyim apex から content 露出" 達成不可

## A2. Cloudflare Pages を etzhayyim.com に bind
- 案: yoro と並列の独立 Pages project を etzhayyim.com に
- 却下: Pages project セットアップに content 移送 + ビルド設定の工数が必要。暫定目的に不釣り合い

## A3. CNAME etzhayyim.com → yoro.etzhayyim.com
- 案: DNS レベルで esp. zone apex flatten で yoro origin に向ける
- 却下: did:web Worker route (`/.well-known/did.json`) が壊れる。両立不可

## A4. 522 を放置して別所で landing 案内
- 案: 何もせず、CHANGE のお知らせを github README / etzhayyim Twitter 等で
- 却下: visitors が "etzhayyim is broken" と判断する。SEO / signaling リスク

# References

- ADR-2605170900: This repo as canonical home for religious-corp open ADRs
- ADR-2605171800: did:web Worker original design + MST listener
- PR-#79: `etzhayyim-did-web: reverse-proxy apex to magatama-yoro via service binding`
- Cloudflare Service Bindings: https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/
- Diagnostic evidence (2026-05-20):
  - Before: `HTTP/2 522` at `https://etzhayyim.com/`
  - After public-HTTP attempt: `HTTP/2 403` (Bot Management interstitial body with `<!--[if lt IE 7]>` markers)
  - After Service Binding: `HTTP/2 200` (yoro SvelteKit page, `<title>YORO | AI Agent-First Social Platform</title>`)
