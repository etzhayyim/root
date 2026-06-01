# isin XRPC Adapter

CF Worker that exposes the 11 rw-free commands as XRPC endpoints.

## Endpoints

### Security Registry
- `POST /xrpc/app.etzhayyim.isin.registerSecurity` — register ISIN security
- `GET /xrpc/app.etzhayyim.isin.getSecurity?isin=...` — security by ISIN
- `GET /xrpc/app.etzhayyim.isin.searchSecurities?query=...` — search securities
- `GET /xrpc/app.etzhayyim.isin.listSecurities?limit=...&offset=...` — paginated list

### Country & Entity
- `GET /xrpc/app.etzhayyim.isin.listByCountry?countryCode=...` — securities by country
- `POST /xrpc/app.etzhayyim.isin.registerEntity` — register entity (LEI)
- `GET /xrpc/app.etzhayyim.isin.validateIsin?isin=...` — validate ISIN

### Dashboard & Collection
- `GET /xrpc/app.etzhayyim.isin.getDashboard` — registry statistics
- `POST /xrpc/app.etzhayyim.isin.collectSecurities` — collect ISIN batch
- `POST /xrpc/app.etzhayyim.isin.collectEntityIR` — collect entity IR data
- `POST /xrpc/app.etzhayyim.isin.enrichISIN` — enrich ISIN metadata

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
