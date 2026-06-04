# ai-gftd-project-resources — Entity Graph Runbook

`60-apps/ai-gftd-project-resources` の権威ルール。
詳細設計は `90-docs/260313-entity-graph-arrow-jsonld-design.md` を正とする。

## CRITICAL: Entity Graph Standard — SQL WIT Only

→ `gftd dodaf tv1 query --id ai-gftd-project-resources-entity-graph-standard-sql-wit-o` / MCP `gftd.dodaf.tv1.query`

## Namespace 命名規則

各エンティティ種別は固定の CURIE prefix を使う。

| prefix | namespace IRI | 対象エンティティ |
|---|---|---|
| `party` | `https://gftd.ai/entities/party/` | 個人・法人 (Party, PartyPerson) |
| `org` | `https://gftd.ai/entities/org/` | 組織 (court, agency, company) |
| `ci` | `https://gftd.ai/entities/ci/` | Configuration Item |
| `case` | `https://courts.go.jp/cases/` | 判例 (case-intelligence) |
| `caseintel` | `https://gftd.ai/vocab/caseintel/` | caseintel 述語語彙 |
| `capital` | `https://gftd.ai/entities/capital/` | Capital エンティティ群 |
| `product` | `https://gftd.ai/entities/product/` | Product |
| `location` | `https://gftd.ai/entities/location/` | Location (address, building) |
| `ip` | `https://gftd.ai/entities/ip/` | IP アドレス |
| `webpage` | `https://gftd.ai/entities/webpage/` | Webpage (crawl entity) |
| `pachinko-store` | `https://gftd.ai/entities/pachinko-store/` | パチンコ店舗 |
| `pachinko-chain` | `https://gftd.ai/entities/pachinko-chain/` | パチンコチェーン |
| `schema` | `https://schema.org/` | Schema.org 標準語彙 |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | XSD リテラルデータ型 |

## Relation 述語規則

| 述語 CURIE | SQL rel type | 意味 |
|---|---|---|
| `schema:knows` | `KNOWS` | 人同士の関係 |
| `org:memberOf` | `MEMBER_OF` | 組織メンバー |
| `org:subOrganizationOf` | `SUB_ORG_OF` | 組織の上位組織 |
| `ci:relatedTo` | `RELATED_TO` | CI 間の汎用関係 |
| `ci:dependsOn` | `DEPENDS_ON` | CI 依存関係 |
| `caseintel:involves` | `INVOLVES` | 事件と当事者 |
| `caseintel:decidedBy` | `DECIDED_BY` | 事件と裁判所 |
| `caseintel:citesPrecedent` | `CITES_PRECEDENT` | 事件と先例 |

## GraphQueryService (XRPC)

グラフトラバーサル API は `GraphQueryService` proto を通じて公開する。
内部実装は `G()` builder の `Traverse()` で variable-length path を使う。

```proto
service GraphQueryService {
  rpc GetNeighbors(GetNeighborsRequest) returns (GetNeighborsResponse);
  rpc GetSubgraph(GetSubgraphRequest) returns (GetSubgraphResponse);
  rpc GetShortestPath(GetShortestPathRequest) returns (GetShortestPathResponse);
}
```

## Use-When-Needed Policy

このファイルは `ai-gftd-project-resources` 配下を変更するときのみ参照する。
設計詳細は `90-docs/260313-entity-graph-arrow-jsonld-design.md` に委譲。
