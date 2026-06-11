---
id: adr-2605202500-temporal-not-adopted-langgraph-rw-durable
title: "ADR-2605202500: Temporal 不採用 — LangGraph + Kotoba/Datomic Durable Job 継続"
status: active
doc_type: adr
topic: temporal-not-adopted-langgraph-rw-durable
authoritative: true
last_verified: 2026-05-20
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "Temporal (workflow engine) を採用しない根拠を Shannon 最適 + Minimax regret で定量化"
authoritative_for:
  - Temporal workflow engine 不採用の根拠
  - LangGraph Server + Kotoba/Datomic を durable job 基盤として継続する決定
  - 常駐化・Durable Job の現行設計の正典記述
  - Temporal 検討を再開する条件 (例外)
depends_on:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
supersedes: []
superseded_by: []
amends: []
---

# ADR-2605202500: Temporal 不採用 — LangGraph + Kotoba/Datomic Durable Job 継続

**Status**: accepted
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

## Context

ADR-2605080600 で L3 Virtual Actor Runtime を Zeebe/pyzeebe から LangGraph Server + Granian に置換した。
移行中に「Temporal (Temporal Technologies 製 durable workflow engine) を採用した方が良いか」という問いが発生した。

Temporal の主な訴求点:
- built-in durable execution (event sourcing + deterministic replay)
- activity timeout + exponential backoff retry
- long-running workflow / saga / compensation の native サポート
- Temporal Cloud (managed service)

一方、現行スタックは以下で durable job を実現している:

| 機能 | 実装 |
|---|---|
| checkpoint | `vertex_langgraph_checkpoint` (Kotoba/Datomic `rw_vertex` mode) |
| HITL long-pause | `vertex_langgraph_checkpoint` (PostgresSaver `postgres` mode) |
| at-least-once replay | Redis BLPOP → bpmn-dispatcher 再投入 |
| graph-as-data self-evolution | `vertex_langgraph_assistant` / `vertex_langgraph_deployment` |
| timer-start | K8s CronJob → `POST /runs` (Phase 5 計画済み) |

## Decision

**Temporal を採用しない。LangGraph Server + Kotoba/Datomic checkpointer を durable job 基盤として継続する。**

## Rationale

### 1. 情報エントロピー H(state)

```
LangGraph + Kotoba/Datomic:
  H(state) = H_rw                  (Kotoba/Datomic が唯一の状態 SSoT)
  I(状態源 A; 状態源 B) = 0

Temporal を追加した場合:
  H(state) = H_temporal + H_rw + I(temporal; rw)
  I > 0 (Temporal history DB と Kotoba/Datomic の同期コストが恒常的に発生)
```

Temporal は独自の PostgreSQL/Cassandra history store を持つ。
Kotoba/Datomic をすでに SSoT として使用しているこのシステムでは、状態が bifurcate し
**Shannon redundancy が増大する**。

### 2. チャネル容量と実効スループット

```
LangGraph ASGI パス:
  dispatch latency: ~10-20ms (HTTP → Granian ASGI → StateGraph)
  checkpoint write: ~2-5KB/step (zlib 圧縮、Kotoba/Datomic append-only)
  recovery: single-row SELECT by vertex_id

Temporal パス:
  dispatch latency: ~50-100ms (Client → Temporal Server → Worker poll)
  history replay: O(n) steps を全再実行 (長期フロー = 計算コスト増大)
  history hard limit: 50,000 events/workflow
  通信モデル: polling (プッシュ不可)
```

LangGraph Server は `/runs/stream` で SSE プッシュを提供する。
Temporal の polling モデルは固有の遅延を生む。
ミッションオーケストレーション (defense) のような長期フローでは
Temporal の O(n) history replay がボトルネックになる。

### 3. Kolmogorov 複雑度

```
現行スタックの記述長 K(A1):
  K(graph-as-data) + K(RW SSoT) + K(MCP nodes) ≈ 1 概念フレームワーク

Temporal 追加後の記述長 K(A2):
  K(A1) + K(Temporal DSL) + K(activities) + K(task queues)
       + K(temporal history DB) + K(sync logic) > K(A1)
```

Zeebe を除去した理由と同型の問題が Temporal にも存在する:
**Java/Go サーバー (~1-2GB)、外部状態ストア、固有の運用語彙 (namespace/task queue/activity)**。
Zeebe からの移行途中に、同類の基盤を再度追加することは Kolmogorov 複雑度を上昇させる。

### 4. Minimax Regret 計算

#### シナリオと確率

| シナリオ | 確率 |
|---|---|
| S1: 通常運用 | 0.70 |
| S2: ノード障害・checkpoint recovery | 0.20 |
| S3: HITL 長期停止/resume (数日〜数週間) | 0.05 |
| S4: エージェント自己進化 (graph-as-data mutation) | 0.04 |
| S5: 壊滅的障害 | 0.01 |

#### 効用行列 (0–10、高いほど良い)

| シナリオ | A1: LangGraph+RW | A2: Temporal |
|---|---|---|
| S1 通常運用 | **9** (ASGI 直通、SSE push、MCP native) | 7 (polling、追加 hop) |
| S2 checkpoint recovery | 7 (RW vertex + at-least-once replay) | **9** (built-in event replay) |
| S3 HITL 長期停止 | 7 (postgres mode、PostgresSaver) | **9** (native saga/compensation) |
| S4 自己進化 | **10** (graph-as-data、repo コミット不要) | **1** (固定ワークフロー定義、不可能) |
| S5 壊滅的障害 | 6 (RW + AT firehose) | 5 (Temporal history) |

#### 期待効用

```
E[A1] = 0.70×9 + 0.20×7 + 0.05×7 + 0.04×10 + 0.01×6 = 8.51
E[A2] = 0.70×7 + 0.20×9 + 0.05×9 + 0.04×1  + 0.01×5 = 7.24
```

#### Regret 行列 (max_j U(j,s) − U(i,s))

| シナリオ | A1 regret | A2 regret |
|---|---|---|
| S1 | 0 | 2 |
| S2 | 2 | 0 |
| S3 | 2 | 0 |
| S4 | 0 | **9** ← 支配項 |
| S5 | 0 | 1 |
| **max regret** | **2** | **9** |

**Minimax 選択: A1 (LangGraph + Kotoba/Datomic)**
max regret 2 vs 9。S4 (自己進化) における Temporal の損失が決定的。

#### S4 が支配する理由

Bonsai Cultivar アーキテクチャ (ADR-2605091300 et al.) の中核は
「エージェントがリポジトリへのコミットなしに `vertex_langgraph_assistant` を更新し、
グラフトポロジを自己進化させる」能力である。
Temporal の workflow 定義は **コードとして静的にコンパイルされる** ため、
この能力を根本的に持てない。graph-as-data パターンと Temporal は構造的に非互換。

### 5. Temporal が優位な点と LangGraph での対処

| Temporal の優位点 | LangGraph + Kotoba/Datomic での対処 |
|---|---|
| Built-in exponential backoff retry | LangGraph node に `retry_policy` 設定 |
| Timer / alarm | K8s CronJob → `POST /runs` (Phase 5、計画済み) |
| Saga / compensation | 補償ノードをグラフエッジとして明示定義 |
| Workflow visibility UI | `vertex_langgraph_checkpoint` SQL + `/assistants` API |
| Activity heartbeat | LangGraph interrupt + resume (`/threads/{id}`) |

いずれも Temporal なしに対処可能であり、Phase 5 (timer replacement) で解消される設計になっている。

## 現行 Durable Job 実装の正典記述

### 常駐化

```
langgraph.json:
  { "graphs": { "agent": "<module>:<graph>" }, "python_version": "3.12" }

K8s Deployment:
  CMD ["granian", "--interface", "asgi", "langgraph_api:app"]
  /runs          → background execution
  /runs/stream   → SSE streaming to CF Worker
  /threads/{id}  → stateful actor (thread = DID + checkpoint lineage)
```

### Durable Job の 3 モード (per-assistant checkpointer_mode)

| モード | バックエンド | 用途 | TTL |
|---|---|---|---|
| `none` (default) | なし | 60 秒以下の短期グラフ | — |
| `rw_vertex` | Kotoba/Datomic `vertex_langgraph_checkpoint` | ストリーム派生グラフ、高書き込みレート | 24h (MV GC) |
| `postgres` | PostgresSaver (Hyperdrive) | HITL、長期停止/resume | 30d (cron hard-delete) |

モード変更 = 新 assistant version (immutable ルール)。

### at-least-once replay

```
Redis BLPOP (transient queue) が揮発しても:
  bpmn-dispatcher が /runs status=pending を検出
  → 再投入 (at-least-once)

Kotoba/Datomic checkpoint は append-only:
  ON CONFLICT → PK implicit upsert (RW は ON CONFLICT 句不要)
  autocommit=True (RW は multi-statement transaction 不可)
```

### 自己進化フロー (Temporal では不可能な能力)

```
agent が新しい推論チェーンを発明
  → vertex_langgraph_assistant に新バージョン行を INSERT
  → vertex_langgraph_deployment の assistant_id を更新 (data write)
  → compiler が次回起動時にグラフを再コンパイル
  → shadow/canary 評価
  → 成功: 旧バージョンの superseded_by = new_id
  → ゼロ repo コミット
```

## Exceptions (Temporal 再検討の条件)

以下のすべてが同時に成立した場合のみ Temporal 採用を再検討する:

1. **graph-as-data 要件がなくなった** (Bonsai Cultivar アーキテクチャの廃止)
2. **Kotoba/Datomic が state store として不適合** と判明した
3. **Temporal の max regret が 2 以下** に下がるシナリオ分布の変化があった
4. 上記 3 条件を新 ADR で定量的に示した

## References

- ADR-2605080600 — LangGraph Server + Granian L3 Runtime
- ADR-2605082000 — LangGraph Graph Definition as Data
- ADR-2605082100 — LangGraph Checkpointer Storage (3-mode)
- ADR-2605080000 — Distributed Cognitive Actor System 6-Layer
- ADR-2605091300 — Bonsai Cultivar Layer (自己進化の根拠)
- ADR-2604282300 — CF Worker Edge Layer (bpmn-dispatcher)
