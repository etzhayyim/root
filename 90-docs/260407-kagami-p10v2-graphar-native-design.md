---
id: kagami-p10v2-graphar-native-design
title: "kagami P10v2: GraphAr-Native Typed Columnar Schema"
status: active
doc_type: explanation
topic: kagami-kotoba-graphar
authoritative: true
last_verified: 2026-04-13
authoritative_for:
  - kagami P10v2 GraphAr-native schema design
related:
  - kagami-kotoba-graphar-design
supersedes:
  - kagami-kotoba-graphar-design
superseded_by: []
---

# kagami P10v2: GraphAr-Native Typed Columnar Schema

## Decision

P10v1 (P9 property decomposition legacy) から **P10v2 GraphAr-native typed columnar schema** に移行。

P10v1 は P9 の「1 property = 1 vertex + val STRING」を GraphAr テーブル名で包んだだけだった。P10v2 は Kotoba/Datomic + GraphAr の設計思想に native に合わせる。

実装時の TypeScript/Cypher ルールは `90-docs/rules/ts-cypher-p10v2-query-rules.md` を参照。

## Shannon Redundancy Analysis

### P10v1 (現状): 62.5% redundancy

```
1 Post write = 5 rows:
  Post:       {vertex_id:"tid1",       rkey:"tid1", repo:$did, _alive, _seq, ts, val:null}
  PostText:   {vertex_id:"tid1::text", rkey:"tid1", repo:$did, _alive, _seq, ts, val:"Hello"}
  PostEmbed:  {vertex_id:"tid1::embed",rkey:"tid1", repo:$did, _alive, _seq, ts, val:'{...}'}
  PostFacets: {vertex_id:"tid1::facets",rkey:"tid1",repo:$did, _alive, _seq, ts, val:'[...]'}
  PostProps:  {vertex_id:"tid1::props",rkey:"tid1", repo:$did, _alive, _seq, ts, val:'{"langs":...}'}

5 rows x 8 shared cols = 40 values. rkey,repo,_alive,_seq,ts x5 = 25 redundant.
Shannon redundancy = 25/40 = 62.5%
5 Kotoba/Datomic INSERTs per Post.
Read: 5 rows scan + application merge.
```

### P10v2 (新設計): 0% redundancy

```
1 Post write = 1 row:
  vertex_post: {vertex_id:"tid1", rkey:"tid1", repo:$did, text:"Hello",
                embed:'{...}', facets:'[...]', langs:'["ja"]',
                reply_root:null, reply_parent:null,
                _alive, _seq, ts, embedding:[...], embedding_norm, ivf_cluster_id}

1 row x 15 cols = 15 values. NULL in Kotoba/Datomic columnar = 0 bytes.
Shannon redundancy = 0%
1 Kotoba/Datomic INSERT per Post.
Read: 1 row fetch (zero merge).
```

### Savings Summary

| Metric | P10v1 | P10v2 | Improvement |
|---|---|---|---|
| Rows per Post | 5 | 1 | 5x fewer |
| INSERTs per Post | 5 | 1 | 5x fewer |
| Shannon redundancy | 62.5% | 0% | eliminated |
| Read: rows scanned | 5 | 1 | 5x fewer |
| Read: app merge | required | none | eliminated |
| val JSON.parse | required | none | eliminated |
| Type safety | STRING only | typed columns | full |

## Design Principles

### 1. GraphAr-Native: 1 AT Record = 1 Row

GraphAr specification: "Each type of vertices (with the same label) constructs a logical vertex table."

P10v1 violated this by decomposing 1 AT record into N vertices (PostText, PostEmbed, etc.). P10v2 stores 1 AT record as 1 row with typed columns.

### 2. Kotoba/Datomic Columnar = Implicit Property Group

GraphAr uses **Property Groups** to split columns into separate files for selective I/O. Kotoba/Datomic columnar storage provides the same benefit natively — only accessed columns are read from disk. No explicit Property Group management needed.

### 3. Relationship Records = Edges

AT Protocol relationship records (Follow, Like, Repost, Block) are **edges by nature**. P10v1 stored them as vertices in `vertex_other`. P10v2 stores them as edges with AT metadata (rkey, repo) on the edge row.

### 4. No val STRING

`val STRING` is a type-erased universal column — Shannon entropy near 0 (all information carried by value, column name carries nothing). P10v2 uses typed columns: `text`, `embed`, `facets`, `display_name`, etc.

### 5. Actor + Profile Merged

In AT Protocol, `app.bsky.actor.profile` describes the actor. There is no separate "Actor" entity without a profile. P10v2 merges them into `vertex_actor` with `display_name`, `description`, `avatar_cid`, `banner_cid` columns.

### 6. GraphAr Adjacency List Types

GraphAr spec は edge 群に対して 4 種の隣接リストタイプを定義する:

| Type | 説明 | Graph Format |
|---|---|---|
| `ordered_by_source` | source vertex ID で sorted + partitioned | CSR (Compressed Sparse Row) |
| `ordered_by_dest` | dest vertex ID で sorted + partitioned | CSC (Compressed Sparse Column) |
| `unordered_by_source` | source vertex ID で partitioned (sort なし) | COO |
| `unordered_by_dest` | dest vertex ID で partitioned (sort なし) | COO |

P10v2 は Kotoba/Datomic DDL で GraphAr adjacency list を native に表現する:

- **`DISTRIBUTED BY HASH(src_vid)`** = source vertex による partition (GraphAr partition key)
- **`DUPLICATE KEY(src_vid, dst_vid)`** = source 内で dst_vid sorted (GraphAr ordered adjacency)
- 上記組み合わせ = **`ordered_by_source`** (CSR equivalent)

#### P10v2 Edge Table → GraphAr Adjacency List Mapping

| Edge Table | DUPLICATE KEY | DISTRIBUTED BY | Adjacency Type |
|---|---|---|---|
| `edge_follows` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_likes` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_reposts` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_blocks` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_has_author` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_reply` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_in_app` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_in_project` | `(edge_id)` | `HASH(src_vid)` | `unordered_by_source` |
| `edge_membership` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_list_item` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_governance` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_capability` | `(src_vid, dst_vid)` | `HASH(src_vid)` | `ordered_by_source` |
| `edge_other` | `(label, src_vid)` | `HASH(src_vid)` | `ordered_by_source` |

#### Reverse Adjacency (ordered_by_dest) の実現 — Materialized Views `[IMPLEMENTED 2026-04-08]`

`ordered_by_dest` (CSC) が必要なクエリを **Kotoba/Datomic Async Materialized View** で実現。イベントドリブンリフレッシュにより、write 完了後に即時反映。

**実装済み MV (12個)**:

| MV | Adjacency Type | 用途 |
|---|---|---|
| `mv_follows_reverse` | CSC (ordered_by_dest) | フォロワー逆引き |
| `mv_likes_reverse` | CSC | Like 逆引き |
| `mv_likes_by_post` | Aggregation | Post 別 Like 数 |
| `mv_reposts_by_post` | Aggregation | Post 別 Repost 数 |
| `mv_replies_by_post` | Aggregation | Post 別 Reply 数 |
| `mv_actor_follower_count` | Aggregation | フォロワー数 |
| `mv_actor_following_count` | Aggregation | フォロー数 |
| `mv_actor_post_count` | Aggregation | Post 数 |
| `mv_actor_stats` | Denormalized JOIN | プロフィール統合統計 (followers + following + posts in 1 query) |
| `mv_post_feed` | CSR (ordered_by_source) | 最新 Post フィード |
| `mv_feed_with_author` | Denormalized JOIN | フィード + 著者情報 |
| `mv_actor_search` | Index | アクター検索 |

**リフレッシュ戦略**: 定期更新ではなくイベントドリブン。Kagami Worker の write 完了後に `REFRESH MATERIALIZED VIEW` を fire-and-forget で発火。`TABLE_MV_DEPS` マップでテーブル→MV 依存関係を管理。

**キャッシュ**: Cloudflare Cache API (60s TTL) で Cypher クエリ結果をキャッシュ。MV + Cache API の 2 層で、Kotoba/Datomic への到達を最小化。

**Cypher パーサー拡張 (2026-04-08)**: `OPTIONAL MATCH` (LEFT JOIN)、`WITH` (CTE)、`UNION [ALL]` をサポート。37 テスト全パス。

当初検討した代替策:
1. ~~**Dedicated reverse table**~~: MV が同等の性能を実現、テーブル増殖を回避
2. ~~**Colocate Join**~~: MV の方がメンテナンスコスト低
3. ~~**定期更新 (EVERY interval)**~~: イベントドリブンに変更済み

### CSC 統一方針 `[DECIDED 2026-04-13]`

**問題**: 0002_streaming_mv.ts の MV1-4 (CSC replacement) と `edge_*_by_dest` 物理テーブルが重複。
MV1-4 は集約も JOIN もなく、`_by_dest` テーブルと同一データ。write 側で dual-write + MV incremental の二重コスト。

**決定**: CSC アクセスは MV に統一し、`_by_dest` テーブルへの manual dual-write を廃止する。

| 段階 | 内容 |
|---|---|
| Phase 1 | read 側を MV に切り替え (`_by_dest` → `mv_followers` 等) |
| Phase 2 | write 側の dual-write ロジック削除 (buildWritePlan の CSC INSERT 不要に) |
| Phase 3 | `_by_dest` テーブル DROP |

**理由**: Kotoba/Datomic streaming MV は base table への INSERT を自動追跡 (< 100ms)。手動 dual-write は冗長。

追跡: `deps.toml [[migrations."csc-mv-consolidation"]]`

### SQL Query Patterns: CSR / CSC / SpMV

Edge テーブルは COO 形式。クエリパターンで CSR/CSC を表現:

```sql
-- CSR (出エッジ): ユーザ X の follow 先
SELECT dst_vid FROM edge_follows WHERE src_vid = $actor_did;

-- CSC (入エッジ): ユーザ X のフォロワー (MV 経由)
SELECT src_vid FROM mv_followers WHERE dst_vid = $actor_did;

-- SpMV (PageRank 1-step): score を out-degree で正規化して伝搬
SELECT e.dst_vid,
       SUM(v.score / d.out_degree) AS new_score
FROM edge_follows e
JOIN mv_follow_out_degree d ON d.src_vid = e.src_vid
JOIN vertex_actor v ON v.vertex_id = e.src_vid
GROUP BY e.dst_vid;
```

degree MV (MV6 `mv_follow_out_degree` / MV7 `mv_follow_in_degree`) が SpMV の正規化因子を提供。

### 不足 MV (Phase 2 候補)

| 用途 | MV 名 | SQL パターン |
|---|---|---|
| 2-hop 近傍 (推薦) | `mv_follow_2hop` | `edge_follows f1 JOIN edge_follows f2 ON f1.dst_vid = f2.src_vid` |
| 重み付き in-degree (影響力) | `mv_weighted_in_degree` | `edge_follows f JOIN mv_follow_out_degree d ON d.src_vid = f.src_vid GROUP BY f.dst_vid` |
| Post engagement rate | `mv_post_engagement` | `mv_post_like_count JOIN vertex_post` で like/repost 比率 |

## Schema (DDL)

### Vertex Tables (12 dedicated + 1 fallback)

```sql
-- ── Core Social Entities ──

CREATE TABLE graphar.vertex_actor (
    vertex_id    VARCHAR(512),
    did          VARCHAR(512),
    handle       VARCHAR(512),
    display_name VARCHAR(1024),
    description  STRING,
    avatar_cid   VARCHAR(512),
    banner_cid   VARCHAR(512),
    status       VARCHAR(64),
    collection   VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(did) BUCKETS 16
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.vertex_post (
    vertex_id      VARCHAR(512),
    rkey           VARCHAR(512),
    repo           VARCHAR(512),
    text           STRING,
    embed          STRING,            -- JSON (images, external, record, etc.)
    facets         STRING,            -- JSON (mentions, links, hashtags)
    langs          STRING,            -- JSON array ["ja", "en"]
    reply_root     VARCHAR(1024),     -- at-uri
    reply_parent   VARCHAR(1024),     -- at-uri
    tags           STRING,            -- JSON array
    created_at     VARCHAR(64),       -- ISO 8601
    _alive         BOOLEAN,
    _seq           BIGINT,
    timestamp_ms   BIGINT,
    embedding       ARRAY<FLOAT>,     -- 384d (multilingual-e5-small)
    embedding_norm  DOUBLE,
    ivf_cluster_id  BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(repo) BUCKETS 32
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.vertex_message (
    vertex_id      VARCHAR(512),
    rkey           VARCHAR(512),
    repo           VARCHAR(512),
    convo_id       VARCHAR(512),
    sender_did     VARCHAR(512),
    text           STRING,
    embed          STRING,            -- JSON
    _alive         BOOLEAN,
    _seq           BIGINT,
    timestamp_ms   BIGINT,
    embedding       ARRAY<FLOAT>,
    embedding_norm  DOUBLE,
    ivf_cluster_id  BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(repo) BUCKETS 16
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Platform Entities ──

CREATE TABLE graphar.vertex_app (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    did          VARCHAR(512),
    display_name VARCHAR(1024),
    description  STRING,
    collection   VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(did) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.vertex_handle (
    vertex_id    VARCHAR(512),     -- = handle value
    did          VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(vertex_id) BUCKETS 4
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.vertex_list (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),     -- List, Generator, Labeler
    display_name VARCHAR(1024),
    description  STRING,
    purpose      VARCHAR(256),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(repo) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.vertex_convo (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),     -- Convo, Project
    display_name VARCHAR(1024),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(vertex_id) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Governance & Capability ──

CREATE TABLE graphar.vertex_governance (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),     -- GovernanceRule, GovernancePolicy
    name         VARCHAR(1024),
    kind         VARCHAR(256),
    standard     VARCHAR(256),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(repo) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.vertex_capability (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),     -- ActorCapability, Tool, ToolGrant, RoleBinding
    did          VARCHAR(512),
    name         VARCHAR(1024),
    description  VARCHAR(65533),
    collection   VARCHAR(512),
    status       VARCHAR(64),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(repo) BUCKETS 16
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Identity ──

CREATE TABLE graphar.vertex_did (
    vertex_id    VARCHAR(512),
    did          VARCHAR(512),
    repo         VARCHAR(512),
    doc          STRING,            -- DID document JSON
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(did) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Vector ──

CREATE TABLE graphar.vertex_ivf_centroid (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    collection   VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT,
    embedding    ARRAY<FLOAT>
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(vertex_id) BUCKETS 4
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Domain-Specific High-Volume ──

CREATE TABLE graphar.vertex_domain (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),     -- Article, Machine, etc.
    did          VARCHAR(512),
    text         STRING,
    display_name VARCHAR(1024),
    description  STRING,
    props        STRING,            -- JSON (domain-specific remaining properties)
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT,
    embedding       ARRAY<FLOAT>,
    embedding_norm  DOUBLE,
    ivf_cluster_id  BIGINT
) ENGINE = OLAP
DUPLICATE KEY(vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(repo) BUCKETS 16
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Fallback ──

CREATE TABLE graphar.vertex_other (
    vertex_id    VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),
    did          VARCHAR(512),
    collection   VARCHAR(512),
    status       VARCHAR(64),
    props        STRING,            -- JSON (all properties)
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(label, vertex_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(vertex_id) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);
```

### Edge Tables (12 dedicated + 1 fallback)

```sql
-- ── Social Interactions (AT records as edges) ──

CREATE TABLE graphar.edge_follows (
    edge_id      VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    src_vid      VARCHAR(512),     -- follower DID
    dst_vid      VARCHAR(512),     -- followee DID
    created_at   VARCHAR(64),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 16
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_likes (
    edge_id      VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    src_vid      VARCHAR(512),     -- liker DID
    dst_vid      VARCHAR(512),     -- liked post rkey
    subject_uri  VARCHAR(1024),
    subject_cid  VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 16
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_reposts (
    edge_id      VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    subject_uri  VARCHAR(1024),
    subject_cid  VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_blocks (
    edge_id      VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    label        VARCHAR(256),     -- Blocks, Mutes
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 4
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Structural Edges ──

CREATE TABLE graphar.edge_has_author (
    edge_id      VARCHAR(512),
    src_vid      VARCHAR(512),     -- Post vertex_id
    dst_vid      VARCHAR(512),     -- Actor DID
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_reply (
    edge_id      VARCHAR(512),
    src_vid      VARCHAR(512),     -- reply Post vertex_id
    dst_vid      VARCHAR(512),     -- parent Post vertex_id
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_in_app (
    edge_id      VARCHAR(512),
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    src_label    VARCHAR(256),
    dst_label    VARCHAR(256),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_in_project (
    edge_id      VARCHAR(512),
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(edge_id)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_membership (
    edge_id      VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    src_vid      VARCHAR(512),     -- member DID
    dst_vid      VARCHAR(512),     -- Convo/Project
    role         VARCHAR(256),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_list_item (
    edge_id      VARCHAR(512),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    src_vid      VARCHAR(512),     -- List
    dst_vid      VARCHAR(512),     -- member
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 4
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Governance & Capability Edges ──

CREATE TABLE graphar.edge_governance (
    edge_id      VARCHAR(512),
    label        VARCHAR(256),     -- CompliesWith, GovernedBy, Implements
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 4
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

CREATE TABLE graphar.edge_capability (
    edge_id      VARCHAR(512),
    label        VARCHAR(256),     -- OwnedBy, HasRoleBinding, ServedBy
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(src_vid, dst_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 4
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);

-- ── Fallback ──

CREATE TABLE graphar.edge_other (
    edge_id      VARCHAR(512),
    label        VARCHAR(256),
    rkey         VARCHAR(512),
    repo         VARCHAR(512),
    src_vid      VARCHAR(512),
    dst_vid      VARCHAR(512),
    src_label    VARCHAR(256),
    dst_label    VARCHAR(256),
    weight       DOUBLE,
    props        STRING,            -- JSON
    _alive       BOOLEAN,
    _seq         BIGINT,
    timestamp_ms BIGINT
) ENGINE = OLAP
DUPLICATE KEY(label, src_vid)
PARTITION BY RANGE(timestamp_ms) (
    PARTITION p_recent VALUES LESS THAN (UNIX_TIMESTAMP(NOW()) * 1000),
    PARTITION p_future VALUES LESS THAN MAXVALUE
)
DISTRIBUTED BY HASH(src_vid) BUCKETS 8
PROPERTIES (
    "replication_num" = "1",
    "storage_cooldown_time" = "300",
    "dynamic_partition.enable" = "true",
    "dynamic_partition.time_unit" = "MONTH",
    "dynamic_partition.start" = "-12",
    "dynamic_partition.end" = "1"
);
```

## Label → Table Router

### Vertex Routing (13 tables)

| Labels | Table | Hash Key | Buckets | Multi-label |
|---|---|---|---|---|
| Actor | `vertex_actor` | did | 16 | no |
| Post | `vertex_post` | repo | 32 | no |
| Message | `vertex_message` | repo | 16 | no |
| App | `vertex_app` | did | 8 | no |
| Handle | `vertex_handle` | vertex_id | 4 | no |
| List, Generator, Labeler | `vertex_list` | repo | 8 | yes |
| Convo, Project | `vertex_convo` | vertex_id | 8 | yes |
| GovernanceRule, GovernancePolicy | `vertex_governance` | repo | 8 | yes |
| ActorCapability, Tool, ToolGrant, RoleBinding | `vertex_capability` | repo | 16 | yes |
| Did | `vertex_did` | did | 8 | no |
| IvfCentroid | `vertex_ivf_centroid` | vertex_id | 4 | no |
| Article, Machine | `vertex_domain` | repo | 16 | yes |
| *(fallback)* | `vertex_other` | vertex_id | 8 | yes |

### Edge Routing (13 tables)

| Labels | Table | Hash Key | Buckets | Multi-label |
|---|---|---|---|---|
| Follows | `edge_follows` | src_vid | 16 | no |
| Likes | `edge_likes` | src_vid | 16 | no |
| Reposts | `edge_reposts` | src_vid | 8 | no |
| Blocks, Mutes | `edge_blocks` | src_vid | 4 | yes |
| HasAuthor | `edge_has_author` | src_vid | 8 | no |
| Reply | `edge_reply` | src_vid | 8 | no |
| InApp | `edge_in_app` | src_vid | 8 | no |
| InProject | `edge_in_project` | src_vid | 8 | no |
| Membership | `edge_membership` | src_vid | 8 | no |
| ListItem | `edge_list_item` | src_vid | 4 | no |
| CompliesWith, GovernedBy, Implements | `edge_governance` | src_vid | 4 | yes |
| OwnedBy, HasRoleBinding, ServedBy | `edge_capability` | src_vid | 4 | yes |
| *(fallback)* | `edge_other` | src_vid | 8 | yes |

## Write Path Change

### Before (P10v1 — property decomposition)

```typescript
// pds-core.ts: 1 Post → 5 vertices
await env.KAGAMI_RPC.writeBatch([
  { record_type: "vertex", label: "Post",       vertex_id: rkey, rkey, repo, collection, ... },
  { record_type: "vertex", label: "PostText",   vertex_id: `${rkey}::text`, rkey, repo, val: text, ... },
  { record_type: "vertex", label: "PostEmbed",  vertex_id: `${rkey}::embed`, rkey, repo, val: JSON.stringify(embed), ... },
  { record_type: "vertex", label: "PostFacets", vertex_id: `${rkey}::facets`, rkey, repo, val: JSON.stringify(facets), ... },
  { record_type: "vertex", label: "PostProps",  vertex_id: `${rkey}::props`, rkey, repo, val: JSON.stringify(rest), ... },
]);
```

### After (P10v2 — typed columnar)

```typescript
// 1 Post → 1 vertex + structural edges
await env.KAGAMI_RPC.writeBatch([
  { record_type: "vertex", label: "Post", vertex_id: rkey, rkey, repo,
    text, embed: JSON.stringify(embed), facets: JSON.stringify(facets),
    langs: JSON.stringify(langs), reply_root: reply?.root?.uri,
    reply_parent: reply?.parent?.uri, created_at: createdAt, ... },
  { record_type: "edge", label: "HasAuthor", edge_id: `${rkey}::author`,
    src_vid: rkey, dst_vid: repo, ... },
  // Reply edge (if reply)
  ...(reply?.parent ? [{ record_type: "edge", label: "Reply", edge_id: `${rkey}::reply`,
    src_vid: rkey, dst_vid: parseAtUri(reply.parent.uri).rkey, ... }] : []),
]);

// 1 Follow → 1 edge (not a vertex)
await env.KAGAMI_RPC.writeBatch([
  { record_type: "edge", label: "Follows", edge_id: rkey, rkey, repo,
    src_vid: repo, dst_vid: subjectDid, created_at: createdAt, ... },
]);

// 1 Like → 1 edge (not a vertex)
await env.KAGAMI_RPC.writeBatch([
  { record_type: "edge", label: "Likes", edge_id: rkey, rkey, repo,
    src_vid: repo, dst_vid: subjectRkey,
    subject_uri: subject.uri, subject_cid: subject.cid, ... },
]);
```

## Read Path Change

### Before (P10v1)

```cypher
-- Get Post: scan 5 rows, merge in app
MATCH (n) WHERE n.rkey = $rkey AND n.repo = $did
RETURN n.label, n.val, n.vertex_id LIMIT 10
-- → PostText.val, PostEmbed.val, PostFacets.val, PostProps.val → app merge
```

### After (P10v2)

```cypher
-- Get Post: 1 row, typed columns
MATCH (p:Post) WHERE p.rkey = $rkey AND p.repo = $did
RETURN p.text, p.embed, p.facets, p.langs, p.reply_root, p.reply_parent LIMIT 1
-- → direct column access, no JSON.parse for text

-- Timeline (text only — Kotoba/Datomic reads only text column from disk)
MATCH (p:Post) WHERE p.repo IN [$did1, $did2]
RETURN p.rkey, p.repo, p.text, p.created_at LIMIT 50

-- Text search
MATCH (p:Post) WHERE p.text CONTAINS $q
RETURN p.rkey, p.repo, p.text LIMIT 50

-- Actor profile
MATCH (a:Actor) WHERE a.did = $did
RETURN a.display_name, a.description, a.handle, a.avatar_cid LIMIT 1

-- Follow count
MATCH (e:Follows) WHERE e.src_vid = $did RETURN count(*) AS cnt

-- Like check
MATCH (e:Likes) WHERE e.src_vid = $did AND e.dst_vid = $postRkey RETURN e.edge_id LIMIT 1
```

## Zero-Downtime Migration: SWAP TABLE

Kotoba/Datomic の `ALTER TABLE SWAP` でスキーマ変更を atomic (~30ms) に適用。

```sql
-- 1. 新スキーマのテーブルを作成
CREATE TABLE graphar.vertex_actor_v2 (... new columns ...)
PARTITION BY RANGE(timestamp_ms) (...) DISTRIBUTED BY HASH(did) BUCKETS 16 PROPERTIES (...);

-- 2. データをバックグラウンドでコピー (既存テーブルで read/write 継続)
INSERT INTO graphar.vertex_actor_v2 SELECT ... FROM graphar.vertex_actor;

-- 3. Atomic swap (metadata-only, ~30ms, zero downtime)
ALTER TABLE graphar.vertex_actor SWAP WITH vertex_actor_v2;

-- 4. 旧テーブルを削除 (swap 後は旧データが _v2 名で残る)
DROP TABLE graphar.vertex_actor_v2;
```

**SWAP TABLE は Kotoba/Datomic 3.3.8 で検証済み** (elapsed: 28ms)。

### Iceberg External Catalog 評価 (rejected)

Iceberg の partition/schema evolution は metadata-only で理想的だが、クエリ性能が劣化する。

| 劣化要因 | 推定 overhead |
|---------|--------------|
| Iceberg metadata chain (S3 GET × 2-3: metadata.json → manifest-list → manifest) | +60-120ms |
| S3 data file read (Parquet, CN datacache 不使用) | +20-40ms per table |
| Parquet decode (vs Kotoba/Datomic native columnar) | +5-10ms |
| JOIN: 3 table × metadata chain | +180-360ms |

| Pattern | Internal OLAP | Iceberg External (warm cache) | 劣化 |
|---------|--------------|------------------------------|------|
| A-point | 12ms | 30-50ms | 3-4x |
| B-join | 30ms | 90-150ms | 3-5x |
| D-2hop | 50ms | 200-400ms | 4-8x |

**結論**: 50ms SLA を守るには Internal OLAP + SWAP TABLE が最適。Iceberg External は cold analytics / time travel 用途に限定。

## Migration Required Changes

| File | Change |
|---|---|
| `_archive/30-graph/kagami-live-260414/src/schema/p10.gen.ts` | **Done** — P10v2 schema |
| `_archive/30-graph/kagami-live-260414/src/types.ts` | VERTEX_PROMOTED_COLUMNS → expand (text, embed, display_name, etc.) |
| `_archive/30-graph/kagami-live-260414/src/cypher/plan.ts` | resolveReturnColumns → typed columns instead of val |
| `50-infra/cloudflare/workers/atproto/src/pds-core.ts` | kagamiWriteVertex → 1 row write, relationship-as-edge |
| `50-infra/cloudflare/workers/atproto/src/pds-helpers.ts` | buildMergeProps → typed record builder |
| `50-infra/cloudflare/workers/atproto/src/pds-handlers-feed.ts` | Cypher queries: PostText → Post.text |
| `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts` | Write dispatch: typed columns |
| Kotoba/Datomic DDL | CREATE TABLE (this doc) |
| Kotoba/Datomic data | P10v1 → P10v2 ETL (INSERT INTO SELECT) |

## GraphAr Spec Alignment

| GraphAr Spec | P10v2 | Alignment |
|---|---|---|
| 1 label = 1 table | `graphar.vertex_{label}` | native |
| (src, edge, dst) = 1 edge table | `graphar.edge_{type}` | partial (src/dst label on column) |
| Property Group (columnar I/O) | Kotoba/Datomic columnar storage | implicit (engine-level) |
| Chunk (fixed row count) | Kotoba/Datomic PARTITION BY RANGE(timestamp_ms) | time-based |
| Adjacency List Type | `ordered_by_source` (CSR) via DUPLICATE KEY + HASH(src_vid)。Reverse (CSC) は MPP JOIN | native (DDL-level) |
| Typed properties | typed SQL columns | native |
| val STRING blob | eliminated | eliminated |

## Declarative Schema Management

**DDL は `p10.gen.ts` から自動生成。手書き DDL script 禁止。**

### Single Source of Truth

| Layer | File | Role |
|---|---|---|
| **Schema definition** | `_archive/30-graph/kagami-live-260414/src/schema/p10.gen.ts` | Table/column/label/partition 宣言 |
| **Column type map** | `P10_COLUMN_TYPES` (same file) | Column name → Kotoba/Datomic SQL type |
| **DDL generation** | `generateVertexDDL()` / `generateEdgeDDL()` / `generateAllDDL()` | 宣言 → `CREATE TABLE IF NOT EXISTS` DDL |
| **Schema validation** | `70-tools/70-tools/70-tools/scripts/schema-check-local.ts` | `val` 禁止、column type 存在チェック |
| **Schema apply** | `70-tools/70-tools/70-tools/scripts/schema-apply.ts` | DDL を Kotoba/Datomic に冪等適用 |
| **This doc** | DDL reference (人間向け) | `p10.gen.ts` と一致を維持 |

### Usage

```bash
cd _archive/30-graph/kagami-live-260414

# Validate schema (pretest)
npx tsx 70-tools/70-tools/70-tools/scripts/schema-check-local.ts

# Generate DDL (dry-run)
npx tsx 70-tools/70-tools/70-tools/scripts/schema-apply.ts --dry-run

# Apply to Kotoba/Datomic (idempotent)
npx tsx 70-tools/70-tools/70-tools/scripts/schema-apply.ts

# Custom endpoint
KAGAMI_ENDPOINT=http://... KAGAMI_TOKEN=... npx tsx 70-tools/70-tools/70-tools/scripts/schema-apply.ts
```

### Adding a New Table

1. `p10.gen.ts`: `P10_VERTEX_TABLES` or `P10_EDGE_TABLES` に table definition 追加
2. `p10.gen.ts`: 新規カラムがあれば `P10_COLUMN_TYPES` に型追加
3. `pds-core.ts`: `buildTypedVertex()` に label 分岐追加（typed column mapping）
4. `schema-check-local.ts` パス確認
5. `schema-apply.ts --dry-run` で DDL 確認
6. `schema-apply.ts` で Kotoba/Datomic 適用
7. この doc の DDL section を更新

**禁止**: 手書き DDL script、`val STRING` column、`p10.gen.ts` 外での table 定義
