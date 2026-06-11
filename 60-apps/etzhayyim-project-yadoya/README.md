# etzhayyim-project-yadoya

Autonomous hotel search and reservation platform delivered as App components.

## Domain

- URL: `https://yadoya.etzhayyim.com`
- API: `https://{nanoid}.etzhayyim.com/xrpc`
- Component: `60-apps/etzhayyim-project-yadoya/wasm/yadoya-ui-b7r4n2xq`

## Business Plan (v1.0)

### Vision

世界中の宿泊施設を AI Agent と人間の両方が検索・予約できる自律型プラットフォーム。MCP ツール経由で AI Agent が直接予約操作を行い、Web UI で人間ユーザーがビジュアルに検索・予約を行う。

### Target Market

| セグメント | 説明 | 優先度 |
|---|---|---|
| AI Agent 自律予約 | MCP protocol 対応 AI Agent からの検索・比較・予約 | Primary |
| 法人出張管理 | APQC フレームワークによる出張宿泊の一元管理 | Primary |
| 個人旅行者 (B2C) | 16 言語 Web UI による直接検索・予約 | Secondary |
| 旅行代理店 API (B2B) | XRPC API 経由での在庫照会・一括予約 | Tertiary |

### Revenue Model

| 収益源 | Phase | 説明 |
|---|---|---|
| アフィリエイト手数料 | Phase 2 | 予約成立時のホテル公式サイトからのコミッション (3-12%) |
| MCP API 利用料 | Phase 3 | AI Agent からのツール呼び出し従量課金 |
| 法人サブスクリプション | Phase 4 | 組織単位の出張管理ダッシュボード |
| プレミアムデータ API | Phase 4 | ホテル在庫・価格データのリアルタイムフィード |

### Competitive Advantages

- MCP/cross-actor 対応で AI Agent から直接予約可能 (業界初のネイティブ対応)
- APQC/ISIC/ISCO プロセス標準によるホテル業務の構造化
- 16 言語ネイティブ対応 (翻訳 API 依存なし)
- B2 Custom Domain による低レイテンシ静的配信

## Implementation Roadmap

### Phase 1 — Foundation (MVP) [COMPLETED]

- App component (yadoya-ui-b7r4n2xq) — TinyGo, port 8164
- Static catalog: 20 hotels across 7 regions
- 16-language i18n (en, ja, es, fr, de, pt, it, ru, zh, ko, ar, hi, bn, tr, id, vi)
- MCP tools: search, list, reserve, heartbeat, scheduler, process-map
- APQC/ISIC/ISCO process taxonomy mapping
- Auto-collection scheduler (interval-based probing)
- Static HTML frontend (vanilla JS, responsive grid)
- WADM manifest (kotodama-runtime namespace)

### Phase 2 — Persistence & Scale [IN PROGRESS]

- performer/rdbms (cypher graph RDBMS) persistence
- Performer framework migration (70-tools/performer)
- SvelteKit frontend → B2 per-site bucket (yadoya-etzhayyim-ai)
- XRPC API (proto/etzhayyim/yadoya/v1/yadoya.proto)
- Real-time price collection via wasi:http/outgoing-handler
- Hotel catalog expansion: 100+ properties
- Affiliate link integration
- Clerk JWT authentication

### Phase 3 — AI Agent Gateway [PLANNED]

- MCP Gateway integration
- cross-actor protocol support (multi-step booking workflows)
- Payment gateway (Stripe Connect)
- Hotel catalog: 500+ properties

### Phase 4 — Enterprise & B2B [PLANNED]

- Organization-scoped booking (Clerk org_id → KV boundary)
- Approval workflow (APQC 2.x → manager approval → booking)
- Travel policy enforcement (budget, preferred hotels, blackout dates)
- Reporting dashboard (analytics, spend by org/dept)
- B2B API (bulk search, allocation, group bookings)
- Hotel partner portal

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/heartbeat` | GET | Operational status and scheduler metrics |
| `POST /api/scheduler/run` | POST | Manual trigger for hotel collection |
| `GET /api/languages` | GET | List supported language codes |
| `GET /api/i18n?lang=<code>` | GET | Internationalization labels |
| `GET /api/hotels` | GET | Published hotel catalog |
| `GET /api/search` | GET | Search hotels (city, country, dates, guests) |
| `POST /api/reservations` | POST | Create hotel reservation |
| `GET /api/process-map` | GET | APQC/ISIC/ISCO connector status |
| `POST /api/mcp` | POST | MCP JSON-RPC endpoint |

## MCP Tools

| Tool | Description |
|---|---|
| `yadoya.search_hotels` | Search global hotels with APQC context |
| `yadoya.list_published_hotels` | List full published hotel catalog |
| `yadoya.create_reservation` | Create reservation with process tags |
| `yadoya.list_supported_languages` | List 16 supported languages |
| `yadoya.get_heartbeat` | Operational status |
| `yadoya.run_scheduler` | Trigger data collection |
| `yadoya.describe_process` | Booking process model |

## Hotel Coverage

- **20 properties** across **7 regions** (Asia, Europe, Middle East, North/South America, Africa, Oceania)
- Price range: JPY 20,000 - 240,000 / night
- Collection date: 2026-02-22
- Source: official hotel websites (per-record `source_url`)

## Process Taxonomy

### APQC

| Code | Process | Yadoya Mapping |
|---|---|---|
| 2.1 | Develop Sales Strategy | Revenue model, channel strategy |
| 2.2 | Manage Sales Pipeline | Search-to-booking funnel |
| 2.3 | Manage Orders & Quotes | Reservation lifecycle |
| 5.1 | Plan Customer Service | Multilingual support |
| 5.2 | Deliver Service | Catalog delivery, booking execution |
| 5.3 | Manage Service Quality | Data collection, health monitoring |

### ISIC

- Primary: `I5510` Hotels and similar accommodation
- Related: `I5520` Short-stay, `N7911` Travel agency, `N7912` Tour operator

### ISCO

| Code | Role | Yadoya Mapping |
|---|---|---|
| 4224 | Hotel Receptionists | Check-in/out automation |
| 5113 | Travel Guides | AI-augmented concierge |
| 5151 | Housekeeping Supervisors | Workflow integration |
| 1411 | Hotel Managers | Partner portal |

## Scheduler / Heartbeat

- Auto-collection on heartbeat/search/hotels access
- Manual trigger: `POST /api/scheduler/run`
- Config: `YADOYA_SCHEDULER_ENABLED` (default: `true`)
- Config: `YADOYA_SCHEDULER_INTERVAL_SEC` (default: `1800`)
- Config: `YADOYA_COLLECTION_TIMEOUT_MS` (default: `200`)

## Architecture

```
Browser/AI Agent
  ├─ HTML/JS/CSS → yadoya.etzhayyim.com (R2 Custom Domain, per-site bucket)
  └─ API → 1.etzhayyim.com/xrpc → Envoy Gateway
              ↓
       yadoya-ui-b7r4n2xq (App, TinyGo)
              ├─ wasi:http/incoming-handler (API)
              ├─ wasi:http/outgoing-handler (hotel site probing)
              ├─ performer/rdbms (cypher graph RDBMS)
```
