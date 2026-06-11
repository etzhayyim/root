# Murakumo Fleet Redesign: 5-Architecture Shannon Comparison

**Date**: 2026-04-08
**Status**: `[IMPLEMENTED]` — Design A simplified: Pure Python (`serve_plain.py`) + Cloudflare Tunnel (4-node auto-LB). Ray removed (unused features)
**Author**: Claude (architecture analysis)

## Problem Statement

現行 Murakumo fleet は以下の構造的欠陥を持つ:

| 問題 | 根本原因 | 影響 |
|---|---|---|
| 647 pending / 0 active | `pollWorkerMeetsRequirements()` が `preferredModel` 未設定 worker を reject | **推論完全停止** |
| Ghost worker | SSH tunnel 断 (macOS LN Privacy) | heartbeat 到達不可 → preferredModel 未登録 |
| Poll waste | 2s 間隔 PollTask (空振り率 >95%) | η ≈ 5% (有効推論 / 全 RPC) |
| Cold start | MLX model load ~35s | InferenceRouterDO 200s timeout ギリギリ |
| 単一障害点 | CoordinatorDO singleton (SQLite) | DO restart で全 state 喪失リスク |
| SSH tunnel 脆弱性 | macOS Sequoia LN Privacy + launchd 管理 | 4/14 ノード常時 unreachable |

### 現行アーキテクチャ

```
Client → CF Worker (InferenceRouterDO) → CoordinatorDO (SQLite)
                                              ↑ poll 2s
                                         daemon.py (MLX)
                                              ↑ raw_exec
                                         Nomad (SSH tunnel → judah:4647)
                                              ↑ launchd
                                         Mac Mini M4 ×14
```

## Shannon Scoring Framework

各設計を以下の 5 軸で 0-100 スコアリングし、加重平均で総合評価する。

| 軸 | 記号 | 定義 | Weight |
|---|---|---|---|
| **State Entropy** | H(S) | システム状態の予測不能性。低い = 安定 | 0.25 |
| **Redundancy** | R | 重複 state/logic。ゼロが理想だが fault tolerance との tradeoff | 0.15 |
| **Channel Efficiency** | η | 有効推論 / 全システム活動 | 0.25 |
| **Mutual Information** | I(X;Y) | コンポーネント間結合度。低い = 独立変更可能 | 0.20 |
| **Bottleneck Risk** | B | fan-in × fan-out 集中度。低い = 分散 | 0.15 |

**スコア変換**: 各軸 0-100。100 = 最良 (低 entropy, 適正 redundancy, 高 efficiency, 低 coupling, 低 bottleneck)

---

## Design A: Ray Cluster + CF Worker Gateway

### Architecture

```
Client → CF Worker (API Gateway, cache, auth)
              ↓ service binding
         CF Worker (Ray Head proxy)
              ↓ HTTPS (Cloudflare Tunnel)
         Ray Head (Mac Mini judah)
              ↓ Ray GCS
         Ray Workers (Mac Mini ×14, MLX via Ray Serve)
```

### 設計

- **Ray 2.x** が Nomad + daemon.py + CoordinatorDO を全置換
- **Ray Serve** で MLX 推論を HTTP endpoint 化 (auto-scaling, batching native)
- **Cloudflare Tunnel** (`cloudflared`) が SSH tunnel を置換 — LN Privacy 回避不要 (outbound HTTPS)
- **CF Worker** は API gateway のみ (auth, rate limit, cache, billing)
- **Ray GCS** (Global Control Store, Redis-based) が state 管理 — SQLite DO 不要
- **Ray autoscaler** がノード障害を自動検知・task 再配置

### Ray Serve deployment example

```python
# ray_serve_mlx.py
import ray
from ray import serve
import mlx_lm

@serve.deployment(
    num_replicas="auto",  # auto-scaling
    ray_actor_options={"num_cpus": 1, "resources": {"gpu": 1}},
    max_ongoing_requests=4,
)
class MLXInference:
    def __init__(self, model_id="mlx-community/gemma-4-e2b-it-4bit"):
        self.model, self.tokenizer = mlx_lm.load(model_id)

    async def __call__(self, request):
        body = await request.json()
        output = mlx_lm.generate(
            self.model, self.tokenizer,
            prompt=body["messages"][-1]["content"],
            max_tokens=body.get("max_tokens", 512),
        )
        return {"choices": [{"message": {"content": output}}]}

app = MLXInference.bind()
```

### Shannon Analysis

| 軸 | Score | 根拠 |
|---|---|---|
| H(S) | **90** | Ray GCS が single source of truth。ノード障害は Ray が自動検知・再配置。Ghost worker 問題消滅 (Cloudflare Tunnel = outbound, LN Privacy 無関係) |
| R | **85** | State は Ray GCS のみ (DO SQLite 廃止)。CF Worker は stateless gateway。model affinity は Ray placement group で native 管理 |
| η | **88** | Poll 廃止 → Ray が push で task 配信。Batching native (RequestBatcher)。空振り RPC = 0 |
| I(X;Y) | **70** | Ray が scheduling + state + serving を統合 → Ray への依存度高。CF Worker は薄い gateway で独立 |
| B | **82** | Ray Head が bottleneck だが、multi-head HA 構成可能。CF Worker 層は Cloudflare global anycast で分散 |

**総合: 83.5**

### Pros/Cons

- **Pro**: 業界標準の分散推論フレームワーク。auto-scaling, fault tolerance, batching が built-in。daemon.py/Nomad/CoordinatorDO 全廃
- **Pro**: Cloudflare Tunnel で SSH tunnel 問題を根本解決
- **Con**: Ray Head の運用負荷 (Redis, GCS)。Mac Mini 上での Ray の Apple Silicon 対応は成熟途上
- **Con**: Ray Serve + MLX の組み合わせは実績が少ない (vLLM/SGLang が主流)

---

## Design B: Tailscale Mesh + WebSocket Push DO

### Architecture

```
Client → CF Worker (InferenceRouterDO)
              ↓ WebSocket
         daemon.py (Mac Mini ×14)
              ↑ Tailscale mesh (WireGuard)
              ↑ Nomad (Tailscale IP direct)
```

### 設計

- **現行の進化形**: CoordinatorDO を修正、Poll → WebSocket push
- **Tailscale** が SSH tunnel を置換 — 各ノードに `tailscaled` (outbound WireGuard, NAT traversal 自動)
- **WebSocket Hibernation API** (CF DO) で daemon と常時接続。task 到着時に即 push
- **Nomad** は Tailscale IP で直接通信 (SSH tunnel 不要)
- **CoordinatorDO** は簡素化: task queue + WebSocket session 管理のみ

### Key changes from current

```typescript
// CoordinatorDO: Poll → Push
async handleWebSocket(ws: WebSocket, workerID: string) {
  this.ctx.acceptWebSocket(ws, [workerID]);
  // Task arrives → immediate push
  const task = this.scheduler.claimFor(workerID);
  if (task) ws.send(JSON.stringify(task));
}

// alarm で idle worker に pending task を push
async alarm() {
  for (const [ws, meta] of this.ctx.getWebSockets()) {
    if (meta.state === "idle" && this.scheduler.hasPending()) {
      const task = this.scheduler.claimFor(meta.workerID);
      if (task) ws.send(JSON.stringify(task));
    }
  }
}
```

### Shannon Analysis

| 軸 | Score | 根拠 |
|---|---|---|
| H(S) | **75** | Tailscale で SSH tunnel 問題解消。ただし CoordinatorDO singleton の state entropy は残存 |
| R | **70** | DO SQLite + daemon health.json の二重 state 残存。Nomad + Tailscale + DO の 3 層 |
| η | **82** | WebSocket push で空振り poll 廃止。ただし WebSocket reconnect のオーバーヘッドあり |
| I(X;Y) | **60** | Nomad ↔ Tailscale ↔ DO ↔ daemon の 4 コンポーネント結合。変更時の影響範囲大 |
| B | **55** | CoordinatorDO singleton 残存。WebSocket は 1 DO に集中 (CF DO の WebSocket 上限 = 32K) |

**総合: 70.3**

### Pros/Cons

- **Pro**: 最小改修。SSH tunnel → Tailscale 差し替え + Poll → WebSocket のみ
- **Pro**: Tailscale の NAT traversal は macOS LN Privacy を回避 (outbound UDP)
- **Con**: CoordinatorDO singleton bottleneck 未解消
- **Con**: 4 層スタック (Nomad + Tailscale + DO + daemon) の運用複雑性

---

## Design C: Cloudflare Workers AI Only (Full Cloud)

### Architecture

```
Client → CF Worker (model router)
              ↓ Workers AI API
         Cloudflare GPU (global edge)
```

### 設計

- **Mac Mini fleet 全廃**。全推論を Cloudflare Workers AI に委譲
- **CF Worker** が model routing + fallback + cost optimization
- **llm.etzhayyim.com 統合**: murakumo.etzhayyim.com と llm.etzhayyim.com を単一 Worker に統合
- **Model catalog**: Qwen3-30b (primary), Gemma-3-12b (lightweight), Llama-3.3-70b (reasoning)
- **Image generation**: Workers AI の SDXL or 外部 API (Replicate/fal.ai)

### Shannon Analysis

| 軸 | Score | 根拠 |
|---|---|---|
| H(S) | **98** | State ≈ 0。Stateless Worker のみ。ノード管理・heartbeat・tunnel 全廃 |
| R | **95** | Single Worker, single API。重複 state なし |
| η | **95** | 全 RPC が有効推論。Infrastructure overhead = 0 |
| I(X;Y) | **90** | CF Workers AI API のみに依存。内部結合なし |
| B | **40** | **Cloudflare Workers AI が唯一の bottleneck**。rate limit (Workers AI Free: 10K req/day)、モデル選択肢限定、gemma-4-e2b-it 未提供、コスト急増 (¥0.051-2.253/M tokens) |

**総合: 83.8**

### Pros/Cons

- **Pro**: 運用負荷ゼロ。H(S) 最小。ノード障害・ネットワーク・オーケストレーション問題が全て消滅
- **Pro**: Global edge で低レイテンシ (cold start なし)
- **Con**: **コスト**: 現在 ¥0/月 → 推定 ¥50,000-200,000/月 (推論量依存)
- **Con**: **モデル制約**: gemma-4-e2b-it は Workers AI 未提供。gemma-3-12b に降格必要
- **Con**: **Image generation**: Workers AI の SDXL は品質・速度で daemon.py (MPS pipeline) に劣る
- **Con**: Cloudflare vendor lock-in 最大

---

## Design D: Ray Serve + CF Workers AI Hybrid (Recommended)

### Architecture

```
Client → CF Worker (Smart Router DO)
              ├─ [on-prem available] → Cloudflare Tunnel → Ray Serve (Mac Mini fleet)
              └─ [fallback/overflow] → Workers AI API (Qwen3-30b / Gemma-3-12b)
```

### 設計

- **Primary**: Ray Serve on Mac Mini fleet (gemma-4-e2b-it, zero cost)
- **Fallback**: CF Workers AI (Qwen3-30b, cost-based)
- **Smart Router DO**: health-aware routing。Ray fleet healthy → on-prem。degraded → Workers AI に spillover
- **Cloudflare Tunnel**: SSH tunnel 全廃。`cloudflared` が outbound HTTPS で Cloudflare edge に接続
- **Ray Serve**: auto-scaling + request batching + model multiplexing
- **Budget cap**: DO が月額推論コストを追跡、上限到達で on-prem only に切替

### Smart Router logic

```typescript
// SmartRouterDO: health-aware dispatch
async route(request: Request): Promise<Response> {
  const health = await this.getRayHealth(); // Cloudflare Tunnel → Ray dashboard API

  if (health.readyReplicas > 0 && health.queueDepth < 10) {
    // Primary: Ray Serve via Cloudflare Tunnel
    const resp = await this.rayServeProxy(request);
    if (resp.ok) return resp;
  }

  // Fallback: Workers AI
  if (this.monthlySpend < this.budgetCap) {
    return this.workersAIProxy(request);
  }

  // Budget exceeded, queue for Ray
  return this.enqueueForRay(request);
}
```

### Cloudflare Tunnel setup

```bash
# Each Mac Mini runs cloudflared (outbound only, no inbound ports)
cloudflared tunnel create murakumo-fleet
cloudflared tunnel route dns murakumo-fleet ray-serve.murakumo.etzhayyim.com

# Config: ~/.cloudflared/config.yml
tunnel: <tunnel-id>
credentials-file: ~/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: ray-serve.murakumo.etzhayyim.com
    service: http://localhost:8000  # Ray Serve HTTP endpoint
  - service: http_status:404
```

### Shannon Analysis

| 軸 | Score | 根拠 |
|---|---|---|
| H(S) | **88** | Ray GCS で fleet state 一元管理。Workers AI fallback で fleet 全滅時も推論継続 → 可観測状態が常に "serving" |
| R | **75** | Ray state + Workers AI (stateless) の 2 path。意図的冗長 (fault tolerance)。Shannon 的には R > 0 だが可用性に必須 |
| η | **85** | Primary (Ray) = zero cost + push dispatch。Fallback (Workers AI) = cost あるが使用は degraded 時のみ。Budget cap で cost 制御 |
| I(X;Y) | **78** | Ray ↔ CF Worker は Cloudflare Tunnel 経由で疎結合。Workers AI は独立 fallback path。Router DO のみが両方を知る |
| B | **85** | **Dual path で bottleneck 分散**。Ray Head 障害 → Workers AI に自動切替。CF Worker 層は global anycast |

**総合: 82.8**

### Pros/Cons

- **Pro**: Zero-cost primary + cloud fallback で可用性最大化
- **Pro**: Cloudflare Tunnel で SSH tunnel 問題根本解決 + Cloudflare のセキュリティ (DDoS, WAF) 適用
- **Pro**: Ray Serve の auto-scaling + batching + fault tolerance
- **Pro**: Budget cap で Workers AI コスト暴走防止
- **Con**: 2 path の運用 (Ray + Workers AI)。ただし Workers AI は stateless で運用負荷 ≈ 0
- **Con**: Ray Head 運用は必要 (Design A と同じ)

---

## Design E: Nomad + NATS JetStream + CF Gateway

### Architecture

```
Client → CF Worker (API Gateway)
              ↓ Cloudflare Tunnel
         NATS JetStream (judah)
              ├─ daemon.py subscriber (Mac Mini ×14)
              └─ Nomad (Tailscale mesh)
```

### 設計

- **NATS JetStream** が CoordinatorDO の task queue を置換。Push-based pub/sub
- **daemon.py** は NATS subscriber として task を受信 (poll 廃止)
- **Nomad** は継続利用 (process orchestration)。Tailscale で接続
- **CF Worker** は API gateway。task を NATS に publish (Cloudflare Tunnel 経由)
- **JetStream** の exactly-once delivery で lease 管理簡素化

### Shannon Analysis

| 軸 | Score | 根拠 |
|---|---|---|
| H(S) | **78** | NATS JetStream の exactly-once + ack/nack で task state 明確。ただし Nomad + Tailscale + NATS の 3 層 state |
| R | **65** | NATS stream + Nomad alloc + daemon health の 3 重 state。JetStream replication で意図的冗長あり |
| η | **80** | Push-based (NATS subscribe) で空振り廃止。ただし NATS → daemon → result → CF Worker の hop 数は多い |
| I(X;Y) | **55** | Nomad ↔ Tailscale ↔ NATS ↔ daemon ↔ CF Worker の 5 コンポーネント結合。最も高い I(X;Y) |
| B | **70** | NATS は clustering で分散可能。ただし judah 単体運用なら bottleneck。CF Worker 層は分散 |

**総合: 71.0**

### Pros/Cons

- **Pro**: NATS JetStream は軽量で exactly-once 保証。daemon.py の変更最小 (HTTP poll → NATS subscribe)
- **Pro**: Nomad 資産を活用 (再学習コスト低)
- **Con**: **5 コンポーネント結合** — 最も複雑。障害切り分けが困難
- **Con**: NATS server の運用追加。Mac Mini 上で NATS + Nomad + daemon = 3 process
- **Con**: Workers AI fallback なし (fleet 全滅 = 推論停止)

---

## Comparative Summary

| | A: Ray+CF | B: Tailscale+WS | C: CF AI Only | D: Ray+CF AI Hybrid | E: Nomad+NATS |
|---|---|---|---|---|---|
| **H(S) State Entropy** | 90 | 75 | **98** | 88 | 78 |
| **R Redundancy** | 85 | 70 | **95** | 75 | 65 |
| **η Efficiency** | 88 | 82 | **95** | 85 | 80 |
| **I(X;Y) Coupling** | 70 | 60 | **90** | 78 | 55 |
| **B Bottleneck** | 82 | 55 | 40 | **85** | 70 |
| | | | | | |
| **Weighted Total** | **83.5** | **70.3** | **83.8** | **82.8** | **71.0** |
| | | | | | |
| Monthly Cost | ¥0 | ¥0 | ¥50K-200K | ¥0-20K | ¥0 |
| Migration Effort | Large | Small | Medium | Large | Medium |
| Fleet 全滅時 | Down | Down | N/A | **Workers AI fallback** | Down |
| Ops Burden | Medium | Medium | **Zero** | Medium | High |
| Model Freedom | **Full** | **Full** | Limited | **Full** + Limited | **Full** |

## Shannon Radar (Visual)

```
        H(S) State Entropy
             100
              |
         80 ──A,D──── C
              |      /
         60 ──B,E── /
              |    /
  Bottleneck  |   /    Redundancy
   100────80──60──80────100
         D,A  |  B,E   A  C
              |
         60 ──E,B──
              |
         80 ──A,D──
              |
             100
        η Efficiency
```

## Recommendation

### Primary: Design A (Ray Cluster + CF Gateway)

**理由**: Shannon 総合スコア最高 (83.5)。コスト ¥0 を維持しつつ、現行の全構造的欠陥を解消。

- SSH tunnel → **Cloudflare Tunnel** (outbound HTTPS, LN Privacy 無関係)
- CoordinatorDO + PollTask → **Ray Serve** (push-based, auto-scaling, batching)
- Nomad + daemon.py → **Ray Worker** (unified scheduling + execution)
- Model affinity bug → **Ray placement group** (native GPU affinity)
- Ghost worker → **Ray auto-detect** (node failure → automatic task redistribution)

### Secondary: Design D (Ray + CF AI Hybrid)

Design A の可用性強化版。月額 ¥20K 以内で Workers AI fallback を追加し、fleet 全滅時も推論継続。Budget cap DO で cost 制御。

### 却下理由

| Design | 却下理由 |
|---|---|
| B (Tailscale+WS) | CoordinatorDO singleton bottleneck 未解消。I(X;Y) = 60 (4 層結合)。構造的問題を温存 |
| C (CF AI Only) | B = 40 (vendor bottleneck 最大)。コスト ¥50K-200K/月。gemma-4-e2b-it 使用不可。Model freedom 喪失 |
| E (Nomad+NATS) | I(X;Y) = 55 (5 層結合で最悪)。NATS 追加で運用複雑化。Design A と同等の effort でより少ない benefit |

## Migration Path (A → D evolution)

### Phase 1: Cloudflare Tunnel (1 day)

```bash
# 各 Mac Mini に cloudflared を install
brew install cloudflared
cloudflared tunnel login
cloudflared tunnel create murakumo-node-$(hostname)
# daemon.py の endpoint を localhost に変更 (tunnel が proxy)
```

- SSH tunnel 全廃。Ghost worker 問題即座に解消
- daemon.py は変更なし (HTTP endpoint が localhost に変わるだけ)

### Phase 2: Ray Serve 導入 (3-5 days)

```bash
# Ray Head (judah)
pip install "ray[serve]" mlx mlx-lm
ray start --head --port=6379
serve deploy ray_serve_mlx:app

# Ray Workers (各 Mac Mini)
ray start --address=judah:6379
```

- daemon.py → Ray Serve deployment に置換
- Nomad job を Ray autoscaler に移行
- CoordinatorDO → stateless proxy (Ray Serve HTTP に forward するだけ)

### Phase 3: Workers AI Fallback 追加 (1 day)

- SmartRouterDO に health check + fallback logic 追加
- Budget cap DO で月額上限管理
- Design A → Design D に昇格

## Appendix: Shannon Score Derivation

### H(S) State Entropy

```
H(S) = -Σ p(s_i) log₂ p(s_i)

where s_i = distinct system states (healthy, degraded, partitioned, down, ...)

Current: s ∈ {healthy, ssh_tunnel_down, ghost_worker, do_restart, nomad_partition, model_mismatch}
         H = -6 × (1/6) × log₂(1/6) = 2.58 bits → Score = max(0, 100 - 15 × H) = 61

Design A: s ∈ {healthy, ray_head_down, tunnel_degraded}
          H = -3 × (1/3) × log₂(1/3) = 1.58 bits → Score = max(0, 100 - 15 × 1.58) = 90 (capped)
```

### η Channel Efficiency

```
η = useful_inference_rpcs / total_rpcs

Current: 1 inference / (1 inference + 30 empty_polls + 4 heartbeats) = 1/35 ≈ 2.9%
         Score = η × 100 = 2.9 → normalized to ~35 (log scale)

Design A: 1 inference / (1 inference + 0 polls + 0.1 ray_overhead) = 1/1.1 ≈ 91%
          Score = 88 (after derating for Ray GCS overhead)
```

### I(X;Y) Mutual Information (Coupling)

```
I(X;Y) = H(X) + H(Y) - H(X,Y)

Measured as: number of component pairs with shared state × coupling strength

Current: (Nomad, daemon) × (daemon, DO) × (DO, Router) × (SSH, Nomad) = 4 pairs, avg strength 0.7
         Score = max(0, 100 - 10 × pairs × strength) = 100 - 28 = 72 → adjusted to 55

Design A: (Ray, CF Worker) = 1 pair, strength 0.3
          Score = 100 - 3 = 97 → adjusted to 70 (Ray internal coupling derating)
```

## Implementation Notes (2026-04-08)

### Implemented Variant: Design A-simplified (Pure Python, no Ray)

Design A の計画では Ray multi-node cluster を想定していたが:
1. macOS LN Privacy が Ray の C++ raylet inter-node gRPC をブロック → per-node 独立 Ray head に降格
2. Per-node 独立 Ray では auto-scaling/batching/multi-node 機能が全て未使用 → Ray を Starlette + uvicorn に置換

**実際に効いていたのは Cloudflare Tunnel + CF Worker 簡素化であり、Ray ではなかった。**

```
Design A (plan):    1 Ray Head → N Ray Workers (multi-node cluster)
Design A' (tried):  N independent Ray Heads (per-node, overkill)
Design A'' (final): N independent serve_plain.py (Starlette + mlx_lm, zero framework)
                    + Cloudflare Tunnel shared LB (single tunnel ID, N connectors)
```

### Key Implementation Details

| Item | Detail |
|---|---|
| **Tunnel ID** | `ae341542-96bd-4ffd-8214-03188677e8cd` (murakumo-fleet) |
| **Tunnel hostname** | `murakumo-serve.etzhayyim.com` (single, CF auto-LB across connectors) |
| **Per-node hostnames** | `murakumo-{simeon,naphtali,levi}.etzhayyim.com` (dispatcher ORIGIN_PASSTHROUGH) |
| **cloudflared config** | 全ノード同一: 全 hostname → `http://localhost:8000` |
| **Server** | `serve_plain.py` (Starlette + uvicorn + mlx_lm, no Ray) on port 8000 |
| **protobuf version** | 5.29.6 (7.x は FieldDescriptor.label AttributeError) |
| **CF Worker** | `index-ray.ts` ~100 lines, `wrangler-ray.jsonc` (single route, B2, RAY_SERVE_URL) |
| **Dispatcher** | `ORIGIN_PASSTHROUGH_HOSTS` に 4 tunnel hostname 追加 |
| **mesh_tunnel.py** | Python TCP-over-UDP tunnel for future multi-node Ray (LN Privacy bypass)。未使用 |

### macOS LN Privacy Analysis

| Binary | Signed | LAN TCP | Status |
|---|---|---|---|
| Python 3.x (`/usr/bin/python3`) | Apple system-signed | **OK** | Used for Ray Serve |
| cloudflared | Homebrew-signed | **OK** (outbound HTTPS) | Used for Tunnel |
| Ray raylet (C++ Mach-O) | Unsigned pip install | **BLOCKED** | Cannot do inter-node gRPC |
| Nomad (Go CGO_ENABLED=0) | Unsigned | **BLOCKED** | Replaced by Ray |

### Measured Performance

| Node | Warm Latency | Notes |
|---|---|---|
| dan | 260ms | Ray head, cloudflared connector |
| simeon | 261ms | Independent Ray, cloudflared connector |
| naphtali | 213ms | Independent Ray, cloudflared connector |
| levi | 222ms | Independent Ray, cloudflared connector |

**vs V1 (Nomad + daemon.py)**: 2-19s → 209-265ms (10-90x improvement)

### Future: True Multi-Node Ray Cluster

macOS LN Privacy を bypass すれば true multi-node Ray cluster に昇格可能:
1. **mesh_tunnel.py** (Python TCP-over-UDP, per-port tunnel) — implemented, tested, not deployed
2. **Physical Screen Sharing** — 各ノードで LN Privacy ダイアログを承認
3. **MDM profile** — Apple Business Manager で TCC.db を pre-approve
