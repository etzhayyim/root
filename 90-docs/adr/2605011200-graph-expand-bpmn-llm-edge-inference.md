---
id: adr-2605011200-graph-expand-bpmn-llm-edge-inference
title: "Graph Expansion via BPMN + LLM Edge Inference (PoC)"
status: proposed
doc_type: adr
topic: graph-expansion
authoritative: true
last_verified: 2026-05-01
authoritative_for:
  - graph expansion proposal pipeline
  - BPMN LLM edge inference
  - vertex_graph_expand_proposal schema
priority: 7.5
axis: gate
weight: 0.75
priority_note: "PoC for growing graph adjacency via proposal-only LLM inference before promotion into edge tables"
depends_on:
  - adr-0056-bpmn-as-actor
  - adr-2604282300
related:
  - adr-2605011300-capital-flow-information-physics
supersedes: []
superseded_by: []
amends:
  - adr-0056-bpmn-as-actor
  - adr-2604282300
---

# ADR 2605011200 — Graph Expansion via BPMN + LLM Edge Inference (PoC)

Status: Proposed
Date: 2026-05-01
Supersedes: —
Amends: ADR-0056 (BPMN-as-actor), ADR-2604282300 (CF Worker = edge layer)

## Context

調査 2026-05-01 の結論:

- `zeebe-worker` Deployment と `bpmn-dispatcher` Deployment は常駐済み (`50-infra/vultr/mitama-udf-pool/templates/{zeebe-worker,dispatcher}.yaml`)。
- `shinka-tick` CronJob は LangGraph + Murakumo LLM で `vertex_shinka_*` を成長させているが、対象は actor 自己情報のみ (`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/shinka/__init__.py`)。
- 「ある vertex を見て依存先 vertex / edge を LLM 推論で生やす」**汎用ループは未実装**。各 actor が個別に handler 内で書いているだけ (`fabric.py`, `science_knowledge.py`, `intel.py` など 20+ 箇所)。

graph を「育てる」第一歩として、新規の K8s Deployment や CronJob を立てずに、**既存の `generic.db.select` / `generic.llm.json` / `generic.db.insert` 3 primitive と既存 `zeebe-worker` daemon だけで動く 3-task BPMN PoC** を導入する。ADR-0056 の「新 actor = INSERT 2 rows」規約に従う。

## Decision

新 BPMN actor `com.etzhayyim.apps.graph.expandTick` を追加する。

### Topology

```
Timer-start (R/PT30M)  or  XRPC POST /xrpc/com.etzhayyim.apps.graph.expandTick
        │
        ▼
[ Task_Pick ]   generic.db.select
   SELECT vertex_id, label, summary
   FROM   vertex_actor
   WHERE  vertex_id NOT IN (
            SELECT source_vid FROM vertex_graph_expand_proposal
            WHERE  llm_model = $1 AND created_at > now() - INTERVAL '7 days'
          )
   ORDER  BY _seq DESC
   LIMIT  1
        │   rows[0] = seed
        ▼
[ Task_Infer ]  generic.llm.json   (tier=classifier)
   prompt = "Given vertex {label} : {summary}, propose ONE
             most-likely related vertex (label + edge_kind +
             confidence ∈ [0,1] + ≤120-char rationale).
             Return strict JSON: {dstLabel, edgeKind, confidence, rationale}."
        │   data = {dstLabel, edgeKind, confidence, rationale}
        ▼
[ Task_Write ]  generic.db.insert (raw SQL path)
   INSERT INTO vertex_graph_expand_proposal
     (vertex_id, source_vid, proposed_dst_label,
      edge_kind, confidence, rationale, llm_model, status,
      created_at, owner_did, sensitivity_ord,
      org_id, user_id, actor_id, actor_did, org_did)
   VALUES ($1..$15)
        │
        ▼
[ Task_Audit ]  generic.audit.emit  (com.etzhayyim.apps.graph.expand.proposal)
        │
        ▼
       End
```

PoC は **proposal を直接 `edge_*` には書かない**。`vertex_graph_expand_proposal` (status='proposed') に貯めて、後段 (manual review or 2 段目 BPMN) で `edge_*` に promote する。これによりハルシネーションが本物の edge を汚さない。

### Why a proposal table, not direct `edge_*` write

| 選択 | 理由 |
|---|---|
| `vertex_graph_expand_proposal` 経由 | LLM 出力 = 提案。confidence しきい値・review・abuse 検出を後段で挟める |
| 直接 `edge_*` | hallucination が graph を汚す。RW は ON CONFLICT 不可 (CLAUDE.md) で再現性確保が難しい |

### Why no new daemon

ADR-2604282300 §「CF Worker = edge only / business logic = Zeebe Python worker」に整合:

- `zeebe-worker` (常駐) が `generic.db.select / llm.json / db.insert / audit.emit` を既に処理する。
- `bpmn-dispatcher` (常駐) が timer-start BPMN を Zeebe broker に register 済み。
- 新 BPMN を `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` に INSERT すれば F5 watcher (30s) が deploy する。

新 K8s manifest 不要。

## Schema

新テーブル 1 本のみ:

```sql
CREATE TABLE vertex_graph_expand_proposal (
  vertex_id          VARCHAR PRIMARY KEY,    -- at://did:web:graph.etzhayyim.com/com.etzhayyim.apps.graph.expandProposal/{rkey}
  _seq               BIGINT,
  created_date       DATE,
  sensitivity_ord    BIGINT,
  owner_did          VARCHAR,
  source_vid         VARCHAR NOT NULL,        -- 既存 vertex (seed)
  proposed_dst_vid   VARCHAR,                 -- LLM が既存 vertex を指したとき
  proposed_dst_label VARCHAR,                 -- LLM が新 vertex を提案したときの label
  edge_kind          VARCHAR NOT NULL,        -- "depends_on" / "related_to" / etc.
  confidence         DOUBLE PRECISION NOT NULL,
  rationale          VARCHAR,                 -- ≤ 240 char
  llm_model          VARCHAR NOT NULL,
  status             VARCHAR NOT NULL DEFAULT 'proposed', -- proposed | accepted | rejected
  created_at         VARCHAR NOT NULL,
  org_id             VARCHAR,
  user_id            VARCHAR,
  actor_id           VARCHAR,
  actor_did          VARCHAR,
  org_did            VARCHAR
);

CREATE INDEX idx_graph_expand_proposal_source
  ON vertex_graph_expand_proposal (source_vid, llm_model, created_at);
CREATE INDEX idx_graph_expand_proposal_status
  ON vertex_graph_expand_proposal (status, confidence);
```

## Write scope

`vertex_bpmn_lexicon_binding.write_table_allowlist = "vertex_graph_expand_proposal"` で本 BPMN は **proposal table 以外には書けない** (2026-04-25 加わった `_enforce_write_scope` defence)。

## Per-actor cadence (deferred)

PoC は **global tick 1 件 / 30 分**。per-actor cadence (shinka 流の mood × stale-age) は次段で。`shinka_tick_actor()` UDF と同型の `graph_expand_tick_actor()` UDF + per-actor BPMN instance に拡張可能だが、本 ADR の scope 外。

## langgraph integration (deferred)

Shinka が既に `langgraph.StateGraph` を使用している (`kotodama/shinka/__init__.py:31`)。PoC では generic.llm.json 1 hop のみ。多 hop reasoning (propose → critique → refine) を入れる時は LangGraph state machine を `kotodama` に新設し、generic primitive `generic.langgraph.run` として exposure する後続 ADR で扱う。

## Acceptance gate (out of scope)

`status='proposed' → 'accepted'` への昇格、および `vertex_graph_expand_proposal → edge_*` の promotion は本 ADR の対象外。手順 candidate:

- `confidence ≥ 0.9` かつ `proposed_dst_vid != NULL` (既存 vertex) を auto-accept
- それ以外は人手 review (CLI / dashboard)
- accepted 時に `edge_<edge_kind>` に INSERT する 2 段目 BPMN

## Files

| 種別 | path |
|---|---|
| ADR | `90-docs/adr/2605011200-graph-expand-bpmn-llm-edge-inference.md` |
| Lexicon (procedure) | `00-contracts/lexicons/com/etzhayyim/apps/graph/expandTick.json` |
| BPMN | `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/graph/expandTick.bpmn` |
| Schema migration | `30-graph/graph-schema/migrations/20260501130000_vertex_graph_expand_proposal.ts` |
| BPMN seed migration | `30-graph/graph-schema/migrations/20260501130100_seed_graph_expand_bpmn.ts` |

## Rollout

1. `pnpm db:migrate` → table + indexes 作成 + BPMN registry seed
2. F5 watcher (30s) が `vertex_bpmn_process_def` を Zeebe broker に deploy
3. 30 分後の最初の timer fire で 1 行が `vertex_graph_expand_proposal` に入る
4. 24h 後 confidence 分布を確認 (`SELECT confidence, COUNT(*) FROM vertex_graph_expand_proposal GROUP BY 1`) して PoC 評価

## Rollback

```sql
DELETE FROM vertex_bpmn_lexicon_binding
 WHERE vertex_id = 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.bpmn.lexiconBinding/graph-expandTick-v1';
DELETE FROM vertex_bpmn_process_def
 WHERE vertex_id = 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.bpmn.processDef/graph-expandTick-v1';
DROP TABLE IF EXISTS vertex_graph_expand_proposal;
```

F5 watcher は次 cycle で `expandTick` を Zeebe から undeploy する。

## Non-goals

- LangGraph multi-hop reasoning (defer)
- per-actor cadence (defer)
- `edge_*` 直接書き込み (intentional, never)
- 大量並列 (PoC = 1 row / 30 min, ~48 row/day)
