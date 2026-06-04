---
id: adr-2604231457-bpmn-security-posture-camunda-alignment
title: "ADR: BPMN-as-Actor security posture and legacy Camunda 8 alignment"
status: active
doc_type: adr
topic: bpmn-security
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - BPMN dispatcher auth mode (off / strict)
  - Legacy Zeebe compatibility-track security posture
  - What Camunda 8 components we used vs. deliberately skipped
  - generic.db.select SQL injection defense-in-depth
related:
  - adr-0056-bpmn-as-actor
  - adr-0058-unified-5-pillar-platform-architecture
  - adr-0059-tool-runtime-selection-python-udf-default
  - adr-0022-auth-topology-consolidation
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
supersedes: []
superseded_by: []
---

# Context

ADR-0056 moved actor logic into declarative BPMN executed by Zeebe + pyzeebe
workers. ADR-0058 formalised the 5-pillar topology. Two concrete attack
surfaces opened as a side-effect:

1. `dispatcher.etzhayyim.com:8080` is an aiohttp entry point in the `mitama-udf`
   namespace that fans any `POST /xrpc/{nsid}` into a Zeebe process
   instance. The Service is `type: LoadBalancer` (Vultr LB) and had **no
   authn** — any caller on the public internet could invoke every
   registered NSID.
2. `generic.db.select` is the most powerful primitive a BPMN actor can
   bind. `table` and `extraFilters.column` were already allow-listed, but
   `columns` (projection) and `orderBy` were spliced into SQL text
   unvalidated. A BPMN actor author — or an attacker who can persuade
   RisingWave to emit a malformed binding — could craft arbitrary SQL.

Separately we had not written down what of Camunda 8's official surface we
rely on vs. what we skip, which has caused confusion about version
upgrades (Zeebe 8.7 ships a breaking exporter change).

# Decision

## 1. Dispatcher auth: shared-secret header, two modes

`etzhayyim-dispatcher` (pymagatama ≥ 0.2.28) gates `/xrpc/*` on a new
`DISPATCHER_AUTH_MODE` env var:

| Mode | Behaviour |
|---|---|
| `off` (default during rollout) | No auth check. Kept for backward-compat during the zero-downtime flip — PDS pipethrough is deployed first without the shared-secret header, then dispatcher flips to strict, then PDS is redeployed with the header. |
| `strict` | Every `/xrpc/*` request must carry `x-internal-trust: <DISPATCHER_INTERNAL_SECRET>`. Verified with `hmac.compare_digest` (constant-time). Absent/mismatched → HTTP 401. Unknown mode → HTTP 500 (fail-closed). |

`/health` and `/bindings` stay open — they return no actor state and are
needed by the kube liveness probe.

This is a pragmatic first step, not the end state. It deliberately
**does not** replicate Camunda's full OAuth2 / Identity story (see
§2.3). The upgrade path is:

1. shared secret (this ADR, 2026-04-23)
2. ES256 Service Auth JWT with `lxm`-scoped audience = dispatcher URL,
   verified via `10-protocol/xrpc/src/ServiceAuth` (alignment with
   ADR-0022, scheduled Phase-2, not in this ADR's scope)

## 2. Camunda 8 official-spec alignment

### 2.1 Version pin: Zeebe 8.6.39 LTS

We pin `camundaplatform/camunda:8.6.39`. Zeebe 8.6 is the last release
whose default exporter (`elasticsearch`) can be swapped out without also
running the new `camundaexporter` (8.7+). `camundaexporter` upstreams a
hard dependency on Elasticsearch 8.x, which we do not run; bumping now
would add an Elasticsearch node to the Vultr VKE cluster purely to feed
Operate. Decision: stay on 8.6 until Operate becomes a requirement.

### 2.2 Components we use (official surface)

| Camunda 8 component | Usage | Notes |
|---|---|---|
| Zeebe gRPC gateway | sole entry for BPMN deploy + process-start | we speak the official protocol via pyzeebe (community, but API-compatible) |
| BPMN 2.0 XML | authoritative actor spec | parsed by Zeebe, not by our tooling |
| FEEL | gateway / io-mapping expression language | standard, no extensions |
| Zeebe `service-task` + `zeebe:taskDefinition.type` | job-worker binding | pyzeebe polls by type |
| Zeebe `multiInstanceLoopCharacteristics` + `zeebe:loopCharacteristics` (inside `extensionElements`) | parallel fan-out | spec-compliant placement |
| Zeebe timer start event (`R/PTxM`, `cron:*/15 * * * *`) | periodic actors | ISO-8601 + quartz-style cron |

### 2.3 Components we deliberately skip

| Camunda 8 component | Why we skip |
|---|---|
| **Operate** | requires Elasticsearch exporter; we rely on RisingWave `vertex_bpmn_instance` / `vertex_bpmn_history` streaming MVs + the dispatcher's `/bindings` endpoint for live state. |
| **Tasklist** | we have no human-task workflow; all actors are machine-executed. If added, tasklist-claim gating would be expressed as FEEL + an `approval` boundary event, still server-side. |
| **Identity** | we already run our own DID + Service Auth stack (ADR-0022). Camunda Identity would be a duplicate trust root. Our strict-mode shared secret + planned ES256 upgrade uses the existing AuthN worker as the trust origin. |
| **AI Agent Task connector** | Camunda's connector expects an OpenAI-compatible endpoint and serialises the full tool-use loop server-side. We route LLM calls through `generic.llm.json` (Murakumo LiteLLM gateway) so the tier-selection / tool-invocation loop stays in Python worker code where we already own the cache, audit, and retry behaviour. Revisit once Camunda ships a provider-agnostic tool contract. |
| **HA cluster** | Zeebe in broker-only mode (1 replica) is sufficient for current traffic. Failover is achieved by k8s pod-reschedule + deterministic PK (ADR-0041) — we do not need Zeebe Raft. |
| **camundaexporter (8.7+)** | as above, forces Elasticsearch. |

### 2.4 Extensions beyond the official surface

We add exactly two patterns that Camunda does not prescribe but do not
violate the spec:

1. **RisingWave-backed process-definition store**
   `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` are our own
   declarations consumed by `dispatcher_main.py`'s watcher loop and
   (re-)deployed to Zeebe on change. Camunda normally uses its own
   Elasticsearch-backed catalog for this; we use RisingWave because it
   is already the canonical state store (ADR-0058 Pillar 3).
2. **Lexicon-bound job types**
   `zeebe:taskDefinition.type` values follow the `generic.<domain>.<action>`
   or `com.etzhayyim.<domain>.<action>` convention and are wired to pyzeebe
   handlers by name. This is no different from Camunda's own convention;
   we document it so reviewers don't look for an implicit registry.

## 3. `generic.db.select` defense-in-depth

`zeebe_worker_main.py` now rejects any `columns` or `orderBy` that does
not match a strict regex:

| Field | Grammar |
|---|---|
| `table` | `^(vertex\|edge\|mv)_[a-z0-9_]+$` (pre-existing) |
| `columns` | `*` or a comma-separated list of `[a-z_][a-z0-9_]*` identifiers, optionally prefixed with `DISTINCT`, optionally with `AS alias`. No parens, no semicolons, no quotes, no comments. |
| `orderBy` | comma-separated `col [ASC\|DESC]` identifiers. |
| `extraFilters[*].column` | `^[a-z_][a-z0-9_]*$` (pre-existing) |
| `extraFilters[*].op` | enum: `=, !=, <>, <, >, <=, >=, LIKE, ILIKE` (pre-existing) |

`whereExpr` remains a caller-provided SQL fragment bound via `%s`
parameters — we trust it because BPMN authors write it at XML-authoring
time, and every BPMN is reviewed on merge.

Failure mode is deliberately a `{"error": ...}` payload (not an
exception) so Zeebe records the failure without retrying into a loop —
the BPMN actor stops at the select task and surfaces the error to the
caller.

# Consequences

## Positive

- Dispatcher LB is no longer a trivially-callable RPC surface once
  strict mode is flipped on.
- SQL injection via `columns`/`orderBy` requires an attacker to bypass a
  regex — every currently-registered BPMN binding still passes.
- We have a written record of which Camunda 8 features we rely on and
  which we skip, so 8.6 → 8.7+ upgrade discussions have a shared
  baseline.

## Negative

- `AUTH_MODE=off` as the default during rollout means the production
  dispatcher is un-authed for a bounded window (hours, not days). We
  accept this in exchange for zero-downtime flip — the alternative
  (default=strict, redeploy PDS and dispatcher in lockstep) is riskier
  for callers already in flight.
- Shared-secret auth is weaker than ES256 Service Auth; the follow-up
  migration is tracked as a separate ADR + migration ticket, not as
  "future work in this ADR".

## Neutral

- The `columns` regex rejects `count(*)`, `jsonb_path_query(...)`, etc.
  Any BPMN actor that needs those must use a dedicated primitive
  (`generic.db.count`, or a typed projection). This is the intended
  behaviour — opening the grammar turns the regex into a parser.

# Rollout

| Step | Action | Gate | Status |
|---|---|---|---|
| 1 | Merge pymagatama 0.2.28 with `AUTH_MODE=off` default | CI green | done (PR #1108, 2026-04-23) |
| 2 | `helm upgrade` dispatcher + mitama-udf workers | `/health` 200, `/bindings` non-empty | done (Version 55, 2026-04-23). All 3 deploys on `sha256:ed35265…d9dee`, dispatcher `/health` 200, direct `http://dispatcher.etzhayyim.com:8080/xrpc/...` → 200 with Zeebe data. |
| 3 | PDS pipethrough sends `x-internal-trust: ${DISPATCHER_INTERNAL_SECRET}` from Secrets Store | PDS Worker deploy ok + end-to-end smoke (atproto → dispatcher → 200) | **partial, blocked** — code deployed (PDS Version `0820a358…`) and CF Secrets Store `dispatcher_internal_secret` created, but CF Workers `fetch("http://dispatcher.etzhayyim.com:8080/...")` returns 5xx from inside the CF fabric. External fetch works. Pipethrough silently falls through to the legacy handler. Every migrated yabai NSID is currently served by fallback, not by the dispatcher. |
| 3.1 | **Blocker fix — dispatcher origin reachability from CF Workers** | Some CF-Worker-callable HTTPS origin resolves to the `bpmn-dispatcher` service | not started. Options: (a) CF Tunnel (`cloudflared` sidecar in `mitama-udf` namespace — recommended, matches murakumo-serve pattern); (b) CF Spectrum (Enterprise); (c) TLS terminate at Vultr LB :443 + orange-cloud `dispatcher.etzhayyim.com`. |
| 3.2 | Re-run end-to-end smoke after 3.1 | `curl atproto.etzhayyim.com/xrpc/com.etzhayyim.apps.yabai.listFlags` → 200 with real flags payload (via dispatcher, not fallback) | — |
| 4 | Flip dispatcher `AUTH_MODE=strict` via helm values | bare curl `http://dispatcher…:8080/xrpc/...` → 401; PDS-forwarded → 200 | blocked on 3.1 |
| 5 | Post-mortem: confirm no non-PDS caller exists on the LB | Vultr LB access-log scan | — |

Rollback: helm rollback to previous release values (`AUTH_MODE=off`) is
the single-step recovery. The pipethrough header is benign when the
dispatcher is in off-mode, so step 3 / 3.2 / 4 can each roll back
independently.

# Post-deploy findings (2026-04-23)

- **Dispatcher reachability from CF Workers is broken.** `http://dispatcher.etzhayyim.com:8080` resolves to the Vultr node IP directly (unproxied) but CF Workers `fetch` to it returns 5xx, so `pipethroughBpmnDispatcher` takes its `>= 500 → null` branch and the caller lands in the 404 "unknown method" fallback of `dispatchXRPC`. Pre-existing — PR #1101 that added the pipethrough code was merged but the PDS Worker was never successfully redeployed after it; this ADR's deploy is the first time the code ran in production.
- **Dispatcher health is fine.** Direct external curl against the Vultr LB returns 200 with real Zeebe-routed data. The issue is purely the CF-Worker → Vultr-LB path.
- **`generic.db.select` columns/orderBy allow-list is live.** Every BPMN binding audited on merge passes the regex; `SUM(*)`, `(select 1)`, `name; DROP`, quoted / commented expressions all reject. Failure returns a structured `{error, rows: [], rowCount: 0}` payload so Zeebe does not retry-loop.
- **Context shim shipped.** `pymagatama/context.py` lets `handlers/__init__.py` import `contracts` and `houbun` handlers without crashing the UDF pool. Those two handlers fail at invocation instead (NotImplementedError), which is the desired failure mode until the real Context is wired.

# Non-goals (explicit)

- Enabling Camunda Operate / Tasklist / Identity.
- Upgrading to Zeebe 8.7.
- Replacing the shared secret with ES256 Service Auth (tracked
  separately).
- Adding per-NSID ACL in the dispatcher (handled at PDS pipethrough
  allowlist — `BPMN_DISPATCHER_NSIDS` — which is already in place and
  does not need a second enforcement layer).

# Addendum — 2026-05-08 — Spiff replacement boundary

ADR-2605081200 supersedes this ADR for **workflow engine selection and
Zeebe version pinning**. This ADR remains active only for the security
decisions it introduced: dispatcher shared-secret mode, the ES256 Service
Auth upgrade path, and `generic.db.select` defense-in-depth.

Camunda 8 / Zeebe references in this document are now legacy compatibility
context. New BPMN runtime apply, rollback, and acceptance decisions are
governed by ADR-2605081200 and
`etzhayyim-root/50-infra/k8s/bpmn-engine-host/RUNBOOK.md`.
