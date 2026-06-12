---
id: adr-2606121350-yoro-ui-svelte-to-cljs-migration-harness
title: "ADR-2606121350: yoro UI svelte→ClojureScript 段階移行ハーネス — wave 2+3 (hooks 修正 + 9 components/state + atproto interop + tests)"
status: accepted
doc_type: adr
topic: yoro-cljs-migration
authoritative: false
last_verified: 2026-06-12
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Session-close record for the 2026-06-12 yoro cljs migration session: the untracked cljs scaffold's blank-screen hook bug fixed, 6 components + 2 state ns + legal doc + atproto XRPC interop ported with parity, 9/19 cljs tests + playwright e2e green, all landed as PR #1696. The svelte app remains production; the cljs harness is a development-time parallel implementation."
authoritative_for:
  - yoro UI cljs migration harness layout + porting conventions (60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/cljs/)
depends_on: []
related:
  - adr-2606121225-session-close-worktree-cleanup-pr-merge-ruleset-bypass
supersedes: []
superseded_by: []
---

# ADR-2606121350: yoro UI svelte→ClojureScript 段階移行ハーネス — wave 2+3

**Status**: accepted
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

yoro UI (svelte 5 SPA, 本番稼働中) の ClojureScript (reagent + re-frame,
shadow-cljs) への段階移植 scaffold が shared checkout に **untracked** で
置かれていた (wave 1: state 4 ns + components 2 本 + 雛形)。本セッションで
local 起動したところ**画面が真っ白**になる障害があり、原因修正と移行続行が
指示された。

# Decision

## 1. 移行ハーネスの形

- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/cljs/` を
  svelte 本体 (`../svelte/`, 本番) と並走する**開発時並行実装**とする。
  1 コンポーネント / 1 store ずつ svelte 原本とパリティを保って移す。
- `core.cljs` は移行済み store を実走させる 5 タブ検証ハーネス
  (Components / History / HITL / Convos / Topology)。
- dev: `pnpm css && pnpm dev` (:dev-http 8700, push-state)。
  test: `pnpm test` (shadow-cljs :node-test)。smoke: `pnpm smoke`
  (playwright, system Chrome)。

## 2. 真っ白バグの根本原因と移植規約 (constitution of the port)

- **React hooks 禁止**: reagent はコンポーネントをクラスコンポーネントとして
  render するため、`react/useEffect` 直呼びは Invalid hook call で
  **全ツリーが落ちて真っ白**になる。svelte `onMount` 相当は form-2 setup /
  form-3 `:component-did-mount` で表現する (streak-badge / no-cookie-banner
  を修正)。
- `rdom/render` (legacy) → `reagent.dom.client/create-root` (React 18)。
- **`""` は cljs で truthy**: TS の falsy ガード直訳は空文字を素通しする
  (topology の空 topic バグをテスト移植が捕捉 → 修正)。
- reagent の controlled input は次フレーム再描画 — playwright `check()` の
  即時検証は落ちる。`click()` + wait を使う。

## 3. CSS — CDN 不使用のローカル Tailwind 生成

Tailwind v4 を svelte 側の `@tailwindcss/postcss` で呼ぶ `build-css.mjs` が
`cljs/src` をスキャンし `public/css/tailwind.css` を生成 (gv2 トークンは
`@theme` で定義)。外部 CDN は導入しない (substrate 自己完結維持)。

## 4. atproto interop — $lib/atproto-agent の cljs slice

`interop/atproto.cljs` に XRPC query/procedure + token 解決 3 段
(explicit → session accessJwt → token-provider) + re-frame fx
(`:atproto/query` / `:atproto/procedure`)。**get-session は local-only**
(unauthenticated bootstrap で `com.atproto.server.getSession` XRPC を
撃たない — yoro CLAUDE.md の 401-noise CRITICAL ルール準拠)。
history の PDS stub を createRecord / kagami graph query / deleteRecord に
実配線、未ログイン時は XRPC を撃たず local-only に fail-open。

## 5. 移植済み一覧 (wave 1 修正 + wave 2/3 追加)

components: streak_badge / no_cookie_banner / brainrot_mascot (6 キャラ) /
kami_yoro_mascot (WebGPU iframe + SVG fallback) / inference_consent
(3 ゲート TOS) / ad_slot (removed stub, Rider §2(c)) /
header_yoro_animation (8 パターン) / nondual_experience_guide
(Charter §1.17: means-agnostic + legality-floor geo gate fail-closed +
anti-coercion)。
state: history / hitl / convos / topology / inference_consent。
legal: inferenceConsentDocument。
test: topology_test (9 tests / 19 assertions)。

# Verification

- shadow-cljs watch 0 warnings; `:node-test` 9/19 green
- playwright smoke: render / タブ遷移 / history 記録 / 同意モーダル 3 ゲート
  e2e / guide e2e (open → 合法的観想の道 → geo fail-closed → anti-coercion →
  continue close) — console/page errors 0
- PR #1696 (branch `worktree-yoro-cljs-migration`)

# Consequences / Follow-up

- svelte が本番のまま — cljs ハーネスは出荷経路に未接続 (意図的)
- 未移植: YoroAuthGate / OpsFAB / AppDrawer / convos listConvos 配線 /
  legal 残り文書 (terms/privacy/feedback/help) / playClick() sound interop
- shadow-cljs / tailwind ビルドは CI 未配線 (path-scoped job が次の一手)
