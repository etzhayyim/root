---
id: adr-2604262000-edge-thin-app-runtime-k8s-zeebe-registry
title: "ADR: Cloudflare Worker is thin edge; app actors run through MCP registry, agent dispatcher, Zeebe BPMN, and Kubernetes Python workers"
status: superseded
doc_type: adr
topic: edge-thin-app-runtime
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - cloudflare-worker-app-count-boundary
  - app-actor-runtime-placement
  - mcp-registry-agent-dispatcher-zeebe-k8s-topology
related:
  - adr-2604261000-mcp-registry-via-kysely-schema
  - adr-2604251801-cron-three-layer-consolidation
  - adr-2604251758-murakumo-yoro-actor-worker-fleet
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-0056-bpmn-as-actor
  - adr-2604231811-atproto-extension-service-layers
  - adr-2604241611-nsid-split-domain-k8s-federation-edge
supersedes: []
superseded_by:
  - adr-2604282300
---

# Context

The repository still contains two phrases that are easy to read as conflicting
runtime guidance:

1. `Hono + Single Worker` for appview style Cloudflare deployments.
2. P5+P3 actor execution, where only T3 apps receive a dedicated Worker or
   Container and the majority of actors are registry-driven.

The current inventory confirms the scale problem:

- `50-infra/cloudflare/workers/*`: 28 local Worker directories.
- `60-apps/**/appview/*/package.json`: 492 appview package entries.
- `60-apps/**/appview/*/src/app.ts`: 252 appview app handlers.
- `60-apps/**/appview/*/svelte/package.json`: 84 Svelte appview entries.

At this scale, interpreting "one app = one Cloudflare Worker" would recreate
the old P1 static deployment problem. It would also approach the account-level
Worker cap and split orchestration, retry, cursor, and observability state
between Cloudflare, Zeebe, Kubernetes, and Kotoba/Datomic.

The intended architecture is already partially decided by existing ADRs:

- ADR-260408 actor executor P5+P3: T1/T2 actors should not require Workers;
  only T3 full custom actors may have a dedicated Worker/Container.
- ADR-2604261000 MCP registry: tool definitions are Kysely/Kotoba/Datomic rows,
  not generated per-app Worker bundles.
- ADR-2604251801 cron consolidation: business schedules move to Zeebe BPMN
  timers and Python workers, not Cloudflare `triggers.crons`.
- ADR-260425 ingest orchestration: durable ingest runs belong in Zeebe plus
  Kubernetes Python workers.

# Decision

Cloudflare Worker is the **thin edge and app shell runtime**, not the app actor
runtime. New app actors must be implemented as registry rows, BPMN processes,
and Kubernetes-executed worker tasks unless they satisfy an explicit T3
exception.

## Runtime Topology

```text
Browser / MCP client / AT Protocol client
        |
        v
Cloudflare main edge Worker
  - Hono router
  - Svelte CSR asset shell
  - auth / DPoP / CORS / service-token checks
  - XRPC and MCP facade
  - request normalization and response shaping
        |
        +--> MCP registry (vertex_mcp_tool_def)
        |
        +--> agent registry dispatcher
        |      - resolves actor_did / nsid / capability / policy
        |      - starts or signals BPMN process instances
        |      - calls direct read-only graph queries for simple views
        |
        v
Zeebe BPMN process instance
        |
        v
Kubernetes pods
  - pyzeebe generic workers
  - pymagatama Python domain workers
  - LangGraph / LLM workers where needed
  - source-specific ingest / browser / OCR / conversion pods
        |
        v
Kotoba/Datomic / B2 / PDS / external APIs
```

## Cloudflare Worker Boundary

Keep only these Cloudflare Workers on the main path:

| Worker class | Responsibility |
|---|---|
| main Hono edge | public HTTP, auth, XRPC, MCP facade, Svelte CSR assets |
| PDS / atproto edge | AT Protocol repo, auth, federation-compatible XRPC |
| routing/proxy edge | DNS/host routing, static CDN, constrained upstream proxy |
| T3 exception | truly custom latency-sensitive edge app or required CF binding |

Do not create one Cloudflare Worker per app actor. A 284-app or 397-app estate
must remain registry-driven.

## App Actor Runtime Boundary

| Tier | Runtime | Allowed implementation |
|---|---|---|
| T1 | registry-composed actor | MCP primitives + BPMN process + graph rows |
| T2 | hybrid actor | BPMN + MCP primitives + constrained script/handler, executed by dispatcher or worker pod |
| T3 | custom actor | dedicated Worker/Container only after exception review |

T1/T2 app creation is a data operation:

1. add or sync lexicon contract;
2. insert or update `vertex_mcp_tool_def`;
3. insert or update actor/app registry rows;
4. deploy or update BPMN process definition;
5. let the dispatcher route calls to Zeebe or read-only graph paths.

No Worker rebuild is required for routine app addition.

## Agent Registry Dispatcher

Introduce or consolidate an `agent-registry-dispatcher` service as the runtime
decision point between the edge facade and Zeebe.

Responsibilities:

- resolve `(host, actor_did, nsid)` to actor manifest, MCP tools, BPMN process,
  and execution tier;
- enforce capability grants, Rego/DMN policy, org/user visibility, and service
  auth before any process start;
- choose route:
  - read-only graph query for simple query endpoints;
  - Zeebe process start/signal for business actions, ingest, long tasks, and
    retries;
  - T3 Worker/Container fetch only for approved T3 exceptions;
- emit audit rows and OCEL events;
- keep edge Workers stateless except for short cache.

The dispatcher may first live inside the existing PDS/atproto Worker for
compatibility, but its contract must be service-shaped so it can move to k8s
without changing MCP/XRPC callers.

## Zeebe / BPMN / Python Worker Boundary

Use Zeebe when a call:

- changes durable domain state;
- can exceed Cloudflare CPU/time/memory limits;
- requires retry, pause/resume, incident handling, compensation, or human
  review;
- needs LLM analysis, browser automation, OCR/conversion, external API cursor,
  or bulk writes;
- is a scheduled actor behavior.

Python worker pods own source-specific logic. They must be importable modules
under `pymagatama`, not one-off operator scripts. Worker pods report run state
to Kotoba/Datomic tables such as `vertex_ingest_run`, domain-specific run tables,
and OCEL/audit tables.

# Migration Plan

## Phase 0: Inventory and Guardrails

- Classify all appview/app handlers into T1/T2/T3.
- Mark existing dedicated Workers as `edge`, `infra`, `PDS`, or `T3`.
- Add CI/reporting that fails new per-app Worker creation unless it is tagged
  with a T3 exception.
- Update wording in operational docs: "Hono + Svelte main edge" replaces
  "all app = Hono + Single Worker".

Exit criteria:

- local Worker count is tracked;
- all appview package entries have a tier;
- no unknown app actor is assumed to need a Worker.

## Phase 1: Registry SSoT

- Finish `vertex_mcp_tool_def` migration and sync.
- Add actor/app registry rows that map `actor_did`, `host`, `nsid`, `bpmn_id`,
  `execution_tier`, and optional `t3_worker_ref`.
- Make `/mcp tools/list` and OpenAPI facade read from registry rows.
- Add an operator command to diff lexicon, registry rows, and BPMN deployment.

Exit criteria:

- adding a T1 app requires only lexicon + registry + BPMN row/process sync;
- the edge Worker can serve tool discovery for a new app without redeploy.

## Phase 2: Dispatcher Contract

- Define dispatcher request/response envelope:
  `(actor_did, nsid, caller, auth_context, input, idempotency_key)`.
- Implement route decisions for:
  - graph read;
  - Zeebe process start;
  - Zeebe message/signal;
  - T3 Worker fetch.
- Emit audit/OCEL events for every dispatch attempt.
- Add idempotency keys and timeout/degraded response semantics.

Exit criteria:

- Hono edge calls dispatcher instead of importing app-specific execution code;
- policy failure, missing tool, Zeebe incident, and T3 fallback are observable.

## Phase 3: Zeebe + Kubernetes Execution

- Create or consolidate `agent-worker` and `ingest-worker` Deployments.
- Register pyzeebe handlers for generic task types:
  `mcp.call`, `graph.query`, `graph.write`, `agent.run`, `pds.dispatch`,
  `ingest.*`, `audit.emit`.
- Move long-running app logic out of Workers into `pymagatama` modules.
- Keep k8s CronJobs only as start signal emitters or infra maintenance jobs.

Exit criteria:

- scheduled app behavior runs through BPMN timers, not CF cron;
- long-running app calls survive Worker request lifetime and are visible in
  Zeebe/Operate plus Kotoba/Datomic run tables.

## Phase 4: T3 Reduction

- Review each dedicated app Worker/Container.
- Convert simple API + Svelte apps to main edge + registry + BPMN.
- Keep only approved T3 cases with one of:
  - mandatory Cloudflare binding;
  - strict edge latency requirement;
  - streaming/websocket behavior that cannot be proxied to k8s safely;
  - hard external compatibility contract.

Exit criteria:

- Worker count remains bounded by platform/infra concerns, not app count;
- app growth from 284 to 500+ changes rows/processes, not Cloudflare Worker
  scripts.

# Consequences

Positive:

- App count no longer consumes Cloudflare Worker count.
- Durable work gains Zeebe retry, incident, and pause/resume semantics.
- MCP registry, actor registry, BPMN, and Kotoba/Datomic become the visible control
  plane for agents.
- Svelte stays available for app UI without forcing per-app edge deployment.

Trade-offs:

- Simple app additions require registry/BPMN discipline instead of copying a
  Worker scaffold.
- Edge-to-k8s calls add a network hop for mutating operations.
- The dispatcher becomes critical infrastructure and needs clear SLOs,
  idempotency, and audit coverage.

# Implementation Notes

## 2026-04-27 state Worker retirement proof

The first country-state retirements have been executed under this ADR's
topology:

- `magatama-g0vafg01` retired after AFG coverage moved to k8s/BPMN/RW.
- `magatama-g0vzaf01` retired after ZAF coverage moved to
  `pymagatama.primitives.gov_zaf`, `govZaf` BPMN/MCP registry rows, and
  Kotoba/Datomic/B2 official-source evidence.

ZAF deletion was gated by `npm run verify:gov-zaf`:

- `vertex_page`: 3/3 official South African Government pages.
- `vertex_wet_chunk`: 3/3.
- `vertex_wat`: 3/3.
- `vertex_screenshot`: 3/3 gyotaku PNGs in B2.
- `vertex_gov_source`: 3/3 official-source manifest rows.
- `vertex_gov_org`: 53 seeded org rows.

The work also exposed a durable platform requirement: large `vertex_page`
tables need narrow covering indexes for point lookup gates. The
`idx_vertex_page_vertex_id_cover` index now covers `vertex_id` lookups used by
state Worker retirement checks.

AGO was executed as the next candidate:

- `pymagatama.primitives.gov_ago` registers the `govAgo` Zeebe task surface.
- `govAgo` BPMN and lexicons now cover seed, DID registration, site follows,
  official-source ingest, WET sync, shinka, list, resolve, and heartbeat.
- Seed data is based on the official Angola government portal pages
  `https://governo.gov.ao/ministro`, `https://governo.gov.ao/governador`, and
  `https://governo.gov.ao/angola/provincias`.
- The delete gate is `pnpm --dir 30-graph/graph-schema verify:gov-ago`; after
  direct fallback ingest of the three official pages, the gate was green
  (`deleteAllowed: true`, page/WET/WAT/screenshot/govSources 3/3,
  orgSeeds ministry=24 state=21).
- `magatama-g0vago01` was deleted after the green gate. Post-delete Cloudflare
  check reports `This Worker does not exist on your account [10007]`, and the
  post-delete AGO verifier remains green.

# Alternatives Considered

## A. One Cloudflare Worker per app

Rejected. It recreates the old P1 static deploy topology, couples app count to
Worker quota, and hides long-running work behind edge request limits.

## B. Keep MCP registry but call handlers directly in the edge Worker

Rejected as the default. It is acceptable for read-only graph queries, but it
does not provide durable orchestration, retry, or worker-pod resource isolation.

## C. Make MCP the dispatcher

Rejected. MCP is tool discovery and invocation surface. BPMN/Zeebe remains the
orchestration source of truth for business processes.

# References

- `50-infra/CLAUDE.md` Cloudflare limits and Hono/Svelte runtime notes.
- `90-docs/260408-actor-executor-p5p3-architecture-design.md`.
- `90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md`.
- `90-docs/adr/2604261000-mcp-registry-via-kysely-schema.md`.
- `90-docs/adr/2604251801-cron-three-layer-consolidation.md`.
