# Zeebe Decommission Runbook — CLOSED (moot, not executed)

**Status (2026-07-07)**: This runbook is retired. Decommissioning the Zeebe
broker described below never happened through the graceful procedure this
file used to document — instead, the entire Vultr Kubernetes cluster the
broker ran on was **permanently deleted** on 2026-06-24/25 as part of an
unrelated wind-down of gftdcojp's murakumo-fleet workload (VKE clusters
`31d5f7dc-…` SJC and `a61d513b-…` LAX, both shared substrate — see
ADR-2607071500 for the full evidence chain). There is nothing left to drain,
scale down, or delete: the compute, the StatefulSet, the PVC, and the
LoadBalancer are all gone along with the cluster.

This file (and the Helm chart / scripts it referenced —
`Chart.yaml`, `values.yaml`, `zeebe.yaml`, `zeebe-simple-monitor.yaml`,
`zeebe-murakumo-gateway-lb.yaml`, `preflight-decommission.sh`,
`inventory-live-dependencies.sh`) is kept only as a pointer to the git
history of that infrastructure; the manifests/scripts themselves were removed
in the same change that closed this runbook (ADR-2607071500). See git log on
this path for the last live revision if you need the exact broker
configuration.

This does **not** touch anything else under `50-infra/vultr/*` — the rest of
that directory remains etzhayyim.com legacy infra per ADR-2605191659 and is
unaffected by this closure.

## What actually happened (superseding the plan below)

The **Do Not Start** / **Step 1–5** plan in the original version of this
runbook (preserved in git history) was written assuming an operator-driven,
gradual broker teardown on a live cluster: stop workers, drain in-flight
jobs, remove the external LoadBalancer, stop the broker, keep the PVC for one
rollback cycle, then clean up. None of those steps were ever run — the
cluster disappeared first. Concretely:

- The **Do Not Start** gates (Spiff `/readyz`, `lawfirm-spiff-worker`
  readiness, `mv_spiff_ready_jobs` drain, cross-cluster
  `yoro-actor-zeebe-worker` dependency) are unverifiable now — the cluster
  they'd be checked against does not exist, so there is nothing to gate.
- **Step 3** (remove the `zeebe-murakumo-gateway` LoadBalancer) and **Step 4**
  (stop the broker StatefulSet) are moot: Vultr deleted all LoadBalancers and
  block storage on that cluster along with it (gftdcojp ADR-2606120930,
  2026-06-24, HTTP 204 on all of them).
- **Rollback** and **Final Cleanup** (retain the PVC one production cycle,
  then delete it) are moot for the same reason — the PVC's backing Vultr
  block-storage volume no longer exists to retain or delete.

## Follow-up already covered elsewhere

ADR-2606162041 (accepted, 2026-06-16) had already moved BPMN-as-actor
execution for the maps3d pipeline off Zeebe onto a pure-cljc kotoba Datom-log
engine, independent of this cluster-death finding, and explicitly marks
"Zeebe worker registration deprecated." That migration's own follow-ups
(retiring `vertex_zeebe_*` runtime tables, etc.) are tracked there, not here.

Any app-level code (`60-apps/**/src/app.ts`) that still names Zeebe in
descriptive strings or defensively-guarded (never-populated) SDK hooks was
surveyed and annotated in the same change that closed this runbook — see
ADR-2607071500 for the per-file disposition. None of it depended on this
broker being reachable at runtime.
