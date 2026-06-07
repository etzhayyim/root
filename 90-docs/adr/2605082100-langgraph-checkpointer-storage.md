---
id: adr-2605082100-langgraph-checkpointer-storage
title: "ADR-2605082100: LangGraph Checkpointer Storage"
status: active
doc_type: adr
topic: langgraph-checkpointer-storage
authoritative: true
last_verified: 2026-05-09
priority: 8.4
axis: architecture
weight: 0.84
priority_note: "checkpointer=true 時の保管先を確定。HITL graph と stream-derived graph で要件が違うため 2-mode 設計"
authoritative_for:
  - LangGraph checkpointer storage backend selection (postgres vs rw_vertex vs none)
  - HITL graph durability contract (PostgresSaver via Hyperdrive)
  - stream-derived graph re-hydration contract (`vertex_langgraph_checkpoint`)
  - checkpoint TTL / GC policy
related:
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2605072000-langgraph-agent-loop-pattern
supersedes: []
superseded_by: []
---

# ADR-2605082100: LangGraph Checkpointer Storage

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

ADR-2605080000 は LangGraph について `checkpointer=None` を原則としつつ、
`長期 HITL が必要な場合のみ SqliteSaver / PostgresSaver` と書いている。
しかし保管先の具体は決まっていなかった。

ADR-2605082000 で graph topology が data 化される結果、checkpointer も
graph_def 側に `checkpointer_mode` として宣言される。各 mode の物理保管先を
確定する必要がある。

要件は graph 種別で 2 つに分かれる:

1. **HITL graph** — human approval pause、日〜週単位、low write rate、
   strict ACID、failure 時の resume が critical
2. **Stream-derived graph** — derive 過程の中間 state、秒〜分単位、
   high write rate、ACID 不要、失敗時は再 derive で十分

両者を同じ backend に乗せるのは Shannon 的に冗長。

## Decision

### 3-mode 設計

`vertex_langgraph_graph_def.checkpointer_mode` の取りうる値:

| mode | backend | 用途 | TTL |
|---|---|---|---|
| `none` | (no checkpointer) | 短時間 intra-job graph (<60s) | — |
| `postgres` | PostgresSaver via Hyperdrive | HITL / 長期 graph | 30 days, GC by job |
| `rw_vertex` | `vertex_langgraph_checkpoint` (RW) | stream-derived graph | 24h, MV-driven GC |

graph 起動時に compiler が mode を読み取り、対応する `BaseCheckpointSaver`
implementation を `compile()` に渡す。

### Mode A: `postgres` (HITL / 長期 graph)

**backend**: LangGraph 公式 `PostgresSaver`、接続先は ADR-0036 の Hyperdrive。

```python
from langgraph.checkpoint.postgres import PostgresSaver
saver = PostgresSaver.from_conn_string(env.HYPERDRIVE_LANGGRAPH_URL)
saver.setup()  # idempotent
graph = builder.compile(checkpointer=saver)
```

物理 schema は `langgraph` schema に分離 (`graphar` と混ぜない):

- `langgraph.checkpoints`
- `langgraph.checkpoint_writes`
- `langgraph.checkpoint_blobs`

これらは LangGraph SDK 管理。マイグレーションは `saver.setup()` に委ねる。

**理由**:

- HITL は ACID + transactional cursor 移動が必須 → RW では不適 (RW は streaming MV エンジン)
- Hyperdrive 経由で CF Worker からも HITL resume を trigger 可能
- PostgresSaver は upstream 公式 → 互換性維持コスト 0

**TTL**: 30 days。`langgraph.checkpoints.created_at < now() - 30d` を
日次 cron job で hard delete (ADR-0036 soft delete 禁止)。
完了済 thread は完了時即削除。

### Mode B: `rw_vertex` (stream-derived graph)

> **2026-05-09 訂正 (iter3)**: 初稿は `RwVertexCheckpointSaver` を新規実装する
> 提案だったが、`kotodama/langgraph_checkpoint_rw.py` に既に実装済み。
> 既存 schema (`vertex_langgraph_checkpoint` + `vertex_langgraph_checkpoint_write`)
> も migration `20260422030000_vertex_langgraph_checkpoint.ts` +
> `20260507600000_vertex_langgraph_store_and_writes.ts` で apply 済み。
> 本 ADR は既存実装を SSoT 認定する形に書き直した。

**backend**: 既存 `kotodama/langgraph_checkpoint_rw.py` の
`Kotoba/DatomicCheckpointSaver` (LangGraph `BaseCheckpointSaver` 実装)。

**Schema (既存 live)**:

```
vertex_langgraph_checkpoint
  vertex_id              VARCHAR PK = "{thread_id}:{checkpoint_ns}:{checkpoint_id}"
  thread_id              VARCHAR
  checkpoint_id          VARCHAR    -- ULID-like, monotonic per thread
  checkpoint_ns          VARCHAR
  parent_checkpoint_id   VARCHAR    -- ToT / fork lineage
  checkpoint_type        VARCHAR
  blob                   VARCHAR    -- base64 JSON (zlib if >2KiB, ADR-2605080600)
  created_at             VARCHAR
  + RLS 3-col (sensitivity_ord/owner_did) + actor_id/org_id/user_id

vertex_langgraph_checkpoint_write
  vertex_id  VARCHAR PK = "{thread_id}:{checkpoint_ns}:{checkpoint_id}:{task_id}:{idx}"
  -- pending writes for crash-resume
```

**実装上の RW 制約対応** (`langgraph_checkpoint_rw.py` 冒頭参照):

- `FOR UPDATE SKIP LOCKED` なし → actor-level lock で single-flight 保証
- `LISTEN/NOTIFY` なし → polling (`ORDER BY checkpoint_id DESC LIMIT 1`)
- `ON CONFLICT` なし → PK implicit upsert (re-INSERT で overwrite)
- multi-statement TX なし → autocommit=True
- `LIMIT $n` 不可 → f-string int (lint: `rw-psycopg3-no-param-limit`)

**制約**:

- write は append-only。同一 PK の re-INSERT は idempotent overwrite
- `blob` は base64 JSON。`_COMPRESS_MIN_BYTES=2048` 超で zlib level 6 (Shannon source-coding 閾値)
- Pickle / msgpack 禁止 (LLM-readable 維持)
- ADR-2605080000 `Hot/Warm/Cold` の Warm State
- TTL は別途 GC MV で実装予定 (現状未実装、Phase 1 TODO)

**理由**:

- stream graph は「もう一度 derive すれば再現できる」性質なので
  ACID は要らず、append-only でよい
- RW の MV 機構と相性がよく、checkpoint そのものを analytics できる
  (どの node で何秒、何回 retry したかが SQL で見える)
- Hyperdrive PG への hot write を避けられる (HITL graph の SLA を守る)

### Mode C: `none`

短時間 intra-job graph (<60s, ≥3 LLM steps の coordination のみ)。
ADR-2605080000 の原則。actor passivation 前に必ず終了する graph はこれ。

### Compiler 側の選択ロジック

```python
# vertex_langgraph_assistant.checkpointer_mode (migration r_20260509130000)
mode = assistant_row["checkpointer_mode"] or "none"
match mode:
    case "none":
        cp = None
    case "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver
        cp = PostgresSaver.from_conn_string(env.HYPERDRIVE_LANGGRAPH_URL)
    case "rw_vertex":
        from kotodama.langgraph_checkpoint_rw import Kotoba/DatomicCheckpointSaver
        cp = Kotoba/DatomicCheckpointSaver()  # uses ensure_rw_async_pool()
graph = builder.compile(checkpointer=cp)
```

mode は assistant 行に宣言されているため、agent が新版 assistant を deploy する
時点で保管先を決める。runtime が mode を後から変えることは禁止 (`superseded_by` で
新行を立てる)。

### Migration / Schema ownership

- `langgraph.*` schema (Mode A) → LangGraph SDK 所有、Alembic 対象外
- `graphar.vertex_langgraph_checkpoint` (Mode B) → ADR-2605080400 Alembic で管理
- ADR-2605080500 SQLMesh の対象は `mv_langgraph_checkpoint_gc` のみ

## Consequences

**得られるもの**:

- HITL graph は ACID 保証で長期 pause 可能
- stream graph は RW の MV / analytics と統合される
- agent が graph を作る時点で SLA tier (`mode`) を選択する設計になる
- `none` を default にすることで checkpointer 起因の cost 暴発を防ぐ

**制約・注意点**:

- 2 backend 並走の運用負荷 (monitoring 2 系統)
- `RwVertexCheckpointSaver` は自前実装 → LangGraph SDK の checkpointer 仕様
  upgrade 時に追従が要る
- mode 変更は graph_def の新 version 発行を伴う (ADR-2605082000 immutable rule)
- HITL の `langgraph.checkpoint_blobs` が大きくなりやすい → 30d GC 必須

## References

- ADR-2605082000: LangGraph Graph Definition as Data (`checkpointer_mode` の発生源)
- ADR-2605080000: Distributed Cognitive Actor System (`checkpointer=None` 原則)
- ADR-2605080600: LangGraph Server + Granian L3 Runtime (実行環境)
- ADR-0036: Worker-direct Hyperdrive Persistence (Mode A の物理接続)
- ADR-2605080400: Alembic Scope Contract (Mode B schema 管理)
- ADR-2605080500: SQLMesh MV Management (GC MV の所有)
