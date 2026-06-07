---
id: adr-2605151600
title: "maps CF Worker → LangServer Direct Call via CF Tunnel"
status: active
doc_type: adr
topic: infra
authoritative: true
last_verified: "2026-05-15"
supersedes: []
related:
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605111300-pds-to-pod-bun-container
---

# ADR-2605151600: maps CF Worker → LangServer Direct Call (amends ADR-2605111200)

**Date**: 2026-05-15
**Status**: Accepted
**Amends**: ADR-2605111200 (CF Worker Edge-Only; No RW Connection)
**Supersedes**: Nothing

## Context

ADR-2605111200 defines the read path as:

> CF Worker → bpmn-dispatcher → pod SELECT → JSON response

The BPMN dispatcher is a deprecated execution path (ADR-2604282300, CLAUDE.md infra layer rules). The `maps-read-langserver` K8s pod (`pymagatama.worker_api`, port 8081) already handles these NSIDs directly:

- `com.etzhayyim.apps.maps.getDashboard`
- `com.etzhayyim.apps.maps.listLiveAircraft`
- `com.etzhayyim.apps.maps.listLiveSatellites`
- `com.etzhayyim.apps.maps.getWorldMonitorDashboard`
- `com.etzhayyim.apps.maps.listIntelEvents`
- `com.etzhayyim.apps.maps.getRiskSnapshot`
- `com.etzhayyim.apps.maps.getLatestBrief`
- `com.etzhayyim.apps.maps.listIntelAlerts`

The pod was only reachable within the K8s cluster (ClusterIP Service). The CF Worker at `maps.etzhayyim.com` was calling through `dispatcher.etzhayyim.com` as a workaround.

## Decision

Remove the bpmn-dispatcher hop for the 8 maps-read NSIDs above. The CF Worker calls the `maps-read-langserver` pod directly via a Cloudflare Tunnel sidecar (CF Tunnel pattern from ADR-2605111300 / atproto-pds).

### Transport

A `cloudflare/cloudflared` sidecar container runs in the `maps-read-langserver` Deployment. The tunnel exposes the pod's port 8081 to `maps-langserver.etzhayyim.com`. The CF Worker reads `MAPS_LANGSERVER_URL` (default `https://maps-langserver.etzhayyim.com`) and calls `/xrpc/{nsid}` directly.

### Auth boundary

The pod (`pymagatama.worker_api`) has no application-layer auth. Trust boundary is the CF Tunnel: only requests that originate from CF Workers (or other CF-authenticated callers) can reach the tunnel endpoint. The data served (aircraft positions, satellite passes, world-monitor intel snapshots) is non-sensitive read-only intelligence — the same data exposed publicly via the XRPC query surface anyway.

No changes to `worker_api.py`. No CF Access Service Token required for phase-1 (can be added later as an operator step without code changes).

### Degraded mode

Both `callMapsLangserverRead` (3 NSIDs with inline fallback) and `cmdMapsPodIntelRead` (5 NSIDs) return a degraded stub when the LangServer is unreachable, preserving the CF Worker's availability invariant.

## Consequences

- **bpmn-dispatcher removed** from the maps-read hot path. The 3-step `CF Worker → dispatcher → pod` becomes 1-step `CF Worker → pod (via CF Tunnel)`.
- **DISPATCHER_INTERNAL_SECRET** binding in wrangler.jsonc remains present (used by other paths) but is no longer referenced by the maps-read functions.
- **ADR-2605111200 amendment scope**: This amendment applies only to the 8 maps-read NSIDs above. All other actors continue to follow the `CF Worker → bpmn-dispatcher → pod` path until individually migrated.

## Live State (2026-05-15)

All operator steps completed in the same session:

| Resource | ID / Value |
|---|---|
| CF Tunnel | `maps-langserver` — ID `a84a1d0b-7dfc-4994-be0b-a20725721cc6` |
| Tunnel status | healthy, 4 connections (lax01 × 2, lax08, lax10) |
| DNS | `maps-langserver.etzhayyim.com` CNAME → `a84a1d0b…cfargotunnel.com` (proxied) |
| Tunnel ingress | `maps-langserver.etzhayyim.com` → `http://localhost:8081` |
| K8s secret | `maps-langserver-tunnel-token` in namespace `maps` |
| K8s secret | `mitama-udf-pool-rw` copied to namespace `maps` (KOTOBA_URL) |
| Deployment | `maps-read-langserver` — 2/2 Running (worker-api + cloudflared) |
| Readyz | `{"ok":true,"component":"maps-read-langserver","ready":true}` |
