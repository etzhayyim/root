---
id: adr-2605111500-openrouter-llm-api-aggregator-agentic-coding
title: "OpenRouter LLM API aggregator + agentic coding tools (OpenCode / Aider)"
status: active
doc_type: adr
topic: openrouter-agentic-coding
authoritative: true
last_verified: 2026-05-11
authoritative_for:
  - OpenRouter as LLM API aggregator for non-Claude models
  - Provider routing policy (non-China upstream selection)
  - Model alternatives: DeepSeek V4 Pro / Kimi K2.6 / MiniMax M2.5 / Gemma 4 26B
  - Agentic coding CLI tools: OpenCode v1.14.48 + Aider v0.86.2
  - OpenRouter API key storage (1Password etzhayyim vault)
  - terminal-agent agentic benchmark suite (etzhayyim code bench --agentic --swe)
  - Model selection by workload (interactive / batch / long-context / code-correctness)
  - Kotoba/Datomic bench result schema (vertex_bench_run / vertex_bench_result)
related:
  - adr-2605010000
  - adr-2605110227-gpu-cross-provider-pricing-research
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-0018-pii-tier3-cohort-first
---

# ADR 2605111500 — OpenRouter LLM API aggregator + agentic coding tools

Status: **Active** (2026-05-11).
Operating Entity: etzhayyim (sole principal).
Vendor: etzhayyim Japan株式会社 (engineering capacity).
Author: etzhayyim Claude Agent on behalf of CEO 河崎.

## 1. Decision

Adopt **OpenRouter** (`openrouter.ai`) as the unified API aggregator for
non-Anthropic LLM models, with **explicit upstream provider pinning** to
non-Chinese inference servers. Primary tools for terminal agentic coding:
**OpenCode v1.14.48** (TUI) and **Aider v0.86.2** (git-first CLI).

## 2. Context

Claude Max $200/month plan provides ~9.7M tokens/month (22 work days × 2
windows/day × 220k tokens/window). Direct API access to Kimi K2.6 and
DeepSeek V4 Pro offers 5.6× and 11× more tokens for the same $200,
respectively — but only if security risks are managed.

Chinese-operated AI APIs (DeepSeek, Moonshot/Kimi) are subject to China's
National Intelligence Law Article 7, which compels disclosure to state
authorities on request without user notification. Self-hosting or routing
via US/EU inference providers that hold open-weight model copies eliminates
this vector.

## 3. Model alternatives evaluated

### 3.1 Price comparison ($200 equivalent, input:output = 3:1 mix)

| Model | Input $/M | Output $/M | Tokens/$200 | vs Claude |
|---|---|---|---|---|
| Claude Sonnet 4.6 (API) | $3.00 | $15.00 | 33M | 1× |
| Kimi K2.6 (official) | $0.60 | $2.50 | 186M | 5.6× |
| DeepSeek V4 Pro (promo ≤2026-05-31) | $0.435 | $0.87 | 368M | 11× |
| DeepSeek V4 Pro (list price) | $1.74 | $3.48 | 92M | 2.8× |

### 3.2 Architecture

All three are MoE (Mixture of Experts) with large total / small active
parameter counts:

| Model | Total params | Active params | Context |
|---|---|---|---|
| Kimi K2.6 | 1T | 32B | 256K |
| DeepSeek V4 Pro | 1T (est.) | 32B (est.) | 128K+ |
| MiniMax M2.5 | — | — | — |

## 4. Security policy — provider routing

### 4.1 Risk classification

| Provider | Jurisdiction | DB breach | Gov ban | Risk |
|---|---|---|---|---|
| Anthropic (Claude) | 🇺🇸 US | None | None | Low |
| OpenRouter (itself) | 🇺🇸 US | None | None | Low (intermediary) |
| DeepSeek official API | 🇨🇳 CN | 1M+ records | Many govts | **High** |
| Moonshot AI official | 🇨🇳 CN | None | Partial | Medium-High |
| AtlasCloud (DeepSeek host) | 🇺🇸 US | None | None | Low |
| Inceptron (Kimi host) | 🇸🇪 SE | None | None | Low |
| SambaNova (MiniMax host) | 🇺🇸 US | None | None | Low |

### 4.2 Routing rules (MUST)

```python
# DeepSeek V4 Pro — US providers only
{
  "model": "deepseek/deepseek-v4-pro",
  "provider": {
    "order": ["AtlasCloud", "NovitaAI", "DeepInfra", "Together", "Fireworks"],
    "allow_fallbacks": false   # CRITICAL: prevents CN fallback
  }
}

# Kimi K2.6 — EU only
{
  "model": "moonshotai/kimi-k2.6",
  "provider": {
    "order": ["Inceptron"],    # Sweden
    "allow_fallbacks": false
  }
}
```

`allow_fallbacks: false` is **mandatory**. Without it, OpenRouter
auto-routes to cheapest provider, which may be the official Chinese API.

### 4.3 Use-case restrictions

| Data type | Claude direct | DeepSeek (US host) | Kimi (SE host) |
|---|---|---|---|
| Public / non-sensitive | ✅ | ✅ | ✅ |
| Internal code / logic | ✅ | ✅ | ✅ |
| PII (Tier 3) | ✅ Enterprise ZDR | ❌ | ❌ |
| Legal / financial | ✅ Enterprise ZDR | ❌ | ❌ |

## 5. OpenRouter setup

### 5.1 API key

Stored in 1Password `etzhayyim` vault:
- Title: `OpenRouter API Key`
- Item ID: `y64zp3ndrfwlxycgo4wyzpg6qm`
- Load: `op read "op://etzhayyim/OpenRouter API Key/credential"`

**Note**: The raw key was inadvertently exposed in chat session
2026-05-11. Key rotation recommended at `openrouter.ai/keys`.

### 5.2 OpenCode configuration

Global config: `~/.config/opencode/config.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "openrouter/deepseek/deepseek-v4-pro",
  "autoshare": false,
  "autosave": true
}
```

Launcher: `~/.local/bin/oc`

```zsh
#!/bin/zsh
OR_KEY=$(op read "op://etzhayyim/OpenRouter API Key/credential")
MODEL="${1:-openrouter/deepseek/deepseek-v4-pro}"
shift 2>/dev/null
OPENROUTER_API_KEY="$OR_KEY" opencode -m "$MODEL" "$@"
```

Launch commands:
```zsh
oc                                              # DeepSeek V4 Pro (default)
oc openrouter/moonshotai/kimi-k2.6             # Kimi K2.6 (Inceptron SE)
oc openrouter/minimax/minimax-m2.5             # MiniMax M2.5 (SambaNova US)
```

### 5.3 Aider configuration

```zsh
aider \
  --openai-api-key "$(op read 'op://etzhayyim/OpenRouter API Key/credential')" \
  --openai-api-base https://openrouter.ai/api/v1 \
  --model openrouter/deepseek/deepseek-v4-pro
```

## 6. Agentic coding tools

| Tool | Version | Strengths | Use case |
|---|---|---|---|
| **OpenCode** | 1.14.48 | TUI, LSP, parallel sessions, model switch in-session | Primary: interactive coding |
| **Aider** | 0.86.2 | Git-first (every edit = commit), stable, provider-agnostic | Secondary: git-tracked refactors |

Both installed globally:
- OpenCode: `npm install -g opencode-ai`
- Aider: `pip install aider-chat`

## 7. Cost break-even

| Monthly tokens | Recommendation |
|---|---|
| < 5B | Use Moonshot/DeepSeek official API directly |
| 5B – 20B | OpenRouter + US/EU providers |
| > 20B | Self-host on RunPod (8× H100 Q4 = ~$22/hr) |

At Claude Max $200/month the effective token budget is ~9.7M/month — well
below the 5B threshold where self-hosting becomes cheaper than API.
OpenRouter supplements Claude for cost-sensitive batch workloads only.

## 8. Verification results (2026-05-11)

| Model | Provider (actual) | Latency | Cost/call | Status |
|---|---|---|---|---|
| DeepSeek V4 Pro | AtlasCloud 🇺🇸 | ~1.5s TTFT | — | ✅ |
| Kimi K2.6 | Inceptron 🇸🇪 | ~1.2s TTFT | $0.00021 | ✅ |
| MiniMax M2.5 | SambaNova 🇺🇸 | — | $0.000039 | ✅ |
| MiniMax M2.7 | MiniMax 🇸🇬 | — | — | ✅ (SG only) |
| OpenCode + DeepSeek | AtlasCloud 🇺🇸 | — | — | ✅ |

Kimi K2.6 is a thinking model — minimum `max_tokens: 300` required or
reasoning consumes all tokens before producing output.

## 9. Agentic benchmark suite (`etzhayyim code bench`)

### 9.1 Bench architecture

`60-apps/etzhayyim-terminal-agent/scripts/bench.py` — LangGraph in-process
benchmark with four suites:

| Flag | Suite | Benches |
|---|---|---|
| (default) | latency + tools | import, echo, multi-turn, read_file, grep, throughput |
| `--agentic` | agentic | bash canary, multi-tool chain, error recovery |
| `--swe` | SWE-bench style | code comprehension, bug hunt, write+run+verify, multi-file synthesis |
| `--rw-export` | persistence | inserts `vertex_bench_run` / `vertex_bench_result` / `edge_bench_run_has_result` into Kotoba/Datomic |

CLI: `etzhayyim code bench --model <openrouter-id> --agentic --swe --runs 2`

Schema DDL: `60-apps/etzhayyim-terminal-agent/scripts/schema_bench.sql`

### 9.2 SWE-bench tasks (added 2026-05-11)

Existing agentic benches test tool-call format compliance (≤ 3 steps).
SWE-bench style tasks require code understanding and multi-step reasoning:

| Task | What it tests | Success criterion |
|---|---|---|
| code comprehension | Read bench.py; explain why p50 = `statistics.median` not mean | reply contains "median" + ("statistics" or "percentile") |
| bug hunt | Find off-by-one `range(1, len(numbers)+1)` in temp file | reply identifies index/boundary/off-by-one cause |
| write + run + verify | Write sum([1..5]) script → bash → report output | reply contains "15" |
| multi-file synthesis | grep + read; report two counts about successes | ≥ 2 distinct numbers + "successes" in reply |

### 9.3 7-model agentic bench comparison (2026-05-11)

`--agentic --runs 2` (9 benches each, p50 latency / agentic success %):

| Model | TTFT echo | p50 multi-tool | p50 throughput | Agentic | $/M in | $/M out |
|---|---|---|---|---|---|---|
| Kimi K2.6 (Inceptron SE) | ~3.9s | ~8.5s | ~29s | 86% | $0.60 | $2.50 |
| **Claude Opus 4.6** | ~1.7s | ~10.1s | ~11.8s | **86%** | $15 | $75 |
| Qwen3.6 Plus | ~6.5s | ~35.3s | ~56.3s | 79% | $0.29 | $0.29 |
| DeepSeek V4 Pro (US) | ~2.1s | ~31.0s | ~23.2s | 100% | $0.435 | $0.87 |
| Gemma 4 26B | ~2.1s | ~4.7s | ~7.1s | 86% | $0.10 | $0.30 |
| Gemma 4 31B | ~0.7s | ~10.8s | ~15.0s | 91% | $0.12 | $0.36 |
| MiniMax M2.7 | ~3.2s | ~18.2s | ~8.3s | 86% | $0.30 | $1.20 |

**Cost × throughput efficiency index** (tok/s ÷ $/M out, higher = better):

| Model | tok/s | $/M out | Efficiency index |
|---|---|---|---|
| Gemma 4 26B | ~78 tok/s | $0.30 | **260** |
| Gemma 4 31B | ~30 tok/s | $0.36 | 83 |
| MiniMax M2.7 | ~67 tok/s | $1.20 | 56 |
| Qwen3.6 Plus | ~10 tok/s | $0.29 | 34 |
| DeepSeek V4 Pro (US) | ~27 tok/s | $0.87 | 31 |
| Kimi K2.6 | ~37 tok/s | $2.50 | 15 |
| Claude Opus 4.6 | ~37 tok/s | $75 | 0.5 |

**Conclusion**: Gemma 4 26B has highest cost-efficiency index (260) for
batch / latency-tolerant workloads. However, public benchmarks (MMLU,
SWE-bench, Arena) rank it below Kimi K2.6 and Claude because our bench
only validates tool-call format compliance, not reasoning depth or
code-correctness under test-suite pressure.

**Model selection by workload**:

| Workload | Recommended model | Reason |
|---|---|---|
| Interactive agentic coding (primary) | Claude Sonnet 4.6 / Opus 4.6 | Best reasoning, ZDR, fast TTFT |
| Cost-sensitive batch (non-PII) | Gemma 4 26B (Groq/OpenRouter) | 260× efficiency index |
| Long-context synthesis (non-PII) | Kimi K2.6 (Inceptron SE) | 256K context, strong tool use |
| Code-correctness critical | DeepSeek V4 Pro (US hosts) | SWE-bench top tier |

### 9.4 Known bench limitations

1. **Bash canary 0% root cause (fixed 2026-05-11)**: `_run_turn` only
   captured `on_chat_model_stream` events. When bash requires approval,
   `interrupt()` pauses the graph before execution; the LLM reply never
   arrives. Fix: `auto_approve=True` resumes via
   `graph.aget_state(config).interrupts` + `Command(resume="allow")`.

2. **Agentic ceiling at 86%**: all top models saturate at 86% on the
   9-bench agentic suite. The ceiling is the bash canary (requires bash
   tool execution + approval) and multi-tool chain (grep→read→list).
   SWE tasks (`--swe`) differentiate reasoning quality above this floor.

3. **Gemma grep false negative**: Gemma 4 31B returns "No matches found"
   for a pattern with many real hits — factually wrong, correctly scored 0%.
# Monthly 100,000 JPY Budget Efficiency Comparison

Assumption: 1 USD = 150 JPY. Monthly budget = $666.67 USD.
Blended API pricing assumes a 3:1 input-to-output token ratio.

| Model | Blend $/M | tok/s | Max Tokens (M) / mo | Agentic | Primary Use Case |
|---|---|---|---|---|---|
| DeepSeek V4 Pro | $0.544 | 27 | 1,226 M | 100% | High-reasoning SWE & Coding |
| Kimi K2.6 | $1.075 | 37 | 620 M | 86% | Long-context (256K) text |
| Qwen3.6 Plus | $0.290 | 10 | 2,298 M | 79% | General low-cost fallback |
| MiniMax M2.7 | $0.525 | 67 | 1,269 M | 86% | High-throughput batch API |
| Gemma 4 31B | $0.180 | 30 | 3,703 M | 91% | API fallback for GenAI pipeline |
