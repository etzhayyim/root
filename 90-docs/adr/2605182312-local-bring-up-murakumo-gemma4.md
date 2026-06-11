---
id: 2605182312-local-bring-up-murakumo-gemma4
title: Local Bring-up of Artificial Organism on Murakumo Fleet
status: active
doc_type: adr
topic: murakumo-bring-up
authoritative: true
last_verified: 2026-05-18
---

# ADR 2605182312: Local Bring-up of Artificial Organism on Murakumo Fleet

## Context
The etzhayyim system operates as an "Artificial Organism Ecosystem" utilizing a Mac mini fleet (Murakumo) to run LangServer workers. The ecosystem orchestrates active inference loops via `kotodama.agent_daemon_main` using local LLMs on the fleet. We needed to bring up the system locally on the Mac mini infrastructure and ensure it pointed to the appropriate local LLM (`gemma4:e4b`) while successfully connecting to the upstream database via keychain credentials.

## Decision
1. We deploy the `murakumo-agent` across the Mac mini nodes (10 nodes) using `etzhayyim murakumo kubelet-deploy`.
2. We utilize the virtual kubelets by running `run-local-kubelet.sh`.
3. We update `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/local_llm.py` to use `gemma4:e4b` as the default model instead of `qwen3:14b` to properly target the Mac mini's available models.
4. We run `kotodama.agent_daemon_main` after acquiring the appropriate database read credentials via `load-database-url.sh` (falling back to macOS keychain).

## Consequences
- The Artificial Organism LangServer ecosystem can execute active inference ticks locally using `gemma4:e4b`.
- Kubelet workloads map correctly onto the Murakumo Mac mini fleet.
- The Python dependencies for `kotodama` (via `uv`) were synced using Python 3.12, avoiding `pyarrow` build issues present on Python 3.14.
