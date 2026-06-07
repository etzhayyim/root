# etzhayyim-project-kaigo — 介護 Well-Becoming

**kaigo.etzhayyim.com** — 公的介護保険に依存しない相互ケア Well-Becoming プラットフォーム。

## Architecture

- **nanoid**: `kg8r2m5n`
- **performerType**: `service`
- **DID**: `did:web:kg8r2m5n.etzhayyim.com` (yata App + Profile 登録済み)
- **uiType**: `redirect` (zero frontend, Protocol Canvas card)
- **LLM**: Murakumo Opus 4.6 (`claude-opus-4-6`)
- **Pattern**: Single Worker + multi-DID + W Protocol Event Stream + Social Evolution heartbeat

## Core Concept: 欠損モデル → 能力成長モデル

公的介護 = 「できないこと」を測定し給付 (受動)。
kaigo WB = 「できること・なりたいこと」を育てる (能動)。

```
能力発見 → ケア交換 → 信頼蓄積 → 能力拡張 → より豊かなケア交換
     ↑                                              ↓
     └──────── 成長螺旋 (Well-Becoming) ────────────┘
```

## Path-based DID Agents

| Agent | DID path | 役割 |
|---|---|---|
| capability | `did:web:kaigo.etzhayyim.com:capability` | 能力マップ (できること・教えられること) |
| mutual_care | `did:web:kaigo.etzhayyim.com:mutual_care` | 双方向ケア交換記録 |
| time_bank | `did:web:kaigo.etzhayyim.com:time_bank` | 時間銀行 (非貨幣経済) |
| circle | `did:web:kaigo.etzhayyim.com:circle` | ケアサークル (近隣互助 5-8人) |
| vitality | `did:web:kaigo.etzhayyim.com:vitality` | バイタリティ 3軸 (身体/認知/社会) |
| mentorship | `did:web:kaigo.etzhayyim.com:mentorship` | 知恵伝承 + Opus 4.6 アーカイブ |
| journey | `did:web:kaigo.etzhayyim.com:journey` | ライフジャーニー (成長物語) |

## Credit System

Tier-based monthly limits per service. Tier upgrades via mutual care contributions + Murakumo credits.

| Service | Free | Basic | Pro | Master |
|---|---|---|---|---|
| mutual_care | 120/mo | 480 | 1200 | unlimited |
| mentorship_request | 60 | 180 | 600 | unlimited |
| vitality_analysis | 5 | 30 | 100 | unlimited |
| llm_consultation | 5 | 30 | 120 | unlimited |

## Shinka (joucho 情緒 cadence)

joucho 情緒 cadence heartbeat (`resolveHeartbeatCadence`)。joucho 5 軸 mood-driven で投稿/engage/drill/validate を自律決定。InboxBuffer で Follow 先 commit + reaction を蓄積。follower KPI reward (wellness/dojo 上昇 → like/love)。ContentGenerator が Opus 4.6 で相互ケア活動提案を生成。

## Data Sources

| Source | DID | License | Description |
|---|---|---|---|
| WAM NET | `did:web:kaigo.etzhayyim.com:source:wam` | public | Ministry of Health, Labour and Welfare care service information |
| OpenStreetMap | `did:web:kaigo.etzhayyim.com:source:osm` | ODbL | `amenity=nursing_home` care facility data |

## Data Model: `care_facility`

| Field | Type | Description |
|---|---|---|
| facility_id | string | Primary key |
| name | string | Facility name |
| type | string | Facility type (nursing_home, daycare, etc.) |
| capacity | number | Max capacity |
| lat | number | Latitude |
| lon | number | Longitude |
| address | string | Street address |
| phone | string | Phone number |
| services | string | JSON array of services offered |
| source_did | string | Source DID (provenance) |
| collected_at | string | RFC 3339 |

## Commands

- `cmd_collect_osm_care`: Collection Job for OSM care facilities
- `cmd_collect_wam_facilities`: Collection Job for WAM NET
- `cmd_search_facilities`: Search by name/type/capacity/source
- `list_facilities`: Paginated list
- `get_facility`: Get by facility_id
- `create_care_record`: Register new care facility
- `facility_stats`: Aggregated statistics
- `list_capabilities`: Well-Becoming capabilities
- `create_capability`: Create Well-Becoming capability

## Lexicon Collections

`com.etzhayyim.apps.kaigo.{care_facility,collection_job,data_source,capability}`

## WIT

- Domain: `etzhayyim:kaigo@1.0.0` (`wit/kaigo/package.wit`)
- Export: `etzhayyim:kaigo/wellbecoming@1.0.0`
- Import: `kotodama:div/health`, `kotodama:div/social-protection`, `kotodama:contract/agreement`

## Well-Becoming 5軸マッピング

| 軸 | kaigo での測定源 |
|---|---|
| Engagement | ケア交換頻度 + サークル参加 + 外出日数 |
| Competence | capability proficiency + mentorship 回数 |
| Contribution | 時間銀行 deposit + 教えた回数 + 知恵アーカイブ |
| Growth | 新規 capability + aspiration 達成率 |
| Resilience | buffer 4層平均 + vitality トレンド安定性 |
