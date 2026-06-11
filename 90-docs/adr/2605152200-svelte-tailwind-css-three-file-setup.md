---
id: adr-2605152200-svelte-tailwind-css-three-file-setup
title: "SvelteKit worker/svelte — Tailwind CSS 3-file setup requirement"
status: active
doc_type: adr
topic: svelte-tailwind-setup
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - tailwindcss setup in worker/svelte SvelteKit projects
  - postcss.config.js required plugins
  - app.css required directives
  - package.json required devDependencies for Tailwind
related:
  - adr-2605152100-auth-unified-topology
  - 40-engine/svelte/design-system/
---

# Context

`auth.etzhayyim.com/sign-in` が全黒画面になる障害が発生した (2026-05-15)。
Tailwind ユーティリティクラス (`flex`, `fixed`, `z-10` 等) が一切 CSS 出力されず、
パーティクルアニメーションのみが描画される状態だった。

調査の結果、`60-apps/etzhayyim-project-auth/worker/svelte/` の Tailwind セットアップが
**3 箇所すべて欠落**していることが原因と特定された。

| ファイル | 欠落内容 |
|---|---|
| `package.json` | `tailwindcss` / `autoprefixer` / `postcss` / `@etzhayyim/design-system` 未登録 |
| `postcss.config.js` | `tailwindcss: {}` プラグインなし (`autoprefixer` のみ) |
| `src/app.css` | `@tailwind base/components/utilities` ディレクティブなし |

`tailwind.config.js` は存在していたが、PostCSS が Tailwind を呼ばないため完全に無効だった。
ビルドエラーは発生せず (Vite は未知の CSS class を無視する)、
テスト・型チェックでも検出不能なサイレント障害だった。

# Decision

`worker/svelte/` または任意の SvelteKit プロジェクトで Tailwind CSS を使う場合、
以下の **3 ファイルをセットで** 設定することを必須とする。

## 1. `package.json` — devDependencies

```json
{
  "devDependencies": {
    "@etzhayyim/design-system": "workspace:*",
    "autoprefixer": "^10.4.27",
    "postcss": "^8.5.9",
    "tailwindcss": "^3.4.19"
  }
}
```

`@etzhayyim/design-system` は `tailwind.config.js` の `etzhayyimUIKit` plugin を提供する。
workspace 内のパッケージなので `workspace:*` を使用する。

## 2. `postcss.config.js` — tailwindcss plugin 必須

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
};
```

`tailwindcss` を省くと Tailwind の CSS 変換が走らない。`autoprefixer` のみでは不十分。

## 3. `src/app.css` — @tailwind ディレクティブ必須

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* アプリ固有スタイルはここ以降 */
```

`@tailwind utilities` がないとユーティリティクラスが出力されない。
`@tailwind base` がないとブラウザリセットが欠ける。

# Consequences

- `pnpm build` 後の CSS bundle に Tailwind utilities が含まれる (68KB+ が正常)
- `tailwind.config.js` の `content` 配列で指定したファイルからクラスが tree-shake される
- `@etzhayyim/design-system` の `etzhayyimUIKit` plugin が CSS カスタムプロパティ (CSS変数) を注入する

# Detection

ビルド後の `_app/immutable/assets/0.*.css` が数 KB 未満の場合は Tailwind 未適用を疑う。
正常時は 60KB 以上。

# Reference Implementation

- 修正: `60-apps/etzhayyim-project-auth/worker/svelte/` (2026-05-15)
- 参照実装: `60-apps/etzhayyim-project-yatabase/svelte/` (同一構成、正常動作)
