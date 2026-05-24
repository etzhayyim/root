---
id: langgraph-coding-baseline-snapshot-260525
title: "langgraph-coding bench baseline (gemma4:e4b on judah, 2026-05-25)"
status: active
doc_type: reference
topic: gemma-coder-distill
authoritative: false
last_verified: 2026-05-25
related:
  - "90-docs/adr/2605250400-gemma-coder-distill-rocm.md"
  - "70-tools/scripts/bench/langgraph-coding/"
  - "90-docs/baien/results-langgraph-baseline.jsonl"
---

# langgraph-coding bench baseline — gemma4:e4b (2026-05-25)

Initial baseline run for ADR-2605250400 §1.5. Bench harness validation +
first reading of gemma4:e4b's LangGraph competence on the Murakumo fleet.

## Setup

| Field | Value |
|---|---|
| Bench | `70-tools/scripts/bench/langgraph-coding/` (4 of 50 prompts populated) |
| Runner host | EVO-X2 (`192.168.1.70`, Python 3.12 + langgraph) |
| Model endpoint | `http://192.168.1.17:11434/v1` (judah Ollama, OpenAI-compat) |
| Model id | `gemma4:e4b` (8.0B Q4_K_M, Gemma 4 Effective 4B) |
| max_tokens | 2048 (all prompts) |
| temperature | 0.0 |
| Grader | exec-graded subprocess on EVO-X2 (langgraph importable) |
| Result file | `90-docs/baien/results-langgraph-baseline.jsonl` |

## Result (v2 — 8 prompts after conditional+interrupt deep-dive)

**2/8 pass (25.0%)** — by category:

| category | pass/total |
|---|---|
| stategraph | 1/1 |
| reducer | 1/1 |
| conditional | 0/3 |
| interrupt | 0/3 |

Per-prompt:

| id | category | passed | reason / failure pattern |
|---|---|---|---|
| s01_stategraph_basic | stategraph | ✅ | ok |
| r01_reducer_add | reducer | ✅ | ok |
| c01_conditional_branch | conditional | ❌ | `SyntaxError: positional argument follows keyword argument` |
| c02_conditional_minimal | conditional | ❌ | called `set_entry_point(START)` — START is not a node name |
| c03_conditional_path_map | conditional | ❌ | crashed inside `build_graph()` |
| i01_interrupt_resume | interrupt | ❌ | `compile(checkpointer=..., config=...)` — config not a compile kwarg |
| i02_interrupt_minimal | interrupt | ❌ | `from langgraph.checkpoint import MemorySaver` — wrong path (correct: `.memory`) |
| i03_interrupt_explicit_api | interrupt | ❌ | `from langgraph.graph.message import Command` — wrong path (correct: `langgraph.types`) |

## Systematic failure patterns (confirmed)

After deepening conditional and interrupt to 3 prompts each, **both categories are 0/3** — the failure is systematic, not prompt-specific. Distinct antipatterns recur:

| Antipattern | Frequency | Correct API |
|---|---|---|
| `from langgraph.checkpoint import MemorySaver` | i02 | `from langgraph.checkpoint.memory import MemorySaver` |
| `from langgraph.graph.message import Command` | i03 | `from langgraph.types import Command` |
| `compile(checkpointer=..., config=...)` | i01 | `compile(checkpointer=...)` ; `invoke(state, config=...)` |
| `set_entry_point(START)` | c02 | `set_entry_point('node_name')` or use `add_edge(START, 'node_name')` |
| Syntactically broken `add_conditional_edges(...)` calls | c01, c03 | (model knows the API name but fails the call surface under length) |

These are exactly the kinds of issues that distilling against an Opus-corrected corpus should fix — they're shallow API-knowledge defects, not deep reasoning failures.

## Bench harness validation

First-run findings that drove fixes before this snapshot:

- **Grader extraction bug** — earlier `_extract_code` failed on unclosed markdown fences (model truncated mid-code-block). Fixed: 2-pass regex (closed fence → open fence) in `graders/_lib.py`.
- **max_tokens too low** — initial 512–1024 caused truncation on verbose generations. Bumped all to 2048.
- **Local-vs-remote model id drift** — CLAUDE.md and `fleet.toml` reference `gemma3:4b` but judah actually serves `gemma4:e4b` + `gemma3:1b` + `qwen3.5:9b`. ADR-2605250400 updated to `gemma4:e4b` (matches user intent "gemma 4").

## Distill gate implications (ADR-2605250400 §1.5)

- **iter-00 (quick)**: requires delta ≥ 0 pp. Current 50% pass; train output must hold ≥ 50% to commit.
- **iter-01+ (real)**: requires delta ≥ +3 pp. Need ≥ 53% post-distill for adapter promotion.
- With only 4 prompts the delta is coarse (each prompt = 25 pp). Bench should grow to 50 before iter-01 to give finer gating signal.

## Next bench-population priorities

(updated after v2 results — systematic gap confirmed)

1. ~~**conditional** + **interrupt** deepen to 3 each~~ — done in v2 (0/3 + 0/3, systematic)
2. **send** (multi-node fan-out) + **subgraph** — not yet probed; high LangGraph specificity
3. **tool / error / streaming** — broader API surface
4. Add at least 1 prompt per the 4 detected antipatterns to ensure distill iter coverage of each

## How to re-run

```bash
# from this Mac
scp -q 70-tools/scripts/bench/langgraph-coding/prompts.jsonl \
       70-tools/scripts/bench/langgraph-coding/run.py \
       evo:C:/bench/
scp -q 70-tools/scripts/bench/langgraph-coding/graders/*.py evo:C:/bench/graders/
ssh evo 'cd C:\bench && C:\Users\gad\ComfyUI\ComfyUI_windows_portable\python_embeded\python.exe \
  run.py --model http://192.168.1.17:11434 --model-id gemma4:e4b --out C:\bench\results-baseline.jsonl'
scp -q evo:C:/bench/results-baseline.jsonl 90-docs/baien/results-langgraph-baseline.jsonl
```
