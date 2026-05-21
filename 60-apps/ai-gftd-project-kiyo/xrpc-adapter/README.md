# Kiyo XRPC Adapter

CF Worker exposing 12 rw-free commands as XRPC endpoints.

## Endpoints

Total: 12 commands across multiple tiers (see lexicons for full list).

## Setup

```bash
cd 60-apps/ai-gftd-project-kiyo/xrpc-adapter && npm install && npm run dev
```

## Deploy

```bash
wrangler deploy
# Deploys to kiyo.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
