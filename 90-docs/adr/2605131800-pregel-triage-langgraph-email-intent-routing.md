---
id: adr-2605131800-pregel-triage-langgraph-email-intent-routing
title: "ADR-2605131800: pregel — Outlook Email Intent Classification & Project Routing LangGraph Pipeline"
status: accepted
doc_type: adr
topic: pregel-triage-email-routing
authoritative: true
last_verified: 2026-05-13
priority: 7.0
axis: architecture
weight: 0.7
priority_note: "Outlook triage の downstream pipeline。clean 判定された email を LLM intent 分類 → Kotoba/Datomic graph → projector project convo へルーティング。"
authoritative_for:
  - pregel_triage LangGraph pipeline の全ノード定義
  - vertex_email_message / vertex_email_sender / edge_email_sent_by schema の pregel 拡張列
  - mv_email_pending_action / mv_email_sales_queue MV 定義
  - outlook_triage → pregel_triage bridge (_node_invoke_pregel)
  - 60-apps/etzhayyim-project-pregel/ actor 定義
  - K8s Helm release lg-pregel (50-infra/k8s/pregel/)
depends_on:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080200-pydantic-l6-validation-contract
  - adr-2605080300-sqlalchemy-core-usage-contract
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-0018-pii-tier3-cohort-first
related:
  - adr-0032-gmail-direct-ingest-yabai-classifier
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605082000-langgraph-graph-definition-as-data
---

# ADR-2605131800: pregel — Outlook Email Intent Classification & Project Routing

## Goal

outlook_triage で `clean` と判定された Outlook/M365 メールを受け取り:

1. **intent 分類** (LLM) — sales / support / internal / unknown
2. **vertex 書込** — `vertex_email_message` + `vertex_email_sender` + `edge_email_sent_by` への INSERT
3. **project routing** — `task_email_route` 呼び出し → `edge_email_routes_to_project` + `vertex_projector_message` 追加

を行う独立 LangGraph Server (`pregel.etzhayyim.com`) を確立する。

## Context

outlook_triage (`outlook_triage.py`) は BEC Tier-2 暗号化 (`subject_enc` / `body_preview_enc`) の制約により、**メタデータのみ** (from_address, from_name, received_at, account_did) を downstream に渡せる。

- `subject_enc` / `body_preview_enc` は vertex_email_message に暗号化保存されており、pregel triage 段階での LLM 分類は metadata-only ヒューリスティックに限定される
- intent 分類は from_name / from_domain / received_at の特徴から推論する
- 将来フェーズで BEC 復号パスを追加することで精度向上が可能

## Architecture

```
outlook_triage (5 min cron)
  └─ _node_invoke_pregel (clean emails のみ)
       └─ pregel_triage LangGraph
            ├─ parse_email      (metadata → PegelState)
            ├─ classify_intent  (LLM: sales/support/internal/unknown)
            ├─ detect_deps      (sender reputation lookup)
            ├─ write_vertex     (asyncpg INSERT vertex_email_message + sender + edge)
            ├─ route_email      (task_email_route → projector convo)
            └─ END
```

### Actor profile

| 項目 | 値 |
|---|---|
| host | `pregel.etzhayyim.com` |
| DID | `did:web:pregel.etzhayyim.com` |
| image | `ghcr.io/etzhayyim/lg-pregel` |
| K8s | `50-infra/k8s/pregel/deployment.yaml` (namespace: mitama-udf) |
| memory limit | 2Gi (1Gi が OOMKill — LangGraph + asyncpg の同時ロードで倍増) |
| secret | `lg-pregel-secrets` (K8s Secret、旧: `lg-pegel-secrets` → 手動再作成要) |
| Python package | `kotodama.pregel` (`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/pregel/`) |
| langgraph.json | `60-apps/etzhayyim-project-pregel/lg/langgraph.json` |

### LangGraph StateGraph (5 node)

```python
class PegelState(TypedDict):
    message_id:    str
    from_address:  str
    from_name:     str
    to_addresses:  str
    subject:       str          # 常に "" (BEC Tier-2 暗号化のため)
    received_at:   str
    body_preview:  str          # from_name を仮置き (暗号化のため)
    intent:        str | None   # classify_intent 出力
    written:       bool         # write_vertex 完了フラグ
```

```
parse_email → classify_intent → detect_deps → write_vertex → route_email → END
```

### _node_invoke_pregel (outlook_triage bridge)

`outlook_triage._build_graph()` の末尾ノードとして追加:

```
claim → t1 → t2_rep → [t3 →] synth → register → mark → invoke_pregel → END
```

clean rows のみを pregel_triage に投入。`message_id` を必須とし、取得できない行はスキップ。graph instance は呼び出しごとに `build_graph()` → `ainvoke()` のワンショット方式 (state 汚染回避)。

### Schema 拡張

既存 `vertex_email_message` に pregel 処理列を追加:

```sql
-- 20260512_0001_email_project_route.py (alembic) に含む
ALTER TABLE graphar.vertex_email_message
  ADD COLUMN IF NOT EXISTS intent         VARCHAR,
  ADD COLUMN IF NOT EXISTS pregel_run_id  VARCHAR,
  ADD COLUMN IF NOT EXISTS routed_at      TIMESTAMPTZ;
```

MV:

| MV | 定義 | 用途 |
|---|---|---|
| `mv_email_pending_action` | `WHERE triaged_at IS NOT NULL AND routed_at IS NULL` | route_email のポーリングソース |
| `mv_email_sales_queue` | `WHERE intent = 'sales' AND routed_at IS NULL` | 営業担当向け未対応リスト |

### Routing rules (task_email_route)

`primitives/email_route.py` (`ACTOR_PREGEL = "did:web:pregel.etzhayyim.com"`) が処理:

1. `mv_email_pending_action` から未 routed を取得
2. intent / from_domain / account_did で project を特定 (`edge_email_routes_to_project`)
3. projector project convo に `vertex_projector_message` を INSERT
4. `vertex_email_message.routed_at = now()` を更新 (FLUSH 付き)

## Rationale

### outlook_triage から分離する理由

- outlook_triage は yabai 判定 (BEC / phish / spam) が責務。intent 分類はセマンティクスが異なる
- pregel を独立 K8s pod にすることでメモリ隔離 (LLM model load が 2Gi 必要) と独立スケールが可能
- 将来の BEC 復号 (Phase 2) 時に pregel のみ変更すればよい

### metadata-only intent 分類の合理性

- BEC Tier-2 では subject/body が暗号化されており、LLM に平文を渡せない
- from_name + from_domain の特徴で sales / support / internal / unknown は十分な精度で区別可能
- unknown 分類された行は `mv_email_pending_action` で人手レビューキューに積まれる

### 命名 (pregel vs pegel)

旧スペルミス `pegel` を 2026-05-13 に全リポジトリで `pregel` に修正。
`pregel` = "Pregel" (Google の分散グラフ処理モデル) ではなく、LangGraph の graph traversal engine の内部名称から着想した命名。

## Pending (Phase 2)

| 項目 | 内容 |
|---|---|
| BEC 復号パス | pregel がメッセージキーを取得して subject/body を復号し LLM に渡す |
| routing rules 拡張 | TMI, Bakshi, 外部パートナー向けルール追加 |
| K8s secret 手動再作成 | `kubectl -n mitama-udf create secret generic lg-pregel-secrets` (値は旧 `lg-pegel-secrets` からコピー) |
| Docker image rename | `ghcr.io/etzhayyim/lg-pregel` (旧: `lg-pegel`) でビルド・プッシュ |

## Forbidden patterns

| 禁止 | 代替 |
|---|---|
| `subject_enc` / `body_preview_enc` を pregel ノードで復号 | Phase 2 まで metadata-only |
| outlook_triage と pregel で同一 graph instance を共有 | `build_graph()` はワンショット |
| CF Worker から asyncpg/asyncio で RW 直接接続 | ADR-2605111200 準拠、pod 経由のみ |
| LLM model 名ハードコード | `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL` |

## References

- ADR-2605080600 (LangGraph Server + Granian L3 Runtime)
- ADR-2605080000 (Distributed Cognitive Actor System)
- ADR-2605111200 (CF Worker Edge-Only — no RW connection)
- ADR-0032 (Gmail Direct Ingest + Yabai Classifier)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/pregel/graph.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/agents/outlook_triage.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/email_route.py`
- `60-apps/etzhayyim-project-pregel/lg/`
- `50-infra/k8s/pregel/deployment.yaml`
