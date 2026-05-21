# houshi XRPC Adapter

CF Worker that exposes the 3 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/ai.gftd.houshi.storeSpore` — store spore data
- `POST /xrpc/ai.gftd.houshi.germinate` — germinate spore into organism
- `GET /xrpc/ai.gftd.houshi.listSpores?limit=...` — paginated spore listing

## Setup

```bash
cd 60-apps/ai-gftd-project-houshi/xrpc-adapter
npm install
```

## Development

```bash
npm run dev
# Worker listens on http://localhost:8787
```

## Example: Store Spore

```bash
curl -X POST http://localhost:8787/xrpc/ai.gftd.houshi.storeSpore \
  -H "Content-Type: application/json" \
  -d '{"sporeId":"sp-001","genomeJson":"{...}"}'
```

## Deploy

```bash
wrangler deploy
# Deploys to houshi.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
