# isin XRPC Adapter

CF Worker that exposes the 11 rw-free commands as XRPC endpoints.

## Endpoints

### Security Registry
- `POST /xrpc/ai.gftd.isin.registerSecurity` — register ISIN security
- `GET /xrpc/ai.gftd.isin.getSecurity?isin=...` — security by ISIN
- `GET /xrpc/ai.gftd.isin.searchSecurities?query=...` — search securities
- `GET /xrpc/ai.gftd.isin.listSecurities?limit=...&offset=...` — paginated list

### Country & Entity
- `GET /xrpc/ai.gftd.isin.listByCountry?countryCode=...` — securities by country
- `POST /xrpc/ai.gftd.isin.registerEntity` — register entity (LEI)
- `GET /xrpc/ai.gftd.isin.validateIsin?isin=...` — validate ISIN

### Dashboard & Collection
- `GET /xrpc/ai.gftd.isin.getDashboard` — registry statistics
- `POST /xrpc/ai.gftd.isin.collectSecurities` — collect ISIN batch
- `POST /xrpc/ai.gftd.isin.collectEntityIR` — collect entity IR data
- `POST /xrpc/ai.gftd.isin.enrichISIN` — enrich ISIN metadata

## Setup

```bash
cd 60-apps/ai-gftd-project-isin/xrpc-adapter
npm install
```

## Deploy

```bash
wrangler deploy
# Deploys to isin.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
