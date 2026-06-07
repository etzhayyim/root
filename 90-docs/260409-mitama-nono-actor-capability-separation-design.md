# Mitama / Nono — Actor-Capability Separation Design

## Problem

現状 397 apps が全て「T3 Worker (app.ts)」として設計されている。しかし実態は:

- **~260 apps**: graph.query + graph.write + agent.chat + derive:social だけで動く (data pipeline)
- **~90 apps**: 上記 + 軽い TS ロジック (reactive pipeline)
- **~27 apps**: CF binding (env.AI, HEADLESS_BROWSER, KV, WebRTC) を握る (infra capability)

全てを同じ「app = Worker」として扱うことで:
- 397 Worker deploy が必要 (CF account limit 500)
- 各 app が build/deploy/wrangler を要求
- actor のビジネスロジックと infra capability が混在
- Shannon η = 0.108 (397 Worker 全独立)

## Solution: mitama (魂) + nono (能) 分離

```
┌─────────────────────────────────────────────────────┐
│                    Cyber Actor (mitama)              │
│  actor-manifest.jsonld → graph MERGE → 自律稼働     │
│  WHO: identity (DID) + WHAT: behavior (pipeline)    │
│  Worker 不要。PDS Shared Executor が実行。           │
│  ~350 actors (T1 MCP-Compose)                       │
├─────────────────────────────────────────────────────┤
│                    Capability (nono)                 │
│  MCP skill provider → Worker deploy (CF binding)    │
│  HOW: compute/IO/external service access            │
│  Actor が agent.invoke で呼ぶ。                      │
│  ~20 nono Workers (T3, infra-level)                 │
└─────────────────────────────────────────────────────┘
```

### mitama (魂) — Cyber Actor

「誰が」「何をするか」を宣言的に定義。graph に存在するだけで「生きている」。

| 属性 | 説明 |
|---|---|
| **定義** | `actor-manifest.jsonld` |
| **実行** | PDS Shared Executor (`executePipeline()`) |
| **Deploy** | `etzhayyim mitama` → `POST /xrpc/com.etzhayyim.actor.registerManifest` → graph MERGE |
| **Worker** | 不要 |
| **Build** | 不要 |
| **wrangler** | 不要 |
| **Trigger** | cron / subscribeRepos / a2aInvoke / xrpc |
| **Capability** | 12 MCP primitives (graph, agent, browser, derive, etc.) |
| **Scale** | ~350 actors (PDS 1 Worker 内で全実行) |
| **η** | 0.667 (zero-code compose) |

### nono (能) — MCP Skill / Host Capability Provider

「どうやって」外部リソースにアクセスするかを提供。Actor が `agent.invoke` で呼ぶ。

| 属性 | 説明 |
|---|---|
| **定義** | `src/app.ts` + `nono-manifest.jsonld` |
| **実行** | 専用 CF Worker (T3) |
| **Deploy** | `etzhayyim nono` → `npx wrangler deploy` (既存 deploy 相当) |
| **Worker** | 必要 (CF binding を握るため) |
| **Build** | esbuild (<1s) |
| **Trigger** | XRPC 受信のみ (actor からの agent.invoke) |
| **役割** | MCP primitive の backend / CF binding holder |
| **Scale** | ~20 nono Workers |

## nono 一覧 (CF binding 必須の capability provider)

→ CF binding 正本: `deps.toml [[nono_workers]]`。以下は `提供 capability` 列を含む拡張ビュー。

| nono | CF Binding | MCP Primitive Backend | 提供 capability |
|---|---|---|---|
| **llm** | `env.AI` (Workers AI) | `agent.chat` | LLM inference (Qwen/Gemma/Claude), SSE streaming, credit gate |
| **site** | `HEADLESS_BROWSER` (Puppeteer) | `browser.fetch` | Headless Chromium, HTML→Markdown, WET/WAT/WebP, Common Crawl |
| **auth** | `AUTH_RPC` service binding, KV | (PDS infra) | WebAuthn/FIDO2, DPoP, ES256 JWT, SMS OTP, Passkey |
| **kagami** | `KAGAMI_RPC` service binding | `graph.query`, `graph.write` | Kotoba/Datomic Cypher→SQL, Hyperdrive, S3 shared_data |
| **pds** | B2, service bindings, Secrets | (host) | AT Protocol commit pipeline, identity, governance |
| **stripe** | Stripe API + Webhooks | — | Payment, card issuing, billing |
| **livecam** | Murakumo fleet (CoreML) | — | YOLO detection, BoT-SORT tracking, cohort hash |
| **mangaka** | `env.AI` (flux-1-schnell) | — | AI image generation, canvas rendering |
| **briefing** | WebRTC (kami-rtc) | — | Real-time audio/video, spatial audio, KNP signaling |
| **celler** | Telnyx SIP + eSIM | — | Telephony, SIP trunk, eSIM provisioning |
| **gazo** | ONNX Runtime WebGPU | — | Browser SD image generation |
| **ameno** | WebGPU (transformers.js) | — | Browser LLM inference (Gemma 4 E2B) |
| **sense** | Camera/LiDAR/WiFi/BT/Mic | — | Sensor fusion, 3D reconstruction |
| **watashi** | CGEvent/Win32 (native) | — | Cross-platform input sharing |
| **browser** | CF Browser Rendering | — | JS rendering, stealth, darkweb |
| **murakumo** | Mac Mini fleet (MLX) | — | On-prem LLM inference (qwen3/VL) |
| **repo** | B2 (Git storage) | — | Git server, repository management |

## Actor → Nono 呼び出しパターン

```
Cyber Actor (mitama)                    Capability Provider (nono)
actor-manifest.jsonld                   src/app.ts (Worker)
┌────────────────────┐                  ┌─────────────────────────┐
│ pipeline step:     │                  │                         │
│ fn: "agent.chat"   │ ──── MCP ────→  │ llm.etzhayyim.com             │
│ args: {message}    │   primitive      │ env.AI → Workers AI     │
│                    │                  │ → inference result      │
│ fn: "browser.fetch"│ ──── MCP ────→  │ site.etzhayyim.com            │
│ args: {url}        │   primitive      │ HEADLESS_BROWSER        │
│                    │                  │ → HTML/Markdown         │
│ fn: "agent.invoke" │ ──── cross-actor ────→  │ livecam.etzhayyim.com         │
│ args: {targetDid,  │   via proxy     │ Murakumo CoreML         │
│        method}     │                 │ → detection result      │
│                    │                  │                         │
│ fn: "graph.query"  │ ──── MCP ────→  │ kagami (Graph Worker)   │
│ args: {cypher}     │   primitive      │ Kotoba/Datomic Hyperdrive    │
│                    │                  │ → rows                  │
└────────────────────┘                  └─────────────────────────┘
```

## mitama lifecycle (Actor)

```
1. 設計:   actor-manifest.jsonld を書く (宣言的)
2. 命:     etzhayyim mitama → registerManifest() → graph MERGE
3. 自律:   PDS Shared Executor が cron/subscribeRepos で executePipeline()
4. 進化:   shinka coverage healing (Murakumo LLM autonomous)
5. 休眠:   status = "dormant" (graph に残る、実行されない)
6. 復活:   koji kyumei → status = "active"
```

No build. No deploy. No Worker. Graph に存在 = 生きている。

## nono lifecycle (Capability)

```
1. 実装:   src/app.ts + nono-manifest.jsonld
2. Build:  etzhayyim nono build → esbuild (<1s)
3. Deploy: etzhayyim nono deploy → CF Worker deploy + smoke test
4. 登録:   nono-manifest → graph MERGE (capability discovery 用)
5. 提供:   actor からの agent.invoke / MCP primitive dispatch を受信
```

Worker deploy が必要だが、数は ~20 に限定。

## nono-manifest.jsonld schema

```json
{
  "@context": "https://etzhayyim.com/ns/nono/v1",
  "@id": "did:web:llm.etzhayyim.com",
  "name": "llm",
  "nanoid": "llm-nanoid",
  "type": "nono",
  "bindings": ["env.AI"],
  "primitiveBackend": ["agent.chat"],
  "skills": [
    {
      "nsid": "com.etzhayyim.apps.llm.infer",
      "description": "LLM inference via CF Workers AI",
      "inputSchema": { "message": "string", "model": "string?" },
      "outputSchema": { "text": "string", "model": "string" }
    },
    {
      "nsid": "com.etzhayyim.apps.llm.inferStream",
      "description": "Streaming LLM inference (SSE)",
      "inputSchema": { "message": "string", "model": "string?" },
      "outputSchema": { "stream": "SSE" }
    }
  ],
  "governance": {
    "classification": "internal",
    "creditGated": true
  }
}
```

## 移行対象の分類

### 現 T3 app.ts → mitama (actor-manifest.jsonld) に移行

全ビジネスロジックが 12 MCP primitives で表現可能な app:

| Category | Apps (例) | 数 |
|---|---|---|
| Identifier registry | isbn, issn, isin, gtin, cas, ndc | ~10 |
| Intelligence pipeline | intel, handotai, malak, yabai, ct-monitor, ipaddress | ~15 |
| Legal/compliance | hanrei, bankruptcy, treaty, nist, completer | ~10 |
| Classification | isic, cpc, unispsc, isco | ~5 |
| Social/community | society6, dojo, shinka, joucho | ~5 |
| Content/media | news, media-anime, media-gamers, kaimono-review | ~10 |
| Government/public | gov, legal-entity, natural-person, chotatsu | ~10 |
| Domain-specific | autorace, keirin, kyotei, pachinko, casino | ~10 |
| Research/knowledge | kenkyusha, bunken, gyotaku | ~5 |
| Governance/ethics | religious, customary, tradition, ethics, blockchain | ~10 |
| Operations | ops, projector, yotei, ocel | ~5 |
| Commerce | okaimono, crowdfunding, kakin, credits | ~5 |
| Well-being | kaigo, omatsuri, soshiki | ~5 |
| Other data apps | dns, sbom, supply-chain, trust, resource-flow, ... | ~50+ |
| **Total** | | **~350** |

### 現 T3 app.ts → nono (capability Worker) として残す

CF binding / crypto / real-time protocol が必須な app:

| nono | 理由 |
|---|---|
| llm | env.AI binding, SSE streaming, credit gate |
| site | HEADLESS_BROWSER, frontier queue, WET/WAT |
| auth | Rust Worker, P-256 ECDSA, KV credentials |
| kagami | Kotoba/Datomic Hyperdrive, S3 shared_data |
| pds | B2, service bindings, AT Protocol host |
| stripe | Stripe API + Webhooks, PCI-DSS |
| livecam | Murakumo CoreML fleet, per-detection DID |
| mangaka | env.AI (flux-1-schnell), canvas pipeline |
| briefing | WebRTC, spatial audio, KNP |
| celler | Telnyx SIP, eSIM, FreeSWITCH |
| gazo | ONNX WebGPU, SD 1.5 pipeline |
| ameno | transformers.js WebGPU, LoRA merge |
| sense | Multi-sensor fusion, WASM compute |
| watashi | Native CGEvent/Win32, mDNS |
| browser | CF Browser Rendering, stealth |
| murakumo | Mac Mini MLX fleet, Starlette |
| repo | B2 Git storage |
| xlsx | HTML DOM grid, 131 formula functions |
| pptx | wgpu WebGPU rendering |
| **Total** | **~20** |

## Shannon 効率比較

| Architecture | Workers | η | Deploy 時間 |
|---|---|---|---|
| 現状: 全 T3 | 397 | 0.108 | 397 × wrangler deploy |
| **mitama + nono**: T1 actors + T3 nono | **20** | **0.667** | 20 × wrangler + 350 × graph MERGE |
| 理論最適: all-in-PDS | 1 | 1.0 | (不可能: CF binding 制約) |

**結果: 397 Workers → 20 Workers。η 6.2× 改善。**

## CLI コマンド設計

```bash
# Actor lifecycle (mitama)
etzhayyim mitama                     # actor-manifest.jsonld → graph MERGE → 自律開始
etzhayyim mitama list                # 全 actor 一覧 (graph query)
etzhayyim mitama inspect <did>       # actor 詳細 (pipelines, capabilities, status)
etzhayyim mitama dormant <did>       # 休眠 (status → dormant)
etzhayyim mitama revive <did>        # 復活 (status → active)

# Capability lifecycle (nono)
etzhayyim nono build                 # esbuild + validation
etzhayyim nono deploy                # CF Worker deploy + skill 登録
etzhayyim nono list                  # 全 nono 一覧
etzhayyim nono skills <nanoid>       # nono が提供する skill 一覧

# Coverage
etzhayyim coverage eta               # system-wide η (mitama + nono)
etzhayyim coverage heal              # shinka autonomous healing
```

## Primitive 拡張: nono が新 MCP primitive を提供

現在の 12 primitives は固定だが、nono が **custom primitive** を追加登録できるようにする:

```json
{
  "primitiveBackend": ["agent.chat"],
  "customPrimitives": [
    {
      "name": "livecam.detect",
      "description": "YOLO object detection on camera frame",
      "inputSchema": { "frameUrl": "string", "model": "string?" },
      "outputSchema": { "detections": "array" }
    }
  ]
}
```

Actor manifest から呼べるようになる:

```json
{
  "fn": "agent.invoke",
  "args": {
    "targetDid": "did:web:livecam.etzhayyim.com",
    "method": "detect",
    "args": { "frameUrl": "$input.frameUrl" }
  }
}
```

## Migration Results (2026-04-09 実行完了)

### Phase 1-3 完了: 33 actors を T1 mitama に移行

→ `deps.toml [[mitama_actors]]` が SSoT (nanoid・domain・location 全量)

### Phase 4 完了: 10 nono Workers 分類

→ `deps.toml [[nono_workers]]` が SSoT (binding・primitive_backend 全量)

### Phase 5 完了: etzhayyim mitama CLI

`70-tools/etzhayyim/etzhayyim/mitama.go` — 実装完了。

```bash
etzhayyim mitama [-dir <path>]     # actor-manifest.jsonld → graph MERGE → 自律開始
etzhayyim mitama list               # 全 T1 actor 一覧
etzhayyim mitama inspect <did>      # manifest 詳細
etzhayyim mitama dormant <did>      # 休眠
etzhayyim mitama revive <did>       # 復活
```

### Final Numbers

```
Before:  45 T3 Workers (全て app.ts + wrangler deploy)
After:   33 mitama (graph MERGE) + 10 nono (Worker) + 1 stub + 1 SDK
Workers: 45 → 10  (33 Workers 削減)
η:       0.108 → 0.667  (6.2× 改善)
```
