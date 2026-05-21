# dns XRPC Adapter

CF Worker that exposes the 6 rw-free commands as XRPC endpoints.

## Endpoints

### Domain Transfer Workflow
- `POST /xrpc/ai.gftd.dns.createTransferRequest` — create transfer request
- `GET /xrpc/ai.gftd.dns.getTransferRequest` — get transfer by ID
- `POST /xrpc/ai.gftd.dns.transferFromSquarespace` — initiate Squarespace transfer
- `POST /xrpc/ai.gftd.dns.putTransferStep` — record transfer step
- `GET /xrpc/ai.gftd.dns.listTransferSteps` — list steps for transfer
- `POST /xrpc/ai.gftd.dns.putTransferOutcome` — record final outcome

## Deploy

```bash
wrangler deploy
# Deploys to dns.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
