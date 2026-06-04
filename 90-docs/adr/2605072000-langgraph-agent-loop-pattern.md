---
id: adr-2605072000-langgraph-agent-loop-pattern
title: "ADR-2605072000: LangGraph Agent Loop Pattern"
status: active
doc_type: adr
topic: langgraph-agent-loop-pattern
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - LangGraph agent loop usage within L3 actor runtime
related:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605072000
  - adr-2605080600-langgraph-server-granian-l3-runtime
supersedes: []
superseded_by: []
amended_by:
  - adr-2605080200-pydantic-l6-validation-contract
  - adr-2605080600-langgraph-server-granian-l3-runtime
---

# ADR-2605072000: LangGraph Agent Loop Pattern

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki
**Supersedes**: —
**Superseded by**: —

## Context

The etzhayyim platform needs multi-step AI agent loops where:
- Each step can call external tools (web scrape, LLM inference, RisingWave read/write)
- The full graph of steps has conditional branches (e.g., quality gate → retry or deliver)
- State must persist across steps within one "run" (proposal generation can take 30–120s)
- Human-in-the-loop approval can pause the graph at defined checkpoints

The existing PyZeebe pattern (`koke_worker_main.py`, `myco_yeast_worker_main.py`) handles:
- Durable BPMN orchestration with retries and timers
- Multi-actor fan-out / fan-in
- Long-running business processes (days/weeks)

It does **not** handle intra-step graph state. A `koke.classify_fixation` job is a single
coroutine that either completes or throws — no graph.

LangGraph fills the gap: it manages **state-machine transitions within one Zeebe job**,
giving each job its own typed state dict and a DAG of node functions.

## Decision

**Use LangGraph as the intra-job agent loop library when a Zeebe job has ≥ 3 LLM steps
with branching.** For ≤ 2 sequential LLM calls, plain async suffices.

## 2026-05-08 Amendment: Runtime Placement

ADR-2605080600 expands this pattern from "LangGraph inside a Zeebe job" to
"LangGraph Server as the main L3 actor runtime". The graph/state-machine
guidance in this ADR still applies, but new implementations should target
LangGraph Server + Granian with RisingWave checkpoint/store persistence.

BPMN-native flows should use ADR-2605081200 SpiffWorkflow BPMN workers instead
of wrapping every BPMN process as a LangGraph graph.

### Integration pattern

```
Zeebe BPMN process
  └─ ServiceTask  type="webmk.run_proposal_agent"
       └─ pyzeebe job handler
            └─ LangGraph.compile(checkpointer=None).invoke(state)
                 ├─ node: research_company      (Playwright scrape + LLM extract)
                 ├─ node: analyze_competitors   (common-crawl + LLM diff)
                 ├─ node: generate_strategy     (Claude claude-sonnet-4-6)
                 ├─ node: generate_copy         (Claude claude-sonnet-4-6)
                 ├─ node: quality_gate          (score ≥ 0.7 → deliver, else retry)
                 └─ node: store_proposal        (RisingWave INSERT)
```

PyZeebe owns **durability** (retries, timeouts, escalation). LangGraph owns **intra-run
state transitions**. The two layers do not overlap.

### Checkpointing

LangGraph checkpointer is **not used** (set to `None`). Durability comes from RisingWave
`vertex_*_proposal` rows written by the `store_proposal` node. If the Zeebe job fails, the
BPMN timer retries the whole job (idempotent on `proposalId`).

### Dependency

```toml
# 20-actors/magatama/py/pyproject.toml additions
langgraph = ">=0.2"
langchain-anthropic = ">=0.3"
resend = ">=2.0"
```

### When NOT to use LangGraph

| Scenario | Tool |
|---|---|
| Single LLM call in a Zeebe job | plain async + `llm.py` |
| Multi-actor fan-out over days | PyZeebe BPMN only |
| Streaming output to client | plain async + SSE |
| Batch classification (> 100 items) | Python async gather |

## Actors that use this pattern

| Actor | ADR | Worker file |
|---|---|---|
| webmk (Web Marketing Proposal) | this ADR | `webmk_worker_main.py` |

## Consequences

- New dependency: `langgraph`, `langchain-anthropic`, `resend` in pyproject.toml
- Worker startup time increases ~200ms (graph compilation on first run)
- LangGraph state dict is typed as `TypedDict` — schema changes require worker restart
- All LangGraph nodes must be idempotent (Zeebe job may retry the whole run)
