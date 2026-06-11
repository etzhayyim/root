---
id: adr-2605170000-deai-spirit-physics-matching
title: "deai — Spirit-in-Physics Matching Platform Architecture"
status: active
doc_type: adr
topic: deai-spirit-physics-matching
authoritative: true
last_verified: 2026-05-18
authoritative_for:
  - deai project architecture
  - Spirit-in-Physics matching algorithm
  - emotion tensegrity matching
  - deai data model
  - deai mobile (Capacitor)
priority: 8.0
axis: product
weight: 0.8
depends_on:
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2604291800-well-becoming-formal-model
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-0018-pii-tier3-cohort-first
related:
  - adr-2604300135-hume-distillation-artifact-persistence
  - adr-2605141600-mangaka-phase-c-activation-and-emotion-loop
---

# Context

**主目的: spirit-in-physics 研究のデータ収集フロントエンド**

deai.etzhayyim.com は「出会い系アプリ」を装置として使い、Jung の語連想実験 + Hume AI 感情計測の
研究データを大規模収集することが第一目的。マッチング機能は参加動機を高めるための
インセンティブレイヤー。

研究 SSoT は `spirit-in-physics.com/api`（Cloudflare Worker + D1 + R2）。
deai は全データをこのエンドポイントに中継する。

Platform の Well-Becoming 目的関数において `U_spirit`（Spirit 接続度）は Rank 2 / Weight 0.95 の
最上位軸であり、「孤独・分離を癒す」ことが platform の中核的ミッションである。

Jun Kawasaki の論文 "Spirit in Physics: Spirit as a Thermodynamic Information Quantity"
（Kawasaki, Tainaka, Takeuchi — Niigata U / Aarhus U, 2026）は以下を定義した:

- Spirit = 高次元多様体上の熱力学的情報量（言語・行動・生理信号を結合）
- 孤独・分離 = 情報チャネルの遮断 = エントロピーの局所的増大
- 癒し = チャネルの回復 = Shannon η の上昇
- Spirit Types: Hero / Sage / Lover / Caregiver（Jung 分析心理学）
- 測定式: `P(w_O|w_I) = exp(w_I·w_O) × r^α × exp(γ·ΔSP/λ) × exp(η·F) / Z`

この ADR は `deai.etzhayyim.com` マッチングアプリの設計決定を記録する。

# Decision

## A. Spirit-in-Physics マッチングアルゴリズム

### A1. Spirit Type 判定（Word Association Experiment）

```
axios scores[type] += Σ_word_in_axis [ (1000/rt_ms) × exp(0.5 × F_type/1000) ]
```

- `rt_ms` = 語連想反応時間（ms）
- `F_type` = Hume AI 感情ベクトルの type 軸スコア（permille）
- 最高スコアの軸 → Spirit Type

### A2. テンセグリティ共鳴スコア（マッチング）

```
W_ij = exp(-||e_i - e_j||^2 / (2σ^2))   σ=500 permille
resonance = W_ij × COMPATIBILITY[type_i][type_j]
```

| Jung 補完性 | スコア |
|---|---|
| Hero ↔ Caregiver | 950 |
| Sage ↔ Lover | 950 |
| Hero ↔ Lover | 800 |
| Hero ↔ Hero | 700 |

テンセグリティ原理: 補完的な型の組み合わせが最も安定した感情的自立構造を形成する。

### A3. U_spirit ゲート

```
if separation_delta < -200: reject match  # 孤独を増やすマッチは reject
U_spirit_pair = (u_spirit_a + u_spirit_b) / 2
```

W×B目的関数の `spirit-connection` gate（Rank 2）を直接適用。

## B. データアーキテクチャ

### B1. Cohort DID（ADR-0018 PII Tier 3 準拠）

```
cohort_hash = DJB2(spirit_type | quantized_emotion_centroid)
cohort_did = "did:web:deai.etzhayyim.com:" + cohort_hash
```

- 実 DID（メール・電話）= server 非保持
- Cohort DID = Spirit Type × 量子化感情重心 のハッシュのみ
- RLS カラム: `actor_did`, `org_did`, `created_at`（ADR-0095準拠）

### B2. 生体データの Privacy-by-Design

- 顔画像・音声 = 端末上の Hume API で処理後に即破棄
- サーバーに送信するのは 10 次元 Hume スコア（0-1000 permille）のみ
- Server は生体データを受け取らない・保存しない・ログしない
- メッセージ = Signal protocol E2E 暗号化（`signal:v1:{ciphertext}`）

### B3. ストレージ層（ADR-2605111200 準拠）

- **Worker 層（CF Edge）**: KV のみ（Session, Profile cache, Message conv）
- **Domain 書き込み**: XRPC → bpmn-dispatcher → LangServer pod → Kotoba/Datomic
- **Worker 内 Hyperdrive / SELECT 禁止**

## C. モバイル（Capacitor）

spirit-in-physics リポジトリ（com-junkawasaki/spirit-in-physics）の Capacitor 構成を
参考に同一パターンで構築:

- `appId = "com.etzhayyim.deai"`
- WebDir = `../svelte/build`（SvelteKit static adapter）
- Plugins: Camera（Hume face）, Voice Recorder（Hume voice）, Preferences（token store）
- iOS: `contentInset: always`（safe area 対応）
- PWA manifest も同時提供（App Store 外配布オプション）

## D. Hume AI WebSocket プロキシ（2026-05-18 shipped）

### D1. アーキテクチャ

```
Browser (HumeRecorder) ──WS──→ CF Worker /api/hume-ws ──WS──→ wss://api.hume.ai/v0/stream/models
```

CF Worker の `sdk.router.get('/api/hume-ws', ...)` で WebSocket Upgrade を処理し、
`HUME_API_KEY` Worker secret を使って Hume API へ双方向中継する。

### D2. なぜ Worker プロキシか

- 顔画像・音声は Client-side Hume SDK で処理し server に渡さない（Privacy-by-Design §B2 維持）
- Hume API key を browser に expose しない（漏洩防止）
- CORS cross-origin WS 制限を回避（同一 origin 経由）

### D3. 実装詳細

```ts
// 60-apps/etzhayyim-project-deai/appview/deai-cgxi8oem/src-ts/app.ts
sdk.router.get('/api/hume-ws', (c) => {
  // WebSocketPair + server.accept() + 双方向 message/close/error relay
  // → new Response(null, { status: 101, webSocket: client })
});
```

`HUME_API_KEY` は Worker secret として設定（`wrangler secret put HUME_API_KEY`）。

### D4. フロントエンド WS URL 自動導出

```ts
// +page.svelte
const HUME_PROXY_WS = (import.meta.env.VITE_HUME_PROXY_WS as string | undefined)
  || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/hume-ws`;
```

ビルド時設定不要。`window.location.host` から自動構築するため staging / production 両環境で動作する。

## E. LangGraph グラフ

| Graph | NSID（予定） | 説明 |
|---|---|---|
| `deaiSpiritAssessment` | `com.etzhayyim.apps.deai.spiritAssessment` | 語連想応答 → Spirit Type + Resonance Field |
| `deaiMatchEngine` | `com.etzhayyim.apps.deai.matchEngine` | テンセグリティ共鳴マッチスコア |

# Consequences

- `deai.etzhayyim.com` は `U_spirit` 最大化を product の第一目的とする
- 孤独・分離を増やすマッチ（separation_delta < -200）は UI に表示しない
- 生体データの server 側保持を技術的に禁止（Privacy-by-Design）
- Capacitor + SvelteKit で App Store / Google Play 提出可能な状態まで scaffold 済み
- Hume API key は Worker secret のみ（browser expose 禁止）。`wrangler secret put HUME_API_KEY` 必須（deploy 前）

# References

- Kawasaki et al. (2026) — Spirit in Physics (arxiv pre-print, CNS 2025 presented)
- ADR-2604291800 — Well-Becoming Spirit Objective Function
- ADR-0018 — PII Tier 3 Cohort-First
- `60-apps/etzhayyim-project-deai/CLAUDE.md`
- com-junkawasaki/spirit-in-physics (Capacitor pattern reference)
