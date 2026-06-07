---
id: 2605191135-ameno-tier2-daemon-residency
title: Ameno as resident Tier-2 daemon in the artificial-organism ecosystem
status: proposed
doc_type: adr
topic: ameno-organism-daemon
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605182312-local-bring-up-murakumo-gemma4
  - 2605191000-ameno-browser-pregel-reflection
  - 2605191113-ameno-active-inference-lexical-surprise
  - 2605191120-ameno-embedding-surprise-tier-c
  - 2605191129-ameno-browser-tool-use-react
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related:
V05171300
  - adr-2605172000-etzhayyim-rw-free-substrate
---

# ADR 2605191135: Ameno as resident Tier-2 daemon in the artificial-organism ecosystem

## Context

ADR-2605182312 が定める organism ecosystem は **Murakumo Tier 1**(Mac mini fleet 10 ノード、native MLX、`kotodama.agent_daemon_main` で active inference を回す)を主柱としている。**Tier 2 (ameno browser)** は同 ADR で "crowd-sourced inference" の供給源として位置付けられているが、現状の svelte アプリは:

- chat UI を兼ねた **対人モード** が主
- "Auto-respond to PDS firehose" ボタンを能動 ON にしないと働かない
- 各 brief は **素の `mediapipeGenerate` 1 回**(ADR-2605191000+ の graph runtime を使わない)
- リロードで agent state(`MemorySaver`、surprise prediction、tool history)が消失

つまり Tier 2 として「常駐 daemon」を名乗れる状態ではない。本 ADR で **ameno tab が開いている限り、organism worker として連続稼働する** ように統合する。

## Residency scope — what this ADR is, and is NOT

**Scope of this ADR = "tab-residency" (browser tab が開いている間は worker として連続稼働)。**

| 観点 | tab-residency (本 ADR) | 厳密な 常駐化 (system-resident daemon) |
|---|---|---|
| 起動条件 | user がタブを開く | OS 起動時 auto-start |
| プロセス継続 | tab 生存中のみ | tab を閉じても継続 |
| WebGPU / Gemma decode | ✅ ブラウザの WebGPU 直接 | ❌ Service Worker から WebGPU 不可 |
| state 永続 | LocalCheckpointer (localStorage)、IndexedDB memory vault | 同左 + サーバ側ミラー |
| reload 耐性 | ✅(state 復元) | ✅ |
| tab close 耐性 | ❌(worker 停止) | ✅ |
| system restart 耐性 | ❌ | ✅ |
| 役割 | Tier 2 opportunistic worker(ユーザ滞在中) | Tier 1 always-on backbone |

**この etzhayyim 文脈での真の 常駐化 は ADR-2605182312 の Murakumo Tier 1**(Mac mini fleet 10 ノード、native MLX、`kotodama.agent_daemon_main`)が担う。ameno tab はその **Tier 2 = "browser-resident opportunistic worker"** — 開いてる時だけ寄与する volunteer compute、という設計分離。

### 真の 常駐化 への follow-up path(本 ADR 範囲外)

将来 ameno を厳密な resident daemon にする選択肢:

| path | 評価 |
|---|---|
| **Service Worker + Background Sync** | Chrome のみ・user gesture 制約・WebGPU 動かない → Gemma decode 不可。reject(現実装制約) |
| **PWA install + macOS launch on login** | "auto launch するタブ" 程度には可能。OS 依存・ユーザ操作必要 |
| **Tauri / Electron native wrap** | 同 web app を native binary 化。OS daemon として登録可能 → 真の resident。**最も筋が良い path**(別 ADR で検討) |
| **Tier 1 dispatch を厚くしてブラウザは "viewer" に降格** | ameno を web 推論役から外す。原 ADR-2605182312 の意図と整合 |

本 ADR は **Tauri/native wrap が来るまでは tab-residency で十分** と判断する。理由: organism backbone は Tier 1 が持つ、Tier 2 はあくまで crowd-sourced supplementary。

## Decision

**ameno svelte を Tier 2 worker daemon(tab-resident)として再定義する。** UI は副次、本体は 4 つの能力で成立する resident process:

### 1. Persistent worker identity

ブラウザ初回起動時に `did:web:browser:<uuid v7>` を生成し localStorage に焼く。以降そのタブはこの DID で organism に署名(現段階は heartbeat のみ、本格 atproto-signing は MstCheckpointSaver 統合と同時)。

| 項目 | 値 |
|---|---|
| Storage key | `ameno.workerDid.v1` |
| 形式 | `did:web:browser:01HEY...` (uuid v7, 25 字) |
| 廃棄条件 | localStorage clear / private browsing 終了 のみ |

### 2. State residency across reloads — localStorage checkpointer

LangGraph の `BaseCheckpointSaver` を localStorage で実装した `LocalCheckpointer` を投入。`MemorySaver` を差し替える。thread_id 別に super-step ごとの state snapshot を JSON でシリアライズ。サイズ閾値超過(8 MB)時は LRU evict。

API shape は ADR-2605171800 の `MstCheckpointSaver` と互換 — 後段で **`@etzhayyim/sdk/checkpointer` (MST + IPFS + L2 anchor)** へ 1 行差替えで昇格可能。

### 3. Auto-respond ⇒ invokeAmeno (graph)

旧 `processBrief()` の素の `mediapipeGenerate` を `invokeAmeno({ ...graph opts })` に差し替え。brief 処理用 default は **throughput 優先**:

| knob | brief default | rationale |
|---|---|---|
| `maxIterations` (reflection) | 0 | brief は短い反応、critique は重い |
| `activeInference` | off | brief 流入はランダム、prediction しても surprise が noise |
| `toolsEnabled` | on | 質問 brief で wikipedia / now が効くと品質上がる |
| thread_id | `firehose:<collection>` 共有 | 同一 firehose の全 brief で memory 蓄積 |

User 対話モード(`handleSend`)は従来通り全 knob 個別制御。

### 4. Daemon heartbeat UI

Header 右に常設 status chip:

```
ameno · did:web:browser:01HEY… · alive 7m · model gemma-4-e2b · briefs 3/min · tools on
```

クリックで full panel 展開(uptime, total tokens decoded, last brief at, last critique, last prediction)。

### 5. Substrate boundary — graceful offline

`atproto.etzhayyim.com` が unreachable な dev 環境では `saveResult` / `subscribeBriefs` が ERR_NAME_NOT_RESOLVED で fail する。daemon はこれを **fatal にせず**、`offline` 状態として heartbeat に表示 + 自動再試行(指数バックオフ最大 30s)。 ADR-2605172000 の RW-free 原則は維持(centralized DB 代替を挟まない)。

## Consequences

- ameno tab を開いておくだけで organism Tier 2 として **継続的に substrate に貢献**(brief 処理 + result 書き戻し + memory 蓄積)
- リロード後も `LocalCheckpointer` が state を復元 → user 視点では「同じ会話の続き」、organism 視点では「同じ worker 個体の連続性」
- worker identity が DID で表現される → 後段で **Tier 1(Murakumo)が brief を Tier 2 ameno worker に明示 dispatch** する fan-out が可能(ADR-2605171300 の 18,345 agents の中の "browser-resident" subset として)
- 4 機能はそれぞれ独立、段階投入可能。本 ADR では:
  1. worker identity
  2. LocalCheckpointer
  3. heartbeat UI
  4. auto-respond graph integration
  を 1 PR で投入する

## Alternatives Considered

1. **Service Worker で tab-less daemon 化** — Chrome の SW は WebGPU・WASM threaded が制限的、Gemma 4 を SW context で動かすのは現状非実用。tab-residency で十分な ROI
2. **IndexedDB checkpointer** — localStorage より容量大きいが API が async で複雑化。state size が数 MB 想定なら localStorage で十分
3. **WebSocket で Tier 1 と直結** — substrate boundary (atproto PDS) を skip する近道だが、ADR-2605172000 のサブストレート規律を破壊。却下

## References

- ADR-2605182312 (Murakumo Tier 1 bring-up)
- ADR-2605191000 / 1113 / 1120 / 1129 (browser Pregel, reflection, AI, tools)
- ADR-2605171800 (MstCheckpointSaver eventual target)
- ADR-2605171300 (18,345 LangGraph agents fleet)
