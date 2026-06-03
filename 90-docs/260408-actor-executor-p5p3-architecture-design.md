# Actor Executor P5+P3 Architecture Design

**Date**: 2026-04-08
**Status**: `[IMPLEMENTED]` `[PRODUCTION]`
**Evidence**: `50-infra/cloudflare/workers/atproto/src/actor-executor-*.ts`, `50-infra/cloudflare/workers/atproto/src/bpmn-pipeline-compiler.ts`, `00-contracts/wit/deps/magatama-actor-executor/package.wit`
**Deploy**: PDS Worker `etzhayyim-pds-2603241700` (atproto.etzhayyim.com)
**Graph**: RisingWave `graphar.vertex_actor` (1,732 rows), `graphar.vertex_actor_manifest`

## Problem

397 apps × 個別 CF Worker deploy = 理論上 397 Workers が必要。実態は 4 のみ deploy 済み、393 は LogicalActor/stub。全 actor が個別 Worker を持つ P1 (Static Deploy) パターンは η=0.108 と非効率。

## Solution: P5+P3 Hybrid — 3-Tier Execution

Shannon 最適パターン P5 (MCP-Compose, η=0.667) をデフォルトとし、P3 (Server Dynamic, η=0.159) を escape hatch として提供。

### Tier 分類

| Tier | パターン | 数 | 実行方式 | η |
|---|---|---|---|---|
| **T1** | P5 MCP-Compose | ~260 | host 関数合成のみ。Worker 不要 | 0.667 |
| **T2** | P5+P3 Hybrid | ~90 | MCP 合成 + sandboxed inline TS | 0.50 |
| **T3** | P3 Full Custom | ~27 | 専用 CF Worker / Container | 0.108 |

**System η: 0.108 → 0.57 (5.3× improvement)**
**CF Workers: 397 → 27**

## Architecture

```
yoro.etzhayyim.com Actor Designer (BPMN/DMN/Forms)
  ↓ compileBpmn / deployProcess
actor-manifest.jsonld (統一メタデータ)
  ├── executionTier: T1 → PDS Shared Executor (host-imports direct)
  ├── executionTier: T2 → ActorExecutorDO (V8 sandbox + host-imports)
  └── executionTier: T3 → Dedicated CF Worker (unchanged)
  ↓
PDS Event Stream + Derive Pipeline
  ↓
kagami graph DB + OCEL 2.0 event log
```

## Actor Manifest Schema

**Collection**: `com.etzhayyim.actor.manifest`
**Graph label**: `ActorManifest`
**Source**: `50-infra/cloudflare/workers/atproto/src/actor-manifest.ts`

```typescript
interface ActorManifest {
  '@context': 'https://etzhayyim.com/ns/actor/v1';
  '@id': string;           // Actor DID
  name: string;            // Slug
  nanoid: string;          // Nanoid
  executionTier: 'T1' | 'T2' | 'T3';
  capabilities: McpPrimitive[];
  pipelines?: Array<{
    trigger: PipelineTrigger;  // cron | subscribeRepos | a2aInvoke | manual | xrpc
    steps: PipelineStep[];     // Ordered MCP primitive calls
  }>;
  derive?: DeriveRules;
  workerRef?: string;       // T3 only
  bpmnXml?: string;         // BPMN 2.0 source
  dmnXml?: string;          // DMN 1.3 source
  formSchemas?: Record<string, Record<string, unknown>>;
}
```

## 12 MCP Primitives

| Primitive | Host Import | BPMN Element |
|---|---|---|
| `graph.query` | `magatama:graph/cypher.cypherQuery` | ServiceTask (camunda:type=graph-query) |
| `graph.write` | `magatama:graph/cypher.cypherBatchExec` | ServiceTask (camunda:type=graph-write) |
| `graph.vectorSearch` | `magatama:graph/vector-search.vectorSearch` | ServiceTask |
| `agent.chat` | `magatama:agent.agentChat` | ServiceTask (camunda:type=agent-chat) |
| `agent.invoke` | `etzhayyim:invoke/invoke.invoke` | ServiceTask (camunda:type=agent-invoke) |
| `identity.resolve` | `magatama:identity.identityResolve` | ServiceTask |
| `browser.fetch` | `magatama:browser.navigate` | ServiceTask (camunda:type=browser-fetch) |
| `signal.encrypt` | `etzhayyim:signal.ratchetEncrypt` | ServiceTask |
| `consent.check` | `magatama:consent.consentCheck` | ServiceTask |
| `derive:social` | PDS commit pipeline | EndEvent (etzhayyim:deriveTemplate) |
| `dmn.evaluate` | FEEL decision table eval | BusinessRuleTask |
| `form.collect` | FormTask graph node | UserTask |

## BPMN → Pipeline Compilation

**Source**: `50-infra/cloudflare/workers/atproto/src/bpmn-pipeline-compiler.ts`

```
BPMN Element          →  Pipeline Step
─────────────────────────────────────────
ServiceTask           →  MCP primitive (etzhayyim:primitive or camunda:type)
BusinessRuleTask      →  dmn.evaluate (decisionRef → args.decisionId)
UserTask              →  form.collect (formRef → args.formId)
ScriptTask            →  custom handler (T2 only, script body → step.handler)
ExclusiveGateway      →  conditional branch (FEEL condition)
ParallelGateway       →  parallel step group
StartEvent (Timer)    →  trigger: { type: "cron" }
StartEvent (Signal)   →  trigger: { type: "subscribeRepos" }
StartEvent (Message)  →  trigger: { type: "a2aInvoke" }
EndEvent              →  derive:social (etzhayyim:deriveTemplate)
```

## Runtime Triggers

### subscribeRepos (Event-Driven)

`pds-core.ts` `comAtprotoRepoCreateRecord` → fire-and-forget → `actor-executor-triggers.ts` `dispatchSubscribeReposTrigger` → scan ActorManifest graph for matching collection → execute pipeline.

### Cron (DO Alarm Chain)

`actor-executor-triggers.ts` `scheduleCronTriggers` → `ActorExecutorDO` `schedule-cron` → DO storage (cron config) + `setAlarm(nextTick)` → `alarm()` handler → execute pipeline → reschedule.

## T2 Sandbox Security Model

- Custom handlers receive restricted `ctx` with ONLY declared capabilities
- `new Function()` constructor creates isolated scope
- No direct `fetch()`, `eval()` beyond handler
- 30s CPU timeout (CF Worker limit)
- 128MB memory (V8 isolate)
- Capabilities must be subset of actor's declared capabilities

## OCEL 2.0 Process Mining

**Source**: `50-infra/cloudflare/workers/atproto/src/actor-executor-ocel.ts`

| Object Type | Description |
|---|---|
| Actor | Executing actor DID |
| Pipeline | Pipeline definition (trigger + steps) |
| Step | Individual step execution |
| FormTask | Pending/submitted user task |

| Event Type | When |
|---|---|
| `pipeline:start` | Pipeline execution begins |
| `pipeline:end` | Pipeline completes successfully |
| `pipeline:error` | Pipeline fails at a step |
| `step:end` | Step completes |
| `step:error` | Step fails |
| `form:pending` | UserTask created |
| `form:submitted` | UserTask form submitted |

## XRPC NSIDs

| NSID | Type | Description |
|---|---|---|
| `com.etzhayyim.actor.executePipeline` | write | Execute T1/T2 pipeline |
| `com.etzhayyim.actor.registerManifest` | write | Register manifest |
| `com.etzhayyim.actor.getManifest` | read | Get manifest by DID |
| `com.etzhayyim.actor.validateManifest` | read | Validate manifest |
| `com.etzhayyim.actor.compileBpmn` | read | BPMN XML → manifest |
| `com.etzhayyim.actor.deployProcess` | write | compile + register |
| `com.etzhayyim.actor.migrateToManifest` | write | Batch T1 stub migration |
| `com.etzhayyim.dmn.evaluate` | write | DMN decision eval |
| `com.etzhayyim.form.submit` | write | UserTask form submit |

## WIT Contract

**Package**: `magatama:actor-executor@1.0.0`
**Source**: `00-contracts/wit/deps/magatama-actor-executor/package.wit`

3 interfaces: `primitives` (12 functions), `executor` (4 functions), `sandbox` (1 function).

## Shannon Analysis

Parquet snapshots: `80-data/shannon/snapshots/`

| Snapshot | Content |
|---|---|
| `snap-20260408-actor-exec-patterns.parquet` | 6-pattern comparison (P1-P5, P5+P3) |
| `snap-20260408-app-tier-classification.parquet` | 397 apps → T1/T2/T3 classification |
| `snap-20260408-bpmn-actor-design.parquet` | JSON vs BPMN vs BPMN+AI design comparison |

## Graph Persistence (RisingWave)

**All actor data is graph-persistent.** Filesystem scaffold/code-less files deleted after completeness proof.

### Graph Labels

| Label | Table | Rows | Content |
|---|---|---|---|
| `Actor` | `graphar.vertex_actor` | 1,732 | DID, handle, displayName, status, executionTier |
| `ActorManifest` | `graphar.vertex_actor_manifest` | 0 (ready) | pipeline steps, capabilities, bpmnXml, dmnXml, formSchemas |
| `Tool` | `graphar.vertex_tool` | — | MCP tool definitions |
| `ToolGrant` | `graphar.vertex_toolgrant` | — | actor → tool access |
| `FormTask` | `graphar.vertex_formtask` | — | UserTask pending/submitted |
| `OcelEvent` | `graphar.vertex_ocelevent` | — | pipeline execution events |

### Source Preservation in Graph

BPMN/DMN/Form sources are stored in `ActorManifest.val` (JSON):

| Source | Location in manifest | Round-trip |
|---|---|---|
| BPMN XML | `val.bpmnXml` | `compileBpmn` → `registerManifest` → `getManifest` |
| DMN XML | `val.dmnXml` | same |
| Form schemas | `val.formSchemas` | same |
| T2 handler source | `val.pipelines[].steps[].handler` | same |

### Completeness Proof (2026-04-09)

```
Filesystem unique DIDs: 1,096
Graph Actor rows:       1,732 (includes per-component DIDs)
Missing (fs - graph):   0
Proof:                  filesystem ⊆ graph = PASS
```

### Scaffold Deletion

| Item | Before | After | Proof |
|---|---|---|---|
| `app.ts` scaffold (< 500 LOC) | 314 | 0 (deleted) | graph Actor T1 node exists |
| Code-less wasm dirs | 1,390 | 0 (deleted) | graph Actor T1 node exists |
| `.etzhayyim-deploy/` git tracked | 1,660 | 0 (gitignored) | deploy artifact, not source |
| Real `app.ts` (>= 500 LOC) | 37 | 37 (preserved) | T3 dedicated Worker |
| Remaining wasm dirs | — | 351 | T3 + WIT contracts |

## Files

| File | Purpose |
|---|---|
| `00-contracts/wit/deps/magatama-actor-executor/package.wit` | WIT contract |
| `50-infra/.../pds/src/actor-manifest.ts` | Schema + validation |
| `50-infra/.../pds/src/actor-executor-primitives.ts` | 12 MCP primitive dispatch |
| `50-infra/.../pds/src/actor-executor-shared.ts` | T1 executor + XRPC handlers |
| `50-infra/.../pds/src/actor-executor-do.ts` | T2 DO sandbox + cron alarm |
| `50-infra/.../pds/src/actor-executor-triggers.ts` | subscribeRepos + cron triggers |
| `50-infra/.../pds/src/actor-executor-migrate-t1.ts` | T1 stub batch migration |
| `50-infra/.../pds/src/actor-executor-ocel.ts` | OCEL 2.0 event logging |
| `50-infra/.../pds/src/bpmn-pipeline-compiler.ts` | BPMN XML → manifest compiler |
| `60-apps/.../yoro/.../actor-designer/+page.svelte` | Visual BPMN/DMN/Forms editor |
