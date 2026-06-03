---
id: adr-2605190100-defense-cluster-topology
title: "Defense Cluster Topology — 防衛調達 AI Platform (Phase 1 SaaS → Air-Gap)"
status: active
doc_type: adr
topic: defense-cluster
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - defense cluster actor namespace (com.etzhayyim.apps.def*)
  - defense deployment tier model (SaaS / Sovereign / Air-Gap)
  - defense CAD management + generative CAD (OpenSCAD/CadQuery)
  - supplier dependency Pregel graph topology
  - security clearance model (0-4 levels)
  - 外為法 / ITAR export-control code regime
  - Phase 9 operational domain (mission / platform / ISR / EW)
  - Phase 10 COP+ROE / cyber operations / logistics-ops bridge
  - Phase 11 Pydantic v2 validation / Rego escalation policies / streaming MVs
priority: 8.5
axis: architecture
weight: 0.85
depends_on:
  - adr-0016-legal-cluster-topology
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
related:
  - adr-0017-maritime-energy-cluster-topology
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605210100-defense-unified-cop-roe-engine
  - adr-2605210200-defense-cyber-operations
  - adr-2605210300-defense-logistics-ops-bridge
supersedes: []
superseded_by: []
---

# Defense Cluster Topology — 防衛調達 AI Platform

## Context

防衛調達（日本の防衛省・ATLA および prime contractor 向け）AI プラットフォームの設計。
Anduril 型の defense-tech ポジションを、etzhayyim の既存 AT Protocol + LangGraph + MCP スタック上で実現する。

etzhayyim は現時点で ATLA 調達情報サービス未登録のため、
**Phase 1 は prime contractor（防衛産業企業）向け SaaS** から開始する。

## Decision

### デプロイメント 3 層モデル

| Tier | 対象 | インフラ | 分類 |
|---|---|---|---|
| T0 SaaS | prime contractor (三菱重工・川崎重工等) | CF Workers + Vultr LAX | unclassified / CUI |
| T1 Sovereign | ATLA vendor 登録後 | Sakura Cloud / NTT Smart Data Platform (国内) | 秘 (confidential) |
| T2 Air-Gap | 特定秘密取扱業者資格取得後 | bare-metal K8s、完全オフライン | 極秘 / 特定秘密 |

**Phase 1 = T0 のみ実装。T1/T2 は同一 K8s manifests をオーバーレイで適用。**
T2 air-gap overlay: `50-infra/k8s/lg-defense/overlays/t2-airgap/` 完成 (Phase 9)。

### セキュリティ分類レベル

```
0 public      — 公開情報
1 sensitive   — 機微 (signal:v1 暗号化)
2 confidential — 秘 (T1 以上必須)
3 secret      — 極秘 (T2 air-gap 必須)
4 top_secret  — 特定秘密 (T2 + 物理隔離 + 専用 KMS)
```

AT Protocol への適用:
- Level 0-1: plaintext / `signal:v1:{ciphertext}` フィールド
- Level 2-3: record 全体暗号化 + clearance-gated DID
- Level 4: AT Protocol federation 完全無効、PDS pod-local only

### Actor NSID 名前空間

| Actor | NSID prefix | 役割 | Phase |
|---|---|---|---|
| defContract | `com.etzhayyim.apps.defContract.*` | 契約ライフサイクル管理 | 1-8 |
| defSupplier | `com.etzhayyim.apps.defSupplier.*` | サプライヤー資格・クリアランス | 1-8 |
| defBudget | `com.etzhayyim.apps.defBudget.*` | EVM コスト追跡 | 1-8 |
| defAudit | `com.etzhayyim.apps.defAudit.*` | 不変監査証跡 | 1-8 |
| defCad | `com.etzhayyim.apps.defCad.*` | CAD ファイル管理・バージョン管理 | 1-8 |
| defCadgen | `com.etzhayyim.apps.defCadgen.*` | LangGraph 生成 CAD (OpenSCAD / CadQuery) | 1-8 |
| defMission | `com.etzhayyim.apps.defMission.*` | ミッション計画・承認・実行 | 9 |
| defPlatform | `com.etzhayyim.apps.defPlatform.*` | 自律プラットフォーム (UAV/UUV/地上) 制御 | 9 |
| defIsr | `com.etzhayyim.apps.defIsr.*` | ISR センサートラック・融合 COP | 9 |
| defEw | `com.etzhayyim.apps.defEw.*` | EW / Counter-UAS 介入 | 9 |
| defCop | `com.etzhayyim.apps.defCop.*` | 統合 COP アラートキュー + ROE 検証 | 10 |
| defCyber | `com.etzhayyim.apps.defCyber.*` | サイバー作戦 (PMESII 第 5 ドメイン) | 10 |
| defLogistics | `com.etzhayyim.apps.defLogistics.*` | 兵站-作戦ブリッジ (補給・EVM 連携) | 10 |

### LangGraph エージェント (v11.0.0, 13 graphs)

defense-langgraph-server (K8s pod, granian L3 runtime) に以下を配置:

**Phase 1-8 (調達・契約)**
- **ProcurementAdvisorAgent** — 入札分析・仕様書生成・契約草案
- **SupplierRiskAgent** — Pregel サプライチェーン N 次リスク伝播
- **ComplianceAgent** — 外為法 / ITAR / 特定秘密 分類チェック
- **ContractReviewAgent** — 防衛調達特例法・調達実施規則対応レビュー
- **CADGenerationAgent** — 要求仕様 → OpenSCAD/CadQuery → STL/STEP
- **ReActAgent** — MCP ループ (最大 10 イテレーション)
- **RiskBatchAgent** — 夜間サプライヤーリスク再スコアリング CronJob

**Phase 9 (作戦ドメイン)**
- **MissionOrchestrationAgent** — ミッション計画・承認・実行 (roc_code コンテキスト付)
- **PlatformControlAgent** — VALID_TRANSITIONS 状態機械 (UAV/UUV/地上/サイバー)
- **SensorFusionAgent** — ISR マルチセンサートラック融合 → mv_defense_fused_cop
- **EwCounterUasAgent** — EW / Counter-UAS 脅威評価・介入 (kinetic 常時 supervised)

**Phase 10 (統合・拡張)**
- **UnifiedCopAgent** — 4 グラフからの Pregel fan-in、ROC-A/B/C ROE 検証
- **CyberOperationsAgent** — PMESII 第 5 ドメイン、destroy/deny 常時 supervised
- **LogisticsOpsAgent** — バッテリー/燃料閾値監視 → 補給トリガー → EVM 連携

### 安全不変条件

| 条件 | 実装 |
|---|---|
| kinetic_soft_kill / HPM → 常時 supervised | `node_assess_autonomy` がモード強制上書き |
| cyber destroy / deny → 常時 supervised | `node_assess_cyber_autonomy` が強制上書き |
| EW / Cyber ops → classification_level ≥ 3 必須 | `node_classify_threat / node_classify_target` |
| ROC-A: ISR only, ROC-B: +EW, ROC-C: +kinetic | `ROC_PERMISSIONS` dict + Rego `etzhayyim.defense.roe` |
| T2-airgap 以外での kinetic / cyber-destroy → 拒否 | Rego `etzhayyim.defense.escalation` |

### Pregel グラフ (30-graph 拡張)

```
vertex_defense_supplier     — 企業ノード (クリアランスレベル、ITAR tier)
vertex_defense_part         — 部品ノード (ECCN 分類)
vertex_defense_personnel    — 人員ノード (clearance_level)
edge_defense_supply_tier    — サプライヤー依存 (tier1→tier2→tier3)
edge_defense_bom            — BOM 親子関係
edge_defense_access         — クリアランス権限チェーン
```

### CAD 管理

```
defCad actor
├─ メタデータ层  — AT Protocol record (vertex_defense_cad_file)
├─ バイナリ層   — T0/T1: CF R2 AES-256,  T2: on-prem MinIO
└─ defCadgen    — OpenSCAD executor + CadQuery executor + STL validator
```

### 外為法 / ITAR コード規制

T0 (unclassified) は通常開発フロー。T1 以上に関する技術データを扱うコードは外為法対象となる可能性があるため:
- アクセス制限付き private repo
- CI/CD ランナー = 国内 self-hosted のみ (GitHub Actions 不可)
- LLM 推論 = on-prem モデルのみ

### MCP ツール一覧 (v11.0.0, 32 tools)

**Phase 1-8 (11 tools)**

| Tool | 機能 |
|---|---|
| defContract.createContract | 契約作成 |
| defContract.listContracts | 契約一覧 |
| defContract.updateStatus | 契約ステータス遷移 |
| defSupplier.registerSupplier | サプライヤー登録 |
| defSupplier.listSuppliers | サプライヤー一覧 |
| defBudget.trackCost | コスト追跡 |
| defAudit.logEvent | 監査ログ |
| defCad.uploadFile | CAD ファイルアップロード |
| defCadgen.generatePart | LLM→CAD 生成 |
| defDashboard.getSummary | ダッシュボード集計 |
| defExport.classifyPart | ITAR/ECCN 輸出規制分類 |

**Phase 9 (12 tools)**

| Tool | 機能 |
|---|---|
| defMission.createMission | ミッション作成 |
| defMission.updateMissionStatus | ミッションステータス遷移 |
| defMission.listMissions | ミッション一覧 |
| defPlatform.registerPlatform | プラットフォーム登録 |
| defPlatform.updatePlatformState | プラットフォーム状態遷移 |
| defPlatform.listPlatforms | プラットフォーム一覧 |
| defIsr.ingestTrack | センサートラック投入 |
| defIsr.queryFusedPicture | 融合 COP クエリ |
| defIsr.listTracks | トラック一覧 |
| defEw.declareTarget | EW ターゲット宣言 (level ≥ 3) |
| defEw.requestIntervention | EW 介入要求 |
| defEw.listInterventions | 介入一覧 |

**Phase 10 (9 tools)**

| Tool | 機能 |
|---|---|
| defCop.queryAlertQueue | COP アラートキュー照会 |
| defCop.acknowledgeAlert | アラート確認 |
| defCop.validateRoe | ROE 検証 (ROC-A/B/C) |
| defCyber.declareTarget | サイバーターゲット宣言 (level ≥ 3) |
| defCyber.requestEffect | サイバー効果要求 |
| defCyber.listEffects | 効果一覧 |
| defLogistics.reportPlatformStatus | プラットフォームステータス報告 |
| defLogistics.linkMissionToBudget | ミッション-予算 EVM 連携 |
| defLogistics.listMaintenanceRequests | 整備要求一覧 |

### LangGraph グラフ一覧 (v11.0.0, 13 graphs)

| Graph ID | 役割 |
|---|---|
| defense-procurement-advisor | 入札分析・仕様書生成・契約草案 |
| defense-supplier-risk | Pregel N次リスク伝播 |
| defense-contract-review | 防衛調達特例法レビュー |
| defense-cadgen | 要求仕様→OpenSCAD/CadQuery→STL |
| defense-react-agent | ReAct MCP ループ (最大 10 イテレーション) |
| defense-risk-batch | 夜間サプライヤーリスク再スコアリング CronJob |
| defense-mission-orchestration | ミッション計画・承認・実行 |
| defense-platform-control | 自律プラットフォーム状態機械 |
| defense-sensor-fusion | ISR センサー融合 → COP |
| defense-ew-counteruas | EW / Counter-UAS 脅威・介入 |
| defense-unified-cop | 統合 COP + ROE 検証ファンイン |
| defense-cyber-operations | サイバー作戦 (PMESII 第 5 ドメイン) |
| defense-logistics-ops | 兵站-作戦ブリッジ |

### XRPC デュアルワイヤー (ADR-2605091400)

内部 wire (`dispatcher.etzhayyim.com/xrpc/<nsid>`) は `x-internal-trust` ヘッダーで認証。
`00-contracts/lexicons/` の lexicon JSON が MCP inputSchema と XRPC validation の両方を駆動。

### 入力バリデーション (Phase 11A)

`pydefense.validation` — Pydantic v2 モデル 29 個が `handle_tools_call` 入口でクリアランスチェック前に検証。
Phase 10 追加: `QueryAlertQueueArgs`, `AcknowledgeAlertArgs`, `ValidateRoeArgs` (ROC code validator),
`DeclareCyberTargetArgs`, `RequestEffectArgs`, `ListEffectsArgs`,
`ReportPlatformStatusArgs`, `LinkMissionToBudgetArgs`, `ListMaintenanceRequestsArgs`。
不正パラメーターは JSON-RPC `-32602 Invalid params` で早期拒否。

### OPA Rego ポリシー (Phase 11A)

`00-contracts/policies/etzhayyim/defense/`:

| パッケージ | ファイル | 役割 |
|---|---|---|
| `etzhayyim.defense.clearance` | `clearance/policy.rego` | T1/T2 tier 強制、有効期限チェック |
| `etzhayyim.defense.escalation` | `escalation/policy.rego` | kinetic/HPM/cyber-destroy の T2 + level≥3 + token gate |
| `etzhayyim.defense.roe` | `roe/policy.rego` | ROC-A/B/C 権限マトリクス + violations リスト |

### ストリーミング MV (Phase 11B)

| MV | 元テーブル | 用途 |
|---|---|---|
| `mv_defense_fused_cop` | vertex_defense_track (Phase 9) | 2km グリッド融合 ISR 画像 |
| `mv_defense_cop_alert_queue` | vertex_defense_cop_alert (Phase 10) | 未確認アラートを priority_rank 順 |
| `mv_defense_platform_readiness` | vertex_defense_maintenance_request | プラットフォーム別稼働可能サマリー |

### ITAR/ECCN 輸出規制 (Phase 5B)

`pydefense.itar_eccn` — 純粋関数、外部依存なし:
- `USML_CATEGORIES`: カテゴリ I〜XXI (21 カテゴリ)
- `ECCN_DESCRIPTIONS`: 20 主要 ECCN + EAR99
- `classify_part()`: `is_itar_controlled`, `export_license_required`, `risk_level` (HIGH/MEDIUM/LOW) を返す
- `flag_bom_itar_risk()`: BOM 行リストに `"itar_risk"` キーを付加する純粋関数

### 契約ライフサイクル状態機械 (Phase 6B)

`pydefense.contract_lifecycle` — 6 状態 (draft → submitted → awarded → in_execution → closed / cancelled)。
遷移に最小クリアランスレベルを課す (`awarded` は level 3 必須)。
変更は `vertex_defense_contract_status_history` への INSERT のみ (record-log semantics)。

### Prometheus メトリクス (Phase 6C)

`pydefense.metrics` — `/metrics` エンドポイントで公開 (`prometheus_client` 依存、dev 環境未インストール):
- `defense_mcp_tool_calls_total` (tool_name, status)
- `defense_mcp_request_duration_seconds` (method)
- `defense_mcp_clearance_rejections_total` (tool_name, required_level, provided_level)

### 夜間リスクバッチ (Phase 8A)

`pydefense.risk_batch` + `50-infra/k8s/lg-defense/cronjob-risk-batch.yaml`:
- スケジュール: `0 17 * * *` (02:00 JST)、`concurrencyPolicy: Forbid`
- `RISK_ALERT_THRESHOLD` (デフォルト 20) を超えたスコア変化で EVM 監査レシートを fire-and-forget

### EVM 監査チェーン

`classification_level >= 2` のイベントと、リスクスコアが `RISK_ALERT_THRESHOLD` を超えた場合に
`audit_chain.submit_audit_receipt` を `asyncio.ensure_future` で非同期発火。
コントラクト: `DefenseAuditRegistry`, chainId `260425`, アルゴリズム: keccak256 (`web3` optional dep)。

### スキーマ (RisingWave graphar)

**Phase 1-8**
```
vertex_defense_eccn_lookup              — ECCN コード参照テーブル
vertex_defense_contract_status_history  — 契約状態遷移ログ
vertex_defense_supplier_risk_snapshot   — サプライヤーリスクスナップショット
```

**Phase 9 (migration: 20260520050000)**
```
vertex_defense_mission          — ミッション頂点
edge_defense_mission_platform   — ミッション↔プラットフォーム辺
vertex_defense_platform         — プラットフォーム頂点
vertex_defense_platform_telemetry — テレメトリ時系列
vertex_defense_track            — ISR センサートラック
edge_defense_track_fusion       — 融合トラック辺
vertex_defense_ew_event         — EW イベント頂点
edge_defense_track_ew           — トラック↔EW 辺
vertex_defense_ew_intervention  — EW 介入頂点
mv_defense_fused_cop            — 融合 COP ストリーミング MV
```

**Phase 10 (migration: 20260521050000 + 20260521060000)**
```
vertex_defense_cop_alert        — COP アラート頂点
vertex_defense_cyber_target     — サイバーターゲット頂点
vertex_defense_cyber_effect     — サイバー効果頂点
edge_defense_target_effect      — ターゲット↔効果辺
vertex_defense_maintenance_request — 整備要求頂点
edge_defense_platform_maintenance  — プラットフォーム↔整備辺
mv_defense_cop_alert_queue      — 未確認アラートキュー MV
mv_defense_platform_readiness   — プラットフォーム稼働可能 MV
```

### デプロイ手順

`20-actors/defense/py/DEPLOY.md` 参照。要点:
1. `apply_defense_phase9.py --dry-run && apply_defense_phase9.py`
2. `apply_defense_phase10.py --dry-run && apply_defense_phase10.py`
3. BuildKit k8s remote build → GHCR push → `kubectl apply -k overlays/t2-airgap/`
4. `npx wrangler deploy` (lexicon bundle 更新後)

### 実装フェーズ

| Phase | 期間 | 内容 | 状態 |
|---|---|---|---|
| Phase 1-8 | 2026-05-20 | 調達・契約・CAD・リスクバッチ・バリデーション | **完了 (v8.0.0)** |
| Phase 9 | 2026-05-20 | ミッション / プラットフォーム / ISR / EW + T2 overlay | **完了** |
| Phase 10 | 2026-05-21 | 統合 COP+ROE / サイバー / 兵站ブリッジ | **完了** |
| Phase 11 | 2026-05-21 | Pydantic v2 全 29 モデル / Rego 3 パッケージ / ストリーミング MV | **完了** |
| Phase 2 | +12-18 ヶ月 | T1 Sovereign。ATLA vendor 登録完了後。Sakura Cloud。 | 未着手 |
| Phase 3 | +24-36 ヶ月 | T2 Air-Gap。特定秘密取扱業者資格取得後。 | 未着手 |

## Consequences

- 既存 CF Workers + Vultr + LangGraph スタックをそのまま再利用できる (T0)
- Lexicon JSON が MCP / XRPC 両 wire の SSoT となる (ADR-2605091400 準拠)
- T1/T2 への昇格は deploy topology の差し替えのみで対応可能
- ATLA vendor 登録・特定秘密取扱業者資格は別途ビジネスプロセスとして進める
- Pydantic v2 バリデーション (29 モデル) をクリアランスチェック前に置くことで不正 payload の早期排除
- record-log semantics (INSERT only) が RisingWave append-only モデルと整合する
- 夜間バッチ + EVM 監査により ISMAP 準拠の audit trail を自動生成できる
- ROC-A/B/C を Rego で宣言的に管理することで ROE 変更が単一ファイル更新で完結する
- kinetic / cyber-destroy の T2 要件を Rego + コードの 2 層で強制し、監査証跡を残す
- PMESII 5 ドメイン (Military/Political/Economic/Social/Infrastructure + **Cyber**) カバレッジ完成
