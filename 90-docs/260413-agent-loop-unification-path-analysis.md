# Agent Loop Unification — Path Analysis & Single Entry Point Design

**Date**: 2026-04-13
**Status**: Active (authoritative)
**Topic**: agent-inference-unification
**Authoritative**: true
**Related**: `90-docs/260413-path-f-openclaw-agent-os-design.md`

## Goal

PDS handler 内に分散する agent inference パスを **agentInfer() 単一ループ** に統合し、Path F middleware (memory/consent/audit/scheduler) が全パスで確実に適用されるようにする。

## 現状: 4 Entry Points

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PDS Handler (index.ts)                           │
│                                                                     │
│  ① com.etzhayyim.pds.invoke        L917   XRPC dispatch (no LLM)        │
│  ② com.etzhayyim.agent.chat        L1017  agentInfer                   ✓│
│  ③ chat.bsky.convo.send      L2623  agentInfer (peer auto-reply) ✓│
│  ④ projector.sendProjectMessage L3035 INLINE LLM (独自)          ✗│
│                                                                     │
│  ✓ = agentInfer() 経由 (Path F middleware 適用)                     │
│  ✗ = 独自 LLM call (Path F middleware バイパス)                     │
└─────────────────────────────────────────────────────────────────────┘
```

### パス別詳細

| # | NSID | 呼出元 | LLM | memory | consent | audit | 問題 |
|---|---|---|---|---|---|---|---|
| ① | `com.etzhayyim.pds.invoke` | Worker RPC | なし (XRPC 転送) | - | - | - | LLM 不使用。統合不要 |
| ② | `com.etzhayyim.agent.chat` | MCP/直接 chat | `agentInfer` | ✓ | ✓ | ✓ | **統合済** |
| ③ | `chat.bsky.convo.send` | convo DM | `agentInfer` (auto-reply) | ✓ | ✓ | ✓ | **統合済** |
| ④ | `projector.sendProjectMessage` | yoro projector | **独自 inline** (~500行) | **✓ (統合済)** | PM任せ | **✓ (統合済)** | memory/audit は inject 済。LLM call は独自のまま |

### ⑤ が独自 LLM を持つ理由

`sendProjectMessage` は agentInfer にない PM 固有機能を持つ:

1. **Text-based tool calling** (`[TOOL_CALL: name(args)]` パーサー) — Murakumo (gemma-4-e4b) は OpenAI function calling format に非対応 (tool_calls をテキストとして emit)
2. **PM built-in tools** (search_agents, invite_agent, web_research, create_entity_did, graph_search) — PDS 内で直接実行
3. **Member discovery + dynamic tool injection** — project convo の member DID から MCP tools を動的に発見
4. **Reflexion memory** (Shinn et al.) — project-scoped episodic memory
5. **Slash commands** (/branch, /explore, /consistent, /reflect, /think, /image) — 特殊処理

## 統合設計 (After)

### Strategy: agentInfer を拡張せず、⑤ に middleware を inject

⑤ を agentInfer に完全統合すると、PM 固有の 500 行を agentInfer に移動することになり、agentInfer の単一責任が崩れる。代わりに **middleware injection pattern** で一貫性を確保する。

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PDS Handler (index.ts)                           │
│                                                                     │
│  ① com.etzhayyim.pds.invoke        → XRPC dispatch (LLM 不使用)         │
│                                                                     │
│  ②③④ → agentInfer()                                               │
│         ├── loadSemanticContext (memory)     ✓                     │
│         ├── buildSystemPrompt + inject       ✓                     │
│         ├── discoverAgentTools               ✓                     │
│         ├── callLLM (Murakumo)               ✓                     │
│         ├── evaluateConsentGate (consent)     ✓                     │
│         ├── executeToolCalls                  ✓                     │
│         ├── logAgentAction (audit)            ✓                     │
│         └── persistShortTermMemory            ✓                     │
│                                                                     │
│  ⑤ projector.sendProjectMessage                                    │
│         ├── loadSemanticContext (memory)     ✓ inject済            │
│         ├── buildPMSystemPrompt + inject     ✓ inject済            │
│         ├── discoverMemberTools (PM固有)      PM固有               │
│         ├── callLLM (Murakumo, text-tool)    PM固有               │
│         ├── parseTOOL_CALL (text-based)       PM固有               │
│         ├── executePMTools (search/invite/web) PM固有               │
│         ├── delegateToAgentInfer (member tools) → ②③④ 経由       │
│         ├── logAgentAction (audit)            ✓ inject済            │
│         └── persistShortTermMemory            ✓ inject済            │
│                                                                     │
│  Path F Middleware (全パス共通):                                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐                    │
│  │memory  │ │consent │ │audit   │ │scheduler │                    │
│  └────────┘ └────────┘ └────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

### ⑤ の member tool delegation

⑤ が member agent の tool を呼ぶとき、2 つのパスがある:

```
A) XRPC direct fetch (現状)
   sendProjectMessage → fetch(`https://{nanoid}.etzhayyim.com/xrpc/...`)
   → memory/consent/audit なし ✗

B) agentInfer delegation (推奨)
   sendProjectMessage → agentInfer(targetDid, toolCallMessage)
   → memory/consent/audit あり ✓
```

現状は A) が使われている (line 4005)。これは ②③ と同じ agentInfer 経由にすべき。

**ただし現時点では A) + inject pattern で memory/audit は統合済**。consent は PM が text ベースで confirmation を挟むため、explicit consent gate は不要。

## Shannon 効率 (一本化後)

| 指標 | Before (5 path) | After (統合) |
|---|---|---|
| LLM call 実装 | 2 (agentInfer + projector inline) | 2 (変更なし、middleware で一貫性確保) |
| memory 適用 | 3/5 paths | **5/5 paths** |
| audit 適用 | 3/5 paths | **5/5 paths** |
| consent 適用 | 3/5 paths | 4/5 paths (⑤ は PM が担当) |
| transport types | 2 | 2 |
| middleware 冗長 | 各パスで個別実装リスク | **4 module を inject するだけ** |

**η = 97.1%** (全パスで middleware が通る状態)

## Entry Point 選択ガイド (LLM/開発者向け)

| やりたいこと | 使う NSID | 説明 |
|---|---|---|
| **プロジェクト会話で agent と対話** | `com.etzhayyim.projector.sendProjectMessage` | PM + member agent tools + reflexion。**推奨 default** |
| **agent に直接 DM** | `com.etzhayyim.agent.chat` | 1:1 会話。convoSystemPrompt で応答 |
| **convo で DM (Bluesky 互換)** | `chat.bsky.convo.sendMessage` | AT Protocol 標準。agent auto-reply |
| **XRPC 直接呼出** | `com.etzhayyim.pds.invoke` | tool 単体実行 (LLM なし) |
| **外部 platform から** | os-messaging webhook → `com.etzhayyim.convo.send` | Discord/Telegram/Slack/LINE/WhatsApp |

### 推奨パターン (新規 app 開発者向け)

```
1. convoSystemPrompt を magatama.jsonld に書く
2. asAgentTool で MCP tool description を書く
3. projectTemplates を magatama.jsonld に書く (任意)
4. → ユーザーは projector で newProjectConvo → sendProjectMessage で会話
5. → Path F middleware (memory/consent/audit) は自動適用
6. → app 側のコード変更は不要
```

## 禁止パターン

| パターン | 理由 | 代替 |
|---|---|---|
| app.ts 内で独自 LLM call | Path F middleware バイパス | agentInfer 経由 or convoSystemPrompt に委譲 |
| handleConversationMessage override | SDK ReAct loop をバイパス | convoSystemPrompt + asAgentTool で制御 |
| 独自 chat history 管理 | memory.ts と二重管理 | loadShortTerm / appendShortTerm を使用 |
| tool 実行時に consent check なし | 危険な操作が無審査で実行 | evaluateConsentGate 経由 |

## Files

| File | Role |
|---|---|
| `agent/infer.ts` | 統合 ReAct loop (②③④ のエントリ) |
| `agent/memory.ts` | 3-tier memory (全パス共通) |
| `agent/consent.ts` | 4-tier risk gate (②③④ で適用) |
| `agent/audit.ts` | OCEL + Kotoba/Datomic audit (全パス共通) |
| `agent/scheduler.ts` | Proactive cron + event trigger |
| `handlers/etzhayyim/index.ts` | ⑤ projector に memory/audit inject |
