# Medical Coverage MCP Control Plane Design

**Status**: proposed for implementation
**Date**: 2026-04-25
**Scope**: medical coverage ingest for PubMed, ClinicalTrials.gov, DSM public
taxonomy rows, and healthcare facility datasets.

## Decision

Expose medical ingest as an **MCP control plane**, not as an MCP-owned ingest
runtime.

MCP tools create, inspect, pause, resume, and diagnose Kubernetes Jobs/CronJobs
and read coverage from Kotoba/Datomic. The actual ingest work remains in Kubernetes
Jobs/CronJobs today and can later move behind Zeebe without changing agent-facing
tool names.

```text
Agent / app
  -> MCP tools/call
    -> medical-coverage-mcp
      -> Kubernetes API: CronJob/Job/log/status/patch
      -> Kotoba/Datomic: coverage, target config, cursor/run records
        -> medical-coverage-ingester Job
          -> PubMed / ClinicalTrials.gov / facility CSV
          -> vertex_repo_record
          -> mv_world_collection_coverage_live
```

## Non-Goals

- Do not fetch PubMed or ClinicalTrials.gov pages inside the MCP request.
- Do not run long polling loops inside the MCP server.
- Do not let MCP request timeout decide ingest success.
- Do not store source API cursors in MCP process memory.
- Do not expose cluster-admin Kubernetes credentials to the MCP server.

## Runtime Placement

Initial runtime:

- Namespace: `kotoba`
- Existing CronJob: `medical-coverage-ingester`
- Existing image: `ghcr.io/etzhayyim/medical-coverage-ingester:latest`
- Existing DB sink: `vertex_repo_record`
- Existing coverage view: `mv_world_collection_coverage_live`

MCP server runtime:

- Deployment: `medical-coverage-mcp`
- Service: `medical-coverage-mcp`
- Optional public facade: Cloudflare Worker or atproto MCP registry endpoint
- ServiceAccount: `medical-coverage-mcp`
- RBAC scope: only `kotoba` namespace, only this CronJob/Job label set

## Tool Surface

Tool names use stable names independent of the current backend.

### `medical.coverage.get`

Read coverage for medical collections.

Input:

```json
{
  "targets": ["pubmed", "clinical_trials", "dsm", "facilities"],
  "includeRows": true
}
```

Output:

```json
{
  "ok": true,
  "coverage": [
    {
      "target": "pubmed",
      "domain": "gakujutsu_ronbun",
      "collection": "com.etzhayyim.apps.iryo.pubmedPaper",
      "recordCount": 500,
      "worldTotal": 200000000,
      "coverageRate": 0.0000025
    }
  ]
}
```

Implementation:

- `SELECT domain, collection, record_count, collected, world_total, coverage_rate`
- from `mv_world_collection_coverage_live`
- filtered to the four medical collections.

### `medical.ingest.trigger`

Create a one-shot Kubernetes Job from the CronJob.

Input:

```json
{
  "targets": ["pubmed", "dsm"],
  "maxRecords": 5000,
  "pubmedTerm": "medicine[MeSH Terms] OR clinical medicine",
  "requestedBy": "mcp",
  "dryRun": false
}
```

Output:

```json
{
  "ok": true,
  "jobName": "medical-coverage-ingester-manual-20260425-081500",
  "namespace": "kotoba",
  "statusUrlHint": "medical.ingest.status"
}
```

Implementation:

- Create `batch/v1 Job` from the stored CronJob template.
- Add labels:
  - `app.kubernetes.io/name=medical-coverage-ingester`
  - `ai.etzhayyim.com/requested-by=mcp`
  - `ai.etzhayyim.com/ingest-targets=<csv>`
- Override env only for approved variables:
  - `TARGETS`
  - `MAX_RECORDS_PER_RUN`
  - `PUBMED_TERM`
- Return immediately after Job creation.

### `medical.ingest.status`

Read Job, Pod, and last termination state.

Input:

```json
{
  "jobName": "medical-coverage-ingester-manual-20260425-081500"
}
```

Output:

```json
{
  "ok": true,
  "job": {
    "name": "medical-coverage-ingester-manual-20260425-081500",
    "active": 0,
    "succeeded": 1,
    "failed": 0,
    "startTime": "2026-04-25T08:15:00Z",
    "completionTime": "2026-04-25T08:15:54Z"
  },
  "pods": [
    {
      "name": "medical-coverage-ingester-manual-...",
      "phase": "Succeeded",
      "node": "kotoba-pool-32gb-...",
      "reason": null
    }
  ]
}
```

### `medical.ingest.logs`

Return bounded logs for a Job.

Input:

```json
{
  "jobName": "medical-coverage-ingester-manual-20260425-081500",
  "tailLines": 200
}
```

Rules:

- Default `tailLines=200`, maximum `1000`.
- Do not stream indefinitely.
- Redact values matching known secret env names.

### `medical.ingest.pause`

Suspend the CronJob.

Input:

```json
{
  "reason": "B2 maintenance window",
  "requestedBy": "mcp"
}
```

Implementation:

- Patch `CronJob.spec.suspend=true`.
- Record an annotation:
  - `ai.etzhayyim.com/paused-by`
  - `ai.etzhayyim.com/paused-at`
  - `ai.etzhayyim.com/pause-reason`

### `medical.ingest.resume`

Unsuspend the CronJob.

Implementation:

- Patch `CronJob.spec.suspend=false`.
- Record matching resume annotations.

### `medical.ingest.configure`

Update approved non-secret runtime config.

Input:

```json
{
  "facilityCsvUrl": "https://example.org/facilities.csv",
  "facilitySourceLabel": "mhlw-open-data-2026-04",
  "maxRecordsPerRun": 5000
}
```

Rules:

- Admin-only.
- Only writes approved keys.
- For secret values, prefer External Secrets or SOPS-backed Kubernetes Secret
  reconciliation. Direct Secret mutation is allowed only as a break-glass path.

### `medical.targets.list`

List configured medical target mappings.

Implementation:

- Read `dim_world_domain_collection`.
- Return target id, domain, collection, world total, and current coverage if
  available.

### `medical.ingest.reconcile`

Compare desired state with live state.

Checks:

- CronJob exists and is not suspended unless requested.
- CronJob image matches Git desired tag/digest policy.
- `imagePullSecrets` contains `ghcr-pull`.
- `medical-coverage-ingester-secrets` exists.
- All four coverage mappings exist.
- Recent Job succeeded within expected schedule window.

Output should be machine-actionable:

```json
{
  "ok": false,
  "checks": [
    {"name": "cronjob_exists", "ok": true},
    {"name": "facility_csv_url_configured", "ok": false, "severity": "warn"}
  ]
}
```

## Backend Adapter Interface

Use a small adapter boundary so the MCP tool names survive backend migration.

```python
class MedicalIngestBackend:
    def get_coverage(self, targets: list[str]) -> dict: ...
    def trigger(self, request: TriggerRequest) -> dict: ...
    def status(self, job_name: str) -> dict: ...
    def logs(self, job_name: str, tail_lines: int) -> dict: ...
    def pause(self, reason: str, requested_by: str) -> dict: ...
    def resume(self, requested_by: str) -> dict: ...
    def reconcile(self) -> dict: ...
```

Initial adapter:

- `KubernetesCronJobBackend`

Future adapter:

- `ZeebeIngestBackend`

The future Zeebe adapter should keep `medical.ingest.trigger` output compatible
by returning both `jobName` when applicable and `runId` /
`zeebeProcessInstanceKey` when the process engine owns execution.

## State Model

Short term:

- Coverage target state remains in `dim_world_domain_collection`.
- Coverage progress remains in `mv_world_collection_coverage_live`.
- Ingester cursor remains in `vertex_repo_record` collection
  `com.etzhayyim.apps.iryo.coverageCursor`.
- Kubernetes Job status is the run status for bounded Jobs.

Medium term:

- Mirror each MCP-triggered run into `vertex_ingest_run`:
  - `ingest_family='medical_coverage'`
  - `source_id in ('pubmed', 'clinical_trials', 'dsm', 'facilities_csv')`
  - `mode in ('delta', 'backfill', 'repair', 'verify')`

This lets generic `com.etzhayyim.apps.ingest.status` and domain-specific
`medical.ingest.status` converge.

## Security

Read-only tools:

- `medical.coverage.get`
- `medical.targets.list`
- `medical.ingest.status`
- `medical.ingest.logs`
- `medical.ingest.reconcile`

Mutation tools:

- `medical.ingest.trigger`
- `medical.ingest.pause`
- `medical.ingest.resume`
- `medical.ingest.configure`

Policy:

- Read-only may be public if exposed through the existing MCP read-only policy.
- Mutation requires AT Protocol session JWT or ES256 service auth.
- `configure` requires admin/operator role.
- The K8s ServiceAccount must not be able to touch arbitrary Jobs.

RBAC minimum:

```yaml
rules:
  - apiGroups: ["batch"]
    resources: ["cronjobs"]
    resourceNames: ["medical-coverage-ingester"]
    verbs: ["get", "patch"]
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "create", "delete"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["medical-coverage-ingester-secrets"]
    verbs: ["get", "patch"]
```

The implementation must additionally filter Jobs by label
`app.kubernetes.io/name=medical-coverage-ingester` before returning logs or
status.

## Failure Semantics

MCP call success means only that the control-plane operation succeeded.

Examples:

- `medical.ingest.trigger.ok=true` means Job creation succeeded, not ingest
  completion.
- `medical.ingest.status.job.succeeded=1` means Kubernetes completed the Job,
  not that coverage reached 100%.
- `medical.coverage.get.coverageRate` is the source of truth for coverage.

Retries:

- Duplicate trigger requests should create a distinct Job unless a caller passes
  an explicit `idempotencyKey`.
- With `idempotencyKey`, return the existing Job if it is still active or
  completed in the retention window.

## Observability

Every triggered Job should include:

- `ai.etzhayyim.com/requested-by`
- `ai.etzhayyim.com/idempotency-key` when supplied
- `ai.etzhayyim.com/targets`
- `ai.etzhayyim.com/run-kind=manual|scheduled|backfill`

Ingester logs must keep the current concise format:

```text
[   54.6s] [pubmed] inserted=500
[   54.6s] [clinical_trials] coverage already complete: 1.1334
```

MCP `logs` should return these lines verbatim as bounded text plus parsed
summary where possible.

## Implementation Options

### Option A: Standalone Python MCP server on Kubernetes

Pros:

- Direct access to Kubernetes in-cluster config.
- Reuses psycopg and Python Kubernetes client.
- Easy to colocate with current ingester.

Cons:

- Needs MCP HTTP/JSON-RPC wrapper or bridge to the existing atproto MCP facade.

### Option B: Cloudflare Worker MCP facade + in-cluster control API

Pros:

- Fits existing public MCP exposure pattern.
- Auth and read-only/mutation policy already exist in Worker layer.

Cons:

- Needs a private in-cluster control API or Kubernetes API proxy.
- More moving pieces.

### Option C: Register as `kotodama` UDF/MCP handlers

Pros:

- Matches existing `com.etzhayyim.apps.ingest.*` handler style.
- Tool registration and MCP discovery already exist.

Cons:

- Kubernetes API access from UDF pod is a broader operational capability.
- UDF calls must remain short and should not become scheduler logic.

Recommended first implementation: **Option A for cluster-local control**, then
register the tools through the existing MCP registry/facade. Keep all mutation
calls short and asynchronous.

## Rollout Plan

1. Add `medical-coverage-mcp` package with backend adapter and JSON-RPC MCP
   handlers.
2. Add Kubernetes Deployment, ServiceAccount, Role, RoleBinding, and Service.
3. Expose read-only tools internally first.
4. Add mutation tools with auth guard.
5. Add `medical.ingest.trigger` idempotency key support.
6. Add `vertex_ingest_run` mirroring.
7. Optionally replace CronJob backend with Zeebe backend when medical ingest
   gains BPMN approval, incident replay, or multi-step human review.

## Acceptance Criteria

- `medical.coverage.get` returns the same four rows visible in
  `mv_world_collection_coverage_live`.
- `medical.ingest.trigger` creates a Job and returns before the Job finishes.
- `medical.ingest.status` observes Active, Complete, and Failed Jobs.
- `medical.ingest.logs` returns bounded logs for only medical ingester Jobs.
- `medical.ingest.pause` and `resume` patch only `medical-coverage-ingester`.
- No MCP request directly fetches PubMed pages or performs bulk inserts.
- The system still works if the backend changes from CronJob to Zeebe.
