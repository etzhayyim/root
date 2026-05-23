# AppShell v2 Layout Standard

## Scope

- 対象: `@etzhayyim/appshellv2` を利用する全 UI (`projects/*/svelte`, `projects/*/wasm/*/svelte`)

## Hard Rules

- `Header` は左上に App Launcher を標準表示する（`showAppLauncher=true`）。
- signed-out 時の `Header` は `Sign in` と `Create account` を標準表示し、登録導線を shell 標準の account sheet に集約する。
- signed-in 時の `Header` は trust badge と workspace switcher を標準表示する。
- `Header` は MetaMask 導線（`walletHref`）を標準表示する。
- workspace の切替 / 新規作成は、Header または Settings の shell 標準 UI から現在画面を離れずに実行できるようにする。
- `Footer` は `Privacy Policy` / `Terms` / `Support` を標準表示する（`showStandardLinks=true`）。
- 各サービスはヘッダー/フッターの構成を独自分岐せず、`Header`/`Footer` の props で差分制御する。

## Default Example

```svelte
<AppShell>
  {#snippet header()}
    <Header
      signInHref="/sign-in"
      signUpHref="/sign-up"
      walletHref="https://metamask.io/download/"
    />
  {/snippet}
  {#snippet footer()}
    <Footer
      privacyHref="/privacy"
      termsHref="/terms"
      helpHref="/support"
    />
  {/snippet}
  {@render children()}
</AppShell>
```
