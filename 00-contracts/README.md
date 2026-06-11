# 00-contracts

`00-contracts` は schema / AT Protocol Lexicon / generated binding の契約層です。

## 責務

- `lexicons`: AT Protocol Lexicon JSON **Single Source of Truth** (2693 files, うち `com.etzhayyim.*` は 2344 files)。host capability (`com.etzhayyim.host.*`) / app commands (`com.etzhayyim.apps.*`) / wire format を一括で定義。F-Plan F2 2026-04-13 以降、TS/Go/Rust bindings は全てこれから codegen
- 共有 schema（graph schema など）の静的定義

## 非責務

- runtime の endpoint routing / dispatch 実装
- protocol transport や middleware の実装
- infra の運用設定（Worker 設定、DB 接続制御）

## 依存境界

- contract 層は runtime 層に依存しない
- contract 層は infra worker に依存しない
- runtime は contract を参照してよい (`@etzhayyim/kotodama-host-sdk` → `00-contracts/lexicons/`)

## Archived (2026-04-13, F-Plan)

- `wit/` — WIT-based host-guest contract は `_archive/00-contracts/wit/` にアーカイブ済み。T3 Container (wasmtime) + Rust contract-jco の 2 components のみ in-tree legacy 例外。設計 doc: `90-docs/atproto/260413-f-plan-lexicon-as-contract.md`
- `kotodama-host-contract/` — 12 行の TS binding stub は `kotodama-host-sdk/src/types.ts` に inline 済み。package は `_archive/00-contracts/kotodama-host-contract-260413/` にアーカイブ
