# etzhayyim-project-open-isco

ISCO-08 occupation classification runtime.

## Active Runtime

- Orchestration: BPMN / LangServer under `orgs/etzhayyim/com-etzhayyim-isco/wire/open-isco/bpmn`
- Worker implementation: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_isco.py`
- SQL helpers: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/handlers/open_isco.py`
- Runtime pattern: LangServer + LangGraph + UDF

Standalone component execution is retired for open-isco. The legacy appview package has been archived under `_archive/retired-cf-workers/adr-2604282300/60-apps/etzhayyim-project-open-isco/appview/etzhayyim-legacy-isco-workforce-coordinator-wfc8k3n1`; new writes go through the LangServer/UDF runtime.

## Coverage

| Surface | Coverage |
|---|---:|
| BPMN processes | 2/2 |
| LangServer task handlers | 2/2 |
| UDF helpers | 3/3 |
| Legacy standalone runtime | retired |

## BPMN Processes

```text
openIsco.classifyWorker
openIsco.recordConcordance
```

Audit steps remain BPMN-level `generic.audit.emit` tasks.

## LangServer Tasks

| Task | Responsibility |
|---|---|
| `openIsco.classifyWorker` | Classify a worker DID to a 1-4 digit ISCO-08 occupation code, derive code level, write classification vertex and occupation edge |
| `openIsco.recordConcordance` | Record exact/broader/narrower/related occupation mappings to another taxonomy |

LangGraph is used as a checkpointable deterministic guard. The hot-path decision rule is:

| Confidence | Verification |
|---:|---|
| `>= 0.9` | `authoritative` |
| `>= 0.5` | `community` |
| `< 0.5` | `candidate` |

Code level is derived from code length:

| Length | Level |
|---:|---|
| 1 | `major` |
| 2 | `submajor` |
| 3 | `minor` |
| 4 | `unit` |

## UDF Helpers

```text
com.etzhayyim.apps.openIsco.codeLevel
com.etzhayyim.apps.openIsco.verificationForConfidence
com.etzhayyim.apps.openIsco.classificationVertexId
```

## Data Model

| Table | Writer |
|---|---|
| `vertex_open_isco_classification` | `openIsco.classifyWorker` |
| `edge_open_isco_classification_occ` | `openIsco.classifyWorker` |
| `vertex_open_isco_concordance` | `openIsco.recordConcordance` |

## Local Checks

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py
pytest -q tests/test_open_isic_apqc_primitives.py

cd ../../..
npm run lint:bpmn:manifest
npm run lint:bpmn:coverage
npm run lint:bpmn:worker-tasks
```
