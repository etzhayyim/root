# etzhayyim-project-agentgateway

AI Agent Gateway (`agentgateway`) is the application-level MCP (Model Context Protocol) router built on top of the AT Protocol. It serves as the primary entry point for AI Agents to discover and call tools across the etzhayyim ecosystem.

## Architecture

* **Runtime:** Cloudflare Worker
* **Protocol:** AT Protocol (XRPC), JSON-RPC 2.0 (MCP)
* **Target Interface:** `com.etzhayyim.mcp.message`

Unlike the Envoy Gateway which handles network-level ingress and security, the `agentgateway` specifically handles MCP requests (`tools/list`, `tools/call`, etc.), routing them to the appropriate backend services based on the requested tool ID.

## Development

```bash
cd worker
pnpm install
npm run dev
```

## Deployment

```bash
cd worker
npm run deploy
```
