---
id: adr-2604281800-open-smartphone-layer-actors
title: "ADR-2604281800: open-smartphone — 7-Layer Independent Actor Architecture (SoC / Modem / Sensor / OS / EMS / BOM / Patent)"
status: active
doc_type: adr
topic: open-smartphone
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - open-smartphone-soc actor (チップ設計・Fab受注・輸出規制)
  - open-smartphone-modem actor (ベースバンド・型式認証・SEP依存)
  - open-smartphone-sensor actor (センサーモジュール・Linuxドライバ・校正)
  - open-smartphone-os actor (OSビルド・OTA・HALドライバ)
  - open-smartphone-ems actor (EMS製造拠点・生産キャパシティ・コンプライアンス)
  - open-smartphone-bom actor (BOM統合・オープンスコア・代替調達)
  - open-smartphone-patent actor (SEPランドスケープ・特許プール・失効ゲート)
  - BPMN flows for all 7 domains (27 BPMN processes)
  - Kotoba/Datomic schema: 19 tables + 2 MVs
  - Lexicon contracts: 26 JSON files
related:
  - adr-0056-bpmn-as-actor
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2604251024-patent-bulk-ingest-and-blob-cid
  - adr-2604271830-patent-expired-pharma-seiyaku-handoff
---

# ADR-2604281800 — open-smartphone 7-Layer Independent Actor Architecture

**Status**: active
**Date**: 2026-04-28
**Authors**: Jun Kawasaki + Claude Code

## Context

スマートフォンは chips → modem → sensor → OS → EMS製造 → BOM → patent の7層からなる複合システムであり、それぞれ独立したライフサイクルと規制を持つ。誰でもオープンなスマートフォンを設計・製造できるようにするためには、各層の情報を独立した actor として管理し、横断的な依存関係 (BOM → 全層、patent → modem/soc) を明示化する必要がある。

「ESM」は Electronics Manufacturing Services の誤記。正しい業界標準用語は **EMS** (Foxconn / Pegatron / Wistron / Jabil / Flextronics 等が代表例)。

既存の関連 actor:
- `open-semiconductor-fab` — ウェハー製造キャパシティ (SoC fab 受注の参照先)
- `open-semi-ip-licensing` — 半導体IP/ライセンス管理
- `open-itu-spectrum` — 周波数割当 (modem 対応 RAT の参照先)
- `open-patent` — USPTO/EPO 特許 DB bulk ingest (patent actor の upstream)
- `open-right-to-repair` — 修理権 (EMS + BOM からの downstream)
- `open-cyber-vuln` — CVE (OS セキュリティパッチの参照先)

## Decision

### 7つの独立 T1 Actor (BPMN-as-actor, ADR-0056)

各 actor は独立した `{name}.etzhayyim.com` ドメイン、`did:web:{name}.etzhayyim.com` AT facade を持ち、0個の新規 CF Worker を追加しない。

| Actor | DID | 担当層 | timer BPMN |
|---|---|---|---|
| open-smartphone-soc | did:web:open-smartphone-soc.etzhayyim.com | L1: Silicon / ISA / Fab | fetchRiscvEcosystemDelta (R/P7D) |
| open-smartphone-modem | did:web:open-smartphone-modem.etzhayyim.com | L2: Radio / RAT / SEP | fetchSepDelta (R/P1D) |
| open-smartphone-sensor | did:web:open-smartphone-sensor.etzhayyim.com | L3: Sensors / Drivers | fetchDriverAvailability (R/P7D), dailyPulse (R/P1D) |
| open-smartphone-os | did:web:open-smartphone-os.etzhayyim.com | L4: OS / HAL / OTA | fetchSecurityPatchDelta (R/P1D) |
| open-smartphone-ems | did:web:open-smartphone-ems.etzhayyim.com | L5: EMS製造拠点 | fetchComplianceDelta (R/P7D), dailyPulse (R/P1D) |
| open-smartphone-bom | did:web:open-smartphone-bom.etzhayyim.com | L6: BOM統合 / Open Score | (XRPC-only) |
| open-smartphone-patent | did:web:open-smartphone-patent.etzhayyim.com | L7: SEP / Patent Pool | fetchSepLandscapeDelta (R/P1D), flagExpiryGate (R/P7D) |

### BPMN inventory — 27 flows, 0 new CF Workers

**open-smartphone-soc** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| registerChipDesign | XRPC | vertex_open_smartphone_soc_design |
| trackFabOrder | XRPC | vertex_open_smartphone_soc_fab_order |
| fetchRiscvEcosystemDelta | R/P7D | audit only |
| flagExportControl | XRPC | vertex_open_smartphone_soc_export_flag |

**open-smartphone-modem** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| recordModemSpec | XRPC | vertex_open_smartphone_modem_spec |
| fetchSepDelta | R/P1D | audit only |
| recordTypeApproval | XRPC | vertex_open_smartphone_modem_type_approval |
| flagPatentBlocker | XRPC | vertex_open_smartphone_modem_sep_dep |

**open-smartphone-sensor** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| registerSensor | XRPC | vertex_open_smartphone_sensor_module |
| recordCalibration | XRPC | vertex_open_smartphone_sensor_calibration |
| fetchDriverAvailability | R/P7D | audit only |
| dailyPulse | R/P1D | audit only |

**open-smartphone-os** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| registerOsBuild | XRPC | vertex_open_smartphone_os_build |
| fetchSecurityPatchDelta | R/P1D | audit only (links to open-cyber-vuln) |
| trackOtaRelease | XRPC | vertex_open_smartphone_os_ota |
| recordHalDriver | XRPC | vertex_open_smartphone_os_hal_driver |

**open-smartphone-ems** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| registerFacility | XRPC | vertex_open_smartphone_ems_facility |
| recordCapacityOrder | XRPC | vertex_open_smartphone_ems_order |
| fetchComplianceDelta | R/P7D | audit only (RBA/conflict minerals) |
| dailyPulse | R/P1D | audit only |

**open-smartphone-bom** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| assembleBom | XRPC | vertex_open_smartphone_bom |
| recordBomLine | XRPC | vertex_open_smartphone_bom_line |
| computeOpenScore | XRPC | db.select + llm.json → audit |
| recordAlternativeSource | XRPC | vertex_open_smartphone_bom_sourcer |

**open-smartphone-patent** (4 flows):
| BPMN | Trigger | Table |
|---|---|---|
| fetchSepLandscapeDelta | R/P1D | audit only (ETSI IPR DB) |
| mapPatentDependency | XRPC | vertex_open_smartphone_patent_dep |
| flagExpiryGate | R/P7D | db.select → audit |
| recordLicensePool | XRPC | vertex_open_smartphone_patent_pool |

### Kotoba/Datomic schema — 19 tables + 2 MVs

| Migration | Tables | MV |
|---|---|---|
| 20260428183000 (soc) | soc_design, soc_fab_order, soc_export_flag | — |
| 20260428183100 (modem) | modem_spec, modem_type_approval, modem_sep_dep | — |
| 20260428183200 (sensor) | sensor_module, sensor_calibration, sensor_driver | — |
| 20260428183300 (os) | os_build, os_ota, os_hal_driver | mv_open_smartphone_os_cve_exposure |
| 20260428183400 (ems) | ems_facility, ems_order, ems_compliance | — |
| 20260428183500 (bom) | bom, bom_line, bom_sourcer | — |
| 20260428183600 (patent) | patent_sep, patent_pool, patent_dep | mv_open_smartphone_patent_free_zone |

### Lexicon contracts — 26 JSON files

`00-contracts/lexicons/com/etzhayyim/apps/openSmartphone{Soc,Modem,Sensor,Os,Ems,Bom,Patent}/`

各ドメイン 3-4 ファイル (procedure + query)。NSID prefix: `com.etzhayyim.openSmartphone{Layer}.*`

### Patent 依存関係グラフ設計

スマートフォンの特許依存は3層に分類される:

**Layer A: SEP (Standard Essential Patents)**
- 4G LTE: Qualcomm / Ericsson / Nokia / Huawei / Samsung が支配的 (~15,000 SEP宣言)
- 5G NR: Huawei (~15%), Qualcomm (~11%), Samsung (~10%), LG (~9%), Nokia (~8%)
- Wi-Fi 802.11ax: Qualcomm / Broadcom / Intel
- Bluetooth 5.x: Qualcomm / Ericsson / CSR (now Qualcomm)
- GNSS: 多くが期限切れまたは FRAND 宣言済み (GPS L1は2001年以前に失効)

**Layer B: 特許プール (FRAND 一括ライセンス)**
- Avanci (5G端末): ~$5/unit for 5G (100+ member companies)
- Via Licensing (Wi-Fi / Bluetooth): $0.30-$2/unit
- Sisvel (4G/5G): 競合するプール
- MPEG LA: video codec 系

**Layer C: 失効ゾーン (Free Zone)**
- `mv_open_smartphone_patent_free_zone` が24ヶ月以内失効 SEP を継続 track
- `flagExpiryGate` (R/P7D) が定期スキャン
- 2G/3G関連の多くは2020-2026年に失効 → 4G/5G-only SoC で回避可能

**実装者向け最小リスクパス**:
1. RISC-V ISA (ARM SEP 回避) + TSMC/Samsung 5nm以下非依存 fab
2. 5G modem は Avanci pool に $5/unit でアクセス (open modem: Osmocom / OsmocomBB ベース)
3. Wi-Fi 6 は Via Licensing $0.72/unit または失効待ち
4. OS: postmarketOS (mainline Linux kernel) + 100% open blob 目標
5. カメラ: OmniVision / Sony IMX は driver が mainlined (Linux 5.x+)

### EMS 選定基準

| 優先度 | 基準 | 理由 |
|---|---|---|
| 1 | RBA (Responsible Business Alliance) passed audit | 労働・環境コンプライアンス |
| 2 | ISO 9001 + ISO 14001 認証 | 品質・環境マネジメント |
| 3 | Conflict Mineral (3TG: Ta/Sn/W/Au) compliant | OECD ガイドライン準拠 |
| 4 | IPC-A-610 Class 3 (highest quality) | 信頼性 |
| 5 | ロケーション分散 (CHN/TWN依存低減) | VNM/IND/THA 拠点を優先 |

### computeOpenScore の算出ロジック

BOM line ごとに:
- `open_source=true` (RISC-V RTL, mainlined driver, AOSP, etc.) → +1 point
- `open_source=false` (closed modem FW, vendor blobs) → +0 point
- weighted: SoC/modem/OS のウェイトを camera/battery より高く設定 (LLM が判断)

Score 100% = 完全オープン (理想: RISC-V SoC + Osmocom modem + postmarketOS)
Score 0% = 全クローズド (Apple/Qualcomm フルスタック)

現実的な目標: Score 60-70% (Fairphone 4 相当の公開部品比率)

## Cross-actor dependencies

| From | To | Relationship |
|---|---|---|
| open-smartphone-soc | open-semiconductor-fab | fab受注 → fabDid 参照 |
| open-smartphone-soc | open-semi-ip-licensing | ISA ライセンス確認 |
| open-smartphone-modem | open-itu-spectrum | RAT 対応周波数帯 確認 |
| open-smartphone-modem | open-smartphone-patent | SEP 依存 → patent_sep 参照 |
| open-smartphone-sensor | open-smartphone-os | driver → hal_driver 参照 |
| open-smartphone-os | open-cyber-vuln | CVE パッチ delta 参照 |
| open-smartphone-bom | 全6 layer | 統合 BOM (soc/modem/os/ems DIDs) |
| open-smartphone-patent | open-patent | USPTO/EPO bulk ingest upstream |
| open-smartphone-ems | open-right-to-repair | 修理可能設計 → 修理権 actor downstream |

## Consequences

- **全27 BPMN** が Zeebe F5 watcher 経由で自動デプロイ (bpmn-dispatcher 30s polling)
- **timer-start BPMN**: fetchRiscvEcosystemDelta (R/P7D), fetchSepDelta (R/P1D), fetchDriverAvailability (R/P7D), fetchSecurityPatchDelta (R/P1D), fetchComplianceDelta (R/P7D), dailyPulse×2 (R/P1D), fetchSepLandscapeDelta (R/P1D), flagExpiryGate (R/P7D) = 計9本
- **XRPC endpoint**: `dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.openSmartphone{Layer}.{method}` 経由
- **`write_table_allowlist`**: NULL (unrestricted) — domain stabilization 後に per-table tighten
- **ERC725 root**: 全7 actor とも `erc725_root_pending = true` — `provision-root-identity` 別 PR
- **実装参照**: RISC-V Foundation、Osmocom、postmarketOS、Fairphone、Framework Laptop の設計哲学を参考にしている

## References

- ADR-0056: BPMN-as-actor pattern
- ADR-0036: Worker-direct Hyperdrive persistence
- ADR-0074: ERC725 root identity
- ADR-2604251024: Patent bulk ingest (open-patent upstream)
- ADR-2604271830: Patent expiry → open-seiyaku handoff (同じ特許失効ゲートパターン)
- Commit: (この ADR と同時に全ファイル作成)
- ETSI IPR Database: https://www.etsi.org/intellectual-property-rights/ipr-database
- RISC-V ISA Specification: https://riscv.org/technical/specifications/
- RBA (Responsible Business Alliance): https://www.responsiblebusiness.org/
- Avanci 5G Patent Pool: https://avanci.com/
