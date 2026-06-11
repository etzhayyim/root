---
id: adr-2605312100-kotoba-migration-agentic-cli-bakeoff-and-gemini-selection
title: "ADR-2605312100: kotoba py-WASM migration — agentic-CLI bake-off (claude-haiku vs gemini vs gemma-4-26B) + gemini selection"
status: accepted
doc_type: adr
topic: kotoba-migration-agentic-cli-bakeoff-and-gemini-selection
authoritative: true
last_verified: 2026-05-31
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Decides the model/agent that ports 8,180 LangGraph cells 1-by-1 to kotoba WASM; supersedes the codegen approach of ADR-2605310200"
authoritative_for:
  - kotoba py-WASM 1-by-1 agentic migration model selection
depends_on:
  - "2605310200"
  - "2605262130"
  - "2605301625"
  - "2605302355"
  - "2605215000"
  - "2605253000"
related:
  - "2605240000"
  - "2605302359"
supersedes: []
superseded_by: []
---

# ADR-2605312100: kotoba py-WASM migration — agentic-CLI bake-off + gemini selection

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605310200 introduced an **automated single-shot** LangGraph→kotoba-WASM migration
pipeline (`migrate_to_kotoba_wasm.py`, gemma4:26b-a4b via LiteLLM). Census (2026-05-31):
**8,180 `StateGraph` files** across 20-actors await porting; **0** migrated outside the
10 `kotoba-langgraph-*` examples. Distribution: 8,074 codegen UNSPSC agents
(`kotodama/langgraph_graphs/`), 34 religious-corp cells, 5 framework-core, ~76 Tier-B
actor cells. (Plan: `90-docs/kotoba-wasm-migration-plan.edn`.)

Founder decision (2026-05-31): **reject codegen/bulk-regeneration; migrate each cell
1-by-1, agentically, for maturity** — and empirically compare **generation quality and
cost** across three models before committing: **claude-haiku-4-5**, **gemma-4-26B-A4B-it**,
and the Gemini flash family.

A bake-off harness was built under `70-tools/scripts/kotoba-migration-bakeoff/`. The pivot
that matters: each contender runs as a **full coding agent** (reads the cell, writes the
port, runs `build-pywasm.sh`, reads build errors, self-repairs, iterates) — not a single
LLM call. claude (Claude Code `-p`) and gemini (Gemini CLI `-p`) are native agentic CLIs;
gemma is driven by a harness-supplied feedback loop (it is not a CLI agent). Corpus = 5
complexity-stratified cells (27→78 LOC, 2→7 nodes). Shared toolchain = a `uv` venv with
`componentize-py 0.23` so every contender builds on equal footing.

## Constitutional boundary (CRITICAL)

claude/gemini/gemma-as-tool call commercial or local endpoints **directly, not via
Murakumo**. This is permissible **only because migration is DEV-TIME tooling** that emits
source code. The migrated WASM actors themselves keep running on kotoba `:8077` → Murakumo
LiteLLM `127.0.0.1:4000` for their own inference (ADR-2605215000 SSoT, ADR-2605302355
loopback fix). Selecting gemini as the migration agent does **not** introduce a commercial
inference dependency into any religious-corp runtime path.

# Decision

**Adopt the agentic-CLI migration harness, and select the Gemini CLI as the migration agent**
(`gemini -p -m gemini-3-flash-preview --approval-mode yolo`, `GEMINI_CLI_TRUST_WORKSPACE=true`).

- Primary model: **`gemini-3-flash-preview`** (the founder asked for Gemini 3; `gemini-3.1-*`
  returns 404 on this account — only `gemini-3-flash-preview` / `gemini-3-pro-preview` are
  served). One-flag swap to **`gemini-2.5-flash`** is retained as a higher-judge alternative
  (see Consequences — judge noise).
- **codex (gpt-5.5)** deferred: hit its usage limit during the run; to be added via
  `bakeoff_cli.py --clis codex` after reset and folded into a later revision.
- Harness, corpus, per-port artifacts and results are committed under
  `70-tools/scripts/kotoba-migration-bakeoff/` (`bakeoff_cli.py`, `corpus.edn`,
  `results/SUMMARY.edn`, `runs/<cell>/<model>/agent.py|.wasm`).

This **supersedes the codegen path of ADR-2605310200** for everything except, optionally,
the 8,074 uniform UNSPSC agents (where bulk-regeneration may still be reconsidered if 1-by-1
proves too costly at that scale — tracked in the migration plan, not decided here).

# Consequences

**Bake-off results (2026-05-31, n=5 cells, judge = claude-haiku 1–5, single-shot, noisy):**

| model | build-pass | avg-judge | cost | wall | self-repair |
|---|---|---|---|---|---|
| gemini-2.5-flash (R1) | 1.0 | **3.6** | n/a (quota) | 127.9s | ✅ |
| gemini-3-flash-preview (R2) | 1.0 | 2.8 | n/a (quota) | 142.0s | ✅ |
| claude-haiku-4-5 (R1/R2) | 1.0 | 2.8 | $0.094–0.107/cell | ~135s | ✅ |
| gemma-4-26B-A4B-it (R3, 2 cells) | 0.0 | — | $0 (local, slow) | 840s/2 | ❌ |

- **All commercial-CLI agents pass build 100%** on all 5 cells with exact node-name
  preservation. The objective gate does not separate claude from gemini at n=5.
- **Judge is noisy**: the *newer* gemini-3-flash-preview scored *lower* (2.8) than
  gemini-2.5-flash (3.6). 1-point deltas at n=5 are within noise — do not over-read.
- **gemma-4-26B-A4B is NOT "just heavy"**: raw single-shot quality (thinking OFF) is faithful
  and buildable, BUT (a) default thinking-ON emits 2000+ reasoning tokens and exhausts the
  token budget → empty code; (b) CPU serve ~5–9 tok/s (5–7× slower, Metal MoE offload crashes
  per ADR-2605253000); (c) **derails under the build-error feedback loop** — by iteration 4 it
  wrote a meta-script (the port embedded as a string literal) instead of fixing the port
  (evidence: `results/gemma-evidence/service-request-iter4-derailed.py`). gemma is viable only
  as a single-shot generator behind an external build/verify harness, **not** as an autonomous
  self-repairing agent — which is exactly the chosen use case. Hence excluded.
- **gemini chosen** for: 100% build, concise faithful ports, competitive wall-time, and no
  metered per-call cost on the current quota. **Trade-off**: the Gemini CLI does not emit
  per-call USD, so cost is tracked only as wall-clock; claude remains the cost-measurable
  fallback ($0.094–0.107/cell).
- **Decision strength = provisional-but-actionable.** None of the open items block starting
  migration with gemini on low-risk cells now.

**Hardening (2026-05-31, items 1–4 executed):**
1. **invoke-equivalence gate built** (`invoke_equiv.py`) and run against live `:8077`:
   deploy `agent.wasm` → invoke with the original cell's input → compare output state to the
   host-CPython `solve()` gold. Result on the 2 functional cells: **2/4 strict-equivalent,
   4/4 equivalent-modulo-input-passthrough**. The gate immediately caught a runtime divergence
   that build-pass + structural + LLM-judge ALL missed.
2. **Real root cause of that divergence was the substrate, not the port**:
   `kotoba_langgraph/graph.py` merged the FULL input dict into state and never dropped
   unwritten channels, unlike real langgraph — so migrated actors retained input keys (e.g.
   `projectId`) in their output. **FIXED in the kotoba submodule** (`py/kotoba_langgraph/graph.py`):
   `invoke()`/`stream()` now track node-written keys and, for dynamic `StateGraph(dict)` graphs,
   drop input-only keys no node writes (typed-schema graphs keep their declared channels — langgraph
   parity). 4 new regression tests (`py/tests/test_dynamic_channels.py`), full suite 100 passed.
   After the substrate fix + the StateGraph(dict) prompt rule + rebuild, **all functional-cell ports are
   now STRICT-equivalent to their originals** — invoke-equiv = **4/4 strict** (service-request +
   final-sign-off × claude + gemini). The `projectId` divergence is fully resolved. Follow-up: commit the
   submodule + bump the pointer.
3. **Deployed `:8077` binary rebuilt** — the running binary cached compiled programs by
   `agent_did` (ADR-2605310200 `program_cid` cache-key fix was in source, not in the deployed
   binary). Rebuilt `kotoba-cli --features kotoba-server/wasm-runtime`, installed
   (`~/.local/bin/kotoba`, old → `kotoba.bak-precachefix`), restarted, **verified** the
   program_cid cache-key is now live.
4. **invoke-equivalence extends to relative-import cells** (package import), but the 3 Tier-B
   rel-import cells are **R0 scaffolds whose originals RAISE on execution** ("activate via
   Council ADR post-ratification") — no runtime gold exists, so equivalence is N/A for
   R0-scaffold cells until ratified.
   **codex (gpt-5.5) still usage-limited at run time** — deferred (`--clis codex` after reset).
Remaining: cross-judge to de-bias, widen corpus to 15–20 cells, the kotoba_langgraph substrate fix.

**Toolchain artifacts** (reusable): 12.7 GB GGUF `gemma-4-26B-A4B-it-UD-Q3_K_M.gguf`
(`~/models/gemma/`) + `llama-server :8090`; venv `componentize-py 0.23`; harness fixes
documented (claude needs `--permission-mode bypassPermissions`; gemini needs
`GEMINI_CLI_TRUST_WORKSPACE=true` + `--approval-mode yolo`; gemma needs
`chat_template_kwargs.enable_thinking=false`).

# Alternatives Considered

1. **Codegen / bulk-regenerate the 8,074 UNSPSC template (ADR-2605310200)** — rejected by
   founder for maturity; bulk shortcut retained only as a fallback for the uniform UNSPSC tier.
2. **claude-haiku-4-5** — equally 100% build + cost-measurable + autonomous; viable runner-up,
   kept as the cost-instrumented fallback.
3. **gemma-4-26B-A4B (Murakumo-native, $0)** — excluded as an autonomous agent (thinking
   runaway + latency + non-convergent self-repair); may serve single-shot behind a harness.
4. **gemini-2.5-flash** — higher judge (3.6) but the founder asked for Gemini 3; retained as a
   one-flag alternative pending de-noised judging.

# References

- `90-docs/kotoba-wasm-migration-plan.edn` — full 8,180-file migration plan + waves
- `70-tools/scripts/kotoba-migration-bakeoff/` — harness, corpus, `results/SUMMARY.edn`, ports
- ADR-2605310200 — automated single-shot migration pipeline (superseded for 1-by-1 path)
- ADR-2605262130 — kotoba canonical substrate; ADR-2605301625 / 2605302355 — actor deploy + LLM verify
- ADR-2605215000 — Murakumo-only inference SSoT (runtime invariant preserved)
- ADR-2605253000 — gemma-4-26B-A4B disk inference (heaviness warning, confirmed)
