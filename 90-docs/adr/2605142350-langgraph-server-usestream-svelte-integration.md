---
id: langgraph-server-usestream-svelte-integration
title: LangGraph Server Wire Protocol + @langchain/svelte useStream Adoption
status: active
doc_type: adr
topic: streaming-ai-chat
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - langchain-svelte-usestream
  - langgraph-server-protocol
  - chat-shell-streaming
  - yoro-convo-streaming
related:
  - chat-shell-apex-bringup-phase1
  - langgraph-server-granian-l3-runtime
  - langgraph-agent-loop-pattern
supersedes: []
superseded_by: []
---

# Context

`etzhayyim-chat-shell` (`etzhayyim.com`) and `yoro.etzhayyim.com` both stream AI responses
to the browser.  Before this ADR the chat-shell used a hand-rolled
`for await (const event of streamChat(...))` SSE loop in `ChatPanel.svelte`,
and yoro's `ConvoHome.svelte` used `graphRAG.query()` (local WebLLM) with no
fallback streaming path for the server-side LLM response.

`@langchain/svelte` ships `useStream`, a Svelte 5 composable that speaks the
LangGraph Server v2 wire protocol natively.  It manages thread creation,
reconnect, reactive `messages` / `isLoading` getters, and `submit()` — all of
which were previously hand-wired.

The LangGraph Server v2 SSE wire protocol is:

```
POST /threads                            → {thread_id}
GET  /threads/{id}                       → {thread_id, status, values, ...}
POST /threads/{id}/commands             → submit input + config
POST /threads/{id}/stream/events        → SSE stream
  {"type":"event","method":"messages","params":{"namespace":[],"data":[<BaseMessage>]}}
  {"type":"event","method":"values","params":{"namespace":[],"data":<state>}}
  {"type":"event","method":"lifecycle","params":{"namespace":[],"data":{"status":"completed"}}}
GET  /assistants/search                 → [{assistant_id, config, ...}]
```

# Decision

**Adopt `@langchain/langgraph-sdk` + `@langchain/svelte` `useStream` as the
standard streaming layer for all Svelte AI chat UIs.**

## Proxy pattern

Each Svelte host adds a thin pass-through route that forwards the LangGraph
Server protocol to the backend pod without business logic:

| Host | Route file | Backend env var |
|---|---|---|
| chat-shell (CF Worker, Hono) | `src/app.ts` `/lg/*` | `CHAT_AGENT_URL` |
| yoro (SvelteKit) | `src/routes/api/pregel/[...path]/+server.ts` | `LG_PREGEL_URL` |

Both proxies forward all headers (including `Authorization` and cookies),
set `x-accel-buffering: no` and `cache-control: no-cache` for SSE, and echo
the request `Origin` in `access-control-allow-origin`.

## LangGraph Server routes in `chat_server.py`

Five aiohttp routes implement the minimum protocol surface required by
`@langchain/svelte` `useStream`:

```python
web.post("/threads",                         lg_post_threads)
web.get ("/threads/{thread_id}",             lg_get_thread)
web.post("/threads/{thread_id}/commands",    lg_post_thread_commands)
web.post("/threads/{thread_id}/stream/events", lg_post_thread_stream_events)
web.get ("/assistants/search",               lg_get_assistants_search)
```

`_lg_run()` bridges the existing `chat_mod.stream_turn()` generator to the
protocol: `delta` → messages event, `final` → values event, `done` →
lifecycle completed, `error` → lifecycle failed.  Threads live in
`_LG_THREADS` in-process dict; subscribers share `_LG_EVENT_SUBS` asyncio
queues.

## `useStream` call sites

### chat-shell `ChatPanel.svelte`

```typescript
const stream = useStream({
  assistantId: "agent",
  apiUrl: "/lg",
  threadId: () => convId || null,
  onThreadId: (id) => { if (!convId) convId = id; },
});
```

The entire manual SSE loop (`for await ... streamChat`) is replaced.
`stream.messages` (reactive `BaseMessage[]`) drives the message list.
The in-flight AI bubble is split as `streamingDelta` from the last message
while `isLoading` is true.

### yoro `ConvoHome.svelte`

```typescript
let lgThreadMap = $state<Record<string, string>>({});
const lgThreadId = $derived(activeConvoId ? (lgThreadMap[activeConvoId] ?? null) : null);
const stream = useStream({
  assistantId: "agent",
  apiUrl: "/api/pregel",
  threadId: () => lgThreadId,
  onThreadId: (id) => {
    if (activeConvoId) lgThreadMap = { ...lgThreadMap, [activeConvoId]: id };
  },
});
```

One LangGraph thread is created per AT Protocol `activeConvoId`.  The
mapping is held in `lgThreadMap` (`$state`).  When the local GraphRAG/WebLLM
is not ready, `handleSend` fires `stream.submit()` instead of `graphRAG.query()`.
A streaming bubble (`streamingDelta`) renders between `FeedTimeline` and
`DMComposer` while `stream.isLoading`.  The AT Protocol history (PDS +
firehose) remains the source of truth; LangGraph streaming is a display-only
fast path.

## Reactivity rules

`useStream` returns a stable object with Svelte 5 getter-based reactive
properties.  **Destructuring breaks reactivity** — always access via the live
handle:

```typescript
// CORRECT
const stream = useStream({ ... });
const msgs = $derived(stream.messages);  // re-runs when messages change

// BROKEN — snapshot at init time, never updates
const { messages } = useStream({ ... });
```

`BaseMessage._getType()` returns `"human" | "ai" | "system"`.  The `id` and
`_getType` fields require type assertions because the SDK types do not expose
them at the TypeScript level.

# Consequences

- Manual SSE parsing in chat-shell `ChatPanel.svelte` is eliminated (~60 LoC).
- Thread lifecycle (create / reconnect / resume) is handled by the SDK.
- Both UIs share the same streaming pattern; new Svelte chat surfaces can
  follow the same three-line `useStream` call.
- `chat_server.py` now serves the LangGraph Server v2 protocol in addition
  to the existing `/api/chat` SSE path.  Both paths call the same
  `chat_mod.stream_turn()` under the hood.
- yoro's AT Protocol DM history and LangGraph streaming are deliberately
  decoupled: LG provides the in-flight preview, PDS/firehose provides
  durable history.  This avoids double-write and keeps the Signal E2E path
  intact for encrypted convos (LG path is skipped when `graphRAG.isLLMReady`).

# Alternatives Considered

- **Keep hand-rolled SSE loop**: rejected.  `useStream` handles reconnect,
  thread creation, and Svelte 5 reactivity with zero boilerplate.
- **Replace yoro AT Protocol DMs with pure LangGraph threads**: rejected.
  AT Protocol DMs carry Signal E2E encryption, firehose federation, and
  the full yoro social graph.  LangGraph threads are stateless compute;
  durable storage belongs in PDS.
- **Use LangGraph `PostgresSaver` checkpointer**: deferred to Phase 2.
  Phase 1 uses in-process `_LG_THREADS` dict (pod restart clears threads,
  acceptable for short-lived sessions).

# References

- `60-apps/etzhayyim-chat-shell/src/app.ts` — `/lg/*` proxy route
- `60-apps/etzhayyim-chat-shell/svelte/src/lib/ChatPanel.svelte` — `useStream` call site
- `60-apps/etzhayyim-chat-shell/svelte/src/lib/api.ts` — `createLangGraphClient()`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/chat_server.py` — LG Server protocol routes
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/api/pregel/[...path]/+server.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/lg-client.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/w/ConvoHome.svelte`
- ADR-2605080600 — LangGraph Server + Granian L3 Runtime
- ADR-2605072000 — LangGraph Agent Loop Pattern
