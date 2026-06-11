# ADR-2605310200 — Automated LLM Migration Pipeline for LangGraph to Kotoba WASM

**Status**: Accepted
**Date**: 2026-05-31
**Owner**: etzhayyim core

Supersedes/extends: ADR-2605302355 (legal-services kotoba WASM in-node deployment)

## Context

Per ADR-2605302355, the `kotoba` substrate now supports invoking WASM components from Python LangGraph sources directly in-node (`kotoba_wasm_run` via MCP/XRPC). However, over 18,000 legacy Python actors using `from langgraph.graph import StateGraph` remained in the repository, making manual migration unfeasible.

## Decision

We have built and deployed an automated LLM-driven migration pipeline (`70-tools/scripts/migrate_to_kotoba_wasm.py`).

Instead of a deterministic AST transform, the script leverages the Murakumo fleet's primary high-capability local model, `gemma4:26b-a4b` (served via LiteLLM at `127.0.0.1:4000`), to intelligently port the logic.

The pipeline performs the following loop for each target cell:
1. **Read**: Finds `cell.py` files containing `from langgraph.graph import...`.
2. **Rewrite**: Prompts `gemma4:26b-a4b` to rewrite the graph into a standalone `kotoba_langgraph` compatible module (mocking relative imports to satisfy the build step).
3. **Compile**: Executes `build-pywasm.sh` using `componentize-py` to generate the `.wasm` binary.
4. **Deploy**: Automatically pushes the compiled WASM to the running Kotoba server's `/mcp` `kotoba_wasm_run` endpoint, using the identity of the operator DID.

## Consequences

- **Velocity**: Mass migration of legacy LangGraph actors to `kotoba-node` WASM is now automated.
- **Consistency**: All ported actors standardize on the `WitWorld` export and `kotoba_langgraph._cbor` interfaces.
- **Reliance on LLM**: The build path now depends on the availability and coherence of `gemma4:26b-a4b`. If the model hallucinates Python syntax, the `build-pywasm.sh` step traps the failure, gracefully skipping the deployment of that cell.

## Execution Record

- Developed and tested during session 2026-05-31.
- Fixed an issue in `40-engine/kotoba/crates/kotoba-server/src/mcp.rs` where the `kotoba_wasm_run` cache-key was hardcoded to `agent_did` instead of `program_cid`.
- Configured local LiteLLM to properly route `gemma4:26b-a4b` requests.
- Left the batch process running on the `gov-municipality` and `infra-utility-connect` namespaces.
