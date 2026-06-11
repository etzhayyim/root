---
id: 260415-hs-code-domain-coverage
title: "HS Code Domain Coverage Design"
status: active
doc_type: explanation
topic: hs-code-domain-coverage
authoritative: true
authoritative_for:
  - etzhayyim-project-code-hs
  - hs-actor-path-did-model
last_verified: 2026-04-15
related:
  - 260324-isin-coverage-social-evolution
  - f-plan-lexicon-as-contract
  - doc-260414-kotoba-premium-32gb-scale-up
---

# HS Code Domain Coverage Design

## Goal

`etzhayyim-project-code-hs` を、Harmonized System (HS) code に基づく **国際貿易品目分類の基盤 project** として定義する。
この project は単なるコード辞書ではなく、以下 3 層を一体で扱う。

1. **actor coverage**
   HS を使って何を判断・記録する actor が必要か
2. **path DID coverage**
   どの分類階層を DID 化して social / write / lineage の境界にするか
3. **domain coverage**
   GTIN, CPC, ISIC, legal-entity, states, trade-flow をどう接続するか

## Positioning

HS はこの repo において次の位置に置く。

- `gtin` の downstream ではなく、**GTIN と trade/compliance を橋渡しする分類基盤**
- `isic` が「経済活動分類」、`isco` が「職務分類」であるのに対し、HS は **国境を越える物品分類**
- `states` / customs / tariff / sanctions / export-control の entrypoint
- `cpc` や `gtin.classification` の主要な concordance 先

要するに、`hs.etzhayyim.com` は「何のモノが国境を越えるか」を表す SSoT とする。

## Architecture

### 1 app x multi-DID

`etzhayyim-project-code-hs` は **1 app × multi-DID** を基本とする。

- primary DID: `did:web:hs.etzhayyim.com`
- NSID prefix: `com.etzhayyim.apps.hs.*`
- performerType: `service`
- execution tier: `T1`

理由:

- HS は階層 taxonomy が強く、path DID との相性が良い
- revision 差分や concordance を 1 coordinator で吸収しやすい
- `isin` / `isco` と同じ coverage-heartbeat 運用に乗せられる

## Path DID Model

### Canonical DID convention

```text
did:web:hs.etzhayyim.com
did:web:hs.etzhayyim.com:section:{section_slug}
did:web:hs.etzhayyim.com:chapter:{chapter2}
did:web:hs.etzhayyim.com:heading:{heading4}
did:web:hs.etzhayyim.com:subheading:{subheading6}
did:web:hs.etzhayyim.com:revision:{edition}
did:web:hs.etzhayyim.com:country:{iso3}
```

### Why this split

- `section` は人間可読な browse / explanation 単位
- `chapter` は regulation / tariff / customs の実務単位
- `heading` は product family の主要一致点
- `subheading` は trade record / customs declaration の基本一致点
- `revision` は HS 改訂差分を path で分離するために必要
- `country` は national tariff schedule との接続点

### Control boundary

write の主境界は以下とする。

- taxonomy write: primary DID
- coverage / report write: level DID (`chapter`, `heading`, `subheading`)
- jurisdiction overlay: `country:{iso3}` DID

これにより、分類そのものと、国別制度・coverage report を分離できる。

## Actor Coverage

`20-actors/hs/actor-manifest.jsonld` では 4 actor に分ける。

| Actor Path | Role | Primary concern |
|---|---|---|
| `taxonomy:canonical` | HS hierarchy registry | section/chapter/heading/subheading SSoT |
| `concordance:trade-item` | Crosswalk resolver | GTIN/CPC/ISIC/internal catalog linkage |
| `analytics:trade-flow` | Trade evidence coverage | import/export/value/route aggregation |
| `compliance:border-controls` | Customs policy overlay | tariff, restriction, sanction, license hints |

### Ownership rule

- taxonomy actor は **コード体系そのもの**
- concordance actor は **他 taxonomy との接続**
- analytics actor は **実データ coverage**
- compliance actor は **国別規制差分**

これで「分類」「接続」「観測」「規制」が責務分離される。

## Domain Coverage

### Core entities

| Entity | Description | Canonical join key |
|---|---|---|
| HS Section | broad domain bucket | `section_slug` |
| HS Chapter | customs/legal browse unit | `chapter2` |
| HS Heading | product family | `heading4` |
| HS Subheading | declaration-grade classification | `subheading6` |
| HS Revision | edition boundary | `edition` |
| Jurisdiction Overlay | country-specific mapping | `iso3 + local_code` |
| Trade Item Link | GTIN/catalog concordance | `product_did + hs_code` |
| Legal Entity Link | trader/manufacturer/exporter/importer | `entity_did + hs_code` |

### Cross-project links

| Project | Link shape | Purpose |
|---|---|---|
| `gtin` | GTIN product → HS subheading | barcode item to customs class |
| `open-isic` / `isic` | entity / plant / activity → common HS baskets | production to traded goods |
| `states` | country DID → tariff / customs authority / ministry | border-control context |
| `legal-entity` | importer/exporter/manufacturer → traded code mix | trade profile |
| `contracts` | procurement item / line item → HS code | public procurement comparability |

### Out of scope for v1

- national 8/10/12 digit tariff schedules as canonical global IDs
- free-text customs ruling ingestion at scale
- invoice / shipment document OCR
- rules-of-origin reasoning engine

これらは overlay project で扱い、`hs` 本体は 6-digit までの global core を優先する。

## Coverage Model

### Coverage dimensions

`etzhayyim-project-code-hs` の coverage は単一メトリクスではなく、最低でも以下の 4 軸で持つ。

| Dimension | Meaning |
|---|---|
| `taxonomyCoverage` | taxonomy node が登録済みか |
| `concordanceCoverage` | GTIN/CPC/ISIC 等との crosswalk があるか |
| `tradeEvidenceCoverage` | trade-flow / customs / market evidence があるか |
| `policyCoverage` | tariff / ban / licensing / sanctions overlay があるか |

### Coverage heartbeat

`isin` の pattern を横展開し、heartbeat は weakest domain を選んで coverage report を出す。

例:

1. chapter ごとに taxonomy / concordance / evidence / policy を集計
2. 最も弱い chapter or heading を選ぶ
3. 対応 DID に `coverage_report` を write
4. social post を派生
5. primary DID が全体サマリを投稿

## Collection Design

推奨 collection:

| Collection | NSID | Writer DID |
|---|---|---|
| taxonomy node | `com.etzhayyim.apps.hs.node` | primary DID |
| concordance | `com.etzhayyim.apps.hs.concordance` | primary DID |
| trade evidence | `com.etzhayyim.apps.hs.tradeEvidence` | heading/subheading DID |
| policy overlay | `com.etzhayyim.apps.hs.policyOverlay` | country DID |
| coverage report | `com.etzhayyim.apps.hs.coverageReport` | chapter/heading/subheading DID |
| revision delta | `com.etzhayyim.apps.hs.revisionDelta` | revision DID |

## Query Surface

最低限の xrpc contract:

| NSID | Purpose |
|---|---|
| `com.etzhayyim.apps.hs.getNode` | code から taxonomy node 取得 |
| `com.etzhayyim.apps.hs.getChildren` | 子ノード一覧 |
| `com.etzhayyim.apps.hs.resolveConcordance` | GTIN/CPC/ISIC から HS 推定 |
| `com.etzhayyim.apps.hs.getCoverage` | coverage snapshot |
| `com.etzhayyim.apps.hs.getPolicyOverlay` | 国別 tariff / restriction 概要 |
| `com.etzhayyim.apps.hs.health` | actor health |

## Revision Strategy

HS は改訂があるため、global core と edition overlay を分離する。

- global stable key: `subheading6`
- revision-sensitive records: `revision:{edition}`
- revision delta record で split / merge / rename を保持

この方式により:

- 既存 link を壊さずに改訂差分を追える
- `gtin` や `contracts` からの参照先を安定化できる
- 国別 overlay が edition ごとに揺れても吸収しやすい

## Recommended Build Order

1. `etzhayyim-project-code-hs` scaffold
2. `20-actors/hs/actor-manifest.jsonld`
3. taxonomy-only static dataset for section/chapter/heading/subheading
4. `getNode` / `getChildren` / `health`
5. coverage heartbeat
6. `gtin.classification` との concordance
7. `states` 経由の country overlay

## Design Decision

### Chosen

- domain: `hs.etzhayyim.com`
- primary DID: `did:web:hs.etzhayyim.com`
- architecture: 1 coordinator app × multi-DID
- canonical depth: section / chapter / heading / subheading
- country and revision are overlays, not replacements

### Rejected

- chapter-per-app
  理由: chapter 数が多く、revision/country overlay と組み合わせると app explosion になる
- subheading-per-app
  理由: coverage/social/write は必要でも app 境界にするほどではない
- GTIN 内包
  理由: GTIN は product identity、HS は trade classification で責務が異なる

## Outcome

`etzhayyim-project-code-hs` は以下を担う。

- 世界共通の物品貿易 taxonomy
- product / industry / legal-entity / state をつなぐ classification hub
- actor/path DID ベースで coverage を自律成長させる T1 service

これにより、repo 全体で「誰が」「何を」「どの制度で」「どの品目として」扱うかを、HS を軸に統合できる。
