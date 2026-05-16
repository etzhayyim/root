# open-power.gftd.ai — Electric Grid Operations & Network Design (OSS)

**Status**: MVP scaffold (2026-04-20). Reference implementation for electric
distribution network design (substations / feeders) and operations
(meter readings, outages). Apache-2.0.

## Scope (MVP)

| NSID | Type | Description |
|---|---|---|
| `ai.gftd.apps.openPower.defineSubstation` | procedure | declare a substation node + voltage class |
| `ai.gftd.apps.openPower.defineFeeder` | procedure | declare a feeder edge (substation → service area) |
| `ai.gftd.apps.openPower.getNode` | query | substation/service-point detail + downstream feeders |
| `ai.gftd.apps.openPower.listFeeders` | query | feeders by substation / status |
| `ai.gftd.apps.openPower.recordReading` | procedure | meter reading (kWh import / export) |
| `ai.gftd.apps.openPower.reportOutage` | procedure | outage with affected feeder + cause |
| `ai.gftd.apps.openPower.listOutages` | query | outages by feeder / since |
| `ai.gftd.apps.openPower.getLoadProfile` | query | hourly aggregate kWh per feeder |

## Architecture

- **Runtime**: Single CF Worker (`src/app.ts`)
- **Storage**: D1. Tables: `nodes`, `feeders`, `meter_readings`, `outages`
- **Identity**: substation/service point/feeder = path-based DIDs
  `did:web:open-power.gftd.ai:{node|feeder|outage}:{id}`
- **Topology**: `nodes` (substation, service_point) + `feeders` (directed
  edges substation → service_point cluster). Voltage class on each node
- **Outage class** by DMN (`openPower.outageClass`): customers affected +
  duration → `{class, requireRegulatoryReport}`
- **Audit**: class ≥ "regional" emits `app.bsky.feed.post`

## Not in MVP

- Real-time SCADA / phasor data
- DR (demand-response), VPP aggregation
- Tariff billing engine, settlement
- N-1 contingency analysis, optimal power flow

## Local Dev / Deploy

```bash
cd 60-apps/ai-gftd-project-open-power/worker
wrangler d1 create ai-gftd-open-power
gftd deploy
```
