# dns XRPC Adapter

CF Worker that exposes the 6 rw-free commands as XRPC endpoints.

## Endpoints

### Domain Transfer Workflow
- `POST /xrpc/app.etzhayyim.dns.createTransferRequest` — create transfer request
- `GET /xrpc/app.etzhayyim.dns.getTransferRequest` — get transfer by ID
- `POST /xrpc/app.etzhayyim.dns.transferFromSquarespace` — initiate Squarespace transfer
- `POST /xrpc/app.etzhayyim.dns.putTransferStep` — record transfer step
- `GET /xrpc/app.etzhayyim.dns.listTransferSteps` — list steps for transfer
- `POST /xrpc/app.etzhayyim.dns.putTransferOutcome` — record final outcome

## Deploy

```bash
wrangler deploy
# Deploys to dns.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
