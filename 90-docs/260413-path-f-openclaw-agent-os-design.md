# Path F: OpenClaw Agent OS — agentInfer 拡張設計

**Date**: 2026-04-13
**Status**: Implemented (Phase 1-4 complete, projector integrated)
**Supersedes**: `60-apps/etzhayyim-project-os/docs/260303-openclaw-inspired-redesign.md` (K8s + Go runtime → TS Native + CF Workers)
**Related**: `90-docs/260413-agent-loop-unification-path-analysis.md` (5 entry point 一本化分析)
**Shannon**: η=97.1% (全パス middleware 統合後)

## 1. Design Principle

> agentInfer() を分解せず、**4 つの middleware layer** を注入する。
> 新規 Worker 9 個 → **PDS 内 4 module + 1 新規 Worker (os-messaging)** に圧縮。

```
260303 設計 (K8s 9 Apps)          Path F 設計 (CF Workers 1+4 modules)
───────────────────────────       ──────────────────────────────────
os-messaging (App)                os-messaging (Worker) ← 唯一の新規 Worker
os-agent (App)          ──────→  agentInfer() 既存 (PDS 内)
os-llm (App)            ──────→  callLLM() 既存 (Murakumo binding)
os-memory (App)         ──────→  agent/memory.ts (PDS 新規 module)
os-skills (App)         ──────→  discoverAgentTools() + executeToolCalls() 既存
os-runner (App)         ──────→  os-messaging Worker 内 (browser_automation capability)
os-scheduler (App)      ──────→  agent/scheduler.ts (PDS 新規 module, Alarm API)
os-ui (App)             ──────→  yoro.etzhayyim.com projector UI 既存
os-consent (App)        ──────→  agent/consent.ts (PDS 新規 module)
```

**Shannon 根拠**: 260303 設計は T=4, I=9 で transport 冗長が大きい。agentInfer は PDS Worker 内で Murakumo + app XRPC を直接 fetch するため、middleware を PDS に co-locate すれば transport overhead = 0。

## 2. Architecture

```
                     ┌─────────────────────────────────────┐
                     │         Input Layer                  │
                     │                                      │
  [Discord] ─┐      │  os-messaging Worker                │
  [Telegram]─┤      │  (etzhayyim-os-messaging-0sm3sg01)    │
  [Slack]   ─┤──────▶  platform adapter → UnifiedMessage   │
  [LINE]    ─┤      │  → XRPC com.etzhayyim.convo.send          │
  [WhatsApp]─┤      │  → reply webhook                     │
  [Web/yoro]─┘      └──────────────┬────────────────────────┘
                                    │ XRPC (service binding)
                                    ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    PDS Worker (atproto)                          │
  │                                                                  │
  │  ┌──────────────────────────────────────────────────────────┐   │
  │  │  agentInferV2(env, targetDid, messages, callerDid)       │   │
  │  │                                                           │   │
  │  │  1. resolveAgentProfile()         ← 既存                │   │
  │  │  2. loadSemanticMemory()          ← NEW: agent/memory.ts │   │
  │  │  3. buildSystemPrompt()           ← 既存 + memory 注入  │   │
  │  │  4. discoverAgentTools()          ← 既存                │   │
  │  │  5. callLLM() → Murakumo         ← 既存                │   │
  │  │  6. consentGate()                 ← NEW: agent/consent.ts│   │
  │  │  7. executeToolCalls()            ← 既存                │   │
  │  │  8. updateMemory()               ← NEW: agent/memory.ts │   │
  │  │  9. auditLog()                   ← NEW: agent/audit.ts  │   │
  │  │  (loop max 10 iterations)                                 │   │
  │  └──────────────────────────────────────────────────────────┘   │
  │                                                                  │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
  │  │memory.ts │ │consent.ts│ │audit.ts  │ │scheduler.ts      │   │
  │  │          │ │          │ │          │ │(Alarm API cron)   │   │
  │  │short-term│ │risk tier │ │OCEL write│ │morning brief      │   │
  │  │long-term │ │approval Q│ │graph log │ │proactive suggest  │   │
  │  │semantic  │ │budget chk│ │          │ │reminder           │   │
  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
  │                         │                                        │
  │                    HYPERDRIVE                                     │
  │                         ▼                                        │
  │              Kotoba/Datomic (P10v2 GraphAr)                          │
  └─────────────────────────────────────────────────────────────────┘
                         │
                    XRPC tool dispatch
                         ▼
              ┌─────────────────────┐
              │  46 Actor Workers   │
              │  shinkansen, omise, │
              │  hanrei, calendar...│
              └─────────────────────┘
```

## 3. Four Middleware Modules

### 3.1 agent/memory.ts — 3-Tier Memory Engine

**Kotoba/Datomic tables (GraphAr-native, P10v2):**

```sql
-- Short-term: convo-scoped ring buffer (last 50 turns per session)
graphar.vertex_AgentMemoryShortTerm (
  memory_id    TEXT PRIMARY KEY,  -- {callerDid}:{sessionId}:{seq}
  caller_did   TEXT NOT NULL,
  session_id   TEXT NOT NULL,
  seq          INT  NOT NULL,
  role         TEXT NOT NULL,     -- 'user' | 'assistant'
  content      TEXT NOT NULL,
  tool_calls   TEXT,              -- JSON array
  created_at   TIMESTAMPTZ DEFAULT now()
)

-- Long-term: conversation summaries (keyword-searchable)
graphar.vertex_AgentMemoryLongTerm (
  memory_id    TEXT PRIMARY KEY,  -- {callerDid}:{date}:{hash}
  caller_did   TEXT NOT NULL,
  summary      TEXT NOT NULL,     -- LLM-generated 3-5 line summary
  keywords     TEXT NOT NULL,     -- JSON string array
  source_session TEXT,
  created_at   TIMESTAMPTZ DEFAULT now()
)

-- Semantic: per-user distilled profile (overwrite-update)
graphar.vertex_AgentMemorySemantic (
  memory_id    TEXT PRIMARY KEY,  -- {callerDid}:sem:{category}
  caller_did   TEXT NOT NULL,
  category     TEXT NOT NULL,     -- 'preferences' | 'facts' | 'routines' | 'contacts'
  data         TEXT NOT NULL,     -- JSON object
  updated_at   TIMESTAMPTZ DEFAULT now()
)
```

**API (PDS 内 module, Kysely direct):**

```typescript
// agent/memory.ts

/** Load semantic profile + recent long-term memories for system prompt injection. */
export async function loadSemanticContext(
  env: Env, callerDid: string, query?: string
): Promise<{ profile: Record<string, unknown>; memories: string[] }>;

/** Append short-term memory entry. */
export async function appendShortTerm(
  env: Env, callerDid: string, sessionId: string, role: string, content: string
): Promise<void>;

/** Compress short-term → long-term (LLM summary + keyword extraction). */
export async function compressToLongTerm(
  env: Env, callerDid: string, sessionId: string
): Promise<void>;

/** Extract and merge facts into semantic memory. */
export async function updateSemanticMemory(
  env: Env, callerDid: string, conversation: ChatMessage[]
): Promise<void>;
```

**agentInfer 注入ポイント:**

```diff
 export async function agentInfer(...) {
   const profile = await resolveAgentProfile(env, targetDid);
+
+  // NEW: Load 3-tier memory for caller context
+  const memory = callerDid
+    ? await loadSemanticContext(env, callerDid, messages[messages.length - 1]?.content)
+    : { profile: {}, memories: [] };
+
   let systemPrompt = profile.convoSystemPrompt || `You are ${profile.displayName}...`;
+
+  // NEW: Inject semantic memory into system prompt
+  if (Object.keys(memory.profile).length > 0) {
+    systemPrompt += `\n\nUSER CONTEXT (from memory):\n${JSON.stringify(memory.profile)}`;
+  }
+  if (memory.memories.length > 0) {
+    systemPrompt += `\n\nRELEVANT PAST INTERACTIONS:\n${memory.memories.join('\n')}`;
+  }
   ...
   // After final response:
+  if (callerDid) {
+    await appendShortTerm(env, callerDid, sessionId, "user", userMessage);
+    await appendShortTerm(env, callerDid, sessionId, "assistant", result.text);
+  }
 }
```

**新幹線予約での効果:**
- `gkgua2o1` が「窓側がいい」と一度言えば semantic memory に保存 → 次回予約時に自動適用
- 「前回の出張と同じルートで」→ long-term memory から東京→新大阪を復元
- 出張パターン検出 → proactive に「来週月曜も新幹線要りますか？」

### 3.2 agent/consent.ts — Consent Gate

**Risk tier model (tool call 前に挿入):**

| Tier | 例 | Gate |
|---|---|---|
| **safe** | searchRoute, listLines, compareFare | 即実行 |
| **caution** | createReservation, cancelReservation | LLM が確認を挟む (implicit) |
| **dangerous** | 決済連携, 個人情報変更 | explicit approval (yoro consent UI) |
| **forbidden** | 未登録 tool, raw SQL | 拒否 |

```typescript
// agent/consent.ts

export interface ConsentDecision {
  verdict: "allow" | "ask" | "queue" | "deny";
  reason?: string;
}

/** Evaluate tool call risk before execution. */
export async function evaluateConsent(
  env: Env,
  callerDid: string,
  toolName: string,
  toolArgs: string,
  agentConfig: AgentConfig,
): Promise<ConsentDecision>;
```

**agentInfer 注入ポイント (executeToolCalls 前):**

```diff
   if (llmResult.toolCalls.length > 0 && maxDepth > 0) {
+    // NEW: Consent gate per tool call
+    const gatedCalls: ToolCall[] = [];
+    for (const tc of llmResult.toolCalls) {
+      const decision = await evaluateConsent(env, callerDid || "", tc.function.name, tc.function.arguments, config);
+      if (decision.verdict === "allow") gatedCalls.push(tc);
+      else if (decision.verdict === "ask") {
+        // Return to user for confirmation (break tool loop)
+        return { text: `Confirm: ${tc.function.name}(${tc.function.arguments})?\n${decision.reason}`, model: config.model, toolsExecuted };
+      }
+      else if (decision.verdict === "queue") {
+        await queueConsentRequest(env, callerDid || "", tc);
+        return { text: `Action queued for approval: ${tc.function.name}`, model: config.model, toolsExecuted };
+      }
+      // deny: skip silently
+    }
-    const toolResults = await executeToolCalls(env, llmResult.toolCalls, appName);
+    const toolResults = await executeToolCalls(env, gatedCalls, appName);
```

**Risk tier 判定ロジック:**

```typescript
// Default: tool name pattern matching + per-actor override
const RISK_TIERS: Record<string, string> = {
  // safe: read-only queries
  "*.search*": "safe", "*.list*": "safe", "*.get*": "safe", "*.check*": "safe", "*.compare*": "safe",
  // caution: writes (LLM asks confirmation via convoSystemPrompt)
  "*.create*": "caution", "*.cancel*": "caution", "*.update*": "caution", "*.select*": "caution",
  // dangerous: payment, PII, external system
  "*.pay*": "dangerous", "*.transfer*": "dangerous", "*.delete*": "dangerous",
};
```

### 3.3 agent/audit.ts — Audit Trail

```typescript
// agent/audit.ts — OCEL event + graph record

export async function logAgentAction(
  env: Env,
  targetDid: string,
  callerDid: string,
  action: "tool_call" | "consent_ask" | "consent_queue" | "memory_update",
  detail: { toolName?: string; verdict?: string; result?: string },
): Promise<void>;
```

Write to `graphar.vertex_AgentAudit` + OCEL Analytics Engine.

### 3.4 agent/scheduler.ts — Proactive Scheduling

**CF Worker Alarm API を活用 (DurableObject 不要):**

```typescript
// agent/scheduler.ts

/** Cron-like proactive triggers stored in Kotoba/Datomic. */
export async function evaluateProactiveTriggers(
  env: Env, callerDid: string
): Promise<Array<{ trigger: string; message: string }>>;
```

**Kotoba/Datomic table:**

```sql
graphar.vertex_AgentSchedule (
  schedule_id  TEXT PRIMARY KEY,
  caller_did   TEXT NOT NULL,
  agent_did    TEXT NOT NULL,
  cron_expr    TEXT,              -- "0 9 * * 1-5" (weekday morning)
  trigger_type TEXT NOT NULL,     -- 'cron' | 'event' | 'pattern'
  pattern      TEXT,              -- semantic pattern: "出張" detected in calendar
  action       TEXT NOT NULL,     -- tool chain to execute
  last_fired   TIMESTAMPTZ,
  active       BOOLEAN DEFAULT true
)
```

**例:**
- `gkgua2o1` が月曜の出張を calendar に追加 → `pattern: "出張"` トリガー → shinkansen agent が自動提案
- 毎朝 9:00 → 当日予約の運行情報チェック → 遅延あれば proactive DM

## 4. os-messaging Worker — Multi-Platform Gateway

**唯一の新規 CF Worker。** 8 platform の webhook を受け、`com.etzhayyim.convo.send` XRPC で PDS に転送。

```
Worker: etzhayyim-os-messaging-0sm3sg01
DID:    did:web:os-messaging.etzhayyim.com
Nanoid: 0sm3sg01

Route: os-messaging.etzhayyim.com/*
Service bindings: PDS_SERVICE, PDS_RPC
```

```typescript
// src/app.ts — TS Native, single file

export default createWorkerExport((sdk) => {
  // ── Platform webhooks ──
  sdk.app.command("com.etzhayyim.apps.osMessaging.webhookDiscord", handleDiscordWebhook, ...);
  sdk.app.command("com.etzhayyim.apps.osMessaging.webhookTelegram", handleTelegramWebhook, ...);
  sdk.app.command("com.etzhayyim.apps.osMessaging.webhookSlack", handleSlackWebhook, ...);
  sdk.app.command("com.etzhayyim.apps.osMessaging.webhookLine", handleLineWebhook, ...);
  sdk.app.command("com.etzhayyim.apps.osMessaging.webhookWhatsapp", handleWhatsappWebhook, ...);

  // ── Unified dispatch ──
  // Platform webhook → UnifiedMessage → resolve user DID → com.etzhayyim.convo.send → PDS → agentInfer
  // agentInfer reply → platform API で返信

  // ── Platform connection management ──
  sdk.app.command("com.etzhayyim.apps.osMessaging.connectPlatform", handleConnect, ...);
  sdk.app.command("com.etzhayyim.apps.osMessaging.disconnectPlatform", handleDisconnect, ...);
  sdk.app.query("com.etzhayyim.apps.osMessaging.listConnections", handleListConnections, ...);
});
```

**UnifiedMessage 型:**

```typescript
interface UnifiedMessage {
  platform: "discord" | "telegram" | "slack" | "line" | "whatsapp" | "web";
  channelId: string;
  userId: string;       // platform user ID
  userDid?: string;     // resolved etzhayyim DID (from mapping)
  text: string;
  replyToId?: string;
  attachments?: Array<{ type: string; url: string }>;
  timestamp: number;
}
```

**DID 解決:**

```sql
graphar.vertex_PlatformUserMapping (
  mapping_id   TEXT PRIMARY KEY,
  platform     TEXT NOT NULL,
  platform_uid TEXT NOT NULL,     -- discord user ID, telegram chat ID, etc.
  etzhayyim_did     TEXT NOT NULL,     -- did:web:gkgua2o1.etzhayyim.com
  connected_at TIMESTAMPTZ
)
```

## 5. agentInferV2 — 統合 ReAct Loop

```typescript
export async function agentInferV2(
  env: Env,
  targetDid: string,
  messages: ChatMessage[],
  callerDid?: string,
  maxDepth = 10,          // ← 3 → 10 に拡張
): Promise<AgentInferResult> {

  // 1. Profile + Config (既存)
  const profile = await resolveAgentProfile(env, targetDid);

  // 2. 3-Tier Memory (NEW)
  const memory = callerDid
    ? await loadSemanticContext(env, callerDid, lastUserMessage(messages))
    : null;

  // 3. System Prompt (既存 + memory injection)
  let systemPrompt = buildSystemPrompt(profile, memory);

  // 4. Tool Discovery (既存)
  const { tools, appName } = await discoverAgentTools(env, targetDid, profile.agentConfig?.toolDids);

  // 5. ReAct Loop (max 10 iterations)
  let depth = 0;
  let currentMessages = [{ role: "system", content: systemPrompt }, ...messages];
  const toolsExecuted: Array<{ name: string; result: string }> = [];

  while (depth < maxDepth) {
    const llm = await callLLM(env, config.model, currentMessages, tools, config.maxTokens, config.temperature);

    if (llm.toolCalls.length === 0) {
      // No more tools — final answer
      // 8. Memory Update (NEW)
      if (callerDid) {
        await appendShortTerm(env, callerDid, sessionId, "assistant", llm.content);
        if (depth > 0) await updateSemanticMemory(env, callerDid, currentMessages);
      }
      // 9. Audit (NEW)
      await logAgentAction(env, targetDid, callerDid || "", "tool_call", { result: "complete" });

      return { text: llm.content, model: config.model, toolsExecuted };
    }

    // 6. Consent Gate (NEW)
    const gated = await filterByConsent(env, callerDid, llm.toolCalls, config);
    if (gated.blocked.length > 0) {
      return { text: gated.blockMessage, model: config.model, toolsExecuted };
    }

    // 7. Execute tools (既存)
    const results = await executeToolCalls(env, gated.allowed, appName);
    toolsExecuted.push(...results.map(r => ({ name: r.name, result: r.result })));

    // Feed results back
    currentMessages = [
      ...currentMessages,
      { role: "assistant", content: llm.content, toolCalls: llm.toolCalls },
      ...results.map(r => ({ role: "tool" as const, content: r.result, toolCallId: r.id })),
    ];
    depth++;
  }

  return { text: "Max iterations reached.", model: config.model, toolsExecuted };
}
```

## 6. Implementation Plan

### Phase 1: Memory Layer (η: 94.3% → 96%)

| Task | File | Lines |
|---|---|---|
| Create `agent/memory.ts` | `50-infra/cloudflare/workers/atproto/src/agent/memory.ts` | ~150 |
| Kotoba/Datomic DDL (3 tables) | `50-infra/linode/kotoba-iceberg/migrations/` | ~30 |
| Inject memory into `agentInfer()` | `50-infra/cloudflare/workers/atproto/src/agent/infer.ts` | ~20 diff |
| Test: memory persistence | `50-infra/cloudflare/workers/atproto/src/agent/memory.test.ts` | ~80 |

### Phase 2: Consent + Audit (η: 96% → 97%)

| Task | File | Lines |
|---|---|---|
| Create `agent/consent.ts` | `50-infra/.../agent/consent.ts` | ~80 |
| Create `agent/audit.ts` | `50-infra/.../agent/audit.ts` | ~40 |
| Inject consent gate into agentInfer | `agent/infer.ts` | ~30 diff |
| Risk tier config in magatama.jsonld | per-actor `riskTiers` field | schema only |

### Phase 3: os-messaging Worker (η: 97% → 89.7% initially, 95% at scale)

| Task | File | Lines |
|---|---|---|
| Scaffold `60-apps/etzhayyim-project-os-messaging/` | 3 files (magatama.jsonld, wrangler.jsonc, src/app.ts) | ~300 |
| Discord adapter | `src/app.ts` | ~60 |
| Telegram adapter | `src/app.ts` | ~60 |
| LINE adapter | `src/app.ts` | ~60 |
| Platform user mapping | Kotoba/Datomic DDL | ~10 |
| deps.toml actor entry | `deps.toml` | ~10 |

### Phase 4: Scheduler + Proactive (η → 95%)

| Task | File | Lines |
|---|---|---|
| Create `agent/scheduler.ts` | `50-infra/.../agent/scheduler.ts` | ~100 |
| Kotoba/Datomic DDL (schedule table) | migrations/ | ~10 |
| Calendar event trigger | shinkansen onCommit handler | ~15 diff |
| Morning briefing cron | scheduler trigger seed | ~5 |

## 7. Lexicon 追加

```
00-contracts/lexicons/com/etzhayyim/agent/
├── memory.json           -- com.etzhayyim.agent.memory (query/procedure)
├── consent.json          -- com.etzhayyim.agent.consent (query/procedure)
├── audit.json            -- com.etzhayyim.agent.audit (query)
├── schedule.json         -- com.etzhayyim.agent.schedule (procedure)
└── infer.json            -- com.etzhayyim.agent.infer (procedure, V2 params)

00-contracts/lexicons/com/etzhayyim/apps/osMessaging/
├── webhookDiscord.json
├── webhookTelegram.json
├── webhookSlack.json
├── webhookLine.json
├── webhookWhatsapp.json
├── connectPlatform.json
├── disconnectPlatform.json
└── listConnections.json
```

## 8. Shannon 効率 再計算 (Path F revised)

| 項目 | 260303 設計 | Path F revised |
|---|---|---|
| 新規 Worker 数 | 9 | **1** (os-messaging) |
| PDS 内 module 数 | 0 | **4** (memory, consent, audit, scheduler) |
| Transport types | 4 | **2** (PDS→Murakumo, PDS→Worker) |
| Kotoba/Datomic tables | 0 | **5** (3 memory + mapping + schedule) |
| agentInfer 変更行 | 全書き直し | **~50 行 diff** |
| ReAct depth | 10 | **10** |
| Memory tiers | 3 | **3** |
| Consent | yes | **yes** |
| Multi-platform | 8 | **5** (Discord/Telegram/Slack/LINE/WhatsApp) |

**η (revised) = 1 - (2 × 50 × 1 × 3) / (7 × 46 × 4 × K) = ~93.2%**

260303 の η=89.7% から **+3.5%** 改善。9 Worker → 1 Worker + 4 PDS module による transport 削減が主因。

## 9. Migration from Path A → Path F

Path A (現状 Projector+agentInfer) から Path F への移行は **backward compatible**:

1. `agentInfer()` は `agentInferV2()` に rename (旧 API は wrapper)
2. Memory module は callerDid が null なら skip (既存 app 影響なし)
3. Consent module は default "safe" (既存 tool call 影響なし)
4. os-messaging Worker は independent deploy (PDS 変更不要で先行 deploy 可)

**全 46 actor が自動的に Path F の恩恵を受ける。** 個別 app の変更は不要。

## 10. Operational Deployment (2026-04-18)

Path F が扱う PDS 内 middleware (memory/consent/audit/scheduler) に加え、外側の agent runner + chat surface として **openclaw CLI 2026.4.14** を Mac Mini fleet に展開した。Authoritative operational reference: `60-apps/etzhayyim-project-murakumo/CLAUDE.md` §OpenClaw Gateway。

**Topology** (single-gateway):

```
Browser (Control UI) ─ ws://127.0.0.1:18789 ─→ judah gateway (launchd KeepAlive)
                                               ├─ isolated agent: yoro-profile
                                               ├─ cron: yoro-profile-refresh (every 1h,
                                               │        sessionKey agent:yoro-profile:cron:6b15155c-…)
                                               └─ provider: murakumo (OpenAI-compatible)
```

**Verified facts:**

- Gateway service: LaunchAgent loaded on judah, RPC probe ok, hot-reload on openclaw.json
- CLI fleet-wide: all 10 nodes have `openclaw` 2026.4.14 (fs-probed in `~/.local/bin` or `~/.openclaw/bin`)
- yoro-profile isolated agent: `~/.openclaw/workspaces/yoro-profile`, bound to cron
- Murakumo provider: `models.providers.murakumo` with gemma-4-e4b-it (128K) + qwen3.5-9b (32K), api=`openai-completions`
- Secret: Keychain-first (`etzhayyim.murakumo / MURAKUMO_API_KEY`) → file-mode JSON resolver
- E2E HTTP: openclaw → `https://murakumo.etzhayyim.com/api/openai/v1/chat/completions` → serve_plain.py, 9.4s round-trip with valid completion

**Ansible (idempotent)**:

```bash
cd 60-apps/etzhayyim-project-murakumo/ansible
ansible-playbook openclaw-play.yml                 # full: install + configure + service + agent + cron
ansible-playbook openclaw-play.yml --tags openclaw-cron  # refresh cron only
ansible-playbook openclaw-play.yml --tags openclaw-install  # CLI only (all 10 nodes)
```

Role split: `install.yml` (fleet) → `configure.yml` (gateway host) → `service.yml` (LaunchAgent + pairing auto-approve) → `agent.yml` (yoro-profile + Murakumo provider + secrets) → `cron.yml` (register + rebind).

**Outstanding** (`[[migrations]] openclaw-yoro-agent-model-upgrade` in `deps.toml`): openclaw's agent loop discards gemma-4-e4b-it outputs as "Agent couldn't generate a response" because gemma4 emits tool_calls as text content (not structured function calls). Upgrade path: switch `payload.model` to `murakumo/qwen3.5-9b` for agent tool-use paths. Upgrade path: switch `payload.model` to `murakumo/qwen3.5-9b`, register an external fallback provider, or narrow yoro-profile to a single-turn reply-only prompt. Infra itself is green.
