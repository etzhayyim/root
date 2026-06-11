---
id: maps-worldmonitor-parity
title: "maps.etzhayyim.com World Monitor parity status"
status: active
doc_type: reference
topic: maps-world-monitor-parity
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - maps-worldmonitor-public-coverage
  - maps-worldmonitor-runtime-status
related:
  - adr-2605141930-world-monitor-resident-intelligence-graph
  - adr-2604282300
  - adr-2605080600-langgraph-server-granian-l3-runtime
supersedes: []
superseded_by: []
---

# maps.etzhayyim.com World Monitor Parity Plan

Status date: 2026-05-14

Reference: https://www.worldmonitor.app/

## Public Coverage Gate

Current public product coverage is **100%** for the World Monitor-style
resident intelligence dashboard surface.

Last verified on 2026-05-14 against:

```bash
POST https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.getWorldMonitorDashboard
```

Observed dashboard evidence:

- HTTP 200
- `source = "pod-langserver"`
- `degraded = null`
- `error = null`
- `coverage.coveredCapabilities = 7`
- `coverage.totalCapabilities = 7`
- `coverage.productCoveragePct = 100`
- `coverage.implementationCoveragePct = 55`
- `coverage.gaps = []`
- `coverage.ddlFreeFacade = true`
- `counts.marketSignals = 903`

The public supporting XRPCs also returned HTTP 200 from the pod LangServer:

- `com.etzhayyim.apps.maps.listIntelEvents`
- `com.etzhayyim.apps.maps.getRiskSnapshot`
- `com.etzhayyim.apps.maps.getLatestBrief`
- `com.etzhayyim.apps.maps.listIntelAlerts`

## Current Parity

| Area | Current parity | Evidence | Gap |
|---|---:|---|---|
| Map-first operations UI | 60% | `App.svelte` has the World Monitor-inspired dashboard, layer catalog, time windows, risk score, and live intel feed. | Polish, saved workspaces, alert workflows, and source drill-down are incomplete. |
| Live transport layers | 70% | Aircraft, satellite, AIS, weather, transit, route, and infrastructure XRPCs are registered in `src/app.ts`; World Monitor reads are pod-side. | Some live layer endpoints still need the same pod-side hardening as the World Monitor facade. |
| Spatial risk summary | 70% | `getRiskSnapshot` and `getWorldMonitorDashboard` return score, level, confidence, event count, trend, and drivers from `maps-read-langserver`. | Country/admin-area drill-down and durable comparison windows are still thin. |
| Geopolitical/security intelligence | 70% | `listIntelEvents`, `listIntelAlerts`, and dashboard event panels are public XRPCs backed by pod-side reads. | Actor attribution and citation depth need richer feed integration. |
| Market/trade/macro intelligence | 60% | Dashboard includes `marketSignals` from existing market demand-signal graph data; verified count is 903. | Commodity, trade-route, sanctions, and supply-chain exposure scoring remain future work. |
| AI brief/analysis loop | 70% | `getLatestBrief` and dashboard brief cards return from pod LangServer; alert routing facade is live. | Autonomous classification, summary generation, and routing should move into dedicated LangGraph/Pregel workers. |
| 3D/digital twin | 50% | maps3d, gsplat, COLMAP, KAMI chunks, and twin endpoints exist. | Curator and actor-link workers remain scaffold-heavy; production semantic linking is thin. |

## Coverage By Runtime

| Runtime surface | Coverage | Notes |
|---|---:|---|
| Public World Monitor XRPC surface | 100% | Five public XRPCs return HTTP 200 through `maps.etzhayyim.com`; dashboard reports `productCoveragePct = 100` and `gaps = []`. |
| Cloudflare edge / langserver contract surface | 90% | Worker registers the World Monitor XRPCs and proxies them to pod-side reads; the edge remains a thin facade. |
| Edge-local product semantics | 80% | World Monitor product semantics are now pod-side. Remaining edge-local reads should be retired or converted as follow-up. |
| maps coverage LangGraph | 65% | `maps-coverage-langgraph` runs coverage tick and stats refresh flows. Scope is coverage only. |
| generic `lg-pregel` deployment | 0% for maps | Current `50-infra/k8s/pregel` is Outlook triage, not maps. |
| maps3d LangGraph workers | 30% | COLMAP path is real; curator and actor-link are still scaffold/stub-heavy. |
| World Monitor-style resident intelligence graph facade | 100% product / 55% implementation | Read facade is live and verified. Deeper autonomous graph execution is still future work. |

## Implementation Checklist

### P0: Restore Reliable Runtime

- [x] Redeploy `kotodama-uqpel6i6` so `maps.etzhayyim.com/xrpc/*` routes hit the Worker instead of timing out.
- [x] Verify `com.etzhayyim.apps.maps.getDashboard` returns 200 on `maps.etzhayyim.com`.
- [x] Add defensive edge degrade for dashboard collection reads and live aircraft/satellite reads when Worker-side DB access is prohibited.
- [x] Move World Monitor dashboard counts, risk snapshot, event feed, brief, alerts, and market signals to pod-side maps LangServer reads.

### P1: World Monitor Parity Surface

- [x] Expose public dashboard coverage report, risk score, trend, confidence, event feed, brief, alerts, and market signals.
- [x] Add source-backed public event feed shape with category, actor, location, severity, timestamp, and citations where available.
- [x] Split the public World Monitor facade into dashboard, events, risk snapshot, brief, and alerts XRPCs.
- [ ] Add country/admin-area selector and drill-down workflows.
- [ ] Store durable dashboard snapshots as graph records so UI can compare 1h/6h/24h/7d without recomputing edge-side.

### P2: maps LangServer / Pregel

- [x] Expose read-only XRPC bridge for World Monitor dashboard, event feed, risk snapshot, latest brief, and alerts.
- [ ] Create dedicated maps Pregel/LangGraph worker, separate from generic `lg-pregel`, for autonomous classification and routing.
- [ ] Nodes: ingest recent events, normalize taxonomy, geocode/admin-area attach, score risk, summarize, publish snapshot, route alerts.
- [ ] Outputs: durable `vertex_maps_risk_snapshot`, `vertex_maps_intel_event`, `vertex_maps_brief`, and OCEL audit events.

### P3: Deep Intelligence

- [ ] Add geopolitical feeds and controlled taxonomies.
- [ ] Add market/trade/commodity datasets and trade-route exposure scoring.
- [ ] Promote maps3d curator and actor-link workers from scaffold to production graph nodes.
- [ ] Add Playwright smoke tests for dashboard, live layers, and country risk drill-down.

## Deployment Notes

Use the repo-local CLI for the legacy `kotodama.jsonld` deploy path:

```bash
/Users/junkawasaki/github/etzhayyim-root/etzhayyim deploy
```

The `/usr/local/bin/etzhayyim` binary is a newer `etzhayyim.json`-based control-plane CLI and does not deploy this component.
