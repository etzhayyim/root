---
id: adr-2605141930-world-monitor-resident-intelligence-graph
title: "World Monitor-style resident intelligence graph facade for maps.etzhayyim.com"
status: active
doc_type: adr
topic: maps-world-monitor-resident-intelligence
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - maps-world-monitor-product-coverage
  - maps-resident-intelligence-read-facade
  - maps-pod-langserver-xrpc-routing
  - maps-dashboard-coverage-reporting
related:
  - adr-2604282300
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605071700-graph-sos-intel-actor
supersedes: []
superseded_by: []
amends:
  - adr-2604282300
---

# Context

`maps.etzhayyim.com` needs a World Monitor-style resident intelligence surface:
risk snapshot, source-backed event feed, latest brief, alert stream, market
signals, and a dashboard-level coverage report. The edge Worker must remain a
thin facade under ADR-2604282300 and ADR-2605111200; it must not own domain DB
reads or resident intelligence logic.

The deployed system now has these public XRPCs on `maps.etzhayyim.com`:

- `com.etzhayyim.apps.maps.getWorldMonitorDashboard`
- `com.etzhayyim.apps.maps.listIntelEvents`
- `com.etzhayyim.apps.maps.getRiskSnapshot`
- `com.etzhayyim.apps.maps.getLatestBrief`
- `com.etzhayyim.apps.maps.listIntelAlerts`

The read implementation runs pod-side through `maps-read-langserver` and is
proxied via `bpmn-dispatcher` / Cloudflare tunnel. The dashboard exposes
`coverage.productCoveragePct = 100` when all seven product capabilities are
present. The implementation coverage remains intentionally separate at 55%;
it reflects depth of autonomous graph processing, not product surface parity.

# Decision

Use a pod-side, read-only LangServer facade as the production boundary for the
World Monitor-style resident intelligence graph.

The facade is accepted as product-complete for the current parity target when
the public dashboard response satisfies all of the following:

- `source = "pod-langserver"`
- `degraded = null`
- `error = null`
- `coverage.coveredCapabilities = 7`
- `coverage.totalCapabilities = 7`
- `coverage.productCoveragePct = 100`
- `coverage.gaps = []`
- `coverage.ddlFreeFacade = true`
- `counts.marketSignals > 0`

The resident graph is represented by live read models and existing graph tables
rather than new DDL in this phase. No RisingWave DDL is required for the
accepted facade. Future Pregel/LangGraph workers may deepen scoring,
classification, alert routing, and snapshot persistence, but they must preserve
the same XRPC contract.

Operationally:

- Cloudflare Worker registers and forwards the five maps World Monitor XRPCs.
- `bpmn-dispatcher` allowlists maps LangServer XRPCs and caches dashboard reads
  for one hour to keep public requests below the Worker XRPC timeout.
- `maps-read-langserver` remains the read authority for the dashboard payload.
- K8s resources must stay in `mitama-udf`; no default namespace resources.

# Consequences

Product coverage for the World Monitor-style surface is 100% on the deployed
public route. Implementation coverage is 55% because deeper resident graph
automation still has known follow-up work:

- autonomous event classification and actor attribution;
- durable snapshot comparison windows;
- market/trade/commodity scoring beyond demand-signal panels;
- richer source citation and drill-down workflows;
- Playwright UI smoke coverage for the World Monitor dashboard.

This split prevents false precision: the public product surface is complete for
the requested coverage gate, while the resident intelligence engine still has a
clear maturation path.

# Verification

Verified on 2026-05-14 against `https://maps.etzhayyim.com`:

```bash
curl -sS --max-time 70 \
  -X POST https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.getWorldMonitorDashboard \
  -H 'content-type: application/json' \
  --data '{"limit":2}'
```

Observed:

- HTTP 200
- `source: pod-langserver`
- `coverage.productCoveragePct: 100`
- `coverage.coveredCapabilities: 7`
- `coverage.totalCapabilities: 7`
- `coverage.gaps: []`
- `counts.marketSignals: 903`

Also verified the four supporting XRPCs returned HTTP 200 from
`source: pod-langserver`: `listIntelEvents`, `getRiskSnapshot`,
`getLatestBrief`, and `listIntelAlerts`.

# References

- `90-docs/maps-worldmonitor-parity.md`
- `20-actors/magatama/py/src/pymagatama/worker_api.py`
- `20-actors/magatama/py/src/pymagatama/dispatcher_main.py`
- `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/src/app.ts`
- `50-infra/vultr/mitama-udf-pool/values.yaml`
