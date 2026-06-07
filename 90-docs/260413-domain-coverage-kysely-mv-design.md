# Domain Coverage Kysely MV Design

## Goal

`etzhayyim coverage domain` の live reconciliation を、`vertex_did` / `vertex_authority_*` への逐次 `COUNT(*)` / `COUNT(DISTINCT)` ではなく、Kotoba/Datomic の materialized view 経由で安定・低レイテンシに取得する。

狙いは 3 つ:

1. CLI の N 回直列クエリを 1 回の `SELECT` に縮約する
2. `family` / `cultural` / `academic` などの alias domain を正規化する
3. Kysely から `selectFrom("mv_domain_coverage_live")` で型安全に読む

## Ops Update (2026-04-16)

- **Count Rollup MVs 追加** (`20260416170000_count_rollups_mv`): 10 pre-computed streaming MVs を追加。
  リポジトリ全体の ad-hoc `fn.count()` / `countAll()` ホットパスをすべて `SUM(cnt)` 読みに置き換え完了。
- **適用済みファイル**:
  - `toshi-kozan/src/app.ts` `shouldAnalyze` ブロック: `vertex_other` ad-hoc count → `mv_vertex_other_count`
  - 135 states apps / isin / legal-entity は事前移行済み
- **`deps.toml` 更新**: `[[migrations]] count-rollups-mv-20260416170000` + `[[conventions]] Kysely COUNT → MV SUM` を追加。
- 新規 COUNT クエリを書く場合は `deps.toml [[conventions]] Kysely COUNT → MV SUM` を参照すること。

## Ops Update (2026-04-15)

- Local CLI DB default DSN は `postgres://root@127.0.0.1:14566/dev?sslmode=disable` (port-forward)。
- `mv_domain_coverage_live` / `mv_domain_repo_authority_count` が欠落した環境向けに、
  `30-graph/graph-schema/migrations/20260415131000_restore_domain_coverage_live_mv.ts`
  を追加した。
- 運用上は次の順で復旧する:
  1. Kysely migration を適用
  2. `mv_domain_coverage_live` の存在確認
  3. `etzhayyim coverage domain` の Reconciliation で live 値確認

## Current Problem

現状の reconciliation は Go 側で domain ごとに以下を直列実行している。

- `COUNT(DISTINCT vertex_id)` on `vertex_did WHERE repo = $1`
- `COUNT(*)` on one of `vertex_authority_* WHERE repo = $1`

問題:

- 1 domain あたり 2 query、全 11 domain で 22 query
- alias domain (`family`, `cultural`, `academic`) が別 target を持つのに、authority table 側は同一 table を共有
- Kysely read path に載っておらず、Graph Worker / app / CLI で共通 read model を使えない

## Design Summary

`live reconciliation` 用の read model を 3 層に分ける。

1. `mv_domain_repo_did_count`
2. `mv_domain_repo_authority_count`
3. `mv_domain_coverage_live`

加えて、静的 target を DB 内に持つ小さな dimension table を 1 つ置く。

- `dim_domain_coverage_target`

これで最終 read は:

```sql
SELECT *
FROM mv_domain_coverage_live
WHERE kind = ANY($1)
ORDER BY kind;
```

になる。

## Schema

### 1. `dim_domain_coverage_target`

live count と seed/target 定義を同じ query plan に載せるための static table。

```sql
CREATE TABLE IF NOT EXISTS dim_domain_coverage_target (
  kind text PRIMARY KEY,
  repo text NOT NULL,
  app text NOT NULL,
  authority_target bigint NOT NULL,
  rule_target bigint NOT NULL,
  scope_target bigint NOT NULL,
  total_target bigint NOT NULL,
  authority_seed bigint NOT NULL,
  rule_seed bigint NOT NULL,
  scope_seed bigint NOT NULL,
  total_seed bigint NOT NULL,
  authority_table text NOT NULL,
  authority_kind text NOT NULL
);
```

`authority_kind` は authority table 粒度の正規化キー。

- `customary`, `family`, `cultural` → `customary`
- `professional`, `academic` → `professional`
- それ以外は `kind == authority_kind`

この列を置く理由:

- live authority count は table 粒度でしか取れない
- ただし coverage の target は `family` と `cultural` で別
- 正規化キーを明示しないと read query 側で if/switch が残る

### 2. `mv_domain_repo_did_count`

repo ごとの DID 数。`kind` は static dim から join で付与する。

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_repo_did_count AS
SELECT
  t.kind,
  t.repo,
  COUNT(*)::bigint AS did_count
FROM dim_domain_coverage_target t
LEFT JOIN vertex_did d
  ON d.repo = t.repo
GROUP BY t.kind, t.repo;
```

注記:

- `COUNT(DISTINCT vertex_id)` を避け、`vertex_did` が current-state table で `vertex_id` unique である前提を使う
- もし unique が保証されないなら、先に `mv_vertex_did_repo_vertex` を作って dedup する

dedup が必要な場合:

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_did_repo_vertex AS
SELECT repo, vertex_id
FROM vertex_did
GROUP BY repo, vertex_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_repo_did_count AS
SELECT
  t.kind,
  t.repo,
  COUNT(*)::bigint AS did_count
FROM dim_domain_coverage_target t
LEFT JOIN mv_vertex_did_repo_vertex d
  ON d.repo = t.repo
GROUP BY t.kind, t.repo;
```

### 3. `mv_domain_repo_authority_count`

authority table 群を 1 つの read model に正規化する。

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_repo_authority_count AS
SELECT 'sovereign'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_sovereign
GROUP BY repo

UNION ALL

SELECT 'treaty'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_treaty
GROUP BY repo

UNION ALL

SELECT 'religious'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_religious
GROUP BY repo

UNION ALL

SELECT 'customary'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_customary
GROUP BY repo

UNION ALL

SELECT 'community'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_community
GROUP BY repo

UNION ALL

SELECT 'professional'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_professional
GROUP BY repo

UNION ALL

SELECT 'industry'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_industry
GROUP BY repo

UNION ALL

SELECT 'blockchain'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count
FROM vertex_authority_blockchain
GROUP BY repo;
```

この MV は alias を吸収しない。吸収は次段の join で行う。

### 4. `mv_domain_coverage_live`

CLI / PDS / app が直接読む最終 MV。

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_coverage_live AS
SELECT
  t.kind,
  t.repo,
  t.app,
  t.authority_kind,
  t.authority_seed,
  t.rule_seed,
  t.scope_seed,
  t.total_seed,
  t.authority_target,
  t.rule_target,
  t.scope_target,
  t.total_target,
  COALESCE(d.did_count, 0) AS did_count,
  COALESCE(a.authority_count, 0) AS authority_count,
  COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0) AS live_record_count,
  CASE
    WHEN t.total_target > 0
    THEN COALESCE(d.did_count, 0)::double precision / t.total_target::double precision
    ELSE 0.0
  END AS live_coverage_did,
  CASE
    WHEN t.total_target > 0
    THEN (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0))::double precision / t.total_target::double precision
    ELSE 0.0
  END AS live_coverage_record,
  CASE
    WHEN t.total_target > 0
    THEN t.total_seed::double precision / t.total_target::double precision
    ELSE 0.0
  END AS authority_rate,
  CASE
    WHEN t.total_target > 0
    THEN (t.total_seed - COALESCE(d.did_count, 0))::double precision / t.total_target::double precision
    ELSE 0.0
  END AS delta_did,
  CASE
    WHEN t.total_target > 0
    THEN (t.total_seed - (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0)))::double precision / t.total_target::double precision
    ELSE 0.0
  END AS delta_record
FROM dim_domain_coverage_target t
LEFT JOIN mv_domain_repo_did_count d
  ON d.kind = t.kind AND d.repo = t.repo
LEFT JOIN mv_domain_repo_authority_count a
  ON a.authority_kind = t.authority_kind AND a.repo = t.repo;
```

## Why This Shape

### `repo` を主キー側に残す理由

将来 `states.etzhayyim.com` のような multi-app / multi-repo domain を吸収しやすい。

今は 1 kind = 1 repo に近いが、read model を `kind` 単独に潰すと将来壊れる。

### `kind` と `authority_kind` を分ける理由

`family` と `cultural` は target が別なのに authority rows は同じ `vertex_authority_customary` に乗る。

このねじれを DB schema で表現しないと、呼び出し元に switch が漏れる。

### seed/target を MV 側に持つ理由

CLI 側の `authorityDomains` ハードコードを削除できる。

結果として:

- Go CLI
- PDS handler
- app Kysely client

が同じ source of truth を読む。

## Kysely Read Model

`30-graph/graph-schema/src/database.ts` に以下を追加する想定。

```ts
export interface DimDomainCoverageTargetRow {
  kind?: string | null;
  repo?: string | null;
  app?: string | null;
  authority_target?: number | bigint | null;
  rule_target?: number | bigint | null;
  scope_target?: number | bigint | null;
  total_target?: number | bigint | null;
  authority_seed?: number | bigint | null;
  rule_seed?: number | bigint | null;
  scope_seed?: number | bigint | null;
  total_seed?: number | bigint | null;
  authority_table?: string | null;
  authority_kind?: string | null;
}

export interface MvDomainRepoDidCountRow {
  kind?: string | null;
  repo?: string | null;
  did_count?: number | bigint | null;
}

export interface MvDomainRepoAuthorityCountRow {
  authority_kind?: string | null;
  repo?: string | null;
  authority_count?: number | bigint | null;
}

export interface MvDomainCoverageLiveRow {
  kind?: string | null;
  repo?: string | null;
  app?: string | null;
  authority_kind?: string | null;
  authority_seed?: number | bigint | null;
  rule_seed?: number | bigint | null;
  scope_seed?: number | bigint | null;
  total_seed?: number | bigint | null;
  authority_target?: number | bigint | null;
  rule_target?: number | bigint | null;
  scope_target?: number | bigint | null;
  total_target?: number | bigint | null;
  did_count?: number | bigint | null;
  authority_count?: number | bigint | null;
  live_record_count?: number | bigint | null;
  live_coverage_did?: number | null;
  live_coverage_record?: number | null;
  authority_rate?: number | null;
  delta_did?: number | null;
  delta_record?: number | null;
}
```

`Database` interface には以下を追加する。

```ts
dim_domain_coverage_target: DimDomainCoverageTargetRow;
mv_domain_repo_did_count: MvDomainRepoDidCountRow;
mv_domain_repo_authority_count: MvDomainRepoAuthorityCountRow;
mv_domain_coverage_live: MvDomainCoverageLiveRow;
```

## Kysely Query Pattern

最終 read はこれでよい。

```ts
const rows = await db
  .selectFrom("mv_domain_coverage_live")
  .select([
    "kind",
    "repo",
    "app",
    "did_count",
    "authority_count",
    "live_record_count",
    "live_coverage_did",
    "live_coverage_record",
    "authority_rate",
    "delta_did",
    "delta_record",
  ])
  .orderBy("kind", "asc")
  .execute();
```

domain filter:

```ts
const rows = await db
  .selectFrom("mv_domain_coverage_live")
  .selectAll()
  .where("kind", "in", selectedKinds)
  .execute();
```

priority list:

```ts
const rows = await db
  .selectFrom("mv_domain_coverage_live")
  .select([
    "kind",
    "total_target",
    "live_record_count",
    "delta_record",
    "live_coverage_record",
  ])
  .where("total_target", ">", 0)
  .orderBy("delta_record", "desc")
  .execute();
```

## Migration Shape

新 migration 例:

`30-graph/graph-schema/migrations/0014_domain_coverage_live_mv.ts`

順序:

1. `CREATE TABLE dim_domain_coverage_target`
2. static rows を `INSERT`
3. `CREATE MATERIALIZED VIEW mv_domain_repo_did_count`
4. `CREATE MATERIALIZED VIEW mv_domain_repo_authority_count`
5. `CREATE MATERIALIZED VIEW mv_domain_coverage_live`

`down()` は逆順 drop。

## Data Seed Example

```sql
INSERT INTO dim_domain_coverage_target (
  kind, repo, app,
  authority_target, rule_target, scope_target, total_target,
  authority_seed, rule_seed, scope_seed, total_seed,
  authority_table, authority_kind
) VALUES
  ('sovereign', 'did:web:states.etzhayyim.com', 'states.etzhayyim.com', 195, 195000, 195, 195390, 195, 390, 195, 780, 'vertex_authority_sovereign', 'sovereign'),
  ('treaty', 'did:web:treaty.etzhayyim.com', 'treaty.etzhayyim.com', 500, 5000, 50, 5550, 48, 85, 18, 151, 'vertex_authority_treaty', 'treaty'),
  ('religious', 'did:web:religious.etzhayyim.com', 'religious.etzhayyim.com', 30, 3000, 10, 3040, 25, 60, 10, 95, 'vertex_authority_religious', 'religious'),
  ('community', 'did:web:communities.etzhayyim.com', 'communities.etzhayyim.com', 100, 1000, 20, 1120, 69, 35, 8, 112, 'vertex_authority_community', 'community'),
  ('customary', 'did:web:customary.etzhayyim.com', 'customary.etzhayyim.com', 100, 500, 50, 650, 28, 40, 12, 80, 'vertex_authority_customary', 'customary'),
  ('family', 'did:web:tradition.etzhayyim.com', 'tradition.etzhayyim.com', 500, 2000, 100, 2600, 25, 30, 12, 67, 'vertex_authority_customary', 'customary'),
  ('cultural', 'did:web:tradition.etzhayyim.com', 'tradition.etzhayyim.com', 200, 1000, 50, 1250, 30, 24, 12, 66, 'vertex_authority_customary', 'customary'),
  ('professional', 'did:web:ethics.etzhayyim.com', 'ethics.etzhayyim.com', 100, 500, 30, 630, 24, 48, 12, 84, 'vertex_authority_professional', 'professional'),
  ('academic', 'did:web:ethics.etzhayyim.com', 'ethics.etzhayyim.com', 50, 200, 10, 260, 10, 18, 5, 33, 'vertex_authority_professional', 'professional'),
  ('industry', 'did:web:industry-standard.etzhayyim.com', 'industry-standard.etzhayyim.com', 200, 3000, 50, 3250, 42, 60, 15, 117, 'vertex_authority_industry', 'industry'),
  ('blockchain', 'did:web:blockchain.etzhayyim.com', 'blockchain.etzhayyim.com', 100, 5000, 200, 5300, 30, 65, 20, 115, 'vertex_authority_blockchain', 'blockchain');
```

`private` は dynamic/per-company なので dimension table には入れない。

## CLI Impact

Go 側 `collectCoverageReconciliationKagami()` は削除できる。

代わりに 1 query:

```sql
SELECT kind, authority_rate, live_coverage_did, live_coverage_record, delta_did, delta_record
FROM mv_domain_coverage_live
ORDER BY kind;
```

これで:

- serial query ループ削除
- table dispatch 削除
- timeout 原因の切り分け対象を DB read model 側に集約

## Recommendation

実装順はこれでよい。

1. `dim_domain_coverage_target` を migration 追加
2. `mv_domain_repo_authority_count` と `mv_domain_coverage_live` を追加
3. `30-graph/graph-schema/src/database.ts` に型追加
4. PDS/CLI の domain reconciliation を `mv_domain_coverage_live` 読みへ置換
5. `authorityDomains` ハードコードを段階的に削除

最重要点は、`kind` と `authority_kind` を分離した schema にすること。ここを潰すと `family` / `cultural` / `academic` の集計がまたアプリ側ロジックに漏れる。
