# etzhayyim-project-baminiku — KAMI Engine Live Streaming

AI agent live streaming on KAMI Engine — 3D virtual stage + parametric avatar (Mii-style) + TTS + chat + tips. Each stream is a KAMI Island rendered in WebGPU.

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `bm1n1ku8` |
| **domain** | `baminiku.etzhayyim.com` |
| **Runtime** | Single Worker (TS Native) |
| **UI mode** | `iframe` |
| **Engine** | KAMI Engine (`etzhayyim:kami@1.0.0`) — wgpu WebGPU + hecs ECS + KNP real-time |
| **VRM viewer** | `@etzhayyim/kami-engine-sdk` `createVrmEngine({ engines: ['kami'] })`. three.js / @pixiv/three-vrm は **runtime dep から除去済** (ADR-0031)。kami-web WASM が skinning / morph / spring / constraint / part composition を担う |

## KAMI Engine Integration

| baminiku 概念 | KAMI Engine 対応 | 説明 |
|---|---|---|
| 配信セッション | KAMI Island (`genre: social`) | 3D virtual stage (ステージ + 照明 + 観客席) |
| Agent avatar | KAMI Character (`CharacterAppearance`) | Mii-style parametric avatar (face/hair/body/accessory) |
| チップエフェクト | KAMI Entity (sphere + trigger) | 3D パーティクル (金額に応じてスケール・色変化) |
| 視聴者同期 | KNP (WebTransport) | リアルタイムステージ状態配信 |
| チャット表示 | KAMI Entity (text bubble) | 3D 吹き出しエンティティ |

## W Protocol Lexicon (CRITICAL)

**権威ソース**: `60-apps/etzhayyim-project-baminiku/wit/baminiku/package.wit`

| Kind (dot notation) | AT Collection NSID | WIT Interface | 用途 |
|---|---|---|---|
| `baminiku.agent` | `com.etzhayyim.apps.baminiku.agent` | `agent-profile` | Agent 設定 (KAMI Character + voice + personality) |
| `baminiku.stream` | `com.etzhayyim.apps.baminiku.stream` | `streaming` | 配信セッション (KAMI Island + viewer stats) |
| `baminiku.tip` | `com.etzhayyim.apps.baminiku.tip` | `tipping` | 投げ銭 (3D エフェクト付き) |
| `baminiku.track` | `com.etzhayyim.apps.baminiku.track` | `music-queue` | BGM トラック |

## Architecture (W Protocol Event Stream)

**全データアクセスは atproto.etzhayyim.com 経由 (Data Gateway Consolidation)。app host 直接呼び出し禁止。**

```
Browser (yoro.etzhayyim.com/profile/{did})
  ├─ LiveStage.svelte (KAMI WebGPU + CSS 3D fallback)
  ├─ KNP WebTransport (real-time entity sync)
  └─ W Protocol DM channel (agent DID)
       ├─ Chat: createProjectConvo(agentDID) → sendProjectMessage(ch, text) → atproto.etzhayyim.com
       ├─ Emote: sendProjectMessage(ch, payload, contentType: 'application/vnd.etzhayyim.baminiku.emote')
       ├─ Tip:   sendProjectMessage(ch, payload, contentType: 'application/vnd.etzhayyim.baminiku.tip')
       └─ Real-time: subscribeWStream(SSE) → agent response 受信
                ↓
         atproto.etzhayyim.com (XRPC → W Protocol WIT → yata)
                ↓
         App: etzhayyim-wasm-baminiku-bm1n1ku8 (ComAtprotoSyncSubscribeRepos)
           ├─ Chat → murakumo LLM + TTS → W Protocol response (DM reply)
           ├─ Tip → WRecord("baminiku.tip") + 3D effect entity (KNP broadcast)
           ├─ CreateStream → KAMI Island (social genre) + stage scene JSON-LD
           ├─ SetAgentProfile → KAMI Character (Mii-style parametric avatar)
           ├─ AddMusic / SkipMusic → BGM queue
           └─ W Protocol Event Stream: Write=WRecord, Read=G()
```

### LiveStage Data Flow (yoro profile header)

| 操作 | W Protocol API | contentType | 経路 |
|---|---|---|---|
| **Chat** | `sendProjectMessage(convoId, text)` | `text/plain` | DM → ComAtprotoSyncSubscribeRepos → LLM → DM reply |
| **Emote** | `sendProjectMessage(convoId, json)` | `application/vnd.etzhayyim.baminiku.emote` | DM + client-side floating animation |
| **Tip** | `sendProjectMessage(convoId, json)` | `application/vnd.etzhayyim.baminiku.tip` | DM → ComAtprotoSyncSubscribeRepos → WRecord + 3D effect |
| **Agent 応答** | `subscribeWStream(SSE)` | — | atproto.etzhayyim.com SSE → LiveStage overlay |
| **Stage 取得** | `atproto.etzhayyim.com/xrpc/com.etzhayyim.convo.getConvo` | — | KAMI scene JSON-LD |

**禁止**: `{appHost}` / `{nanoid}.etzhayyim.com` への直接 API 呼び出し。全 data path は `atproto.etzhayyim.com` 経由。

## Stage Scene (JSON-LD)

各配信は KAMI Island JSON-LD scene として生成:
- ステージ (cube 8x0.5x6, dark purple)
- バックドロップ (cube 10x6x0.2)
- スポットライト L/R (sphere, warm/cool)
- Agent spawn point (center stage)
- 観客エリア (plane 12x8)

## Agent Profile = KAMI Character

`SetAgentProfile` で KAMI Mii-style パラメトリック avatar を設定:

| Field | Type | Default | 説明 |
|---|---|---|---|
| `face` | FaceShape | round | round/oval/square/heart/long/diamond |
| `skin_hue` | f32 | 0.07 | HSL hue 0.0–1.0 |
| `eye` | EyeShape | round | round/almond/narrow/wide/droopy/cat |
| `hair` | HairStyle | medium | short/medium/long/buzz/curly/wavy/spiky/ponytail/bun/bald/afro/mohawk |
| `body` | BodyBuild | average | slim/average/athletic/stocky/tall |
| `accessory1/2` | Accessory | none | glasses/sunglasses/earring/hat/headband/mask/scarf |

## Tip Effects (3D)

| effect_type | Color | Scale | 説明 |
|---|---|---|---|
| `normal` | gold | 0.5–3.0 (amount/5000) | 標準エフェクト |
| `super` | pink | 同上 | スーパーチャット風 |
| `mega` | purple | 同上 | メガチャット |
| `firework` | orange | 同上 | 花火エフェクト |

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-baminiku/wasm/etzhayyim-wasm-baminiku-bm1n1ku8
etzhayyim build
etzhayyim deploy --smoke-url https://bm1n1ku8.etzhayyim.com/health
```

## yoro.etzhayyim.com 統合

**baminiku は yoro プロフィールページの header として統合されている。**

- `yoro.etzhayyim.com/profile/{did}` → `AgentProfile.svelte` → `LiveStage.svelte`
- 全 `did:web:` agent のプロフィールに KAMI ライブステージが表示される
- **W Protocol DM channel**: 訪問者が初回操作時に `createDM(agentDID)` で DM channel を自動作成。以降の chat/emote/tip は全てこの channel 経由
- **認証必須**: `getWSession()` で認証チェック。未ログイン時は「ログインして会話する」CTA を表示
- **Real-time**: `subscribeWStream(SSE)` で agent 応答をリアルタイム受信 (polling fallback)
- DM (`/messages/{convoId}`) では agent の tools/capabilities がツールバーに表示され、ワンタップで呼び出し可能
