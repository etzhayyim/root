# ADR: Evolution to 1000 Cognitive Actors, Root Router, and IPFS Dashboard

**Date:** 2026-06-07
**Status:** Accepted
**Context:** Etz Hayyim Architecture (Clean Room Emulation & Cognitive Inference)

## 1. Context and Problem Statement
Following the successful generation of the first 600 Clean Room Actors (ADR-260607), we identified a need to push the boundaries of this ecosystem to 1000 platforms, fully encompassing the "long-tail" of dominant global infrastructure (Regional Super Apps, Legacy Mainframes, Vertical Monopolies, and Frontier Tech like BCI/SynBio). Furthermore, the breadth of 1000 actors necessitated a shift toward "depth": giving these actors reasoning capabilities (Cognitive Inference), orchestrating them via a single gateway, and visualizing their state.

## 2. Decision: 1000 Cognitive Actors
We generated Waves 7-10 to reach 1000 actors. We then executed a mass transformation (`cognitive_actor_injector.py`) to convert all 1000 actors from static CRUD APIs into **Cognitive Actors**.
* **Strict Compatibility:** The external API signature of every actor strictly matches its proprietary counterpart (e.g., Salesforce, Stripe, JohnDeere).
* **Internal LLM Reasoning:** The internal implementation feeds the payload into a LangGraph state machine. An embedded LLM parses intent, scores risk, and enriches data.
* **Immutable State:** The AI's reasoning path and the final state are transacted to Datomic.

## 3. Decision: The Root Router (Unified Gateway)
To orchestrate 1000 isolated WASM actors, we constructed the **Root Router** (`40-engine/root-router/src/main.py`).
* **Dynamic Routing:** Intercepts traffic at `/api/v1/{actor_name}/*` and proxies to the respective Py Kotodama WASM sandbox.
* **IPFS Gateway:** Serves pinned decentralized applications at `/ipfs/{cid}`.

## 4. Decision: World State Visualization (Chaos Monitor)
We built a real-time React/HTML dashboard (`60-apps/chaos-dashboard`) to visualize the 1000-node substrate topology and monitor faults injected by the `Chaos Simulator`.
* **IPFS Deployment:** Pinned to the local node (Simeon) with a generated CID.
* **Portal Integration:** Registered in the central `infra-actors.ts` registry as `chaos_monitor`. It is accessible via the app portal (`/apps`), direct CID (`/ipfs/{cid}`), and seamlessly embeds into ATProto profile pages.
* **Nomenclature:** Enforced the strict prohibition of the term "God" across the repository, ensuring all architecture aligns with the "Root/Core" structural philosophy.

## 5. Consequences
* **Positive:** We now possess a functional, 1000-platform digital twin of human civilization's software infrastructure. Every node is capable of dynamic LLM reasoning while maintaining legacy API compatibility.
* **Next Steps:** Proceed with rigorous load-testing of the Root Router using the Chaos Simulator, and begin integrating live LLM models into the Cognitive Actors' internal LangGraph workflows.
