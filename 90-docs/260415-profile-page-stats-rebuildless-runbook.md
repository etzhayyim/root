# Profile Page Stats Rebuildless Runbook

`mv_profile_page_stats` の full recreate（`DROP MATERIALIZED VIEW`）で長時間停止・高メモリ化が発生する問題を、分離 MV + VIEW で運用する手順。

## Goal

- `vertex_page`（高 cardinality）の再集計を profile 全体 MV から分離する
- read path で relation を安定化し、blue/green で切替できるようにする
- 本番で「重い DDL の同時実行」を禁止する

## Topology

- `mv_profile_core_stats`
  - followers/following/posts/governance/tool の集約（比較的小さい）
- `mv_page_count_by_owner_canonical_did`
  - `vertex_page` 由来 page_count 専用（重い処理をここへ隔離）
- `view_profile_page_stats`
  - 上記2 MV を join して appview から読む統一 read surface
- appview
  - `view_profile_page_stats` 優先、未展開環境は `mv_profile_page_stats` に fallback

## One-time Migration

実装ファイル:

- [20260415200000_profile_page_stats_rebuildless_split.ts](/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/migrations/20260415200000_profile_page_stats_rebuildless_split.ts)
- [feed.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/handlers/appview/feed.ts)

適用:

```bash
cd 30-graph/graph-schema
DATABASE_URL='postgresql://root@172.236.132.11:4566/dev?sslmode=disable' pnpm db:migrate
```

## DDL Concurrency Rule

重い backfill 中に他 DDL を流さない。

- 禁止: `CREATE MATERIALIZED VIEW ... FROM vertex_page ...` 実行中に別 `CREATE TABLE/VIEW/MV`
- 許可: 読み取りクエリ、軽微な `SELECT`、監視クエリ

運用チェック:

```sql
SHOW JOBS;
```

`FOREGROUND` の重い job がある間は、追加 DDL を投入しない。

## Cutover Procedure (Blue/Green)

1. 新 MV 群を作成し backfill 完了を待つ

```sql
SHOW JOBS;
```

2. 値一致を確認

```sql
SELECT actor_did, page_count
FROM view_profile_page_stats
WHERE canonical_actor_did IN (
  'did:web:en-wikipedia-org.etzhayyim.com',
  'did:web:en-wiktionary-org.etzhayyim.com'
)
ORDER BY actor_did;
```

3. appview は既に view 優先なので、そのまま利用開始
4. 安定後、旧 `mv_profile_page_stats` の依存を除去して retire 計画へ進む

## Sanity Queries

```sql
SELECT count(*) AS total_rows FROM view_profile_page_stats;
```

```sql
SELECT canonical_actor_did, page_count
FROM mv_page_count_by_owner_canonical_did
WHERE canonical_actor_did IN (
  'did:web:en-wikipedia-org.etzhayyim.com',
  'did:web:en-wiktionary-org.etzhayyim.com'
)
ORDER BY canonical_actor_did;
```

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('mv_profile_core_stats', 'mv_page_count_by_owner_canonical_did')
ORDER BY tablename, indexname;
```

## Failure Handling

1. `SHOW JOBS` で停滞/失敗 job を特定
2. `rw_catalog.rw_event_logs` で `INJECT_BARRIER_FAIL` / `GLOBAL_RECOVERY_FAILURE` を確認
3. 追加 DDL を停止
4. 必要なら問題 job のみ `CANCEL JOB <id>` して単独再実行

```sql
SELECT event_type, "timestamp", LEFT(info::text, 220) AS info
FROM rw_catalog.rw_event_logs
WHERE "timestamp" > now() - interval '30 minutes'
  AND event_type IN (
    'GLOBAL_RECOVERY_FAILURE',
    'GLOBAL_RECOVERY_SUCCESS',
    'INJECT_BARRIER_FAIL',
    'CREATE_STREAM_JOB_FAIL'
  )
ORDER BY "timestamp" DESC
LIMIT 30;
```

## Acceptance Criteria

- `view_profile_page_stats` で profile counts が返る
- `en-wiktionary-org` / `en-wikipedia-org` の `page_count` が 0 でない
- 重い backfill 中に追加 DDL を流さない運用が守られる
