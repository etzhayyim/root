# mailer-mcp-component (Go App Component)

This component exposes mailer MCP endpoints on `/api/mcp` and `/{nanoid}/api/mcp`.

## Endpoints

- `POST /api/mcp` (JSON-RPC 2.0: `tools/list`, `tools/call`)
- `GET /api/mcp/tools`
- `POST /api/mcp/tools/{tool}/call`
- `POST /api/mcp` on `ra27m5t6.etzhayyim.com`

## Required Environment

- `CLERK_JWKS_URL`

## Optional Environment

- `CLERK_ISSUER`
- `CLERK_AUDIENCE`

## Build

```bash
etzhayyim build
```

## Deploy

```bash
kubectl apply -f <repo-deploy-config>
```

## Runtime notes

- This App component is self-contained and does not call legacy runtime-side services.
