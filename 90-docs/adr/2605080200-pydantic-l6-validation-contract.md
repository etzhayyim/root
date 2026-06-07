---
id: adr-2605080200-pydantic-l6-validation-contract
title: "ADR-2605080200: Pydantic v2 L6 Boundary Validation Contract"
status: active
doc_type: adr
topic: pydantic-l6-validation-contract
authoritative: true
last_verified: 2026-05-07
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "L6 入口/出口のバリデーション規約。PyZeebe job I/O / LangGraph state / Anthropic structured output の型安全を保証する"
authoritative_for:
  - Pydantic v2 usage at L6 compute boundaries
  - PyZeebe job input/output base classes (ZeebeJobInput / ZeebeJobOutput)
  - LangGraph graph state as Pydantic BaseModel (BaseModelState)
  - Anthropic structured output parsing (AnthropicStructuredOutput)
  - pydantic-settings for worker entrypoint env config
depends_on:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605072000-langgraph-agent-loop-pattern
related:
  - adr-2605080100-bonsai-growth-prune-model
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
amends:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605072000-langgraph-agent-loop-pattern
amended_by: []
supersedes: []
superseded_by: []
---

# ADR-2605080200: Pydantic v2 L6 Boundary Validation Contract

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki
**Amends**: ADR-2605080000, ADR-2605072000

## Context

ADR-2605080000 defines the 6-Layer Distributed Cognitive Actor System. L6 is the
compute/execution layer — PyZeebe workers, Kotoba/Datomic External Python UDF handlers,
LangGraph subgraphs, and Anthropic tool-use parsers all live here.

Until now, L6 code used ad-hoc `dict.get()` access on job variables and LLM
responses, creating three classes of failure:

1. **Silent type coercion** — a missing field returns `None` and propagates silently,
   causing incorrect DB writes that are hard to trace.
2. **No schema documentation** — the shape of a Zeebe job's `variables` dict is
   implicit in handler code and not machine-readable.
3. **LangGraph state drift** — `TypedDict` state and the graph's actual checkpoint
   schema diverge without compile-time or runtime detection.

Pydantic v2 (`pydantic>=2.7.0`) is already added to `pyproject.toml`.  This ADR
defines the canonical usage contract.

## Decision

### Rule 1: PyZeebe job I/O uses `ZeebeJobInput` / `ZeebeJobOutput`

```python
from pymagatama.primitives.pydantic_job import ZeebeJobInput, ZeebeJobOutput

class GrowthProposalInput(ZeebeJobInput):
    actor_did: str
    trigger_signal: str
    eta_at_birth: float

class GrowthProposalOutput(ZeebeJobOutput):
    proposed_did: str
    eta_score: float
    approved: bool = False

@worker.task(task_type="shinka.propose_growth")
async def propose_growth(job: Job) -> dict:
    inp = GrowthProposalInput.from_job(job)   # ← L6 entry boundary
    # ... compute ...
    return GrowthProposalOutput(
        proposed_did="did:plc:...",
        eta_score=0.72,
    ).to_variables()
```

`ZeebeJobInput.from_job()` raises `pydantic.ValidationError` on schema mismatch.
PyZeebe surfaces this as a BPMN incident, preserving field-level error detail in
the incident message — no silent failure.

`extra="ignore"` on `ZeebeJobInput` means unknown Zeebe variables pass through
without error, preserving forward compatibility as the process model evolves.

### Rule 2: LangGraph state uses `BaseModelState`

```python
from pymagatama.primitives.pydantic_job import BaseModelState

class ProposeState(BaseModelState):
    actor_did: str = ""
    eta_score: float = 0.0
    proposal_text: str = ""
    approved: bool = False

graph = StateGraph(ProposeState)
```

`BaseModelState` uses `extra="allow"` so LangGraph can inject internal keys
(e.g., `__start__`, `messages`) without raising.

### Rule 3: Anthropic tool_use / json-mode output uses `AnthropicStructuredOutput`

```python
from pymagatama.primitives.pydantic_job import AnthropicStructuredOutput

class EtaScoreResult(AnthropicStructuredOutput):
    eta: float
    reason: str

result = EtaScoreResult.from_tool_use(tool_block.input)
```

Use `safe_parse()` when a missing/malformed LLM response should degrade gracefully
rather than raise:

```python
result = EtaScoreResult.safe_parse(tool_block.input, default=EtaScoreResult(eta=0.0, reason="parse_failed"))
```

### Rule 4: Worker entrypoint config uses `pydantic-settings`

```python
from pydantic_settings import BaseSettings

class WorkerSettings(BaseSettings):
    rw_host: str = "localhost"
    rw_port: int = 4566
    zeebe_address: str = "zeebe:26500"

    model_config = {"env_prefix": "MAGATAMA_"}

settings = WorkerSettings()
```

`pydantic-settings` reads from env vars with the configured prefix.  No manual
`os.environ.get()` chains.

---

## File Location

```
20-actors/magatama/py/src/pymagatama/primitives/pydantic_job.py
```

Classes exported:
- `ZeebeJobInput`
- `ZeebeJobOutput`
- `BaseModelState`
- `AnthropicStructuredOutput`

---

## Design Principles

1. **L6 entry/exit boundaries are typed** — every Zeebe task handler and LLM
   response parser goes through a Pydantic model.
2. **Failures are loud** — `ValidationError` propagates to BPMN incident rather
   than silently producing wrong data.
3. **Extra fields are ignored** — Zeebe variables and LangGraph state may carry
   extra keys; `extra="ignore"` / `extra="allow"` preserves forward compatibility.
4. **No hand-rolled `dict.get()` chains** — use `ZeebeJobInput.from_job()` or
   `AnthropicStructuredOutput.from_tool_use()` at the boundary.

---

## Consequences

**Gained**:
- Schema documentation is co-located with handler code (model class = spec)
- BPMN incidents carry field-level validation errors (easy to diagnose)
- LangGraph state shape is machine-verifiable
- Worker env config is self-documenting via `BaseSettings`

**Constraints**:
- All new L6 handlers must subclass the appropriate base class
- Existing handlers should be migrated incrementally (no flag-day required)

---

## References

- ADR-2605080000: Distributed Cognitive Actor System (L6 layer definition)
- ADR-2605072000: LangGraph Agent Loop Pattern (LangGraph state usage)
- ADR-2605071200: Myco-Yeast Artificial Organism (PyZeebe worker registry)
- `20-actors/magatama/py/src/pymagatama/primitives/pydantic_job.py`
- `20-actors/magatama/py/pyproject.toml` (`pydantic>=2.7.0`, `pydantic-settings>=2.3.0`)
