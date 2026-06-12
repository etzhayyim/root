# yoro-ui cljs — svelte → ClojureScript 移行ハーネス

yoro UI (svelte) の ClojureScript (reagent + re-frame, shadow-cljs) 段階移植。
svelte 本体 (`../svelte/`) は本番のまま、ここに 1 コンポーネント / 1 store ずつ
パリティを保って移していく。

## Dev

```bash
pnpm install        # shadow-cljs + react 18
pnpm css            # ../svelte の tailwindcss v4 で public/css/tailwind.css を生成 (CDN 不使用)
pnpm dev            # shadow-cljs watch app → http://localhost:8700 (hot reload)
pnpm test           # shadow-cljs :node-test (cljs.test)
pnpm smoke          # headless Chrome smoke (render / tabs / consent modal e2e)
```

クラスを追加・変更したら `pnpm css` を再実行 (cljs/src をスキャンして再生成)。

## 移植済み

| cljs | svelte 原本 | 備考 |
|---|---|---|
| `components/streak_badge.cljs` | `components/StreakBadge.svelte` | form-2 (hooks 禁止 — reagent はクラスコンポーネント) |
| `components/no_cookie_banner.cljs` | `components/NoCookieBanner.svelte` | host gate に localhost 追加 (dev) |
| `components/brainrot_mascot.cljs` | `components/BrainrotMascot.svelte` | 6 キャラ SVG + blink/phrase interval (form-3) |
| `components/kami_yoro_mascot.cljs` | `KamiYoroMascot.svelte` | WebGPU iframe + SVG fallback |
| `components/inference_consent.cljs` | `components/InferenceConsent.svelte` | 3 ゲート TOS モーダル |
| `components/ad_slot.cljs` | `components/AdSlot.svelte` | removed stub (Charter Rider §2(c)) |
| `state/history.cljs` | `$lib/history.svelte.ts` | re-frame events/subs (PDS interop は stub) |
| `state/hitl.cljs` | `$lib/hitl-store.svelte.ts` | 10s ポーリング |
| `state/convos.cljs` | `$lib/w/convo-store.svelte.ts` | 骨格のみ (atproto-agent interop 未移植) |
| `state/topology.cljs` | `$lib/session-topology.svelte.ts` | 空文字 topic を弾く fix 込み |
| `state/inference_consent.cljs` | `components/inference-consent-state.svelte.ts` | promise ゲート |
| `legal/content.cljs` | `$lib/legal/content.ts` | inferenceConsentDocument のみ |
| `components/header_yoro_animation.cljs` | `components/HeaderYoroAnimation.svelte` | 8 パターン + blink/rotate interval |
| `components/nondual_experience_guide.cljs` | `components/NondualExperienceGuide.svelte` | Charter §1.17 (geo gate fail-closed) |
| `interop/atproto.cljs` | `$lib/atproto-agent` (client slice) | XRPC query/procedure + re-frame fx; get-session は local-only (401-noise ルール) |
| `test/.../topology_test.cljs` | `session-topology.test.ts` | 9 tests / 19 assertions |

## 落とし穴 (svelte → reagent)

- **React hooks 禁止**: reagent コンポーネントはクラスコンポーネント。`useEffect` は
  Invalid hook call で全画面真っ白。`onMount` 相当は form-2 setup / form-3
  `:component-did-mount`。
- **`""` は truthy**: TS の falsy ガードを `(when x ...)` に直訳すると空文字が通る。
- **controlled checkbox**: reagent の再描画は次フレーム — playwright `check()` の即時
  検証は落ちる。`click()` + wait を使う。
- shadow-cljs `:dev-http` の push-state は `Accept: text/html` 必須 (curl 素叩きは 404)。
