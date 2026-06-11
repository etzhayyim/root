# Crawler Murakumo Resource Intel Design

Date: 2026-03-13
Scope: `crawler.etzhayyim.com` が収集した Web データを、`murakumo` を用いた抽出・分類・要約で強化し、`collector`、`resources`、`entity`、`resourceflow`、`intel` に段階的に格納する設計。

## 1. Goal

この設計の目的は、`crawler.etzhayyim.com` のページ取得結果を単なる `CrawlPage` JSON-LD で終わらせず、次の 5 層に分離して再利用可能にすること。

1. `collector`: 収集実行の事実、raw evidence、connector 状態
2. `resources`: 再利用可能な公開資源・文書・サイト・データセット
3. `entity`: 人、組織、サイト、IP、連絡先などの canonical / provisional entity
4. `resourceflow`: どのページから何が抽出され、どの entity / resource に割り当てられたかの lineage
5. `intel`: observation、link、fusion、alert としての分析結果

## 2. Core Principle

- 収集と分析を分離する
- raw payload は `collector` / crawl storage に残す
- canonical object は `resources` / `entity` に置く
- page から canonical object に落とした経路は `resourceflow` に置く
- threat / anomaly / confidence 付きの判断結果は `intel` に置く
- `murakumo` は既定で `https://murakumo.etzhayyim.com/api/openai/v1/chat/completions` を使い、分類・抽出・要約・risk hint 生成に使う
- public query は XRPC (`/xrpc/{NSID}`)、command は W Protocol Event Stream に寄せる
- structured persistence は Tonbo Flight SQL + Arrow-compatible schema を正とする

## 3. End-to-End Flow

```text
crawler.etzhayyim.com
  -> content/crawl/job/*.jsonld
  -> content/crawl/page/*.jsonld
  -> content/crawl/site/*.jsonld

Crawl ingest command
  -> collector normalization
  -> murakumo enrichment
  -> entity resolution
  -> resourceflow assignment
  -> resources upsert
  -> intel observation upsert
  -> fusion / alert update
```

## 4. Role Of Murakumo

`murakumo` はこの設計では marketplace ではなく、まず OpenAI-compatible LLM surface を analyzer として使う。

主用途:

- page category classification
- candidate extraction の補助
- organization / person / dataset / legal reference の補完抽出
- summary / topic / language / risk hint 生成
- phishing / abuse / suspicious infra など security lens の一次判定
- intel observation 用の narrative summary 生成

非用途:

- canonical ID の最終決定
- RLS を跨ぐ勝手な参照
- legality 判定の最終確定

canonicalization は rule-based resolver と既存 graph を優先し、`murakumo` は evidence augmentation に限定する。

## 5. Layer Responsibilities

### 5.1 Collector

`collector` は「何をいつどの connector で取りに行ったか」を保持する実行層。

保持対象:

- crawl run / collection run metadata
- seed URL、domain、schedule、priority
- fetch result、HTTP status、headers、content hash
- raw extracted text、raw HTML / blob ref
- connector health、retry、failure reason

代表 table:

- `collector_runs_current`
- `collector_sources_current`
- `collector_evidence_current`

`crawler.etzhayyim.com` の `CrawlJob` / `CrawlPage` は collector にとって外部 connector 由来 evidence として扱う。

### 5.2 Resources

`resources` は公開再利用可能な文書・サイト・データセット・記事・法令・企業 profile を置く。

格納対象:

- `WebPage`
- `WebSite`
- `Article`
- `Dataset`
- `Report`
- `LegalCase`
- `Legislation`
- `Product` / `Service` のうち公開資源として扱うもの

格納方針:

- page 自体の canonical public representation を `resources` に置く
- public export 可能な summary / metadata を JSON-LD export する
- private raw payload は `resources` に直置きしない

### 5.3 Entity

`entity` は page から抽出された主体・対象の canonical registry。

対象:

- `Person`
- `Organization`
- `WebSite`
- `ContactPoint`
- `IPAddress`
- `SoftwareApplication`
- `Place`

状態:

- `resolved`
- `provisional`
- `merged`

主キーは canonical ID を使い、未解決時だけ provisional ID を発行する。

### 5.4 Resourceflow

`resourceflow` は page から resource / entity へ落ちる lineage を保持する。

例:

- どの `CrawlPage` から
- どの extractor / model version を通り
- どの candidate が作られ
- どの resolver rule で
- どの entity / resource に配賦されたか

これにより downstream は「なぜこの entity が作られたか」を説明できる。

### 5.5 Intel

`intel` は観測、相関、スコア、アラートを扱う分析層。

対象:

- `observation`
- `source`
- `entity link`
- `hypothesis score`
- `alert`
- `case`

`resources` に置いた public object のうち、security / threat / anomaly / watch 対象になるものだけを `intel_observations_current` に正規化する。

## 6. Pipeline Stages

### Stage 1: Crawl ingest

入力:

- `content/crawl/page/<result_id>.jsonld`
- `content/crawl/site/<domain>.jsonld`

処理:

- content hash dedupe
- domain normalization
- blob reference linkage
- collector evidence row 作成

出力:

- `collector_evidence_current`
- `crawl_resource_pages_current`

### Stage 2: Murakumo enrichment

入力:

- page title
- description
- extracted text
- links / emails / phones / organizations / persons

処理:

- page category classification
- structured candidate extraction
- concise summary
- language / region / risk hint
- analytic lens tagging

出力の基本 shape:

```json
{
  "pageCategory": "security-report",
  "summary": "Suspicious domain impersonating financial support portal.",
  "analyticLens": ["OSINT", "WEBINT", "CYBINT"],
  "riskHint": "high",
  "candidates": [
    {
      "kind": "organization",
      "rawValue": "Example Bank Support",
      "normalizedValue": "example bank support",
      "confidence": 0.88
    }
  ]
}
```

### Stage 3: Entity resolution

優先順:

1. exact identifier match
2. normalized domain / email / phone / IP match
3. alias / sameAs match
4. graph adjacency match
5. provisional entity creation

出力:

- `crawl_resource_entities_current`
- `crawl_resource_page_entity_edges`

### Stage 4: Resourceflow assignment

flow taxonomy:

- `identity`
- `contact`
- `publication`
- `legal`
- `commercial`
- `security`
- `dataset`
- `relationship`

出力:

- `crawl_resource_flows_current`

### Stage 5: Resource upsert

page を public reusable resource に変換できる場合だけ `resources` に昇格する。

昇格条件:

- article / report / dataset / legal material として再利用価値がある
- minimum metadata を満たす
- raw-only ではない

出力例:

- `content/public/**`
- `content/legal/**`
- `content/ti/**`
- `content/intel/public/**`

### Stage 6: Intel observation upsert

security / threat / anomaly / watch の lens が付いた page / entity / flow を `intel` に転写する。

マッピング:

- `source_family = public`
- `collection_method = crawl`
- `analytic_lens = WEBINT | SOCMINT | CYBINT | FININT ...`
- `source_ref = crawl/page/<result_id>`
- `subject_entity_id = resolved entity id`

出力:

- `intel_observations_current`
- `intel_links_current`
- `intel_sources_current`
- 必要に応じて `intel_alerts_current`

## 7. Canonical Storage Mapping

| Layer | Primary record | Main storage |
|---|---|---|
| `collector` | run, source, raw evidence | Tonbo Flight SQL current tables + blob refs |
| `resources` | reusable public documents | project content JSON-LD export + projection table |
| `entity` | canonical / provisional entities | `crawl_resource_entities_current` |
| `resourceflow` | page-to-entity lineage | `crawl_resource_flows_current`, `crawl_resource_page_entity_edges` |
| `intel` | observation / alert / fusion | `intel_*_current` tables |

## 8. Recommended Table Set

最小構成は次の 10 table。

- `collector_runs_current`
- `collector_sources_current`
- `collector_evidence_current`
- `crawl_resource_pages_current`
- `crawl_resource_entities_current`
- `crawl_resource_flows_current`
- `crawl_resource_page_entity_edges`
- `intel_observations_current`
- `intel_links_current`
- `intel_alerts_current`

必要なら `intel_fusion_scores_current` と `intel_cases_current` を後段で追加する。

## 9. Public vs Private Boundary

public に出してよいもの:

- page title
- canonical URL
- public summary
- public entity profile
- published article / dataset / legal metadata
- sanitized intel summary

private に閉じるもの:

- raw HTML
- full extracted text のうち権利・ポリシー上 problem があるもの
- access-controlled observation detail
- analyst notes
- intermediate prompt / model trace

## 10. Query Surfaces

public / first-party query は XRPC (`/xrpc/{NSID}`)。

候補:

- `CrawlerResourceQueryService/GetPage`
- `CrawlerResourceQueryService/ListPageEntities`
- `CrawlerResourceQueryService/ListPageFlows`
- `CrawlerResourceQueryService/GetEntity`
- `IntelQueryService/ListObservations`
- `IntelQueryService/GetFusionGraph`

command は Matrix event。

候補:

- `org.etzhayyim.command.collector.crawl.ingest`
- `org.etzhayyim.command.collector.crawl.reanalyze`
- `org.etzhayyim.command.resources.entity.resolve`
- `org.etzhayyim.command.intel.collection.run`

## 11. Recommended Ownership Split

- `crawler.etzhayyim.com`: fetch / render / frontier / dedupe / page JSON-LD
- `collector`: run orchestration / evidence registry / raw lineage
- `murakumo`: extraction / classification / summarization / risk hint
- `resources`: reusable document publication
- `entity`: canonical subject registry
- `resourceflow`: explainable transformation lineage
- `intel`: observation / fusion / alert

## 12. Initial Implementation Order

1. `crawler` page ingest を `collector_evidence_current` と `crawl_resource_pages_current` に接続
2. `murakumo` enrichment で `pageCategory`, `summary`, `analyticLens`, `riskHint`, `candidates` を出す
3. entity resolver を追加して `crawl_resource_entities_current` を作る
4. flow assigner を追加して `crawl_resource_flows_current` を作る
5. `security` / `legal` / `dataset` の flow から `resources` export を始める
6. `security` / `watch` flow を `intel_observations_current` に接続する
7. alert / fusion は observation 蓄積後に追加する

## 13. Decision

推奨 canonical path は次の通り。

`crawler.etzhayyim.com` の結果をまず `collector` に evidence として受け、`murakumo` で enrichment し、その結果を `entity` と `resourceflow` で正規化し、再利用可能なものだけ `resources` に昇格し、脅威・異常・監視価値のあるものを `intel` observation として保持する。

これにより、収集、資源化、主体同定、lineage、分析が 1 つの page ingestion から一貫して追跡できる。
