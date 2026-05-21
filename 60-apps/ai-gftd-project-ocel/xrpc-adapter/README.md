# ocel XRPC Adapter

CF Worker exposing 3 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/ai.gftd.ocel.recordEvent` — record event
- `GET /xrpc/ai.gftd.ocel.getEvent` — event by ID
- `GET /xrpc/ai.gftd.ocel.listEvents` — paginated list

## Deploy

```bash
wrangler deploy
```

See ADR-2605210000.
