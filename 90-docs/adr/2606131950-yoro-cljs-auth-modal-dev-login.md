---
id: adr-2606131950-yoro-cljs-auth-modal-dev-login
title: "ADR-2606131950: yoro ClojureScript auth-modal dev-login form — wave 4 (passkey rpId 回避 + paren fix)"
status: accepted
doc_type: adr
topic: yoro-cljs-migration
authoritative: false
last_verified: 2026-06-13
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Session-close record 2026-06-13: auth_modal.cljs paren imbalance fix (rf/reg-fx :http/post-json unclosed) + dev-mode app-password login form (handle + app-password + PDS selector → com.atproto.server.createSession). Dev login modal verified live at localhost:8700."
authoritative_for:
  - yoro UI cljs auth-modal dev-login design + :http/post-json re-frame fx pattern
depends_on:
  - adr-2606121350-yoro-ui-svelte-to-cljs-migration-harness
related:
  - adr-2606121350-yoro-ui-svelte-to-cljs-migration-harness
supersedes: []
superseded_by: []
---

# ADR-2606131950: yoro ClojureScript auth-modal dev-login form — wave 4

**Status**: accepted
**Date**: 2026-06-13
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

## Context

### 問題1 — shadow-cljs が再コンパイルしない

`auth_modal.cljs` に S 式バランス崩れがあり、shadow-cljs がソース変更を
検出してもコンパイルエラー (スタックトレースなし) で**旧 JS をそのまま提供
し続ける**状態になっていた。コンソールに `shadow-cljs: #28 ready!` のまま
固まり、新しいコードが反映されない。

根本原因: `(rf/reg-fx :http/post-json ...)` ブロック (line 140–159) の
`.catch` ファンクション末尾が `)` 1 個不足 → `rf/reg-fx` フォーム自体が
閉じられず、ファイル終端の depth が 1 (正常は 0)。

Python カウンタ診断 (文字列/コメント考慮):
```
L140  0-> 1: (rf/reg-fx          ← depth 0→1、終端まで閉じられない
L159  7-> 1: ...dispatch...(err)))))))))  ← depth 7→1 のまま
EOF depth = 1  (should be 0)
```

### 問題2 — WebAuthn rpId ドメイン不一致

passkey 認証は `rpId: "etzhayyim.com"` で登録されているため、
`localhost:8700` では `navigator.credentials.get()` が `NotSupportedError`
を返し**ログイン不可**。

従来は WebAuthn のみ実装していたが、localhost 開発時にパスキーを使わずに
bsky.social ハンドル + アプリパスワードでセッションを取得する手段がなかった。

## Decision

### 1. paren fix — line 159 に `)` 1 個追加

```diff
- (rf/dispatch (conj on-failure (.-message err)))))))))
+ (rf/dispatch (conj on-failure (.-message err))))))))))
```

追加した `)` が `(rf/reg-fx :http/post-json ...)` フォームを閉じる。
修正後 EOF depth = 0、shadow-cljs が即時再コンパイル。

### 2. dev-mode app-password login フォーム

`auth_modal.cljs` の WebAuthn ボタン下部に divider + 3 入力要素を追加:

| 要素 | 詳細 |
|---|---|
| `[:input {:type "text"}]` | ハンドル (`@handle` 形式) |
| `[:input {:type "password"}]` | アプリパスワード (bsky.social 設定で生成) |
| `[:select ...]` | PDS 選択 (`bsky.social` / `atproto.etzhayyim.com`) |
| `[:button "ログイン"]` | 空欄・ロード中で disabled |

状態は `r/atom` 3 本 (`dev-id` / `dev-pwd` / `dev-pds`) — form-2 outer let で
宣言、コンポーネント再描画ごとに保持。

### 3. `:http/post-json` re-frame fx ハンドラ

```clojure
(rf/reg-fx
 :http/post-json
 (fn [{:keys [url body on-success on-failure]}]
   (-> (js/fetch url #js {:method "POST"
                          :headers #js {"Content-Type" "application/json"}
                          :body (js/JSON.stringify (clj->js body))})
       (.then (fn [r]
                (let [ok? (.-ok r)]
                  (-> (.json r)
                      (.then (fn [data]
                               (let [d (js->clj data :keywordize-keys true)]
                                 (if ok?
                                   (rf/dispatch (conj on-success d))
                                   (when on-failure
                                     (rf/dispatch (conj on-failure
                                                        (or (:error d) (:message d)
                                                            (str "HTTP " (.-status r)))))))))))))
       (.catch (fn [err]
                 (when on-failure
                   (rf/dispatch (conj on-failure (.-message err)))))))))
```

### 4. `:auth/dev-login` イベントチェーン

```
:auth/dev-login [identifier password pds-host]
  → :http/post-json POST https://{pds-host}/xrpc/com.atproto.server.createSession
  → on-success :auth/dev-login-ok pds-host
       at/set-service! + ss-set! SESSION_KEY + ls-set! DID_KEY + dispatch :auth/set-session
  → on-failure :auth/dev-login-fail
       snd/play-fail! + assoc error message
```

`at/set-service!` で以降の XRPC 呼び出しを createSession を発行した PDS に
向ける (bsky.social / atproto.etzhayyim.com の切り替えに対応)。

## Verification

- Python カウンタ: 修正後 `Final depth: 0 (should be 0)` ✓
- compiled JS: `grep -c "dev_login|post_json"` → 16 matches ✓ (旧 JS は 0)
- ブラウザ `http://localhost:8700` → ログインボタンクリック → auth modal 表示:
  - ハンドル / アプリパスワード / PDS セレクタ / ログインボタン 確認 ✓
  - 空欄時ログインボタン disabled 確認 ✓

## Consequences

- passkey が使えない localhost 環境でも bsky.social / etzhayyim PDS に
  app-password でログイン可能になる (dev ループ完成)
- `:http/post-json` fx は汎用 JSON POST fx として他コンポーネントからも利用可
- アシスタントは credentials 入力不可 (safety rule); ユーザが手動で
  ハンドル + アプリパスワードを入力してログインする
- アプリパスワードは bsky.social 設定 → プライバシーとセキュリティ → アプリパスワード で生成

## Follow-up

- 未ログイン → ログイン後の compose + 投稿フロー の E2E 確認
- playwright smoke に dev-login フロー追加 (env var からアプリパスワード注入)
- 本番環境では WebAuthn passkey が主経路のまま (dev-form は localhost 限定の UX)
