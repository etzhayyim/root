---
id: adr-2605212300-etzhayyim-organism-phase-4-multi-region-replication
title: "ADR-2605212300: etzhayyim organism Phase 4 — multi-region replication on AT MST + IPFS + Base L2"
status: proposed
doc_type: adr
topic: etzhayyim-organism-phase-4-multi-region
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: governance
weight: 0.80
priority_note: "FUTURE WORK — Phase 4 follows Phase 3 (ADR-2605212200) completion. Architects the replication of organism state across geographic regions so the organism can survive a single-cluster outage. Blocked on Phase 3 30d clean run + operator capacity for multi-cluster setup."
authoritative_for:
  - multi-region replication strategy for organism state
  - cross-region read/write semantics (AT MST commit ordering)
  - region failover runbook + RTO / RPO targets
  - did:web routing across regions
depends_on:
  - adr-2605211200-etzhayyim-active-inference-organism-on-murakumo
  - adr-2605212200-etzhayyim-organism-phase-3-vendor-decouple
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-0019-atproto-native-identifier-topology
supersedes: []
superseded_by: []
---

# ADR-2605212300: Phase 4 multi-region organism replication

**Status**: proposed
**Date**: 2026-05-21
**Blocked on**: ADR-2605212200 Phase 3 complete (≥30 days clean post-Stage E)
**Deciders**: Jun Kawasaki

# Context

After Phase 3 (ADR-2605212200) completes:
- Organism state lives canonically on AT MST + IPFS + per-pod SQLite
  hot-cache.
- The 12 + 4 lexicon NSIDs are in the `ai.etzhayyim.*` namespace.
- `vertex_agent_*` tables are dropped from RW.
- The single Murakumo Mac mini fleet (1 region: Japan / DC TBD) hosts
  the entire organism deployment.

That topology has a **single region failure mode**: if the Murakumo
fleet's site loses power, network, or hardware, the organism stops.
The AT MST and IPFS canonical records survive (third-party PDS and
IPFS pinning provide replication), but the organism's compute,
SQLite hot-cache, and dispatch routing all live in one place.

Phase 4 architects the multi-region replication needed to bound the
worst-case organism downtime.

# Decision

Adopt a 2-region active-passive topology backed by AT MST + IPFS
canonical state. **No active-active in Phase 4** because the
active-inference loop has serializability assumptions (one BeliefState
update at a time per agent_did) that active-active would have to
relax.

## Topology

```
                ┌───────────────────────┐
                │ AT MST (any PDS)      │ ←─ canonical organism state
                │ IPFS pinning network  │    (federated, not regional)
                │ Base L2               │
                └───────────────────────┘
                          ↕ ↕
       ┌──────────────────┴ ┴──────────────────┐
       │ Region JP (primary, Murakumo)         │ Region EU (warm standby, TBD)
       │ - lg-organism pod (active)            │ - lg-organism pod (paused, env: PASSIVE=1)
       │ - SQLite hot-cache                    │ - SQLite hot-cache (replays AT MST on switchover)
       │ - CF Worker dispatch (active route)   │ - CF Worker dispatch (registered, weight=0)
       │ - Path 1 LLM (murakumo fleet)         │ - Path 1 LLM (regional fleet, paused)
       └───────────────────────────────────────┴
                          ↕
                ┌───────────────────────┐
                │ Path 2 LLM (RunPod)   │ ←─ regionless, vendor capability
                └───────────────────────┘
```

## Per-region components

Each region runs:
- 1 `lg-organism` Deployment + `langgraph-server` Service
- 1 SQLite hot-cache PVC per actor (7 actors × 2Gi = 14Gi per region)
- 1 `consent-capability-handler` CF Worker (uses regional D1 instance
  for revocation list; multi-region D1 replication is via Cloudflare's
  built-in replicas, not part of this ADR)
- 1 regional LLM fleet for Path 1 (etzhayyim hardware; in standby
  region, lower spec OK — only spins up on failover)
- Standard observability stack (Prometheus + Grafana + AlertManager)
  scraping that region's pods

## Canonical state replication

AT MST + IPFS provide federation natively:
- Every `ai.etzhayyim.agent.*` record is published to a PDS that
  participates in the AT relay. Other PDS instances pull via
  `com.atproto.sync.subscribeRepos`.
- Large blobs (model snapshots, belief tensor archives) live on IPFS
  pinned by ≥2 regions.
- Base L2 settlement receipts are inherently global (one chain).

Standby region replicas:
- Run a `com.atproto.sync.subscribeRepos` consumer that writes incoming
  records to local SQLite hot-cache (mirror of primary).
- Lag: typically < 5 seconds on healthy networks; bounded by AT relay
  propagation.

## Switchover (active → passive promotion)

Trigger: any of
1. Operator command (planned maintenance)
2. Primary region health check fails for ≥5 minutes
3. Primary region's `/_worker/metrics` endpoint unreachable from
   monitoring vantage point

Runbook:
1. Pause CronJobs on primary: `kubectl --context <primary> -n
   organism-langgraph patch cronjob ki-cycle saikin-cycle koke-cycle
   --type merge -p '{"spec":{"suspend":true}}'`
2. Wait 60s for any in-flight LangGraph runs to complete or timeout.
3. Promote standby: `kubectl --context <standby> -n organism-langgraph
   patch deployment lg-organism --type merge -p
   '{"spec":{"template":{"spec":{"containers":[{"name":"server","env":[{"name":"PASSIVE","value":""}]}]}}}}'`
   (clear PASSIVE env, restart pods.)
4. Flip CF Worker route weight: route 100% of organism XRPC traffic to
   the standby region's CF Worker route.
5. Un-suspend CronJobs on the (now-promoted) region: same patch as
   step 1 with `suspend: false`.

RTO target: ≤ 10 minutes. RPO target: ≤ 5 seconds (bounded by AT relay
propagation lag).

## Did:web routing

did:web records for organism actors (e.g.
`did:web:etzhayyim-kobo.etzhayyim.com`) point at static well-known JSON
served from CF Worker edge. Multi-region failover is transparent at the
DID level because CF Workers are globally edge-resolved.

## What this ADR does NOT decide

- Standby region hardware procurement timeline
- Standby region location (EU vs US vs APAC alternate)
- Cross-region cost amortization model
- Whether Phase 5 (active-active) is worth pursuing

# Consequences

## Positive

- Bounded RTO/RPO for single-region failure scenarios
- Operator can run regional maintenance (Mac mini fleet hardware
  refresh, etc.) without organism downtime
- Standby region's idle compute can be used for offline workloads
  (model training, batch evaluation) until failover

## Negative / risks

- 2x hardware cost (mitigated by lower-spec standby + idle workload
  use)
- Switchover runbook complexity (4 manual steps, error-prone under
  pressure)
- Cross-region AT MST replay can lag during high write rates (mitigated
  by partition pre-warm + SQLite snapshot ship at promotion time)
- Active-inference loop serializability: if both regions un-pause
  simultaneously due to a split-brain misdetection, there could be
  duplicate BeliefState writes for the same agent_did. Mitigation:
  enforce via PDS commit ordering (each record has a stable
  vertex_id; PDS rejects duplicates) — but the cycle decisions may
  still diverge for ~5s.
- Phase 4 does NOT eliminate Path 2 LLM single-vendor dependency
  (RunPod). A separate Phase 4.X ADR can address Path 2 multi-vendor
  fallback.

## Re-judgment triggers

- Phase 3 SLO alerts fire post-cutover → defer Phase 4 until Phase 3
  stabilizes
- Murakumo Mac mini fleet hardware EOL forces re-architecture →
  re-judge primary region location
- IPFS pinning service goes offline for ≥1 hour during Phase 4 → may
  need to add region-local IPFS pinning operators

# Verification

When Phase 4 is fully implemented:
1. Synthetic primary outage: kill primary region's lg-organism pod;
   measure recovery via standby promotion; should be ≤10 minutes
2. Lag measurement: write a record on primary, time arrival on standby;
   should be ≤5 seconds p99 over 24h
3. Switchover dry-run: execute the 4-step runbook on staging clusters
   once per quarter
4. RW-free invariant: standby region's SQLite hot-cache should not
   require any vendor RW connection (verify with `lsof` or equivalent
   on the standby pod during normal operation)

# Phase 5 boundary

Phase 5 (not in this ADR's scope) would add:
- Active-active replication with conflict resolution (e.g. CRDT-based
  BeliefState merge)
- Geographic LLM routing (Path 1 calls go to nearest etzhayyim fleet)
- Multi-region IPFS pinning under explicit etzhayyim governance

Phase 5 is gated on Phase 4 stable production operation ≥6 months.

# References

- ADR-2605211200 — Phase 1 + 2 (parent of this work)
- ADR-2605212200 — Phase 3 vendor decouple plan (immediate predecessor)
- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605172100 — payments on-chain only (Base L2 receipts are global)
- ADR-0019 — atproto-native identifier topology (did:web routing model)
