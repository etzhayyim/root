# open-gas.gftd.ai — Gas Utility Operations & Network Design (OSS)

**Status**: MVP scaffold (2026-04-20). Reference implementation for natural-gas
distribution network design (city-gate / regulators / pipe segments) and
operations (meter readings, leak reports, pressure logs). Apache-2.0.

## Scope (MVP)

| NSID | Type | Description |
|---|---|---|
| `ai.gftd.apps.openGas.defineRegulator` | procedure | city-gate / district regulator node + outlet pressure |
| `ai.gftd.apps.openGas.definePipeSegment` | procedure | pipe segment (regulator → service points), DN + material + MAOP |
| `ai.gftd.apps.openGas.getNode` | query | node detail + downstream segments |
| `ai.gftd.apps.openGas.listSegments` | query | segments by regulator / status |
| `ai.gftd.apps.openGas.recordReading` | procedure | meter reading (m³) |
| `ai.gftd.apps.openGas.reportLeak` | procedure | leak with class (DOT-aligned 1/2/3) |
| `ai.gftd.apps.openGas.listLeaks` | query | leaks by segment / since / minClass |
| `ai.gftd.apps.openGas.recordPressureLog` | procedure | inlet/outlet pressure sample |
| `ai.gftd.apps.openGas.listPressureLogs` | query | pressure logs by segment / since |

## Architecture

- **Runtime**: Single CF Worker (`src/app.ts`)
- **Storage**: D1. Tables: `nodes`, `segments`, `meter_readings`, `leaks`, `pressure_logs`
- **Identity**: regulator/service-point/segment/leak = path-based DIDs
- **Topology**: directed regulator → service-point cluster via segments
- **Leak class** by DMN (`openGas.leakClass`): grade 1/2/3 — hazard to
  persons/property → emergency / scheduled-repair / routine. Class 1 →
  immediate gov audit
- **MAOP enforcement**: pressure log > MAOP triggers `app.bsky.feed.post`

## Not in MVP

- SCADA inlet/outlet realtime, RTU integration
- Cathodic protection telemetry
- Tariff billing, NRG (non-revenue gas)

## Local Dev / Deploy

```bash
cd 60-apps/ai-gftd-project-open-gas/worker
wrangler d1 create ai-gftd-open-gas
gftd deploy
```
