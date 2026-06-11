---
id: adr-2604261110-wproto-wreactive-wit-retirement
title: "ADR: wproto / wreactive / WIT を dead path 化、browser は @atproto/api 直接、Signal は新パッケージへ分離"
status: proposed
doc_type: adr
topic: protocol-layer-retirement
authoritative: true
last_verified: 2026-04-26
authoritative_for:
  - browser-xrpc-client
  - signal-e2e-package-location
  - wit-terminal-scope
related:
  - adr-2604261100-rego-dmn-policy-decision-layers
  - adr-0019-identifier-topology
  - adr-0036-worker-direct-hyperdrive-persistence
supersedes: []
superseded_by: []
amends: []
---

# Context

DSM 整理 (2026-04-26) で、現 contract layer のうち以下 3 つは Shannon η の
観点で冗長 / 縮退:

1. **WIT** (`_archive/00-contracts/wit/`, `_archive/wit-2026-04-13/`)
   F-Plan 2026-04-13 で `com.etzhayyim.host.*` Lexicon JSON に置換済み。
   T3 Container (`etzhayyim-wasm-cad-cd4dview`) と Rust `contract-jco`
   (`etzhayyim-wasm-hoge-h0g3t3st`) のみ in-tree `wit/` を保持。
2. **wproto** (`10-protocol/wproto/`)
   N3 migration (2026-04-12) 後は `@atproto/api` AtpAgent の facade に
   縮退。235 typed XRPC wrapper を保持しているが、Lexicon 起点の
   client codegen に統合可能。Signal Protocol E2E (`src/signal.ts`) と
   secret 系 (`vault.ts`) のみが wproto 固有資産。
3. **wreactive** — `[[conventions]] wRPC Reactive Pipeline` (deps.toml
   line 5714) と CLAUDE.md pointer のみ存在し、対応する code / package
   は未実装。dead convention。

ADR-2604261100 が Rego + DMN を一級化するのと並行して、subtractive 側
を本 ADR で一括宣言する。

# Decision

## 1. WIT — terminal、新規禁止

- **新規 component で `wit/world.wit` を追加することを禁止**。
- 既存 2 例外 (`etzhayyim-wasm-cad-cd4dview` Container runtime,
  `etzhayyim-wasm-hoge-h0g3t3st` contract-jco generator) は legacy compat
  として **凍結** (機能追加なし、bug fix のみ)。
- `com.etzhayyim.host.*` Lexicon を全 host capability の SSoT として再宣言
  (F-Plan 2026-04-13 を上書き)。
- `Governance WIT` / `WIT Lexicon Typed Alignment` / `Contract WIT` /
  `W Protocol Query WIT` などの旧 convention は all `[[conventions]]`
  から削除し、本 ADR を sole reference とする。

## 2. wproto — 解体、3 経路に分配

`10-protocol/wproto/` を以下 3 つに分配して廃止:

| 旧 wproto 資産 | 移行先 | 経路 |
|---|---|---|
| 235 typed XRPC wrapper (browser) | **`@atproto/api` AtpAgent 直接呼び出し** | call site で `agent.com.atproto.repo.*` / `agent.app.bsky.*` / `agent.api.call('com.etzhayyim.apps.foo.bar', ...)` に書き換え |
| `src/signal.ts` (Signal Protocol E2E) | **新パッケージ `10-protocol/signal/`** | パッケージ独立、wproto に依存しない |
| `src/vault.ts` (secret bootstrap) | **新パッケージ `10-protocol/signal/` 配下 or `kotodama-host-sdk`** | 評価して fast-follow ADR で確定 |
| `src/client.ts` / `service.ts` (session bootstrap) | **削除** (AtpAgent.login で代替) | — |
| stream consumers / W-extension types | **`@atproto/api` の types + Lexicon-generated types** | wproto 固有型は廃止 |
| `server-wproto` | **削除** (SSR は ADR-0036 Worker-direct で不要) | — |

### Browser XRPC client policy

- **公式 Lexicon (`com.atproto.*` / `app.bsky.*` / `chat.bsky.*` /
  `tools.ozone.*`)** → `@atproto/api` AtpAgent の typed method を直接
  使用。
- **`com.etzhayyim.*` 拡張 NSID** → Lexicon JSON から **browser client を
  codegen** (host 側 `host-client.ts` と対称、後続 ADR で実装計画)。
  暫定は `agent.api.call('com.etzhayyim.apps.foo.bar', input)` で動かす。
- **両方とも単一 AtpAgent インスタンス**を使用 (session / DPoP / refresh
  を一元管理)。

### Signal package (`10-protocol/signal/`)

- パッケージ名: `@etzhayyim/signal`
- 公開 API: `signal:v1:` envelope encode/decode、prekey bundle exchange、
  X3DH + double-ratchet。`com.etzhayyim.signal.*` Lexicon を本パッケージが
  consume する側、record 定義は `00-contracts/lexicons/com/etzhayyim/signal/`
  に維持。
- 依存: `@atproto/api` (transport), libsodium (crypto)。**`@etzhayyim/wproto`
  に依存しない**。
- CRITICAL convention `Signal Protocol E2E` の SSoT pointer を
  `10-protocol/wproto/src/signal.ts` から `10-protocol/signal/` に
  移動。
- 移行は本 ADR commit 直後に作業 issue として `[[migrations]]
  signal-extract-from-wproto` で track。

## 3. wreactive — 即時削除

- `[[conventions]] wRPC Reactive Pipeline` を deps.toml から削除。
- CLAUDE.md pointer 行を削除。
- 関連実装は元から存在しないため code change なし。

# Migration plan

| Step | Action | Track |
|---|---|---|
| 0 | 本 ADR + ADR-2604261100 を merge | done in PR |
| 1 | `10-protocol/signal/` package 雛形作成、`signal.ts` 移植 | `[[migrations]] signal-extract-from-wproto` |
| 2 | `appshellv2` / 他 wproto consumer を AtpAgent 直接 + `@etzhayyim/signal` に書き換え | per-app PR |
| 3 | `com.etzhayyim.*` 用 browser codegen (`gen-browser-client-from-lexicon.mjs`) 設計 ADR | fast-follow |
| 4 | 235 typed wrapper 全廃 → call site 書き換え完了後 `10-protocol/wproto/` を `_archive/` に移動 | `[[migrations]] wproto-retirement` |
| 5 | `server-wproto` 削除 | `[[migrations]] server-wproto-removal` |

dead path 化は本 ADR 採択時点で発効 (新規 import 禁止)、`_archive/`
移動は step 4 完了時。

# Consequences

- Browser 側の XRPC 経路が `@atproto/api` 単一 SDK + Lexicon-generated
  client に統一され、Shannon η=1 を回復。
- Signal E2E が独立パッケージ化され、XRPC client の都合と切り離される。
- WIT を retire することで「TS Native (DEFAULT) は Lexicon JSON、Container
  例外のみ WIT」という 2-way fork が ADR レベルで明確化。
- 既存の wproto-import を持つ ~数十 app の書き換え作業が発生。AtpAgent
  facade はすでに薄いため API 互換は概ね保てる。
- `Signal Protocol E2E` CRITICAL convention の SSoT 移動を伴うため、
  consumer (yoro / vault 系) の import 書き換えが必須。

# Alternatives Considered

- **wproto 維持 (薄い facade のまま放置)**: AtpAgent + 235 wrapper の
  二重 surface が残り Shannon η が低下。却下。
- **Signal を wproto に残し wproto を signal-only に縮小**: 名前が誤誘導
  (W Protocol ≠ Signal)。新パッケージで意味的に正しい境界を引く。却下。
- **Signal を `kotodama-host-sdk` に吸収**: Signal は browser-side
  primitive、host capability ではない。却下。
- **WIT を全 component で即時禁止**: T3 Container は wasmtime linking で
  WIT 必須、Rust contract-jco も jco 生成に WIT 必須。即時禁止は破壊的。
  terminal scope (新規禁止 + 既存凍結) を採択。

# References

- 90-docs/adr/2604261100-rego-dmn-policy-decision-layers.md (additive companion)
- 90-docs/adr/0019-identifier-topology-atproto-native-5-layer.md
- 90-docs/adr/0036-worker-direct-hyperdrive-persistence.md
- 10-protocol/wproto/ (retiring)
- 00-contracts/lexicons/com/etzhayyim/signal/ (E2E lexicon, 維持)
