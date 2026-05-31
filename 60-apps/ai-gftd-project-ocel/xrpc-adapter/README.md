# ocel XRPC Adapter

CF Worker exposing 3 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/app.etzhayyim.ocel.recordEvent` — record event
- `GET /xrpc/app.etzhayyim.ocel.getEvent` — event by ID
- `GET /xrpc/app.etzhayyim.ocel.listEvents` — paginated list

## Deploy

```bash
wrangler deploy
```

See ADR-2605210000.
