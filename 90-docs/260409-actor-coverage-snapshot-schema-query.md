# ActorCoverageSnapshot schema/query design (actorName/nodeCount fix)

## 問題
- `ActorCoverageSnapshot` の write が `SET` 依存だったため、実行系で `SET` 句が反映されず `actorName/nodeCount` が `NULL` になっていた。
- さらに `graph.write` の params 受け渡しが文字列化されていたため、`$did` 展開も壊れるケースがあった（修正済み）。

## スキーマ方針
- `ActorCoverageSnapshot` は `graphar.vertex_actor_coverage` 専用テーブルに格納する。
- 最低限の正規化カラム:
  - key: `actorDid`, `bucket`
  - snapshot: `actorName`, `nanoid`, `nodeCount`, `latestTs`, `repo`, `collection`, `status`
  - system: `_alive`, `_seq`, `timestamp_ms`

## write query 方針
- `SET` を使わず、`MERGE` map に保存対象カラムをすべて含める。
- 前step出力は `args.params` に `$stepId...` を置き、executor 補間で解決する。

### coverageNodes
```cypher
MATCH (n) WHERE n.repo = $did
RETURN count(n) AS nodeCount, coalesce(max(n.timestamp_ms), 0) AS latestTs
LIMIT 1
```

### coverageSnapshot (graph.write template)
```cypher
MERGE (c:ActorCoverageSnapshot {
  actorDid: $did,
  bucket: $bucket,
  actorName: $actorName,
  nanoid: $nanoid,
  nodeCount: $nodeCount,
  latestTs: $latestTs,
  repo: $did,
  collection: $collection,
  status: 'active'
})
```

### coverageSnapshot params
```json
{
  "bucket": "6h",
  "actorName": "<manifest.name>",
  "nanoid": "<manifest.nanoid>",
  "nodeCount": "$coverageNodes.rows[0].nodeCount",
  "latestTs": 0,
  "collection": "com.etzhayyim.apps.<segment>.coverageSnapshot"
}
```

## read query 方針
- 最新スナップショットを `actorDid+bucket` で読む。
- 取得クエリ:
```sql
SELECT actorDid, bucket, actorName, nodeCount, latestTs, collection, status, _seq
FROM graphar.vertex_actor_coverage
WHERE actorDid = '<did>' AND bucket = '6h'
ORDER BY _seq DESC
LIMIT 1
```

## 実装メモ
- 生成ロジック更新: `70-tools/scripts/actors/add-t1-coverage-pipelines.mjs`
- 既存manifest一括更新: `70-tools/scripts/actors/fix-coverage-snapshot-pipelines.mjs`
- 乖離検査: `70-tools/scripts/lint/p10-write-schema-guard.mjs`
