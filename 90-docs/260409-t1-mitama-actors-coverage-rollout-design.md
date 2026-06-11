# T1 Mitama Actors Coverage Rollout Design

## Goal
`20-actors/*/actor-manifest.jsonld` (executionTier = `T1`) に共通 coverage pipeline を実装し、`etzhayyim mitama` で deploy 可能な状態に揃える。

## Scope
- Target: T1 actors under `20-actors/*/actor-manifest.jsonld`
- Runtime: PDS Shared Executor (no Worker deploy)
- Validation: `etzhayyim mitama --dry-run`

## Coverage Template (T1-safe)
T1 制約 (`custom` handler 禁止) に合わせ、以下 primitive のみを使用:
- `graph.query`
- `graph.write`

Per actor で追加する pipeline:
1. `cron` (`0 */6 * * *`)
- Query node count / latest timestamp (`repo = $did`)
- Query top collections (`repo = $did`)
- Write `ActorCoverageSnapshot`

2. `xrpc` (`com.etzhayyim.apps.<actor-segment>.coverage.get`)
- Query latest `ActorCoverageSnapshot`
- Query freshness rate (last 24h)

## Data Node
`ActorCoverageSnapshot`
- `actorDid`
- `actorName`
- `nanoid`
- `nodeCount`
- `latestTs`
- `topCollections`
- `timestamp_ms`
- `collection` (`com.etzhayyim.apps.<actor-segment>.coverageSnapshot`)

## Rollout Automation
Script:
- `70-tools/scripts/actors/add-t1-coverage-pipelines.mjs`

Usage:
- Dry run: `node 70-tools/scripts/actors/add-t1-coverage-pipelines.mjs`
- Apply: `node 70-tools/scripts/actors/add-t1-coverage-pipelines.mjs --apply`

Behavior:
- Scans `20-actors/*/actor-manifest.jsonld`
- Applies only `executionTier = "T1"`
- Skips manifests that already contain standard coverage pipeline (`.coverage.get` or `coverageSnapshot/coverageStats` step)

## Operational Verification
- JSON validity: parse all actor manifests
- Mitama validation: `etzhayyim mitama -dir <actor-dir> --dry-run`
- Coverage endpoint availability: check each manifest contains `.coverage.get` trigger

## Notes
- Existing domain/world coverage CLI remains unchanged (`etzhayyim coverage domain`, `etzhayyim coverage`)
- This rollout focuses on actor-local coverage visibility and snapshot continuity.
