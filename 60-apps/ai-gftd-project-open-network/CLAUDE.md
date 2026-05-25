# open-network.etzhayyim.com — Telecom Network Operations & Design (OSS)

**Status**: MVP scaffold (2026-04-20). Reference NMS — site/link topology
design, link utilization ingest, incident reporting, change request
workflow. Apache-2.0.

## Scope (MVP)

| NSID | Type | Description |
|---|---|---|
| `app.etzhayyim.apps.openNetwork.defineSite` | procedure | network site (PoP / DC / cell tower / customer edge) |
| `app.etzhayyim.apps.openNetwork.defineLink` | procedure | bidirectional link between two sites + capacity Mbps + media |
| `app.etzhayyim.apps.openNetwork.getSite` | query | site detail + adjacent links |
| `app.etzhayyim.apps.openNetwork.listLinks` | query | links by site / status |
| `app.etzhayyim.apps.openNetwork.recordUtilization` | procedure | link 5-min Mbps sample (in/out) |
| `app.etzhayyim.apps.openNetwork.getLinkUtilization` | query | hourly aggregate per link |
| `app.etzhayyim.apps.openNetwork.reportIncident` | procedure | NOC incident with severity + impact |
| `app.etzhayyim.apps.openNetwork.listIncidents` | query | incidents by site / link / since |
| `app.etzhayyim.apps.openNetwork.requestChange` | procedure | change request with risk DMN |
| `app.etzhayyim.apps.openNetwork.listChanges` | query | change requests by status |

## Architecture

- **Runtime**: Single CF Worker (`src/app.ts`)
- **Storage**: D1. Tables: `sites`, `links`, `utilization`, `incidents`, `changes`
- **Identity**: site/link/incident/change = path-based DIDs
- **Topology**: undirected graph (sites + links). Each link records bidirectional capacity
- **Incident severity** by DMN (`openNetwork.incidentSeverity`):
  customers impacted + minutes → SEV1..SEV5
- **Change risk** by DMN (`openNetwork.changeRisk`):
  blast radius + reversibility + maintenance window → RISK_LOW/MED/HIGH +
  approverLevel
- **Audit**: SEV1/SEV2 incidents and HIGH-risk changes → `app.bsky.feed.post`

## Not in MVP

- BGP/IPAM/AS-level routing (separate project)
- Realtime SNMP/streaming-telemetry collector
- Predictive capacity planning, ML-based anomaly detection

## Local Dev / Deploy

```bash
cd 60-apps/ai-gftd-project-open-network/worker
wrangler d1 create ai-gftd-open-network
e7m actor deploy .
```
