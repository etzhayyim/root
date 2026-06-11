# TIA wasmComponents Design (`/api/mcp` + `tia-seeker`)

## 1. Goal

`etzhayyim-project-tia` の MCP エンドポイントを App コンポーネントで実運用可能な形に再設計し、
Seeker 系処理を独立コンポーネント (`tia-seeker-component`) に分離する。

## 2. Components

- `tia-mcp-component`
  - public MCP gateway
  - `/api/mcp` JSON-RPC + REST (`/api/mcp/tools`, `/api/mcp/tools/{name}/call`)
  - GraphQL backend と seeker backend へのルーティング
- `tia-seeker-component`
  - seeker orchestration
  - 対象取得・プラットフォーム検索計画生成・観測報告受付

## 3. Endpoint Convention

MCP endpoint は host-based の convention に統一する。

- TIA MCP: `https://tia.etzhayyim.com/api/mcp`
- TIA Seeker MCP: `https://seeker.tia.etzhayyim.com/api/mcp`

legacy path-based endpoint (`https://{nanoid}.etzhayyim.com/xrpc`) は新規設計で使用しない。

## 4. `tia-mcp-component` Tool Contract

- `tia.accounts.list`
  - args: `project_id`, `limit`
  - backend: GraphQL `accounts(...)`
- `tia.detections.list`
  - args: `project_id`, `severity`, `limit`
  - backend: GraphQL `detections(...)`
- `tia.reports.publish`
  - args: `project_id`, `detection_id`, `channel`, `message`
  - backend: GraphQL `publishThreatReport(...)`
- `tia.seeker.run`
  - args: `project_id`, `platform`, `query`, `limit`
  - backend: `tia-seeker-component` へ JSON-RPC dispatch

## 5. `tia-seeker-component` Tool Contract

- `tia_seeker.targets.list`
  - args: `project_id`, `limit`
  - backend: `tia-mcp-component` の `tia.accounts.list`
- `tia_seeker.run`
  - args: `project_id`, `platform`, `query`, `limit`
  - behavior: 検索URLと seek job を生成、必要なら recorder sink に通知
- `tia_seeker.observe.report`
  - args: `project_id`, `account_id`, `platform`, `url`, `screenshot_url`, `note`
  - behavior: 観測結果を sink へ転送 (設定時)

## 6. Runtime Config

### tia-mcp-component

- `TIA_GRAPHQL_ENDPOINT`
  - default: `http://tia-ports-graphql-6ffwdypt:4000/api/graphql`
- `TIA_SEEKER_MCP_ENDPOINT`
  - default: `http://tia-seeker-component:8001/api/mcp`

### tia-seeker-component

- `TIA_MCP_ENDPOINT`
  - default: `http://tia-mcp-component:8001/api/mcp`
- `TIA_RECORDER_SINK`
  - optional webhook sink

## 7. Security + Context

両コンポーネントともに以下ヘッダを透過し、監査情報を上流へ伝播する。

- `Authorization`
- `X-ETZHAYYIM-ORG-ID`
- `X-ETZHAYYIM-USER-ID`

CORS は `tia.etzhayyim.com`, `seeker.tia.etzhayyim.com`, `etzhayyim.com`, `etzhayyim.com`, `localhost` 系を許可。

## 8. Deployment Notes

- WADM `Application` namespace は `kotodama-runtime`。
- `HTTPRoute` は gateway namespace (`etzhayyim-performers-org-org_34dKrNTTK3cNixZzHIzzFwLw1s4`) を使用し、
  backend service は `kotodama-system` を参照。
