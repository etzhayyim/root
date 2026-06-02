---
id: adr-2605071800-airline-cluster-topology
title: "ADR-2605071800: 航空会社フルオペレーション クラスタ トポロジー — 10-actor 設計"
status: active
doc_type: adr
topic: airline-cluster
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - airline operations cluster (10 independent actors)
  - air-sched / air-book / air-yield / air-dcs / air-ops / air-crew / air-mro / air-sms / air-cargo / air-ffp の責務分離
  - cross-actor 連携配線 (IRROP / AOG / safety escalation 経路)
  - IATA / ICAO / EASA / FAA 標準準拠マッピング
related:
  - adr-0017-maritime-energy-cluster-topology
  - adr-0056-bpmn-as-actor
  - adr-2604282300
  - adr-0095-simplified-3layer-identity-rw-vault
supersedes: []
superseded_by: []
---

# Context

航空会社の運営 (airline full operation) は、複数の独立したビジネスドメインで構成される:

| ドメイン | 主要標準 | actor 候補 |
|---|---|---|
| スケジュール管理 | IATA SSIM, AIDX, Level 2/3 slot | air-sched |
| 予約・発券 | IATA NDC, ONE Order, ATPCO, BSP/ARC | air-book |
| 収益管理 | ATPCO, RBD, O&D, yield theory | air-yield |
| 地上運用 / DCS | IATA AHM, RP1745, CUTE/CUSS, APIS | air-dcs |
| 運航管理 / OCC | ICAO Doc 4444, ARINC 633, IFPS | air-ops |
| 乗務員管理 | EASA FTL/Part-FCL, FAA Part 117, FRMS | air-crew |
| 整備 / 耐空証明 | EASA Part-145/CAMO, FAA Part 121 | air-mro |
| 安全 / コンプライアンス | ICAO Annex 19 SMS, Annex 13, IOSA | air-sms |
| 貨物運用 | IATA CASS, CARGOIMP, e-AWB, DGR | air-cargo |
| FFP / ロイヤルティ | FFP tier / mileage / partner earn-burn | air-ffp |

telecom のモノリシック設計 (1 DID × 18 フェーズ) と異なり、航空は **事業者が異なるベンダーシステムを使用** (Amadeus/Sabre/Navitaire for DCS, Jeppesen for crew, AMOS for MRO 等)。maritime-energy ADR-0017 と同様に **クラスタ型** (独立 DID × クロスアクター配線) が最適。

既存との関係:
- `flight-offer` (fl1ghts1.etzhayyim.com) — 消費者向け運賃集約。航空会社内部システムとは独立。
- `vertex_airline` table — 42 IATA 航空会社レジストリ。本クラスタは FK 参照のみ、重複なし。
- Maps transit pipeline (OpenFlights/GTFS-JP) — 外部スケジュールデータ取込。`air-sched` の SSIM/AIDX は航空会社内部スケジュール SSoT。

# Decision

10 actor をクラスタ型トポロジーで構成する。各 actor は独立した DID (`did:web:{name}.etzhayyim.com`) を持ち、BPMN-as-actor (ADR-0056) パターンで実装する。

## アーキテクチャ図

```
                    ┌──────────────────────────────┐
                    │   air-sched                  │  ← スケジュール基盤
                    │   did:web:air-sched.etzhayyim.com  │    IATA SSIM / Level 2/3 Slot
                    │   8 BPMNs                    │
                    └────────────┬─────────────────┘
                                 │ schedule drives
        ┌────────────────────────┼──────────────────────┐
        ▼                        ▼                       ▼
┌───────────────┐  ┌─────────────────────┐  ┌───────────────────┐
│  air-book     │  │   air-yield         │  │   air-ops         │
│  PNR/NDC      │  │   RBD/ATPCO/O&D     │  │   IFPS/OFP/OCC   │
│  BSP/ARC      │  │   Overbooking       │  │   NOTAM/wx        │
│  8 BPMNs      │  │   8 BPMNs           │  │   8 BPMNs         │
└──────┬────────┘  └─────────────────────┘  └─────────┬─────────┘
       │ booking→checkin                               │ OFP→loadsheet
       ▼                                               ▼
┌───────────────┐                          ┌───────────────────┐
│  air-dcs      │ ←──── load sheet ────── │  air-crew         │
│  DCS/CUTE     │                          │  FTL/FRMS/Jepps   │
│  APIS/IATA    │                          │  8 BPMNs          │
│  RP1745       │                          └───────────────────┘
│  8 BPMNs      │
└───────────────┘

                    ┌──────────────────────────────┐
                    │   air-mro                    │  ← 整備鎖
                    │   Part-145/CAMO              │
                    │   AD/SB/MPD compliance       │
                    │   8 BPMNs                    │
                    └────────────┬─────────────────┘
                                 │ occurrence report
                                 ▼
                    ┌──────────────────────────────┐
                    │   air-sms                    │  ← 安全管理
                    │   ICAO Annex 19 SMS          │
                    │   IOSA / Annex 13            │
                    │   8 BPMNs                    │
                    └──────────────────────────────┘

┌───────────────┐                    ┌───────────────────┐
│  air-cargo    │                    │  air-ffp          │
│  e-AWB/CASS   │                    │  FFP Tier/Miles   │
│  ULD/DGR      │                    │  Partner earn/burn│
│  8 BPMNs      │                    │  8 BPMNs          │
└───────────────┘                    └───────────────────┘
```

## Actor 一覧

| actor | domain | nanoid | BPMNs | 主要標準 | pyzeebe module |
|---|---|---|---|---|---|
| air-sched | air-sched.etzhayyim.com | a1rsch3d | 8 | SSIM / AIDX / Slot | airline_sched |
| air-book | air-book.etzhayyim.com | a1rb00k1 | 8 | NDC / ONE Order / BSP | airline_book |
| air-yield | air-yield.etzhayyim.com | a1ry13ld | 8 | ATPCO / RBD / O&D | airline_yield |
| air-dcs | air-dcs.etzhayyim.com | a1rd3cs0 | 8 | AHM / RP1745 / CUTE | airline_dcs |
| air-ops | air-ops.etzhayyim.com | a1r0ps01 | 8 | ICAO 4444 / IFPS / ACARS | airline_ops |
| air-crew | air-crew.etzhayyim.com | a1rcr3w0 | 8 | FTL / FRMS / Part-FCL | airline_crew |
| air-mro | air-mro.etzhayyim.com | a1rmr001 | 8 | Part-145 / CAMO / MPD | airline_mro |
| air-sms | air-sms.etzhayyim.com | a1rsms01 | 8 | Annex 19 / IOSA / DGR | airline_sms |
| air-cargo | air-cargo.etzhayyim.com | a1rcarg0 | 8 | e-AWB / CASS / DGR | airline_cargo |
| air-ffp | air-ffp.etzhayyim.com | a1rffp01 | 8 | FFP / Tier / Partner | airline_ffp |

## NSID 構造

各 actor の XRPC NSID は `com.etzhayyim.apps.{camelCaseActor}.{operation}` に従う:
- `com.etzhayyim.apps.airSched.registerSchedule`
- `com.etzhayyim.apps.airBook.createPnr`
- `com.etzhayyim.apps.airYield.publishFareClass`
- `com.etzhayyim.apps.airDcs.processCheckIn`
- `com.etzhayyim.apps.airOps.fileFlightPlan`
- `com.etzhayyim.apps.airCrew.publishRoster`
- `com.etzhayyim.apps.airMro.createWorkOrder`
- `com.etzhayyim.apps.airSms.submitSafetyReport`
- `com.etzhayyim.apps.airCargo.createCargoBooking`
- `com.etzhayyim.apps.airFfp.enrollMember`

## Cross-Actor 配線

| 発火元 | イベント | 受信先 | 連携種別 |
|---|---|---|---|
| air-sched | schedule published | air-book (fare class open) | derive rule |
| air-sched | fleet assigned | air-crew (pairing constraint) | derive rule |
| air-book | PNR confirmed | air-dcs (checkin window open) | derive rule |
| air-book | IRROP trigger | air-book reprotect | self |
| air-yield | inventory gate | air-book (availability) | sync query |
| air-ops | OFP released | air-dcs (load sheet input) | derive rule |
| air-ops | delay > 30min | air-crew (reassign) | derive rule |
| air-dcs | departure closed | air-ops (ACARS dispatch) | derive rule |
| air-mro | tech occurrence | air-sms (safety report) | derive rule |
| air-mro | AOG declared | air-ops (cancel/divert) | derive rule |
| air-sms | safety bulletin | air-mro (AD/SB check) | derive rule |
| air-crew | fatigue risk HIGH | air-crew (reassign) | self |

## グラフスキーマ プレフィックス規約

- Vertex: `vertex_air_{actor_short}_{entity}` — e.g., `vertex_air_sched_schedule`, `vertex_air_book_pnr`
- Edge: `edge_air_{relation}` — e.g., `edge_air_pnr_has_ticket`
- MV: `mv_air_{purpose}` — e.g., `mv_air_schedule_daily`
- 既存 `vertex_airline` への FK 参照: `carrier_code VARCHAR(3)` カラムで結合 (IATA 2文字コード)

## PII Tier 分類

| actor | tier | 代表データ | 対策 |
|---|---|---|---|
| air-book | Tier 3 (full PII) | passenger name, DOB, passport | vault:// pointer, Signal E2E |
| air-dcs | Tier 3 | seat assignment, APIS data | sensitivity_ord=3, hash PNR |
| air-crew | Tier 2 | crew name, qualification, duty | hashed crew_did |
| air-sms | Tier 2-3 | confidential safety report | sha256: payload hash, vault:// |
| air-ffp | Tier 3 | member profile, address | vault:// for PII fields |
| air-sched/yield/ops/mro/cargo | Tier 1 | operational data only | no PII |

## 実装フェーズ

| フェーズ | 内容 | Migration |
|---|---|---|
| P1 | air-sched schema + BPMNs | 20260507600000 |
| P2 | air-book schema + BPMNs | 20260507610000 |
| P3 | air-yield schema + BPMNs | 20260507620000 |
| P4 | air-dcs schema + BPMNs | 20260507630000 |
| P5 | air-ops schema + BPMNs | 20260507640000 |
| P6 | air-crew schema + BPMNs | 20260507650000 |
| P7 | air-mro schema + BPMNs | 20260507660000 |
| P8 | air-sms schema + BPMNs | 20260507670000 |
| P9 | air-cargo schema + BPMNs | 20260507680000 |
| P10 | air-ffp schema + BPMNs | 20260507690000 |
| BPMN seed | 全 80 BPMN rows INSERT | 20260507700000 |

## 既存 vertex_airline との関係

`flight-offer` の `vertex_airline` (42 IATA 航空会社, carrier_code PK) を権威ソースとして参照。本クラスタは `carrier_code VARCHAR(3)` で FK 的に結合し、重複 INSERT しない。`air-sched.registerSchedule` → `carrier_code` lookup → `vertex_airline.carrier_code`.
