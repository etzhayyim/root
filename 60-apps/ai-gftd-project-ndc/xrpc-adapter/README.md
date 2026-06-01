# ndc XRPC Adapter

CF Worker that exposes the 3 rw-free commands as XRPC endpoints.

## Endpoints

### Drug Registry (US FDA NDC + WHO ATC)
- `POST /xrpc/app.etzhayyim.ndc.registerDrug` — register drug
- `GET /xrpc/app.etzhayyim.ndc.lookupByCode` — lookup by code
- `GET /xrpc/app.etzhayyim.ndc.listDrugs` — paginated list

## Deploy

```bash
wrangler deploy
# Deploys to ndc.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
