---
id: adr-2604271600-projector-l7-langgraph-integration
title: "ADR: Projector L7 LangGraph Integration"
status: proposed
doc_type: adr
topic: projector-l7-langgraph
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - projector-langgraph-runtime
  - projector-bpmn-actor-l7
related:
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-0056-bpmn-as-actor
  - adr-0042
---

# ADR 2604271600 — Projector L7 LangGraph Integration

**Status**: proposed (Phase 1+2 scaffolded; Phase 3 implemented behind `PROJECTOR_USE_BPMN` flag, default off; Phase 4-5 pending)
**Date**: 2026-04-27
**Supersedes (partially)**: ADR-0042 §D3 projector reasoning surface
**Amends**: ADR-0056 (BPMN-as-actor) — adds projector to the canonical
deployable list of L7 actors
**Relates**: ADR-2604251830 (8-Layer Shannon-Optimal Architecture),
ADR-2604240946 (yoro autonomous BPMN cadence), ADR-0046 (triple-witness),
ADR-0049 (pyzeebe in-cluster worker), ADR-0023 (auth Shannon-optimal)

## Context

The yoro `/projects` projector (`com.etzhayyim.projector.*`) currently runs
as a co-located handler inside the PDS CF Worker
(`50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/`). Reasoning
loops (Chain-of-Thought, Tree-of-Thoughts, Self-Consistency, Reflexion)
and PM tool calling (`pm.search_agents`, `pm.web_research`,
`pm.create_entity_did`, `pm.graph_search`, `pm.invite_agent`) are all
implemented in TypeScript, dispatched from a single
`sendProjectMessage` XRPC handler.

This held while the surface was small, but three pressures have
compounded:

1. **CF Worker 30s / 128MB ceiling** — multi-iteration ReAct loops,
   N-path Self-Consistency sampling, and ToT branch evaluation
   regularly approach the limit. Cold-start `1101` events on the
   PDS Worker were already a known recovery path (ADR-0041); adding
   long projector runs increases the blast radius.
2. **No durable orchestration** — there is no resumable run state.
   If the LLM gateway returns an error mid-loop, the entire chain is
   lost. ADR-0056 already established `vertex_bpmn_process_def` +
   `vertex_bpmn_lexicon_binding` + Zeebe + pyzeebe for exactly this,
   but projector reasoning was not yet ported.
3. **Reasoning surface drift from the rest of the platform** —
   shinka heartbeat (Phase Z-α), gameka studio, mangaka, and most
   recent T1 actors all live as LangGraph state graphs invoked from
   pyzeebe primitives. The projector handler was the last large
   in-Worker reasoning surface.

The user has explicitly requested: 「推論なども zeebe, pyzeebe,
langgraph, langchain で設計統合」(integrate reasoning itself into
Zeebe + pyzeebe + LangGraph + LangChain).

## Decision

Migrate the projector reasoning + tool-calling surface from CF Worker
TypeScript to **L7 BPMN-as-actor** with **LangGraph state machines**
inside **pyzeebe primitives**, retaining LangChain message envelopes
for typed system/user/tool transitions. CF Worker remains as L3
dispatcher (XRPC accept → Zeebe message publish → 202 Accepted),
matching the canonical 8-layer Shannon-optimal topology
(ADR-2604251830).

### Layer responsibilities (after cutover)

| Layer | Component | Responsibility |
|---|---|---|
| **L3 Dispatcher** | `pds-handlers-etzhayyim.ts handleSendProjectMessage` | XRPC accept, viewer DID resolution, `sdk.zeebe.publishMessage(name="com.etzhayyim.apps.projector.sendProjectMessage", correlationKey=convoId, variables)`. Returns 202 + convoId. **No reasoning, no tool dispatch.** |
| **L7 Orchestration** | Zeebe (Vultr k8s) | XOR command routing, sub-process call activities, retry, OCEL audit emission, guardrail boundary events. |
| **L7 pyzeebe** | `pymagatama.primitives.projector.*` | LangGraph StateGraph entries: ReAct (`projector.agent.loop`), ToT (`projector.tot.expand`), Self-Consistency (`projector.sc.parallel`), Reflexion R/W (`projector.reflexion.{load,write}`), MCP discovery (`projector.tools.discover`), persist (`projector.persist.message`), command parser (`projector.command.parse`). |
| **L4 Registry** | RisingWave PG | `vertex_bpmn_process_def` × 4 + `vertex_bpmn_lexicon_binding` × 4 (this ADR's seed migration). `vertex_projector_reflection` for episodic memory. `vertex_repo_record` for projector replies (graph-visible to existing yoro UI fetch path). |
| **L8 Tool Pods** | (Phase 3 only) site.etzhayyim.com pod | `pm.web_research` HTTP fetch — not in Phase 1+2. |

### BPMN process graph

```
com.etzhayyim.apps.projector.sendProjectMessage  (root, message-start)
  │
  ├─ Task_ParseCommand        (projector.command.parse)
  │
  └─ Gateway_Command  (XOR by leading slash)
       ├─ /explore     → Call_TreeOfThoughts   → Task_PersistReply
       ├─ /consistent  → Call_SelfConsistency  → Task_PersistReply
       ├─ /reflect     → Task_ReflexionWrite   → Task_PersistReply
       ├─ /image       → Task_DeferImage       → Task_PersistReply  (CF direct, Phase 3)
       ├─ /think       → Task_DeferThink       → Task_PersistReply  (CF direct, Phase 3)
       └─ default      → Call_AgentLoop        → Task_PersistReply

com.etzhayyim.apps.projector.agentLoop  (sub-process)
  │
  ├─ Task_ReflexionLoad   (projector.reflexion.load)
  ├─ Task_LoadHistory     (generic.db.select on vertex_repo_record)
  ├─ Task_DiscoverTools   (projector.tools.discover)
  └─ Task_AgentLoop       (projector.agent.loop, LangGraph ReAct)
        ⊥ BE_GuardrailDenied → EndDenied  (boundary error: agent.guardrail.denied)

com.etzhayyim.apps.projector.treeOfThoughts  (sub-process)
  └─ Task_TotExpand       (projector.tot.expand, LangGraph ToT)

com.etzhayyim.apps.projector.selfConsistency (sub-process)
  └─ Task_ScParallel      (projector.sc.parallel, asyncio.gather + Counter)
```

### LangGraph state machines (per primitive)

#### `projector.agent.loop` — ReAct + CoT + Reflexion injection

```
StateGraph:
  reason  ─(tool-call detected)─→  guardrail
  reason  ─(final answer / max iters)─→  END
  guardrail  ─(allow)─→  dispatch
  guardrail  ─(deny)─→  END  (raises agent.guardrail.denied)
  dispatch ─→  reason
```

- `_AgentState` carries `messages[]`, `reflexionMemory[]`, `historyRows[]`,
  `memberTools[]`, `toolsCalled[]`, `iterations`, `reasoning`, `reply`,
  `done`, `guardrail`.
- System prompt embeds Reflexion memory (max 5 lessons), tool catalog,
  CoT instruction (`<reasoning>…</reasoning>`), tool-call grammar
  (`[TOOL_CALL: name({json})]`), and final-answer grammar
  (`<answer>…</answer>`).
- LLM transport = `pymagatama.llm.call_tier` (Vultr Serverless +
  RunPod fallback per ADR-2604231328). LangChain `ChatOpenAI` is
  intentionally NOT used — adding `langchain-openai` would double
  the pyzeebe worker image. We compose with LangChain at the message-
  envelope level only (transitively available via `langgraph` 0.2 →
  `langchain-core` >= 0.3).
- Guardrail node implements Camunda agentic pattern #4
  (`agent.guardrail.denied` OCEL). Conservative deny-list for
  Phase 1+2; richer DMN rule sets land in Phase 5.

#### `projector.tot.expand` — Tree of Thoughts

`expand → evaluate → finalize`. Three sequential LLM calls:
1. Expand: generate N=4 distinct approaches (JSON output).
2. Evaluate: score each 0-10 (JSON output).
3. Finalize: write the concise reply from the best-scored approach.

Returns `{reply, approaches[], scores[], bestIndex}`. BPMN ioMapping
splices everything back into process variables for OCEL audit.

#### `projector.sc.parallel` — Self-Consistency

`asyncio.gather(_sc_one_path × N)` at temperature 0.7. Each path
emits `<reasoning>` + `<answer>`; we extract the answer block,
normalise, and run `Counter.most_common`. Reply includes the winning
answer plus `(self-consistency: N/M paths agreed)` summary.

#### `projector.reflexion.{load,write}` — Episodic memory

- `load` reads up to 5 most recent rows from `vertex_projector_reflection`
  (existing table per `30-graph/graph-schema/migrations/
  20260421010000_vertex_projector_reflection.ts`).
- `write` parses `attempt | outcome | lesson` shape (or free-text)
  from `/reflect` argText; falls back to `vertex_repo_record` if
  the dedicated table is absent on this cluster.

### Reply surface

`projector.persist.message` writes the projector's reply to
`vertex_repo_record` under `collection=com.etzhayyim.convo.message`,
`repo=did:web:ops.etzhayyim.com` (PM agent DID). yoro's existing
`loadProjectChat` graph SQL query already reads this surface, so
the UI sees BPMN-produced replies with no client-side change.

This is the same C-path workaround documented in ADR-2604240946:
PDS XRPC writes from pyzeebe pods hit 401 (CF WAF strips
`x-magatama-verified` on `com.atproto.repo.createRecord` writes from
external IPs). Going direct to `vertex_repo_record` keeps the row
graph-visible without minting a Service Auth JWT in pyzeebe (Phase 3
will add the JWT path so projector replies federate into the AT
Protocol firehose).

## Implementation phases

| Phase | Status | Scope |
|---|---|---|
| **Phase 1** | ✅ Scaffolded | 4 BPMN files, `pymagatama.primitives.projector` module with LangGraph ReAct, Reflexion, history loader, tool discovery, persist primitive. Migration `20260427160000_seed_projector_bpmn_actors.ts` registers `process_def` + `lexicon_binding`. Worker registration in `zeebe_worker_main.py`. |
| **Phase 2** | ✅ Scaffolded | Tree-of-Thoughts (`projector.tot.expand`) and Self-Consistency (`projector.sc.parallel`) implementations, `treeOfThoughts.bpmn` + `selfConsistency.bpmn`, XOR routing in `sendProjectMessage.bpmn`. |
| **Phase 3** | ✅ implemented (flag-gated, default off) | (a) CF Worker `handleSendProjectMessage` now branches on `env.PROJECTOR_USE_BPMN`: when `1`/`true`, it `waitUntil(fetch(dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.projector.sendProjectMessage))` and returns `202 + {convoId, backend:"bpmn"}`. (b) yoro Worker exposes `GET /sse/projects/{convoId}` (90s server budget, auto-reconnect) — Server-Sent Events stream of new `vertex_repo_record` rows scoped to that convoId. (c) `/projects/[projectId]/+page.svelte` opens `EventSource` on `initProjectChat`, dedups by rkey, appends BPMN replies as they land. (d) `projector.persist.message` honours `PROJECTOR_PERSIST_VIA_PDS=1` to route the reply through `generic.pds.dispatch` (HMAC-mint Service Auth) so it federates; default = direct `vertex_repo_record` INSERT (graph-visible, non-federable). (e) `projector.auth.mint` task type exposes the existing `_mint_pds_service_auth(lxm)` helper to BPMN flows so PM tools can splice a Bearer for downstream `generic.http.fetch` / `generic.pds.dispatch` without 401. `/image` and `/think` slash commands stay on the deferred shim (BPMN-side reply text) — moving them to dedicated `imageGen.bpmn` / `deepReason.bpmn` sub-processes is deferred to Phase 5. |
| **Phase 4** | pending | Delete the obsolete TS reasoning code from `pds-handlers-etzhayyim.ts` (≈ 1500 LoC), keep PDS-bound writes (`branchConvo`, `addReflection`, `newProjectConvo` metadata) in TS. CF Worker bundle size measurement target: −30%. |
| **Phase 5** | pending | DMN guardrail rules (richer policy beyond the Phase 1 deny-list), per-tool RACI binding in `vertex_bpmn_lexicon_binding.governance_json`, A/B vs CF Worker direct path on a 5% canary cohort. |

## Consequences

### Pros

- **30s / 128MB ceiling lifted.** Multi-step ReAct, ToT × 4 branches,
  SC × 5 paths all run inside the pyzeebe pod with no CF time pressure.
- **Resumable runs.** Zeebe checkpoints flow position to PG metastore;
  primitive crashes mid-loop trigger Zeebe retry rather than losing
  the entire conversation context.
- **Durable audit.** Every BPMN service task → OCEL event in
  `com.etzhayyim.apqc.apqcEvent` via the Kyber projector pipeline
  (ADR-0025), so projector reasoning is now first-class auditable.
- **Reuse.** ToT, SC, Reflexion, agent loop are surfaceable as
  primitives any other BPMN can `Call_*` — gameka, mangaka, oshikatsu,
  6ir, briefing each gain access to projector reasoning patterns
  without TS code duplication.
- **Triple-witness alignment.** ADR-0046's three-way invariant
  (Zeebe job log ↔ `vertex_bpmn_*` row ↔ OCEL event) extends to
  projector flows for free.

### Cons / risks

- **Latency increase on the warm path.** CF Worker direct can return
  a one-shot LLM reply in 1.5-3s; the BPMN path adds Zeebe message
  publish + activate + complete round-trips (~150-400ms overhead at
  current Vultr cluster RTT). Mitigation: BPMN `resultTimeoutMs` lets
  short flows return synchronously to the message-publisher; the CF
  Worker decides between sync wait vs 202 Accepted based on expected
  latency tier.
- **PDS write 401 from external IP.** Documented in ADR-2604240946.
  Phase 3 must mint ES256 Service Auth JWT (lxm-scoped, 60s TTL) so
  pyzeebe primitives can call `com.atproto.repo.createRecord` for
  federation. Until then, projector replies live in the graph but
  don't enter the AT firehose.
- **Worker image size.** LangGraph + transitively `langchain-core`
  add ~120 MB to the pyzeebe image. Acceptable for a single shared
  worker pool (already loaded for shinka), but the image is now
  > 1.4 GB. Future split (per-actor worker pods) tracked under
  `[[migrations]] zeebe-worker-pool-split-2026-Q3`.
- **Two reply surfaces during Phase 1-3 coexistence.** Until Phase 4
  retires the TS path, both can write `vertex_repo_record` rows for
  the same `convoId`. Mitigation: Phase 1 BPMN seed is created with
  `status='active'` but not yet referenced by the CF Worker's
  XRPC handler — handler still owns reply writes. Cutover is a
  single CF Worker deploy, not a gradual one.

### Migration plan (idempotent)

1. **Apply migration** `20260427160000_seed_projector_bpmn_actors.ts`
   on staging via `pnpm db:migrate latest` (or
   `30-graph/graph-schema/scripts/apply-pending.sh` per
   ADR-2604241342 if pnpm path hits the known kysely+RW corruption).
2. **F5 watcher** in `dispatcher.etzhayyim.com:8080` picks up the 4 new
   `vertex_bpmn_process_def` rows within 30s and deploys to Zeebe.
3. **Smoke**: `curl -X POST http://dispatcher.etzhayyim.com:8080/xrpc/
   com.etzhayyim.apps.projector.sendProjectMessage -d '{"convoId":"…",
   "text":"hello","callerDid":"did:web:…"}'`. Expect 202 + a new
   `vertex_repo_record` row for the projector reply within 10s.
4. **Phase 3 cutover** (this ADR's Phase 3 row, now ✅):
   - Flip `PROJECTOR_USE_BPMN=1` env on the PDS Worker (`atproto.etzhayyim.com`);
     `handleSendProjectMessage` then delegates to Zeebe via
     `dispatcher.etzhayyim.com:8080` and returns 202 + convoId.
   - (Optional) `PROJECTOR_PERSIST_VIA_PDS=1` env on the pyzeebe pod
     so projector replies enter the AT firehose. Default off keeps
     replies graph-visible-only.
   - yoro Worker auto-exposes `/sse/projects/{convoId}`; no separate
     toggle. Browsers without `EventSource` fall back to the existing
     `loadProjectChat` poll on focus (no UI regression).
5. **Rollback**: `unset PROJECTOR_USE_BPMN` (or set to `0`) and re-deploy
   the PDS Worker; the handler reverts to the inline TS reasoning path
   on the next request. The yoro `/sse/projects/*` route can stay live
   (it's read-only against `vertex_repo_record`); SSE just goes idle
   when no BPMN replies arrive. The migration's `down()` removes the
   4 BPMN rows and the F5 watcher un-deploys from Zeebe within 30s.
   Zero behavior change for any deployed app while the flag is off.

## Open follow-ups

- ~~**SSE / poll surface for async replies.**~~ ✅ Phase 3 ships
  `GET /sse/projects/{convoId}` on the yoro Worker (90s server budget,
  auto-reconnect from the client). `loadProjectChat` poll remains as
  the no-EventSource fallback.
- **BPMN authorship UX.** All 4 process definitions are hand-written
  XML. ADR-0042 §D3 hinted at a future BPMN.io-based editor; once
  that lands, projector becomes the canary for visual editing.
- **Cross-actor BPMN reuse.** If projector's `treeOfThoughts.bpmn`
  proves useful, generalize it to `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/reasoning/`
  and expose as `com.etzhayyim.reasoning.tot` / `com.etzhayyim.reasoning.sc` so
  any actor BPMN can `Call_*` it without per-actor copies.

## Files changed

### Phase 1+2 (scaffold)

| Path | Type |
|---|---|
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/projector/sendProjectMessage.bpmn` | new |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/projector/agentLoop.bpmn` | new |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/projector/treeOfThoughts.bpmn` | new |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/projector/selfConsistency.bpmn` | new |
| `20-actors/magatama/py/src/pymagatama/primitives/projector.py` | new |
| `20-actors/magatama/py/src/pymagatama/zeebe_worker_main.py` | edit (1 line: register projector) |
| `30-graph/graph-schema/migrations/20260427160000_seed_projector_bpmn_actors.ts` | new |
| `60-apps/etzhayyim-project-projector/CLAUDE.md` | edit (L7 LangGraph Migration section) |
| `90-docs/adr/2604271600-projector-l7-langgraph-integration.md` | new (this file) |

### Phase 3 (flag-gated cutover, default off)

| Path | Type |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | edit (early-return BPMN delegate when `PROJECTOR_USE_BPMN=1`) |
| `20-actors/magatama/py/src/pymagatama/primitives/projector.py` | edit (`PROJECTOR_PERSIST_VIA_PDS` branch in `task_projector_persist_message` + new `task_projector_auth_mint` task type) |
| `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts` | edit (new `GET /sse/projects/:convoId` route, 90s budget, vertex_repo_record poll) |
| `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/projects/[projectId]/+page.svelte` | edit (`EventSource` consumer, dedup by rkey, auto-reconnect, `onDestroy` cleanup) |

Phase 3 leaves the inline TS reasoning path in place; the flag is the
only behavior switch. Phase 4 deletes the obsolete TS surface
(`handleSendProjectMessage` reasoning loop, ~1500 LoC) once Phase 3
canary monitoring closes clean.
