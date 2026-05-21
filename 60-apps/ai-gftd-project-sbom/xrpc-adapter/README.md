# Sbom XRPC Adapter

CF Worker exposing 17 rw-free commands as XRPC endpoints.

## Endpoints

Total: 17 commands across multiple tiers (see lexicons for full list).

## Setup

```bash
cd 60-apps/ai-gftd-project-sbom/xrpc-adapter && npm install && npm run dev
```

## Deploy

```bash
wrangler deploy
# Deploys to sbom.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
