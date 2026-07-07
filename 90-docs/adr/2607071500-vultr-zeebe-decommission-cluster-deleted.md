---
id: adr-2607071500-vultr-zeebe-decommission-cluster-deleted
title: "ADR-2607071500: Zeebe decommission is moot — its VKE cluster was already deleted; prune 50-infra/vultr/zeebe/*"
status: accepted
doc_type: adr
topic: vultr-zeebe-decommission-cluster-deleted
authoritative: true
last_verified: 2026-07-07
priority: 4.5
axis: infra
weight: 0.25
priority_note: "Closeout record: the Zeebe broker's DECOMMISSION-RUNBOOK.md was never executed because the Vultr Kubernetes cluster it ran on (mitama-udf namespace, VKE 31d5f7dc-… SJC / a61d513b-… LAX) was permanently deleted 2026-06-24/25 by an unrelated murakumo-fleet wind-down in the gftdcojp org sharing that substrate. This ADR prunes the now-inert Helm chart/scripts, closes the runbook, and surveys (does not necessarily fix) app-level Zeebe references. Does NOT supersede ADR-2605191659 — the rest of 50-infra/vultr/* stays as etzhayyim.com legacy infra."
authoritative_for:
  - "50-infra/vultr/zeebe/* disposition (closed/pruned)"
  - "confirmation that the VKE cluster hosting etzhayyim's Zeebe broker no longer exists"
depends_on:
  - adr-2605191659-vultr-stays-for-etzhayyim
  - adr-2606162041-bpmn-zeebe-to-datomic-clj-engine
related:
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
supersedes: []
superseded_by: []
---

# ADR-2607071500: Zeebe decommission is moot — its VKE cluster was already deleted; prune `50-infra/vultr/zeebe/*`

**Status**: accepted
**Date**: 2026-07-07
**Deciders**: Jun Kawasaki (operator directive: "zeebe は deprecated, prune")

# Context

`50-infra/vultr/zeebe/DECOMMISSION-RUNBOOK.md` documented a graceful, operator-driven
teardown of the Camunda Zeebe 8.5.23 broker running in the `mitama-udf` namespace on a
Vultr Kubernetes Engine (VKE) cluster — stop legacy pyzeebe workers, drain in-flight
jobs, remove the `zeebe-murakumo-gateway` LoadBalancer, stop the broker, retain the PVC
one rollback cycle, then clean up. Its own "Latest preflight" note (2026-05-09 JST)
recorded the broker and gateway LB as still live and blocking on cross-cluster consumers
(`mitama-udf`, `intel`, `shinka-actors`, `yoro-actors`).

Separately, ADR-2606162041 (2026-06-16, accepted) already moved BPMN-as-actor execution
for the maps3d pipeline off Zeebe onto a pure-cljc kotoba Datom-log engine, explicitly
marking "Zeebe worker registration deprecated" — but that ADR is about the *execution
model*, not this specific broker's infrastructure lifecycle.

ADR-2605191659 (2026-05-19, active) separately recorded the operator's decision that
`50-infra/vultr/*` stays in this repo as etzhayyim.com legacy infra — no archive sweep.
That ADR predates this finding by well over a month and never anticipated the cluster
itself disappearing; it protects the *directory*, not any specific workload's uptime.

## Finding: the cluster is gone, not merely idle

This session's kubectl config on the operator's machine has two Vultr contexts:

```text
vke-31d5f7dc-bd15-4059-b9ee-9ead33cfc068   (SJC)
vke-a61d513b-f9b7-4121-abb9-b53732aa5ec4   (LAX)
```

Both cluster IDs (`31d5f7dc-…`, `a61d513b-…`) exactly match the two VKE clusters that
gftdcojp's ADR-2606120930 (`murakumo-fleet-stateless-k3s-vultr-winddown`, in the
`ai-gftd-apps-gftdcojp` repo) records as **permanently deleted**:

- **2026-06-24**: VKE cluster `31d5f7dc-bd15-4059-b9ee-9ead33cfc068` (SJC) plain-deleted
  (HTTP 204), all 5 Vultr LoadBalancers on that account deleted (HTTP 204), 5 block
  storage volumes deleted (HTTP 204). LAX (`a61d513b-…`) had been deleted earlier.
- **2026-06-25**: the 2 retained block-storage volumes were migrated off and deleted too
  — "Vultr 完全 \$0" (Vultr fully zero cost).

Independent corroboration gathered this session, without relying on the gftdcojp ADR:

- `kubectl get ns` / `kubectl get statefulset -n mitama-udf` against the configured SJC
  context fail with `dial tcp 127.0.0.1:6443: connect: connection refused`.
- That is not an ordinary network blip: `vultr-k8s.com` (the parent domain of the
  per-cluster API hostname `<uuid>.vultr-k8s.com`) itself now resolves to `127.0.0.1` —
  consistent with Vultr sinkholing DNS for a domain/cluster record that no longer has a
  live backing cluster, rather than a transient outage.
- A direct TCP probe of the `zeebe-murakumo-gateway` LoadBalancer's last-known public IP
  (`66.42.104.29`, used elsewhere in this repo as a hardcoded dispatcher origin —
  unrelated app, see Follow-ups) times out with no RST, consistent with a deleted Vultr
  LoadBalancer rather than a firewalled-but-alive host.

Both the same-org (etzhayyim/root) and cross-org (gftdcojp) evidence agree: this is not
a live cluster that merely stopped responding to one probe. It was deleted, on purpose,
by a wind-down that had nothing to do with etzhayyim or Zeebe — it just happened to share
the substrate. The graceful decommission runbook's "Do Not Start" gates and staged
steps (remove LB → stop broker → retain PVC → delete PVC) are now unexecutable and moot:
there is no LB, no StatefulSet, and no PVC left to act on.

## Contents reviewed

Every file under `50-infra/vultr/zeebe/` was read in full before removal:

- `Chart.yaml` / `values.yaml` — a thin Helm wrapper (verbatim-copied templates, no
  parameterization) around the three manifests below. Zeebe-only.
- `zeebe.yaml` — the broker `StatefulSet` + `zeebe-gateway` (ClusterIP) + `zeebe-broker`
  (headless) Services in `mitama-udf`, pinned to `camunda/zeebe:8.5.23` for licensing
  reasons (avoid Camunda 8.6+ production licensing) with a patched hazelcast exporter
  init container. Zeebe-only; a single-broker pilot deploy.
- `zeebe-simple-monitor.yaml` — the Camunda Community `zeebe-simple-monitor` UI
  Deployment/Service, wired only to the Zeebe gRPC gateway and its Hazelcast exporter.
  Zeebe-only.
- `zeebe-murakumo-gateway-lb.yaml` — checked specifically because the name suggested it
  might carry unrelated Murakumo traffic. It does not: it is a `LoadBalancer` `Service`
  selecting `app.kubernetes.io/name: zeebe`, exposing only the gRPC gateway (26500) and
  metrics (9600) ports, source-range-restricted to one Murakumo LAN egress IP. Purely a
  narrower ingress path onto the same broker — no other workload depends on it.
- `preflight-decommission.sh` / `inventory-live-dependencies.sh` — `kubectl`/`curl`
  read-only queries against the (now-nonexistent) cluster to inventory Zeebe consumers
  before a manual teardown. No side effects of their own; simply unusable now (nothing to
  query).
- `8.5-downgrade-runbook.md` — a one-off runbook for a specific 8.6→8.5.23 broker
  downgrade (2026-04-29, licensing + a hazelcast-exporter `close()` NPE incompatibility on
  8.6.x). **Kept** (see Decision) rather than removed, unlike the manifests/scripts.

None of the above manifests, scripts, or LB definitions serve anything other than this
one Zeebe broker; nothing outside Zeebe's own footprint depends on them.

## App-level Zeebe references surveyed

Three previously-flagged `60-apps/**/src/app.ts` references were read in context (not
just grepped) to determine whether Zeebe deprecation left anything **live and broken**,
versus merely stale descriptive text:

1. **`etzhayyim-project-yukkuri` (`y5kk5r1x`)** — two response fields
   (`pipeline: "zeebe:yukkuriCompose — …"` in `cmdCompose`, and
   `pipeline: { zeebe: "yukkuriCompose.bpmn", … }` in `cmdHealth`) are pure descriptive
   metadata returned to callers. The actual dispatch (`triggerBpmnPipeline`) is a plain
   HTTP POST to a dispatcher XRPC origin — it never touches Zeebe. **Determination:
   stale-but-harmless.** Relabeled `zeebe` → `bpmn` in both spots with a comment
   explaining why, since operators reading a health/status response would otherwise waste
   time chasing a broker that no longer exists.

2. **`etzhayyim-project-legal-entity` (`le9k4x2m`)** — the `/health` response's
   `businessLogic` field names
   `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py`. That
   file is real (lives in the `com-junkawasaki/kotoba` repo, mounted at `40-engine/kotoba`
   in a fully-populated checkout — not visible in this ADR's throwaway worktree, which
   never ran west/whatever vendors it in) and is an in-cluster Zeebe worker entrypoint —
   i.e. it, too, depended on the now-deleted cluster's internal `*.svc.cluster.local`
   DNS. But this app never calls that file directly: `/health` returns a static
   descriptor string, and the real request path (`proxyToDispatcher`) forwards to
   `https://dispatcher.etzhayyim.com`, decoupled from Zeebe. Per ADR-2606162041, the
   Python task *bodies* in that file are stated to be "reused as injected handlers" even
   as the Zeebe *worker/subscription* wrapper is deprecated — so declaring the whole file
   dead would overclaim. **Determination: stale-but-harmless health-check metadata; the
   file itself is out of scope (different repo/org, multi-purpose, not something this
   change should rewrite).** Annotated the descriptor to note the Zeebe broker path is
   deprecated without asserting the Python module itself is gone.

3. **`etzhayyim-project-maps` (`maps-ui-uqpel6i6`)** — two `try { const zeebe: any =
   (sdk as any).zeebe; if (zeebe && typeof zeebe.publishMessage === "function") { … } }`
   guards (train + bake gsplat jobs). Checked the actual `@etzhayyim/kotodama-host-sdk`
   contract (`host-contract.cljc` in `kotoba-lang/kotodama-host`): its operation set is
   `create-host-sdk` / `dispatch` / `cancel` / `health` only — **no `zeebe` operation has
   ever existed** on `HostSDK`. This means `(sdk as any).zeebe` has always resolved to
   `undefined`, independent of whether any Zeebe broker was reachable; the guard has
   never fired, and both call sites already fall back safely (job row is still queued and
   picked up by the dumper pod's poll loop per the existing comments).
   **Determination: permanently-unreachable dead code that was already safe** — not a
   regression from the cluster deletion, and not something Zeebe's deprecation newly
   broke. Left the logic as-is (removing it is a larger, unrelated cleanup) and added a
   comment at both sites recording this finding so a future reader doesn't waste time
   treating it as a live integration point.

None of the three needed a functional "honest failure instead of silent success" fix —
none of them hang, silently swallow a real failure into a false success, or fabricate a
working backend. All three were either non-functional descriptive strings or code that
was already a documented, safely-guarded no-op.

## Decision

1. **Close `DECOMMISSION-RUNBOOK.md`** — rewritten in place to state plainly that
   decommissioning is moot (nothing left to drain/stop/delete) and to point at this ADR
   and at gftdcojp's ADR-2606120930 for the cluster-death evidence. The file is kept (not
   deleted) as the pointer of record for this closure and to preserve its git history.

2. **Remove the inert Helm chart + scripts**: `Chart.yaml`, `values.yaml`, `zeebe.yaml`,
   `zeebe-simple-monitor.yaml`, `zeebe-murakumo-gateway-lb.yaml`,
   `preflight-decommission.sh`, `inventory-live-dependencies.sh`. All of them exist only
   to manage or query a broker/cluster that has been physically deleted; keeping them
   invites someone to `kubectl apply -f` infrastructure that cannot exist without
   redoing real design work (new cluster, new LB, new PVC) that this ADR does not
   authorize. Git history retains the last live revision of each.

3. **Keep `8.5-downgrade-runbook.md`**, annotated as historical-only. Unlike the
   manifests, it is referenced by path from two structured knowledge-inventory files
   (`00-contracts/deps.edn`, `30-graph/deps.edn`) that document the Camunda-8.6-licensing
   and hazelcast-exporter-incompatibility decision it recorded; those are not enforced by
   the `verify_deps_edn_paths.py` gate (which only checks the *root* `deps.edn`, confirmed
   by reading the script — it hardcodes `repo_root/deps.edn` regardless of which nested
   `deps.edn` triggered the lefthook glob), so removing the file would not break CI, but
   it would orphan those two knowledge entries' citations for no operational gain.

4. **Annotate, not rewrite, the three app-level Zeebe references** per the survey above —
   `yukkuri`'s two descriptor fields relabeled `zeebe` → `bpmn`; `legal-entity`'s
   `businessLogic` descriptor annotated to note the Zeebe broker path is deprecated;
   `maps-ui`'s two guarded dead-code blocks annotated with the HostSDK-contract finding.
   No behavior changes; all three verified as **not** live-dispatch-critical.

5. **This does NOT supersede ADR-2605191659.** The rest of `50-infra/vultr/*` (every
   subdirectory other than `zeebe/`) is untouched and remains etzhayyim.com legacy infra
   per that ADR's explicit "no archive sweep" decision. This ADR's scope is limited to
   the one now-provably-dead Zeebe broker and its own directory.

## Follow-ups (not addressed by this ADR — flagging for the operator)

- **`etzhayyim-project-yukkuri`'s `DISPATCHER_ORIGINS` fallback
  (`http://66.42.104.29`) is a Vultr LoadBalancer IP and is very likely dead** for the
  same reason this ADR documents (all LBs on that account were deleted 2026-06-24). This
  is unrelated to Zeebe specifically — it is yukkuri's general BPMN-compose dispatch
  path, not a Zeebe client — so it is out of scope for this change, and this ADR does not
  modify `triggerBpmnPipeline`/`DISPATCHER_ORIGINS`. If Cloudflare's `DISPATCHER_URL`
  secret already overrides this fallback in production, there is no live bug; if it does
  not, `cmdCompose` currently returns `status: "queued"` to the caller even when the
  fire-and-forget dispatch is guaranteed to fail, which would be a real, separate,
  honest-failure bug worth its own follow-up once someone can confirm the current
  deployed dispatcher address.
- Per ADR-2606162041's own follow-up list: `vertex_zeebe_*` / Zeebe-shaped runtime tables
  and any remaining `bpmn-zeebe` runtime registrations are that ADR's cleanup, not this
  one's.

# Consequences

**Positive**:

- No more dead infrastructure-as-code in the tree that looks actionable but is not; a
  future `kubectl apply -f 50-infra/vultr/zeebe/zeebe.yaml` (or Helm install of the
  chart) would have failed confusingly against a context whose API server no longer
  exists, with no explanation in-repo of why.
- `DECOMMISSION-RUNBOOK.md` no longer reads as an open, blocked runbook — closing it
  removes a stale "Do Not Start" gate that nobody can action.
- The three app-level Zeebe mentions are now accurate rather than pointing at
  infrastructure that has not existed for six weeks.

**Negative**:

- The exact broker resource-budget tuning history (JVM heap sizing, backpressure limits,
  the patched hazelcast-exporter jar) is no longer visible without checking out this ADR
  commit's parent or searching git log/blame — acceptable, since none of it is
  actionable against a cluster that no longer exists, and git history is not deleted.
- The yukkuri dispatcher-origin finding is left as an unresolved flag rather than a fix,
  because guessing a replacement address would risk fabricating a working-looking
  backend that silently routes to the wrong place — worse than leaving an honest,
  documented gap.

# Alternatives Considered

**A. Leave `50-infra/vultr/zeebe/*` in place untouched, matching ADR-2605191659's "no
archive sweep" literally.**
Rejected. ADR-2605191659 protects the *directory as a whole* from a blanket sweep of
unrelated etzhayyim.com-legacy infra; it does not obligate keeping infrastructure-as-code
for a specific broker whose only possible target (the VKE cluster) has been physically
deleted by an unrelated org's wind-down. Keeping it risks someone attempting to
`kubectl apply`/`helm install` against a dead context and wasting time debugging what
looks like a transient outage.

**B. Move `50-infra/vultr/zeebe/*` to an `_archive/` subdirectory instead of deleting.**
Rejected as unnecessary: git history already preserves every file's last live revision at
this commit's parent; an in-tree archive directory adds a second, redundant place to look
without adding information the git log doesn't already have, and ADR-2605191358's own
archive-sweep step 6 was already superseded (not resurrected) by ADR-2605191659.

**C. Also delete `8.5-downgrade-runbook.md` for consistency with the other scripts.**
Rejected: unlike the Helm chart/manifests (which describe *live infrastructure to
manage*), this file documents a *decision* (avoid Camunda 8.6+ licensing; a specific
hazelcast-exporter incompatibility) that two knowledge-inventory files
(`00-contracts/deps.edn`, `30-graph/deps.edn`) still cite by path. Keeping it, clearly
marked historical, costs nothing and avoids orphaning those citations.

**D. Rewrite the yukkuri `DISPATCHER_ORIGINS` fallback to a guessed-correct current
dispatcher address as part of this change.**
Rejected. This ADR's scope and evidence chain are about Zeebe/the deleted VKE cluster;
the dispatcher-origin question is a distinct, unconfirmed live-bug candidate that
deserves its own investigation (confirm whether `DISPATCHER_URL` is already overridden in
production) rather than a guess bundled into an unrelated infra-pruning change.

# References

- `50-infra/vultr/zeebe/DECOMMISSION-RUNBOOK.md` (closed by this ADR)
- ADR-2605191659 (`50-infra/vultr/*` retention — this ADR's scope is a narrow exception
  inside that boundary, not a supersession of it)
- ADR-2606162041 (BPMN-as-actor off Zeebe onto the kotoba Datom log — the execution-model
  side of this same deprecation)
- gftdcojp `ai-gftd-apps-gftdcojp` ADR-2606120930
  (`murakumo-fleet-stateless-k3s-vultr-winddown`) — the cross-org record of the VKE
  cluster deletion (2026-06-24/25) that makes this decommission moot
- ADR-2605081200 (SpiffWorkflow BPMN engine replacement — the ADR the original
  DECOMMISSION-RUNBOOK.md was written to close out)
