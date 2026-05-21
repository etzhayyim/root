# Ki XRPC Adapter

CF Worker exposing 4 rw-free commands as XRPC endpoints.

## Endpoints

Total: 4 commands across multiple tiers (see lexicons for full list).

## Setup

```bash
cd 60-apps/ai-gftd-project-ki/xrpc-adapter && npm install && npm run dev
```

## Deploy

```bash
wrangler deploy
# Deploys to ki.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
