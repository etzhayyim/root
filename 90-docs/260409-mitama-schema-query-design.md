# mitama ActorManifest: Schema & Query Design (2026-04-09)

## Goal
`etzhayyim mitama register/list/inspect` を、PDS/graph の部分的なスキーマ差分があっても壊れない read/write 契約にする。

## Canonical Storage Contract

### 1. Stable table
`graphar.vertex_actor_manifest`

### 2. Required columns (hard contract)
- `did` (actor DID)
- `name`
- `nanoid`
- `execution_tier`
- `status`
- `timestamp_ms`
- `_alive`
- `collection` (=`com.etzhayyim.actor.manifest`)
- `repo`
- `rkey`

### 3. Payload column (source of truth)
- `val` = full `ActorManifest` JSON string

`inspect` は `val` を最優先で返し、`val` が空/壊れている時のみ typed columns から最小復元する。

### 4. Optional promoted columns (best-effort)
- `display_name`
- `description`

これらは検索/一覧の補助列。存在しない環境でも `inspect` を壊さない。

## Write Query Design

### registerManifest
- Cypher `MERGE (m:ActorManifest {did: $did})`
- `SET`
  - required columns
  - `val` (full JSON)
  - optional promoted columns (`display_name`, `description`)

方針:
- 読みの互換性を優先し、`val` を常に書く。
- 新しい promoted columns を追加しても、read はそれを必須にしない。

## Read Query Design

### list (CLI)
SQL を使って DID 単位に集約し、重複行を排除する:

```sql
SELECT
  did,
  MAX(name) AS name,
  MAX(nanoid) AS nanoid,
  MAX(execution_tier) AS tier
FROM graphar.vertex_actor_manifest
WHERE _alive = true
  AND status = 'active'
  AND name IS NOT NULL
  AND nanoid IS NOT NULL
GROUP BY did
ORDER BY name
LIMIT 200
```

### inspect (PDS actor.getManifest)
1. `SELECT did,name,nanoid,execution_tier,display_name,description,val ... ORDER BY timestamp_ms DESC LIMIT 1`
2. `val` があれば JSON decode して返す
3. 失敗時は typed columns で最小 `ActorManifest` を復元して返す

## Migration Strategy

1. 既存運用は `CREATE TABLE IF NOT EXISTS` だけでは列追加が反映されない。
2. 列追加は `ALTER TABLE ... ADD COLUMN` の migration を別途実行する。
3. migration 完了前でも read path は壊れないよう、optional 列を query 必須にしない。

## Related Rules
- `90-docs/rules/ts-cypher-p10v2-query-rules.md`

## Operational Rules

- `list` の正常条件: `name/nanoid/tier/did` が全て非 null。
- `inspect` の正常条件: full JSON (`val`) が返る。最低でも最小復元が返る。
- 404 (`ManifestNotFound`) は「該当 DID の active row 不在」のみで返す。
