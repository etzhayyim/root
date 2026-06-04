# Crawl Resource Entity Flow App Design

Date: 2026-03-13
Scope: `crawler.gftd.ai` が分類済みの Web ページを入力として、`ai-gftd-project-resources` 内で `resource`、`entity`、`resource flow` に正規化し、下流 (`yabai`, search, graph, analytics) に渡す App の設計。

## 1. Problem

現状の `ai-gftd-project-resources` は crawler 結果を `content/crawl/job`, `content/crawl/page`, `content/crawl/site` に保存できるが、その先の

- ページ本文から何を `resource` とみなすか
- どの `entity` に紐付けるか
- どの `resource flow` に落とすか

を自動判定して永続化する標準 app がない。

そのため downstream は `CrawlPage` を直接解釈する必要があり、各 app が個別にページ解析・名寄せ・分類を実装してしまう。

## 2. Goal

新 app は次を担う。

1. `content/crawl/page/*.jsonld` から分類済みページを読む
2. ページ内の candidate resource を抽出する
3. candidate を canonical entity に resolve する
4. entity ごとに適切な `resource flow` に振り分ける
5. Arrow/LanceDB projection table を更新する
6. `#yabai-resource-feed` に必要な entity event を publish する

## 3. Component

```
60-apps/ai-gftd-project-resources/wasm/ai-gftd-wasm-crawl-resource-flow-crf8m2q1/
├── main.go
├── db_schema.go
├── db_flow.go
├── db_entity.go
├── db_projection.go
├── classifier.go
├── extractor.go
├── resolver.go
├── matrix_commands.go
├── publisher.go
├── magatama.toml
├── App manifest
└── wit/world.wit
```

Nanoid: `crf8m2q1`
Subdomain: `crf8m2q1.gftd.ai`

役割:

- command: Matrix event で ingest / classify / republish を受ける
- query: XRPC で page-to-entity / page-to-flow 結果を返す
- persistence: Tonbo Flight SQL / LanceDB projection

## 4. Input Contract

### Primary Input

- `content/crawl/page/<result_id>.jsonld`
- `@type = gftd:CrawlPage`
- crawler または前段 classifier が付与した以下の情報を利用する
  - `url`
  - `name`
  - `description`
  - `inLanguage`
  - `httpStatus`
  - `pageCategory`
  - `contentClass`
  - `extractedText`
  - `links`
  - `emails`
  - `phoneNumbers`
  - `ipAddresses`
  - `organizations`
  - `persons`

### Secondary Input

- `content/crawl/site/<domain>.jsonld`
- 既存 `resources` canonical source
  - `content/public-company/**`
  - `content/legal/**`
  - `content/ti/**`
  - `content/public/**`

## 5. Output Model

この app は 3 系統を出力する。

### 5.1 Entity Resource

ページ由来の正規化 entity。**source of truth は Arrow schema / LanceDB table** とする。

対象例:

- `Organization`
- `Person`
- `WebSite`
- `WebPage`
- `ContactPoint`
- `IPAddress`
- `Dataset`
- `Article`
- `LegalCase`

### 5.2 Resource Flow

ページから entity に落ちる処理結果を append-only に記録する。**source of truth は Arrow/LanceDB**。

`resource flow` は「どのページから、どの抽出器を通り、どの entity/resource に配賦されたか」の lineage 単位。

### 5.3 Current Projection

高速 query 用の current/projection table。JSON-LD は必要なら export/view として生成するが、保存本体にはしない。

- `crawl_resource_pages_current`
- `crawl_resource_entities_current`
- `crawl_resource_flows_current`
- `crawl_resource_page_entity_edges`

## 6. Resource Flow Taxonomy

各 candidate resource は下記 flow に分類する。

| Flow | 用途 | 主な entity |
|---|---|---|
| `identity` | 人・組織・サイトの同定 | `Person`, `Organization`, `WebSite`, `ContactPoint`, `IPAddress` |
| `contact` | email / phone / IP / SNS 等の連絡先/到達点 | `ContactPoint`, `IPAddress` |
| `publication` | 記事・発表・ブログ・アナウンス | `Article`, `BlogPosting`, `Report` |
| `legal` | 判決・処分・規制文書 | `Legislation`, `LegalCase`, `GovernmentService` |
| `commercial` | 商品・サービス・決済・販売導線 | `Product`, `Offer`, `Service`, `Organization` |
| `security` | IOC, phishing, malware, abuse, suspicious infra | `IPAddress`, `WebSite`, `ContactPoint`, `SoftwareApplication` |
| `dataset` | CSV/JSON/PDF/統計資料など再利用可能資源 | `Dataset`, `DataDownload` |
| `relationship` | ownership / operates / linked-to など graph edge | entity-edge only |

1 ページは複数 flow に入ってよい。正規入口は single classification ではなく multi-flow assignment。

## 7. Classification Pipeline

```
CrawlPage
  -> page classifier
  -> candidate extractor
  -> entity resolver
  -> flow assigner
  -> evidence / relation builder
  -> JSON-LD writer
  -> Matrix publisher
```

### Step 1: Page Classifier

ページ全体を coarse category に分類する。

- `profile-page`
- `contact-page`
- `product-page`
- `article-page`
- `legal-page`
- `security-report`
- `dataset-page`
- `directory-page`
- `landing-page`
- `unknown`

用途:

- 後段 extractor の優先順位を切り替える
- false positive を抑える
- review queue を制御する

### Step 2: Candidate Extractor

抽出器は page category ごとに複数動く。

- `extractPersons`
- `extractOrganizations`
- `extractWebSites`
- `extractContacts`
- `extractIPAddresses`
- `extractLegalRefs`
- `extractOfferAndProduct`
- `extractDatasets`

出力は共通 `ResourceCandidate`:

```json
{
  "candidateId": "cand_xxx",
  "pageId": "crawl/page/...",
  "kind": "contact",
  "subkind": "email",
  "rawValue": "support@example.com",
  "normalizedValue": "support@example.com",
  "confidence": 0.91,
  "sourceSpan": "mailto:support@example.com"
}
```

### Step 3: Entity Resolver

candidate を canonical entity に解決する。

優先順:

1. exact match: 既存 canonical ID / normalized value
2. alias match: alias / alternateName / sameAs
3. scoped match: domain, email domain, E.164, CIDR
4. graph match: site owner / linked organization / referenced legal entity
5. create provisional entity

resolve 失敗時は provisional entity を作る。

- `entity_status = provisional`
- `resolution_status = unresolved`
- review queue に送る

### Step 4: Flow Assigner

candidate + resolved entity + page category をもとに multi-flow assignment を作る。

例:

- phishing report 内の `support@evil-bank-alert.com`
  - `contact`
  - `security`
- 行政 PDF 内の法人名
  - `identity`
  - `legal`
- 企業 IR ページ
  - `identity`
  - `publication`
  - `dataset`

### Step 5: Relation Builder

ページから entity 間 edge を作る。

例:

- `page -> mentions -> organization`
- `website -> exposes -> contactpoint`
- `organization -> operates -> website`
- `article -> reports_on -> legal_case`
- `security_report -> references -> ip_address`

## 8. Arrow / Flight SQL Table Design

### Table: `crawl_resource_pages_current`

| Column | Type | Description |
|---|---|---|
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `page_id` | String | `_doc_id` |
| `url` | String | canonical URL |
| `domain` | String | normalized host |
| `page_category` | String | coarse classifier result |
| `content_class` | String | crawler-side class |
| `title` | String | page title |
| `summary` | String | summary/snippet |
| `http_status` | Int64 | HTTP status |
| `extracted_at` | String | extraction timestamp |
| `candidate_count` | Int64 | extracted candidates |
| `entity_count` | Int64 | resolved entities |
| `flow_count` | Int64 | assigned flows |
| `review_status` | String | `auto-approved`, `needs-review`, `rejected` |
| `updated_at` | String | timestamp |

### Table: `crawl_resource_entities_current`

| Column | Type | Description |
|---|---|---|
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `entity_id` | String | `_doc_id` |
| `entity_type` | String | canonical type |
| `canonical_name` | String | |
| `normalized_value` | String | email/phone/ip/domain |
| `resolution_status` | String | `resolved`, `provisional`, `merged` |
| `source_page_count` | Int64 | evidence page count |
| `primary_flow` | String | main assigned flow |
| `risk_hint` | String | `none`, `watch`, `high` |
| `updated_at` | String | timestamp |

### Table: `crawl_resource_flows_current`

| Column | Type | Description |
|---|---|---|
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `flow_id` | String | `_doc_id` |
| `page_id` | String | source page |
| `entity_id` | String | target entity |
| `flow_type` | String | taxonomy above |
| `candidate_kind` | String | source candidate type |
| `assignment_confidence` | Float64 | assignment score |
| `resolver` | String | exact/alias/graph/provisional |
| `publisher_status` | String | `pending`, `published`, `skipped` |
| `updated_at` | String | timestamp |

### Table: `crawl_resource_page_entity_edges`

| Column | Type | Description |
|---|---|---|
| `org_id` | String | RLS |
| `user_id` | String | RLS |
| `actor_id` | String | RLS |
| `edge_id` | String | `_doc_id` |
| `page_id` | String | source page |
| `entity_id` | String | target entity |
| `relation` | String | `mentions`, `exposes`, `operates`, `references` |
| `confidence` | Float64 | edge confidence |
| `updated_at` | String | timestamp |

## 9. Deterministic Key Rules

Arrow/LanceDB row key は以下で安定化する。

- page projection: `crawl-resource/page/<page_id>`
- entity: `entity/<entity_type>/<stable_key>`
- resource flow: `resource-flow/<page_id>/<entity_id>/<flow_type>`
- relation edge: `entity-edge/<page_id>/<entity_id>/<relation>`

同一 page 再処理でも `entity_id` が変わらないように、以下を stable key に使う。

- website: normalized domain
- webpage: canonical URL
- email: normalized email
- phone: normalized E.164 or digit-normalized
- ip: canonical IP or CIDR
- organization/person: resolver result、無ければ provisional hash

## 10. Transport Design

## Matrix Commands

| Event Type | Description |
|---|---|
| `org.gftd.command.crawl-resource-flow.ingest-page` | 単一 page を取り込み |
| `org.gftd.command.crawl-resource-flow.ingest-batch` | 複数 page を再処理 |
| `org.gftd.command.crawl-resource-flow.resolve-entity` | provisional entity の名寄せ |
| `org.gftd.command.crawl-resource-flow.publish-yabai` | high-risk candidate の publish |
| `org.gftd.command.crawl-resource-flow.review` | review 結果反映 |

### XRPC Query

```
POST /xrpc/gftd.crawl_resource_flow.v1.CrawlResourceFlowQueryService/GetPageFlow
POST /xrpc/gftd.crawl_resource_flow.v1.CrawlResourceFlowQueryService/ListPageFlows
POST /xrpc/gftd.crawl_resource_flow.v1.CrawlResourceFlowQueryService/GetEntityResolution
POST /xrpc/gftd.crawl_resource_flow.v1.CrawlResourceFlowQueryService/ListPendingReviews
POST /xrpc/gftd.crawl_resource_flow.v1.CrawlResourceFlowQueryService/SearchEntitiesByValue
```

## 11. Yabai / Search / Graph Integration

### Yabai

下記条件の flow は `#yabai-resource-feed` publish 対象。

- `flow_type = security`
- `entity_type in (ContactPoint, IPAddress, WebSite, Organization, Person)`
- `risk_hint != none`
- confidence threshold 以上

publish payload:

```json
{
  "entityId": "entity/contactpoint/support-evil-bank-alert-com",
  "entityType": "ContactPoint",
  "name": "support@evil-bank-alert.com",
  "contacts": ["support@evil-bank-alert.com"],
  "contactKind": "email",
  "normalizedValue": "support@evil-bank-alert.com",
  "source": "resources/crawl-resource-flow",
  "category": "FraudSignal",
  "summary": "Email extracted from phishing-classified page",
  "confidence": 0.93,
  "severity": 4,
  "probability": 0.08
}
```

### Search

page, entity, flow を別 index にせず、search projection で join できるよう flat export を用意する。

### Graph

`crawl_resource_page_entity_edges` を graph app が pull できるようにする。独自 graph store をこの app 内には持たない。

## 12. Review and Governance

自動確定してよいのは以下だけ。

- exact normalized contact match
- domain exact match
- canonical source site 上の organization exact match

review 必須:

- person/organization fuzzy match
- single-source legal accusation
- extracted values が watchlist に部分一致のみ
- OCR 由来 candidate

review queue 出力:

- `content/review/crawl-resource-flow/<review_id>.jsonld`

## 13. Failure Policy

- extractor 失敗: page 単位で `review_status = needs-review`
- resolver 失敗: provisional entity 作成で継続
- publisher 失敗: `publisher_status = pending` のまま再試行
- downstream 未接続でも page/entity/flow 永続化は成功扱い

## 14. Initial Increment

Phase 1:

- `contact-page`, `security-report`, `article-page` のみ対応
- entity は `WebSite`, `ContactPoint`, `IPAddress`, `Organization`
- flow は `contact`, `security`, `publication`, `identity`
- `yabai` publish のみ実装

Phase 2:

- `legal-page`, `dataset-page`, `product-page` を追加
- relation builder 強化
- provisional review UI を追加

Phase 3:

- LLM-assisted resolver
- cross-page graph evidence aggregation
- search/analytics 連携

## 15. Why This App Belongs in `resources`

- crawler は取得責務に集中するべきで、entity canonicalization まで持たせない
- `resources` は Arrow schema / LanceDB projection を canonical source にできるため、entity/resource flow の永続化責務に合う
- `yabai` は risk evaluation に集中し、page parsing を再実装しなくて済む

この app を入れることで、`crawler -> resources(crawl page) -> crawl-resource-flow -> yabai/search/graph` の責務分離が明確になる。
