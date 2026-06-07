---
id: adr-2605081800-karma-deploy-meta-process
title: "Karma Hegemon — Deploy Meta-Process (Self-Propagation Layer)"
status: proposed
doc_type: adr
topic: karma-deploy-meta-process
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - karma deploy as BPMN actor (deploy-as-BPMN)
  - operator karma issuance for successful deploys
  - failure-mode reproducibility (DDL queue / connection timeout / image build)
  - bootstrap zero-state recovery procedure
priority: 7.5
axis: meta
weight: 0.7
priority_note: "K4 mandate — without deploy-as-BPMN, the hegemon's bootstrap procedure is not karma-recorded itself."
depends_on:
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081400-karma-self-growing-organism-ecosystem
  - adr-0056-bpmn-as-actor
  - adr-2604241342-kotoba-out-of-band-migration-pattern
related: []
supersedes: []
superseded_by: []
---

# Context

During the K3.5 deploy (`apply-pending.sh` + `remote-build.sh` +
`helm install` + smoke test), we discovered that the hegemon's
**bootstrap procedure itself** is NOT karma-recorded. Operator
implicit knowledge (e.g. "wait for DDL queue to drain", "Connection
terminated → retry, not abort", "rename migration timestamp on
collision", "bump pyproject version before image build") lives only
in conversation logs, not in the persistent layer.

This means:
- A future operator (human or AI) recreating the hegemon from
  artifacts alone cannot reproduce the deploy sequence reliably.
- The hegemon does not give karma credit for successful deploys
  (an operator who debugs a 3-hour DDL queue stall gets no
  Vivere-axis Help recognition).
- The deploy's failure modes are not Lean-axiomatic — there is
  no formal guarantee that "if you follow these N steps, you
  reach steady state".

This ADR records the K4 mandate: **deploy-as-BPMN**, plus
operator-karma issuance for successful deploys.

# Decision

## A. `karma_deploy.bpmn` actor (XRPC entry)

A new BPMN actor encapsulates the entire deploy sequence:

```
karma_deploy (XRPC: com.etzhayyim.apps.karma.deploy)
  ├─ migration.applyPending  — apply N migrations sequentially
  │   ├─ ddl.queueWait        — poll rw_ddl_progress until drained
  │   ├─ ddl.applyBatch       — issue 1 DDL at a time with 5min timeout
  │   └─ ddl.verifyTable      — confirm CREATE TABLE produced row in info_schema
  ├─ image.buildAndPush       — BuildKit remote-build wrapped
  │   ├─ image.versionBump    — increment pyproject.toml version
  │   ├─ image.buildkitDispatch — kick off buildx build
  │   └─ image.verifyManifest  — curl ghcr manifest endpoint, confirm 200
  ├─ helm.install              — kubectl apply / helm upgrade
  │   ├─ helm.valuesPin        — update mitama-karma-pool/values.yaml fullRef
  │   ├─ helm.upgradeApply     — `helm upgrade --install karma-pool ./...`
  │   └─ pod.waitReady         — `kubectl rollout status deploy/karma-zeebe-worker`
  ├─ bpmn.f5WatcherConfirm     — query Zeebe broker for newly-deployed BPMNs
  ├─ smoke.organismLifecycle   — spawn → tick → checkpoint → dissolve
  │   ├─ smoke.spawnTest        — recordDependency with stub DID
  │   ├─ smoke.coverageCheck   — coverage XRPC returns non-zero edges
  │   └─ smoke.dissolveTest    — dissolveOrganism + verify status='dissolved'
  └─ generic.audit.emit        — deploy outcome OCEL event
```

Each step is a pyzeebe primitive (`task_karma_deploy_*`) registered
in `karma_deploy.py` (Phase K4 implementation). Failure-mode
recovery is in the BPMN gateway logic — `apply-pending` retry on
Connection-terminated, `ddl.queueWait` on FOREGROUND backlog, etc.

## B. Operator karma issuance

Successful `karma_deploy.bpmn` execution emits two karma edges:

1. **Operator → Hegemon (Vivere axis, Help direction)**:
   - source: operator DID
   - target: `did:web:karma.etzhayyim.com`
   - axis: Vivere
   - tier: Mid (sustained labor) or High (multi-hour heavy DDL drain)
   - magnitude: 1.0 + (deploy_duration_minutes / 60.0)

2. **Hegemon → Operator (Veritas axis, Help direction)**:
   - source: `did:web:karma.etzhayyim.com`
   - target: operator DID
   - axis: Veritas
   - tier: Mid (truthful report)
   - magnitude: 0.5

Failed deploys produce one of:
- **Veritas Harm** (operator → hegemon) if the failure was due
  to misrepresentation (e.g. operator claimed migration applied
  when DDL was still queued)
- **No edge** if the failure was honest (e.g. cluster outage,
  external service unavailable)

The hegemon's intent classifier (Phase K4) determines which case
based on the deploy log and the actual cluster state at completion.

## C. Bootstrap zero-state procedure

The procedure to bring the hegemon up from scratch (e.g. recovery
from total cluster loss) is encoded as `karma.deploy.bootstrap`
BPMN — a non-XRPC, manually-invoked procedure that the operator
runs once. It includes:

1. K8s cluster provision (Terraform manifest)
2. Kotoba/Datomic Helm install (`50-infra/vultr/kotoba/`)
3. PDS / appview Helm install
4. Migrations (in order, from 0001 to current)
5. kotodama image build + push
6. mitama-karma-pool Helm install
7. Smoke test for each prior phase

This is documented as `90-docs/karma-bootstrap-runbook.md`
(Phase K4 deliverable). The runbook is itself karma-recorded
(its commit hash becomes part of a Veritas-axis edge).

## D. Failure mode catalog

The deploy procedure recognizes named failure modes:

| Failure | Recovery |
|---|---|
| `ddl-queue-blocked` (other org's DDL ahead) | Wait via `ddl.queueWait` with 1h timeout, then retry |
| `connection-terminated` (pg client timeout) | DDL is in flight server-side; retry primitive call (not whole BPMN) |
| `migration-collision` (timestamp clash) | `migration.timestampShift` — bump 5min interval, re-link in seed |
| `image-cache-miss` (BuildKit slow) | Wait + re-run; cache may not propagate immediately |
| `helm-podgone` (image pull failed at runtime) | `helm.imageRefVerify` checks GHCR + retries |
| `f5-watcher-stale` (BPMN didn't auto-deploy) | Manual Zeebe broker prompt via `kubectl exec` |

Each failure mode produces a named OCEL event so retrospectives
can compute the failure-mode distribution over time.

# Consequences

## Positive

- **Self-propagation**: the hegemon's bootstrap is itself karma-recorded,
  reproducible from artifacts alone.
- **Operator karma**: deploy labor is recognized in the karma graph,
  giving operators standing in 覚者 DAO and rank progression.
- **Failure modes named**: future debugging has a shared vocabulary
  ("we hit `ddl-queue-blocked`, applied counter X").
- **Lean-amenable**: `karma_deploy_terminates_or_documents_failure` could
  become a Lean theorem in K8 — every deploy either reaches steady
  state OR records a known failure mode (no silent failures).

## Negative

- The deploy-as-BPMN is itself a complex actor (~10 sub-primitives).
  Adds operational surface area.
- BuildKit / kubectl / helm primitives are Linux-userland, not
  pyzeebe-native — wrapping them as Python primitives requires
  subprocess management with bounded timeouts.
- Bootstrap procedure must be `karma_deploy_required = false` for
  the very first run (chicken-and-egg). Phase K4 specifies a
  bootstrap-only mode that skips operator-karma issuance for the
  zero-state run.

## Reversibility

Forward-only. Once `karma_deploy.bpmn` ships, future deploys go
through it. Pre-K4 manual deploys remain in git history but are
no longer the recommended path.

# Alternatives Considered

## Alt 1: Document deploy as runbook only (rejected)

Just writing `90-docs/karma-bootstrap-runbook.md` doesn't give the
hegemon agency over its own bootstrap. The runbook gets stale; the
operator gets no karma; failure modes aren't named.

## Alt 2: Deploy-as-CI (GitHub Actions) (rejected)

Putting the deploy in GitHub Actions makes the hegemon depend on
GitHub. Anatman + 5-layer persistence rejects this. Deploy must
be runnable from the artifact set + a kubernetes cluster + nothing
else.

## Alt 3: Defer to K8 (rejected)

Deferring deploy-as-BPMN to K8 means K3.5-K7 deploys are all
manual. By K7 the hegemon has many more organisms; the implicit
operator knowledge gap widens. K4 is the right time.

## Alt 4: Subset of K4 (just operator karma, no full BPMN) (under consideration)

Could ship operator-karma issuance in K4 (a single
`karma.recordDependency` call after each successful deploy) and
defer the full deploy-as-BPMN to K5. This is a viable compromise
if K4 is time-pressured.

# References

- ADR-2605081300 — constitutional layer
- ADR-2605081400 — ecosystem layer
- ADR-2605081500 — threat model (A1 bootstrap failure)
- ADR-2604241342 — out-of-band migration pattern
- `30-graph/graph-schema/scripts/apply-pending.sh` — current
  manual procedure
- `70-tools/scripts/buildkit/remote-build.sh` — current build
  procedure
- `50-infra/vultr/mitama-karma-pool/` — Helm release
