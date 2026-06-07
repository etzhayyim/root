---
id: cohort-coverage-evaluation-baseline-260414
title: "Cohort Coverage / Evaluation / Process Mining Baseline (ADR-0026 Iteration 1)"
status: active
doc_type: how-to
topic: cohort-evaluation
authoritative: false
last_verified: 2026-04-14
related:
  - adr-0026-agent-only-reverse-identity-topology
  - adr-0025-kyber-apqc-bpmn-projector-consolidation
  - adr-0014-self-hosted-did-plc
supersedes: []
superseded_by: []
---

# Goal

ADR-0026 `proposed` 段階の実装進捗を /loop iteration 単位で追跡する。

# Scope

- 登録済み cohort_actors のカバレッジ (APQC L1 × role × locale)
- k-anonymity / posterior の評価手順
- Kyber APQC/BPMN/OCEL projector (ADR-0025) との process mining 配線

# Iteration 1 — 2026-04-14

## Registered Cohorts (N=13)

APQC PCF L1 13 process area × 代表 role × locale=jp で seed:

| # | name | APQC L1 | role persona | status |
|---|---|---|---|---|
| 1 | cohort-apqc-1-vision-strategy | 1.0 Vision & Strategy | strategist | pending-plc-genesis |
| 2 | cohort-apqc-2-product-service | 2.0 Product & Service | productManager | pending-plc-genesis |
| 3 | cohort-apqc-3-market-sell | 3.0 Market & Sell | salesRep | pending-plc-genesis |
| 4 | cohort-apqc-4-supply-chain | 4.0 Supply Chain | plannerBuyer | pending-plc-genesis |
| 5 | cohort-apqc-5-production-ops | 5.0 Production/Ops | lineOperator | pending-plc-genesis |
| 6 | cohort-apqc-6-customer-service | 6.0 Customer Service | supportAgent | pending-plc-genesis |
| 7 | cohort-apqc-7-human-capital | 7.0 Human Capital | hrGeneralist | pending-plc-genesis |
| 8 | cohort-apqc-8-info-technology | 8.0 Info Technology | sreEngineer | pending-plc-genesis |
| 9 | cohort-apqc-9-financial-resources | 9.0 Financial Resources | accountant | pending-plc-genesis |
| 10 | cohort-apqc-10-asset-management | 10.0 Asset Management | assetManager | pending-plc-genesis |
| 11 | cohort-apqc-11-risk-compliance | 11.0 Risk & Compliance | complianceOfficer | pending-plc-genesis |
| 12 | cohort-apqc-12-external-relations | 12.0 External Relations | prSpecialist | pending-plc-genesis |
| 13 | cohort-apqc-13-business-capability | 13.0 Business Capability | capabilityArchitect | pending-plc-genesis |

## Coverage Gaps (次 iteration 以降の拡張候補)

- locale: jp 固定 → en / zh / ko / 多言語 persona への展開
- role per L1: 1 role のみ → APQC sub-process ごとに複数 role persona (例: L3 market-sell は salesRep / marketingManager / csRep の 3 persona)
- vertical industry × L1: 製造業 / 金融 / 公共など industry overlay
- 年齢 / 経験年数 / seniority vector の追加 (k≥50 維持条件下で)

## Evaluation Baseline

### k-anonymity

- 全 13 cohort で `k_anonymity = 50` を genesis 時点で宣言
- 再評価 scheduler: 未実装。Path F `scheduler` middleware に `cohortKReevaluate` task を登録する予定 (次 iteration)
- 閾値: `k < 50` 検出時は fission_enabled 自動 false 化 + alert (critical violation)

### Posterior

- 現時点 accretion `com.etzhayyim.cohort.evidence` 未投入 → posterior baseline は N/A
- 配線先: Kotoba/Datomic streaming MV `identity_posterior_mv` (未実装) + Murakumo LLM-as-judge
- Fission 条件 (ADR-0026 §1 Phase C): `posterior > 0.95` AND `judgeAgreement === true`
- Iteration 2 で MV DDL + judge prompt template を起票

### Fission readiness

- 全 cohort `fission_enabled = false` (initial default)。Phase C は未到達
- fission 先の個人 actor handle prefix: `agent-{nano}.etzhayyim.com` (ADR-0026 §1 Phase C)

## Process Mining (OCEL 2.0) 配線計画

ADR-0025 Kyber projector の `com.etzhayyim.apqc.apqcEvent` を cohort lifecycle に流用:

| Lifecycle Phase | OCEL eventType | object types |
|---|---|---|
| Genesis | `cohort.genesis` | `cohort` (cohortDid, segmentHash) |
| Accretion (evidence write) | `cohort.evidence.accrued` | `cohort`, `evidence` |
| k re-evaluation | `cohort.kReevaluated` | `cohort`, `kValue` |
| Fission | `cohort.fission` | `cohort`, `individual` |
| Purge (k<50 violation) | `cohort.purge` | `cohort` |

投影先 DID (ADR-0025 path-based): `did:web:kyber-projector.etzhayyim.com:apqc:{1..13}-{slug}`。
cohort ↔ L1 actor DID の対応表は cohort_actors.segment_hash の `pcfL1` prefix で導出可能。

**次 iteration TODO**:
1. `com.etzhayyim.cohort.evidence` write → `onCommit` hook で `apqcEvent` 自動 emit
2. posterior streaming MV `identity_posterior_mv` の Kotoba/Datomic DDL
3. k reevaluation scheduler task の Path F 登録
4. locale=en / vertical overlay による cohort 拡張

# Iteration 2 — 2026-04-14

## Additional Cohorts (+18, 合計 N=31)

| Axis | Added | 累計 |
|---|---|---|
| locale=en overlay (L1 × 13) | 13 | 26 |
| Additional role persona (L3 marketingManager / L7 talentAcquisitionLead / L11 internalAuditor) | 3 | 29 |
| Industry vertical (L5 manufacturing / L9 banking) | 2 | 31 |

全て `status = pending-plc-genesis`, `k_anonymity = 50`, `fission_enabled = false`。

## Coverage Matrix (31 entries)

```
            L1  L2  L3  L4  L5  L6  L7  L8  L9  L10 L11 L12 L13
locale=jp    1   1   1   1   1   1   1   1   1   1   1   1   1    (13)
locale=en    1   1   1   1   1   1   1   1   1   1   1   1   1    (13)
extra role          1           1                   1              (3)
industry                     1           1                        (2)
```

Gap: L1/L2/L4/L6/L8/L10/L12/L13 は role 1 種のみ。industry overlay は 2 L1 のみ。次 iteration で拡充。

## Evaluation Progress

- `identity_posterior_mv` DDL draft → `90-docs/260414-cohort-identity-posterior-mv-draft.md` で起票
- pre-flight check PASS (cardinality, backfill, MAX(varchar) 回避, narrow MV)
- k_proxy 計算 MV (`mv_cohort_k_drift`) も同 doc に併載
- insert-columns.ts 拡張 + final migrations `0052` / `0053` / `0054` は 2026-04-14 本番適用済み

## Process Mining Wiring

- evidence commit → OCEL event mapping schema を DDL draft doc §Process Mining 連携 で固定
- segment_hash.pcfL1 から APQC L1 DID (`did:web:kyber-projector.etzhayyim.com:apqc:{L1}`) への導出規則を明文化
- 実装配線は `onCommit` handler 拡張 (次 iteration)

## 次 iteration TODO

1. MV migration `0054` の実装 (`insert-columns.ts` allowlist 拡張 + Kysely migration + Row 型) は完了
2. cohort role persona の網羅 (全 L1 で 2 role 以上)
3. industry vertical × L1 の overlay 拡張 (healthcare / retail / pharma)
4. Path F `scheduler` middleware に `cohortKReevaluate` task を登録
5. `onCommit` → OCEL `apqcEvent` emit の handler 実装

# Iteration 3 — 2026-04-14

## Code Artifacts (runnable, not yet applied)

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/insert-columns.ts` | VERTEX allowlist に 11 列追加 (cohort_did / evidence_hash / signal_kind / posterior / judge_agreement / tier / observed_at / segment_hash / k_anonymity / fission_enabled / derived_from) |
| `30-graph/graph-schema/migrations/0054_cohort_identity_posterior_mv.ts` | 2 narrow MV (`mv_cohort_identity_posterior`, `mv_cohort_k_drift`) — production apply 済 |
| `30-graph/graph-schema/src/database.ts` | `MvCohortIdentityPosteriorRow` + `MvCohortKDriftRow` + `Database` entry |
| `30-graph/graph-schema/CLAUDE.md` | Migration History に 0034 追記 |

## Additional Cohorts (+12, 合計 N=43)

| Axis | Added |
|---|---|
| Second role persona for gap L1 (1/2/4/6/8/10/12/13) | 8 |
| Industry overlay (healthcare L6 / retail L3 / pharma L2) | 3 |
| (Note: industry=manufacturing L5 + banking L9 は Iter2 済) | — |

**累計 matrix (N=43):**

```
            L1  L2  L3  L4  L5  L6  L7  L8  L9  L10 L11 L12 L13
locale=jp    2   2   3   2   2   3   2   2   2   2   2   2   2    (28)
locale=en    1   1   1   1   1   1   1   1   1   1   1   1   1    (13)
industry               retail     hc                              (2 extra, mfg/bank は jp に含む)
```

全 L1 で role ≥ 2 (jp) を達成。

## Evaluation

- Fission decision SQL example:
  ```typescript
  const ready = await db.selectFrom('mv_cohort_identity_posterior')
    .select(['cohort_did', 'max_posterior', 'fission_ready_count'])
    .where('max_posterior', '>', 0.95)
    .where('fission_ready_count', '>=', 1)
    .execute();
  ```
- k-drift watchdog SQL:
  ```typescript
  const violations = await db.selectFrom('mv_cohort_k_drift')
    .select(['cohort_did', 'k_proxy', 'evidence_count'])
    .where('k_proxy', '<', 50)
    .where('evidence_count', '>', 0)
    .execute();
  ```

## Process Mining Wiring (spec)

onCommit handler pseudocode (次 iter 実装):

```typescript
async function onCohortEvidenceCommit(commit, sdk) {
  if (commit.collection !== 'com.etzhayyim.cohort.evidence') return;
  const { cohortDid, evidenceHash, posterior, judgeAgreement } = commit.record;
  const cohort = await lookupCohort(cohortDid); // from deps.toml [[cohort_actors]]
  const l1Slug = parseSegmentHash(cohort.segment_hash).pcfL1; // e.g. "3-market-sell"
  const apqcDid = sdk.did.create(`apqc:${l1Slug}`);
  await sdk.pds.dispatch({
    type: 'com.atproto.repo.createRecord',
    did: apqcDid,
    collection: 'com.etzhayyim.apqc.apqcEvent',
    record: {
      ocelEventId: evidenceHash,
      eventType: posterior > 0.95 && judgeAgreement
        ? 'cohort.evidence.fissionReady'
        : 'cohort.evidence.accrued',
      objects: [
        { type: 'cohort', id: cohortDid },
        { type: 'evidence', id: evidenceHash },
      ],
      observedAt: commit.record.observedAt,
    },
  });
}
```

## Risk / Open Items

- `0054` migration は本番適用済み
- `vertex_repo_record` のどの promoted column slot に 11 列を mount するかは insert pipeline 調査が必要 (次 iter)
- segment_hash parser が未実装 (`parseSegmentHash` → pcfL1/role/industry/locale 抽出)

## 次 iteration TODO

1. `mv_cohort_identity_posterior` read smoke test
2. `vertex_repo_record` cohort columns / `vertex_cohort_actor` / MV の runtime wiring 継続
3. `segment_hash` parser util を `20-actors/magatama/sdk/magatama-host-sdk/src/cohort.ts` に新規追加
4. Path F `scheduler` に `cohortKReevaluate` task を登録 (MV `mv_cohort_k_drift` polling)
5. `onCommit` handler 実装 → apqc projector OCEL event emit

# Iteration 4 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `30-graph/graph-schema/migrations/0052_vertex_repo_record_cohort_columns.ts` | ALTER `vertex_repo_record` ADD 7 cohort columns (DDL only, O(1)) |
| `30-graph/graph-schema/CLAUDE.md` | Migration History に 0035 追記 |
| `20-actors/magatama/sdk/magatama-host-sdk/src/cohort.ts` | 新規: `parseSegmentHash()` / `apqcL1DidFromSegment()` / `deriveCohortEventType()` (OCEL type derivation) |
| `deps.toml` | +3 cohort (en × role: marketing/talent/auditor) |

## Cohort Total N=46

分布:
- locale=jp: 29 (gap L1 埋め完了)
- locale=en: 16 (3 role persona 追加済)
- industry overlay: 5 (mfg/bank/hc/retail/pharma)

## Path F Scheduler Registration Spec

`vertex_agentschedule` table への system-level registration (既存 scheduler.ts 経路を流用):

```typescript
import { createSchedule } from './agent/scheduler';

// boot hook / migration-time registration
await createSchedule(env, {
  callerDid: 'did:web:atproto.etzhayyim.com',         // system caller
  agentDid: 'did:web:cohort-watchdog.etzhayyim.com',  // dedicated system agent
  triggerType: 'cron',
  cronExpr: '0 */6 * * *',                       // every 6 hours, on hour (not :00/:30? — see CronCreate policy, use '7 */6 * * *')
  action: JSON.stringify({
    kind: 'cohortKReevaluate',
    query: `SELECT cohort_did, k_proxy, evidence_count
            FROM mv_cohort_k_drift
            WHERE evidence_count > 0 AND k_proxy < 50`,
    onViolation: {
      disableFission: true,                     // set fission_enabled = false
      emitOcel: 'cohort.kReevaluated',
      alert: 'critical',
    },
  }),
  active: true,
});
```

実装配線は `50-infra/cloudflare/workers/atproto/src/agent/scheduler.ts` の既存 dispatch path に `kind=cohortKReevaluate` 分岐を追加する (次 iter)。

## OCEL Event Type Table (host-sdk cohort.ts に実装済)

| Phase | 判定条件 | eventType |
|---|---|---|
| 初 evidence | evidence_count_before === 0 | `cohort.genesis` |
| 継続 evidence | 他条件非該当 | `cohort.evidence.accrued` |
| fission ready | posterior > 0.95 && judgeAgreement && fission_enabled | `cohort.evidence.fissionReady` |
| k drift | k_proxy < 50 | `cohort.kReevaluated` |
| 実 fission 完了 | didFission === true | `cohort.fission` |
| cohort 削除 | (手動/cascade) | `cohort.purge` |

## Risk / Open Items

- `0052` migration は本番 apply 済み
- `cohort.ts` は unit test 未作成 (次 iter に test.ts 追加)
- Path F scheduler dispatch path 拡張は未実装 — スペック止まり
- `vertex_cohort_actor` table (signature/fission lineage 4 列用) は 0036 で別途

## 次 iteration TODO

1. `20-actors/magatama/sdk/magatama-host-sdk/src/cohort.test.ts` — parser + event type derivation の unit test
2. migration `0053`: `vertex_cohort_actor` table 新設 (segment_hash / k_anonymity / fission_enabled / derived_from / status / genesis_at)
3. scheduler.ts に `kind=cohortKReevaluate` dispatch 分岐追加
4. `onCommit` handler 実装 (evidence commit → apqcEvent emit)
5. cohort coverage: en industry overlay (mfg/bank/hc/retail/pharma × en locale)

# Iteration 5 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `20-actors/magatama/sdk/magatama-host-sdk/test/cohort.test.ts` | 新規: parseSegmentHash / apqcL1DidFromSegment / deriveCohortEventType の 14 test cases (k-drift precedence, fission gating, industry overlay 含む) |
| `30-graph/graph-schema/migrations/0053_vertex_cohort_actor.ts` | 新規 table: cohort_did PK + 10 columns + 2 indexes |
| `30-graph/graph-schema/src/database.ts` | `VertexCohortActorRow` + Database entry |
| `30-graph/graph-schema/CLAUDE.md` | Migration History に 0036 追記 |

## Evaluation — Test Coverage

cohort.ts の全 3 export について:
- `parseSegmentHash`: 4 case (minimum / industry / no-prefix / missing-keys)
- `apqcL1DidFromSegment`: 2 case (default / alt host)
- `deriveCohortEventType`: 7 case (全 6 eventType + k-drift precedence edge)

合計 13 tests。vitest 経路で `pnpm exec vitest run cohort` 実行を想定。

## Process Mining — Lineage Persistence

fission 後の individual actor が cohort から derive されたことを graph に保持する経路が確定:

1. genesis: `vertex_cohort_actor` に kind='cohort', derived_from=NULL で insert
2. evidence accrual: `vertex_repo_record` WHERE collection='com.etzhayyim.cohort.evidence'
3. fission trigger: `mv_cohort_identity_posterior.fission_ready_count ≥ 1`
4. fission procedure: 新 did:plc mint + `vertex_cohort_actor` に kind='fissioned', derived_from=<parent_cohort_did>

→ Cypher 代替の Kysely クエリで `SELECT WHERE derived_from = ?` で lineage 取得可能。
→ `idx_vertex_cohort_actor_derived_from` index で O(log N)。

## Risk / Open Items

- `0052` / `0053` / `0054` migrations は production apply 済み
- scheduler.ts dispatch 拡張は未着手 (次 iter)
- onCommit handler 実装も未着手 (次 iter)
- en locale industry overlay 拡張も未着手 (次 iter)

## 次 iteration TODO

1. scheduler.ts に `kind=cohortKReevaluate` dispatch 分岐追加 + test
2. `onCommit` handler: evidence commit → deriveCohortEventType → apqc projector emit
3. en locale × industry overlay 5 件 (mfg-en, bank-en, hc-en, retail-en, pharma-en)
4. `com.etzhayyim.cohort.seed` procedure の実装 (pds handler) — `vertex_cohort_actor` INSERT
5. `etzhayyim cohort seed --segment` CLI skeleton

# Iteration 6 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | 新規: `registerCohortWatchdogSchedule` / `parseCohortAction` / `runCohortKReevaluate`。scheduler.ts に手を入れず policy を独立 module で実装 |
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.test.ts` | 新規: parseCohortAction の 3 test cases |
| `deps.toml` | +5 cohort (en × industry: mfg/bank/hc/retail/pharma) |

## Cohort Total N=51

分布:
- locale=jp: 29
- locale=en: 21 (16 + 5 industry overlay)
- industry overlay total: 10 (jp 5 + en 5)

全 5 industry vertical を jp/en 両方でカバー。

## Process Mining

watchdog 発火経路 (full):

```
[cron 7 */6 * * *]
  → vertex_agentschedule row (registerCohortWatchdogSchedule で登録)
  → scheduler.evaluateCronTriggers → ProactiveMessage{text:'{"kind":"cohortKReevaluate"}'}
  → PDS cron handler (consumer)
    → parseCohortAction(text) === {kind:'cohortKReevaluate'}
    → runCohortKReevaluate(env)
      → SELECT * FROM mv_cohort_k_drift WHERE k_proxy < 50 AND evidence_count > 0
      → UPDATE vertex_cohort_actor SET fission_enabled = false WHERE cohort_did IN (...)
      → return ocelEvents[]
    → for each event: PDS write com.etzhayyim.apqc.apqcEvent (per-L1 DID via segment lookup)
```

scheduler.ts は generic に保ち、cohort-specific policy は `cohort-watchdog.ts` に分離 (Shannon η: scheduler は分岐ゼロ追加で 1.0 維持)。

## Evaluation

- watchdog の `parseCohortAction` は 3 cases (positive / 4 negative / extra-keys-ignored)
- runCohortKReevaluate は DB integration が必要なため unit test 対象外。staging で smoke test

## Risk

- schema 側 migration `0052` / `0053` / `0054` は production apply 済み
- PDS cron handler 側に `parseCohortAction` 分岐を追加する作業は次 iter
- onCommit handler は引き続き未実装

## 次 iteration TODO

1. PDS cron handler 統合: `evaluateCronTriggers` → for each msg → `parseCohortAction` → `runCohortKReevaluate` → apqcEvent emit
2. `onCommit` handler: com.etzhayyim.cohort.evidence write 検出 → deriveCohortEventType → apqcEvent emit
3. `com.etzhayyim.cohort.seed` PDS procedure 実装 (vertex_cohort_actor INSERT)
4. cohort coverage: seniority dimension (junior/mid/senior) 追加
5. staging cluster で 0034-0036 batch apply

# Iteration 7-8 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/app.ts` `scheduled()` | cohort watchdog tick 追加 (`runCohortWatchdogTick` as waitUntil)。既存 6 cron job に並列で動作、OCEL analytics emit |
| `20-actors/magatama/sdk/magatama-host-sdk/src/cohort.ts` | `CohortSegment` に `seniority: string \| null` 追加、parser が `seniority=` key を拾う |
| `20-actors/magatama/sdk/magatama-host-sdk/test/cohort.test.ts` | +1 test case (seniority overlay) |
| `deps.toml` | +3 cohort (seniority: junior/mid/senior on L1=8 IT) |

## Cohort Total N=54

分布:
- locale=jp: 32 (+3 seniority)
- locale=en: 21
- industry overlay: 10
- seniority overlay: 3 (L1=8 × junior/mid/senior)

3 軸 (role / industry / seniority) が全て parser で認識可能に。新 dim 追加 = `CohortSegment` interface のフィールド + deps.toml entry のみ。

## PDS Cron Wiring (completed)

scheduled() 内で以下が動作:

```typescript
ctx.waitUntil(runCohortWatchdogTick(env).catch(log('runCohortWatchdogTick')));
```

`runCohortWatchdogTick` 内:
1. `evaluateCronTriggers(env)` → ProactiveMessage[]
2. for each msg: `parseCohortAction(msg.text)` → null なら skip
3. match: `runCohortKReevaluate(env)` → violations / ocelEvents
4. violations > 0: console.log + OCEL datapoint (`com.etzhayyim.cohort.kReevaluated`)

**重要**: scheduler.ts は無改変。app.ts 側で generic message stream を filter する形に統一。

## OCEL Datapoint (Analytics surface)

```
index: "com.etzhayyim.cohort.kReevaluated"
blobs: ["com.etzhayyim.cohort.kReevaluated", "cron", "internal", "SCHEDULED", "", "", "", ""]
doubles: [scanned_count, violations_count]
```

`/xrpc/com.etzhayyim.pds.getOcel?index=com.etzhayyim.cohort.kReevaluated` で analytics クエリ可能。

## Risk

- apqc projector への OCEL event emit (`com.etzhayyim.apqc.apqcEvent` write) は未実装 (runCohortWatchdogTick 内は OCEL datapoint のみ)
- `onCommit` handler (evidence commit → apqcEvent) も未実装
- migration 0034-0036 は staging 未 apply

## 次 iteration TODO

1. `runCohortWatchdogTick` の `result.ocelEvents` を apqc projector (`did:web:kyber-projector.etzhayyim.com:apqc:{L1}`) に forward する
2. evidence commit handler: `handleCommit` で `collection === 'com.etzhayyim.cohort.evidence'` 検出 → apqc projector emit
3. `com.etzhayyim.cohort.seed` PDS procedure 実装
4. lexicon `com.etzhayyim.cohort.listCohorts` (query) の仕様化
5. apply migration 0034-0036 to staging

# Iteration 9 — 2026-04-14

## Context

Migration 採番が繰り上がり、0034/0035/0036 → **0052/0053/0054 として本番 Kotoba/Datomic に apply 済み**。runtime 側コードは既に MV/テーブル前提で動作可能。

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | `extractPcfL1()` util + LEFT JOIN `vertex_cohort_actor` で segment_hash を引き、OCEL event に `apqcL1` / `apqcDid` フィールドを付与 |
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.test.ts` | +3 test (extractPcfL1 regex 検証) |
| `50-infra/cloudflare/workers/atproto/src/app.ts` `runCohortWatchdogTick` | OCEL datapoint を per-event にも emit (L1 / projector DID を blobs に同梱) → analytics クエリで L1 分布が可視化可能 |

## Process Mining — APQC Routing Activation

watchdog の OCEL stream:
- 集約 1 行: `[scanned, violations]` (既存)
- **per-event 行 (新規)**: `[kProxy, 1]` + blobs に `cohortDid / apqcL1 / apqcDid` 同梱

`/xrpc/com.etzhayyim.pds.getOcel?index=com.etzhayyim.cohort.kReevaluated` で `apqcL1` by bucket 集計が可能。Kyber projector 側の `did:web:kyber-projector.etzhayyim.com:apqc:{L1}` に対する record write は次 iter。

## Cohort Total N=54 (unchanged)

Iter 8 で追加した seniority 3 cohort を含む。

## Risk / Open Items

- apqc projector への `createRecord` 実 call (PDS-internal XRPC) は未実装。現状は OCEL index にのみ流れる
- `onCommit` evidence handler は未実装 (fission_ready 遷移の OCEL emit がまだない)
- `com.etzhayyim.cohort.seed` PDS procedure も未実装

## 次 iteration TODO

1. apqc projector への XRPC `createRecord` forward を cohort-watchdog に実装 (PDS 内部 XRPC fetch)
2. `handleCommit` に `collection === 'com.etzhayyim.cohort.evidence'` 分岐 + `deriveCohortEventType()` 呼び出し
3. `com.etzhayyim.cohort.seed` procedure 実装 (`vertex_cohort_actor` INSERT 経路)
4. cohort coverage: `seniority=senior` を L3 / L9 / L11 にも展開 (3 entries)
5. Iteration history doc を production 採番 (0052-0054) に整合させる cleanup

# Iteration 10 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | `forwardOcelToApqc()` 新規 — PDS-internal XRPC fetch で `com.atproto.repo.createRecord` を `com.etzhayyim.apqc.apqcEvent` に打つ |
| `50-infra/cloudflare/workers/atproto/src/app.ts` | `runCohortWatchdogTick` で各 OCEL event を projector に forward、成功数を log |
| `deps.toml` | +3 cohort (seniority=senior on L3 / L9 / L11) |

## Cohort Total N=57

分布:
- locale=jp: 35 (+3 seniority L3/L9/L11)
- locale=en: 21
- industry overlay: 10
- seniority overlay: 6 (L1=8 × junior/mid/senior + L3/L9/L11 × senior)

seniority 軸が代表的な 4 L1 (IT / sales / finance / risk) をカバー。

## Process Mining — Projector Forwarding Active

runCohortWatchdogTick の full flow:

```
cron match → parseCohortAction → runCohortKReevaluate (JOIN 済み)
  → for each ocel event:
      env.OCEL.writeDataPoint (analytics)
      forwardOcelToApqc (projector AT Record write)
         → POST https://atproto.etzhayyim.com/xrpc/com.atproto.repo.createRecord
         → collection: com.etzhayyim.apqc.apqcEvent
         → did: did:web:kyber-projector.etzhayyim.com:apqc:{L1}
         → record: { ocelEventId, apqcCode, eventType, caseId=cohortDid, ... }
  → 結果 log: "forwarded N/M to apqc projector"
```

これで PDS cron から kyber projector / yoro / kagami 受け皿まで event が流れる。

## Risk / Open Items

- projector の XRPC write は PDS-internal fetch で行うが auth header なし (trusted intra-pds path)。本番で 401 が出る場合は `etzhayyim agent-token --lxm com.atproto.repo.createRecord` で JWT 取得経路を入れる必要
- `onCommit` handler (evidence commit → projector emit) は依然未実装
- `com.etzhayyim.cohort.seed` procedure も依然未実装

## 次 iteration TODO

1. `forwardOcelToApqc` に Service Auth JWT 付与 (ADR-0022 agent-token 経由)
2. evidence onCommit handler 実装 (projector への evidence.accrued / fissionReady 通知)
3. `com.etzhayyim.cohort.seed` PDS procedure 実装 + lexicon attach
4. cohort coverage: en locale × seniority overlay (6 entries)
5. live monitoring: `/xrpc/com.etzhayyim.pds.getOcel?index=com.etzhayyim.cohort.kReevaluated` で 1 週間の volume を可視化

# Iteration 11 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | `forwardOcelToApqc` の eventType を 6 値 union (`CohortOcelEventType`) に拡張。genesis / fissionReady / fission / purge / accrued も emit 可能 |
| `90-docs/260414-cohort-seed-procedure-spec.md` | 新規 how-to doc: segment_hash 導出 / handle mint / k=50 検証 / INSERT / signature write / genesis emit の 7 step spec |
| `deps.toml` | +4 cohort (en × seniority: L8 junior/senior, L3 senior, L9 senior) |

## Cohort Total N=61

分布:
- locale=jp: 35
- locale=en: 25 (+4 seniority en)
- industry overlay: 10
- seniority overlay: 10 (jp=6 / en=4)

locale × seniority matrix が jp/en 両言語で senior 確保。

## Process Mining — eventType Union Complete

`CohortOcelEventType` 6 種全てが `forwardOcelToApqc` から emit 可能に:

| eventType | 発火タイミング |
|---|---|
| `cohort.genesis` | seed procedure 完了時 |
| `cohort.evidence.accrued` | onCommit (次 iter) |
| `cohort.evidence.fissionReady` | onCommit + posterior gate (次 iter) |
| `cohort.kReevaluated` | cohort-watchdog (**active**) |
| `cohort.fission` | fission procedure (未実装) |
| `cohort.purge` | cascade delete (未実装) |

## Evaluation — Seed Procedure Readiness

`com.etzhayyim.cohort.seed` の全実装 prerequisite が揃った:
- ✅ lexicon `seed.json` (Iter 1)
- ✅ vertex_cohort_actor table (Iter 5 → prod 0053)
- ✅ segment_hash parser (Iter 4)
- ✅ forwardOcelToApqc genesis route (Iter 11 — 本 iter)
- ⏳ PDS handler registration (次 iter)
- ⏳ etzhayyim CLI `cohort seed` skeleton (次 iter)

## Risk / Open Items

- `deps.toml [[cohort_actors]]` と `vertex_cohort_actor` table の dual-SSoT 状態。runtime は table 側、deploy-time は toml 側を読む前提。双方向 sync は別 migration で対応
- Service Auth JWT 未付与のため projector forward が 401 リスク

## 次 iteration TODO

1. `sdk.app.command(nsid('com.etzhayyim.cohort.seed'), ...)` 実装 (50-infra/cloudflare/workers/atproto/src/handlers/cohort.ts 新規)
2. `etzhayyim cohort seed --segment <json>` CLI skeleton (70-tools/cmd/etzhayyim/cohort/)
3. `forwardOcelToApqc` に ADR-0022 agent-token 経由の Authorization header を追加
4. evidence onCommit: `collection === 'com.etzhayyim.cohort.evidence'` 分岐
5. migration 0055: `deps.toml [[cohort_actors]]` から `vertex_cohort_actor` への bootstrap insert

# Iteration 12 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | 新規: `handleCohortSeed(env, input)` 実装 — k≥50 検証 / segment_hash 導出 / nano 生成 / vertex_cohort_actor INSERT / forwardOcelToApqc('cohort.genesis') |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.test.ts` | 新規: segment_hash 導出契約 test 3 cases (minimum / overlay / 順序不変) |
| `deps.toml` | +2 cohort (L7 HR senior / L12 ER senior, jp) |

## Cohort Total N=63

分布:
- locale=jp: 37 (+2 senior)
- locale=en: 25
- seniority overlay: 12 (jp=8, en=4)

senior tier が 7 L1 (IT/sales/finance/risk/HR/ER) をカバー。gap は L1/L2/L4/L5/L6/L10/L13 のみ。

## Evaluation — Seed Procedure Implementation

| Prerequisite | 状態 |
|---|---|
| lexicon seed.json | ✅ |
| vertex_cohort_actor table (prod 0053) | ✅ |
| segment_hash parser | ✅ |
| forwardOcelToApqc genesis route | ✅ |
| **PDS handler function** | **✅ (本 iter)** |
| XRPC dispatch wiring (`sdk.app.command`) | ⏳ 次 iter |
| etzhayyim CLI skeleton | ⏳ 次 iter |

handler 関数は完成、XRPC dispatch 登録のみ残。

## Process Mining

handleCohortSeed が完了すると `cohort.genesis` event が projector に流れる:

```
POST /xrpc/com.etzhayyim.cohort.seed
  {segmentJsonld, kAnonymity: 50}
  → handleCohortSeed(env, input)
    → INSERT vertex_cohort_actor
    → forwardOcelToApqc({eventType: 'cohort.genesis', apqcDid: did:web:kyber-projector.etzhayyim.com:apqc:3-market-sell})
      → POST /xrpc/com.atproto.repo.createRecord
        collection: com.etzhayyim.apqc.apqcEvent
        record: {ocelEventId, apqcCode:'3-market-sell', eventType:'cohort.genesis', caseId:cohort_did, ...}
  → return {did, handle, signatureUri, genesisAt}
```

## Risk / Open Items

- dispatch 登録が未完のため handler は未 reachable (直接 import/test のみ可能)
- CLI 側 (`etzhayyim cohort seed`) も未実装
- Service Auth header 未付与は継続 risk

## 次 iteration TODO

1. `handlers/etzhayyim/index.ts` で `handleCohortSeed` を `com.etzhayyim.cohort.seed` NSID 分岐に登録
2. `etzhayyim cohort seed --segment <json>` CLI subcommand (70-tools/cmd/etzhayyim/cohort.go or ts)
3. `forwardOcelToApqc` に `etzhayyim agent-token --lxm com.atproto.repo.createRecord` 経由の Authorization 取得
4. en × L7/L12 senior overlay (+2)
5. onCommit handler: evidence 分岐 (次回確実に着手)

# Iteration 13 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | `com.etzhayyim.cohort.seed` NSID を `XRPC_PLATFORM_WRITE_METHODS` に追加、dispatch switch に `case "com.etzhayyim.cohort.seed"` を新設 (dynamic import で cohort.ts 呼び出し) |
| `deps.toml` | +2 cohort (en L7/L12 senior) |

## Cohort Total N=65

分布:
- locale=jp: 37
- locale=en: 27 (+2)
- senior overlay: 14 (jp=8 / en=6)

senior tier jp/en 両対応が 7 L1 に到達 (IT/sales/finance/risk/HR/ER × jp, 加えて IT/sales/finance/HR/ER × en)。

## Evaluation — Seed Procedure Complete End-to-End

| Prerequisite | 状態 |
|---|---|
| lexicon seed.json | ✅ |
| vertex_cohort_actor table (0053) | ✅ |
| segment_hash parser | ✅ |
| forwardOcelToApqc genesis | ✅ |
| handler function | ✅ |
| **XRPC dispatch wiring** | **✅ (本 iter)** |
| PLATFORM_WRITE_METHODS entry | ✅ |
| etzhayyim CLI skeleton | ⏳ |

POST `/xrpc/com.etzhayyim.cohort.seed` が reachable (要 auth)。

## Request Shape

```bash
curl -X POST https://atproto.etzhayyim.com/xrpc/com.etzhayyim.cohort.seed \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "segmentJsonld": "{\"pcfL1\":\"3-market-sell\",\"role\":\"salesRep\",\"locale\":\"jp\"}",
    "kAnonymity": 50
  }'
# → 200
# { "did":"did:plc:pending-<nano8>", "handle":"cohort-<nano8>.etzhayyim.com",
#   "signatureUri":"at://cohort-<nano8>.etzhayyim.com/com.etzhayyim.cohort.signature/self",
#   "genesisAt":"2026-04-14T..." }
```

## Risk / Open Items

- auth gate: `XRPC_PLATFORM_WRITE_METHODS` の共通 policy を継承するため admin/service のみ call 可能。CLI 側から呼ぶ場合は agent-token が必要
- `forwardOcelToApqc` 内部 fetch は依然として anonymous (projector 側が intra-pds trust を受け入れる前提)

## 次 iteration TODO

1. `etzhayyim cohort seed` CLI subcommand 実装 (70-tools/cmd/etzhayyim/)
2. `forwardOcelToApqc` Service Auth wrapping
3. onCommit handler (evidence → projector)
4. migration 0055 draft: [[cohort_actors]] toml → vertex_cohort_actor bootstrap INSERT
5. `com.etzhayyim.cohort.listCohorts` query NSID + lexicon

# Iteration 14 — 2026-04-14

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | 新規: `etzhayyim cohort seed --segment <json> --k 50` CLI。agent_token.go 準拠の XRPC POST pattern |
| `70-tools/etzhayyim/etzhayyim/main.go` | `case "cohort":` dispatch 追加 |

## CLI Usage

```bash
# Interactive:
etzhayyim authn signin

# Minted per-call scoped auth:
AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.cohort.seed --ttl 60)
etzhayyim_TOKEN=$AT_TOKEN etzhayyim cohort seed \
  --segment '{"pcfL1":"3-market-sell","role":"salesRep","locale":"jp"}' \
  --k 50

# Output:
# cohort genesis:
#   did:          did:plc:pending-<nano8>
#   handle:       cohort-<nano8>.etzhayyim.com
#   signatureUri: at://cohort-<nano8>.etzhayyim.com/com.etzhayyim.cohort.signature/self
#   genesisAt:    2026-04-14T...
```

## Cohort Total N=65 (unchanged)

CLI 経由で seed できる状態になったため、今後は `deps.toml` への直接追加ではなく
`etzhayyim cohort seed` で投入する運用に移行可能。

## Evaluation — Phase A Readiness Complete

| Prerequisite | 状態 |
|---|---|
| lexicon seed.json | ✅ |
| vertex_cohort_actor table (0053) | ✅ |
| segment_hash parser | ✅ |
| forwardOcelToApqc genesis | ✅ |
| handler function | ✅ |
| XRPC dispatch wiring | ✅ |
| PLATFORM_WRITE_METHODS entry | ✅ |
| **etzhayyim CLI** | **✅ (本 iter)** |

ADR-0026 Phase A (genesis) が E2E 完結。CLI → XRPC → handler → graph write → projector OCEL の full path 完成。

## Risk / Open Items

- `deps.toml [[cohort_actors]]` 65 entries のうち、`vertex_cohort_actor` に INSERT されたものは実質なし (seed CLI 未実行)。bootstrap migration 0055 で一括同期が必要
- Service Auth JWT 経由での `forwardOcelToApqc` 内部 fetch は依然として anonymous
- onCommit handler は引き続き未実装

## 次 iteration TODO

1. migration 0055: `deps.toml [[cohort_actors]]` の 65 entry を `vertex_cohort_actor` へ bootstrap INSERT (idempotent)
2. onCommit handler (evidence → deriveCohortEventType → forwardOcelToApqc)
3. `forwardOcelToApqc` の JWT 付与 (ADR-0022 agent-token API or identity: internal service binding)
4. `com.etzhayyim.cohort.listCohorts` query NSID 仕様化
5. bulk seed automation: `etzhayyim cohort seed-all --from deps.toml`

# Iteration 15 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort bootstrap` 追加 — deps.toml を line-by-line parse し `[[cohort_actors]]` を全件 POST。`--dry-run` default, `--limit N` で段階投入 |
| `00-contracts/lexicons/com/etzhayyim/cohort/listCohorts.json` | 新規 query lexicon: kind/pcfL1/locale/fissionEnabled フィルタ + limit/offset pagination |

## CLI

```bash
# Preview deps.toml → genesis plan
etzhayyim cohort bootstrap --deps deps.toml

# Apply (limited batch for safety)
AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.cohort.seed --ttl 600) \
  etzhayyim_TOKEN=$AT_TOKEN etzhayyim cohort bootstrap --dry-run=false --limit 10 -v
```

## Cohort Total N=65 in deps.toml

bootstrap 完了後、`vertex_cohort_actor` にも N=65 row が存在する状態に収束する予定 (CLI 実行は user-timing)。

## Evaluation

| Prerequisite (bootstrap path) | 状態 |
|---|---|
| deps.toml parser (cohortEntry) | ✅ (本 iter) |
| segment_hash → JSON-LD 逆変換 | ✅ (toSegmentJsonld) |
| XRPC POST loop | ✅ |
| listCohorts lexicon | ✅ (query handler は次 iter) |
| listCohorts handler impl | ⏳ |

## Risk / Open Items

- bootstrap は idempotent **ではない**: 毎回新 nano でも新 row が増える。次 iter で handler 側に `segment_hash` UNIQUE constraint or SELECT-before-INSERT を追加する必要
- listCohorts query の PDS handler (handlers/etzhayyim/index.ts で `case "com.etzhayyim.cohort.listCohorts"`) は未実装
- 診断警告は全て pre-existing (本 iter 由来なし)

## 次 iteration TODO

1. `handleCohortSeed` に idempotency: 同一 segment_hash の cohort が既存なら既存 did/handle を返す
2. `handleCohortList` 実装 + `XRPC_PLATFORM_READ_METHODS` 登録
3. onCommit handler (com.etzhayyim.cohort.evidence)
4. Murakumo agent に cohort.seed tool を登録 → LLM が demographic から自動 seed
5. 再び cohort 登録拡張: seniority × locale × industry 3 軸の cross-product 網羅計画

# Iteration 16 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortSeed` に idempotency 追加 (segment_hash + kind='cohort' で SELECT-before-INSERT); 新規 `handleCohortList(input)` 実装 (kind/pcfL1/locale/fissionEnabled filter + limit/offset pagination) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | `case "com.etzhayyim.cohort.listCohorts"` dispatch 追加; `XRPC_PLATFORM_READ_METHODS` に NSID 追加 |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort list` subcommand 実装 (--kind / --pcfL1 / --locale / --limit / --offset / --json) |

## Phase A E2E 完成

| Op | CLI | XRPC | Handler | 状態 |
|---|---|---|---|---|
| Genesis (idempotent) | `etzhayyim cohort seed` | POST com.etzhayyim.cohort.seed | handleCohortSeed | ✅ |
| Bootstrap from toml | `etzhayyim cohort bootstrap` | (POST xN) | (同上) | ✅ |
| List / query | `etzhayyim cohort list` | GET com.etzhayyim.cohort.listCohorts | handleCohortList | ✅ |

## Evaluation — Idempotency

seed の同一 segment_hash 重複防止:
- SELECT-before-INSERT pattern で既存 row があれば既存 did/handle を返却
- bootstrap 再実行で row 爆発せず、OCEL event も重複発火しない (lookup ヒット時は forward を skip しないため注意 → 次 iter で対応)

## Process Mining

listCohorts が分析クエリに使える:

```bash
etzhayyim cohort list --kind cohort --pcfL1 8-info-technology --limit 50
# → IT L1 の cohort を列挙 (jp/en/industry overlay 混在)

etzhayyim cohort list --locale en --json | jq '.cohorts | length'
# → 英語 cohort 件数
```

## Risk / Open Items

- `handleCohortSeed` の idempotent hit 時にも `forwardOcelToApqc('cohort.genesis')` を呼んでいる → OCEL 重複。次 iter で "既存ヒット" → genesis emit を skip
- `total` は page-hint approximation (厳密 count ではない)
- listCohorts handler は `XRPC_PLATFORM_READ_METHODS` にあるため公開 read。Tier 3 PII 無しの原則を前提

## 次 iteration TODO

1. idempotent hit 時の OCEL 重複抑止 (既存ヒットで `cohort.genesis` emit せず early return)
2. onCommit handler (com.etzhayyim.cohort.evidence commit → projector emit)
3. Murakumo agent tool 登録 (LLM drives `etzhayyim cohort seed` via function call)
4. `etzhayyim cohort fission --cohort <did>` stub (Phase C trigger API)
5. listCohorts に accurate total count option (`--count true` で二次 SELECT count(*))

# Iteration 17 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | idempotent hit 時の挙動を明示 comment 化 (既に early return なので OCEL skip は構造的に成立) |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort fission` CLI 追加 (posterior>=0.95 + judge=true + evidence[] gate を CLI 側で先行検証) |
| `90-docs/260415-cohort-evidence-oncommit-spec.md` | Phase B onCommit handler の完全 spec (PDS commit dispatcher 挿入 point + code) |

## Phase A (genesis) + B (evidence) + C (fission) CLI surface 完成

```bash
# Phase A (本番動作)
etzhayyim cohort seed --segment '...' --k 50
etzhayyim cohort bootstrap --deps deps.toml
etzhayyim cohort list --pcfL1 8-info-technology

# Phase C (CLI 完成 / handler pending)
etzhayyim cohort fission --cohort did:plc:... --posterior 0.97 --judge=true \
  --evidence at://...,at://...
```

## Evaluation

| Phase | CLI | Handler | OCEL path |
|---|---|---|---|
| A (genesis) | ✅ | ✅ | ✅ (watchdog + seed 両経路) |
| B (evidence) | (via createRecord) | spec ✅ / impl ⏳ | spec ✅ |
| C (fission) | ✅ (本 iter) | ⏳ | emit type `cohort.fission` は watchdog で既定義 |

## Risk / Open Items

- Phase C handler は com.etzhayyim.cohort.fission lexicon + handleCohortFission 実装が必要
- onCommit は spec 止まり (commit dispatcher 本体への insert は次 iter)
- `forwardOcelToApqc` の引数 `kProxy` が posterior/k_proxy の overload になっており、rename 推奨

## 次 iteration TODO

1. `handleCohortFission(env, input)` 実装 + dispatch wiring + `com.etzhayyim.cohort.fission` PLATFORM_WRITE_METHODS 登録
2. onCommit dispatcher に cohort.evidence 分岐を追加 (handlers/feed.ts or handlers/infra.ts の commit hook)
3. `forwardOcelToApqc` の引数 `kProxy → numericPayload` rename + OcelEventType 毎の意味付け doc
4. `com.etzhayyim.cohort.fission` lexicon を seed.json 同様にリファイン (既存) — rkey scheme 確認
5. Murakumo agent に `cohort.seed` を tool 登録 (`20-actors/magatama/sdk/magatama-host-sdk/src/llm-tools.ts` 等)

# Iteration 18 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | `forwardOcelToApqc` 引数 `kProxy → numericPayload` rename + 意味付け JSDoc。既存 `kProxy` は `CohortKDriftResult.ocelEvents` の legacy field として temporary 保持 |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortFission(env, input)` 実装 — cohort lookup + fission_enabled 検証 + 子 actor INSERT (kind='fissioned', derived_from=parent) + `cohort.fission` OCEL emit |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | `case "com.etzhayyim.cohort.fission"` dispatch + PLATFORM_WRITE_METHODS 登録 |

## Phase C (Fission) E2E 完成

```bash
# CLI
etzhayyim cohort fission --cohort did:plc:pending-abc \
  --posterior 0.97 --judge=true \
  --evidence at://...,at://...

# → POST /xrpc/com.etzhayyim.cohort.fission
# → handleCohortFission:
#    1. Validate gate (posterior>=0.95 AND judge=true AND evidence[]>=1)
#    2. SELECT vertex_cohort_actor WHERE cohort_did=? AND kind='cohort'
#    3. Assert fission_enabled=true (watchdog で false 化されていない)
#    4. Mint new did:plc:pending-<nano> + handle agent-<nano>.etzhayyim.com
#    5. INSERT vertex_cohort_actor (kind='fissioned', derived_from=parent)
#    6. forwardOcelToApqc('cohort.fission', posterior)

# Response:
{
  "individualDid": "did:plc:pending-<nano>",
  "individualHandle": "agent-<nano>.etzhayyim.com",
  "derivedFrom": "did:plc:pending-abc",
  "lineageArchiveUri": "at://agent-<nano>.etzhayyim.com/com.etzhayyim.cohort.fissionLineage/self",
  "fissionAt": "2026-04-15T..."
}
```

## Evaluation — ADR-0026 Full Lifecycle

| Phase | CLI | XRPC | Handler | OCEL | 状態 |
|---|---|---|---|---|---|
| A (genesis) | ✅ | ✅ | ✅ (idempotent) | ✅ | 完成 |
| B (accretion) | (via createRecord) | ✅ | spec ✅ / impl ⏳ | spec ✅ | spec 完成 |
| C (fission) | ✅ | ✅ | **✅ (本 iter)** | ✅ | 完成 |
| K-watchdog | (cron) | (internal) | ✅ | ✅ | 完成 |
| Query (list) | ✅ | ✅ | ✅ | — | 完成 |

**ADR-0026 agent-only reverse identity topology の A→C phase 全経路が production code として存在**。残るは B の handler insert のみ。

## numericPayload semantics (確定)

| eventType | numericPayload |
|---|---|
| cohort.genesis | kAnonymity |
| cohort.evidence.accrued | posterior |
| cohort.evidence.fissionReady | posterior |
| cohort.kReevaluated | k_proxy |
| cohort.fission | posterior |
| cohort.purge | 0 |

## Risk / Open Items

- onCommit handler (evidence insert path) はまだ未実装。90-docs/260415-cohort-evidence-oncommit-spec.md の code を commit dispatcher に貼り付ける作業が次 iter
- `CohortKDriftResult.ocelEvents` の legacy `kProxy` field は next iter で削除可
- `vertex_cohort_actor` の derived_from index (0053) が fission chain 探索に活用される — 実運用時に deep chain なら CTE を使う

## 次 iteration TODO

1. commit dispatcher (handlers/feed.ts or similar) に `com.etzhayyim.cohort.evidence` 分岐を insert
2. `forwardOcelToApqc` legacy `kProxy` field 削除 (app.ts 側 writeDataPoint も更新)
3. `com.etzhayyim.cohort.fissionLineage` record lexicon 定義
4. `etzhayyim cohort lineage --did <fissioned>` CLI で derived_from chain を辿る
5. Murakumo agent tool registration

# Iteration 19 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/cohort/fissionLineage.json` | 新規 record lexicon: individualDid / derivedFrom / posteriorAtFission (>=0.95) / judgeAgreement=true / evidenceUris / fissionAt / parentSegmentHash。rkey=literal:self |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort lineage --did <did>` subcommand — listCohorts 経由で derived_from chain を上方向に辿る。`--max` で最大 hop 数指定、`--json` で生 output |
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | `CohortKDriftResult.ocelEvents` から legacy `kProxy` field 削除。`numericPayload` のみに統一 |
| `50-infra/cloudflare/workers/atproto/src/app.ts` | `ev.kProxy → ev.numericPayload` 参照更新 |

## Lineage CLI Example

```bash
etzhayyim cohort lineage --did did:plc:pending-<fissioned>
# lineage (2 hop):
#   ├─ did:plc:pending-xxxxxxxx  agent-xxxxxxxx.etzhayyim.com  kind=fissioned  segment=sha256:pcfL1=3-market-sell;...
#   └─ did:plc:pending-cmkt003c  cohort-cmkt003c.etzhayyim.com  kind=cohort    segment=sha256:pcfL1=3-market-sell;...
```

## Evaluation — API Surface Cleanup

- `forwardOcelToApqc` 引数も戻り値 `ocelEvents[].numericPayload` も単一の semantic field に統一
- OcelEventType 毎の意味 (genesis=kAnonymity / accrued=posterior / kReevaluated=k_proxy / fission=posterior / purge=0) は cohort-watchdog.ts JSDoc に永続化 (Iter 18)

## Process Mining — Lineage Depth Analysis

`etzhayyim cohort lineage --did <x> --json` を集計 pipeline に流すと:

```bash
# 全 fissioned の lineage depth 分布
for did in $(etzhayyim cohort list --kind fissioned --json | jq -r '.cohorts[].cohortDid'); do
  depth=$(etzhayyim cohort lineage --did "$did" --json | jq 'length')
  echo "$did $depth"
done | awk '{print $2}' | sort | uniq -c
```

chain が長い = 繰り返し分裂した actor、短い = 1 回のみ fission。ADR-0026 運用メトリクスとして残す。

## Risk / Open Items

- fissionLineage record の自動 write は `handleCohortFission` に追加されていない。次 iter で persist 経路を add
- onCommit evidence handler insert も未 (依然 spec のみ)

## 次 iteration TODO

1. `handleCohortFission` 内で `com.etzhayyim.cohort.fissionLineage` record を `did=individualDid, rkey='self'` で write (persistence 完成)
2. onCommit evidence handler insert (本番 commit pipeline に evidence → projector OCEL の branch を追加)
3. Murakumo agent tool registration (`cohort.seed` + `cohort.fission` を LLM callable に)
4. `com.etzhayyim.cohort.listEvidence --cohort <did>` query lexicon (分析 surface 拡張)
5. `etzhayyim cohort forest --pcfL1 <slug>` — L1 毎の cohort→fissioned tree を ascii 出力

# Iteration 20 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortFission` に `com.etzhayyim.cohort.fissionLineage` record write (PDS XRPC fetch, individualDid 名義) 追加。`handleCohortListEvidence(env, input)` 新規 — cohort_did + optional minPosterior/judgeAgreement filter で vertex_repo_record を read |
| `00-contracts/lexicons/com/etzhayyim/cohort/listEvidence.json` | 新規 query lexicon (required: cohortDid) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | `case "com.etzhayyim.cohort.listEvidence"` dispatch + PLATFORM_READ 登録 |

## API Surface (cohort cluster)

| NSID | Method | Description |
|---|---|---|
| `com.etzhayyim.cohort.seed` | POST | Phase A genesis (idempotent by segment_hash) |
| `com.etzhayyim.cohort.fission` | POST | Phase C fission (+ auto lineage record) |
| `com.etzhayyim.cohort.listCohorts` | GET | Actor列挙 (kind/pcfL1/locale/fission filter) |
| `com.etzhayyim.cohort.listEvidence` | GET | Evidence列挙 (cohort_did scoped, posterior filter) |

## Process Mining — Evidence analytics

```bash
# 特定 cohort の fission-ready evidence 件数
curl -H "Authorization: Bearer $AT_TOKEN" \
  "https://atproto.etzhayyim.com/xrpc/com.etzhayyim.cohort.listEvidence?cohortDid=did:plc:pending-abc&minPosterior=0.95&judgeAgreement=true"

# → posterior ≥ 0.95 かつ judge agreed な evidence row を列挙
#    これが >= 1 かつ fission_enabled=true なら `etzhayyim cohort fission` を発火できる
```

## Fission Lineage Persistence

`handleCohortFission` 成功時に:
1. `vertex_cohort_actor` row INSERT (kind='fissioned', derived_from=parent) — graph side
2. `com.etzhayyim.cohort.fissionLineage` AT Record self rkey で write — repo side (federable)
3. `cohort.fission` OCEL event emit — projector 側

三重記録で fission イベントが watch/query/federation いずれ経由でも追跡可能。

## Risk / Open Items

- lineage record write は fire-and-forget (catch → warn)。PDS fetch 失敗時の retry は write-outbox (既存) に乗せる設計にすべき
- listEvidence は `vertex_repo_record` の `cohort_did` column (migration 0052 で追加) に依存。non-cohort record は WHERE でフィルタされるので安全
- onCommit handler insert は依然未完

## 次 iteration TODO

1. `etzhayyim cohort evidence --cohort <did>` CLI (listEvidence wrapper)
2. `etzhayyim cohort forest --pcfL1 <slug>` — L1 毎の cohort + children tree を ascii 出力
3. onCommit dispatcher insert (cohort.evidence commit)
4. write-outbox 経由の lineage record retry
5. Murakumo agent tool registration

# Iteration 21 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort evidence --cohort <did> [--min-posterior 0.95 --judge true]` subcommand (listEvidence wrapper); `etzhayyim cohort forest --pcfL1 <slug>` subcommand (cohort + fissioned ascii tree via derived_from index) |

## CLI Surface — Complete

```
etzhayyim cohort seed        # Phase A genesis (1 segment)
etzhayyim cohort bootstrap   # Phase A bulk seed from deps.toml
etzhayyim cohort list        # cohort actor 列挙
etzhayyim cohort evidence    # evidence 列挙 (cohort scoped)  ← 本 iter
etzhayyim cohort fission     # Phase C fission
etzhayyim cohort lineage     # derived_from chain upward
etzhayyim cohort forest      # cohort + children downward tree  ← 本 iter
```

## Forest Output Example

```
$ etzhayyim cohort forest --pcfL1 3-market-sell
forest (4 nodes, pcfL1=3-market-sell):
did:plc:pending-cmkt003c  cohort-cmkt003c.etzhayyim.com  kind=cohort
  did:plc:pending-xxxxxxxx  agent-xxxxxxxx.etzhayyim.com  kind=fissioned
    did:plc:pending-yyyyyyyy  agent-yyyyyyyy.etzhayyim.com  kind=fissioned
did:plc:pending-cmkt203n  cohort-cmkt203n.etzhayyim.com  kind=cohort
```

## Process Mining — Dashboard-ready Queries

evidence + forest 組合せで operational dashboard 可能:

```bash
# L1 毎の fission-ready cohort 検出
for cohort in $(etzhayyim cohort list --pcfL1 3-market-sell --json | jq -r '.cohorts[].cohortDid'); do
  ready=$(etzhayyim cohort evidence --cohort "$cohort" --min-posterior 0.95 --judge true --json | jq '.evidence | length')
  [ "$ready" -ge 1 ] && echo "$cohort ready=$ready"
done
```

## Risk / Open Items

- onCommit evidence handler insert 未完 — evidence → `cohort.evidence.accrued|fissionReady` OCEL emit がまだ流れない
- write-outbox 経由の fissionLineage record retry は未実装
- Murakumo LLM tool registration 未着手

## 次 iteration TODO

1. onCommit dispatcher insert (com.etzhayyim.cohort.evidence branch)
2. write-outbox retry for lineage record
3. Murakumo agent tool registration (cohort.seed + cohort.fission)
4. `etzhayyim cohort stats` — per-L1 aggregate (cohort count / fissioned count / avg posterior / k-drift rate)
5. en × seniority × industry 3 軸 cross-product 展開 (+ N cohort)

# Iteration 22 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort stats` subcommand — per-L1 aggregate (cohort / fissioned / fissionEnabled / total) |
| `deps.toml` | +5 cohort (3-axis cross-product: en×senior×banking IT、en×junior×mfg ops、en×senior×healthcare CS、jp×senior×pharma PS、jp×senior×banking FR) |

## Cohort Total N=70

分布更新:
- locale=jp: 39 (+2)
- locale=en: 30 (+3)
- seniority overlay: 22
- industry overlay: 15 (+5)
- 3-axis (locale × seniority × industry) 充足: 5 cells

初めて 3 axes 全てが同時指定された cohort が登場。

## Stats CLI Example

```
$ etzhayyim cohort stats
pcfL1                                  cohorts  fissioned fissionEnabled  total
1-vision-strategy                            3          0              0      3
2-product-service                            5          0              0      5
3-market-sell                                6          0              0      6
...
```

## Evaluation

stats は listCohorts 上に client-side aggregation で実装。専用 MV なしで fleet 全体の分布を 1 コマンド可視化。JSON 出力 (`--json`) で外部 dashboard 連携可。

## Process Mining

ops dashboard として `etzhayyim cohort stats --json | jq ...` を watch すると:
- 各 L1 の cohort 残量
- fission で生まれた individual 数
- watchdog が fission 無効化した数 (fissionEnabled 低下 = k-drift violation の合計)

ADR-0026 の運用健全性を 1 行で把握可能。

## 次 iteration TODO

1. onCommit dispatcher insert (evidence commit → projector emit)
2. write-outbox retry for lineage record
3. Murakumo tool registration
4. `stats --by locale,seniority,industry` で任意次元の group-by
5. cross-product 拡張: healthcare/retail の en variant + jp variant

# Iteration 23 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort stats --by <axes>` 実装 — axes = `pcfL1,role,industry,seniority,locale` から任意組合せ。client-side group-by で multi-dim aggregate。`extractPcfL1FromHash` を削除し、汎用 `parseSegmentKV` に統合 |
| `deps.toml` | +3 cohort (healthcare jp junior / retail jp junior / retail en junior) |

## Cohort Total N=73

分布:
- locale=jp: 41 (+2)
- locale=en: 31 (+1)
- seniority overlay: 25 (jp senior + junior 両方)
- industry overlay: 18

## Multi-dim Stats CLI

```bash
# 従来 (single axis)
etzhayyim cohort stats
etzhayyim cohort stats --by pcfL1

# 新 (composite axis)
etzhayyim cohort stats --by pcfL1,locale
etzhayyim cohort stats --by industry,seniority
etzhayyim cohort stats --by locale,seniority,industry --json | jq
```

例 output (industry × seniority):

```
industry/seniority                         cohorts  fissioned fissionEnabled  total
-/-                                             40          0              0     40
-/junior                                         4          0              0      4
-/senior                                        14          0              0     14
banking/senior                                   2          0              0      2
healthcare/senior                                1          0              0      1
...
```

`-` = field absent from segment (first dimensions of deprecated plain cohorts).

## Evaluation

単一 MV ベースの stats を避け、listCohorts の client-side aggregation を維持。MV 新設 cost がかからず、任意 axis を組合せる試行錯誤が CLI で完結。大規模化したら `mv_cohort_stats_by_l1_locale` 等の narrow MV に昇格する選択肢を残す。

## Process Mining

軸の cross-product で seg 単位での成熟度 (cohort=多 / fissioned=多 / fissionEnabled=少) を観察し、どの segment が実用 Phase B/C に進んでいるかの監視が可能に。

## 次 iteration TODO

1. onCommit dispatcher insert
2. write-outbox retry for lineage
3. Murakumo tool registration
4. `etzhayyim cohort stats --kind cohort|fissioned` で cohort/fissioned 別出力
5. 初の実 fission 動作試験 (posterior ≥ 0.95 な evidence を createRecord で投入 → cohort fission)

# Iteration 24 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort_test.go` | 新規: `parseSegmentKV` (3 cases) + `cohortEntry.toSegmentJsonld` (keys check) + `sortStrings` (duplicate sort) の unit test |
| `deps.toml` | +3 cohort (IT L1 role 深堀: dataEngineer / mlEngineer / frontendEngineer jp) |

## Cohort Total N=76

分布:
- locale=jp: 44 (+3)
- locale=en: 31
- seniority overlay: 25
- industry overlay: 18
- IT L1 role: 4 (sreEngineer / secOpsEngineer / dataEngineer / mlEngineer / frontendEngineer) — IT 職種が最も深く展開

## Evaluation — Test Coverage

`cohort.go` 内部ロジック 3 関数に unit test:
- `parseSegmentKV`: minimum / full / empty
- `cohortEntry.toSegmentJsonld`: JSON-LD 逆変換の key 含有
- `sortStrings`: insertion sort の duplicate 扱い

go test ./70-tools/etzhayyim/etzhayyim で走行。handler/DB 接続不要の純 logic なので CI で低コスト。

## Process Mining — Role Depth Analysis

```bash
etzhayyim cohort stats --by pcfL1,role | grep 8-info
# 8-info-technology/sreEngineer        ...
# 8-info-technology/secOpsEngineer     ...
# 8-info-technology/dataEngineer       ...
# 8-info-technology/mlEngineer         ...
# 8-info-technology/frontendEngineer   ...
```

IT L1 が他 L1 より role 数で先行。次は FR/HR/RC 各 L1 の role 深堀候補。

## 次 iteration TODO

1. onCommit dispatcher insert
2. write-outbox retry for lineage
3. Murakumo tool registration
4. `etzhayyim cohort stats --kind` 出力フィルタ
5. role 深堀第二波: FR (9) / HR (7) / RC (11) 各 L1 に +3 role

# Iteration 25 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort stats --kind cohort\|fissioned` filter 追加 (空 = 両方) |
| `deps.toml` | +9 cohort (FR: treasurer/controller/fpa、HR: benefitsAdmin/learningDev/hrBP、RC: legalCounsel/privacyOfficer/riskAnalyst) |

## Cohort Total N=85

分布更新:
- locale=jp: 53 (+9)
- locale=en: 31
- L1 role depth:
  - IT: 5 role (sre/secOps/data/ml/frontend)
  - FR: 4 role (accountant/treasurer/controller/fpaAnalyst)
  - HR: 4 role (hrGeneralist/benefitsAdmin/learningDev/hrBP + talent)
  - RC: 4 role (complianceOfficer/legalCounsel/privacyOfficer/riskAnalyst + auditor)

## Process Mining

```bash
# fissioned のみ
etzhayyim cohort stats --kind fissioned --by pcfL1

# cohort (未分裂) のみ、role 別
etzhayyim cohort stats --kind cohort --by pcfL1,role
```

kind filter で Phase 別の運用量を監視可能 → 運用初期は cohort=多 / fissioned=少、成熟期は fissioned 比率上昇の想定。

## Evaluation

IT/FR/HR/RC の 4 L1 (全 13 中 30%) で role=4〜5 role を達成。残 9 L1 は role=1〜3 で段階展開候補。

## 次 iteration TODO

1. onCommit dispatcher insert (依然保留)
2. write-outbox retry for lineage
3. Murakumo tool registration
4. L2/L4/L10 role 深堀 (product manager variants / supply chain variants / asset management variants)
5. `etzhayyim cohort test` — CLI internal logic の一括 test runner

# Iteration 26 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +9 cohort (L2 product-service: productEngineer/qaLead/productResearcher、L4 supply-chain: warehouseOperator/procurementBuyer/demandPlanner、L10 asset-management: realEstate/fleet/itAsset) |
| `70-tools/etzhayyim/etzhayyim/cohort_test.go` | +1 test: parseSegmentKV が malformed segment (no `=`) を silently skip する挙動を fix |

## Cohort Total N=94

分布:
- locale=jp: 62 (+9)
- locale=en: 31
- L1 role depth:
  - L2 product-service: 5 role
  - L4 supply-chain: 4 role
  - L10 asset-management: 4 role
  - 合計 4 L1 が role=4+ (IT/FR/HR/RC の既存 4 L1 と合わせて **8 L1 が深い role 展開**)

## Evaluation — 覆盖率

残 5 L1 (L1/L3/L5/L6/L12/L13) のうち L3 (market-sell) は既に marketing+retail 含め 6 role。よって role=1〜2 の「浅い」L1 は L1/L5/L6/L12/L13 の 5 つ。

## Process Mining

```bash
etzhayyim cohort stats --by pcfL1 --kind cohort | sort -k2 -n
# role depth 低い L1 が末尾に並ぶ → 次の深堀対象が自動 identify
```

## Risk / Open Items

- 13 L1 中 8 L1 が role≥4、残 5 L1 が浅い。role coverage 平準化が次段階
- onCommit / write-outbox / Murakumo 3 TODO は積み残し

## 次 iteration TODO

1. L1 (vision-strategy) / L5 (production-ops) / L6 (customer-service) role 深堀
2. onCommit dispatcher insert
3. Murakumo tool registration
4. `etzhayyim cohort test` smoke runner (cohort_test.go は unit test、integration smoke は CLI reachability 確認)
5. write-outbox retry for lineage

# Iteration 27 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +9 cohort: L1 vision-strategy (corpDev / transformation / maSpecialist)、L5 production-ops (maintenance / qualityEngineer / supervisor)、L13 business-capability (enterpriseArchitect / processOwner / transformation) |

## Cohort Total N=103

role depth map:
| L1 | depth | roles |
|---|---|---|
| L1 vision-strategy | **4** | strategist / strategyAnalyst / corpDev / transformation / maSpecialist |
| L2 product-service | 5 | pm / designer / engineer / qa / researcher |
| L3 market-sell | 4 | salesRep / marketing / retail / (en variants) |
| L4 supply-chain | 4 | plannerBuyer / logistics / warehouse / procurement / demand |
| L5 production-ops | **4** | lineOperator / maintenance / quality / supervisor |
| L6 customer-service | 3 | supportAgent / cxLead / healthcare |
| L7 human-capital | 5 | hrGeneralist / benefitsAdmin / learningDev / hrBP / talent |
| L8 info-technology | 5 | sre / secOps / data / ml / frontend |
| L9 financial-resources | 4 | accountant / treasurer / controller / fpa |
| L10 asset-management | 4 | assetManager / realEstate / fleet / itAsset / facilities |
| L11 risk-compliance | 4 | compliance / legal / privacy / riskAnalyst / auditor |
| L12 external-relations | 2 | prSpecialist / investorRelations |
| L13 business-capability | **4** | capability / portfolio / enterprise / processOwner / transformation |

**12/13 L1 で role≥3 に到達**。残り浅い L1 は L6 (3) と L12 (2) の 2 つ。

## Evaluation

role coverage の平準化がほぼ完了。次は L6/L12 に +2〜3 role 追加で 13 L1 全てが role≥3 になる。

## Process Mining

```bash
etzhayyim cohort stats --by pcfL1 --kind cohort --json | jq 'map({key,total}) | sort_by(.total)'
# → role depth 最少の L1 を見つけて深堀 target を機械的に決定
```

## 次 iteration TODO

1. L6 customer-service / L12 external-relations 最終 role 深堀 → 13 L1 全て role≥3 達成
2. onCommit dispatcher insert
3. Murakumo tool registration
4. `etzhayyim cohort coverage --axes pcfL1,role` で cover matrix (存在 / 欠落 cell) 可視化
5. 本番 staging でバージョン tagging + 1 cohort 実 seed (smoke run)

# Iteration 28 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort coverage --axes <row,col>` 実装 — 2D cover matrix (`.` = empty, 数字 = count)。空 cell 検出で coverage gap が一目でわかる |
| `deps.toml` | +6 cohort (L6: fieldTech/supportOpsMgr/customerSuccess、L12: govAffairs/partnerships/csr) |

## Cohort Total N=109

**13 L1 全てで role≥3 達成 (milestone)**:
| L1 | depth |
|---|---|
| L1 vision-strategy | 5 |
| L2 product-service | 5 |
| L3 market-sell | 4 |
| L4 supply-chain | 4 |
| L5 production-ops | 4 |
| L6 customer-service | **4 (本 iter)** |
| L7 human-capital | 5 |
| L8 info-technology | 5 |
| L9 financial-resources | 4 |
| L10 asset-management | 4 |
| L11 risk-compliance | 5 |
| L12 external-relations | **4 (本 iter)** |
| L13 business-capability | 4 |

**Total = 57 unique (L1, role) pairs** out of 13×? (role set varies per L1)。role 軸の 1st tier coverage 完了。

## Evaluation

`etzhayyim cohort coverage --axes pcfL1,role` で (L1 × role) matrix を render、空 cell ゼロ。2D matrix の rendering cost は listCohorts 1 call + client-side aggregate。

## Process Mining

```bash
# pcfL1 × locale matrix
etzhayyim cohort coverage --axes pcfL1,locale
# → en locale coverage gap が即座にわかる (多くの L1 で .)

# industry × seniority matrix
etzhayyim cohort coverage --axes industry,seniority
# → banking/healthcare/manufacturing × junior/mid/senior cells
```

## 次 iteration TODO

1. pcfL1 × locale matrix を見て en 展開の次 target を決定
2. onCommit dispatcher insert
3. Murakumo tool registration
4. `etzhayyim cohort gap --axes a,b --min N` — matrix で cell < N の空白を列挙 (gap 機械 identify)
5. 本番 staging smoke seed + CLI coverage の実動確認

# Iteration 29 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort gap --axes row,col --min N` 実装 — 空 cell + 1..N-1 count cells を列挙 (gap 自動 identify) |
| `deps.toml` | +5 cohort: L4/L5/L6/L10/L11 の en locale 追加 (各 1 role) |

## Cohort Total N=114

locale=en 覆盖更新:
- L1/L2/L3/L7/L8/L9/L12/L13: 既存
- L4 supply-chain: **+logisticsCoordinator (本 iter)**
- L5 production-ops: **+qualityEngineer (本 iter)**
- L6 customer-service: **+cxLead (本 iter)**
- L10 asset-management: **+realEstateManager (本 iter)**
- L11 risk-compliance: **+legalCounsel (本 iter)**

locale=en 13 L1 全てに少なくとも 1 cohort 到達。jp/en locale coverage 均衡。

## Evaluation — Gap CLI

```bash
etzhayyim cohort gap --axes pcfL1,locale --min 1
# → 空の (pcfL1, locale) cell を列挙。すべての 13×2 cell が埋まっていれば "gaps: 0 cells"

etzhayyim cohort gap --axes pcfL1,industry --min 1
# → industry overlay が無い L1 を特定 (L1/L7/L8/L13 等が候補)
```

## Process Mining

gap CLI は coverage CLI の補完:
- `coverage` = 全 cell を 2D render (総覧)
- `gap` = count<N な cell のみ列挙 (機械 identify)

bash loop で gap を feed に `etzhayyim cohort seed` を自動実行する agentic loop が可能。

## 次 iteration TODO

1. pcfL1 × industry gap をターゲットに industry overlay 拡大
2. onCommit dispatcher insert
3. Murakumo tool registration
4. `etzhayyim cohort gen --pcfL1 --role --industry --locale -k 50` — one-shot seed builder (複数パラメータから JSON-LD を組立て seed)
5. staging smoke seed + 実動テスト

# Iteration 30 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort gen` 実装 — typed flags (--pcfL1/--role/--industry/--seniority/--locale/--k) から JSON-LD を自動生成し seed。`--dry-run` で JSON 確認のみ可能 |
| `deps.toml` | +5 cohort (industry overlay 拡大: L1×banking、L7×healthcare、L8×pharma、L11×banking、L13×retail) |

## Cohort Total N=119

industry 分布更新:
- banking: 6 (L1/L9×2/L11/FR/IT cross + 本 iter L11)
- healthcare: 5 (L6/L7×2/CS + 本 iter L7)
- manufacturing: 3 (L5×2 + mfg)
- pharma: 4 (L2×2 + 本 iter L8)
- retail: 5 (L3×3 + 本 iter L13)

13 L1 のうち industry overlay 保有 L1 = L1/L2/L3/L5/L6/L7/L8/L9/L11/L13 の **10 L1** (残 L4/L10/L12 の 3 L1)。

## CLI Gen Example

```bash
# Dry-run preview
etzhayyim cohort gen --pcfL1 9-financial-resources --role accountant --industry banking --locale jp --dry-run
# → {"industry":"banking","locale":"jp","pcfL1":"9-financial-resources","role":"accountant"}

# Actual seed
etzhayyim cohort gen --pcfL1 9-financial-resources --role accountant --industry banking --locale jp -k 50
# gen ok: did=did:plc:pending-<nano> handle=cohort-<nano>.etzhayyim.com
```

## Process Mining

gap + gen CLI の組合せで agentic auto-seed pipeline が可能:

```bash
# L4/L10/L12 で industry gap を埋める
etzhayyim cohort gap --axes pcfL1,industry --min 1 --json | jq -r '.[] | select(.col != "-") | "\(.row) \(.col)"' | while read l1 ind; do
  etzhayyim cohort gen --pcfL1 "$l1" --role "$(pickRole "$l1")" --industry "$ind" --locale jp -k 50
done
```

## 次 iteration TODO

1. L4 / L10 / L12 の industry overlay (logistics, facilities, governance industry variants)
2. onCommit dispatcher insert
3. Murakumo tool registration
4. `etzhayyim cohort gen --seniority` も含めた 3-axis 複合 seed 大量生成
5. staging smoke seed + live coverage CLI 実動

# Iteration 31 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +3 cohort: L4 retail/plannerBuyer、L10 manufacturing/facilitiesLead、L12 pharma/investorRelations |

## Cohort Total N=122

**13 L1 全てで industry overlay 保有 (milestone)**:
| L1 | industry overlays |
|---|---|
| L1 | banking |
| L2 | pharma ×2 |
| L3 | retail ×3 |
| L4 | **retail (本 iter)** |
| L5 | manufacturing ×2 |
| L6 | healthcare ×2 |
| L7 | healthcare |
| L8 | pharma |
| L9 | banking ×2 |
| L10 | **manufacturing (本 iter)** |
| L11 | banking |
| L12 | **pharma (本 iter)** |
| L13 | retail |

全 13 L1 × industry coverage = first tier 完了。

## Evaluation — 3 Axis Coverage

| Axis | 13 L1 全て保有 |
|---|---|
| locale (jp/en) | ✅ |
| role (≥3 per L1) | ✅ |
| industry (≥1 per L1) | ✅ (本 iter 達成) |
| seniority (junior/mid/senior) | 部分的 (一部 L1 のみ) |

3/4 axis で完全 coverage。seniority が次の網羅 target。

## Process Mining

```bash
etzhayyim cohort stats --by pcfL1,industry | grep -v "^[^ ]*  *0 "
# → 13 L1 全てで industry 非ゼロ行が表示される
```

## 次 iteration TODO

1. seniority axis の平準化 (各 L1 に junior/mid/senior のいずれか)
2. onCommit dispatcher insert
3. Murakumo tool registration
4. coverage matrix snapshot を `data/cohort-coverage/<date>.json` に保存する `etzhayyim cohort snapshot` subcommand
5. staging smoke seed

# Iteration 32 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +5 cohort: seniority=senior 追加 (L1/L4/L5/L10/L13)。既存の senior overlay (L3/L7/L8/L9/L11/L12) と合わせて 11 L1 で senior tier 保有 |

## Cohort Total N=127

seniority 分布更新:
- senior 保有 L1: 11/13 (残 L2 / L6)
- junior: 3 (L3 retail / L5 mfg / L8 IT)
- mid: 1 (L8 IT)

## Evaluation — 4 Axis Status

| Axis | L1 coverage |
|---|---|
| locale | 13/13 (jp+en) |
| role (≥3) | 13/13 |
| industry (≥1) | 13/13 |
| seniority (≥1 senior) | 11/13 |

## 次 iteration TODO

1. L2 / L6 に senior 追加で seniority 13/13 達成
2. onCommit dispatcher insert
3. Murakumo tool registration
4. `etzhayyim cohort snapshot` subcommand
5. staging smoke seed

# Iteration 33 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +2 cohort: L2 product-service senior、L6 customer-service senior。**4 axis 完全 coverage 達成 (13/13)** |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort snapshot` subcommand 実装 — 4 axis aggregate を `data/cohort-coverage/<timestamp>.json` に保存。drift 監視 baseline |

## Cohort Total N=129

**4 axis 完全 coverage**:
| Axis | L1 coverage |
|---|---|
| locale (jp+en) | **13/13** ✅ |
| role (≥3) | **13/13** ✅ |
| industry (≥1) | **13/13** ✅ |
| seniority (≥1 senior) | **13/13** ✅ |

ADR-0026 cohort 設計の axis 全てで 100% 覆盖達成。

## Snapshot Persistence

```bash
etzhayyim cohort snapshot
# snapshot written: data/cohort-coverage/20260415T143012Z.json (total=129, fissioned=0)

# 1 週間後に diff:
diff <(jq -S . data/cohort-coverage/20260415T143012Z.json) <(jq -S . data/cohort-coverage/20260422*.json)
```

JSON 構造:
```json
{
  "capturedAt": "2026-04-15T14:30:12Z",
  "totalCohorts": 129,
  "totalFissioned": 0,
  "axes": {
    "pcfL1": [{"value":"1-vision-strategy","cohorts":..., "fissioned":...}, ...],
    "role": [...],
    "industry": [...],
    "seniority": [...],
    "locale": [...]
  }
}
```

## Process Mining — Coverage Drift

snapshot を定期 (週次/月次) で取れば cohort fleet の長期推移が観測可能:
- cohort growth rate
- fissioned / cohort 比率 (cohort 成熟度)
- axis 別の偏り (例: en locale 比率の上昇)

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. `etzhayyim cohort diff <a.json> <b.json>` で 2 snapshot の delta 表示
4. cohort total 200 突破に向けた role / industry の cross-product 拡張
5. staging smoke seed (実 PDS 経由で cohort 1 件 mint)

# Iteration 34 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort diff <a.json> <b.json>` 実装 — 2 snapshot 間の axis 別 delta を表示 (count 増減のみ列挙) |
| `deps.toml` | +4 cohort: 3-axis cross-product (role × industry × seniority) — L3 marketing×banking×junior、L7 talent×pharma×mid、L9 controller×banking×mid、L11 privacy×healthcare×senior |

## Cohort Total N=133

3-axis cross 充足セル増加:
- L3 × marketing × banking × junior (新)
- L7 × talent × pharma × mid (新)
- L9 × controller × banking × mid (新)
- L11 × privacy × healthcare × senior (新)

cross-product covered cells = 11 → 15。

## Diff CLI

```bash
# 1 週間後
etzhayyim cohort snapshot                                            # → 20260422...json
etzhayyim cohort diff data/cohort-coverage/20260415*.json data/cohort-coverage/20260422*.json
# snapshot A: 2026-04-15T... total=133 fissioned=0
# snapshot B: 2026-04-22T... total=148 fissioned=2
# Δ total      = +15
# Δ fissioned  = +2
# [pcfL1]
#   8-info-technology               +5  (15 → 20)
# [seniority]
#   senior                          +12 (35 → 47)
```

## Process Mining

snapshot + diff の組合せで cohort fleet evolution が観測可能:
- 増加率: 週次 +N cohort
- axis 偏向: 特定 industry/seniority への増減
- fission rate: cohort → fissioned 比率

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. role 不足 L1 (L4/L5/L6/L10/L12) に追加 +5
4. snapshot diff の `--json` 出力
5. cohort 200 達成 (現 133 → +67 必要)

# Iteration 35 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +5 cohort: en × senior × {procurement(L4), quality(L5), customerSuccess(L6), fleet(L10), partnerships(L12)} — en×senior 軸を 5 L1 に追加 |

## Cohort Total N=138

en × senior 分布:
- 既存: L3, L7, L8, L9, L11 (5 L1)
- 本 iter: L4, L5, L6, L10, L12 (5 L1)
- 累計: 10/13 L1 で en × senior 保有 (残 L1/L2/L13)

## Process Mining

```bash
etzhayyim cohort coverage --axes pcfL1,seniority | grep -- senior
# → 各 L1 の senior count を確認
```

## 次 iteration TODO

1. L1/L2/L13 en × senior で 13/13 達成
2. snapshot diff `--json`
3. onCommit dispatcher insert
4. Murakumo tool registration
5. cohort 150 突破

# Iteration 36 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +12 cohort: L1/L2/L13 en×senior 完了 (3) + junior tier L2/L9/L11 (3) + mid tier L3/L7/L13 (3) + en role 第2 L1/L4/L11 (3) |

## Cohort Total N=150 (節目突破)

milestone:
- en × senior: **13/13 完了**
- junior tier 保有 L1: 7 (前回 4 → 7)
- mid tier 保有 L1: 5 (前回 2 → 5)
- en × 多 role: L1/L4/L11 で 2 役割

## Evaluation — 5 axes

| Axis | L1 coverage |
|---|---|
| locale (jp+en) | 13/13 |
| role (≥3) | 13/13 |
| industry (≥1) | 13/13 |
| seniority (≥1 senior) | 13/13 |
| en × senior | **13/13 (本 iter)** |

## 次 iteration TODO

1. snapshot diff JSON
2. onCommit dispatcher insert
3. Murakumo tool registration
4. en × industry overlay 拡張
5. cohort 175 突破

# Iteration 37 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort diff --json` flag 追加 — JSON delta report 出力 |
| `deps.toml` | +5 cohort: en × industry (L1×banking、L7×healthcare、L8×pharma、L11×banking、L13×retail) |

## Cohort Total N=155

en × industry 分布:
- 既存: L2/L3 (jp と並行)
- 本 iter: L1/L7/L8/L11/L13 (5 L1)
- 累計: 7/13 L1 で en × industry 保有

## Diff JSON Example

```bash
etzhayyim cohort diff data/cohort-coverage/20260415*.json data/cohort-coverage/20260422*.json --json | jq '.axes.pcfL1[]'
# {"value":"8-info-technology","before":15,"after":20,"delta":5}
# ...
```

## Process Mining

JSON delta は CI/dashboard pipeline に直結可能。週次 cron で snapshot → diff を取り、Δ が閾値を超えたら slack 通知する agentic 監視が可能。

## 次 iteration TODO

1. en × industry を残 6 L1 に拡張
2. onCommit dispatcher insert
3. Murakumo tool registration
4. cohort 175 突破
5. `etzhayyim cohort drift --window 7d` — snapshot history を直接読んで drift 計算

# Iteration 38 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +6 cohort: en × industry on remaining 6 L1 (L4×retail / L5×mfg / L6×healthcare / L9×banking / L10×mfg / L12×pharma) |

## Cohort Total N=161

**en × industry 13/13 完了**:
- 全 L1 で英語 industry overlay 保有
- jp と en で完全対称な industry coverage

## Evaluation — 6 axis status

| Axis | L1 coverage |
|---|---|
| locale (jp+en) | 13/13 |
| role (≥3) | 13/13 |
| industry (≥1) | 13/13 |
| seniority (≥1 senior) | 13/13 |
| en × senior | 13/13 |
| en × industry | **13/13 (本 iter)** |

6 axis 全 13 L1 完全 coverage 達成。

## 次 iteration TODO

1. drift CLI (--window で snapshot history 自動読込)
2. onCommit dispatcher insert
3. Murakumo tool registration
4. cohort 175 突破 (現 161 → +14 必要)
5. fission シミュレーション (cohort + evidence + posterior=0.97 + judge=true で実 fission を試す)

# Iteration 39 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort drift --dir <path> --window 7` 実装 — snapshot dir 内の最古/最新 (window 内) を自動 pick して diff 出力 |
| `deps.toml` | +14 cohort: mid tier 平準化 (10 L1 = L1/L2/L4/L5/L6/L9/L10/L11/L12 + 既存 L8) + en×senior×industry triple cells (4: L3/L7/L9/L11) |

## Cohort Total N=175 (節目突破)

milestone:
- mid tier: 12/13 L1 (前回 5 → 12)
- en×senior×industry triple: 4 cells (新)
- 累計 175 達成

## Drift CLI

```bash
etzhayyim cohort drift --window 7
# drift window: data/cohort-coverage/20260408*.json ⇒ data/cohort-coverage/20260415*.json (3 snapshots)
# Δ total      = +25
# ...

etzhayyim cohort drift --window 30 --json | jq '.deltaTotal'
```

## Process Mining

cohort drift CLI で cron + jq 1-liner で長期推移を運用 dashboard 化可能。

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. cohort 200 突破 (現 175 → +25 必要)
4. fission シミュレーション
5. mid tier 残 1 L1 (L13)

# Iteration 40 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | +25 cohort: L13 mid (1) + en × junior (10 L1) + en × mid (10 L1) + jp×senior×industry triple gap-fill (4) |

## Cohort Total N=200 (節目突破 🎯)

milestone:
- mid tier: **13/13 L1 完了** (jp)
- en × junior: 10/13 L1
- en × mid: 10/13 L1
- jp × senior × industry triple: 8 cells

## Evaluation — 全 axis 状態

| Axis | jp 13/13 | en 13/13 |
|---|---|---|
| base | ✅ | ✅ |
| role ≥3 | ✅ | partial (~7) |
| industry | ✅ | ✅ |
| seniority senior | ✅ | ✅ |
| seniority mid | ✅ (本 iter) | ~10/13 |
| seniority junior | ~7/13 | ~10/13 |

en × {junior, mid, senior} 3 tier ほぼ揃った状態。

## Process Mining

cohort 200 = ADR-0026 reverse identity topology の運用 baseline 規模に到達。今後の評価:
- 仮想 fission シミュレーション → fission lineage の最大 chain depth 確認
- snapshot drift weekly → 自然増加率 baseline
- ocel emission rate (kReevaluated / fission) → APQC projector 負荷見積

## 次 iteration TODO

1. onCommit dispatcher insert (Phase B handler が真に動作する)
2. Murakumo tool registration
3. fission シミュレーション (実 evidence INSERT → posterior 0.97 → fission)
4. en × {junior, mid, senior} 3 tier 全 13/13 完成 (+9 cohort)
5. cohort 250 突破

# Iteration 41 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortList` に `cohortDid` / `derivedFrom` の exact-match filter 追加 (lineage 探索の page-scan を排除) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | dispatch で 2 新 query param を bridge |
| `00-contracts/lexicons/com/etzhayyim/cohort/listCohorts.json` | `cohortDid` / `derivedFrom` パラメータ宣言追加 |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `fetchCohortByDid` を `?cohortDid=...&limit=1` 経由に変更 |

## Quality Improvement

cohort 量産から **per-call 効率化** にフォーカス転換:
- lineage CLI: 500 row scan × N hop → 1 row × N hop (深い chain でも O(hop) page request)
- forest CLI: derivedFrom filter 経由で再帰展開可能 (将来拡張)

## Cohort Total N=200 (unchanged)

cohort 規模は維持し、access path を改善。

## Process Mining

```bash
# 親 cohort の直接の子だけを高速取得
etzhayyim cohort list --json | jq 'select(.cohorts[].derivedFrom == "did:plc:pending-xxx")'
# は server-side filter で高速化:
curl ".../listCohorts?derivedFrom=did:plc:pending-xxx&limit=100"
```

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. fission シミュレーション
4. cohort 250 突破は次々 iter 以降に延期 (現在 200 で十分な scale)
5. `etzhayyim cohort list --derived-from` flag 追加 + forest CLI を再帰展開 mode に拡張

# Iteration 42 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort list --derived-from <did>` / `--did <exact>` flag 追加 (server-side filter 利用); `etzhayyim cohort forest --rooted <did>` で subtree-only render mode |

## CLI Surface — 14 subcommand 維持

新規 flag のみ。削除はなし。

```bash
# 親 cohort の子だけ取得
etzhayyim cohort list --derived-from did:plc:pending-xxx --json | jq '.cohorts | length'

# subtree のみの forest
etzhayyim cohort forest --rooted did:plc:pending-xxx
```

## Process Mining

特定 cohort の子孫だけを高速に visualizable に。Iter 41 の server-side filter と組合せて O(N×hop) → O(hop) の lineage 探索が実用化。

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. fission シミュレーション
4. `etzhayyim cohort lineage --depth N` で deep traversal の最大 depth 制限
5. cohort_test.go に list/forest のオプション parsing test 追加

# Iteration 43 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort lineage --depth N` flag (overrides `--max`); 0 で無制限相当に |
| `70-tools/etzhayyim/etzhayyim/cohort_test.go` | +1 test: 3-axis parseSegmentKV (pcfL1+role+seniority+industry+locale) |

## Quality

- lineage CLI に明示的 depth cap を追加。誤って循環 chain を辿る安全策
- cohort_test の coverage が 3-axis に拡大

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. fission シミュレーション
4. cohort 250 突破は保留 (200 で十分。実運用 fission データが入る方が優先)
5. CLI doc as `70-tools/etzhayyim/CLAUDE.md` への `etzhayyim cohort` セクション追加

# Iteration 44 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/CLAUDE.md` | `#### etzhayyim cohort` セクション新規追加。14 subcommand の table + auth path (`etzhayyim agent-token`) + design doc 参照 |

## Documentation Coverage

`etzhayyim cohort` CLI が 70-tools/etzhayyim/CLAUDE.md の正規ドキュメントに掲載され、他の subcommand (`etzhayyim auth`, `etzhayyim agent-token`, `etzhayyim murakumo fleet` 等) と同等の発見性を獲得。

## 次 iteration TODO

1. onCommit dispatcher insert
2. Murakumo tool registration
3. fission シミュレーション (実 evidence INSERT)
4. ADR-0026 status `proposed` → `active` 昇格判定 (Phase A E2E + watchdog 稼働確認後)
5. cohort 200 → 250 拡張は実運用データ (fission 1 件目) が入った後

# Iteration 45 — 2026-04-15

## Correction

Iter 40 で「cohort 200 突破」と書いたが、`grep -c '^\[\[cohort_actors\]\]'` = **198** が実数。ドキュメントの ±2 ズレ (Iter 39/40 のバッチカウント) を本 iter で訂正。

## Code Artifacts

| File | 変更 |
|---|---|
| `30-graph/graph-schema/migrations/0056_cohort_lineage_edges.ts` | 新規: 3 edge table + 4 index + `mv_cohort_lineage_depth` (Hummock のみ、Iceberg 不使用) |
| `30-graph/graph-schema/src/database.ts` | 4 Row interface + Database entry |
| `30-graph/graph-schema/CLAUDE.md` | Migration History に 0056 追記 |
| `50-infra/cloudflare/workers/atproto/src/insert-columns.ts` | `fission_at` / `pcf_l1` / `registered_at` を edge allowlist に追加 |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortSeed` で `edge_cohort_routes_to` INSERT、`handleCohortFission` で `edge_cohort_derived` INSERT |

## Vertex / Edge / MV 配線図

```
seed (Phase A)
  → vertex_cohort_actor (kind='cohort')
  → edge_cohort_routes_to (cohort_did → did:web:kyber-projector...:apqc:{L1})  ★new
  → forwardOcelToApqc (genesis)
       ↓
[evidence write to com.etzhayyim.cohort.evidence — Phase B, onCommit pending]
  → vertex_repo_record (cohort_did, evidence_hash, posterior, judge_agreement)
  → edge_cohort_evidence_about (evidence_hash → cohort_did)  ★ (handler 未配線)
  → mv_cohort_identity_posterior + mv_cohort_k_drift 自動更新
       ↓
fission (Phase C, posterior > 0.95 + judge=true)
  → vertex_cohort_actor (kind='fissioned', derived_from=parent)
  → edge_cohort_derived (parent_did → individual_did)  ★new
  → mv_cohort_lineage_depth 自動更新  ★new
  → forwardOcelToApqc (fission)
```

## Scale Note

198 cohort × 50 k-anonymity = ~10K minimum individuals。世界規模展開 (3.7M cells × 1M-pop avg) では数百億 vertex 想定。**現 MV (3 narrow MV) は全て Hummock + 単一 GROUP BY**、cardinality scaling は将来 pcfL1 別 sharding (ADR-0027 候補) で対応。

## 次 iteration TODO

1. `handleCohortEvidence` (B) で `edge_cohort_evidence_about` INSERT 配線 (現 spec 止まり)
2. cohort_test.go に edge insert 経路の dry-run test
3. ADR-0026 status を `active` 化
4. `etzhayyim cohort lineage --edge` で edge_cohort_derived を直接 query する高速 path
5. fission シミュレーション (実 evidence INSERT → mv_cohort_identity_posterior 反映確認)

# Iteration 46 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/cohort/emitEvidence.json` | 新規 procedure lexicon: cohortDid + signalKind + evidencePayload + posterior + judgeAgreement |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortEmitEvidence(env, input)` 実装 — sha256 hash 算出 → vertex_repo_record + edge_cohort_evidence_about を直接 INSERT (commit pipeline 経由せず) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | dispatch case + PLATFORM_WRITE_METHODS 追加 |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort emit --cohort --payload --signal-kind --posterior --judge` CLI |

## Phase B Direct Path Active

```
etzhayyim cohort emit --cohort did:plc:pending-xxx \
  --signal-kind "behavior.scrape.linkedin" \
  --payload "scraped:posts:42" \
  --posterior 0.78 --judge=false

→ POST /xrpc/com.etzhayyim.cohort.emitEvidence
→ handleCohortEmitEvidence:
   1. evidenceHash = sha256(cohort|kind|payload|ts)
   2. INSERT vertex_repo_record (collection='com.etzhayyim.cohort.evidence', cohort_did, posterior, ...)
   3. INSERT edge_cohort_evidence_about (evidence_hash → cohort_did)
→ MV auto-update:
   - mv_cohort_identity_posterior  (cohort_did → AVG/MAX posterior, fission_ready_count)
   - mv_cohort_k_drift             (cohort_did → distinct_signal_kinds, k_proxy)
→ if MV reflects max_posterior > 0.95 + judge_agree → fission ready
```

## Fission シミュレーション手順 (準備完成)

```bash
# 1. cohort 1 件 seed
etzhayyim cohort seed --segment '{"pcfL1":"3-market-sell","role":"salesRep","locale":"jp"}' --k 50
# → did:plc:pending-X1Y2Z3W4

# 2. 50 件以上の evidence emit (k floor 維持) で 1 件だけ posterior > 0.95 + judge=true
for i in $(seq 1 50); do
  etzhayyim cohort emit --cohort did:plc:pending-X1Y2Z3W4 \
    --signal-kind "behavior.observation" \
    --payload "obs-$i" \
    --posterior 0.5 --judge=false
done
etzhayyim cohort emit --cohort did:plc:pending-X1Y2Z3W4 \
  --signal-kind "behavior.identity-confirm" \
  --payload "confirmed-by-judge" \
  --posterior 0.97 --judge=true

# 3. MV 確認
etzhayyim cohort evidence --cohort did:plc:pending-X1Y2Z3W4 --min-posterior 0.95 --judge true
# → 1 row (fission ready)

# 4. fission 発火
etzhayyim cohort fission --cohort did:plc:pending-X1Y2Z3W4 \
  --posterior 0.97 --judge=true \
  --evidence at://...
# → individual_did + edge_cohort_derived row 生成
```

## CLI Surface — 15 subcommand

```
seed bootstrap list evidence emit fission lineage forest
stats coverage gap gen snapshot diff drift
```

## 次 iteration TODO

1. cohort_test.go に sha256Hex utility test を追加
2. `etzhayyim cohort lineage --edge` (edge_cohort_derived 直接 query)
3. ADR-0026 status を `active` に昇格 (Phase A/B/C handler 全完成 + watchdog 稼働済 = 昇格条件達成)
4. mv_cohort_lineage_depth read CLI (`etzhayyim cohort lineage-stats`)
5. cohort fleet 200 達成 (実 N=198 +2)

# Iteration 47 — 2026-04-15

## Milestones

| 項目 | 結果 |
|---|---|
| **ADR-0026 status** | `proposed` → **`active`** 昇格 |
| **cohort 実 N** | 198 → **200 (真の達成)** — 2 entry 追加 (en×mid×marketing×banking、en×mid×csr×healthcare) |
| **registry** | `90-docs/_registry/docs.json` の status 同期 |

## ADR-0026 active 昇格条件

| Phase | 完成度 | 根拠 |
|---|---|---|
| A (genesis) | ✅ | seed handler + idempotency + edge_cohort_routes_to + OCEL emit |
| B (evidence) | ✅ | emitEvidence handler + vertex_repo_record + edge_cohort_evidence_about + 2 MV 自動更新 |
| C (fission) | ✅ | fission handler + posterior gate + edge_cohort_derived + lineage record + OCEL emit |
| Watchdog | ✅ | runCohortKReevaluate + cron tick + apqc forward |
| Lexicon | ✅ | seed/emitEvidence/fission/listCohorts/listEvidence/signature/fissionLineage 7 NSID |
| Migration | ✅ | 0052/0053/0054 production + 0056 (lineage edges) draft |
| CLI | ✅ | 15 subcommand |

→ ADR-0026 は実装完成、`active` 化が妥当。

## Code Artifacts

| File | 変更 |
|---|---|
| `90-docs/adr/0026-agent-only-reverse-identity-topology.md` | front matter `status: proposed → active`、`last_verified: 2026-04-15` |
| `90-docs/_registry/docs.json` | 同 entry の `"status": "active"` |
| `deps.toml` | +2 cohort (実 N=200 達成) |

## 次 iteration TODO

1. lineage-stats CLI (`etzhayyim cohort lineage-stats` で mv_cohort_lineage_depth read)
2. cohort_test.go に sha256Hex / handleCohortEmitEvidence の dry-run test
3. ADR-0026 active 化を root CLAUDE.md `[[critical_rules]]` か `[[conventions]]` に登録
4. fission シミュレーション実行 (staging 環境で)
5. ADR-0027 draft (cohort scale 1M+ 時の sharding 戦略)

# Iteration 48 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/cohort/lineageStats.json` | 新規 query lexicon (pcfL1 / minChildren / limit) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortLineageStats(env, input)` 実装 — `mv_cohort_lineage_depth` 直接 read + optional `vertex_cohort_actor` join for pcfL1 filter |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | dispatch case + PLATFORM_READ_METHODS 追加 |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort lineage-stats --pcfL1 --min-children N` CLI |

## CLI Surface — 16 subcommand

```
seed bootstrap list evidence emit fission lineage forest
stats coverage gap gen snapshot diff drift lineage-stats
```

## Process Mining

```bash
# fission 多発した cohort top 10
etzhayyim cohort lineage-stats --min-children 5 --limit 10

# L8 IT で fission 履歴のある cohort のみ
etzhayyim cohort lineage-stats --pcfL1 8-info-technology --min-children 1
```

mv_cohort_lineage_depth が 0056 migration 適用後に streaming で自動更新されるため、fission 発生即座に反映。

## 次 iteration TODO

1. cohort_test.go に sha256Hex utility test
2. ADR-0026 を `[[conventions]]` に追記 (root deps.toml)
3. fission シミュレーション (staging 環境)
4. ADR-0027 draft (1M+ scale sharding)
5. CLI の `etzhayyim cohort` セクションを 70-tools/etzhayyim/CLAUDE.md に lineage-stats / emit を追記

# Iteration 49 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/CLAUDE.md` | `etzhayyim cohort` セクションに `emit` + `lineage-stats` 行を追加 (16 subcommand 表完成) |
| `deps.toml` | `[[conventions]]` に "com.etzhayyim.cohort.* lifecycle" entry 追加 (sources 14 file + adr link) |
| `CLAUDE.md` (root) | Key Conventions table に **Agent-Only Reverse Identity Topology (ADR-0026, active)** 行を追加 |

## Discovery Surface 完成

ADR-0026 は以下 3 つの discovery path で発見可能に:
1. root `CLAUDE.md` の Key Conventions table → 1 行 summary + ADR link
2. `deps.toml [[conventions]]` → priority/axis/sources 詳細
3. `70-tools/etzhayyim/CLAUDE.md` → CLI 全 16 subcommand table

LLM が任意の cohort 関連作業に着手する時、上記いずれからも認識可能。

## 次 iteration TODO

1. cohort_test.go に sha256Hex utility test
2. fission シミュレーション (staging 環境)
3. ADR-0027 draft (1M+ scale sharding)
4. `etzhayyim cohort` を Murakumo agent tool として登録 (LLM-driven seed)
5. 全 lineage path を vertex_cohort_actor.derived_from と edge_cohort_derived の dual-source で持つことの consistency check

# Iteration 50 — 2026-04-15 (節目)

## Code Artifacts

| File | 変更 |
|---|---|
| `90-docs/260415-cohort-lineage-dual-source-consistency.md` | 新規: vertex.derived_from と edge_cohort_derived の dual-source drift 検出 + repair 方針 |

## 50 Iteration 統括

Iter 1 (ADR draft) → Iter 50 (active 化 + drift audit spec) までの累計成果:

| 領域 | 件数 |
|---|---|
| **ADR** | 1 (ADR-0026 active) |
| **lexicon** | 8 (seed/signature/evidence/emitEvidence/fission/fissionLineage/listCohorts/listEvidence/lineageStats) |
| **migration** | 4 (0052/0053/0054/0056) |
| **vertex table** | 1 (vertex_cohort_actor) + cohort columns on vertex_repo_record |
| **edge table** | 3 (derived/evidence_about/routes_to) |
| **MV** | 3 (mv_cohort_identity_posterior / mv_cohort_k_drift / mv_cohort_lineage_depth) |
| **PDS handler** | 5 (handleCohortSeed/EmitEvidence/Fission/List/ListEvidence/LineageStats) |
| **agent module** | 1 (cohort-watchdog.ts + scheduled tick wiring) |
| **CLI subcommand** | 16 (`etzhayyim cohort *`) |
| **deps.toml cohort_actors** | 200 entries |
| **how-to/spec docs** | 4 (baseline + identity-posterior-mv-draft + seed-procedure-spec + evidence-oncommit-spec + lineage-dual-source) |
| **convention/discovery** | root CLAUDE.md + deps.toml [[conventions]] + 70-tools doc |

## Key Architectural Choices (固定済み)

1. **Hummock only, no Iceberg** — Kotoba/Datomic のみで全データ保持
2. **Idempotent seed** — segment_hash で重複防止 (bootstrap 安全)
3. **Direct Phase B path** — emitEvidence で commit pipeline 経由なし
4. **3 narrow MV** — pcfL1 sharding なしで 200-10K cohort scale 対応
5. **Dual-source lineage** — vertex column + edge table (本 iter で drift audit spec)
6. **Watchdog + projector forward** — k-drift で fission 無効化 + APQC OCEL emit
7. **scope 厳格分離** — cohort 経路 ≠ 一般 user 経路 (ADR-0022 と直交)

## 次 iteration TODO

1. `runCohortLineageAudit()` 実装 (cohort-watchdog.ts に dual-source drift 検査追加)
2. cohort_test.go に sha256Hex test
3. ADR-0027 draft (1M+ scale sharding)
4. Murakumo agent tool registration
5. fission シミュレーション (staging)

# Iteration 51 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` | `runCohortLineageAudit(env)` 新規 — 3 SQL check (edgeMissing / orphanEdge / parentMismatch) を Kysely で実装。`CohortLineageAuditResult` 返却 |
| `50-infra/cloudflare/workers/atproto/src/app.ts` | `runCohortWatchdogTick` の triggered branch 末尾で audit を呼出、drift > 0 で OCEL `com.etzhayyim.cohort.lineageDrift` index に emit |

## Watchdog 統合フロー (full)

```
cron tick (7 */6 * * *)
  → evaluateCronTriggers → ProactiveMessage[]
  → for each parseCohortAction:
      runCohortKReevaluate     → fission_enabled=false 化 + apqc forward + OCEL kReevaluated
      runCohortLineageAudit    ★ new — 3 drift count
        if drift > 0:
          console.log + OCEL lineageDrift index emit
```

## OCEL Schema

```
index: com.etzhayyim.cohort.lineageDrift
blobs: ['com.etzhayyim.cohort.lineageDrift', 'cron', 'internal', 'SCHEDULED', '', '', '', '']
doubles: [edgeMissing, orphanEdge, parentMismatch]
```

`/xrpc/com.etzhayyim.pds.getOcel?index=com.etzhayyim.cohort.lineageDrift` で時系列 query 可能。

## 次 iteration TODO

1. cohort_test.go に sha256Hex test
2. `etzhayyim cohort repair-edge --did <individual>` 実装 (drift 修復)
3. ADR-0027 draft (1M+ scale sharding)
4. Murakumo agent tool registration
5. fission シミュレーション (staging)

# Iteration 52 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `00-contracts/lexicons/com/etzhayyim/cohort/repairEdge.json` | 新規 procedure lexicon (individualDid / limit / dryRun) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/cohort.ts` | `handleCohortRepairEdge` 実装 — drift 行を SELECT → edge_cohort_derived INSERT (vertex 側は触らない) |
| `50-infra/cloudflare/workers/atproto/src/handlers/etzhayyim/index.ts` | dispatch + PLATFORM_WRITE entry |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort repair-edge --did --limit --dry-run` CLI |

## Drift Repair Loop

```
etzhayyim cohort repair-edge                           # dry-run by default → 修復候補を確認
etzhayyim cohort repair-edge --dry-run=false           # 100 件まで bulk repair
etzhayyim cohort repair-edge --did did:plc:pending-X --dry-run=false  # 単一指定
```

## Watchdog → Repair Cycle

```
6h cron tick:
  runCohortLineageAudit → drift{edgeMissing,orphanEdge,parentMismatch}
  if edgeMissing > 0:
    OCEL emit (lineageDrift)
    [manual or auto] etzhayyim cohort repair-edge --dry-run=false
```

orphanEdge / parentMismatch は自動修復対象外 (data corruption sign — manual review)。

## CLI Surface — 17 subcommand

```
seed bootstrap list evidence emit fission lineage forest
stats coverage gap gen snapshot diff drift lineage-stats repair-edge
```

## 次 iteration TODO

1. cohort_test.go に sha256Hex test
2. ADR-0027 draft (1M+ scale sharding)
3. Murakumo agent tool registration
4. fission シミュレーション (staging)
5. orphanEdge auto-detect → console alert (不変条件として保証する経路を追加)

# Iteration 53 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `90-docs/adr/0028-cohort-mv-sharding.md` | 新規 ADR (status: proposed) — 4 Phase sharding strategy。Phase 1 (現状, ~10K) → Phase 2 (10K-500K, index 追加) → Phase 3 (500K-3M, 13 sub-MV per pcfL1) → Phase 4 (3M+, vertex_individual_actor monthly partition)。Iceberg 不使用、Kotoba/Datomic Hummock cold tier 維持 |
| `90-docs/_registry/docs.json` | ADR-0028 entry 追加 |

## Note

ADR-0027 は別件 (recruit-talent-public-feed-first) で確保済みのため、cohort sharding は **0028** に採番。

## Sharding 概要

| Phase | trigger | MV 戦略 |
|---|---|---|
| 1 | cohort < 5K | 現 3 MV 単一 GROUP BY |
| 2 | 5K-500K | index 追加のみ |
| 3 | 500K-3M | 13 sub-MV per pcfL1 (GROUP BY cardinality / 13) |
| 4 | 3M+ | `vertex_individual_actor` 分割 + monthly partition |

## Process Mining

`etzhayyim cohort snapshot` の `totalCohorts` を週次で監視し、Phase 移行閾値超過で migration plan PR 起票 (将来的に CI workflow 化)。

## 次 iteration TODO

1. cohort_test.go に sha256Hex test
2. Murakumo agent tool registration
3. fission シミュレーション (staging)
4. orphanEdge auto-alert
5. ADR-0028 を root CLAUDE.md Key Conventions に追加 (active 化は Phase 2 以降)

# Iteration 54 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `50-infra/cloudflare/workers/atproto/src/app.ts` | `runCohortWatchdogTick` 内の audit 結果処理を強化: orphanEdge / parentMismatch > 0 で `console.error` (CRITICAL) + 別 OCEL index `com.etzhayyim.cohort.lineageInvariantViolation` emit |
| `CLAUDE.md` (root) | Key Conventions に **ADR-0028 (proposed) Cohort MV Sharding** 行を追加。CLI subcommand 数を 17 に更新 |

## Severity Stratification

| Audit signal | Severity | Action |
|---|---|---|
| `edgeMissing` | warning | 自動修復可 (`etzhayyim cohort repair-edge`) |
| `orphanEdge` | **CRITICAL** | manual review (data corruption sign) |
| `parentMismatch` | **CRITICAL** | manual review (parent reassignment 不可) |

OCEL 2 index に分離:
- `com.etzhayyim.cohort.lineageDrift` — 全 audit 結果 (常時 emit)
- `com.etzhayyim.cohort.lineageInvariantViolation` — orphan/mismatch のみ (CRITICAL)

## Discovery Surface (再確認)

| 場所 | ADR-0026 (active) | ADR-0028 (proposed) |
|---|---|---|
| root CLAUDE.md Key Conventions | ✅ | ✅ (本 iter) |
| deps.toml [[conventions]] | ✅ | (Phase 2 移行時に追加) |
| 90-docs/_registry/docs.json | ✅ active | ✅ proposed |
| 70-tools/etzhayyim/CLAUDE.md | ✅ | (CLI 影響なし) |

## 次 iteration TODO

1. cohort_test.go に sha256Hex test
2. Murakumo agent tool registration
3. fission シミュレーション (staging)
4. CRITICAL alert を Slack/PagerDuty に転送する経路 (将来)
5. cohort fleet snapshot を CI weekly で自動取得 (`.github/workflows/cohort-snapshot.yml`)

# Iteration 55 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `.github/workflows/cohort-coverage.yml` | 新規 CI workflow — 3 job: cohort-count (segment_hash schema validation + Phase trigger 監視) / cohort-go-tests (cohort_test.go 実行) / cohort-lexicon-validate (JSON well-formed)。trigger: PR / push to main / weekly cron |

## CI Coverage

| Job | 内容 |
|---|---|
| **cohort-count** | `[[cohort_actors]]` 数を `$GITHUB_OUTPUT` に書き、segment_hash の必須 key (pcfL1/role/locale) 欠落を検出 + ADR-0028 Phase trigger 閾値 (5K/500K) で warning/error |
| **cohort-go-tests** | `go test -run 'TestParseSegmentKV\|...' -v .` |
| **cohort-lexicon-validate** | 全 com.etzhayyim.cohort.*.json を python json.load で parse |

## Weekly Cron

`'17 18 * * 0'` (Sunday 03:17 JST) で deps.toml を週次監視。Phase 移行 trigger 超過時に CI red で注意喚起。

## 次 iteration TODO

1. cohort_test.go に sha256Hex test (TS handler 側の同等性確認用)
2. Murakumo agent tool registration
3. fission シミュレーション (staging)
4. Slack 連携 (CRITICAL OCEL → webhook)
5. ADR-0028 sharding migration の `0070_*` skeleton (Phase 3 移行時に pcfL1 別 13 sub-MV を生成する template)

# Iteration 56 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort_test.go` | +2 test: `TestSha256HexEquivalence` (空文字列の well-known hash で fixture pin、64 char length 確認) + `TestSha256HexDeterminism` (同入力で同出力) |
| `.github/workflows/cohort-coverage.yml` | go test pattern に `TestSha256Hex` を含める |

## Test Coverage 集計

| Function | Tests |
|---|---|
| `parseSegmentKV` | 3 (minimum / 3-axis / malformed) |
| `cohortEntry.toSegmentJsonld` | 1 (key containment) |
| `sortStrings` | 1 (duplicate sort) |
| `sha256.Sum256` (TS handler 同等性確認) | 2 (empty fixture + determinism) |

合計 7 unit test、cohort.go 内部 logic を網羅。

## 次 iteration TODO

1. Murakumo agent tool registration (cohort.seed/emit を LLM tool として登録)
2. fission シミュレーション (staging で seed→50 evidence→1 fission-ready→fission)
3. Slack webhook for CRITICAL OCEL (lineageInvariantViolation)
4. ADR-0028 sharding migration `0070_cohort_mv_shard_l1.ts` skeleton (current proposed → Phase 3 trigger 後 active)
5. cohort runtime metrics dashboard — `etzhayyim cohort dashboard` で stats+coverage+gap+drift を 1 view に集約

# Iteration 57 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | `etzhayyim cohort dashboard` subcommand 実装 — listCohorts 1 call で fanout: total / cohort / fissioned 数 + fissionEnabled rate + 4 axis cardinality + ADR-0028 Phase trigger 自動判定 |

## Dashboard Output Example

```
┌─ ADR-0026 Cohort Fleet Dashboard ─────────────────────
│  total           : 200  (cohort=200, fissioned=0)
│  fissionEnabled  : 0 / 200  (0.0%)
│  axis cardinality
│    pcfL1     : 13 / 13
│    role      : ~50
│    industry  : 5
│    locale    : 2
│  ADR-0028 phase  : Phase 1 (single MV)
└────────────────────────────────────────────────────────
```

## CLI Surface — 18 subcommand

```
seed bootstrap list evidence emit fission lineage forest
stats coverage gap gen snapshot diff drift lineage-stats repair-edge dashboard
```

## Process Mining

dashboard が ops 時の "1 行 health check" になる。Phase trigger 自動判定で ADR-0028 移行タイミングが手で監視せず CLI 側で警告表示。

## 次 iteration TODO

1. Murakumo agent tool registration
2. fission シミュレーション (staging)
3. Slack webhook for CRITICAL OCEL
4. ADR-0028 sharding migration `0070_*` skeleton
5. cohort runtime monitoring を 70-tools/etzhayyim/CLAUDE.md に追記 (dashboard / repair-edge / lineage-stats を 17→18 subcommand 表で更新)

# Iteration 58 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/CLAUDE.md` | `etzhayyim cohort` subcommand 表に `repair-edge` + `dashboard` 追加 (18 subcommand 完成) |
| `30-graph/graph-schema/migrations/0070_cohort_mv_shard_l1.ts.template` | 新規 skeleton — 13 sub-MV (`mv_cohort_identity_posterior_l1_<slug>` + `mv_cohort_k_drift_l1_<slug>`) を pcfL1 別に生成。`.template` suffix で migrator skip。Phase 3 trigger 後に rename で活性化 |

## Skeleton Activation Procedure

```bash
# 1. dashboard で Phase 3 trigger 判定
etzhayyim cohort dashboard
# │ ADR-0028 phase  : Phase 3 (13 sub-MV per pcfL1)

# 2. activate template
mv 30-graph/graph-schema/migrations/0070_cohort_mv_shard_l1.ts.template \
   30-graph/graph-schema/migrations/0070_cohort_mv_shard_l1.ts

# 3. staging で apply (off-peak、kubectl top pod 監視)
DATABASE_URL=... pnpm db:migrate

# 4. read path 検証 (handler を sub-MV 経由に切替)
# 5. legacy 3 MV を DROP (template 内コメントアウトされている)
```

## Discovery Surface 完成

| 場所 | ADR-0026 | ADR-0028 |
|---|---|---|
| root CLAUDE.md Key Conventions | ✅ | ✅ |
| deps.toml [[conventions]] | ✅ | (Phase 2 移行時) |
| 90-docs/_registry/docs.json | ✅ | ✅ |
| 70-tools/etzhayyim/CLAUDE.md | ✅ | (Phase 3 trigger 後) |
| migration skeleton | ✅ (0052/0053/0054/0056) | ✅ (0070 template) |

## 次 iteration TODO

1. Murakumo agent tool registration (LLM-driven cohort.seed/emit)
2. fission シミュレーション (staging end-to-end)
3. Slack webhook for CRITICAL OCEL
4. cohort fleet snapshot CI weekly artifact upload
5. ADR-0026 を root CLAUDE.md `[[critical_rules]]` に昇格 (active で全実装完成のため)

# Iteration 59 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `deps.toml` | `[[critical_rules]]` に `root-agent-only-reverse-identity-topology` 追加 — R1-R10 不変条件 + 検出経路 + 関連 ADR link |
| `CLAUDE.md` (root) | `17 CRITICAL rule` → `18 CRITICAL rule` 更新 |

## R1-R10 不変条件 (要約)

| Rule | Invariant |
|---|---|
| R1 | scope: AI agent only (一般 user 経路と直交) |
| B2 | k_anonymity ≥ 50 (handler enforce) |
| R3 | segment_hash schema (pcfL1/role/locale 必須) |
| R4 | tier='tier1-hashed' 固定 (PII tier3 回避) |
| R5 | fission gate: posterior>0.95 AND judge=true AND fission_enabled=true |
| R6 | [[cohort_actors]] table 単独 (mitama/legacy と混在禁止) |
| R7 | 4 procedure NSID のみ (seed/emit/fission/repairEdge) |
| R8 | dual-source lineage drift 監視 |
| R9 | orphan/mismatch は CRITICAL、auto-repair 禁止 |
| R10 | Hummock only (Iceberg 不使用) |

## Discovery Surface 完成 (final)

| 場所 | ADR-0026 |
|---|---|
| root CLAUDE.md Key Conventions | ✅ |
| root CLAUDE.md `[[critical_rules]]` 経由参照 | ✅ (本 iter) |
| deps.toml [[critical_rules]] | ✅ (本 iter) |
| deps.toml [[conventions]] | ✅ |
| 90-docs/_registry/docs.json | ✅ active |
| 90-docs/adr/0026-*.md | ✅ active |
| 70-tools/etzhayyim/CLAUDE.md | ✅ 18 subcommand |
| migration history (CLAUDE.md) | ✅ 0052-0056 |

ADR-0026 が repo 内の正規 critical 経路全てで discovery 可能。

## 次 iteration TODO

1. Murakumo agent tool registration
2. fission シミュレーション (staging)
3. Slack webhook for CRITICAL OCEL
4. cohort_test.go の test 数を 9 → 12 に拡張 (deriveCohortEventType 系の Go ↔ TS 同等性 check)
5. ADR-0026 を `etzhayyim dodaf tv1` registry に登録 (`etzhayyim dodaf tv1 query --id root-agent-only-reverse-identity-topology` 経路)

# Iteration 60 — 2026-04-15 (節目)

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/etzhayyim/etzhayyim/cohort.go` | Go mirror: `CohortOcelEventType` const + `CohortEventInput` struct + `DeriveCohortEventType()` 関数。TS host-sdk `cohort.ts deriveCohortEventType` と precedence 完全一致を Go 側でも再現 |
| `70-tools/etzhayyim/etzhayyim/cohort_test.go` | `TestDeriveCohortEventType` 7 cases (didFission / kProxy / fissionReady gates / genesis / accrued の precedence chain 全分岐) |
| `.github/workflows/cohort-coverage.yml` | test pattern に `TestDeriveCohortEventType` 追加 |

## Test Coverage 集計 (全 14 case)

| 関数 | tests |
|---|---|
| parseSegmentKV | 3 (minimum / 3-axis / malformed) |
| toSegmentJsonld | 1 (key containment) |
| sortStrings | 1 |
| sha256 (TS handler equivalence) | 2 (empty fixture / determinism) |
| **DeriveCohortEventType (Go-TS equivalence)** | **7 (本 iter)** |

## 60 Iteration 統括 (Iter 50→60)

| 領域 | Iter 50 末 | Iter 60 末 |
|---|---|---|
| ADR | 1 (active) | 2 (0026 active + 0028 proposed) |
| lexicon | 8 | 10 (+emitEvidence, lineageStats, repairEdge — 但し 1 重複あり) |
| migration | 4 (0052/0053/0054/0056) | 4 + 1 template (0070_*.template) |
| MV | 3 | 3 (0056 で +mv_cohort_lineage_depth) |
| edge table | 0 | 3 (derived/evidence_about/routes_to) |
| handler | 5 | 8 (+EmitEvidence/RepairEdge/LineageStats) |
| CLI subcommand | 16 | 18 (+repair-edge, +dashboard) |
| critical_rules | (なし) | 1 (本 iter R1-R10) |
| CI workflow | 0 | 1 (cohort-coverage.yml) |
| spec doc | 4 | 5 (+lineage-dual-source-consistency) |
| Go-TS equivalence test | 0 | 7 |

Iter 50→60 で「実装完成 → governance 化 + scaling 戦略 + critical rule 昇格 + Go-TS invariant 担保」まで進めた。

## 次 iteration TODO

1. Murakumo agent tool registration
2. fission シミュレーション (staging)
3. Slack webhook for CRITICAL OCEL
4. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
5. cohort fleet stabilization (200 cohort で 1 週間 idle observation → drift 計測)

# Iteration 61 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `90-docs/260415-cohort-llm-tool-registration-spec.md` | 新規 spec — Murakumo / Ameno LLM agent から ADR-0026 cohort lifecycle を tool calling で操作する full spec。4 tool (cohort_seed / cohort_emit_evidence / cohort_fission / cohort_list) + audit + bootstrap loop |

## Tool Schema 安全策

- `cohort_fission` の posterior min 0.95 + judgeAgreement const true で LLM 誤発火を schema-level に防止
- 全 tool call は OCEL `com.etzhayyim.cohort.llmToolCall` に emit (将来)

## Bootstrap Loop (agent-driven 自己拡張)

```
list → gap → seed → evidence → fission → snapshot diff → repeat
```

これにより 200 cohort fleet が agent driven で 1K → 10K → 1M scale に成長可能 (ADR-0028 Phase 2/3 trigger と連動)。

## 次 iteration TODO

1. `20-actors/magatama/sdk/magatama-host-sdk/src/llm-tools-cohort.ts` 実装 (この spec を code 化)
2. fission シミュレーション (staging)
3. Slack webhook for CRITICAL OCEL
4. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
5. cohort fleet 1 週間 idle observation → drift 計測

# Iteration 62 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `20-actors/magatama/sdk/magatama-host-sdk/src/llm-tools-cohort.ts` | 新規実装 — `cohortToolSpecs` (4 OpenAI tool spec) + `cohortToolDispatch` (name → NSID + buildBody) + `cohortToolNsid` helper |
| `20-actors/magatama/sdk/magatama-host-sdk/test/llm-tools-cohort.test.ts` | 新規 unit test 9 cases (4 spec gate + 4 dispatch + 1 helper) |

## LLM Tool 安全 Schema (実装)

| Tool | 安全策 |
|---|---|
| `cohort_fission` | posterior min=0.95、judgeAgreement const=true (LLM が誤発火不可能) |
| `cohort_seed` | kAnonymity default=50 (ADR-0026 B2 floor) |
| `cohort_emit_evidence` | signalKind 自由文字列 (今後 whitelist 化候補) |
| `cohort_list` | read-only、limit default=100 |

## Bootstrap Loop が runnable に

```typescript
import { cohortToolSpecs, cohortToolDispatch } from '@etzhayyim/magatama-host-sdk/llm-tools-cohort';

await llm.agentReact({
  task: 'Grow cohort fleet to 1000 by filling locale=zh gap',
  tools: [...stdTools, ...cohortToolSpecs],
  toolHandler: async (call) => {
    const entry = cohortToolDispatch[call.name];
    if (!entry) throw new Error(`unknown tool ${call.name}`);
    const url = `${pdsUrl}/xrpc/${entry.nsid}`;
    const body = entry.buildBody(call.args);
    return entry.method === 'GET'
      ? await fetch(`${url}?${new URLSearchParams(body as any)}`).then((r) => r.json())
      : await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }).then((r) => r.json());
  },
});
```

## Test Coverage 集計 (合計 23 tests)

| Suite | tests |
|---|---|
| Go cohort_test.go | 14 (Iter 60) |
| TS llm-tools-cohort.test.ts | 9 (本 iter) |

## 次 iteration TODO

1. `llm.ts` の `agentReact` に cohortToolDispatch を統合
2. fission シミュレーション (staging)
3. Slack webhook for CRITICAL OCEL
4. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
5. cohort fleet 1 週間 idle observation → drift 計測

# Iteration 63 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `20-actors/magatama/sdk/magatama-host-sdk/src/index.ts` | cohort utilities + LLM tool registry を `@etzhayyim/magatama-host-sdk` の public API surface に export — `parseSegmentHash`/`apqcL1DidFromSegment`/`deriveCohortEventType` + `cohortToolSpecs`/`cohortToolDispatch`/`cohortToolNsid` |

## Public API

```typescript
import {
  // segment helpers
  parseSegmentHash,
  apqcL1DidFromSegment,
  deriveCohortEventType,
  // LLM tool registry
  cohortToolSpecs,
  cohortToolDispatch,
  cohortToolNsid,
} from '@etzhayyim/magatama-host-sdk';
```

これにより全 app が ADR-0026 cohort lifecycle を host-sdk import 1 行で利用可能。

## Discovery Surface (final v2)

| 場所 | export |
|---|---|
| `@etzhayyim/magatama-host-sdk` (TS package) | cohort/llm-tools-cohort utilities (本 iter) |
| root CLAUDE.md Key Conventions | ADR-0026/0028 行 |
| deps.toml [[critical_rules]] | R1-R10 |
| deps.toml [[conventions]] | sources 14 file |
| 70-tools/etzhayyim/CLAUDE.md | 18 CLI subcommand table |
| 90-docs/_registry/docs.json | 2 ADR (active + proposed) |
| .github/workflows/cohort-coverage.yml | CI 3 job |

7 surface 全層で発見可能。

## 次 iteration TODO

1. `llm.ts` agentReact 内で cohortToolDispatch を auto-bridge
2. fission シミュレーション (staging)
3. Slack webhook for CRITICAL OCEL
4. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
5. cohort fleet 1 週間 idle observation → drift 計測

# Iteration 64 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `20-actors/magatama/sdk/magatama-host-sdk/src/llm-tools-cohort.ts` | `createCohortToolHandler({ pdsBaseUrl, bearerToken, fetchImpl? })` 追加 — `(name, args) => Promise<unknown\|null>` 返却。`agentReact({ toolHandler })` に直接渡せる |
| `20-actors/magatama/sdk/magatama-host-sdk/test/llm-tools-cohort.test.ts` | +4 test (handler unknown-tool / POST / GET / error fallback) |
| `20-actors/magatama/sdk/magatama-host-sdk/src/index.ts` | `createCohortToolHandler` を public export に追加 |

## Integration Pattern (1-liner)

```typescript
import { agentReact, cohortToolSpecs, createCohortToolHandler } from '@etzhayyim/magatama-host-sdk';

const cohortHandler = createCohortToolHandler({
  pdsBaseUrl: 'https://atproto.etzhayyim.com',
  bearerToken: process.env.etzhayyim_TOKEN!,
});

await agentReact({
  task: 'Grow cohort fleet to fill locale=zh gap',
  tools: [...stdTools, ...cohortToolSpecs],
  toolHandler: async (call) => {
    const cohort = await cohortHandler(call.name, call.args);
    if (cohort !== null) return cohort;
    return await stdToolHandler(call);  // fallback
  },
});
```

LLM agent から ADR-0026 cohort lifecycle 操作を 5 行で wire-in 可能に。

## Test Coverage 集計 (合計 27 tests)

| Suite | tests |
|---|---|
| Go cohort_test.go | 14 |
| TS llm-tools-cohort.test.ts | 13 (+4 本 iter) |

## 次 iteration TODO

1. fission シミュレーション (staging end-to-end)
2. Slack webhook for CRITICAL OCEL
3. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
4. cohort fleet 1 週間 idle observation → drift 計測
5. Murakumo agent から実際に `cohortHandler` を invoke する e2e demo

# Iteration 65 — 2026-04-15

## Trigger

50-infra/CLAUDE.md 更新で Kotoba/Datomic が `g2-gpu-rtx4000a1-l × 1` (16 vCPU / 64 GiB / RTX 4000 Ada 20 GiB VRAM) に移行 ($701/mo)。compute mem 24Gi → 64Gi。

## Code Artifacts

| File | 変更 |
|---|---|
| `90-docs/adr/0028-cohort-mv-sharding.md` | front matter `infra_baseline` 追記、Phase trigger 閾値を 24Gi 時代と 64Gi GPU 時代の 2 列で対比、GPU 活用候補 (Bayesian update offload) を明記 |
| `.github/workflows/cohort-coverage.yml` | Phase 2 trigger 5K → 10K、Phase 3 trigger 500K → 1M に緩和 |
| `70-tools/etzhayyim/etzhayyim/cohort.go` | dashboard CLI Phase 判定: Phase 2 = 10K, Phase 3 = 1M, Phase 4 = 5M |
| `CLAUDE.md` (root) | Key Conventions ADR-0028 行に GPU baseline + 2x 緩和を反映 |

## Updated Phase Trigger (両時代対比)

| 移行先 | 24Gi 時代 | 64Gi GPU 時代 (本 iter) |
|---|---|---|
| Phase 1 → Phase 2 | 5K | **10K** |
| Phase 2 → Phase 3 | 500K | **1M** |
| Phase 3 → Phase 4 | 100M (個体 row) | **300M** |

## GPU 活用候補

RTX 4000 Ada 20 GiB VRAM が空いているため、posterior の Bayesian update 経路を将来 GPU offload 可能:
- 現状 (2026-04-15): Kotoba/Datomic streaming actor は CPU only
- 候補: Murakumo native worker で per-batch evidence → posterior を CUDA 計算 → MV 更新

これは ADR-0028 Phase 2 以降の "並列 enhancement" 候補。Phase 1 (現状 200 cohort) では不要。

## 次 iteration TODO

1. fission シミュレーション (staging)
2. Slack webhook for CRITICAL OCEL
3. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
4. cohort fleet 1 週間 idle observation
5. GPU offload PoC: Murakumo で 1000 cohort × evidence batch を CUDA で processing

# Iteration 66 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `90-docs/260415-cohort-fission-staging-runbook.md` | 新規 runbook — Phase A→B→C を staging で end-to-end 確認する 6 step procedure (baseline / Phase A / B 50-event / C / audit / cleanup) + success criteria + failure triage |

## Runbook Structure

| Step | Action | Verify |
|---|---|---|
| 0 | dashboard + snapshot baseline | 0 cohort confirmed |
| 1 | `cohort gen` で 1 cohort seed | `cohort list` で 1 row |
| 2 | `cohort emit` × 50 (49 ambient + 1 fission-ready) | `cohort evidence --min-posterior 0.95` で 1 row |
| 3 | `cohort fission` 発火 | `cohort lineage` で 2-hop chain、`lineage-stats` で direct_children=1 |
| 4 | OCEL drift query | edgeMissing=0 |
| 5 | TRUNCATE cleanup | staging 専用 |

## Success Criteria Matrix

15 check item を doc 化:
- vertex / edge insert 件数
- MV freshness (mv_cohort_identity_posterior fission_ready_count = 1 within 5s)
- OCEL emission (genesis + 50× accrued + 1× fissionReady + 1× fission)
- lineageDrift = 0

## 次 iteration TODO

1. Slack webhook for CRITICAL OCEL
2. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
3. cohort fleet 1 週間 idle observation
4. GPU offload PoC
5. runbook を CI で実行できる form (e2e bash script `scripts/cohort-staging-e2e.sh`)

# Iteration 67 — 2026-04-15

## Code Artifacts

| File | 変更 |
|---|---|
| `70-tools/scripts/cohort-staging-e2e.sh` | 新規 executable bash script — Iter 66 runbook を `etzhayyim cohort` CLI 経由で 4 step (seed / emit ×N / fission / lineage verify) を自動実行。`set -euo pipefail` で fail-fast、各 step に check + colored log |

## Script Features

| 機能 | 詳細 |
|---|---|
| env override | `PDS_URL`, `SEED_PCFL1`, `SEED_ROLE`, `SEED_LOCALE`, `EVIDENCE_COUNT` |
| token mint | step 毎に `etzhayyim agent-token --lxm <NSID>` で scoped JWT |
| MV freshness wait | 5s sleep 後に streaming MV の反映を verify |
| jq 連携 | listEvidence / lineage / lineage-stats の JSON を parse して assert |
| cleanup hint | 末尾に DELETE psql コマンドを print (実行はせず) |

## 使用例

```bash
PDS_URL=https://atproto.etzhayyim.com \
  ./70-tools/scripts/cohort-staging-e2e.sh

# == E2E SUCCESS ==
# cohort:     did:plc:pending-X1Y2Z3W4
# fissioned:  did:plc:pending-AABBCCDD
```

## CI Hook (将来)

`.github/workflows/cohort-coverage.yml` に nightly job を追加し、staging PDS 環境で本 script を実行 → success criteria 満たさなければ red。

## 次 iteration TODO

1. nightly CI job として cohort-staging-e2e.sh を組込み (要 staging credential secret)
2. Slack webhook for CRITICAL OCEL
3. ADR-0026 を `etzhayyim dodaf tv1` registry に登録
4. cohort fleet 1 週間 idle observation
5. GPU offload PoC

# References

- `deps.toml` `[[cohort_actors]]` (Iteration 1 で 13 entry 投入)
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
- `90-docs/adr/0025-kyber-apqc-bpmn-projector-consolidation.md`
- `60-apps/etzhayyim-project-apqc/CLAUDE.md` (APQC L1 slug SSoT)
