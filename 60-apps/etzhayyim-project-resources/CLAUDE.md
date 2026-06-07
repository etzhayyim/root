# etzhayyim-project-resources — Entity Graph Runbook

`60-apps/etzhayyim-project-resources` の権威ルール。
詳細設計は `90-docs/260313-entity-graph-arrow-jsonld-design.md` を正とする。

## CRITICAL: Entity Graph Standard — SQL WIT Only

→ `etzhayyim dodaf tv1 query --id etzhayyim-project-resources-entity-graph-standard-sql-wit-o` / MCP `etzhayyim.dodaf.tv1.query`

## Namespace 命名規則

各エンティティ種別は固定の CURIE prefix を使う。

| prefix | namespace IRI | 対象エンティティ |
|---|---|---|
| `party` | `https://etzhayyim.com/entities/party/` | 個人・法人 (Party, PartyPerson) |
| `org` | `https://etzhayyim.com/entities/org/` | 組織 (court, agency, company) |
| `ci` | `https://etzhayyim.com/entities/ci/` | Configuration Item |
| `case` | `https://courts.go.jp/cases/` | 判例 (case-intelligence) |
| `caseintel` | `https://etzhayyim.com/vocab/caseintel/` | caseintel 述語語彙 |
| `capital` | `https://etzhayyim.com/entities/capital/` | Capital エンティティ群 |
| `product` | `https://etzhayyim.com/entities/product/` | Product |
| `location` | `https://etzhayyim.com/entities/location/` | Location (address, building) |
| `ip` | `https://etzhayyim.com/entities/ip/` | IP アドレス |
| `webpage` | `https://etzhayyim.com/entities/webpage/` | Webpage (crawl entity) |
| `pachinko-store` | `https://etzhayyim.com/entities/pachinko-store/` | パチンコ店舗 |
| `pachinko-chain` | `https://etzhayyim.com/entities/pachinko-chain/` | パチンコチェーン |
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

このファイルは `etzhayyim-project-resources` 配下を変更するときのみ参照する。
設計詳細は `90-docs/260313-entity-graph-arrow-jsonld-design.md` に委譲。
