---
id: adr-2605122100-artificial-organism-architecture
title: "Artificial Organism Architecture: LangGraph, PEGEL, LangProcessMiner, and Murakumo Fleet"
status: active
doc_type: adr
topic: artificial-organism
authoritative: true
last_verified: 2026-05-12
authoritative_paths:
  - 20-actors/magatama/py/src/pymagatama/malak/
  - 20-actors/magatama/py/src/pymagatama/keiei/
  - 20-actors/magatama/py/src/pymagatama/fleet/
  - 50-infra/k8s/murakumo-kubelet/
  - 30-graph/graph-schema/sql_migrations/20260512180000_langprocessminer_schema.up.sql
---

# ADR 2605122100: Artificial Organism Architecture

## 1. Context

Previous ADRs defined the conceptual elements of etzhayyim's autonomous systems: CXO roles (ADR 2605101200), the PEGEL evaluation loop for provenance (ADR 260509-pokopia), and the physical fleet infrastructure via Murakumo Virtual Kubelet (ADR 2605121700).

However, these were isolated concepts. The development iterations of `iter126` through `iter142+` (May 2026) have necessitated synthesizing these components into a unified, self-sustaining system. We needed to transition from running discrete, human-triggered Python scripts to a constantly vigilant, self-monitoring, and natively distributed ecosystem—effectively realizing the long-planned "Artificial Organism."

## 2. Decision

We formally declare the integration of the following systems as the realization of the **Artificial Organism Architecture**:

### A. Cellular Structure & Organs (Kubernetes Pods & Role Graphs)
Instead of monolithic applications, the organism is composed of specialized cells (LangGraph workflows) running as Kubernetes Pods via the `murakumo-kubelet`.
- **Malak Layer (Immune System):** Roles like `malak`, `honeypot-tracker`, `crypto-tracker`, and `sns-tracker` constantly ingest external threats (OSINT, spam) to protect the ecosystem.
- **Keiei Layer (Cerebral Cortex):** Shadow and primary roles (`ceo`, `cto`, `cfo`, `coo`, `clo`, `ciso`, `cdo`) provide strategic governance, budget gates, and legal constraints.
- **Fleet Layer (Motor Cortex):** Workloads like `web_crawler`, `maps_ingest`, and `3d_splat` execute heavy physical compute tasks across the Mac mini nodes.

### B. Autonomic Nervous System (Heartbeat Loop)
Instead of waiting for RPC calls, agents run an asynchronous `_heartbeat_loop()` (defined in `lsp_server.py` and `langgraph_worker.py`). This acts as the organism's pulse, waking up at fixed intervals (e.g., 10 seconds or 15 minutes) to autonomously pull from OSINT feeds (e.g., OpenPhish) or check internal status, ensuring continuous vigilance.

### C. Learning and Reasoning (PEGEL - Provenance Evidence Graph Evaluation Loop)
Inside each LangGraph, intelligence is not blindly trusted. The `pegel_evaluate_node` correlates incoming signals (e.g., an IP address from a honeypot) against the organism's long-term memory (the Kotoba/Datomic Graph DB). It calculates a `pegel_score` based on supporting/contradicting evidence before allowing the LLM to formulate a decision (`deliberate_node`).

### D. Memory and Homeostasis (Kotoba/Datomic & LangProcessMiner)
To avoid reliance on third-party SaaS (like LangSmith) and maintain full sovereignty over the organism's "thoughts," we implemented **LangProcessMiner**.
- A custom LangChain `BaseCallbackHandler` (`lpm_callback.py`) captures every node transition, LLM prompt, and token usage.
- This trace data is persisted natively into Kotoba/Datomic (`vertex_langprocessminer_trace` / `span`).
- A materialized view (`mv_lpm_agent_performance_summary`) provides real-time homeostasis metrics (error rates, latency, token burn), visible instantly on the local Yoro UI (`/lpm-dashboard`).

## 3. Rationale

- **Sovereignty:** By keeping tracing (LPM) and execution (Murakumo on Metal) entirely within our own network and databases, we secure our intelligence pipelines and avoid vendor lock-in for critical observability.
- **Resilience:** The combination of Kubernetes orchestration with independent, asynchronous agent heartbeats ensures that if one "cell" dies, K8s restarts it, and the organism continues functioning without human intervention.
- **Scalability:** The architecture maps perfectly to the 11-node wired Mac mini fleet. Adding more compute is as simple as powering on a node and letting the Virtual Kubelet schedule new Pods onto it.

## 4. Consequences

- **DB Dependency:** The Langservers now have a hard dependency on the Kotoba/Datomic cluster (`KOTOBA_URL`). If the internet or VPN connection to Vultr drops, the agents will degrade to fallback stubs (as designed).
- **Audit Completeness:** The organism leaves an immutable, cryptographically hashable trail of its entire reasoning process in the graph database, fulfilling the strict audit requirements of the Keiei (CXO) layer.
