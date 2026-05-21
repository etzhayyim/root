# open-banking XRPC Adapter

CF Worker that exposes the 5 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/ai.gftd.apps.openBanking.createAccount` — open account
- `GET /xrpc/ai.gftd.apps.openBanking.getAccount?accountId=...` — account + balance
- `GET /xrpc/ai.gftd.apps.openBanking.listAccounts?ownerDid=...` — paginated accounts
- `POST /xrpc/ai.gftd.apps.openBanking.transfer` — atomic double-entry transfer
- `GET /xrpc/ai.gftd.apps.openBanking.listTransactions?accountId=...` — ledger with running balance

## Setup

```bash
cd 60-apps/ai-gftd-project-open-banking/xrpc-adapter
npm install
```

## Development

```bash
npm run dev
# Worker listens on http://localhost:8787
```

## Example: Create Account

```bash
curl -X POST http://localhost:8787/xrpc/ai.gftd.apps.openBanking.createAccount \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "alice-checking",
    "ownerDid": "did:web:example.com:user:alice",
    "kind": "checking",
    "currency": "USD",
    "displayName": "Alice Checking"
  }'
# {"status":"created","accountUri":"...","did":"did:web:open-banking.etzhayyim.com:account:alice-checking"}
```

## Example: Transfer

```bash
curl -X POST http://localhost:8787/xrpc/ai.gftd.apps.openBanking.transfer \
  -H "Content-Type: application/json" \
  -d '{
    "transferId": "tx-001",
    "clientRequestId": "client-req-001",
    "fromAccountId": "alice-checking",
    "toAccountId": "bob-savings",
    "amountMinor": 10000,
    "currency": "USD",
    "memo": "coffee"
  }'
# {"status":"transferred","transferId":"tx-001",...}
```

## Deploy

```bash
wrangler deploy
# Deploys to open-banking.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
