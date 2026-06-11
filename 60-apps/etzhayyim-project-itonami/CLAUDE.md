# etzhayyim-project-itonami — Aircraft Engine Lifecycle Simulation

航空機エンジンのライフサイクル全体（設計 → 調達 → 組立 → 試験 → デジタルツイン運用）を
シミュレーションおよび記録する Kotodama actor。UNSPSC（部品調達分類）と ISIC（サプライヤー産業分類）を統合する。

## Identity

| 属性 | 値 |
|---|---|
| nanoid | `it0n4m1x` |
| handle | `itonami.etzhayyim.com` |
| DID | `did:web:itonami.etzhayyim.com` |
| NSID prefix | `com.etzhayyim.apps.itonami.*` |
| runtimeType | `worker` |
| complianceFramework | `aerospace-safety` |

## Domain Model

```
EngineDesign
  ├── designCode         (e.g. "CFM56-7B")
  ├── engineType         turbofan | turboprop | piston | electric
  ├── thrustRatingKn     integer (kN × 100, e.g. 12100 = 121.00 kN)
  ├── massKg             integer
  └── certificationStatus  uncertified | in_progress | certified | retired

  AssemblyRecord (per engine instance)
  ├── engineId
  ├── phaseCode          design | procurement | assembly | testing | certified
  │                      | in_service | retired
  ├── progressPermille   0–1000
  └── notes

  ProcurementItem (UNSPSC integration)
  ├── engineId
  ├── unspscCode         8-digit commodity code
  ├── supplierIsicCode   4-digit ISIC Rev.4 class (supplier industry)
  ├── quantity           integer
  └── unitCostJpy        integer (JPY)

  TestResult
  ├── engineId
  ├── testType           bench | ground | flight
  ├── outcomeCode        pass | fail | conditional
  ├── thrustAchievedKn   integer (kN × 100)
  └── durationSeconds    integer

  FlightEvent (digital twin)
  ├── engineId
  ├── aircraftId
  ├── cycleCount         integer (total engine cycles to date)
  ├── flightHours        integer (hours × 10, e.g. 12345 = 1234.5 h)
  ├── eventCode          string (e.g. "HOT_SECTION_INSPECTION", "COMPRESSOR_SURGE")
  └── severityCode       info | warning | critical
```

## XRPC Surface (MVP — 7 methods)

| NSID | Type | 用途 |
|---|---|---|
| `com.etzhayyim.apps.itonami.health` | procedure | ヘルスチェック |
| `com.etzhayyim.apps.itonami.registerEngine` | procedure | エンジン設計エントリを登録 |
| `com.etzhayyim.apps.itonami.recordAssembly` | procedure | 組立フェーズのマイルストーンを記録 |
| `com.etzhayyim.apps.itonami.logTestResult` | procedure | 試験結果を記録 |
| `com.etzhayyim.apps.itonami.logFlightEvent` | procedure | デジタルツイン飛行イベントを記録 |
| `com.etzhayyim.apps.itonami.listEngines` | query | エンジン一覧（フィルタ・ページネーション） |
| `com.etzhayyim.apps.itonami.getEngine` | query | エンジン詳細（最新テスト結果含む） |

## Lexicons

`00-contracts/lexicons/com/etzhayyim/apps/itonami/`

| ファイル | NSID |
|---|---|
| `health.json` | `com.etzhayyim.apps.itonami.health` |
| `registerEngine.json` | `com.etzhayyim.apps.itonami.registerEngine` |
| `recordAssembly.json` | `com.etzhayyim.apps.itonami.recordAssembly` |
| `logTestResult.json` | `com.etzhayyim.apps.itonami.logTestResult` |
| `logFlightEvent.json` | `com.etzhayyim.apps.itonami.logFlightEvent` |
| `listEngines.json` | `com.etzhayyim.apps.itonami.listEngines` |
| `getEngine.json` | `com.etzhayyim.apps.itonami.getEngine` |

## SQL Graph Schema

### Nodes (vertex tables)

| Table | Key columns | 用途 |
|---|---|---|
| `vertex_itonami_engineDesign` | `vertex_id`, `engine_id`, `design_code`, `engine_type`, `thrust_rating_kn`, `mass_kg`, `certification_status` | エンジン設計マスタ |
| `vertex_itonami_assemblyRecord` | `vertex_id`, `engine_id`, `phase_code`, `progress_permille`, `notes`, `created_at` | 組立フェーズ記録 |
| `vertex_itonami_testResult` | `vertex_id`, `engine_id`, `test_type`, `outcome_code`, `thrust_achieved_kn`, `duration_seconds`, `created_at` | 試験結果 |
| `vertex_itonami_flightEvent` | `vertex_id`, `engine_id`, `aircraft_id`, `cycle_count`, `flight_hours`, `event_code`, `severity_code`, `created_at` | デジタルツイン飛行ログ |

### Edges (edge tables)

| Edge | From → To | 用途 |
|---|---|---|
| `edge_itonami_engine_assembly` | `:ItamiEngineDesign` → `:ItamiAssemblyRecord` | エンジン → 組立記録 |
| `edge_itonami_engine_test` | `:ItamiEngineDesign` → `:ItamiTestResult` | エンジン → 試験結果 |
| `edge_itonami_engine_flight` | `:ItamiEngineDesign` → `:ItamiFlightEvent` | エンジン → 飛行イベント |

## UNSPSC / ISIC Integration

- **部品調達 (UNSPSC)**: 航空エンジン部品は UNSPSC Segment 25 (Aerospace) および Segment 26 (Defense) が中心。`openUnispsc.commodity` actor を `Invoke` して commodity spec を取得。
- **サプライヤー分類 (ISIC)**: ISIC Rev.4 Section C (製造業) Division 30 (その他輸送機器製造業) Division 33 (機械器具修理業) を主に参照。`openIsic.classifyEntity` actor を `Invoke` してサプライヤーの産業コードを検証。
- **cross-actor invoke パターン**:
  ```ts
  // UNSPSC commodity spec 取得
  const spec = await kotodama.Invoke("", "com.etzhayyim.apps.openUnispsc.commodity", { code: "25101504" });
  // ISIC supplier 分類
  const isic = await kotodama.Invoke("", "com.etzhayyim.openIsic.classifyEntity", { name: supplierName });
  ```

## appview

- **Worker**: `60-apps/etzhayyim-project-itonami/appview/itonami-it0n4m1x/src/app.ts`
- **Kotodama descriptor**: `60-apps/etzhayyim-project-itonami/appview/itonami-it0n4m1x/kotodama.jsonld`
- **Svelte SPA**: `60-apps/etzhayyim-project-itonami/svelte/`

## Deploy

```bash
cd 60-apps/etzhayyim-project-itonami/appview/itonami-it0n4m1x
etzhayyim deploy
curl https://it0n4m1x.etzhayyim.com/health
```

## Migration Backlog

| ID | 内容 | Status |
|---|---|---|
| `itonami-app-ts-xrpc` | `app.ts` に全 7 XRPC method を実装 (registerEngine, recordAssembly, logTestResult, logFlightEvent, listEngines, getEngine, health) | done (2026-05-16) |
| `itonami-rw-migrations` | RisingWave migration: `vertex_itonami_{engineDesign,assemblyRecord,testResult,flightEvent}` + edge tables (20260516620000) | done (2026-05-16) |
| `itonami-unispsc-procurement-item` | ProcurementItem lexicon + vertex table (unspscCode, supplierIsicCode, quantity, unitCostJpy) | done (2026-05-16) |
| `itonami-digital-twin-stream` | FlightEvent 集計 `view_itonami_engine_health_summary` (plain VIEW — NOW() 禁止制約のため streaming MV ではなく VIEW) | done (2026-05-16) |
| `itonami-certification-bpmn` | AS9100D 認証フロー BPMN (`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/itonami/certification.bpmn`) — BPMN-as-actor runtime integration は operational | done (2026-05-16) |
| `itonami-isic-supplier-registry` | `registerSupplier` lexicon + handler + ISIC コード検証 (downstream cross-actor invoke openIsic.classifyEntity) | done (2026-05-16) |
