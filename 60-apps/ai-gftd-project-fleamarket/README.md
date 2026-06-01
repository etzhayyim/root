# ai-gftd-project-fleamarket

フリマ（個人間売買）向けの App プロジェクト設計です。

## Design Principles

- 実行基盤: App component
- WIT world: `packages/wasm/world/gftd-component.wit` の `gftd:platform/gftd-mcp@0.1.0`
- UI 配信: `70-tools/gftd-static-site`
- 認証: Clerk (JWT + JWKS)

## Components

- `fleamarket-mcp-component`
  - `/api/mcp`, `/{nanoid}/api/mcp` を提供
  - Clerk JWT を検証して tool 実行
- `fleamarket-ui-k6p4x2n9`
  - `fleamarket.gftd.ai` 向け static site
  - MCP endpoint へ接続する最小 UI

詳細は `wasm/README.md` を参照してください。
