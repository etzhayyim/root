---
id: adr-2605081200-spiffworkflow-bpmn-engine-replacement
title: SpiffWorkflow を Zeebe 後継 BPMN engine とする (Kotoba/Datomic-native, code-as-data)
status: active
doc_type: adr
topic: workflow-engine
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - workflow-engine-selection
  - bpmn-runtime
  - spiffworkflow-runtime
  - BPMN-native worker path alongside LangGraph Server main runtime
  - zeebe-replacement-runbook
related:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2604282300
  - 90-docs/adr/0056-bpmn-as-actor.md
  - 90-docs/adr/0036-worker-direct-hyperdrive-persistence.md
  - 90-docs/adr/0094-kotoba-stable-three-node-topology.md
  - 90-docs/260424-bsky-compat-kotoba-split.md
supersedes: []
superseded_by: []
---

# Context

現状の workflow runtime は **Camunda Zeebe (Camunda 8)** を broker、`pyzeebe` を Python worker SDK として `mitama-udf-pool` namespace で運用している (`50-infra/k8s/{open-lei-mcp,intel-dependency-worker,claim-consumer-actor,livecam-vision-actor,comfyui-generation-actor,shigotoba-jobs-actor,smishing-actor}` の 7 worker、合計 100–300 inst/s 規模)。

問題:

1. **License**: Camunda 8 (Zeebe) は **Camunda Self-Managed License** で商用本番利用に有償ライセンスが必要。Camunda 7 CE は 2025-10-11 で community サポート終了済 (新規採用不可)。
2. **broker 重量**: Zeebe broker pod は JVM + RocksDB partition で常駐数百 MB〜GiB を占め、`mitama-udf-pool` の compute floor (`vhf-16c-58gb × 2`) を圧迫する。
3. **データ層二重化**: Zeebe は RocksDB を内部 state とし、別途 Kotoba/Datomic に解析データを書く。**ADR-0036 (Worker-direct Hyperdrive Persistence) と record-log semantics (`90-docs/260424-bsky-compat-kotoba-split.md`)** の "RW を SSoT、UPDATE 禁止、delete-then-insert、MST なし" 規約と engine 内部状態が分離している。
4. **pyzeebe watchdog hazard**: `50-infra/CLAUDE.md` に既知の "pyzeebe asyncio loop starvation → false restart" issue が記録済。SDK 構造由来の問題で根本回避できない。

**code-as-data deploy + worker pull 型 + Kotoba/Datomic を data 層** の前提を維持しつつ、license-clean な BPMN engine が必要。代替評価は `[knowledge.bpmn-engine-alternatives-20260508]` (deps.toml 候補) で実施し、SpiffWorkflow / DBOS Transact / bpmn-engine / Flowable / Camunda 7 CE / Temporal / Conductor / RW-native custom interpreter を比較した。

# Decision

**SpiffWorkflow (LGPL-3.0, sartography/SpiffWorkflow) を Zeebe 後継 BPMN engine として採用する。** Engine 本体のみを Python library として `mitama-udf-pool` の worker pod に in-process 同梱し、`spiff-arena` の REST runtime は使わない。State 永続層は **Kotoba/Datomic のみ** (ADR-0036 / record-log semantics 準拠、UPDATE / ON CONFLICT 不使用)。

ADR-2605080600 により、L3 actor runtime の main path は LangGraph Server +
Granian とする。本 ADR の SpiffWorkflow path はそれと競合しない。BPMN XML が
業務・監査・運用レビューの正本である flow、または timer / boundary event /
process diagram が価値を持つ flow は、LangGraph node 化せず SpiffWorkflow
BPMN worker で実行する。

## Architecture

```
BPMN XML (com.etzhayyim.bpmn.process AT record collection, code-as-data)
    │ deploy = AT record commit
    ▼
graphar.vertex_bpmn_process (RW, append-only, latest version = MAX(deployed_at))
    │
    │ instance create
    ▼
graphar.vertex_spiff_instance (1 row = 1 instance, state_json = SpiffWorkflowSerializer JSON)
    │
    │ MV 導出
    ▼
graphar.mv_spiff_ready_jobs ──pull──→ pyzeebe-shim worker pool (existing 7 workers)
    │                                          │
    │                                          │ complete/fail
    │ delete-then-insert state                 ▼
    └──────────────────── engine host (`bpmn-engine-host` Deployment, Python)
                          (Spiff `do_engine_steps()` only)

graphar.vertex_spiff_history (append-only, → Iceberg archive)
graphar.vertex_spiff_timer (instance_id, fire_at, 1s tick reconciler)
```

- **Engine host** = 新規 `etzhayyim-root/50-infra/k8s/bpmn-engine-host/` Deployment (Python 3.12 + SpiffWorkflow)。replica 1 active + 1 standby (active-standby、shard 分割は Phase 3 で評価)。
- **Persistence**: `vertex_spiff_instance` への state write は **delete-then-insert** (1 row 単位、PK = `instance_id`)。`db.transaction()` は RW で no-op として扱う (root CLAUDE.md "Record-log semantics" 規約)。
- **Job dispatch**: engine が `READY` task を `vertex_spiff_job` に append、worker は `mv_spiff_ready_jobs` を 5s polling もしくは RW subscribe で pull。`claim_until` lease column で at-least-once。
- **Worker shim**: `etzhayyim_bpmn` decorator package を `40-engine/kotoba/crates/kotoba-kotodama/sdk/` 配下に新設し、`@worker.task(task_type="...")` 互換 API を提供。既存 handler 関数本体は無改修。
- **Deploy = AT record**: BPMN XML を `com.etzhayyim.bpmn.process` collection に commit (Worker-direct Hyperdrive、ADR-0036)。engine host は firehose (or RW notification) で hot-reload。
- **Timer**: `vertex_spiff_timer` を 1s tick reconciler で照会し、`fire_at <= now()` を engine に inject。
- **Archive**: 完了 instance の `vertex_spiff_history` を Iceberg sink (既存 RW B2 path) で長期保存。

## 数字設計 (capacity baseline, c2-standard-4 同等 / Python 3.12)

| 指標 | 値 | 備考 |
|---|---|---|
| `do_engine_steps()` 1 token | 0.3–0.8 ms | in-process |
| serialize (JSON, 30-task spec) | 0.5–2 ms | SpiffWorkflowSerializer |
| RW persist (delete + insert) | 4–8 ms | Hyperdrive 1-RTT |
| End-to-end token transition | **5–11 ms** | 支配項 = persist |
| Throughput / 単機 (1 process) | ~150 inst/s | GIL 制約 |
| Throughput / 単機 (worker × 8) | **~1.0–1.2k inst/s** | multiprocessing |
| RAM / 1k live instance | ~150 MB | engine state JSON |
| Cold start | 1.5 s | spec parse 含む |
| Persisted state size / instance | **5.7–8.1 KB** (実測, lawfirm BPMN) | `BpmnWorkflowSerializer` JSON、blob は `vertex_spiff_instance.state_json` に格納 |

現状 7 worker の合計 peak 100–300 inst/s に対し **single shard で 3–4× headroom**。Phase 3 で hash partition による多 shard 化を検討。

## License Posture

- SpiffWorkflow = **LGPL-3.0**: linking (import) 利用は source 開示義務なし。**SpiffWorkflow 本体を改変しない限り** SaaS / network use で問題なし。改変が必要な場合のみ public fork を維持する (CLA は不要)。
- 依存: `lxml` (BSD), `celery` は使用しない (engine library のみ採用)。

# Consequences

## 利点

- **License $0**, broker pod 廃止 ($140/mo Vultr 削減見込) , `mitama-udf-pool` 圧縮緩和
- **ADR-0036 / record-log 規約と完全整合** (engine state も append-only、no UPDATE)
- **既存 BPMN 資産** (`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/lawfirm/*.bpmn` 等) **そのまま利用可**
- **既存 pyzeebe worker は handler 無改修**、decorator のみ差し替え
- **pyzeebe watchdog hazard 解消** (asyncio 占有 SDK を撤去)
- DMN 1.3 が同梱され `00-contracts/dmn/` policy と直接連携可能 (ADR-2604261100 系)

## 欠点 / リスク

- **単機 throughput が Zeebe より 1 桁低い** (1.2k vs 10k+/s)。現規模では十分だが、将来 Phase 3 で **RW-native custom BPMN interpreter** への段階移行を準備。
- **BPMN 機能 gap**: Compensation / Transaction subprocess の実装は薄い。既存 BPMN を audit し、未対応要素は移行前に書き換える。
- **Spiff 3.x の hidden LOE**: 4 つの API 罠 (`get_subprocess_specs` 形状 / ServiceTask converter 欠落 / STARTED state / `complete()` API) + Zeebe `taskDefinition` 非対応 → engine 実装 +0.5d。詳細は本 ADR §Implementation Notes。
- **既存 BPMN corpus の 50% (7/14) は cleanup 必要** (sequenceFlow 欠落 / ISO 8601 cycle)。engine 不具合ではなく BPMN モデル側の事情。詳細は §Implementation Notes 表を参照。
- **Multi-instance parallel** は GIL のため engine 内では擬似並列 (service task 自体は外部 worker dispatch で実並列を担保)。
- **Camunda Modeler の `zeebe:taskDefinition` 拡張** はパーサ拡張が必要。Spiff 側の `CamundaParser` で吸収可能だが PoC で確認。
- **LGPL の解釈**: SpiffWorkflow を import するだけの利用は network use 開示義務なし、と本 ADR は判断。万一改変が必要になった場合は `_archive/spiffworkflow-fork/` を public mirror する。

## 影響範囲

- 新規 dir: `etzhayyim-root/50-infra/k8s/bpmn-engine-host/`
- 新規 schema: `30-graph/graph-schema/sql_migrations/20260509110000_vertex_spiff_runtime.{up,down}.sql`
- 新規 lexicon: `00-contracts/lexicons/com/etzhayyim/apps/bpmn/{process,instance,job}.json`
- 新規 SDK: `40-engine/kotoba/crates/kotoba-kotodama/sdk/etzhayyim-bpmn/` (Python decorator shim)
- 影響 worker: `50-infra/k8s/{open-lei-mcp,intel-dependency-worker,claim-consumer-actor,livecam-vision-actor,comfyui-generation-actor,shigotoba-jobs-actor,smishing-actor}` × 7 (decorator 差し替え)
- 撤去対象: `etzhayyim-root/50-infra/vultr/zeebe/zeebe.yaml`, `50-infra/vultr/mitama-udf-pool/templates/zeebe-worker.yaml` の Zeebe broker 部分 (Phase 2 完了後)

# Alternatives Considered

| 候補 | License | 不採用理由 |
|---|---|---|
| **DBOS Transact** | MIT | code-as-code (BPMN 不要)、UPDATE / SELECT FOR UPDATE / ON CONFLICT 多用で **RW backend 不可** (別 Postgres を要する)。BPMN 資産を破棄する根本転換になり影響範囲が本件を逸脱 |
| **bpmn-engine** (Node.js, MIT) | MIT | engine 自体は良いが TS host を別建てする必要があり、Python worker と engine が別 pod 化。Spiff の同 pod in-process 実行に対し境界が増える |
| **Flowable / Camunda 7 CE** | Apache 2.0 | JDBC 経由で `UPDATE` / `ON CONFLICT DO UPDATE` を engine 内部から実行 → RW 規約と構造的に衝突。JVM 起動 600–700 MB / 8–20 s cold start も負担。C7 CE は 2025-10 EOL |
| **Temporal (self-host)** | MIT | code-as-code、内部 Cassandra/Postgres を要求し RW を state 層にできない (要件外)。BPMN 資産も破棄 |
| **Conductor (Orkes OSS)** | Apache 2.0 | JSON DAG (BPMN ではない)。Postgres backend は ON CONFLICT 依存 |
| **RW-native custom BPMN interpreter** | (自作) | 性能・規約整合は最高だが LOE 20–30 d + BPMN feature gap の自己責任。**Phase 3 オプション** として温存 |
| **Camunda 8 (Zeebe) 継続** | Camunda Self-Managed | License コスト ($50–150k/yr trigger 想定) + 上記 broker 重量問題が継続 |

# PoC Scope (Phase 1)

**対象**: `open-lei-mcp` の `open_lei_collect_gleif_global_lei` BPMN を SpiffWorkflow + RW で再実装

**LOE**: 8–10 人日

**Deliverables**:

1. `30-graph/graph-schema/sql_migrations/20260509110000_vertex_spiff_runtime.{up,down}.sql` — `vertex_spiff_{instance,job,timer,history}` + `mv_spiff_ready_jobs` (`rw-health-gate.sh` 通過後に Alembic 直適用。table cardinality 数千・MV は status filter のみのため heavy DDL queue は不要)
2. `00-contracts/lexicons/com/etzhayyim/apps/bpmn/{process,instance,job}.json` (PDS bundle 再生成 3-step 必須、root CLAUDE.md 規約)
3. `40-engine/kotoba/crates/kotoba-kotodama/sdk/etzhayyim-bpmn/` — Python decorator shim (`@etzhayyim_bpmn.task("...")`)
4. `etzhayyim-root/50-infra/k8s/bpmn-engine-host/` — Deployment + ConfigMap (replica 1, sleepAfter ∞)
5. `50-infra/k8s/open-lei-mcp/` の `gleif_ingester.py` を `pyzeebe` → `etzhayyim_bpmn` decorator に差し替え
6. Smoke test: 100 instance 並行起動 → 全 complete (timeout 60s 以内)、RW state row 数 / history 整合性確認

## Phase 2 follow-ups (engine-side, completed 2026-05-08)

| Item | API | LOE | 状態 |
|---|---|---|---|
| BPMN error event routing | `POST /v1/job/{id}/throwBpmnError` → `wf.catch(BpmnEvent(ErrorEventDefinition(code)))` | ~80 行 | ✅ |
| Timer reconciler (per-instance) | `POST /v1/instance/{id}/tick` → `wf.refresh_waiting_tasks()` | ~30 行 | ✅ |
| Timer reconciler (bulk) | `POST /v1/timer/tick` + `cronjob-timer-tick.yaml` (1m schedule) | ~30 行 | ✅ |
| Signal / message correlation | `POST /v1/instance/{id}/signal` | TBD | ⏳ Phase 3 |
| 残 7 lawfirm BPMN cleanup | per-file (sequenceFlow / ISO 8601 cycle) | per-file | ⏳ actor 担当 |

## Cluster apply gate (PoC Phase 1)

初回 cluster apply の正本は
`etzhayyim-root/50-infra/k8s/bpmn-engine-host/RUNBOOK.md` とする。この ADR は設計判断、
runbook は手順と当日の acceptance gate を持つ。

適用順序は固定:

1. `bash etzhayyim-root/50-infra/k8s/bpmn-engine-host/preflight.sh`
2. `70-tools/scripts/ingest/rw-health-gate.sh`
3. Alembic migration `r_20260509110000_vertex_spiff_runtime`
4. immutable image tag build (`bpmn-engine-host` と `open-lei-mcp`)
5. `bpmn-engine-host-secrets` (`KOTOBA_URL`) 作成
6. `bpmn-engine-host` Deployment + `cronjob-timer-tick.yaml`
7. `open-lei-spiff-worker` Deployment
8. low-concurrency smoke (`--concurrency 3`)
9. acceptance smoke (`--concurrency 100 --p95-budget-s 30`)
10. restart drill (smoke 実行中に engine pod delete)

成功条件:

- `alembic_version` head が `r_20260509110000_vertex_spiff_runtime`
- `vertex_spiff_{instance,job,timer,history}` と `mv_spiff_ready_jobs`
  が Kotoba/Datomic に存在する
- `vertex_bpmn_instance` など既存 Zeebe runtime shape は無変更
- `pnpm db:gen && pnpm db:drift` が 0 drift
- `/healthz` と `/readyz` が 200
- `open-lei-spiff-worker` が対象 task type を subscribe している
- `lawfirm_intake_funnel` smoke が 100 並行で p95 < 30s
- restart drill 後も running instance が完了する

Rollback は runbook の順に、worker stop → engine host stop → schema
downgrade を行う。`mcp_server.py` は `BPMN_ENGINE_URL` を unset すれば
legacy `ZEEBE_GATEWAY` fallback に戻るため、Phase 1 は fresh rollback 可能。

**Acceptance**:

- 100 instance 並行で p95 end-to-end < 30s
- engine host pod restart 時に running instance が history から replay されて完了する
- RW で `UPDATE` / `ON CONFLICT` が一切発行されない (pg log 確認)
- pyzeebe watchdog issue が再発しない (engine host pod の liveness が asyncio 非依存)

## Operational acceptance (2026-05-09 JST)

RW 安定化後に RUNBOOK gate を再実行し、本 ADR の採用判断は accepted 相当に進めた。
ADR file の `status` は既存 convention に合わせて `active` のまま保持する。

Acceptance snapshot:

- `bpmn-engine-host` image:
  `ghcr.io/etzhayyim/bpmn-engine-host:20260509-0229remember-followups`
  (`replicas=1 ready=1 updated=1`)
- `lawfirm-spiff-worker` image:
  `ghcr.io/etzhayyim/lawfirm-spiff-worker:20260509-0154inline0-scale10`
  (`replicas=6 ready=6 updated=6`)
- c10 smoke: `completed=10`, `p95_s=4.193`, no history/orphan violations
- c100 smoke: `completed=100`, `p95_s=20.328`, `rc=0`, no history/orphan violations
- restart drill: engine pod delete mid-run; `completed=100`, `errored=0`, `rc=0`,
  no history/orphan violations
- RW health healthy; active jobs query returned 0 rows
- no smoke or port-forward processes left running; OSM jobs restored
- verification: engine/worker `py_compile` OK,
  `uv run pytest tests/test_spiff_worker_pure.py -q` => 3 passed,
  `git diff --check` OK
- The acceptance p95 is DB-clock duration from
  `vertex_spiff_history.event_type='instance_started'` to
  `vertex_spiff_instance.completed_at`. `observed_p95_s` in smoke output
  includes runner-side RW polling/read visibility latency and is recorded
  as diagnostics, not the acceptance latency.

Zeebe broker retirement is now gated by
`etzhayyim-root/50-infra/vultr/zeebe/DECOMMISSION-RUNBOOK.md`.

## Phase Plan

| Phase | Scope | LOE | 完了基準 |
|---|---|---|---|
| 1 | open-lei PoC (本 ADR) | 8–10d | `RUNBOOK.md` の cluster apply gate + 上記 Acceptance |
| 2 | 残り worker 移行 + Zeebe broker 撤去 | 12–15d | Spiff smoke green、legacy pyzeebe consumers drained、`etzhayyim-root/50-infra/vultr/zeebe/DECOMMISSION-RUNBOOK.md` 完了 |
| 3 (optional) | hot-path を RW-native custom interpreter に置換 | 20–30d | 単機 ≥ 5k inst/s、Spiff は cold/legacy path に残す |

# Implementation Notes (Spiff 3.1.2 verified, 2026-05-08)

PoC Phase 1 のエンジン実装中にローカル検証 (`SpiffWorkflow==3.1.2` + 既存
`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/lawfirm/*.bpmn` 14 件) で発覚した **inherent な追加
LOE と API 制約**。後続の engine host 実装者が同じ罠を踏まないために残す。

## Spiff 3.x API 制約 (engine 設計に直接影響)

| # | 制約 | 修正パターン |
|---|---|---|
| A | `BpmnParser.get_subprocess_specs(name)` は **subprocess dict のみ**返す。1.x の `(spec, subs)` タプル API は撤去済 | `spec = parser.get_spec(name); subs = parser.get_subprocess_specs(name) or {}` |
| B | `BpmnWorkflowSerializer()` のデフォルト registry (`DEFAULT_CONFIG`, 48 entries) は `NoneTask` / `ManualTask` / `UserTask` / `ScriptTask` の converter を持つが **`ServiceTask` / `SendTask` / `ReceiveTask` は欠落**。Spiff 設計: external work の serialize はユーザー責任 | `BpmnWorkflowSerializer.configure({**DEFAULT_CONFIG, ServiceTask: BpmnTaskSpecConverter, SendTask: BpmnTaskSpecConverter, ReceiveTask: BpmnTaskSpecConverter})` |
| C | `do_engine_steps()` 後の external-work token state は `READY` ではなく **`STARTED`**。READY は engine が内部ループで消費する transient state | worker pickup filter: `wf.get_tasks(state=TaskState.STARTED)` + `isinstance(spec, (ServiceTask, SendTask, ReceiveTask))` |
| D | STARTED service task の完了は **`task.complete()` 一択**。`task.run()` は STARTED に対して no-op/raise。Spiff 1.x の `complete()` は名残ではなく canonical API | `Task.complete()` を直接呼ぶ。`getattr` defensive chain は不要 |

これらはドキュメント化が薄く、Spiff の sample (Spiff Arena) を読んで判明する。
ADR drafting 時の **bpmn-engine-alternatives 評価で見落とした隠し LOE ≈ 0.5d**。

## Zeebe `taskDefinition` extraction pattern

`BpmnParser` は **Camunda 8 (Zeebe) 拡張 (`<zeebe:taskDefinition type="...">`) を
解釈しない**。`SpiffWorkflow.spiff.parser` は Spiff own DSL (`serviceTaskOperator`)
を期待し、これも Zeebe とは別物。lawfirm BPMN corpus は全 Zeebe-shape のため、
out-of-band で XML を再走査して `task_type` を task_spec に stitch する:

```python
def _inject_zeebe_task_types(spec, xml_root, bpmn_process_id):
    proc = xml_root.find(f".//bpmn:process[@id='{bpmn_process_id}']", NS)
    for st in proc.findall(".//bpmn:serviceTask", NS):
        td = st.find(".//zeebe:taskDefinition", NS)
        if td is not None and st.get("id") in spec.task_specs:
            spec.task_specs[st.get("id")].task_type = td.get("type")
```

動的属性は default converter で **serialize round-trip 時に脱落する** ため、
`BpmnTaskSpecConverter` をサブクラス化して `to_dict` / `from_dict` で `task_type`
を明示的に往復させる必要がある (engine.py `_etzhayyimServiceTaskConverter`)。

代替案として CamundaParser 系のフルカスタムサブクラス (~150 行) も評価したが、
**XML 再走査 + dynamic attr + custom converter (~50 行)** の方が小回り効く。
将来 multi-engine 対応 (Spiff own DSL / Camunda 7 BPMN) する際に分岐点になる。

## 既存 lawfirm BPMN corpus 互換性 (engine fix 適用後)

| BPMN | engine boundary | 備考 |
|---|---|---|
| `engagementClose.bpmn` | ✅ | 5 zeebe task injected |
| `intakeFunnel.bpmn` | ✅ | seed via migration `20260509080000` |
| `marketingAdHoc.bpmn` | ✅ | |
| `matterCreate.bpmn` | ✅ | seed via same migration |
| `paymentIntake.bpmn` | ✅ | |
| `pipelineStageTransition.bpmn` | ✅ | |
| `pwcClearance.bpmn` | ✅ | 4 zeebe task injected |
| `issueInvoice.bpmn` | ❌ | `No output task connected` (BPMN sequenceFlow 欠落) |
| `runConflictCheck.bpmn` | ❌ | 同上 |
| `searchPrecedent.bpmn` | ❌ | 同上 |
| `submitFiling.bpmn` | ❌ | 同上 |
| `marketingTick.bpmn` | ❌ | `R/PT24H` ISO cycle expression を Spiff Python script engine が eval 不可 |
| `msGraphSubscriptionRenewTick.bpmn` | ❌ | 同上 |
| `salesCadenceTick.bpmn` | ❌ | 同上 |

PoC Phase 1 acceptance には **7/14 通れば十分** (intakeFunnel が smoke 対象)。
残 7 件は **engine ではなく BPMN 個別の cleanup** で、PoC scope 外:

- **`No output task connected` (4 件)** = BPMN モデル修正 (Spiff strict、Camunda は緩い)。各 actor 担当が修正
- **ISO 8601 cycle (3 件)** = Spiff の timer parser override (~30 行) または BPMN
  side で `<bpmn:timeCycle>` 構造に揃える。後者の方が portable

## Namespace separation (cluster-apply preflight で発覚)

`vertex_bpmn_instance` / `vertex_bpmn_activity_event` / `vertex_bpmn_signal_log`
は **既存 Camunda 8 (Zeebe) shape** で `migrations/20260419150000_vertex_bpmn_tables.ts`
+ `0001_initial_schema.ts` 経由で deploy 済、`50-infra/cloudflare/workers/graph`
等が active consumer。同名で `CREATE TABLE IF NOT EXISTS` を発行しても古い
schema が残り、engine の SELECT が `column does not exist` で死ぬ。

このため Spiff runtime 層は `vertex_spiff_*` 名前空間に分離:

| 層 | テーブル | 由来 |
|---|---|---|
| Spec (engine-agnostic, 共有) | `vertex_bpmn_process_def`, `vertex_bpmn_lexicon_binding` | 既存 (`migrations/20260423000000_vertex_bpmn_actor_def.ts`) |
| Spiff runtime (新規) | `vertex_spiff_instance`, `vertex_spiff_job`, `vertex_spiff_timer`, `vertex_spiff_history`, `mv_spiff_ready_jobs` | 本 ADR migration `r_20260509110000_vertex_spiff_runtime` |
| Zeebe runtime (legacy, 不変) | `vertex_bpmn_instance`, `vertex_bpmn_activity_event`, `vertex_bpmn_signal_log` | Camunda 8、Phase 2 で broker 撤去後に retire 候補 |

AT record collection paths も整合:
`com.etzhayyim.apps.spiff.{instance,job,history}` — 既存
`com.etzhayyim.bpmn.process` (spec) は engine-agnostic として保持。

## requirements.txt ピン

`SpiffWorkflow>=3.1,<4.0` は **必須**。3.0 以前は API 形状が違う、4.0 は破壊的変更
予定。`requirements.txt` (engine host) で固定済。

# References

- SpiffWorkflow: https://github.com/sartography/SpiffWorkflow (LGPL-3.0)
- ADR-0036 Worker-direct Hyperdrive Persistence: `90-docs/adr/0036-worker-direct-hyperdrive-persistence.md`
- ADR-0056 BPMN-as-actor: `90-docs/adr/0056-bpmn-as-actor.md`
- Record-log semantics (no MST): `90-docs/260424-bsky-compat-kotoba-split.md`
- ADR 2604282300 CF Worker = Edge Layer / Zeebe・RW UDF = Business Logic
- Kotoba/Datomic Smooth Scaling Gate: `50-infra/CLAUDE.md` + `50-infra/vultr/kotoba/scaling-contract.yaml`
- Camunda 7 CE EOL: https://docs.camunda.org/manual/7.21/introduction/supported-environments/ (community support 2025-10-11 終了)
