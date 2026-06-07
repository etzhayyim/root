# etzhayyim-project-rireki

履歴書・職務経歴書作成プラットフォーム (rireki.etzhayyim.com). yagish 風の SuperApp App.

## Architecture

- **Runtime**: TS Native + Lexicon Contract
- **Domain**: `rireki.etzhayyim.com`
- **nanoid**: `a41574ad`
- **Static**: static delivery で `svelte/build/` を配信

## CRITICAL: XRPC URL Pattern

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-rireki-xrpc-url-pattern` / MCP `etzhayyim.dodaf.tv1.query`

## Features

- JIS 規格準拠の履歴書テンプレート
- 職務経歴書 (Chronological / Functional)
- セクション単位の自動保存 (kotodama WIT)
- AI 文面アシスト (志望動機・自己PR)
- 顔写真アップロード (Nata Blob API)
- PDF エクスポート (サーバーサイド生成)
- 複数履歴書管理

## Arrow Tables (4)

| テーブル | 用途 |
|----------|------|
| `rireki_documents` | 履歴書ドキュメント管理 |
| `rireki_sections` | セクションデータ (個別保存) |
| `rireki_templates` | テンプレートマスタ |
| `rireki_exports` | PDF エクスポート履歴 |
