# ipaddress XRPC Adapter

CF Worker that exposes the 37 rw-free commands across 12 tiers as XRPC endpoints.

## Endpoints

- **ASN**: `POST .registerAsn`, `GET .getAsn`
- **Prefix**: `POST .registerPrefix`, `GET .getPrefix`
- **Provider**: `POST .registerProvider`, `GET .getProvider`
- **IP**: `POST .registerIp`, `GET .getIp`
- **Scan**: `POST .registerScan`, `GET .getScan`, `GET .listScans`
- **Search**: `GET .searchProviders`, `GET .listProviders`, `GET .listPrefixes`
- **Topology**: `GET .getDelegationChain`, `GET .getIpTopology`, `GET .getPeering`
- **Geo/Abuse**: `GET .getGeolocation`, `GET .getAbuseContact`
- **Collect**: `POST .collectGeoip`, `POST .collectWhois`, `POST .batchIngestRir`
- **List**: `GET .listAsns`, `GET .listIps`, `POST .batchRegisterIp`
- **Analyze**: `GET .analyzeIp`, `GET .analyzeAsn`, `GET .analyzePrefix`
- **Peering/RIR**: `POST .registerPeering`, `GET .listPeering`, `POST .registerRir`, `POST .registerNir`, `GET .getRir`, `GET .listRirs`, `GET .listNirs`, `GET .getNir`, `GET .getPrefixContainingIp`

## Setup

```bash
cd 60-apps/ai-gftd-project-ipaddress/xrpc-adapter
npm install
```

## Development

```bash
npm run dev
# Worker listens on http://localhost:8787
```

## Example: Register ASN

```bash
curl -X POST http://localhost:8787/xrpc/ai.gftd.apps.ipaddress.registerAsn \
  -H "Content-Type: application/json" \
  -d '{
    "asn": "AS65001",
    "country": "JP",
    "provider": "example-provider"
  }'
```

## Deploy

```bash
wrangler deploy
# Deploys to ipaddress.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
