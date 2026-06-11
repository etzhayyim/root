---
id: adr-2606033600-tsuzuri-adobe-free-inbrowser-wasm-pdf-editor
title: "ADR-2606033600: tsuzuri 綴 — Adobe-independent, in-browser (WASM) PDF editor"
status: accepted
doc_type: adr
topic: tsuzuri-adobe-free-inbrowser-wasm-pdf-editor
authoritative: true
last_verified: 2026-06-03
priority: 4.0
axis: architecture
weight: 0.40
priority_note: "First-party end-user app (tool), not a Tier-B religious-corp actor; landed on main via PR #873."
authoritative_for:
  - 60-apps/tsuzuri
depends_on:
  - "2606014500"
  - "2606013800"
  - "2605192200"
related:
  - "2605262130"
  - "2605231525"
  - "2605215000"
supersedes: []
superseded_by: []
---

# ADR-2606033600: tsuzuri 綴 — Adobe-independent, in-browser (WASM) PDF editor

**Status**: accepted
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

問い: 「**adobe に依存しない pdf editor は wasm で設計されている?**」

PDF は ISO 32000 のオープン規格であり、Adobe の SDK/サービスに依存せず読み書きできる。
一方で「Adobe非依存 ⇒ WASM」という固定の関係は **無い**: メタ編集（結合・分割・回転・
署名・フォーム）だけなら純 JS で足り、WASM が真価を発揮するのは既存 C/C++ 資産
(PDFium/MuPDF) の持ち込みや、レンダリング・OCR など CPU バウンドな処理である。

本リポジトリ固有の制約:

- **ライセンス**: Apache-2.0 + Charter Compliance Rider v2.0 が既定（ADR-2605192200）。
  permissive を弱める copyleft（**AGPL の MuPDF / Ghostscript**）は採用不可。
- **端末内完結 / プライバシー**: 利用者文書をサーバーへ送らない。
- **no-server-key**（ADR-2605231525）: サーバー保管鍵・サーバー署名を持たない。
- **広告排除 / 反 addictive-design**（§1.13 Wellbecoming）。

既存の `etzhayyim-project-editor` はコードエディタであり PDF エディタは未提供だった。

# Decision

新規 first-party アプリ **`60-apps/tsuzuri/`**（綴 = 文書を綴じ編む）を新設する。
**DOM ベースのブラウザアプリ**として、render/edit/OCR の全処理をクライアント側
WASM/JS で実行し、**PDF bytes を端末外に出さない**。

## ライブラリ選定（no-Adobe / no-AGPL、WASM は必要箇所のみ）

| 役割 | ライブラリ | ライセンス | WASM |
|---|---|---|---|
| 構造編集・保存 | pdf-lib | MIT | 不要（純JS） |
| CJK フォント埋め込み | @pdf-lib/fontkit (+pako) | MIT | 不要 |
| ページ描画 → canvas | pdf.js (Mozilla) | Apache-2.0 | 一部 |
| OCR | tesseract.js | Apache-2.0 | ✅ WASM |
| 埋め込み日本語フォント | Sawarabi Gothic | OFL-1.1 | — |

→ 設計上の答え: **「Adobe非依存」と「WASM」は別軸**。本アプリは「純JS編集 + WASMレンダ +
WASM OCR」のハイブリッドで、Adobe非依存を最小コストで達成する。MuPDF/Ghostscript (AGPL)
と Adobe SDK は意図的に不採用。

## 編集モデル

`state.bytes`（現在の PDF）を唯一の真実とし、編集ごとに pdf-lib で load → 変更 → `save()`
→ 新 bytes に差し替え → pdf.js で再描画する単純で常に WYSIWYG な往復モデル。

## 日本語テキスト追記

`@pdf-lib/fontkit` を registerFontkit し、ASCII→Helvetica / 非ASCII→JP TTF を `subset: true`
で自動埋め込み。node 検証で出力に **Type0 / Identity-H / CIDFontType2 subset + FontFile2** を
確認（CJK 用の正しい CID フォント埋め込み）。

## vendor 化 / オフライン

import を bare specifier 化し `<script type="importmap">` を唯一の CDN/vendor 切替点とする
（既定 = esm.sh CDN、即起動）。`scripts/fetch-vendor.mjs` が 14 資産（pdf-lib / fontkit /
pako / pdf.js+worker / tesseract.js + wasm core + eng/jpn lang data + JP font, ≈50MB）を
`public/vendor/` に同梱し、`importmap.vendored.json` + `manifest.json` を生成。importmap 差し替え
+ CSP `connect-src 'self'` 有効化で **egress ゼロ** を技術的に保証。`public/vendor/` は gitignore。

## did:web actor 登録（ameno browser-local）

Canonical DID = `did:web:etzhayyim.com:actor:tsuzuri`。
`00-contracts/schemas/actor-profile-seed.kotoba.edn`（正本, kind `:infra` / tier `app`）+
`50-infra/etzhayyim-did-web/src/registry/infra-actors.ts`（フォールバック）+ `kotodama.jsonld`
（`uiType: ameno` / `runtimeType: logical` / `agentType: reactive`）に登録。

**正直なスコープ（CRITICAL）**: tsuzuri は DOM アプリで**単一 WASM コンポーネントではない**ため、
ameno の `wasm-actor-loader`（`EtzhayyimWasmComponent` + `ipfs://<cid>` を fetch+CID検証して
headless 実行）の**ロード対象ではない**。tsumugi/watatsuna 等の `:actor/wasm-cid` を持つ
componentize 系 actor とは別カテゴリ。service type は `EtzhayyimBrowserLocalApp` とし、
`EtzhayyimWasmComponent` を**詐称せず wasm-cid も付与しない**。アプリが*使う* WASM は
依存（pdf.js / tesseract.js）側であり、実行モデル（端末内 WASM/JS）が ameno の browser-local
に一致する、という意味での統合。

# Consequences

**Positive**

- Adobe・AGPL を排し Apache-2.0 + Charter Rider 既定を維持（NOTICE に第三者ライセンス明記）。
- PDF が端末外に出ない（プライバシー既定）、サーバー無し（no-server-key 自明に充足）。
- 日本語注釈が subset 埋め込みで本物に機能。
- importmap 1 点切替で CDN→完全オフラインへ無改修移行可能。
- OCR は tesseract.js のローカル WASM で完結し、外部推論サービス・商用 GPU を一切叩かない
  （ADR-2605215000 の商用 GPU 排除の精神に整合; これは LLM 推論ではない）。

**Negative / Honest limits**

- テキスト配置座標は**未回転ページ前提**（回転ページはずれる）。
- 各編集で全体を再保存するため巨大 PDF では遅い（差分編集モデルは将来）。
- vendor バンドルは ≈50MB（gitignore、`npm run vendor` で再現）。
- ブラウザ拡張未接続のため pdf.js 描画 / Tesseract OCR の**ブラウザ実走**は本セッション未確認
  （コアロジックは node で検証済）。
- DOM アプリゆえ単一 WASM コンポーネント化は不可 → ameno wasm-actor-loader 配信は対象外。

# Alternatives Considered

- **MuPDF / Ghostscript (AGPL)**: 高機能だが copyleft が permissive 既定を侵すため却下。
- **PDFium (BSD) を WASM 持ち込み**: 採用可能だがビルド/サイズが重く MVP には過剰。将来
  高精度レンダ/ラスタライズで再検討余地（BSD は Charter 互換）。
- **pdf.js のみ**: 表示中心で編集が弱い → 編集は pdf-lib に分担。
- **サーバーサイド処理**: 端末内完結 / no-server-key 違反のため却下。
- **アプリ全体の WASM コンポーネント化**: DOM 必須のため不可能。
- **Adobe SDK / サービス**: 設問の前提（Adobe非依存）に反するため却下。

# References

- アプリ: `60-apps/tsuzuri/`（`public/index.html`, `public/tsuzuri.js`, `scripts/fetch-vendor.mjs`,
  `kotodama.jsonld`, `README.md`, `CLAUDE.md`, `NOTICE`）
- 登録: `00-contracts/schemas/actor-profile-seed.kotoba.edn` / `50-infra/etzhayyim-did-web/src/registry/infra-actors.ts`
- PR #873（main merge commit `765edc66e5`）
- ADR-2606014500（One Worker, many WASM actors / ameno browser-local 実行モデル）
- ADR-2606013800（Actor profile + dynamic did.json）
- ADR-2605192200（Apache-2.0 + Charter Compliance Rider v2.0）
- ADR-2605231525（no-server-key）
- ADR-2605262130（kotoba storage substrate）
- ADR-2605215000（Murakumo-only inference — OCR は LLM 推論ではなくローカル WASM）
