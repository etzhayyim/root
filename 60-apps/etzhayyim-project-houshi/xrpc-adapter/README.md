# houshi XRPC Adapter

CF Worker that exposes the 3 kotoba commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/com.etzhayyim.houshi.storeSpore` — store spore data
- `POST /xrpc/com.etzhayyim.houshi.germinate` — germinate spore into organism
- `GET /xrpc/com.etzhayyim.houshi.listSpores?limit=...` — paginated spore listing

## Setup

```bash
cd 60-apps/etzhayyim-project-houshi/xrpc-adapter
npm install
```

## Development

```bash
npm run dev
# Worker listens on http://localhost:8787
```

## Example: Store Spore

```bash
curl -X POST http://localhost:8787/xrpc/com.etzhayyim.houshi.storeSpore \
  -H "Content-Type: application/json" \
  -d '{"sporeId":"sp-001","genomeJson":"{...}"}'
```

## Deploy

```bash
wrangler deploy
# Deploys to houshi.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
