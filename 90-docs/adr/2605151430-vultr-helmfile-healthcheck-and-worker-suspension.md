---
id: adr-2605151430
title: "Vultr Helmfile Healthcheck and Worker Suspension"
status: active
doc_type: adr
topic: infra-ops
authoritative: true
last_verified: "2026-05-15"
authoritative_for:
  - vultr-vke-helmfile-healthcheck
  - mitama-udf-pool-worker-suspension
  - helmfile-owned-raw-resource-adoption
related:
  - buildx-remote-build-only
  - adr-2605131900-organism-mcp-xrpc-proxy-phase-h
supersedes: []
superseded_by: []
---

# ADR-2605151430: Vultr Helmfile Healthcheck and Worker Suspension

**Date**: 2026-05-15
**Status**: Accepted
**Deciders**: Jun Kawasaki

## Context

The Vultr VKE cluster accumulated many live resources that were not represented
in Helmfile-managed manifests. That made `kubectl` drift difficult to audit and
allowed broken resident jobs to reappear outside the normal release surface.

During the May 15 cleanup, the operational target was tightened:

- Helmfile is the source of truth for application and ops resources.
- Unmanaged application resources must stay at zero.
- Non-deployed Helm releases, unschedulable pods, bad pod states, and failed
  jobs must be surfaced as a cluster signal.
- Known-broken resident loops should be suspended declaratively until their
  image/module or database timeout blockers are fixed.

## Decision

Adopt the remaining application resources into Helmfile/raw Helm charts and add
a resident healthcheck loop in `ops`.

The healthcheck is implemented as:

- Script: `50-infra/vultr/ops/helmfile-healthcheck.sh`
- CronJob: `50-infra/vultr/ops-cron-raw/templates/helmfile-healthcheck-cronjob.yaml`
- Status signal: ConfigMap `ops/helmfile-healthcheck-status`

The signal is JSON in `data.lastStatus`:

```json
{
  "state": "ok",
  "checkedAt": "2026-05-15T05:08:00Z",
  "counts": {
    "unmanagedAppResources": 0,
    "unschedulablePendingPods": 0,
    "badPodStates": 0,
    "failedJobs": 0
  }
}
```

The following loops are intentionally suspended until their underlying blockers
are resolved:

- `akuma-probe/scope-egress-reconciler`: image/module missing
  `pymagatama.akuma.scope_egress_reconciler`.
- `mitama-udf/domain-expansion-ticker`: Kotoba/Datomic gap query timeout.
- `mitama-udf/maps-coverage-ticker`: Kotoba/Datomic batch connection resets in
  `advance_coverage`.
- `mitama-udf/legal-entity-langserver-worker`: pinned legal-entity profile
  image does not include `pymagatama.worker_api`; the legal-entity surface is
  served by the LangGraph pod proxy instead.

The `mitama-udf-pool` chart also standardizes the resident worker values key on
`.Values.zeebeWorker`. Templates must not reference the obsolete
`.Values.langserverWorker` key.

## Verification

The closing verification for this phase is:

```sh
cd 50-infra/vultr
./ops/helmfile-healthcheck.sh
helm list -A | awk 'NR==1 || $8 != "deployed" {print}'
kubectl get pods -A --no-headers | awk '$4 ~ /CrashLoopBackOff|Error|ImagePullBackOff|ErrImagePull|CreateContainerConfigError/ {print}'
kubectl get jobs -A -o json | jq '[.items[] | select((.status.failed // 0) > 0)] | length'
kubectl -n ops get configmap helmfile-healthcheck-status -o json | jq -r '.data.lastStatus | fromjson'
```

Verified on 2026-05-15:

- unmanaged application resources: `0`
- non-deployed Helm releases: `0`
- unschedulable pending pods: `0`
- bad pod states: `0`
- failed jobs: `0`
- `mitama-udf-pool` Helm release: revision `481`, status `deployed`

## Consequences

Positive:

- Cluster drift has an explicit, machine-readable signal.
- Failed resident loops are now declarative suspensions instead of recurring
  CrashLoop/failed Job noise.
- Future phases can treat `ops/helmfile-healthcheck-status` as the first
  cluster readiness gate before deeper app-level probes.

Negative:

- Suspended loops are not producing domain expansion, maps coverage, or akuma
  scope reconciliation updates until their blockers are fixed.
- Raw Helm adoption still preserves many JSON-derived manifests; later cleanup
  can normalize them into first-class chart templates.

## Rollback

Rollback is a Helmfile change, not a direct `kubectl apply`:

1. Re-enable the relevant `enabled` flag or CronJob `suspend: false` in the
   owning chart.
2. Run `cd 50-infra/vultr && helmfile -l name=<release> sync --skip-deps`.
3. Re-run `./ops/helmfile-healthcheck.sh`.
