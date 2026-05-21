# ai-gftd-project-okaimono

okaimono.gftd.ai — Amazon-grade AI-operated EC marketplace.

## Components

| Component | nanoid | 役割 |
|---|---|---|
| `okaimono-shopping-mcp-component` | `ok4imn1o` | Marketplace (catalog/orders/inventory/pricing/reviews/recommendations/fulfillment/procurement/support/analytics) |
| `okaimono-checkout-agent-component` | `chk8uty2` | Checkout SAGA orchestrator |

## Data Access

W Protocol Event Stream only:
- Write: `WRecord()` / `WUpdate()` / `WDelete()` → PDS → yata Cypher direct (SHA-256 content CID)
- Read: `G()` (Cypher)

## Deployment

```bash
cd wasm/okaimono-shopping-mcp-component && gftd build && gftd deploy
cd wasm/okaimono-checkout-agent-component && gftd build && gftd deploy
```

- `okaimono.gftd.ai` — marketplace UI + API
- `chk8uty2.gftd.ai` — checkout agent
