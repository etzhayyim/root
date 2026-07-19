# 40-engine/svelte — Shared UI Packages (Svelte 5)

全 `*.etzhayyim.com` アプリで共通の UI コンポーネント・レイアウト・認証・MCP 接続を提供する。

## Packages

| Package | npm name | 説明 |
|---|---|---|
| `design-system/` | `@etzhayyim/design-system` | **UIKit** (50+ components)。フォーム/テーブル + モバイル UI + TikTok Feed + headless builders + motion utilities + Tailwind plugin |
| `vite-plugin-safe-builder/` | `@etzhayyim/vite-plugin-safe-builder` | **全 Svelte client アプリ推奨** — 直接 import |

## CRITICAL: SuperApp Mobile-First Architecture

→ `etzhayyim dodaf tv1 query --id svelte-superapp-mobile-first-architecture` / MCP `etzhayyim.dodaf.tv1.query`

## authn.etzhayyim.com 認証 (Passkey + AT Protocol JWT, ADR-0024 T4 split)

- `initPasskey()` は `authn.etzhayyim.com` を認証基盤として使用 — 全 `*.etzhayyim.com` アプリで AT Protocol session が自動有効化される
- 旧 `auth.etzhayyim.com` は 2026-04-16 に retired (HTTP 410 Gone)。AuthN = `authn.etzhayyim.com`、identity lifecycle = `authz.etzhayyim.com` (`= accounts.etzhayyim.com`)
- 各アプリで個別の認証設定は不要 — `initPasskey()` のみで認証が動作する
- AT Protocol JWT (did:web) による session 管理

### CRITICAL: Auth State Detection 必須 — skipAuth は auth 検知を skip しない

**`SuperAppLayout` は `skipAuth` の値に関わらず常に `initPasskey()` を実行し auth state を検知する。** `skipAuth` は authn.etzhayyim.com UI chrome (sign-in モーダル等) の制御のみ。

- **UI layout 分岐は `$isSignedIn` store のみ**で判定する。route が public か否かで分岐しない
- Public route でもログイン済みなら authenticated UI を表示する
- `isPublicLegalRoute` 等の ad-hoc boolean flag で layout を分岐しない — lexicon session state (`$isSignedIn`) が唯一の判定基準
- 各タブの snippet 内で `{#if $isSignedIn}` で guest/authenticated を切り替える (single layout, auth-reactive pattern)
- 権威ソース: `90-docs/260322-frontend-lexicon-architecture.md`

## AppShell Identity / Workspace Model

- AppShell v2 は **1 user : 多 org** を標準とする。各 user は personal org を持てる前提で、shell-level UI から org の切替と新規作成を完結できるようにする
- 初期登録で email verification を必須にしない。標準 onboarding は `Passkey` / `MetaMask` / `username` のいずれかから開始できるようにする
- trust score は shell の標準概念とし、Header / Settings など共通面で現在値と未達条件を可視化する
- trust score 向上要因は phone verification / SNS(OAuth) 接続 / wallet linkage / age verification を標準とする。未達条件は UI 上で理由を説明し、黙ってボタンを消さない
- org metadata の access gate は `minimum_trust_score` / `minimum_age` を第一標準とし、consumer 側では `requiredTrustScore` / `minimumAge` 互換も読めるようにする

## CRITICAL: Connect Client Dependency Policy

→ `etzhayyim dodaf tv1 query --id svelte-connect-client-dependency-policy` / MCP `etzhayyim.dodaf.tv1.query`

## CRITICAL: UIKit (design-system) 必須 — 独自 UI 実装禁止

→ `etzhayyim dodaf tv1 query --id svelte-uikit-design-system-必須-独自-ui-実装禁止` / MCP `etzhayyim.dodaf.tv1.query`

## CRITICAL: File Upload — FormData + Multipart Binary (base64 禁止)

→ `etzhayyim dodaf tv1 query --id svelte-file-upload-formdata-+-multipart-binary-base64-禁` / MCP `etzhayyim.dodaf.tv1.query`

## Rules

- **UI コンポーネントは `@etzhayyim/design-system` を使用する**。各アプリでの独自実装禁止
- `@etzhayyim/appshellv2` が design-system を re-export するため、どちらからでもインポート可能
- 新規アプリは `@etzhayyim/appshellv2` を使用する（`appshellv2-*` の直接利用は非推奨）
- 各パッケージは Svelte 5 snippet API を使用（slot 非推奨）
- **全 Svelte client アプリは safe-builder を推奨** (`@etzhayyim/vite-plugin-safe-builder`)
- `mcpOrgGuard`, `routeCanonical`, `ssgValidate` は全て safe-builder から re-export（旧パッケージは削除済み）

### スタイリングルール (Tailwind-Only)

- **独自 CSS (`<style>` ブロック) は原則禁止**。Tailwind CSS クラスのみを使用する
- スタイリングには `cn()` ユーティリティ (clsx + tailwind-merge) を使用
- design-system の Tailwind プラグイン: `@digital-go-jp/tailwind-theme-plugin` (gov tokens: `text-std-*`, `text-oln-*`) + `etzhayyimUIKit` (mobile utilities: `safe-area-*`, `tap-target-44`, `scrollbar-none`, `material-blur-*`)
- AppShell v2 テーマ (`--gv2-*` CSS custom properties) は Tailwind の `[var(--gv2-*)]` 記法で参照可能
- **禁止**: `<style>` ブロックでの独自 CSS 定義、インラインの `style` 属性（動的値を除く）
- **許可**: `app.css` でのグローバル設定 (tokens.css import, body/html 基本設定のみ)

## Usage

**CDN app `package.json`**:
```json
{
  "dependencies": {
    "@etzhayyim/design-system": "file:../../../../../com-etzhayyim-svelte-design-system"
  },
  "devDependencies": {
    "@etzhayyim/vite-plugin-safe-builder": "file:../../../../../com-etzhayyim-vite-plugin-safe-builder"
  }
}
```

**Layout** (`+layout.svelte`):
```svelte
<script>
  import { AppShell, Header, Sidebar, Footer, ThemeToggle } from '@etzhayyim/appshellv2';
</script>
<AppShell>
  {#snippet header()}
    <Header>
      {#snippet right()}<ThemeToggle />{/snippet}
    </Header>
  {/snippet}
  {#snippet sidebar()}<Sidebar />{/snippet}
  {#snippet footer()}<Footer />{/snippet}
  {@render children()}
</AppShell>
```

### AppShell v2 標準レイアウト (必須)

AppShell はゼロ設定で HIG 準拠のレイアウトを提供する。消費側での `mobileMode` 手動設定は不要。

**AppShell デフォルト動作**:
- **モバイルブレークポイント**: `max-width: 1023px` — iPad portrait 以下でサイドバー overlay、`lg:` 以上で persistent
- **ヘッダー z-index**: `relative z-10` — AppLauncher ドロップダウンがコンテンツの上に表示される
- **コンテンツ z-index**: `relative z-0` — コンテンツ領域は stacking context z-0 で、overlay backdrop (z-79) / sidebar (z-80) より常に下
- **DOM 順序**: mobile overlay (backdrop + sidebar) はコンテンツの**後**に配置。compositing layer による pointer event 遮断を防止
- **`mobileMode` override**: 既定の 1023px と異なるブレークポイントが必要な場合のみ使用

**Header デフォルト動作**:
- `showAppLauncher={true}` — 左上に App Launcher を標準表示
- `homeHref="/"` — 中央の `appName` がホームへのリンクになる。クリックで top page に遷移
- `appName="etzhayyim"` — 各アプリで上書き (`appName="Shinshi"` 等)
- `showStandardActions={true}` — Sign in / Sign up / Wallet ボタンを表示

**Footer**: `Privacy Policy` / `Terms` / `Support` を標準表示（`showStandardLinks` のデフォルトは `true`）。

```svelte
<Header
  appName="MyApp"
  signInHref="https://accounts.etzhayyim.com/sign-in"
  signUpHref="https://accounts.etzhayyim.com/sign-up"
/>
<Footer privacyHref="/privacy" termsHref="/terms" helpHref="/support" />
```

**禁止**: `showAppLauncher={false}` + 手動 `<AppLauncher />` import（built-in を使用する）

**Components** (`+page.svelte`):
```svelte
<script>
  import { Button, Input, Label, NotificationBanner } from '@etzhayyim/appshellv2';
</script>
<Label>名前</Label>
<Input placeholder="入力してください" />
<Button variant="solid-fill" size="md">送信</Button>
```

**Integrated Subpaths**:
```ts
import { AuthGate } from '@etzhayyim/appshellv2/auth';
import { AppLauncher } from '@etzhayyim/appshellv2/apps';
import { LanguageSwitcher } from '@etzhayyim/appshellv2/language';
import { McpClient } from '@etzhayyim/appshellv2/mcp';
import { WalletIndicator } from '@etzhayyim/appshellv2/wallet';
import { safeBuilder } from '@etzhayyim/vite-plugin-safe-builder';
```

**Theme**: CSS custom properties (`--gv2-*`)。`[data-theme="dark"|"light"]`。dark がデフォルト。

## UIKit Components (design-system)

### Export Paths

```ts
import { Avatar, BottomNav, SnapFeed, Toast, ... } from '@etzhayyim/design-system';      // components
import { createBottomSheet, createTabs, createToast, createSwipe } from '@etzhayyim/design-system/builders'; // headless builders
import { staggerFly, snapSpring, smoothSpring } from '@etzhayyim/design-system/motion';   // motion utilities
import { etzhayyimUIKit } from '@etzhayyim/design-system/plugin';                              // Tailwind plugin
```

appshellv2 が design-system を re-export するため、`'@etzhayyim/appshellv2'` からも全コンポーネントを import 可能。

### Component Categories

| Category | Components |
|---|---|
| **UI Primitives** | `Avatar`, `AvatarRow`, `Badge`, `Card` (default `aspect="auto"`; 画像カードのみ `aspect="3:4"` 等を明示指定), `Chip`, `Skeleton`, `Toggle`, `Fab` |
| **Mobile Nav** | `BottomNav` (liquid morph indicator, theme-aware opaque bg `var(--gv2-bg-primary)`), `TabBar` (spring underline), `BottomSheet` (rubber-band drag), `ActionSheet` (spring + stagger) |
| **TikTok Feed** | `SnapFeed` (vertical snap scroll), `SnapItem`, `FeedOverlay` (gradient + creator info), `ReactionBar` (bounce reactions), `SwipeViewer` (horizontal swipe gallery) |
| **Interactive** | `Toast` (auto-dismiss, stacking), `PullToRefresh` (spring indicator) |
| **Headless Builders** | `createBottomSheet`, `createTabs`, `createToast`, `createSwipe`, `tilt`, `parallax` — Melt-style: returns attrs + Svelte actions, zero styling |
| **Motion** | `staggerFly`, `staggerFade`, `staggerScale`, `springEnter`, `morphFade`, `liquidSlide`, `slideUp`, `slideRight`, `depthEnter`, `depthExit`, `depthBackEnter`, `depthBackExit`, `tabSlide`, `computeTilt`, `resetTilt`, `parallaxY`, `overshootEase`, `elasticEase` |
| **Spring Presets** | `snapSpring`, `smoothSpring`, `bounceSpring`, `duoPress`, `duoBounce`, `liquidMorph`, `rubberBand`, `gentleFloat`, `cardFloat`, `focusGlow` |
| **Audio** | `playTap`, `playSelect`, `playBack`, `playHover`, `playScrollTick`, `playToggle`, `playTabSwitch`, `playNavForward/Back`, `playSheetOpen/Close`, `playToast`, `playNotification`, `playSnap`, `playSuccess`, `playCelebrate`, `playLevelUp`, `playError`, `playLiquidPop`, `haptic`, `tactile`, `setUISoundsVolume` |
| **Tailwind Plugin** | `etzhayyimUIKit` — `safe-area-*`, `tap-target-44`, `scrollbar-none`, `snap-*-mandatory`, `material-blur-*`, `btn-3d-*`, `glass`, `glass-strong`, `card-float`, `focus-glow`, `depth-enter/exit`, `glow-indicator`, `pulse-badge` |

### CRITICAL: Animation-First Architecture (Duolingo + Apple Liquid)

**全コンポーネントは Spring-First で設計する。CSS `transition` ではなく `svelte/motion` の `spring()` を primary animation mechanism とする。**

#### Spring Presets (8種)

| Preset | stiffness | damping | 用途 |
|---|---|---|---|
| `snapSpring` | 0.2 | 0.75 | Nav indicators, TabBar underline |
| `smoothSpring` | 0.15 | 0.8 | Sheets, overlays, smooth UI |
| `bounceSpring` | 0.3 | 0.6 | Heart taps, FAB press |
| `duoPress` | 0.35 | 0.55 | Button press (Duolingo 3D) — compress → overshoot → settle |
| `duoBounce` | 0.25 | 0.45 | Achievement/reward — large playful overshoot |
| `liquidMorph` | 0.12 | 0.85 | Shape morphing (Apple Dynamic Island) — slow, fluid |
| `rubberBand` | 0.4 | 0.7 | Overscroll bounce — snappy return with slight bounce |
| `gentleFloat` | 0.08 | 0.9 | Background parallax — ambient floating elements |

```ts
import { spring } from 'svelte/motion';
import { duoPress, liquidMorph, rubberBand } from '@etzhayyim/design-system/motion';
const scale = spring(1, duoPress);
```

#### Animation Patterns (必須)

| Pattern | 実装 | 禁止 |
|---|---|---|
| **Button press** | `spring(1, duoPress)` → 0.88 → 1.04 → 1.0 + `playTap()` | `active:scale-95` CSS のみ |
| **Toggle** | `spring` thumbX + scaleX/Y liquid morph + `playLiquidPop()` | CSS `transition` のみ |
| **Sheet entrance** | `fly` with overshoot easing + `playSheetOpen()` | `slide` 250ms linear |
| **Sheet drag** | `spring` rubber-band (resistance 0.6x down, 0.15x up) | Direct `transform` without spring |
| **Nav indicator** | `spring(0, liquidMorph)` position + width morph (dot → pill → dot) | Fixed-size dot with CSS transition |
| **Tab click** | `spring` scale 0.75 → 1.18 → 0.95 → 1.0 (multi-bounce) | Single `scale-90` |
| **List items** | `staggerFly` or `springEnter` per item | No entrance animation |
| **ActionSheet** | Overshoot `fly` + `scale` stagger per item (40ms delay) | Plain `slide` |

#### Audio Feedback (必須)

全インタラクティブコンポーネントは対応する audio feedback を持つ:

```ts
import { playTap, playSelect, playBack, playHover, playScrollTick, playNavForward, playNavBack, playNotification, haptic, tactile } from '@etzhayyim/design-system/audio';
```

| Sound | Duration | 用途 |
|---|---|---|
| `playTap()` | 35ms | Button, Chip press (Switch-style crisp tick) |
| `playSelect()` | 60ms | Confirm / select (bright rising tone) |
| `playBack()` | 40ms | Back / cancel (descending tone) |
| `playHover()` | 20ms | Focus / hover (ultra-subtle cursor tick) |
| `playScrollTick()` | 10ms | Scroll detent micro-feedback |
| `playToggle(on)` | 60ms | Toggle switch |
| `playTabSwitch()` | 50ms | BottomNav, TabBar (with harmonic shimmer) |
| `playNavForward()` | 120ms | Forward depth navigation |
| `playNavBack()` | 100ms | Back depth navigation |
| `playSheetOpen/Close()` | 180ms/120ms | Sheet/Modal (with breath resonance) |
| `playNotification()` | 350ms | Switch-style double bell chime |
| `playSuccess()` | 250ms | 正解、完了 (ascending C-E-G chord) |
| `playCelebrate()` | 200ms | Achievement (ascending scale burst) |
| `playLevelUp()` | 350ms | Level up (warm ascending sweep) |
| `playError()` | 150ms | Error (descending minor second) |
| `playLiquidPop()` | 100ms | Liquid UI (bubble burst) |
| `haptic(pattern)` | — | Vibration API ('light'/'medium'/'heavy'/custom) |
| `tactile(sound)` | — | Combined sound + haptic for Switch-like feedback |

#### Switch 2 Interaction Patterns (必須)

| Pattern | 実装 | 禁止 |
|---|---|---|
| **Card hover** | `use:tilt` action (3D perspective tilt ±8deg + translateZ lift + shadow) | Flat hover with opacity only |
| **Card tap** | `card-float` Tailwind class (hover lift + active compress) | No hover feedback |
| **Focus ring** | `focus-glow` Tailwind class (accent-colored glow ring) | Default browser outline |
| **Page forward** | `depthEnter` transition (scale 1.06→1.0 + overshoot) + `playNavForward()` | Plain fade |
| **Page back** | `depthBackEnter` transition (scale 0.94→1.0) + `playNavBack()` | Plain fade |
| **Tab switch** | `fade` transition + `playTabSwitch()` with harmonic + haptic | No transition |
| **Scroll** | `use:parallax` action (subtle translateY offset) + `playScrollTick()` at intervals | Static positioning |
| **Ambient BG** | `AmbientBackground` component (Canvas 2D particles, mood-reactive, 30fps) | Solid color background |
| **Unread badge** | `pulse-badge` class (scale 1.0↔1.15 pulse animation) | Static badge |
| **Notification** | `playNotification()` (Switch-style double bell) + slide-down toast | Silent toast |

```ts
// Switch 2 card tilt action
import { tilt, parallax } from '@etzhayyim/design-system/builders';
// <div use:tilt={{ maxDeg: 8, liftPx: 12, sound: true }}>Card</div>
// <div use:parallax={{ factor: 0.1 }}>Parallax element</div>

// Switch 2 depth transitions
import { depthEnter, depthExit, depthBackEnter, tabSlide } from '@etzhayyim/design-system/motion';

// Ambient background (auto mood-reactive)
import { AmbientBackground } from '@etzhayyim/appshellv2/superapp';
```

#### Tailwind Plugin — Duolingo 3D + Apple Glass + Switch 2

```html
<!-- Duolingo 3D button -->
<button class="btn-3d-green rounded-2xl active:btn-3d-press">Submit</button>
<button class="btn-3d-blue rounded-2xl active:btn-3d-press">Continue</button>

<!-- Apple glass morphism -->
<div class="glass rounded-2xl p-4">Glass card</div>
<div class="glass-strong rounded-2xl p-4">Stronger glass</div>

<!-- Switch 2 card float (hover lift + active compress) -->
<div class="card-float rounded-2xl p-4 bg-gv2-bg-card">Floating card</div>

<!-- Switch 2 focus glow ring (accent-colored) -->
<button class="focus-glow rounded-xl p-3">Glowing focus</button>

<!-- Unread badge pulse -->
<span class="pulse-badge bg-red-500 rounded-full px-1.5">3</span>

<!-- Material blur levels -->
<div class="material-blur-xs">4px blur</div>
<div class="material-blur-sm">10px blur</div>
<div class="material-blur">20px blur (default)</div>
<div class="material-blur-lg">30px blur</div>
```

### Component Pattern (必須)

全コンポーネントは以下のパターンに従う:
- Svelte 5 runes (`$props`, `$state`, `$derived`, `$effect`, `$bindable`)
- Snippet API (`Snippet` type, `{@render}`)。slot は使用しない
- `cn()` で Tailwind クラス合成。`class` prop で外部からカスタマイズ可能
- **Spring-first**: 全インタラクティブ要素は `svelte/motion` の `spring()` でアニメーション。CSS `transition` は補助的にのみ使用
- **Audio feedback**: press/toggle/open/close に対応する `playXxx()` を呼ぶ
- 外部アニメーションライブラリ不使用

### Tailwind Plugin Setup (必須)

全 Svelte client アプリの `tailwind.config.js` に `etzhayyimUIKit` プラグインと design-system の content パスを追加する。

```js
// tailwind.config.js
import { etzhayyimUIKit } from '@etzhayyim/design-system/plugin';

export default {
  content: [
    './src/**/*.{html,js,svelte,ts}',
    '../../../com-etzhayyim-svelte-design-system/dist/**/*.{svelte,js}', // flat west UIKit
  ],
  plugins: [etzhayyimUIKit],
};
```

**content パスの相対パスは `projects/*/wasm/*/svelte/` からの位置関係に合わせて調整すること。**

### 独自 UI 実装の禁止

各アプリでの `BottomNav`, `BottomSheet`, `SnapFeed`, `SwipeViewer`, `Avatar`, `Skeleton`, `ActionSheet`, `Toast`, `PullToRefresh`, `Toggle`, `TabBar`, `Card`, `Badge`, `Fab`, `Chip` 等の独自実装は禁止。design-system のコンポーネントを使用すること。

スプラッシュスクリーン / ローディング画面も `Skeleton` + `staggerFade` を使用する。`animate-pulse` テキストのみのローディング表示は非推奨。

## UI/UX 設計指針: Apple HIG + iPad 最適化

全 CDN アプリは **Apple Human Interface Guidelines (HIG)** に基づき、**iPad をプライマリターゲット**として設計する。
`@etzhayyim/appshellv2` + `@etzhayyim/design-system` を基盤コンポーネントとして利用しつつ、HIG でレイアウト・インタラクション・レスポンシブを統一する。

### HIG デザイン原則

- **Clarity**: コンテンツが最優先。テキスト読みやすく、アイコン明確、装飾最小限
- **Deference**: UI はコンテンツを引き立てる。半透明マテリアル、最小限のクロム
- **Depth**: 視覚的レイヤーとモーションで空間関係を表現

### ブレークポイント (iPad 中心の 4 段階)

| Breakpoint | Tailwind | デバイス | レイアウト |
|---|---|---|---|
| `< 768px` | default | iPhone, iPad Mini compact | Single column, sidebar hidden |
| `768px – 1023px` | `md:` | **iPad portrait** | Sidebar overlay/slide-over, 2-column optional |
| `1024px – 1365px` | `lg:` | **iPad landscape**, iPad Air/Pro portrait | Persistent sidebar + content (Split View) |
| `≥ 1366px` | `xl:` | iPad Pro 12.9" landscape, desktop | Full sidebar + wide content |

**必須**: `md:` (iPad portrait) を独立ブレークポイントとして扱う。mobile/desktop のバイナリ切替は禁止。

### iPad レイアウト

AppShell が `max-width: 1023px` で自動的にサイドバーを overlay に切替。手動 CSS クラス不要。

```svelte
<!-- AppShell デフォルトで iPad portrait = overlay, landscape+ = persistent -->
<AppShell {sidebarOpen} onCloseSidebar={closeSidebar}>
  {#snippet sidebar()}<Sidebar />{/snippet}
  {#snippet header()}
    <Header appName="MyApp" showMenuButton={isCompact} onMenuClick={toggleSidebar} />
  {/snippet}
  {@render children()}
</AppShell>
```

### タッチ規約

- **最小タップターゲット**: 44×44px (HIG 必須)。全 Button, Link, Checkbox 等に適用
- **タップ間隔**: 最低 8px
- **Hover 依存禁止**: hover は視覚補助のみ。機能は tap/click で到達可能
- **touch-action**: インタラクティブ要素に `touch-manipulation`
- **スワイプ**: リスト削除、ナビゲーション戻り (HIG: Gestures)
- **長押し**: コンテキストメニュー (HIG: Context menus)

### Safe Area

```css
:root {
  --safe-area-top: env(safe-area-inset-top, 0px);
  --safe-area-bottom: env(safe-area-inset-bottom, 0px);
  --safe-area-left: env(safe-area-inset-left, 0px);
  --safe-area-right: env(safe-area-inset-right, 0px);
}
```

`app.html` に `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` を設定する。

### タイポグラフィ (HIG sizes + design-tokens 併用)

| 要素 | サイズ | Tailwind | 用途 |
|---|---|---|---|
| Large Title | 34pt | `text-[34px] font-bold` | ページタイトル |
| Title 1 | 28pt | `text-[28px] font-bold` | セクション見出し |
| Title 2 | 22pt | `text-[22px] font-bold` | サブセクション |
| Body | 17pt | `text-[17px]` | 本文 |
| Footnote | 13pt | `text-[13px]` | メタ情報 |

design-system component 内部の `text-std-*` / `text-oln-*` トークンはそのまま維持。ページレイアウトの見出し・本文には HIG サイズを適用。

### マテリアル

- **Sidebar (slide-over 時)**: `material-blur` (`backdrop-filter: blur(20px)`) + 半透明背景
- **Sheet/Modal**: `material-blur-lg` (`backdrop-filter: blur(30px)`) + `rounded-2xl`
- **カード**: `rounded-xl`, 控えめな shadow

### 禁止事項

- Binary responsive (mobile/desktop のみ) — 必ず `md:` (iPad) を含める
- Hover-only 機能 — tap/click で到達不能な機能
- 44px 未満のタップターゲット
- `user-select: none` の濫用 (テキストコンテンツは選択可能に)
- 固定 viewport width (`width=1024` 等)
