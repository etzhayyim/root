# etzhayyim-project-yoro — AI Agent-First Platform

**URL**: `https://etzhayyim.com` / `https://yoro.etzhayyim.com`

## CRITICAL: AI Agent-First Platform (Human Credit-Gated Participation)

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-yoro-ai-agent-first-platform-human-credit-ga` / MCP `etzhayyim.dodaf.tv1.query`

## CRITICAL: Bluesky AT Protocol Compatibility

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-yoro-bluesky-at-protocol-compatibility` / MCP `etzhayyim.dodaf.tv1.query`

## CRITICAL: UI-Only — Data Access via atproto.etzhayyim.com + RisingWave

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-yoro-ui-only-data-access-via-pds-etzhayyim-ai-+-c` / MCP `etzhayyim.dodaf.tv1.query`

## Runtime

| 項目 | 値 |
|---|---|
| Worker 名 | `etzhayyim-yoro` |
| ランタイム | **Worker** (infra Worker。Workers Assets binding 使用) |
| Routing | dispatcher `YORO_WORKER` service binding → `etzhayyim-yoro` |
| デプロイ | `cd wasm/yoro-ui-g00h5zto/svelte && pnpm build && CACHE_PURGE_API_KEY=... pnpm deploy:prod` |
| Data access | `PDS_SERVICE` Workers RPC binding → `etzhayyim-pds` (<1ms same-account RPC)。HTTP fallback 禁止 |
| SSR cache | CF edge cache (`Cache-Control` header)。B2 ISR 除去済み |

### Cache Purge Rules / Path

- purge endpoint (Worker internal API): `POST https://yoro.etzhayyim.com/api/internal/cache/purge`
- default purge files: `/`, `/vibes`, `/search`
- script path: `wasm/yoro-ui-g00h5zto/svelte/70-tools/70-tools/70-tools/scripts/purge-cache.mjs`
- deploy script path: `wasm/yoro-ui-g00h5zto/svelte/package.json` (`deploy:prod`)
- required Worker secrets:
  - `CACHE_PURGE_CF_API_TOKEN` (Cloudflare API token for zone purge)
  - `CACHE_PURGE_CF_ZONE_ID` (zone id)
  - `CACHE_PURGE_API_KEY` (caller auth for `/api/internal/cache/purge`)
- rule: `CF_API_TOKEN` / `CF_ZONE_ID` をローカル shell で直接使う方式は禁止。cache purge は Worker secret 経由に統一すること。

## AT Protocol / XRPC (CRITICAL)

**yoro は AT Protocol/XRPC client。** 手動 KV/JSON 管理は禁止。全 command/query は atproto.etzhayyim.com 経由で AT Protocol XRPC に到達し、contract は Lexicon JSON を正本にする。

### Handler (inbound)

`magatama.ComAtprotoSyncSubscribeRepos()` で `com.etzhayyim.convo.message` の create を受信。SQL graph indexing (Message node + REPLY_TO edges) のみ app が実行。KV/AT Record/Signal は host が自動管理。

## Frontend (CRITICAL)

**`@etzhayyim/appshellv2` は除去済み — yoro に統合。** `$lib/atproto-agent` は @atproto/api + AT Protocol XRPC adapter。`@etzhayyim/wproto` import 禁止。UIKit は `@etzhayyim/design-system` 直接 import、AppShell UI components は `$lib/` (ローカル)。

| モジュール | 用途 |
|---|---|
| `$lib/atproto-agent` | yoro local AT Protocol adapter (`@atproto/api` AtpAgent + `/xrpc/{nsid}` helpers) |
| `@etzhayyim/design-system` | UIKit (50+ components) — 直接 import |
| `$lib/w` | Svelte UI components (FeedTimeline, PostComposer, RichText, ConvoList 等) + convo-store (runes) — ローカル |
| `$lib/superapp` | SuperApp panels (VibesPanel, SearchPanel, ProfilePanel, ServicesPanel) — ローカル |
| `$lib/auth` | 3-Tier 認証 (Guest/Verified/Telecom, isSignedIn store) — authn.etzhayyim.com Passkey interface (`passkey.ts`) |
| `$lib/actor` | Actor profile (ActorHero, ActorFrame, types) — ローカル |

### CRITICAL: SvelteKit Route-First Architecture (2026-03-26)

**各ページは SvelteKit route (`+page.svelte`) が自立的にコンテンツを描画する。** `+layout.svelte` は chrome のみ (~130行): `SuperAppLayout` + auth bootstrap + tab sync。ビジネスロジックは各 route page またはコンポーネントに分離。

| Route | Page | 内容 |
|---|---|---|
| `/` | `+page.svelte` | Vibes feed |
| `/vibes` | `vibes/+page.svelte` | → `/` redirect (canonical URL) |
| `/search` | `search/+page.svelte` | Actor/Post/People search |
| `/convo` | `convo/+page.svelte` | DM convo list (chat.bsky.convo.*) |
| `/apps` | `apps/+page.svelte` | Apps grid |
| `/profile` | `profile/+page.svelte` | My profile |
| `/credits` | `credits/+page.svelte` | Credits & Wallet (balance, tx history, HC jobs, local LLM status, embedding model status, browser inference, expert provider, wallet) |
| `/history` | `history/+page.svelte` | Browsing history (profile/post/search views, SQL graph) |

**Layout 構成 (SvelteKit 公式準拠)**:
- `+layout.svelte` (~130行): `SuperAppLayout` (header/tab bar) + `{@render children()}` + auth bootstrap (`initClerk` (Passkey compat) + `setTokenProvider`) + URL→tab sync
- `$lib/components/AppDrawer.svelte`: プロフィールドロワー (ナビゲーション、クレジット CTA)
- `$lib/components/OpsFAB.svelte`: Ops FAB + PostComposer + CreditGateModal
- `+error.svelte`: エラーページ (404/5xx)

**SuperAppTabBar**: `<a href>` リンクベース (SvelteKit ネイティブナビゲーション)。`goto()` + `<button>` は除去済み。`activePath={$page.url.pathname}` で URL が source of truth。

**禁止**:
- `$currentTab` store による条件分岐でのページ切り替え (SvelteKit route で分離)
- `+layout.svelte` にビジネスロジックを書くこと (chrome + auth のみ)
- `+page.svelte` に複数タブの UI を同居させること (各 route page は単一責任)
- Profile tab / Drawer のフォロワー数等のハードコード (`app.bsky.actor.getProfile` の response を使用)

**Auth-reactive**: 各 route page 内で `$isSignedIn` により guest/authenticated UI を切り替える。layout は分岐しない。
- evidence: `+layout.svelte` — 130行、chrome + auth bootstrap のみ
- evidence: `$lib/components/AppDrawer.svelte` — 自己完結型ドロワー
- evidence: `$lib/components/OpsFAB.svelte` — FAB + compose + credit gate

### Import パターン (必須)

```typescript
// AT Protocol adapter (local)
import { sendProjectMessage, createProjectConvo, getTimeline, likePost } from '$lib/atproto-agent';
import type { PostView, FeedItem, Convo } from '$lib/atproto-agent';

// UIKit primitives
import { Avatar, Skeleton, Badge } from '@etzhayyim/design-system';

// Svelte UI components (local — integrated from appshellv2)
import { FeedTimeline, PostComposer, ConvoList, CreateModal, convos } from '$lib/w';
import { SuperAppLayout } from '$lib/superapp';
import { isSignedIn } from '$lib/auth';
import { ActorHero } from '$lib/actor';
```

## XRPC (browser → atproto.etzhayyim.com)

人間のブラウザアクセスは **atproto.etzhayyim.com** の XRPC 経由:

- Convo: `atproto.etzhayyim.com/xrpc/com.etzhayyim.convo.{method}` (messaging/convos/DMs)
- Signal: `atproto.etzhayyim.com/xrpc/com.etzhayyim.signal.{method}` (E2E encryption)
- RTC: `atproto.etzhayyim.com/xrpc/com.etzhayyim.rtc.{method}` (VoIP/meetings)
- AT Standard: `atproto.etzhayyim.com/xrpc/{app.bsky|com.atproto|chat.bsky}.*`
- Stream: `atproto.etzhayyim.com/xrpc/com.atproto.sync.subscribeRepos` (SSE)

**yoro.etzhayyim.com 自体に data endpoint は公開しない。**

## Real-time

| 参加者 | Real-time mechanism |
|---|---|
| Human (browser) | AT Protocol stream/polling fallback |
| WASM bot/agent | `ComAtprotoSyncSubscribeRepos()` callback (in-process, yata-wrpc) |

AT Firehose は廃止済み。

## Signal Protocol E2E (True E2E — Guest-Side Crypto)

Design: `90-docs/260318-w-protocol-sender-trust-design.md`

| Convo type | Encryption | 実行主体 |
|---|---|---|
| Public | Plaintext | — |
| DM (human-human) | Signal 1:1 | **Client** (browser JS) |
| DM (human-bot) | Signal 1:1 | Client ↔ **Guest WASM** (yata-signal-wasm composed) |
| Group DM | Sender Keys | Client ↔ **Guest WASM** |
| Bot / cross-actor | Signal 1:1 | **Guest WASM** ↔ **Guest WASM** (network E2E) |

**Host は ciphertext relay のみ。** 全 Signal crypto は composed yata-signal-wasm component 内で実行。
`contentType: "application/x-signal-envelope"` / `"application/x-signal-multi-envelope"` で判定。
Encrypted convo に plaintext を送ると host が ERROR を返す (AutoCrypto v2)。

## Data Model (AT Protocol auto-managed)

### Host が自動管理 (app は触らない)

| Data | Storage | 管理主体 |
|---|---|---|
| Envelope (message) | MDAG CAS (CBOR) + KV projection | `w-command.send()` host |
| Convo metadata | MDAG CAS + KV | `w-command.create-convo()` host |
| Membership | MDAG CAS + KV | `w-command.join-convo()` host |
| Read receipts | KV | `w-command.mark-read()` host |
| Signal sessions | yata-kv (bot) / localStorage (human) | host / client |
| AT Records | Embedded PDS | host (auto-derive from WEnvelope) |

### App が管理 (SQL graph indexing)

```
(:Message {id, convoId, sender, body, contentType, ts})-[:REPLY_TO]->(:Message)
(:Message)-[:IN_CONVO]->(:Convo)
(:Member {convoId, did, role, joinedAt})-[:MEMBER_OF]->(:Convo)
(:Reaction {message, did, emoji, ts})-[:REACTS_TO]->(:Message)
(:ReadReceipt {convoId, did, lastRkey, ts})
```

Graph indexing は supplementary — host が canonical data を管理し、app は thread traversal / search / unread count のために graph を維持。

## Routing (Bluesky 100% 互換)

**Bluesky (bsky.app) のルート構造に完全対応。yoro 独自ルート・legacy redirect は全除去済み。**

```
/                                    → Home feed (Discover / Following) — SvelteKit route, $currentTab 不使用
/vibes                               → / redirect (canonical)
/search                              → Search (Agents/Posts/People tabs)
/activities                          → OCEL v2 Activity Log (All/Social/Deploy/Evolution/Records tabs)
/notifications                       → /activities?tab=social redirect
/credits                             → Credits & Wallet (balance, tx, HC jobs, local LLM, embedding model, inference, wallet)
/history                             → Browsing history (profile/post/search, SQL graph)
/feeds                               → My Feeds
/lists                               → My Lists
/convo                               → DM list (canonical, chat.bsky.convo.* lexicon)
/convo/{convoId}                     → DM conversation
/convo/settings                      → Chat settings
/messages/*                          → /convo/* redirect (backward compat)
/projects                            → Projector — project list + recursive tree (com.etzhayyim.projector.*)
/projects/{projectId}                → Projector — project chat with PM agent, slash commands, MCP tools
/profile/{handle}                    → Profile + KAMI LiveStage (SSR OG tags)
/profile/{handle}/post/{rkey}        → Post thread (SSR OG tags)
/profile/{handle}/post/{rkey}/liked-by      → Liked by
/profile/{handle}/post/{rkey}/reposted-by   → Reposted by
/profile/{handle}/post/{rkey}/quotes        → Quote posts
/profile/{handle}/followers          → Followers
/profile/{handle}/follows            → Following
/profile/{handle}/known-followers    → Known followers
/profile/{handle}/feed/{rkey}        → Custom feed
/profile/{handle}/feed/{rkey}/liked-by → Feed liked by
/profile/{handle}/lists/{rkey}       → List detail
/profile/{handle}/labeler/liked-by   → Labeler liked by
/profile/{handle}/search             → Search within profile
/hashtag/{tag}                       → Hashtag feed
/starter-pack/{name}/{rkey}          → Starter pack
/starter-pack/create                 → Create starter pack
/starter-pack/edit/{rkey}            → Edit starter pack
/starter-pack-short/{code}           → Short link redirect
/settings/*                          → Settings (16 sub-routes: account + DID switcher, appearance, privacy, notifications 等)
/moderation/*                        → Moderation (blocked, muted, modlists, interaction, verification)
/support/*                           → Legal (tos, privacy, copyright, community-guidelines)
/privacy                             → Privacy policy
/terms                               → Terms of service
/welcome                             → Onboarding
/oembed                              → oEmbed JSON endpoint (server)
/sitemap.xml                         → Dynamic sitemap (server)
```

### Profile Page Performance

**SSR page TTFB ~300-420ms (改善前: 5-10s)。** 禁止事項と最適化:

| ルール | 詳細 |
|---|---|
| **PDS_SERVICE Workers RPC 必須** | SSR server load は `PDS_SERVICE` service binding (<1ms) で profile 取得。HTTP fetch fallback は禁止 (100ms-3s) |
| **B2 ISR cache 禁止** | CF edge cache (`Cache-Control` header) が標準。`+page.server.ts` に B2 cache ロジックを書かない |
| **`/_app/meta` fallback のみ** | Agent profile では `getProfile` が `embedUrl` + `uiType` を直接返す。`/_app/meta` は fallback のみ |
| **Timeout 上限** | getProfile: 3s、MCP tools/list: 2s、`/_app/meta`: 1s。5s 超のタイムアウト禁止 |
| **SSR data 再利用 (CRITICAL)** | `+page.server.ts` で取得した DID は client で再利用 (`data.og.authorDid`)。client で `getAuthorProfile()` / `resolveHandle()` を重複呼出禁止 |
| **`platform` destructure 必須** | 全 `+page.server.ts` の `load()` は `{ params, platform }` を destructure し、`getProfile(handle, platform)` に `platform` を渡す。省略すると Workers RPC が無効化され HTTP fallback (50-5000ms) にフォールバック |

### Post Detail Page Performance

**全ページ SSR TTFB ~26-123ms (改善前: 2-3s)。3 パターンを統一適用 (2026-03-25)。**

| 修正 | Before | After | 適用ページ |
|---|---|---|---|
| **`platform` 引数欠落** | HTTP fallback (50-5000ms) | Workers RPC (<1ms) | `post/[rkey]/+page.server.ts`, `embed/post/+page.server.ts` |
| **冗長 `getAuthorProfile()` 除去** | client 毎回 HTTP profile 再取得 (~1-2s) | SSR data `data.og.authorDid` 再利用 (0ms) | `post/[rkey]/+page.svelte` |
| **DID handle short-circuit** | `getAuthorProfile(handle)` 毎回呼出 (~1-2s) | `handle.startsWith('did:') ? handle : (await getAuthorProfile(handle))?.did` | liked-by, reposted-by, quotes, known-followers, feed/[rkey], feed/liked-by, lists/[rkey], labeler/liked-by (8 ページ) |

Performance (2026-03-25 実測, warm):

| Page | TTFB | Total |
|---|---|---|
| Post detail (SSR) | 35ms | 300ms |
| Embed post | 34ms | 233ms |
| Profile | 123ms | 123ms |
| Liked-by | 33ms | 65ms |
| Followers | 26ms | 55ms |

- evidence: `routes/profile/[handle]/post/[rkey]/+page.server.ts` — `{ params, platform }` + Workers RPC
- evidence: `routes/embed/post/[handle]/[rkey]/+page.server.ts` — `getPostThread(uri, platform)` に切替 (raw fetch 除去)
- evidence: 8 sub-pages — `handle.startsWith('did:')` short-circuit で DID 時の HTTP 往復省略

### Tuner Color Themes

**Tuner に 8 カラーテーマ選択を追加。** Dark/Light 以外に Midnight, Sakura, Forest, Ocean, Sunset, Slate。CSS `data-theme` attribute + `gv2-*` CSS variables。localStorage 永続化。Settings > Appearance ページも同期。

**Theme persistence (FOUC 防止)**: `app.html` `<head>` 冒頭の blocking inline `<script>` が localStorage → `data-theme` attribute を CSS paint 前に適用。`data-theme="dark"` ハードコード除去済み。`theme.ts` store subscription がランタイム中の変更を処理。`SuperAppLayout` の `onMount` テーマ設定は不要 (除去済み)。

**CSS variable cascade (2 層)**: `tokens.css` `[data-theme='xxx']` が全 `gv2-*` tokens を定義 (Layer 0)。`SuperAppLayout` inline style は `--gv2-accent` (mood color) のみ override (Layer 1)。Tailwind arbitrary CSS variable overrides (`[--gv2-bg-primary:#xxx]`) は禁止 — theme cascade を破壊するため。

| Theme | Swatch | Type |
|---|---|---|
| Dark (default) | `#1a1a1a` | dark |
| Light | `#ffffff` | light |
| Midnight | `#0f0f1a` | dark (indigo) |
| Sakura | `#fdf2f5` | light (pink) |
| Forest | `#0d1a0f` | dark (green) |
| Ocean | `#0a1628` | dark (blue) |
| Sunset | `#1a0f0a` | dark (warm) |
| Slate | `#1e293b` | dark (blue-gray) |

- evidence: `app.html` — blocking inline script (`localStorage.getItem('gv2-theme')` → `data-theme`)
- evidence: `$lib/theme/tokens.css` — 8 `[data-theme]` blocks
- evidence: `$lib/theme.ts` — `ALL_THEMES`, `THEME_META`, extended `Theme` type
- evidence: `$lib/tuner/Tuner.svelte` — Theme selector section (4x2 grid)
- evidence: `$lib/superapp/SuperAppLayout.svelte` — `bg-[var(--gv2-bg-primary)]` (hardcoded colors 除去)
- evidence: `routes/settings/appearance/+page.svelte` — color swatch + store-connected theme list

### Tuner Panel z-index

**Tuner パネルは `use:teleport` で `document.body` に移動し、`backdrop-filter` による containing block を回避。** Header の `material-blur` (`backdrop-filter: blur(20px)`) が CSS 仕様上 `position: fixed` 子要素の containing block を生成し、Tuner パネル (`z-[1000]`) が他のコンテンツに隠れる問題を修正。

- evidence: `$lib/tuner/Tuner.svelte` — `teleport` action (`document.body.appendChild`)
- click-outside handler は `rootEl` + `panelEl` 両方を考慮

### Messages Page (convo-store)

**`/messages` がスケルトンから進まない問題を修正。** `convo-store.svelte.ts` の `reload()` が `getSession()` で session を確認していたが、`setSession()` が本番環境で一度も呼ばれないため常に `null` → `listConvos()` が実行されずスケルトン永続化。`getSession()` ガードを完全除去し、直接 XRPC API を呼び出すように変更。API エラー時は `status: 'error'` に遷移。

- evidence: `$lib/w/convo-store.svelte.ts` — `reload()` から `getSession` import + guard 除去

### channel → convo 完全除去 + AT Protocol 互換拡張

**AT Protocol `chat.bsky.convo.*` を canonical、`com.etzhayyim.convo.*` を extension として統一。** `channel` 概念は frontend・PDS 双方から完全除去済み。deprecated alias と response/body compat はすべて削除。`convoId` が唯一の識別子。

**NSID 階層 (AT Protocol Layer Separation 準拠)**:

| Layer | Namespace | 用途 | 例 |
|---|---|---|---|
| **Layer 0 (AT faithful)** | `chat.bsky.convo.*` | 標準 DM — Bluesky 互換 | listConvos, getConvo, sendMessage, updateRead |
| **Layer 1 (W extension)** | `com.etzhayyim.convo.*` | etzhayyim AT Protocol extension — presence/typing/pin/forward/encryption/consent | updatePresence, sendTyping, pinMessage, setEncryption |
| **Layer 2 (Projector)** | `com.etzhayyim.projector.*` | AI PM project convo — recursive nesting, slash commands, MCP tool calling | newProjectConvo, sendProjectMessage, listProjectConvos, getProjectConvo |

**PDS handler 統合**: `chat.bsky.convo.*` write methods は `com.etzhayyim.convo.*` の unified handler に委譲。`sendMessage` → `ConvoSendMessage`、`updateRead` → `ConvoMarkRead`、`addReaction` → `ConvoReact`、`removeReaction` → `ConvoUnreact`、`deleteMessageForSelf` → `ConvoRedactMessage`、`leaveConvo` → `ConvoLeaveConvo`。Read methods (`ListConvos/GetConvo/GetMessages`) は infra handler に残存 (AT Protocol 互換レスポンス形式)。

**etzhayyim AT Protocol extension NSIDs** (AT Protocol にない `com.etzhayyim.convo.*` 独自機能):
- `updatePresence` — オンライン/オフライン/離席
- `sendTyping` — タイピングインジケーター
- `pinMessage` / `unpinMessage` — メッセージピン
- `forwardMessage` — メッセージ転送
- `setEncryption` — Signal E2E 暗号化切替
- `setProfile` — convo プロフィール設定

E2E verified: 19 NSIDs (chat.bsky.convo 4 + com.etzhayyim.convo 10 + feed/social 5) — 18 pass, 1 expected 404

- evidence: `pds-dispatch.ts` L270-290 (chat.bsky write → Convo* delegate)、L356-400 (com.etzhayyim.convo aliases)
- evidence: `pds-handlers-etzhayyim.ts` L512-576 (unified handler, `convoId` canonical)
- evidence: `convo-store.svelte.ts` L167-224 (`convos:` spread)
- evidence: `$lib/atproto-agent` service.ts L51-64 (`createProjectConvo` return type)
- evidence: `AgentProfile.svelte/+layout.svelte/+page.svelte/vibes/+page.svelte/messages/+page.svelte/LiveStage.svelte` (convoId callers)

### Follow / Message ボタン分離 + Stats

**Agent プロフィールに「フォロー」と「メッセージ」を別ボタンで表示。** フォロー = `followUser`/`unfollowUser` トグル。メッセージ = Follow + DM convo 作成 → `/convo/{convoId}` 遷移。

**Stats 行**: `投稿 | フォロワー | フォロー | deps` を常時表示。follows/followers/neighbors は起動時に eager load。各数字タップで対応タブに遷移。

| Touchpoint | Follow | Create DM | Navigate |
|---|---|---|---|
| **AgentProfile フォロー** | `followUser(did)` / `unfollowUser(did)` toggle | — | — |
| **AgentProfile メッセージ** | `followUser(did)` (if not following) | `createProjectConvo(did)` | `/convo/{convoId}` |
| **ServicesPanel app tap** | `followUser(did)` | `createProjectConvo(did)` | `/convo/{convoId}` (guest: `/profile/did:web:{host}`) |
| **ActorHero DM button** | — | `createProjectConvo(did)` | `/convo/{convoId}` |
| **SearchActors Follow/DM** | `followUser(did)` + `createProjectConvo(did)` | actor card inline buttons | `/convo/{convoId}` |
| **Messages new DM** | `followUser(handle)` | `createProjectConvo(handle)` | `/convo/{convoId}` |
| **Layout createProjectConvo** | `followUser(did)` | `createProjectConvo(did)` | `/convo/{convoId}` |
| **Home createProjectConvo** | `followUser(did)` | `createProjectConvo(did)` | `/convo/{convoId}` |

- evidence: `AgentProfile.svelte` `handleFollow()` + `handleInstall()`, `ServicesPanel.svelte` `handleOpenApp()`, `ActorHero.svelte` `handleDM()`

### Consent-Gated Data Sharing (in-messenger)

**App が DM でユーザーデータを要求する場合、messenger 内に consent カードを表示。** GNAP (RFC 9635) + W3C VC/VP + UMA 2.0 準拠。

| 層 | 実装 | Status |
|---|---|---|
| **Lexicon JSON** | `magatama:consent@1.0.0` — `request-consent`, `resolve-consent`, `revoke-consent`, `check-consent`, `list-grants` | |
| **TS Client** | `$lib/atproto-agent` — `requestConsent()`, `resolveConsent()`, `revokeConsent()`, `checkConsent()`, `listConsentGrants()` | |
| **UI** | `ConsentPrompt.svelte` — inline consent card (scope, sensitivity, selective disclosure, Allow/Deny) | |
| **Detection** | `/convo/[convoId]` — `contentType: "application/vnd.etzhayyim.consent.request"` メッセージを自動検出 | |

- evidence: `_archive/00-contracts/wit/wit/deps/magatama-consent/package.wit` (archived 2026-04-12), `$lib/w/ConsentPrompt.svelte`, `routes/convo/[convoId]/+page.svelte`

### XRPC E2E Coverage

**22 NSID E2E verified (2026-03-25)。** 全 social action + feed read + actor + graph + notification + messaging + repo/identity が動作確認済み。

| Category | NSIDs | Status | 修正 (2026-03-25) |
|---|---|---|---|
| **Feed Read** | getTimeline, getDiscoverFeed, getAuthorFeed, getPostThread, getLikes, getRepostedBy, searchPosts | 全 OK | `getDiscoverFeed` NSID dispatch 追加 |
| **Feed Write** | like, unlike, repost, unrepost | 全 OK | `body.subject.uri/cid` nested format 対応 |
| **Bookmark** | createBookmark, deleteBookmark | 全 OK | SQL label typo `Createbookmark` → `CreateBookmark` + `rec.uri` fallback |
| **Graph Write** | follow, unfollow | 全 OK | DID string subject マッチ (`body.did`/`body.subject` string) |
| **Actor** | getProfile, searchActors | 全 OK | — |
| **Graph Read** | getFollows, getFollowers | 全 OK | — |
| **Notification** | listNotifications, getUnreadCount | 全 OK | — |
| **Messaging** | listConvos, createProjectConvo | 全 OK | `body.peerDid` param + `{convo}` response 形式。deprecated param は除去済み |
| **Repo/Identity** | resolveHandle, getRecord, describeServer | 全 OK | — |

- evidence: E2E curl test suite (etzhayyim authn token + atproto.etzhayyim.com/xrpc)
- evidence: `pds-handlers-repo.ts` L126-141 (subject nested), L196-206 (DID string match)
- evidence: `pds-handlers-etzhayyim.ts` L519 (peerDid param), L521-528 (convo response)
- evidence: `pds-dispatch.ts` L162 (getDiscoverFeed alias)

### XRPC NSID Alias Coverage

**`$lib/atproto-agent` service.ts の atProcedure NSID と PDS dispatch の NSID_TO_METHOD を完全一致。** Client NSID alias 追加で 501 エラーを解消。

| Category | Client NSID (alias) | Dispatch NSID (canonical) | Method |
|---|---|---|---|
| **Social write** | `app.bsky.feed.like/unlike/repost/unrepost` | (new) | `Like/Unlike/Repost/Unrepost` |
| **Social graph** | `app.bsky.graph.follow/unfollow/block/unblock` | (new) | `Follow/Unfollow/Block/Unblock` |
| **Threadgate** | `app.bsky.feed.threadgate/removeThreadgate` | (new) | `CreateThreadgate/DeleteThreadgate` |
| **Convo short** | `com.etzhayyim.projector.sendProjectMessage/edit/redact` | `sendProjectMessage/editMessage/redactMessage` | alias |
| **RTC call** | `com.etzhayyim.rtc.sendCallOffer/sendCallAnswer/sendCallICE/hangupCall` | `sendOffer/sendAnswer/sendIce/hangup` | alias |
| **RTC VAPID** | `com.etzhayyim.rtc.getVAPIDPublicKey` | `getVapidKey` | alias |

- evidence: `50-infra/cloudflare/workers/atproto/src/pds-dispatch.ts` NSID_TO_METHOD
- evidence: `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts` XRPC_WRITE_METHODS/XRPC_DELETE_METHODS
- test: 298 PDS tests pass, 22 NSIDs verified E2E (0 returns 501)

### CRITICAL: Profile LiveStage (KAMI Engine + AT Protocol XRPC event stream)

**Agent プロフィールの header は baminiku KAMI ライブステージ。** Agent が常時 "alive" で動く 3D virtual stage。全インタラクションは AT Protocol DM convo 経由 (atproto.etzhayyim.com)。

| 機能 | AT Protocol API | contentType |
|---|---|---|
| **3D ステージ** | `atproto.etzhayyim.com/xrpc/com.etzhayyim.convo.getConvo` | — |
| **Agent avatar** | 常時アニメーション (idle/dancing/waving/talking) | — |
| **リアルタイムチャット** | `createProjectConvo(agentDID)` (`com.etzhayyim.projector.createProjectConvo`) → `sendProjectMessage(ch, text)` (`com.etzhayyim.projector.sendProjectMessage`) → `subscribeWStream(SSE)` で応答受信 | `text/plain` |
| **Emote** | `sendProjectMessage(ch, json)` (`com.etzhayyim.projector`) + client-side floating animation | `application/vnd.etzhayyim.baminiku.emote` |
| **投げ銭** | `sendProjectMessage(ch, json)` (`com.etzhayyim.projector`) → ComAtprotoSyncSubscribeRepos → WRecord + 3D effect | `application/vnd.etzhayyim.baminiku.tip` |
| **音楽** | BGM 表示 | — |
| **LIVE バッジ** | 赤 LIVE indicator + viewer count | — |

**データフロー**: `LiveStage.svelte` → `ensureConvo()` (lazy DM 作成 + 履歴ロード + SSE 購読) → `sendProjectMessage()` via `atproto.etzhayyim.com` → baminiku ComAtprotoSyncSubscribeRepos → murakumo LLM → DM reply → SSE → UI 表示

**認証**: `getSession()` で認証チェック。未ログイン時は chat input の代わりに CTA 表示。emote/tip ボタンも認証必須。

**禁止**: `{appHost}` / `{nanoid}.etzhayyim.com` への直接 API 呼び出し (Data Gateway Consolidation 違反)

**コンポーネント**: `AgentProfile.svelte` → `LiveStage.svelte` (header) + compact info bar + tabs

### Subdomain → yoro Redirect + iframe Auto-Embed

`{nanoid}.etzhayyim.com/` への browser アクセスは dispatcher が `yoro.etzhayyim.com/profile/did:web:{host}?app=1` に 301 redirect。`?app=1` query param により AgentProfile の iframe embed (`{nanoid}.etzhayyim.com/?embed=1`) が自動展開される。API/manifest/static/embed request は user Worker に直接 dispatch (redirect なし)。

### Hero Section App Preview — Profile-Embedded embedUrl (Shannon optimized)

**`getProfile` が `embedUrl` + `uiType` を直接返す。** `/_app/meta` の追加 fetch は不要 (fallback のみ)。

```
getProfile(did) → { ..., uiType: "iframe", embedUrl: "https://murakumo.etzhayyim.com/chat" }
  → iframe src={profile.embedUrl}    ← 1 fetch で完結
```

**データフロー**: `etzhayyim deploy` → `registerApp` XRPC → PDS App node に `ui_type` + `embed_url` 保存 → `getProfile` SQL → response に `uiType` + `embedUrl`。

`AgentProfile.svelte` `loadAppPreview()` fast path: `actorData.embedUrl` + `actorData.uiType` があれば即座に `appPreview` を構築。`/_app/meta` fetch をスキップ。

**Fallback** (profile に embedUrl がない legacy app): `/_app/meta` fetch。

hero section は `uiType` + `performerType` × `hasEmbed` (embedUrl 有無) で決定:

| 条件 | heroKind | Aspect | 用途 |
|---|---|---|---|
| `uiType === 'appview'` + embed + playUrl | **`game`** | 9:16, max 80vh | KAMI Engine ゲーム即プレイ |
| `service` + embed | `iframe` | 4:3, max 70vh | App interactive preview |
| `system` + embed | `iframe` | 4:3, max 70vh | System dashboard |
| `person` | `baminiku` | — | KAMI LiveStage |
| `organization` + embed | `iframe` | 4:3, max 70vh | Org portal |
| `organization` + `isSelf` | `org-banner` + Org tab | — | Org management (path DIDs, members, DID switcher) |
| embed なし | `app-card` / `status` / `org-banner` | — | Static hero card |

- evidence: `AgentProfile.svelte` — fast path `actorData.embedUrl` check before `/_app/meta` fetch
- evidence: `pds-handlers-feed.ts` — `getProfile` returns `uiType` + `embedUrl` from App node
- evidence: `pds/src/index.ts` — `registerApp` stores `ui_type` + `embed_url`
- evidence: `deploy.go` — `registerProfileToYata` sends `uiType` + `embedUrl`

### CRITICAL: Search = Actors-First (AT Protocol 用語)

**Search のデフォルトタブは Actors (AT Protocol 用語)。** `app.bsky.actor.searchActors` を使用。「Agent」ではなく「Actor」が AT Protocol 標準。

| Tab | 用途 | データソース (AT Protocol Lexicon) |
|---|---|---|
| **Actors** (default) | AT Protocol Actor 検索 (登録日/更新日ソート) | `searchActors("etzhayyim", {limit:25})` (`app.bsky.actor.searchActors`) → PDS SQL `STARTS WITH` + `did:web:` server-side filter → `indexedAt` 付き response → client-side sort (re-fetch なし)。PDS 側: `:Profile` + `:App` SQL ノード (PascalCase) |
| Posts | 投稿セマンティック検索 (client embed → vector) + text fallback | `searchPosts({q, vector})` (`app.bsky.feed.searchPosts` POST, client embedding → kagami ivfSearch on PostText) |
| People | ユーザー検索 | `searchActors()` (`app.bsky.actor.searchActors`) |

Actor カード: Avatar + displayName + DID + description + sensitivity badge + 日時表示 + ソート切替 (Registered/Updated) → タップで `/profile/{did}`

**Search Performance (2026-03-25)**:

| 修正 | Before | After |
|---|---|---|
| SQL `CONTAINS` → `STARTS WITH` | フルスキャン O(N) | `display_name`/`handle` index 活用 O(log N)。`description` のみ `CONTAINS` 維持 |
| `did:web:` filter server-side | client で 100 件取得後 filter | PDS SQL `WHERE p.did STARTS WITH "did:web:"` |
| `limit: 100` → `limit: 25` | 100 件転送 | 25 件転送 |
| `indexedAt` response 付与 | PDS が `created_at` 未返却 → client sort 空振り | `p.created_at AS created_at` → `indexedAt` で返却 |
| ソート切替 client-only | sort 切替で re-fetch | `sortActors()` で in-memory sort (XRPC 発行なし) |
| `$effect` + `onMount` 二重発火防止 | mount 時 2 回 `searchActors` 発火 | `mounted` guard で `$effect` を mount 後のみ有効化 |
| `cyCached` auth-independent cache (2026-03-27) | 認証済みと未認証で別キャッシュ → yata cold start 時に空結果がキャッシュされログイン時 actors 非表示 | cross-actor listing (SearchActors/GetSuggestions) は全ユーザー同一キャッシュ。ActorVisibilityGate は handler 内で row ごとに適用 |

- evidence: `pds-handlers-feed.ts` L563-567 — `cyCached(..., 60)`
- evidence: `pds.ts` L459-462 — `STARTS WITH` + `did:web:` + `created_at` return
- evidence: `search/+page.svelte` L43-91 — `fetchActors(limit:25)` + `sortActors()` + `mounted` guard

**Profile 登録**: `etzhayyim deploy` → `com.atproto.admin.registerApp` XRPC (DID auth) → PDS が `:Profile` + `:App` + `:DIDDocument` + `:AgentKey` を yata SQL に MERGE (Pipeline + mergeRecord durable write)。`searchActors` がこれらのノードを検索

### AT Protocol 用語対応 (CRITICAL)

**yoro は AT Protocol に忠実な用語を使用する。AT Protocol 独自用語は internal transport のみ。**

| AT Protocol 用語 | etzhayyim AT Protocol extension | UI 表示 | 使い分け |
|---|---|---|---|
| **Actor** (`app.bsky.actor`) | App (performer) | "Actor" | 全 social context で使用 |
| **Record** (`com.atproto.repo`) | WEnvelope (内部型) | — | 外部 API は record、内部型名は W prefix 維持 |
| **Convo** (`chat.bsky.convo`) | Convo (`convoId`) | "Messages" | DM は AT Protocol `convo` 準拠。legacy alias は除去済み |
| **Post** (`app.bsky.feed.post`) | — | "Post" | AT Protocol そのまま |
| **Profile** (`app.bsky.actor.getProfile`) | — | "Profile" | AT Protocol そのまま |
| — (AT Protocol に存在しない) | HandleStream (wRPC) | — | etzhayyim AT Protocol extension |
| — (AT Protocol に存在しない) | Signal E2E | — | etzhayyim AT Protocol extension |
| — (AT Protocol に存在しない) | SQL graph query | — | etzhayyim AT Protocol extension |

### CRITICAL: DM Agent Toolbar

**DM 相手が `did:web:` agent の場合、agent の tools/capabilities をツールバーとして表示。**

- Agent tools 取得: canonical `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` (compat: `mcp.etzhayyim.com/mcp`) に `tools/list` (JSON-RPC 2.0) + `/_app/meta` fallback (並列)
- Tools (紫ボタン): wrench icon → タップで `/toolName` メッセージ送信 + agent API 直接呼び出し
- Queries (青ボタン): search icon → タップで実行
- ツールバー位置: composer の直上、横スクロール

**data endpoint は yoro.etzhayyim.com に公開しない。** Browser は `atproto.etzhayyim.com/xrpc/{NSID}` に直接接続。

### MCP Tool Calling in Convo

**DM で agent にメッセージを送ると、Murakumo LLM + MCP tool calling で agent の capabilities を実行。**

| Step | 処理 |
|---|---|
| 1. Tool Discovery | `ActorCapability` graph query + `/_app/meta` fallback |
| 2. System Prompt | `convoSystemPrompt` (magatama.jsonld) or default + tools list |
| 3. LLM Call | Murakumo `qwen3-vl-8b` with `tools` + `tool_choice: auto` |
| 4. Tool Execution | DISPATCHER → app Worker XRPC → result |
| 5. Tool Result | `contentType: application/vnd.etzhayyim.mcp.tool-result` メッセージ |
| 6. Summary | Second LLM call with tool results → final reply |

**convoSystemPrompt**: `magatama.jsonld` の `profile.convoSystemPrompt` が優先。未設定時は `displayName` + `description` から自動生成。

- evidence: `pds-handlers-etzhayyim.ts` — MCP tool discovery + tool_calls execution + summary loop

### CRITICAL: Local Browser LLM (Opt-In + GraphRAG Domain Coverage)

**Messenger / Project convo の LLM 応答はブラウザローカル推論を優先。** モデルロードは **opt-in** (ヘッダーのモデル選択で有効化、`localStorage` に永続化)。PDS server-side LLM はフォールバック。

| コンポーネント | ファイル | 役割 |
|---|---|---|
| **Ameno Engine (PRIMARY)** | `$lib/provider/ameno.svelte.ts` | `@etzhayyim/ameno` Svelte 5 provider — transformers.js ONNX + WebGPU + per-actor LoRA merge + RAG-LoRA context injection。Gemma 4 E2B multimodal (2.3B) |
| **WebLLM Engine (SECONDARY)** | `$lib/provider/local-llm.svelte.ts` | WebLLM (`@mlc-ai/web-llm`) エンジン — MLC compiled models。Qwen 3.5 series。Ameno fallback |
| **Embedding Engine** | `$lib/provider/embedding.svelte.ts` | Transformers.js multilingual-e5-small (384d, 100+ langs, 45MB)。auto-init on mount。Search + post creation + search_agents で使用。$0 |
| **GraphRAG Engine** | `$lib/provider/graph-rag.svelte.ts` | Design 1+5: Domain-aware lazy loading + federated Parquet query + dual-backend LLM (ameno → WebLLM fallback) |
| **kagami Graph Store (RisingWave)** | `$lib/graph/kagami-store.svelte.ts` | RisingWave graph via PDS XRPC。`query()` / `loadLabel()` / `federatedQuery()` / `listAvailableLabels()` |
| **Browser Inference State** | `$lib/provider/browser-inference-state.svelte.ts` | GPU probe + murakumo gateway 接続 + モデル選択 |
| **Browser Gateway** | `$lib/provider/browser-gateway-client.ts` | モデル定義 (`BROWSER_INFERENCE_MODELS`) + WebSocket protocol |
| **Opt-In Init** | `+layout.svelte` | LLM: `localStorage('yoro-local-llm-enabled') === '1'` で opt-in。Embedding: 全ユーザー auto-init (45MB OPFS cached) |

**Dual-Backend Architecture (ameno + WebLLM)**:

```
User sends message
  ├─ Ameno ready? (Gemma 4 E2B, transformers.js ONNX + WebGPU)
  │   YES → ameno.chatCompletion(messages, { ragContext }) + LoRA adapter merge
  │         → immediate UI display + PDS persist
  │
  ├─ WebLLM ready? (Qwen 3.5, MLC compiled, Web Worker)
  │   YES → localLLM.chatCompletion(messages) fallback
  │
  └─ NO → PDS server-side LLM (Murakumo fleet)
```

**Backend 選択基準:**

| Backend | Package | Models | LoRA | RAG | Use Case |
|---|---|---|---|---|---|
| **Ameno (primary)** | `@etzhayyim/ameno` | Gemma 4 E2B (ONNX, 2.3B) | per-actor WebGPU merge | ameno RAG-LoRA pipeline | Multimodal inference + personalized response |
| **WebLLM (secondary)** | `@mlc-ai/web-llm` | Qwen 3.5 0.8B/2B/4B (MLC) | なし | keyword + federated | Fast text-only inference |
| **PDS server (fallback)** | — | qwen3-vl/qwen3-30b/qwq-32b | — | — | Heavy reasoning, image gen, slash commands |

**モデル選択 (credits page / header pulldown):**

| Model | Params | VRAM (Q4) | GPU Tier | Tag |
|---|---|---|---|---|
| Qwen 3.5 0.8B | 0.8B | ~520MB | g1+ | Fast |
| Qwen 3.5 2B | 2B | ~1.4GB | g2+ | — |
| Gemma 4 E2B | 2.3B (5.1B total, PLE) | ~2.5GB | g2+ | Multimodal (text/image/audio/video) |
| Qwen 3.5 4B | 4B | ~2.6GB | g3+ | Best |

**Opt-in persistence**: `localStorage('yoro-local-llm-enabled')` = `'1'`、`localStorage('yoro-local-llm-model')` = model ID。ヘッダーのモデル選択プルダウンで変更時に自動保存。未 opt-in ユーザーはリロード時にモデルダウンロード/GPU ロードが走らない。

**Browser Image Generation (SD 1.5, /credits):**

| コンポーネント | ファイル | 役割 |
|---|---|---|
| **Diffusion Worker** | `$lib/provider/diffusion-worker.ts` | Web Worker — ONNX Runtime WebGPU で SD パイプライン実行。Sequential load/unload: CLIP → UNet → VAE |
| **Diffusion State** | `$lib/provider/local-diffusion.svelte.ts` | Svelte 5 singleton state manager。`useLocalDiffusion()` composable |
| **Model Definitions** | `$lib/provider/browser-gateway-client.ts` | `BROWSER_DIFFUSION_MODELS` — SD 1.5 (B2 CDN hosted ONNX) |

SD 1.5 ONNX (FP16 UNet) を `cdn.etzhayyim.com/models/sd15/` から sequential fetch。Peak VRAM = UNet (~1.7GB)。OPFS cache。詳細: `60-apps/etzhayyim-project-gazo/CLAUDE.md`

- evidence: `$lib/provider/diffusion-worker.ts` — CLIP+UNet+VAE sequential pipeline
- evidence: `$lib/provider/local-diffusion.svelte.ts` — Svelte 5 singleton state
- evidence: `routes/credits/+page.svelte` — Image Generation section UI

**推論優先順位:**

```
User sends message
  ├─ Slash command (/task, /think, /image, etc.)
  │   → PDS server-side (always, special handling required)
  │
  ├─ Local LLM ready? (opt-in 済みの場合のみ)
  │   → YES: GraphRAG (domain-aware) → ローカル推論 → 即座に応答表示
  │   │      + PDS persist (Hyperdrive → RisingWave, durable)
  │   │
  │   → NO: PDS server-side LLM (Murakumo fleet)
  │          → 応答を待って表示
  │
  └─ GraphRAG (Design 1+5: RisingWave + Local LLM)
      → label classification → lazy load → RisingWave query → federated fallback
      → context injection → Local LLM → grounded response
```

**GraphRAG アーキテクチャ (Design 1+5: Domain-Aware Lazy Loading + Federated Parquet Query)**:

```
User message: "TSMCの半導体サプライチェーンについて教えて"
  ↓
1. Label classification (keyword fast path + LLM enhanced):
   keyword "半導体","TSMC" → [Post, Profile, Article, CohortCompany]
  ↓
2. Lazy loading: Article, CohortCompany not cached → loadLabel() on-demand (5s timeout)
  ↓
3. RisingWave query via Hyperdrive:
   MATCH (n:Article) WHERE n.text CONTAINS 'TSMC'
   RETURN n ORDER BY n.updated_at DESC LIMIT 30
  ↓
4. Federated fallback (if local < 3 rows):
   graph SQL path → RisingWave filter (TSMC)
   → server-side SQL CONTAINS filter → RisingWave → merge → re-query
  ↓
5. Context formatting (3000 chars max):
   [Article] title: 半導体市場2026Q1, source: handotai.etzhayyim.com
   [CohortCompany] name: TSMC, sector: semiconductor
  ↓
6. System prompt injection + Local LLM → knowledge-grounded response
```

**Design 1: Domain-Aware Lazy Loading**:
- `classifyLabels()` — keyword マッチ (0ms) + LLM 分類 (`listAvailableLabels` → JSON 配列)
- `DOMAIN_LABEL_MAP` — 30+ keyword → label マッピング (半導体→Article/CohortCompany, 法律→Statute 等)
- 必要 label のみ on-demand で `loadLabel()` (Post/Profile は core で常時ロード)

**Design 5: Federated Parquet Query**:
- `federatedQuery(label, filter, limit)` — graph SQL path → RisingWave でフィルタ
- ローカル結果が 3 行未満の場合に自動 fallback
- 別 cache key (`snapshot:f-{keyword}.parquet`) でフィルタ済み Parquet をキャッシュ
- `listAvailableLabels()` — PDS `com.etzhayyim.kagami.listLabels` XRPC (14+ labels、5min cache)

**Data flow**:
```
Write: PDS XRPC → graph write path → RisingWave Stream Load → MV refresh (event-driven, fire-and-forget)
Read:  PDS XRPC → CF Cache API (60s) → graph SQL path → RisingWave (MV transparent rewrite)
```

### Materialized View による高速化 `[IMPLEMENTED 2026-04-08]`

12 個の RisingWave Async MV がイベントドリブンで更新。SQL クエリは RisingWave が自動的に MV にルーティング。

| 画面 | Before (MPP JOIN) | After (MV + Cache) | MV |
|---|---|---|---|
| **Profile** (followers/following/posts) | 5 parallel queries, 50-100ms | 1 query, 5-10ms | `mv_actor_stats` |
| **Post engagement** (likes/reposts/replies) | 3 count queries, 100-200ms | 3 MV lookups, 10ms | `mv_likes_by_post`, `mv_reposts_by_post`, `mv_replies_by_post` |
| **Feed** (post + author) | JOIN per post, 50ms | pre-joined MV, 10ms | `mv_feed_with_author` |
| **Actor search** | full scan, 500ms | indexed MV, 50ms | `mv_actor_search` |
| **GraphRAG federated** | loadLabel → full table, 200ms | CF Cache hit, 0ms (60s TTL) | CF Cache API |

### SQL パーサー拡張 `[IMPLEMENTED 2026-04-08]`

`OPTIONAL MATCH` (LEFT JOIN)、`WITH` (CTE)、`UNION [ALL]` をフルサポート。フロントエンドの workaround（個別 MATCH に分解）を将来的に本来の構文に戻せる。

**暗号化アーキテクチャ**:

| 層 | 暗号化 | Key | Server が見えるもの |
|---|---|---|---|
| **Write** | AES-256-GCM (per-label HKDF key) | `PARQUET_MASTER_KEY` → `HKDF(master, label:tier)` | Ciphertext only (B2) |
| **Transport** | B2 HTTPS | TLS | Ciphertext (B2 egress) |
| **Client Read** | AES-256-GCM decrypt | `getLabelKey` XRPC → session-wrapped key | — (client のみ) |
| **RisingWave Query** | Plaintext (server-side) | — | — (query result only) |

- evidence: `50-infra/cloudflare/workers/atproto/src/parquet-crypto.ts` — HKDF + AES-256-GCM encrypt
- evidence: `$lib/graph/parquet-crypto-client.ts` — Client decrypt + key cache
- evidence: `$lib/graph/kagami-store.svelte.ts` — `decryptRows()` + `federatedQuery()` + `listAvailableLabels()`
- evidence: `$lib/provider/graph-rag.svelte.ts` — Design 1+5 GraphRAG engine
- evidence: `$lib/provider/local-llm.svelte.ts` — WebLLM engine + chatCompletion
- evidence: `+layout.svelte` — opt-in auto-load (`localStorage` check)
- evidence: `routes/projects/[convoId]/+page.svelte` — GraphRAG first, PDS fallback
- evidence: `_archive/30-graph/kagami-live-260414/CLAUDE.md` §Architecture RisingWave

### Projector PM Tools (Research + DID Expansion)

**Projector (`/projects/[convoId]`, `com.etzhayyim.projector.*`) の PM agent に 5 つの built-in ツール。** LLM が text-based `[TOOL_CALL: name(args)]` で自動チェーン。設計: `60-apps/etzhayyim-project-projector/CLAUDE.md`

| Tool | 説明 | 用途 |
|---|---|---|
| `pm.search_agents` | Platform 上の AI agent を embedding semantic search (multilingual-e5-small 384d client-side) + keyword fallback で検索 | 調査に適した agent を発見 |
| `pm.invite_agent` | Agent をプロジェクトに招待 | 専門 agent の tools を利用可能に |
| `pm.web_research` | site.etzhayyim.com 経由で URL 取得 → Markdown | 外部情報収集 |
| `pm.create_entity_did` | 発見したエンティティに path-based DID 作成 | DID ドメイン拡張 |
| `pm.graph_search` | ナレッジグラフ検索 | 既存エンティティ確認 (DID 重複防止) |

**Research → DID Expansion ワークフロー** (「〇〇の情報を調べて集めて」で自動実行):

```
User: "半導体サプライチェーンの情報を調べて集めて"
  ↓
PM Agent (LLM + text-based tool calling):
  1. [TOOL_CALL: pm.graph_search({"query":"半導体"})]
     → 既存エンティティ確認 (重複防止)
  2. [TOOL_CALL: pm.web_research({"url":"https://example.com/semiconductor","topic":"半導体"})]
     → site.etzhayyim.com 経由 fetch → Markdown 返却
  3. [TOOL_CALL: pm.create_entity_did({"path":"tsmc","displayName":"TSMC / 台湾積体電路製造","description":"世界最大の半導体ファウンドリ","category":"company","website":"https://www.tsmc.com"})]
     → did:web:{host}:tsmc 作成 + Profile 登録
  4. [TOOL_CALL: pm.create_entity_did({"path":"samsung-foundry","displayName":"Samsung Foundry","description":"Samsung の半導体製造部門","category":"company"})]
     → did:web:{host}:samsung-foundry 作成
  ↓
PM reply: "半導体サプライチェーンの調査完了。以下の DID を作成しました: ..."
```

**Slash commands** (`sendProjectMessage` handler):

| Command | Model | 用途 |
|---|---|---|
| `/image {prompt}` | Murakumo WAI-REAL | 画像生成 |
| `/think {prompt}` | qwen3-30b | Deep reasoning (`<think>` tags) |

- evidence: `pds-handlers-etzhayyim.ts` L2434-2500 — PM built-in tools (search/invite/web_research/create_entity_did/graph_search)
- evidence: `pds-handlers-etzhayyim.ts` L2577-2685 — Tool execution handlers (search_agents/invite_agent/web_research/create_entity_did/graph_search → cross-actor dispatch)
- evidence: `pds-handlers-etzhayyim.ts` L2221-2387 — Slash commands (/image, /think)

### Profile eSIM Management (Celler Integration)

**自分のプロフィールに「SIM」タブを追加。** Celler (celler.etzhayyim.com) 経由で Telnyx Wireless eSIM の契約・管理が可能。

| 機能 | XRPC NSID | 説明 |
|---|---|---|
| **eSIM 発行** | `com.etzhayyim.apps.celler.provisionEsim` | Telnyx API → QR code + activation code |
| **アクティベート** | `com.etzhayyim.apps.celler.activateEsim` | ICCID → enable |
| **一時停止** | `com.etzhayyim.apps.celler.suspendEsim` | ICCID → disable |
| **使用量確認** | SQL `(:ESimProfile)` query | data_used/remaining MB |

**オンボーディングバナー**: 自分のプロフィール表示時に eSIM 未契約の場合、emerald グラデーションのバナーで契約を促進。Welcome フローにも「eSIM で繋がる」ステップを追加。

- evidence: `routes/profile/[handle]/+page.svelte` — SIM tab + eSIM state management + onboarding banner
- evidence: `$lib/components/YoroAuthGate.svelte` — welcome step + feature pill

### Profile Cross-App Scores (Dojo / Joucho)

**ActorHero に dojo / joucho スコアをバッジ表示。** Profile ロード時に `atproto.etzhayyim.com/xrpc/com.etzhayyim.kagami.graph.query` で並列 Graph query (2s timeout、non-blocking)。

| Score | SQL Label | 表示 | 色 |
|---|---|---|---|
| **Dojo** | `:dojo_drill_completed` | avg score + drill count | emerald |
| **Joucho** | `:review` (joucho_score) | grade (S/A/B/C/D) + avg score + review count | grade-based (S=amber, A=blue, B=green, C=yellow, D=gray) |

- evidence: `$lib/actor/ActorHero.svelte` — scores section (between stats and badges)
- evidence: `/profile/[handle]/+page.svelte` — `fetchActorScores()` parallel SQL query
- evidence: `$lib/actor/types.ts` — `ActorScores` interface

### Profile Feed Actions (Like/Repost/Reply)

**ProfilePanel (`$lib/superapp/ProfilePanel.svelte`) のフィード投稿に Like/Repost/Reply アクションバーを実装。** VibesPanel と同じパターン。`likePost`/`unlikePost`/`repost`/`unrepost` を `$lib/atproto-agent` から import。`likedItems`/`repostedItems` Set で optimistic UI。色: Reply=#1185FE, Repost=#00BA7C, Like=#F91880。

### Bluesky-style Compose Modal

**Bluesky social-app を参考にした compose modal。** FAB → modal open → 投稿 → 自動 close。

**Layout (Bluesky 準拠)**:
- **Top bar**: Cancel (左) + Post ボタン (右、`#1185FE` blue、disabled when empty)
- **Body**: Avatar (42px) + textarea (17px, min-height 120px, leading-snug) + embeds (scrollable)
- **Bottom toolbar**: Image / Video / Threadgate (globe/lock icon cycle) / Content warning (shield) | Circular character counter (SVG progress ring、残り20以下で数字表示)

**機能**: image (4枚、2列 grid)、video upload (progress bar)、link card auto-detect、quote post、@mention typeahead、threadgate (everyone/mentioned/following/nobody)、content warning (sexual/nudity/porn/gore cycle)、300 grapheme limit、Cmd+Enter submit、Escape close、backdrop click close。

**ALT text**: Bluesky 風 `+ ALT` / `ALT ✓` badge (bottom-left of image)。

- evidence: `$lib/w/PostComposer.svelte` — full rewrite
- evidence: `+layout.svelte` L600 — `<PostComposer bind:open={showComposePost}>`

### XRPC Auth Bridge (Passkey → $lib/atproto-agent)

**`$lib/atproto-agent` XRPC client に `setTokenProvider()` を追加。** Passkey session JWT を XRPC Bearer token として PDS に送信。authn.etzhayyim.com Passkey interface (`signIn`, `signUp`, `getSessionToken`) — `passkey.ts` が実装。

**設計**: `$lib/atproto-agent` の `xrpcFetch` は `_session?.accessJwt` (AT Protocol session) を優先し、fallback で `_tokenProvider()` (Passkey session JWT) を使用。

**解決**: 外部 token provider hook pattern。

| 層 | 実装 |
|---|---|
| **`$lib/atproto-agent` client.ts** | `setTokenProvider(provider: () => Promise<string \| null>)` — 外部 token provider 登録 |
| **`xrpcFetch`** | `_session?.accessJwt` → fallback → `_tokenProvider()` (Passkey session JWT) |
| **yoro `+layout.svelte`** | `setTokenProvider(getSessionToken)` — Passkey `getSessionToken()` を橋渡し |

**Token 解決優先順位**: (1) `opts.bearerToken` → (2) `_session.accessJwt` → (3) `_tokenProvider()` (Passkey AT Protocol session JWT)

- evidence: `10-protocol/atproto/ts/src/client.ts` — `setTokenProvider()` + `_tokenProvider` fallback in `xrpcFetch`
- evidence: `+layout.svelte` — `import { setTokenProvider } from '$lib/atproto-agent'` + `setTokenProvider(getSessionToken)`

### Post View Count (Twitter-style Impressions)

**Twitter/X 風の view 数 (impression count) を全 feed に表示。** `app.bsky.feed.sendInteractions` で view event を記録し、PDS が `Interaction` label から per-post view count を集計。

| 層 | 実装 |
|---|---|
| **PostView type** | `viewCount: number` フィールド追加 (`$lib/atproto-agent` types.ts) |
| **PDS buildPostView** | `viewCount: 0` default (`pds-helpers.ts`) |
| **PDS SendInteractions** | per-interaction 個別 record (`uri`, `event`, `createdAt`) を SQL に書込 |
| **PDS feed handler** | `Interaction` label query → `event === "view"` を per-post URI カウント → `post.viewCount` attach |
| **PDS thread handler** | 同上パターンで GetPostThread にも viewCount 付与 |
| **Client tracking** | feed load / post detail 表示時に `sendInteractions([{uri, event: 'view'}])` fire-and-forget |
| **UI display** | Analytics chart icon + count (全 feed view: Home, Profile, AgentProfile, VibesPanel, ProfilePanel, hashtag, embed, post detail) |

**表示条件**: `viewCount > 0` の場合のみ表示。アイコン: chart/analytics SVG (`M3 3v18h18` + `M7 16l4-8 4 4 4-6`)。Post detail では "N 表示" テキスト形式。

- evidence: `pds-helpers.ts` L305 — `viewCount: 0` in buildPostView
- evidence: `pds-handlers-feed.ts` — Interaction label query + viewCounts Map + post.viewCount attach
- evidence: `$lib/atproto-agent` types.ts — `viewCount: number` in PostView
- evidence: `+page.svelte` — `sendInteractions` import + trackViews + chart icon display
- evidence: `post/[rkey]/+page.svelte` — viewCount derived + "N 表示" engagement stat

### MCP Tools in Agent Profile

**Agent profile の「ツール」タブに MCP tools を表示。** `AgentProfile.svelte` が 4 層 fallback で tools を取得しレンダリング (紫 wrench icon + MCP badge)。

**Discovery 4 層 fallback:**
1. canonical `mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` (compat: `mcp.etzhayyim.com/mcp`) に `tools/list` POST (JSON-RPC 2.0, public — 認証不要) → `:ActorCapability` / `:ActorCard` / DISPATCHER `/_app/meta` graph query
2. `actor.tools` prop (SSR `+page.server.ts` が `/_app/meta` をサーバーサイドで fetch → `data.appTools` → `actorData.tools` で渡す。CORS 不要)
3. `{nanoid}.etzhayyim.com/_app/meta` 直接 fetch (CORS header `Access-Control-Allow-Origin: *` が `magatama-host-sdk` に追加済み。user Worker 再デプロイ後に動作)
4. PDS `getProfile` response の `service.capabilities` (capabilities prop fallback)

**CORS fix:** `20-actors/magatama/sdk/magatama-host-sdk/src/index.ts` の `/_app/meta` レスポンスに `Access-Control-Allow-Origin: *` を追加。全 user Worker 再デプロイで反映。再デプロイ前は Layer 2 (SSR server-side fetch) が primary fallback として機能。

**MCP Auth policy:** Read-only methods (`tools/list`, `resources/list`, `initialize`, `ping`) は public (認証不要)。Mutation methods (`tools/call`) は AT Protocol session JWT or ES256 Service Auth 必須。evidence: `50-infra/cloudflare/workers/atproto/src/app.ts` (`isMcpReadOnly`)

**Capabilities pipeline:**
- `magatama.jsonld` `profile.capabilities` → `etzhayyim deploy` → `__APP_CAPABILITIES_JSON__` → entry.ts `/_app/meta` に `capabilities`/`tools` 出力 (+ CORS header)
- `etzhayyim deploy` → `registerProfileToYata` → PDS `com.atproto.admin.registerApp` → `capabilities_json` を `:App` graph node に MERGE
- PDS `getProfile` SQL → `m.capabilities_json` → `service.capabilities` に parse して返却
- SSR `+page.server.ts` → `getAppMetaTools(appHost)` → `/_app/meta` server-side fetch (CORS 不要) → `data.appTools`

### Org Management in Profile `[DESIGN]`

**組織管理 UI は profile ページ (`/profile/[handle]`) に統合。** 独立した org 管理ページは作らない。Backend は `moderator.etzhayyim.com` XRPC。

#### Org-Account-Based Identity

全アカウントはデフォルトで org DID (`performerType: organization`, `org_type: personal`)。person profile は org 内の `:person` path-based DID。設計詳細: `60-apps/etzhayyim-project-moderator/CLAUDE.md` §Org-Account-Based Identity Design。

#### Profile Org Tab (`isSelf && isOrgController`)

`AgentProfile.svelte` の tabs に「Org」タブを追加。自分の profile かつ org controller の場合のみ表示。

```
AgentProfile tabs (isSelf && org_type !== 'personal'):
  Posts | Org | Tools | Graph | Follows
              ↑
  ├─ Org Info: org_type, org_name, created_at
  ├─ Path DIDs: 一覧 + 作成 + 無効化 (「部署追加」ボタン)
  ├─ Members: 一覧 + 招待 + ロール変更 + 除外
  └─ DID Switcher: active_did 切替プレビュー
```

#### active_did Switcher

- **Profile header**: avatar tap → dropdown で org 内 path DID リスト表示 → 選択で active_did 切替
- **Settings `/settings/account`**: DID Switcher UI (フル版、全 path DID + ロール表示)
- 切替後の posts/likes/follows は新 active_did で実行

#### Data Flow

```
yoro Profile Org Tab
  → XRPC moderator.etzhayyim.com/list_org_dids (account_did)
  → XRPC moderator.etzhayyim.com/create_org_did (path, display_name)
  → XRPC moderator.etzhayyim.com/invite_member (org_did, member_person_did, role)
  → authn.etzhayyim.com/rpc/switch-active-did (new_active_did) → session 更新
```

### AppShell Flex Layout Fix

**AppShell コンテンツラッパーに `flex flex-col overflow-hidden` を追加。** コンテンツラッパーが flex コンテナでなかったため、子の `<main class="flex-1 overflow-y-auto">` の高さ制約が効かず、コンテンツがタブバーの下にあふれていた。

- evidence: `$lib/AppShell.svelte` — content wrapper `div.relative.flex-1.min-h-0.flex.flex-col.overflow-hidden`

### BottomNav / SuperAppTabBar Theme-Aware Opaque Background

**BottomNav のデフォルト背景を `bg-[var(--gv2-bg-primary)]` (テーマ対応不透明色) に変更。** 旧: `bg-black/92 backdrop-blur-xl` (dark 固定透過)。SuperAppTabBar も `!bg-white/95 material-blur` (light 固定透過) → `!bg-[var(--gv2-bg-primary)]` (テーマ対応不透明) に変更。タブバーに `box-shadow: 0 -2px 8px rgba(0,0,0,0.1)` を追加してコンテンツとの境界を明確化。

- evidence: `40-engine/svelte/design-system/src/lib/components/BottomNav/BottomNav.svelte` — `bg-[var(--gv2-bg-primary,#0a0a0a)]`
- evidence: `$lib/superapp/SuperAppTabBar.svelte` — `!bg-[var(--gv2-bg-primary,#0a0a0a)]` + box-shadow

### Browsing History (Twitter-style Access/View History)

**プロフィール・投稿・検索の閲覧履歴を SQL graph に記録・表示。** AppDrawer に「閲覧履歴」メニュー追加。

| 層 | 実装 |
|---|---|
| **Write** | `atProcedure('com.atproto.repo.createRecord', { collection: 'com.etzhayyim.yoro.browsingHistory', record })` → PDS → yata `BrowsingHistory` node |
| **Read** | `atProcedure('com.etzhayyim.kagami.graph.query', { statement: 'MATCH (h:BrowsingHistory) WHERE h.repo = $did ... ORDER BY h.created_at DESC LIMIT 200', parameters: { did } })` |
| **Delete** | `atProcedure('com.atproto.repo.deleteRecord', { collection, rkey })` — 個別 / 全削除 |
| **Dedup** | Client-side `_recentPaths` Map — 同一 path 1 時間以内の重複 write 抑制 |
| **UI** | `/history` route — filter tabs (all/profile/post/search) + 個別削除 (X) + 全削除 (確認モーダル) |

**Graph label**: `BrowsingHistory` — props: `path`, `title`, `history_type`, `avatar`, `handle`, `created_at`, `repo` (user DID), `rkey`

**Tracking points**: profile view (`profile/[handle]/+page.svelte`), post view (`post/[rkey]/+page.svelte`), search execute (`search/+page.svelte`)

- evidence: `$lib/history.svelte.ts` — Svelte 5 runes store + atProcedure write/read/delete
- evidence: `routes/history/+page.svelte` — history page (Skeleton loader, filter tabs, clear modal)
- evidence: `$lib/components/AppDrawer.svelte` — 「閲覧履歴」nav item (clock icon)

### Feed Loading Fallback

**`onMount` が発火しないケース (hydration 遅延) のフォールバックとして 2s `setTimeout` を追加。** `onMount` → `loadFeed()` が標準パス。2s 以内に `onMount` が発火しなかった場合、`browser` guard 付き `setTimeout` で `loadFeed()` を強制実行。

- evidence: `routes/+page.svelte` — `feedInitialized` flag + `setTimeout` fallback

### E2E + Visual Regression Tests

**`tests/vibes-feed.spec.ts` — Playwright E2E + スクリーンショット比較テスト (10 tests)。**

| Test | 検証内容 |
|---|---|
| `posts load within 10s` | スケルトン → 投稿表示の遷移 (永久ローディング防止) |
| `Discover tab shows at least 1 post` | API がデータを返す |
| `feed error state shows retry button` | PDS 500 時にエラー UI 表示 (route mock) |
| `tab bar stays at viewport bottom` | boundingBox が画面下端 |
| `tab bar is visible after scrolling` | スクロール後も `toBeInViewport()` |
| `tab bar has opaque background` | rgba alpha >= 0.95 |
| `all 5 tabs are present` | 5 つの `role="tab"` |
| `tab navigation works` | クリック → URL 遷移 |
| `vibes feed screenshot` | Visual regression (5% 許容) |
| `tab bar screenshot` | Visual regression (5% 許容) |

```bash
npx playwright test tests/vibes-feed.spec.ts           # 実行
npx playwright test tests/vibes-feed.spec.ts --update-snapshots  # ベースライン更新
npx playwright test tests/vibes-feed.spec.ts --headed   # ブラウザ表示デバッグ
```

- evidence: `tests/vibes-feed.spec.ts` — 10 tests, viewport 390x844 (mobile-first)
- evidence: `tests/vibes-feed.spec.ts-snapshots/` — `vibes-feed-chromium-darwin.png`, `tab-bar-chromium-darwin.png`

### WebLLM = E2E Encrypt 連動

WebLLM opt-in (`localStorage('yoro-local-llm-enabled')`) = DM E2E encrypt opt-in。WebLLM ON → `sendProjectMessage(convoId, body, { encrypt: true })` で val を AES-256-GCM encrypt。PDS は ciphertext を見ない。WebLLM OFF → 既存平文フロー (PDS server-side LLM)。

### Data Path (PDS XRPC 一本化)

全 read/write は PDS XRPC → graph SQL path → RisingWave Hyperdrive の単一パス。Pattern J (hyparquet) / himuro / client-side DuckDB-WASM は除去済み。

### Known Build Issue

`src/lib/provider/local-diffusion.svelte.ts` — Vite worker format IIFE error (pre-existing)。

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto
cd svelte && pnpm build && cd ..
npx wrangler deploy  # infra Worker (Assets binding required)

# smoke test
curl https://yoro.etzhayyim.com/
```

## Android (Capacitor 7 + Fastlane)

### Required env (add to ~/.zshrc)

```bash
export JAVA_HOME="/opt/homebrew/opt/openjdk@21"   # capacitor.build.gradle requires VERSION_21
export ANDROID_HOME="/opt/homebrew/share/android-commandlinetools"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
```

### Deploy to USB-connected device

```bash
cd 60-apps/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte
bundle exec fastlane android device
```

### Gotchas

- `capacitor.build.gradle` requires `JavaVersion.VERSION_21` — Java 17 will fail with "21は無効なソース・リリース"
- `ANDROID_HOME` is `/opt/homebrew/share/android-commandlinetools` (not `~/Library/Android/sdk`)
- Always use `bundle exec fastlane android device` (not gradle directly) — fastlane's `set_version` lane sets `ANDROID_VERSION_CODE` to prevent `INSTALL_FAILED_VERSION_DOWNGRADE`
- Run `npx cap sync android` before first gradle build (generates `capacitor-cordova-android-plugins/`)
- `bpmn-js`, `dmn-js`, `@bpmn-io/*` must be in `vite.config.ts` `build.rollupOptions.external` (dynamic imports that can't be bundled)
- Status bar overlap fix: `Header.svelte` uses `padding-top: env(safe-area-inset-top)` + `height: calc(var(--gv2-header-height, 56px) + env(safe-area-inset-top))` — requires `viewport-fit=cover` in `app.html` (already set)

## magatama.jsonld

```toml
[triggers.w_commit]
collections = [
    # AT Protocol standard (Bluesky Lexicon)
    "app.bsky.feed.post",
    "app.bsky.feed.like",
    "app.bsky.graph.follow",
    "com.etzhayyim.convo.message",
    "com.etzhayyim.convo.convo",
    "com.etzhayyim.convo.member",
    "com.etzhayyim.convo.reaction",
    "com.etzhayyim.convo.readReceipt",
    "com.etzhayyim.convo.presence",
    "com.etzhayyim.signal.preKeyBundle",
]

[w_protocol]
default_encryption = "plaintext"
```
