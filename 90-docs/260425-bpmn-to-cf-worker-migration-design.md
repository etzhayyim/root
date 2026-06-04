# BPMN → CF Worker Migration Design (defence cluster)

**Status**: Draft 2026-04-25
**Scope**: 105 defence BPMN process definitions (Wave 1–5) currently dispatched by `bpmn-dispatcher` → Zeebe → `pyzeebe` worker pool.
**Goal**: split per-actor scope cleanly, reduce always-on cost, and align with the etzhayyim app actor pattern that ADR-0036 / ADR-0022 already use elsewhere.

## 1. Why migrate

The current pipeline:

```
PDS (XRPC pipethrough) → bpmn-dispatcher pod (admin trust) → Zeebe broker
                                                              ↓
                                                       pyzeebe worker pool
                                                       (root psycopg, can write any RW table)
                                                              ↓
                                                       vertex_open_defence_event
```

Three structural issues:

1. **Authority scope** — `pyzeebe` holds a single root credential. The `generic.db.insert` task accepts any `table` name; only the format regex (`vertex_*|edge_*|mv_*`) is enforced. Wave-5 onward we added an explicit `write_table_allowlist` per binding (mig 20260425160000), which closes the worst hole, but the credential itself is still root.
2. **Identity collapse** — 105 distinct `did:web:open-{project}.etzhayyim.com:ops` owners share one execution pool. The owner_did column is a label, not an enforcement boundary.
3. **Idle floor** — `pyzeebe` and `bpmn-dispatcher` are always-on. With 105 stub BPMNs that each do `start → db.insert → audit.emit → end` (linear, ~50 ms work), the orchestration overhead is essentially zero work, but we pay for two persistent pods.

CF Worker pattern (etzhayyim app actor T3) is the inverse: per-DID isolate, Service Auth scoped to that NSID, scale-to-zero between requests.

## 2. Migration target

For each of the 105 defence BPMNs:

```
PDS (XRPC) → CF Worker (per-actor DID, Service Auth scoped)
                ↓ Hyperdrive
             RisingWave (vertex_open_defence_event INSERT, then audit emit)
```

Result:
- 0 BPMN orchestration calls for these stubs
- 0 always-on pods touched on the request path
- per-actor credential isolation by construction (CF Worker holds only its own actor signing key)

## 3. Which BPMNs migrate

Heuristic: any BPMN with the shape `start → 1 ServiceTask of type generic.db.insert → 1 ServiceTask of type generic.audit.emit → end`, **no gateway, no parallelism, no error compensation**, qualifies. All 105 defence stubs match.

BPMNs that **stay** in the orchestration layer (out of scope here, kept for orchestration work that genuinely needs it):
- multi-step approvals (Wave 1 originally had `requirePublicNotice` gateway; we removed it for stubs but real ops will reintroduce)
- parallel ServiceTask fan-out (compensation, retry, manual user task)
- timer-start (`R/PT15M` cron-style) — these are the BPMN-as-cron pattern in ADR-0056

## 4. Code generation

The 105 BPMNs were generated from a 9-column TSV (`project|proc|nsidNs|bpmnId|jpName|actionName|fields|subjectField|severity[|extraColumns]`). The same TSV produces a CF Worker:

```typescript
// 60-apps/etzhayyim-project-open-{project}/appview/.../src/app.ts
import { createWorkerExport, nsid, parseLexiconInput, type LexiconOutput }
  from "@etzhayyim/magatama-host-sdk";
import { createKyselyDb } from "@etzhayyim/magatama-host-sdk";
import type { Database } from "@etzhayyim/graph-schema";

export default createWorkerExport((sdk) => {
  sdk.app.command(
    nsid("com.etzhayyim.apps.{nsidNs}.{proc}"),
    async (ctx, body) => {
      const input = parseLexiconInput("com.etzhayyim.apps.{nsidNs}.{proc}", body);
      const db = createKyselyDb<Database>(ctx.env.HYPERDRIVE);
      await db.insertInto("vertex_open_defence_event")
        .values({
          vertex_id: input.vertexId,
          owner_did: ctx.callerDid,
          bpmn_process_id: "{bpmnId}",   // historical key, kept for compatibility
          nsid: "com.etzhayyim.apps.{nsidNs}.{proc}",
          project: "{project}",
          subject_vid: input.{subjectField} ?? null,
          action_class: "{actionName}",
          severity: "{severity}",
          detected_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          // ...extra typed columns from extraColumns mapping
          sensitivity_ord: 1,
          org_id: ctx.callerDid,
          user_id: ctx.callerDid,
          actor_id: "open-defence.{project}",
        })
        .execute();
      sdk.audit.success("{actionName}", input.vertexId);
      return JSON.stringify({ ok: true } satisfies LexiconOutput<"...">);
    },
    asAgentTool("{description}"),
  );
});
```

This is mechanical. A single generator script in `70-tools/scripts/contract/gen-defence-cfworker.mjs` reads the TSV and emits 105 `app.ts` files plus `magatama.jsonld` per project.

## 5. Project shape

105 NSIDs are spread across **50+ open-* projects**. Most projects already exist (we added their lexicons in waves 1–5). The migration only **adds** an `app.ts` command per existing project, not new projects.

For projects that don't have a deployed CF Worker yet (e.g. open-cyber-soc, open-redsea-incident, open-itu-spectrum), we need:
- `magatama.jsonld` (nanoid + name + description)
- `wrangler.jsonc` (compat date + binding for `HYPERDRIVE`)
- `src/app.ts`
- `etzhayyim deploy`

Estimate: 3 files per project × 50 projects = 150 files. All template-generated.

## 6. Auth & scope

Per ADR-0022 each CF Worker invocation receives a Service Auth JWT with `lxm = com.etzhayyim.apps.{ns}.{proc}` claim. The Worker:
- only accepts requests where the JWT `lxm` matches the called NSID (mismatched = 401)
- writes to `vertex_open_defence_event` via Hyperdrive — the Hyperdrive credential is per-Worker (not shared with pyzeebe)
- emits audit via the existing `sdk.audit` helper (PDS-routed)

Net effect: a Worker that gets a JWT for `screenSanctions` cannot perform `flagNuclearWeaponDiversion`'s write. Compare: today both share one pyzeebe pool with one psycopg credential.

## 7. BPMN binding row disposition

For each migrated NSID we have two options:

a. **Hard cutover**: delete the binding row + the process_def row. PDS pipethrough sees no binding for that NSID and falls back to the project's CF Worker route.
b. **Soft cutover**: leave the binding inactive (`status='inactive'`). Easier rollback, but every PDS pipethrough still does a binding lookup that misses.

Recommend (a) at the end, **after** the CF Worker has been deployed and verified. Sequence per NSID:

1. CF Worker deploy + smoke test
2. PDS routing config: prefer Worker, fall back to BPMN dispatcher (no-op since binding still present)
3. Burn-in 24h, watch error rate
4. `DELETE FROM vertex_bpmn_lexicon_binding WHERE nsid = $1` + `DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id = $2`
5. F5 watcher / Zeebe broker eventually GC the unused process

Step 2 is the only piece that requires PDS code change. The route-resolution order in `pds-handlers-etzhayyim.ts` already prefers static service binding over dispatcher; we just need the Worker to be reachable on that route.

## 8. Cost & scale impact

Today (defence cluster only):
- bpmn-dispatcher: 1 pod, 0.1 vCPU / 87 MiB → ~$5/mo
- pyzeebe worker (mitama-udf): 3 replicas, ~5 mCPU / 75 MiB each → ~$15/mo
- always-on regardless of traffic

After migration:
- 0 BPMN cost on defence path
- CF Worker request: $0.30 / 1M requests + $12.50 / 1M GB-s; defence stub is ~50 ms × ~50 MiB → effectively rounding error at any plausible volume
- Hyperdrive included
- Idle = $0

Other actors that genuinely need orchestration (timer-start crons, multi-step approvals) keep BPMN, but a smaller hot pool.

## 9. Risks & mitigations

| risk | mitigation |
|---|---|
| Worker cold start adds latency | CF Worker cold ~5 ms (V8 isolate); on first request after idle the Hyperdrive connection re-handshakes. For burst writes use `ctx.waitUntil` to avoid blocking response |
| Service Auth `lxm` mismatch breaks legacy callers | Phase 2 — start permissive (warn-only) for 48h before enforcing |
| binding `write_table_allowlist` and CF Worker drift | document the mapping in the same TSV so both stay in sync |
| audit emit semantics differ between BPMN audit task and `sdk.audit` | both write to the same `audit_event` graph; verify with a probe call after first deploy |

## 10. Sequence

1. **Phase 1 (today)** — `write_table_allowlist` enforcement on pyzeebe (mig 20260425160000) — done as a separate change. Closes the immediate root-credential exposure on existing 105 stubs.
2. **Phase 2** — generator script + 105 CF Worker `app.ts` + `etzhayyim deploy` for each project.
3. **Phase 3** — PDS routing prefers Worker; binding rows still present (soft cutover).
4. **Phase 4** — 48h burn-in.
5. **Phase 5** — delete BPMN process_def + binding rows; pyzeebe pool shrinks (KEDA scale-to-zero candidate, ADR-0049 follow-up).

Each phase is independently revertible.

## 11. Open questions

- Do we keep `bpmn_process_id` as a column on `vertex_open_defence_event` after migration? (Useful for historical join; harmless if we keep it.)
- Should the CF Worker generator emit a single Worker per project (multiplexes all NSIDs in that project) or one Worker per NSID? Recommend per-project: 50 Workers, not 105 — closer to existing T3 pattern.
- Do we need to migrate the typed columns (`subject_lei`, `subject_imo`, etc.) into a graph-edge model at the same time? Independent change; defer.

## 12. Out of scope

- Wave 4 timer-start BPMNs (none in defence cluster yet, but ADR-0056 §F5 covers them). Stay in BPMN.
- mitama-udf KEDA scale-to-zero (separate ADR-0049 follow-up).
- Any change to host capability lexicons. The Worker uses existing `host-client.ts` generated from `00-contracts/lexicons/com/etzhayyim/host/*.json`.
