---
id: adr-2605130000-projector-mcp-project-management
title: "ADR-2605130000: projector.* MCP tools — Project Lifecycle Management"
status: accepted
doc_type: adr
topic: projector-mcp-project-management
authoritative: true
last_verified: 2026-05-13
priority: 8.0
axis: architecture
weight: 0.8
priority_note: "Claude Agent が多セッション作業を継続するための project lifecycle 管理レイヤー。MCP as cell membrane (ADR-2605091400) の具体実装。"
authoritative_for:
  - projector.* MCP tool 全定義 (create_project / update_status / add_blocker / resolve_blocker / get_status / list_projects)
  - vertex_projector_blocker / edge_projector_project_dep schema 定義
  - vertex_project_props 拡張列 (progress_permille / lifecycle_state / lg_thread_id / target_date)
  - mv_projector_project_status MV 定義
  - pymagatama/projector/ LangGraph + Pregel 実装
  - com/etzhayyim/projector/ Lexicon 定義
  - GRAPHS["projector_lifecycle"] の pregel pod 登録
  - Claude Agent が projector tools を使うべきタイミングの契約
depends_on:
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605131800-pregel-triage-langgraph-email-intent-routing
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605080600-langgraph-server-granian-l3-runtime
related:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
---

# ADR-2605130000: projector.* MCP tools — Project Lifecycle Management

## Goal

Claude Agent が **複数セッションにまたがる作業** を継続・再開するための project lifecycle 管理レイヤーを確立する。

具体的には:

1. **project の作成と状態追跡** — `vertex_project_props` を SSoT として `progress_permille` / `lifecycle_state` を管理
2. **blocker の登録・伝播・解除** — `vertex_projector_blocker` + Pregel BSP で依存グラフ上の blocked 状態を自動伝播
3. **LangGraph による lifecycle 遷移** — `projector_lifecycle` state machine が planning → active → blocked → done を管理
4. **MCP facade** — CF Worker `mcp-adapter.ts` の BUILTIN_TOOLS として `projector.*` 6 ツールを公開

## Context

Claude Agent は長期タスクを複数セッションで実行するが、セッション間の状態連続性がない。既存の手段では:

- どこまで進んだか (progress) を次セッションで参照できない
- 外部依存待ち (blocked) の記録がない
- 依存プロジェクト間の blocked 伝播がない

MCP as cell membrane (ADR-2605091400) により、外部公開 API は MCP tool 経由でのみ許容される。`projector.*` はこの原則に従い、CF Worker が提供する 6 本の MCP tool として実装する。

## Architecture

```
Claude Agent (MCP client)
  │
  ├─ projector.create_project ────────────────────────────────────┐
  ├─ projector.update_status  ─── XRPC → bpmn-dispatcher ─────── LangGraph
  ├─ projector.add_blocker    ─── com.etzhayyim.projector.*  ─────────  projector_lifecycle
  ├─ projector.resolve_blocker ──────────────────────────────────  (pregel pod)
  ├─ projector.get_status     ─── READ → mv_projector_project_status
  └─ projector.list_projects  ─── READ → mv_projector_project_status

                   LangGraph projector_lifecycle (pymagatama/projector/graph.py)
                     load_project → check_health → transition → END

                   Pregel BSP blocker_pregel (pymagatama/projector/blocker_pregel.py)
                     Superstep 1: blocked signal を edge_projector_project_dep で伝播
                     Superstep 2: unblocked signal を逆伝播 (max_hop=2)

Kotoba/Datomic Tables:
  vertex_project_props          (progress_permille, lifecycle_state, lg_thread_id, target_date)
  vertex_projector_blocker      (type, severity, status)
  edge_projector_project_dep    (依存グラフ、Pregel traversal 用)
  mv_projector_project_status   (open/total blocker counts, aggregated status)
```

### スキーマ詳細

```sql
-- vertex_projector_blocker
CREATE TABLE graphar.vertex_projector_blocker (
  did        VARCHAR PRIMARY KEY,
  project_did VARCHAR NOT NULL,
  type       VARCHAR NOT NULL,   -- external_dep / internal / review_wait
  severity   VARCHAR NOT NULL,   -- critical / high / medium / low
  status     VARCHAR NOT NULL DEFAULT 'open',  -- open / resolved
  description VARCHAR,
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

-- edge_projector_project_dep
CREATE TABLE graphar.edge_projector_project_dep (
  src_did  VARCHAR NOT NULL,
  dst_did  VARCHAR NOT NULL,
  dep_type VARCHAR DEFAULT 'blocks'
);

-- vertex_project_props 拡張列
ALTER TABLE graphar.vertex_project_props
  ADD COLUMN IF NOT EXISTS progress_permille BIGINT DEFAULT 0,
  ADD COLUMN IF NOT EXISTS lifecycle_state   VARCHAR DEFAULT 'planning',
  ADD COLUMN IF NOT EXISTS lg_thread_id      VARCHAR,
  ADD COLUMN IF NOT EXISTS target_date       VARCHAR;

-- mv_projector_project_status (MV)
SELECT p.did, p.name, p.lifecycle_state, p.progress_permille,
       COUNT(b.did) FILTER (WHERE b.status = 'open') AS open_blockers,
       COUNT(b.did) AS total_blockers
FROM graphar.vertex_project_props p
LEFT JOIN graphar.vertex_projector_blocker b ON b.project_did = p.did
GROUP BY p.did, p.name, p.lifecycle_state, p.progress_permille;
```

### Lexicon 一覧 (`com/etzhayyim/projector/`)

| ファイル | type | 用途 |
|---|---|---|
| `addBlocker.json` | procedure | blocker 登録 |
| `resolveBlocker.json` | procedure | blocker 解除 |
| `updateProgress.json` | procedure | progress_permille + lifecycle_state 更新 |
| `getProjectStatus.json` | query | 単一 project の status 取得 |
| `listProjects.json` | query | project 一覧取得 (filter 付き) |

### LangGraph `projector_lifecycle`

```python
class ProjectorState(TypedDict):
    project_did:      str
    lifecycle_state:  str
    progress_permille: int
    open_blockers:    int
    lg_thread_id:     str | None

# node 順
load_project → check_health → transition → END

# 遷移ルール (check_health が判定)
open_blockers > 0  → lifecycle_state = "blocked"
progress_permille >= 1000 → lifecycle_state = "done"
else → lifecycle_state = "active" (planning からの昇格含む)
```

### Pregel BSP `blocker_pregel`

```
Superstep 1 (add_blocker 時):
  blocker が追加されたプロジェクトに blocked シグナルを送信
  → edge_projector_project_dep を辿り、依存プロジェクトにも伝播 (max_hop=2)

Superstep 2 (resolve_blocker 時):
  全 open_blockers = 0 になったプロジェクトに unblocked シグナルを送信
  → 依存プロジェクトを再評価し lifecycle_state を active に戻す
```

### Lifecycle states

```
planning → active → blocked → active (ループ可) → done
```

## Decision

1. `projector.*` MCP tools は CF Worker `mcp-adapter.ts` の BUILTIN_TOOLS に登録する
2. lifecycle 遷移は LangGraph `projector_lifecycle` が担当し、CF Worker から XRPC 経由で呼び出す
3. blocker の依存グラフ伝播は Pregel BSP `blocker_pregel` が担当する (ADR-2605131800 の pregel pod を拡張)
4. read は `mv_projector_project_status` から直接取得 (LangGraph 不要)
5. CF Worker から Kotoba/Datomic への直接接続は ADR-2605111200 に従い禁止。全 write は pod 経由
6. `summarize=true` 指定時のみ LLM (gemma-4-E2B-it) による status サマリを生成する

## Consequences

- Claude Agent は `projector.get_status` を呼ぶだけで前回セッションの状態を復元できる
- blocker が追加されると依存プロジェクトも自動的に `blocked` に遷移する (Pregel 伝播)
- `etzhayyim projector` CLI により人手での操作も可能
- pregel pod のメモリ使用量が増加する可能性がある (projector_lifecycle graph の追加登録分)

---

## Agent Usage Contract

**THIS IS THE KEY SECTION。** Claude Agent は以下の契約に従い `projector.*` tools を使用しなければならない。

### 必須使用タイミング

| タイミング | 使用すべき tool | 理由 |
|---|---|---|
| 複数セッションにまたがるタスク開始時 | `projector.create_project` | 状態 SSoT を確立する |
| セッション再開時 (最初のアクション) | `projector.get_status` | 前回の progress / blockers を確認する |
| 外部依存待ちが発生した時点 | `projector.add_blocker` | blocked 状態を即時記録し伝播させる |
| 外部依存が解消された時点 | `projector.resolve_blocker` | unblocked 伝播を起動する |
| セッション終了前 | `projector.update_status` | 現在の progress_permille を保存する |
| タスク完了を報告する前 | `projector.update_status` (lifecycleState=done) | 完了状態を確定する |

### 各 tool の使用方法

#### `projector.create_project`

新しいプロジェクトを作成する。マルチセッション作業の**最初のアクション**として呼ぶ。

```json
{
  "tool": "projector.create_project",
  "arguments": {
    "name": "lexicon-migration-2026-05",
    "description": "com.etzhayyim.projector.* Lexicon の PDS bundle 再生成と deploy",
    "targetDate": "2026-05-20"
  }
}
```

戻り値: `{ "projectDid": "did:web:pregel.etzhayyim.com#proj-xxxx", "lifecycleState": "planning" }`

#### `projector.get_status`

セッション**再開時の最初のアクション**として必ず呼ぶ。前回の state を復元する。

```json
{
  "tool": "projector.get_status",
  "arguments": {
    "projectDid": "did:web:pregel.etzhayyim.com#proj-xxxx",
    "summarize": false
  }
}
```

戻り値: `{ "projectDid": "...", "name": "...", "lifecycleState": "active", "progressPermille": 350, "openBlockers": 0, "totalBlockers": 1 }`

`summarize: true` を指定すると LLM による日本語サマリが `summary` フィールドに付与される。

#### `projector.update_status`

セッション終了前および**完了報告前**に必ず呼ぶ。

```json
{
  "tool": "projector.update_status",
  "arguments": {
    "projectDid": "did:web:pregel.etzhayyim.com#proj-xxxx",
    "progressPermille": 700,
    "lifecycleState": "active"
  }
}
```

完了時:

```json
{
  "tool": "projector.update_status",
  "arguments": {
    "projectDid": "did:web:pregel.etzhayyim.com#proj-xxxx",
    "progressPermille": 1000,
    "lifecycleState": "done"
  }
}
```

#### `projector.add_blocker`

外部依存待ち、レビュー待ち、内部依存待ちが**発生した瞬間**に呼ぶ。後回しにしない。

```json
{
  "tool": "projector.add_blocker",
  "arguments": {
    "projectDid": "did:web:pregel.etzhayyim.com#proj-xxxx",
    "type": "external_dep",
    "severity": "high",
    "description": "PDS deploy 権限承認待ち (j.kawasaki@etzhayyim.com に確認中)"
  }
}
```

`type` の値: `external_dep` / `internal` / `review_wait`
`severity` の値: `critical` / `high` / `medium` / `low`

戻り値: `{ "blockerDid": "did:web:pregel.etzhayyim.com#blocker-yyyy", "propagated": 2 }`
(`propagated` = Pregel で blocked に遷移した依存プロジェクト数)

#### `projector.resolve_blocker`

blocker が解消されたら**即時**呼ぶ。

```json
{
  "tool": "projector.resolve_blocker",
  "arguments": {
    "blockerDid": "did:web:pregel.etzhayyim.com#blocker-yyyy"
  }
}
```

戻り値: `{ "unblocked": 3 }` (`unblocked` = Pregel で active に戻ったプロジェクト数)

#### `projector.list_projects`

担当プロジェクト一覧を確認する。セッション開始時に状況把握のために使ってよい。

```json
{
  "tool": "projector.list_projects",
  "arguments": {
    "lifecycleState": "active",
    "limit": 20,
    "offset": 0
  }
}
```

`lifecycleState` フィルタ: `planning` / `active` / `blocked` / `done` (省略で全件)

### progress_permille の計算ガイド

| 状態 | permille 目安 |
|---|---|
| 作業開始直後 | 0–50 |
| 要件・設計完了 | 100–200 |
| 実装中 (前半) | 200–500 |
| 実装完了・テスト中 | 500–800 |
| レビュー対応中 | 800–950 |
| deploy 完了、検証中 | 950–999 |
| 完了確認済み | 1000 (lifecycleState=done) |

### Forbidden patterns

| 禁止 | 代替 |
|---|---|
| セッション再開時に `get_status` を省略する | 必ず最初のアクションとして呼ぶ |
| 「完了です」と報告する前に `update_status(done)` を省略する | 報告前に必ず呼ぶ |
| blocked になっているのに `add_blocker` を後回しにする | 発生した瞬間に呼ぶ |
| `progress_permille` を 1000 にしたまま `lifecycleState` を `active` にする | 1000 の場合は `lifecycleState=done` を必ず同時に指定する |
| CF Worker から Kotoba/Datomic に直接 INSERT する | ADR-2605111200 に従い pod 経由のみ |

## References

- ADR-2605111200 (CF Worker Edge-Only — no RW connection)
- ADR-2605091400 (MCP as cell membrane)
- ADR-2605131800 (pregel triage pipeline — pregel pod を拡張)
- ADR-2605082000 (LangGraph graph definition as data)
- ADR-2605080600 (LangGraph Server + Granian L3 Runtime)
- `20-actors/magatama/py/src/pymagatama/projector/graph.py`
- `20-actors/magatama/py/src/pymagatama/projector/blocker_pregel.py`
- `60-apps/etzhayyim-project-pregel/lg/lg_pregel/server.py` (`GRAPHS["projector_lifecycle"]`)
- `50-infra/cloudflare/workers/atproto/src/mcp-adapter.ts` (BUILTIN_TOOLS `projector.*`)
- `00-contracts/lexicons/com/etzhayyim/projector/`
- `50-infra/vultr/geth-private/contracts/` (migration `20260513000000_vertex_projector_blocker_project_progress`)
- `70-tools/etzhayyim/projector.go` (`etzhayyim projector` CLI)
