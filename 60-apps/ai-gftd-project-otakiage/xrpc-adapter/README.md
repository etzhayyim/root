# Otakiage XRPC Adapter

CF Worker exposing 13 rw-free commands as XRPC endpoints.

## Endpoints

Total: 13 commands across multiple tiers (see lexicons for full list).

## Setup

```bash
cd 60-apps/ai-gftd-project-otakiage/xrpc-adapter && npm install && npm run dev
```

## Deploy

```bash
wrangler deploy
# Deploys to otakiage.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
