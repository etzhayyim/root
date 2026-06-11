---
id: adr-2605121400-terminal-agent-graph-enhancement-claude-code-parity
title: "terminal-agent LangGraph enhancement — Claude Code feature parity (Router/Reflection/Plan/Repomap/Supervisor/Memory/CodeAct/Context/Edit/WebFetch/TokenCost/ParallelTools/Vision/Thinking/Compact/YoroHITL)"
status: active
doc_type: adr
topic: terminal-agent-graph
authoritative: true
last_verified: 2026-05-13
authoritative_for:
  - terminal-agent LangGraph node topology (10-node graph)
  - Token/cost telemetry (per-turn + session total, _PRICING table, _format_usage)
  - Parallel tool execution (asyncio.gather in tool_node; replaces sequential ToolNode)
  - Vision input (@path syntax, base64 image_url content blocks)
  - Extended thinking (AGENT_THINKING_BUDGET, thinking block display in CLI)
  - /compact command (RemoveMessage + LLM summary, context compression)
  - Yoro HITL notification (AT Protocol DM via chat.bsky.convo.*, fire-and-forget)
  - Real-time bash streaming (adispatch_custom_event bash_line, RunnableConfig propagation)
  - Router node + task-type specialist routing
  - Reflection node with task-type-specific prompts
  - Plan node for file_edit task decomposition
  - Repomap node (git ls-files cached per thread)
  - Supervisor node (AGENT_SUPERVISOR=true, multi-worker orchestrator)
  - Memory node (JSONL episodic memory at ~/.terminal-agent/memories.jsonl)
  - Observability (LocalTraceCallback, AGENT_TRACE_DIR, LangSmith)
  - CodeAct mode (AGENT_CODEACT=true, Python block execution)
  - Context window management (AGENT_MSG_WINDOW, head+tail trim)
  - etzhayyim CLI integration (code.go delegates to terminal-agent; code exec flags: --dir, --message, --model, --api-key, --uv-bin, --dry-run)
  - MCP server (uv run agent mcp, stdio + HTTP transport)
  - Git tools (git_status, git_diff, git_log, git_commit)
  - LSP tools (lsp_check, lsp_symbols)
  - edit_file tool (exact string replace, ambiguity detection)
  - web_fetch tool (URL fetch + HTML→Markdown, 8000 char cap)
  - Benchmark suite (scripts/bench.py --agentic --swe, scripts/compare_models.py)
related:
  - adr-2605111500-openrouter-llm-api-aggregator-agentic-coding
  - adr-2605120600-terminal-agent-hitl-yoro-inbox
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605080600-langgraph-server-granian-l3-runtime
---

# ADR 2605121400 — terminal-agent LangGraph graph enhancement (Claude Code parity)

Status: **Active** (2026-05-12).
Operating Entity: etzhayyim.
Author: etzhayyim Claude Agent on behalf of CEO 河崎.

## 1. Decision

Extend `60-apps/etzhayyim-terminal-agent` from a single `llm → tools` loop to a
**10-node LangGraph graph** that achieves feature parity with Claude Code for
agentic coding tasks. All enhancements are implemented in-process; the LangGraph
Server deployment (ADR-2605120600) is preserved unchanged.

## 2. Node topology

```
START → router → memory_load → repomap → plan
                                             ↓ (conditional)
                                         supervisor ←─────────────┐
                                             ↓                     │
                                           llm ──→ codeact ──────→ llm
                                             ↓
                              ┌──────────────┼──────────────┐
                           approval        tools        reflection
                              └──────────────┴──────────────┘
                                             ↓ (no tool calls, has results)
                                         supervisor / reflection
                                             ↓ (feedback=None)
                                            END
```

### Node roles

| Node | Env gate | Purpose |
|---|---|---|
| `router` | always | LLM-based task classifier → `task_type` ∈ {file_edit, shell_run, search, question, general}; resets all per-turn state |
| `memory_load` | always | Load top-3 relevant episodic memories from `~/.terminal-agent/memories.jsonl` |
| `repomap` | always | `git ls-files` compact file tree; cached in `AgentState.repo_map` per thread |
| `plan` | always | Step-by-step plan for `file_edit` tasks; skipped for other task types |
| `supervisor` | `AGENT_SUPERVISOR=true` | Picks worker profile (researcher/coder/tester/reviewer/generalist); routes back to llm or END; max `_MAX_SUPERVISOR_TURNS` iterations |
| `llm` | always | Chat completion with trimmed context window; uses specialist model if `AGENT_MODEL_{TASK_TYPE}` set |
| `codeact` | `AGENT_CODEACT=true` | Extracts and executes `python` fenced blocks via `asyncio.create_subprocess_exec`; result injected as HumanMessage |
| `approval` | tool in APPROVAL_REQUIRED | HITL interrupt for `request_human_decision`; resumes with allow/deny |
| `tools` | always | Standard LangChain ToolNode |
| `reflection` | always (unless supervisor) | LLM verifier; injects `reflection_feedback` or terminates; task-type-specific prompts |

## 3. Feature index

### 3.1 Router + specialist routing (Phase 1-A / 2-A)

`router_node` classifies every turn. `_model_for_task(task_type)` reads
`AGENT_MODEL_{TASK_TYPE}` env vars (e.g. `AGENT_MODEL_FILE_EDIT`) to select a
specialist model per task type. Falls back to `AGENT_MODEL` default.

### 3.2 Git tools (Phase 1-A)

`tools/git.py`: `git_status`, `git_diff(staged, path)`, `git_log(max_count,
oneline)`, `git_commit(message, files)` — all via `asyncio.create_subprocess_exec("git", ...)`.

### 3.3 Repomap node (Phase 1-B)

`git ls-files | head -200` output stored in `AgentState.repo_map`; injected into
system prompt once per thread. Subsequent turns reuse cached value (no extra
subprocess).

### 3.4 Plan node (Phase 2-B)

For `task_type == "file_edit"`, generates a numbered step-by-step execution
plan via a short `_llm_plain()` call. Stored in `AgentState.execution_plan`;
prepended to system prompt during the LLM node.

### 3.5 MCP server (Phase 1-C)

`tools/mcp_server.py` using FastMCP. Launched via `uv run agent mcp` (stdio) or
`uv run agent mcp --http PORT` (streamable HTTP). Exposes all tools except
`request_human_decision` (HITL only).

### 3.6 LSP tools (Phase 1-D)

`tools/lsp.py`: `lsp_check(path)` — pyright for `.py`, `npx tsc --noEmit` for
`.ts/.tsx`; auto-detects language. `lsp_symbols(path)` — Python AST (class/def
names) or grep-based fallback for other languages.

### 3.7 Supervisor (Phase benchmark)

`supervisor_node` uses a separate `_llm_plain()` call to pick a worker profile.
Controlled by `AGENT_SUPERVISOR=true` env. Guards against infinite loops via
`_MAX_SUPERVISOR_TURNS` (default 3). `worker_profile` stored in `AgentState` for
system prompt injection.

### 3.8 Memory (Phase benchmark)

`memory_load_node` queries `~/.terminal-agent/memories.jsonl` (max 100 entries,
FIFO eviction) by keyword overlap scoring against the current user message. Top-3
matches injected as system prompt bullets. After session, `_save_session_memory()`
generates a 1-2 sentence LLM summary + 3-5 keyword tags and appends to the store.

### 3.9 Observability (Phase benchmark)

`trace.py`: `LocalTraceCallback(BaseCallbackHandler)` writes `on_llm_start` /
`on_llm_end` events as JSONL to `{AGENT_TRACE_DIR}/{session_id}_{ts}.jsonl`.
Enabled by `AGENT_TRACE_DIR` env or `--trace` CLI flag. LangSmith tracing via
standard `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` env.

### 3.10 Context window management

`llm_node` trims message history when `len(messages) > _MSG_WINDOW` (default 40,
override `AGENT_MSG_WINDOW`): keeps `messages[:2]` (system + first human) +
`messages[-(window-2):]`. Prevents context overflow on long sessions without
losing initial instructions.

### 3.11 CodeAct mode

`AGENT_CODEACT=true` enables Python block execution. After each LLM turn that
produces `\`\`\`python ... \`\`\`` blocks but no tool calls, `codeact_executor_node`
runs each block via `asyncio.create_subprocess_exec("python3", "-c", code, cwd=working_dir)`
with a 30s timeout. Output (truncated to 2000 chars) is injected as a HumanMessage
and the LLM continues. Does not use ToolMessage (no corresponding tool_call_id).

### 3.12 Reflection accuracy

Reflection prompts are task-type-specific. `file_edit` checks for file writes
and correctness; `shell_run` checks exit codes; `search` checks for results;
`question` checks completeness. Generic fallback for `general`.

### 3.13 Edit tool (Phase A — 2026-05-13)

`tools/files.py` — `edit_file(path, old_string, new_string, replace_all=False)`.

Replaces an exact string in a file without rewriting the whole file — equivalent
to Claude Code's `Edit` tool. Semantics:
- `old_string` must match byte-for-byte (including indentation/whitespace).
- If `replace_all=False` (default): exactly 1 occurrence required; 0 or 2+ occurrences
  → error with actionable hint ("add surrounding lines" or "set replace_all=True").
- If `replace_all=True`: all occurrences replaced.
- Returns a diff-style summary (`replaced N occurrence(s), M line(s) → P line(s)`).
- No external dependencies — pure stdlib `Path.read_text` / `str.replace` / `Path.write_text`.

This replaces the previous pattern of `read_file` → full rewrite via `write_file`,
which was fragile for large files and obscured the agent's intent.

### 3.14 Web fetch tool (Phase B — 2026-05-13)

`tools/web_fetch.py` — `web_fetch(url, timeout=15)`.

Fetches any HTTP/HTTPS URL and returns readable content:
- HTML → Markdown conversion via a lightweight `HTMLParser` subclass
  (`_TextExtractor`). Strips `<script>`, `<style>`, `<nav>`, `<header>`,
  `<footer>`, `<aside>`, `<noscript>`. Converts headings, links, list items to
  Markdown. Collapses excess blank lines.
- JSON / plain text / Markdown returned as-is.
- Download capped at 512 KB; output capped at 8000 chars with truncation notice.
- Uses `urllib.request` only — no third-party dependencies (`httpx`, `requests`
  not required).
- User-Agent: `terminal-agent/1.0 (research; +https://etzhayyim.com)`.

### 3.22 Real-time bash streaming (Phase K — 2026-05-13)

`tools/shell.py` + `nodes.py` + `cli.py` — bash output streams line-by-line while running.

- `bash` tool rewritten to read stdout via `async for raw in proc.stdout:` instead of
  `proc.communicate()`. Each line dispatched via `adispatch_custom_event("bash_line", {"line": …})`.
- Output still capped at 4000 chars (`_MAX_OUTPUT`); truncation appended to returned string.
- `tool_node(state, config: RunnableConfig)` — `config` parameter added (LangGraph node
  injection) and forwarded to `tool.ainvoke(args, config=config)`. This is required for
  `adispatch_custom_event` to propagate events back through `astream_events`.
- CLI: `on_custom_event` with `name=="bash_line"` handler added to all 3 event loops
  (`_run_local` main, `_run_local` interrupt resume, `_run_once`). Lines shown as
  `[dim]  {line}[/dim]` below the tool panel header.

### 3.17 Parallel tool execution (Phase F — 2026-05-13)

`nodes.py` — `tool_node` replaced with a parallel implementation using `asyncio.gather`.

- Removed `ToolNode` from LangGraph prebuilt (was sequential).
- `_TOOL_MAP: dict[str, object]` — tool name → callable, built once at module load.
- `tool_node` extracts `tool_calls` from the last message and runs each via `asyncio.gather`.
- Unknown tool names return `ToolMessage` with `[error: unknown tool '...']`.
- Exceptions per-tool are caught and returned as error ToolMessages — other tools still complete.

### 3.18 Vision input (Phase G — 2026-05-13)

`cli.py` — `@path` syntax inlines images into user messages.

- `_IMG_EXTS` — `.png .jpg .jpeg .webp .gif` (matching Claude's supported image types).
- `_parse_vision_input(text) -> list | str` — splits on `@\S+` tokens; converts existing
  image files to `{"type": "image_url", "image_url": {"url": "data:{mime};base64,{data}"}}`
  blocks; non-image `@` tokens kept as plain text. Returns original string if no images found.
- Applied to user input in `_run_local` before graph invocation.

### 3.19 Extended thinking (Phase H — 2026-05-13)

`nodes.py` — `AGENT_THINKING_BUDGET` env var (int tokens) enables Claude extended thinking.

- `_llm()` reads `AGENT_THINKING_BUDGET` lazily; cache key extended to `(model, profile, budget)`.
- When budget > 0, adds `{"thinking": {"type": "enabled", "budget_tokens": N}}` to `extra_body`
  (merged with existing `OPENROUTER_PROVIDER_CONFIG` provider routing).
- `cli.py` — stream handlers updated to handle list-type chunk content: `"thinking"` blocks
  displayed as `[dim]💭 …[/dim]`; `"text"` blocks displayed normally.
- `--thinking N` CLI flag sets `AGENT_THINKING_BUDGET=N`.

### 3.20 `/compact` command (Phase I — 2026-05-13)

`cli.py` — `/compact` compresses conversation history in-place.

- `_compact_messages(messages) -> str` — builds a 30-message transcript (skipping system
  messages), asks `_llm_plain()` to summarize into ≤300 words preserving key decisions,
  file paths, and task outcomes.
- REPL handler: fetches current state, calls `_compact_messages`, uses `RemoveMessage` to
  delete all existing messages, injects a single `HumanMessage` with the context summary.
- `graph.aupdate_state` applies the deletion + injection atomically via the checkpointer.
- No-op if fewer than 4 messages.

### 3.21 Yoro HITL notification (Phase J — 2026-05-13)

`cli.py` — `_yoro_notify_hitl()` fire-and-forget DM to AT Protocol inbox on HITL interrupt.

- Required env vars: `ATP_SERVICE` (PDS URL), `ATP_IDENTIFIER`, `ATP_PASSWORD`,
  `AGENT_YORO_DID` (recipient). All loaded from keychain before running the agent.
- Flow: `com.atproto.server.createSession` → `chat.bsky.convo.getConvoForMembers` →
  `chat.bsky.convo.sendMessage` (all via `httpx.AsyncClient` with 10s timeout).
- Message format: `[terminal-agent HITL] {tool_name}\n{question}\nContext: {context[:300]}`.
- Launched via `asyncio.create_task()` — does not block the CLI approval prompt.
- All exceptions swallowed (non-fatal; CLI approval proceeds regardless).

### 3.16 Token/cost telemetry (Phase E — 2026-05-13)

`cli.py` — per-turn token counts and estimated cost, displayed after each assistant turn.

- `_PRICING: dict[str, tuple[float, float]]` — `model → (input_per_mtok, output_per_mtok)`.
  Covers Claude Sonnet/Opus/Haiku, GPT-4o/mini, o3-mini, Gemini 2.0 Flash.
- `_format_usage(inp, out, cache_read=0, model="") -> str` — formats `↑Xk ↓Xk cache:Xk ~$X.XXXX`.
  Cost omitted when model not in `_PRICING`. Cache read billed at 10% of input price.
- `_accum_usage(event, ci, co, cc)` — extracts `usage_metadata` from `on_chat_model_end` events;
  accumulates into mutable `[int]` cells.
- Per-turn display: `[dim]↑Xk ↓Xk ~$X.XXXX[/dim]` after each `astream_events` call.
- Session total: `[dim]session total: ↑Xk ↓Xk ~$X.XXXX[/dim]` printed on REPL exit.
- Bug fix: `while True:` REPL loop moved inside `async with local_checkpointer()` block
  (was outside, so the checkpointer connection was closed before any graph calls ran).

### 3.15 Benchmark suite

`scripts/bench.py` — in-process LangGraph benchmark:
- `--agentic`: 9 benches, tool-call compliance, 86% ceiling for top models
- `--swe`: 4 SWE-bench style tasks (code comprehension, bug hunt, write+verify, multi-file)
- `--rw-export`: persist to Kotoba/Datomic (schema: `schema_bench.sql`)
- `--json`: machine-readable output

`scripts/compare_models.py` — multi-model comparison: runs `bench.py --json` for
N models via subprocess, prints markdown table, saves to `results/compare_{ts}.json`.

## 4. etzhayyim CLI integration

`70-tools/etzhayyim/etzhayyim/code.go` delegates all execution to the terminal-agent (LangGraph).
aider and codex were removed 2026-05-14 (`etzhayyim-code-remove-aider-codex-2026-05-14`).

### `etzhayyim code` (interactive REPL)

Delegates directly to `runCodeAgent(args)` → `uv run agent [--local]`.

### `etzhayyim code exec` (non-interactive one-shot)

Launches `uv run agent --local --message <msg> --dir <dir>` from the terminal-agent
app directory. Env vars set: `OPENROUTER_API_KEY`, `AGENT_MODEL`.

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` | working directory passed to agent via cli.py `--dir` → `AgentState.working_dir` |
| `--message` | (required) | one-shot prompt |
| `--model` | `AGENT_MODEL` or `anthropic/claude-sonnet-4-6` | OpenRouter model id |
| `--api-key` | `OPENROUTER_API_KEY` | OpenRouter API key |
| `--uv-bin` | `uv` | uv binary path |
| `--dry-run` | off | print resolved command and exit |

### cli.py `--dir` flag (added 2026-05-14)

`_run_once(message, local, working_dir="")` sets `initial["working_dir"] = working_dir`
when provided, so `AgentState.working_dir` is initialized to the caller's target directory
instead of the default `"."` (terminal-agent app root).

### Environment gates (agent-side, unchanged)

| Env var | Effect |
|---|---|
| `AGENT_SUPERVISOR=true` | enable supervisor node |
| `AGENT_CODEACT=true` | enable CodeAct Python execution |
| `AGENT_MSG_WINDOW=N` | context window message count (default 40) |
| `AGENT_TRACE_DIR` | enable JSONL trace output |
| `AGENT_MODEL_{TASK_TYPE}` | specialist model per task type |

## 5. State schema (`AgentState`)

```python
class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    pending_approval: PendingApproval | None = None
    approval: Literal["allow", "deny"] | None = None
    working_dir: str = "."
    task_type: str | None = None           # router_node
    reflection_count: int = 0              # reflection_node
    reflection_feedback: str | None = None
    repo_map: str | None = None            # repomap_node (cached per thread)
    execution_plan: str | None = None      # plan_node (reset per turn)
    worker_profile: str = "generalist"     # supervisor_node
    supervisor_turns: int = 0
    memories: list[str] = Field(default_factory=list)
    session_id: str = ""
```

## 6. Key implementation constraints

- `_llm_plain()` (router, plan, supervisor, memory summary) uses `streaming=False`
  so no `on_chat_model_stream` events are emitted — these calls are invisible in
  CLI output.
- CodeAct results use `HumanMessage` not `ToolMessage` (no tool_call_id exists).
- `_llm_cache` is `dict[str, object]` keyed by model id; different task types may
  resolve to different models and maintain independent cache entries.
- MCP server excludes `request_human_decision` (HITL; not suited for MCP callers).

## 7. File inventory

| File | Change |
|---|---|
| `src/terminal_agent/state.py` | Added 7 fields (task_type, reflection_count, reflection_feedback, repo_map, execution_plan, worker_profile, supervisor_turns, memories, session_id) |
| `src/terminal_agent/graph.py` | 10-node graph; 5 routing functions |
| `src/terminal_agent/nodes.py` | router, memory_load, repomap, plan, supervisor, codeact, reflection nodes; context trimming in llm_node; _model_for_task(); trace callbacks |
| `src/terminal_agent/trace.py` | New: LocalTraceCallback + get_trace_callbacks() |
| `src/terminal_agent/tools/git.py` | New: git_status, git_diff, git_log, git_commit |
| `src/terminal_agent/tools/lsp.py` | New: lsp_check, lsp_symbols |
| `src/terminal_agent/tools/memory.py` | New: load_memories(), save_memory() |
| `src/terminal_agent/tools/mcp_server.py` | New: FastMCP serve_stdio() + serve_http(); +edit_file_tool +fetch_url |
| `src/terminal_agent/tools/web_fetch.py` | New: web_fetch tool (HTML→Markdown, urllib only) |
| `src/terminal_agent/cli.py` | mcp subcommand, --trace flag, _save_session_memory(), session_id; --dir flag + _run_once working_dir param (2026-05-14) |
| `pyproject.toml` | Added mcp>=1.0 dependency |
| `scripts/compare_models.py` | New: multi-model bench comparison |
| `scripts/build-push.sh` | New: build → push → rollout script (--dry-run, --build-only, --tag) |
| `Dockerfile` | uv.lock-based reproducible build, OCI labels, layer-cached deps |
| `k8s/deployment.yaml` | readinessProbe, AGENT_SUPERVISOR/AGENT_CODEACT env vars, specialist model comments |
| `70-tools/etzhayyim/etzhayyim/code.go` | 2026-05-14: rewrite — remove aider/codex; runCode() → runCodeAgent(); runCodeExec() → uv run agent --local --message --dir |
