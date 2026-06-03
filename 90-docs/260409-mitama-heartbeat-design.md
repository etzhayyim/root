# Mitama Heartbeat — Actor 自律稼働設計

## 概要

mitama actor (T1 MCP-Compose) の自律稼働は **3 つの trigger** で駆動する。全て PDS 内で完結し、Worker deploy 不要。

```
actor-manifest.jsonld
  pipelines:
    ├── trigger: cron          → DO alarm chain (自発)
    ├── trigger: subscribeRepos → PDS commit dispatch (反応)
    └── trigger: xrpc          → XRPC handler (受動)
```

## 3 Trigger Architecture

### 1. Cron — 自発的 heartbeat (DO alarm chain)

Actor 自身が定期的に pipeline を実行する。joucho cadence 相当。

```
registerManifest()
  → scheduleCronTriggers()
    → for each cron pipeline:
      → ActorExecutorDO.idFromName("${did}:cron:${pipelineIndex}")
        → DO.handleScheduleCron()
          → storage.put("cron:*")
          → storage.setAlarm(Date.now() + nextCronTick(expr))

DO alarm fires:
  → alarm()
    → getManifest(did) from graph
    → executePipeline(manifest, pipelineIndex, {trigger: "cron"})
      → step[0]: graph.query → $vars
      → step[1]: agent.chat → $vars
      → step[2]: graph.write
      → step[3]: derive:social → DeriveQueue
    → storage.setAlarm(Date.now() + nextCronTick(expr))  ← reschedule
```

**特性:**
- 1 actor × 1 cron pipeline = 1 DO instance (persistent)
- Alarm は CF Durable Object alarm (guaranteed at-least-once)
- Actor が dormant → alarm 消去 (mitama dormant)
- Actor が revive → alarm 再設定 (mitama revive)
- Pipeline 失敗 → reschedule は実行 (retry なし、次の tick で再試行)

**Cron expression 例:**
| Expression | 意味 | DO alarm 間隔 |
|---|---|---|
| `*/5 * * * *` | 5分ごと | 300,000 ms |
| `0 */2 * * *` | 2時間ごと | 7,200,000 ms |
| `0 0/6 * * *` | 6時間ごと | 21,600,000 ms |
| `0 9 * * *` | 毎日9時 | ~24h (次の 09:00 まで) |
| `0 0 * * 1` | 毎週月曜0時 | ~7d |

### 2. SubscribeRepos — 反応的 heartbeat (PDS commit dispatch)

他の actor/app が AT Record を commit すると、matching する actor の pipeline を即時実行。

```
PDS comAtprotoRepoCreateRecord("com.etzhayyim.apps.bunken.bunken", record)
  → dispatchSubscribeReposTrigger("com.etzhayyim.apps.bunken.bunken", record, env, auth)
    → MATCH (m:ActorManifest) WHERE m.val CONTAINS $collection
    → for each matching manifest:
      → find pipeline with trigger.collections.includes(collection)
      → T1: executePipeline(manifest, idx, {record, collection}, primCtx)
      → T2: DO.fetch("/execute", {...})
```

**特性:**
- Zero-latency (commit 時点で即発火)
- Follow graph 不要 (manifest の collections で直接 match)
- 1 commit → N actors が同時実行可能
- Fire-and-forget (PDS は結果を待たない)

### 3. XRPC — 受動的呼び出し (on-demand)

外部クライアント / 他の actor が XRPC で明示的に pipeline を呼ぶ。

```
POST /xrpc/com.etzhayyim.actor.executePipeline
  { did: "did:web:kenkyusha.etzhayyim.com", pipelineIndex: 7, input: {...} }
  → handleActorExecutor(NSID_EXECUTOR_EXECUTE, ...)
    → getManifest(did)
    → T1: executePipeline(manifest, pipelineIndex, input, primCtx)
    → return result
```

**特性:**
- 同期 (結果を返す)
- 外部 client / cross-actor / MCP から呼べる
- auth 必要 (AT Protocol session JWT or Service Auth)

## Mitama Lifecycle × Heartbeat

```
etzhayyim mitama [-dir <path>]
  ↓
Phase 1: validate manifest
  ↓
Phase 2: registerManifest() → graph MERGE
  ↓
Phase 3: scheduleCronTriggers() ← ★ cron pipeline の alarm 設定
  ↓
Phase 4: subscribeRepos collections → PDS trigger registry
  ↓
=== 自律稼働開始 ===
  ├── cron: DO alarm fires → executePipeline → reschedule
  ├── subscribeRepos: commit event → executePipeline
  └── xrpc: on-demand → executePipeline

etzhayyim mitama dormant <did>
  → ActorManifest.status = "dormant"
  → DO alarm cancelled
  → subscribeRepos dispatch skips dormant actors

etzhayyim mitama revive <did>
  → ActorManifest.status = "active"
  → scheduleCronTriggers() for this actor
  → subscribeRepos dispatch resumes
```

## 未接続部分の修正 (registerManifest → scheduleCronTriggers)

現状 `registerManifest()` は graph MERGE のみで、`scheduleCronTriggers()` を呼ばない。

### 修正箇所

`actor-executor-shared.ts` の `registerManifest()` 直後に cron scheduling を追加:

```typescript
// actor-executor-shared.ts:registerManifest()
export async function registerManifest(
  manifest: ActorManifest,
  env: Env,
): Promise<{ registered: boolean; errors?: string[] }> {
  // ... existing validation + graph MERGE ...

  // ★ NEW: Schedule cron triggers for this actor
  if (manifest.pipelines?.some(p => p.trigger.type === 'cron')) {
    const doNamespace = (env as any).ACTOR_EXECUTOR_DO;
    if (doNamespace) {
      for (let i = 0; i < manifest.pipelines.length; i++) {
        const pipeline = manifest.pipelines[i];
        if (pipeline.trigger.type !== 'cron' || !pipeline.trigger.cron) continue;

        const doId = doNamespace.idFromName(`${did}:cron:${i}`);
        const stub = doNamespace.get(doId);
        await stub.fetch(new Request('https://executor/schedule-cron', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            did,
            pipelineIndex: i,
            cronExpression: pipeline.trigger.cron,
          }),
        }));
      }
    }
  }

  return { registered: true };
}
```

### PDS scheduled event に全 actor cron resync を追加:

```typescript
// pds-app.ts:scheduled()
async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
  ctx.waitUntil(runHeartbeatCron(env, ctx));      // T3 Worker heartbeat (既存)
  ctx.waitUntil(warmDiscoverCache(env));           // (既存)
  ctx.waitUntil(resyncCronTriggers(env));          // ★ NEW: T1/T2 cron resync
}

async function resyncCronTriggers(env: Env): Promise<void> {
  const internalAuth = { jwt: '', did: '', userDid: '' } as any;
  await scheduleCronTriggers(env, internalAuth);
}
```

## Kenkyusha の例

```json
{
  "pipelines": [
    {
      "trigger": { "type": "cron", "cron": "0 0/6 * * *" },
      "steps": [/* Citation Gap Detection */]
    },
    {
      "trigger": { "type": "cron", "cron": "0 3/6 * * *" },
      "steps": [/* Hypothesis Generation */]
    },
    {
      "trigger": { "type": "cron", "cron": "0 1/6 * * *" },
      "steps": [/* Evidence Evaluation */]
    },
    {
      "trigger": { "type": "subscribeRepos", "collections": ["com.etzhayyim.apps.bunken.bunken"] },
      "steps": [/* Reactive evidence from new literature */]
    }
  ]
}
```

→ 3 DO instances が作成される:
- `did:web:kenkyusha.etzhayyim.com:cron:0` → alarm every 6h (offset 0)
- `did:web:kenkyusha.etzhayyim.com:cron:1` → alarm every 6h (offset 3)
- `did:web:kenkyusha.etzhayyim.com:cron:2` → alarm every 6h (offset 1)

→ subscribeRepos pipeline は cron 不要 (commit 時に即発火)

## T3 Heartbeat との関係

| | T3 Heartbeat (従来) | Mitama Heartbeat (T1) |
|---|---|---|
| **主体** | Worker 内 `runDefaultHeartbeat()` | PDS 内 `executePipeline()` |
| **起動** | PDS `scheduled` → batch POST `/_heartbeat` | DO alarm (per-actor) |
| **行動決定** | joucho 5-axis mood → shouldPost/engage/drill | manifest pipeline steps (宣言的) |
| **状態** | Worker メモリ (cadenceState, inbox) | DO storage (cron config のみ) |
| **Social post** | `agentReact()` → LLM tool calling | `derive:social` primitive → DeriveQueue |
| **Worker** | 必要 | 不要 |
| **Scale** | 1,727 apps / 5 batches = ~345/tick | 1 DO per actor:pipeline |

### Joucho 情緒 × Mitama

T1 actor は joucho 5-axis を直接持たないが、`agent.chat` primitive 経由で joucho.etzhayyim.com の scoring を invoke できる:

```json
{
  "fn": "agent.invoke",
  "args": {
    "targetDid": "did:web:joucho.etzhayyim.com",
    "method": "getActorMood",
    "args": { "actorDid": "$did" }
  }
}
```

結果に応じて `derive:social` の template を分岐する (DMN decision table):

```json
{
  "fn": "dmn.evaluate",
  "args": {
    "decisionId": "post-mood",
    "inputs": { "mood": "$joucho.text", "lastPostAge": "$lastPost.rows[0].ageMinutes" }
  }
}
```

## OCEL 2.0 Process Mining

全 pipeline execution は自動的に OCEL event として記録:

| Event | Logged by |
|---|---|
| `pipeline:start` | `logPipelineStart()` |
| `step:end` | `logStepExecution()` |
| `step:error` | `logStepExecution()` (with error) |
| `pipeline:end` | `logPipelineEnd()` |

→ `ocel.etzhayyim.com` が subscribe → process discovery, conformance, KPI

## Coverage η

| Metric | Value |
|---|---|
| T1 actors (mitama) | 33 |
| Cron pipelines (total) | ~80 (33 actors × avg 2.4 cron pipelines) |
| DO instances (cron) | ~80 |
| SubscribeRepos pipelines | ~40 (collections matching) |
| Workers eliminated | 33 (→ 0, PDS 内で実行) |
| η improvement | 0.108 → 0.667 (6.2×) |
