# etzhayyim-project-commodities

Global commodity market data with individual wasm components per commodity.

## Architecture

All 25 commodity Apps are deployed and accessible via per-subdomain direct routing.

```
Browser/AI Agent
  └─ API → {nanoid}.etzhayyim.com → Cloudflare → Envoy Gateway
              ↓ HTTPRoute (per-App, hostname: {nanoid}.etzhayyim.com)
           App Service (kotodama-runtime:80, kotodama-operator auto-created)
```

No performers-gateway-provider intermediary. Each App has its own subdomain.

## Deployment Status (25/25 live)

| Symbol | Nanoid | Exchange | API Path |
|--------|--------|----------|----------|
| CL | e1cl2o3p | XCME | `/commodity.v1.CommodityService/*` |
| BZ | e2bz4r5s | XCME | `/commoditybz.v1.CommodityBzService/*` |
| NG | e3ng6t7u | XCME | `/commodity.v1.CommodityService/*` |
| RB | e4rb8v9w | XCME | `/commodity.v1.CommodityService/*` |
| HO | e5ho1a2b | XCME | `/commodity.v1.CommodityService/*` |
| LE | l1le3m4n | XCME | `/commodity.v1.CommodityService/*` |
| HE | l2he5o6p | XCME | `/commodity.v1.CommodityService/*` |
| GC | p1gc3c4d | XCEC | `/commodity.v1.CommodityService/*` |
| SI | p2si5e6f | XCEC | `/commodity.v1.CommodityService/*` |
| PL | p3pl7g8h | XCEC | `/commodity.v1.CommodityService/*` |
| PA | p4pa9i1j | XCEC | `/commodity.v1.CommodityService/*` |
| HG | b1hg2k3l | XCEC | `/commodity.v1.CommodityService/*` |
| ZC | g1zc3u4v | XCBT | `/commodity.v1.CommodityService/*` |
| ZS | g2zs5w6x | XCBT | `/commodity.v1.CommodityService/*` |
| ZW | g3zw7y8z | XCBT | `/commodity.v1.CommodityService/*` |
| ZL | g4zl9a1b | XCBT | `/commodity.v1.CommodityService/*` |
| ZM | g5zm2c3d | XCBT | `/commodity.v1.CommodityService/*` |
| KC | s1kc4e5f | IFUS | `/commodity.v1.CommodityService/*` |
| SB | s2sb6g7h | IFUS | `/commodity.v1.CommodityService/*` |
| CC | s3cc8i9j | IFUS | `/commodity.v1.CommodityService/*` |
| CT | s4ct1k2l | IFUS | `/commodity.v1.CommodityService/*` |
| AH | b2ah4m5n | XLME | `/xrpc/commodity.v1.CommodityService/*` |
| ZSLME | b3zs6o7p | XLME | `/commodity.v1.CommodityService/*` |
| NI | b4ni8q9r | XLME | `/commodity.v1.CommodityService/*` |
| PB | b5pb1s2t | XLME | `/commodity.v1.CommodityService/*` |

**Note**: AH (pilot) uses `/xrpc` prefix. BZ uses `commoditybz.v1.CommodityBzService` path.

## SDK & Build

- **Runtime**: TS Native (`src/app.ts` + `@etzhayyim/kotodama-host-sdk`)
- **KV**: `performer/rdbms.OpenStore("default")` → sql graph RDBMS backing table
- **Executor**: `containerd-shim-kotodama` (standard, NOT `containerd-shim-kotodama-nats`)

## App Manifest Template

```yaml
apiVersion: core.kotodama-runtime.dev/v1alpha1
kind: App
metadata:
  name: etzhayyim-wasm-commodity-{symbol}-{nanoid}
  namespace: kotodama-runtime
spec:
  image: ghcr.io/etzhayyim/etzhayyim-wasm-commodity-{symbol}-{nanoid}:{tag}
  executor: containerd-shim-kotodama
  replicas: 1
  imagePullSecrets:
    - name: ghcr-pull-secret
```

## Component Count: 25 (commodity Apps only)

## Commodity Groups (HS Classification)

| Group | HS Chapter | Exchange | Count |
|-------|-----------|----------|-------|
| Energy | 27 | XCME | 5 |
| Precious Metals | 71 | XCEC | 4 |
| Base Metals | 74-79 | XCEC/XLME | 5+1 (HG on XCEC, rest XLME) |
| Grains & Oilseeds | 10, 12 | XCBT | 5 |
| Softs | 09, 17, 18, 52 | IFUS | 4 |
| Livestock | 01, 02 | XCME | 2 |

## KV Storage (sql graph RDBMS)

- Bucket: `commodities-store` (in the RDBMS backing table)
- Key schema: `commodity_{exchange}_{symbol}_{datatype}`
  - `commodity_xcme_cl_info` — Commodity info
  - `commodity_xcme_cl_price_2026-02-28` — Daily price
  - `commodity_xcme_cl_flow_2026-02-28` — Daily flow
  - `commodity_xcme_cl_producers_2025` — Production data
  - `commodity_xcme_cl_consumers_2025` — Consumption data

## API Endpoints (per component)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/commodity.v1.CommodityService/GetInfo` | Commodity metadata |
| POST | `/commodity.v1.CommodityService/GetPriceSankey` | Price cascade Sankey |
| POST | `/commodity.v1.CommodityService/GetSupplyChain` | Supply chain Sankey |
| POST | `/commodity.v1.CommodityService/GetPriceDecomposition` | Price breakdown |
| POST | `/commodity.v1.CommodityService/GetGlobalTradeFlow` | Import/export flows |
| POST | `/commodity.v1.CommodityService/GetProducers` | Top producers |
| POST | `/commodity.v1.CommodityService/GetConsumers` | Top consumers |
| GET | `/health` | Health check |

## Verification

```bash
# Health check
curl https://{nanoid}.etzhayyim.com/health

# GetInfo
curl -X POST https://{nanoid}.etzhayyim.com/commodity.v1.CommodityService/GetInfo \
  -H "Content-Type: application/json" -d '{}' | jq .

# Batch health sweep
for n in e1cl2o3p e2bz4r5s e3ng6t7u ...; do
  curl -s "https://${n}.etzhayyim.com/health" | jq -r '.commodity // .symbol'
done
```

## Data Sources

| Source | Data |
|--------|------|
| CME Group | Futures prices, settlement, volume, open interest |
| EIA | Energy production, consumption, inventory |
| USDA | Agricultural production, consumption, trade |
| World Bank | Commodity price indices, historical data |
| UN COMTRADE | International trade flows |
| OPEC | Oil production quotas, output |
| LME | Base metal prices, warehouse stocks |
| ICE | Soft commodity prices |

## Cross-Project Dependencies

- ISIN cross-link — `(:Commodity)-[:PRODUCED_BY]->(:Security {isin})` SQL edge (旧 `etzhayyim:public-company` WIT は除去済み → `etzhayyim:isin@1.0.0` + SQL graph に移行)
- `etzhayyim:resource-flow@0.1.0` — Shared Sankey visualization patterns
