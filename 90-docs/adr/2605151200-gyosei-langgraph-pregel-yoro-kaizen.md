---
id: adr-2605151200-gyosei-langgraph-pregel-yoro-kaizen
title: Gyosei Fractal Pregel, Yoro Integration, and Kaizen Architecture
status: active
doc_type: adr
topic: gyosei-langgraph
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - gyosei-pregel-architecture
  - yoro-gyosei-integration
---

# ADR: Gyosei Fractal Pregel, Yoro Integration, and Kaizen Architecture

## Date
2026-05-15

## Status
Accepted

## Context
The `gov` and `state` actors require a scalable mechanism to discover and track the organizational structures and administrative procedures of over 140 countries. Additionally, these administrative procedures must be actionable by external users (citizens/businesses) and continuously monitored for compliance with real-world changes.

The existing infrastructure relied on static BPMN task definitions (`xrpc.com.etzhayyim.govXXX.*`) which did not scale gracefully to hierarchical agency discovery, nor did they natively support conversational intake or continuous improvement (Kaizen) loops for the legal schemas.

## Decisions

1. **Fractal Pregel Orchestrator (`gov-fractal-pregel`)**
   - Implemented a Map-Reduce and Iterative BFS architecture using LangGraph's Send API.
   - Replaced legacy BPMN tasks with a unified `generic.langgraph.run` dispatcher targeting the LangGraph server.
   - Allows dynamic, recursive discovery of sub-agencies and dependencies mapped back to Kotoba/Datomic (`vertex_gov_org`, `govOrgSiteDep`).

2. **Conversational Intake & Internal Processing (`gyosei-procedure-pregel`)**
   - **Yoro Integration**: Designed an intake agent (`gyosei-intake-agent`) to process user messages/mentions from the `yoro.etzhayyim.com` social feed, identify intents, and draft procedures (`com.etzhayyim.apps.gyosei.startProcedure`, `submitDraft`).
   - **Back-office Workflow**: Designed an internal agent (`gyosei-internal-processing`) to validate submitted schemas against `governanceContract`, route for Human-in-the-loop (HAR) or automated review, and notify the user via Yoro DM.
   - Enhanced `vertex_gov_org` to include `address`, `phone`, and `email` to route procedures correctly.

3. **Continuous Evaluation Loop (`gyosei-procedure-kaizen-pregel`)**
   - Implemented an autonomous quality assurance graph that periodically compares the etzhayyim modeled schema (`current_schema`) against real-world scraped texts (`official_source_data`).
   - If discrepancies (gaps) are detected (e.g., score < 100), the LLM generates JSON-Patch directives.
   - Outputs are persisted to a new `com.etzhayyim.apps.gyosei.kaizenReport` lexicon record for audit and application.

4. **Graph as Data — `py_factory` kind**
   - Adhering strictly to ADR-2605082000, all new graphs (`gov-fractal-pregel`, `gyosei-intake-agent`, `gyosei-internal-processing`, `gyosei-procedure-kaizen-pregel`, `gyosei-procedure-pregel`) are registered via Alembic into `vertex_langgraph_assistant` (kind=`'py_factory'`) and `vertex_langgraph_deployment`.
   - `py_factory` references a `factory_path` (e.g. `kotodama.agents.gov_pregel`) whose `build_graph()` callable returns a compiled `CompiledStateGraph`. No `vertex_langgraph_node_binding` rows are required.
   - Node implementations are purely functional Python mapping to MCP tool calls, executed on dedicated Kubernetes pools (`lg-gov`, `lg-gyosei`).
   - Alembic seeds: `20260515_0001` (gov-fractal-pregel), `20260515_0002` (gyosei-procedure-pregel), `20260515_0003` (gyosei-intake-agent + gyosei-internal-processing), `20260515_0004` (gyosei-procedure-kaizen-pregel).

5. **Deployment Infrastructure (`Dockerfile.lg`, Helm unpark)**
   - `40-engine/kotoba/crates/kotoba-kotodama/py/Dockerfile.lg` created as the canonical lightweight build target for both `ghcr.io/etzhayyim/lg-gov:latest` and `ghcr.io/etzhayyim/lg-gyosei:latest` (python:3.11-slim-bookworm, libpq5, uv install, uv stripped post-install).
   - `langgraph_server_app.py` `/health` alias added (stacked above `/healthz`) to satisfy Helm liveness/readiness probes which target `/health`.
   - `lg-gov-raw` and `lg-gyosei-raw` Helm deployments unparked: `replicas: 0 → 1`, `state: parked` label removed from helmfile.yaml.
   - **Operator steps pending**: `docker buildx build --builder etzhayyim-vke` for both images → `helmfile sync -l pool=gov` → `helmfile sync -l pool=gyosei` → `alembic upgrade head` against prod Kotoba/Datomic.

## Consequences
- **Positive:** Massive reduction in BPMN boilerplate (840 files updated). Seamless end-to-end integration from policy discovery to citizen social interaction to procedure execution. Autonomous self-healing schemas reduce maintenance overhead.
- **Negative/Risk:** High reliance on the LangGraph Checkpointer (`rw_vertex` mode) in Kotoba/Datomic for state persistence across thousands of parallel procedure threads. Requires careful monitoring of K8s cluster resources.
