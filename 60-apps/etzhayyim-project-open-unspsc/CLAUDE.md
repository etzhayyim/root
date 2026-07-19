# etzhayyim-project-open-unispsc — UNSPSC Product & Service Classification Platform

Contract-Bounded Component Architecture (DM2 Agreement + WIT Component Model) で UNSPSC (United Nations Standard Products and Services Code) 製品・サービス調達分類をモデル化。

## UNSPSC Hierarchy → Entity Model

```
Segment  (2桁)  ~55 segments    → APP boundary (1 APP per segment)
  Family   (4桁)  ~400 families   → SQL node (:UNSPSCFamily)
    Class    (6桁)  ~900 classes    → SQL node (:UNSPSCClass)
      Commodity (8桁)  ~70,000 items → Entity (SQL node :UNSPSCCommodity + Lexicon records)
```

## Lexicon Namespace: `com.etzhayyim.apps.unispsc.*`

全 record に `commodity_code` (8桁) フィールドを持ち、commodity entity を特定。
canonical DID は alpha-start ルール準拠:

- App DID: `did:web:unispsc.etzhayyim.com`
- Segment DID: `did:web:unispsc.etzhayyim.com:seg{2-digit}` (例: `seg43`)
- Commodity DID: `did:web:unispsc.etzhayyim.com:seg{2-digit}:commodity:c{8-digit-code}`
  - 例: `did:web:unispsc.etzhayyim.com:seg43:commodity:c43211501`
  - `c` prefix で数字始まりを回避

| Lexicon NSID | WRecord kind | Rkey | Entity ID | 用途 |
|---|---|---|---|---|
| `com.etzhayyim.apps.unispsc.commodity` | `unispsc.commodity` | UNSPSC 8桁 | commodity_code | commodity entity 登録 (master) |
| `com.etzhayyim.apps.unispsc.spec` | `unispsc.spec` | nanoid | commodity_code | 製品仕様テンプレート |
| `com.etzhayyim.apps.unispsc.procurement` | `unispsc.procurement` | nanoid | commodity_code | 調達イベント記録 |
| `com.etzhayyim.apps.unispsc.supplier` | `unispsc.supplier` | nanoid | commodity_code | サプライヤー評価 |
| `com.etzhayyim.apps.unispsc.standard` | `unispsc.standard` | standard_id | commodity_codes[] | 品質規格バインド |
| `com.etzhayyim.apps.unispsc.risk` | `unispsc.risk` | nanoid | commodity_code | リスク評価 |
| `com.etzhayyim.apps.unispsc.rfp` | `unispsc.rfp` | nanoid | commodity_code | RFP/RFQ テンプレート |
| `com.etzhayyim.apps.unispsc.concordance` | `unispsc.concordance` | unispsc_code | unispsc_code | CPC concordance |
| `com.etzhayyim.apps.unispsc.hsConcordance` | `unispsc.hsConcordance` | unispsc_code | unispsc_code | HS concordance |

## UNSPSC-CPC Concordance

UNSPSC commodity は CPC subclass の下位粒度。`etzhayyim:unispsc-product-classification/concordance` で N:M mapping。

| UNSPSC Segment | CPC Section (primary) | 関係 |
|---|---|---|
| 10-15 (Raw materials) | 0-1 (Agriculture, Ores) | 原材料 |
| 20-27 (Industrial) | 3-4 (Transportable goods, Machinery) | 工業製品 |
| 30-31 (Construction) | 5 (Construction) | 建設 |
| 39-48 (Components, Equipment) | 3-4 (Goods, Machinery) | 部品・機器 |
| 50-53 (Food, Apparel) | 2 (Food, Textiles) | 消費財 |
| 55-60 (Media, IT, Telecom) | 8 (Business services) | 情報・通信 |
| 70-86 (Services) | 6-9 (Services) | サービス |
| 90-95 (Travel, Public) | 9 (Community services) | 公共・旅行 |

## Segment APP Commands

各 Segment APP は以下の command set を持つ。全 commodity operations は `commodity_code` パラメータで entity を特定。

## LangGraph / Pregel MCP Business Logic

UNSPSC hierarchy は単一の `commodity_code` lookup ではなく、4 つの business boundary として MCP tool 化する。

| Grain | MCP tool | Code | Business logic |
|---|---|---|---|
| Segment | `com.etzhayyim.apps.openUnispsc.segment` | 2桁 | portfolio/domain ownership, regulated segment detection, default approval policy |
| Family | `com.etzhayyim.apps.openUnispsc.family` | 4桁 | category-management strategy under segment |
| Class | `com.etzhayyim.apps.openUnispsc.class` | 6桁 | compliance/control policy under family |
| Commodity | `com.etzhayyim.apps.openUnispsc.commodity` | 8桁 | executable procurement policy: parent hierarchy, approval tier, risk tags, optional spend calculation |

Implementation:

- Primitive handlers: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/open_unispsc.py`
- Pregel graph: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/open_unispsc_pregel.py`
- Item-specific LangGraph + LangChain design graph: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/open_unispsc_item.py`
- MCP dispatch registration: `kotodama.mcp_dispatch` actor `openUnispsc`
- MCP registry seed: `30-graph/graph-schema/sql_migrations/20260514010000_seed_open_unispsc_hierarchy_mcp.up.sql`
- Lexicons: `00-contracts/lexicons/com/etzhayyim/apps/openUnispsc/{segment,family,class,commodity,designItem,itemGetSpec,itemScreenSupplier,itemPlanProcurement,itemFlagCompliance,syncCatalogItem,planCatalogPurchase,syncAllCommodityDids,importSegmentCatalog,supplier,procurement,flagArmsCommodity,flagDualUseCommodity,applyGraphWritePlan,runItemWorkflow,coverageSnapshot}.json`

Pregel execution walks ancestors before the requested grain:

```text
segment -> family -> class -> commodity
```

For example, `openUnispsc.commodity(code=43211501)` returns segment 43,
family 4321, class 432115, and commodity 43211501 records, each with its own
MCP tool name and businessLogic payload.

Actual UNSPSC item design uses `com.etzhayyim.apps.openUnispsc.designItem`.
It accepts an 8-digit commodity item (for example `25172504 Vehicle Batteries`)
and produces:

- item-specific LangGraph nodes and edges
- item-specific LangChain `ChatPromptTemplate` contract
- MCP tool names scoped to the commodity item
- BPMN references selected from `00-contracts/bpmn/com/etzhayyim/open-unispsc/`

Executable item-level MCP tools:

| MCP tool | Implements | BPMN reference |
|---|---|---|
| `com.etzhayyim.apps.openUnispsc.itemGetSpec` | item-specific spec/evidence contract + LangGraph/LangChain references | procurement/supplier process context |
| `com.etzhayyim.apps.openUnispsc.itemScreenSupplier` | supplier KYC + quality routing: blocked/manual-review/approved | `supplier.bpmn` |
| `com.etzhayyim.apps.openUnispsc.itemPlanProcurement` | totalAmount, approvalTier, requireCab, commodityDst | `procurement.bpmn` |
| `com.etzhayyim.apps.openUnispsc.itemFlagCompliance` | arms / dual-use compliance flags and process refs | `flagArmsCommodity.bpmn`, `flagDualUseCommodity.bpmn` |
| `com.etzhayyim.apps.openUnispsc.syncCatalogItem` | UNSPSC commodity item → `okaimono` catalog upsert contract | `260326-unispsc-okaimono-integration-design.md` Phase 2 |
| `com.etzhayyim.apps.openUnispsc.planCatalogPurchase` | `okaimono` product/order line → checkout SAGA + segment item-spec invocation + fulfillment handoff | `260326-unispsc-okaimono-integration-design.md` Phase 3, `procurement.bpmn` |
| `com.etzhayyim.apps.openUnispsc.syncAllCommodityDids` | cross-segment fanout plan for `register-commodities-bulk` + `register-commodity-profiles` + social registration post | `260326-unispsc-okaimono-integration-design.md` UNSPSC-side requirement |
| `com.etzhayyim.apps.openUnispsc.importSegmentCatalog` | `okaimono` bulk import plan: query `unispsc_commodities` by segment and apply `syncCatalogItem` | `260326-unispsc-okaimono-integration-design.md` okaimono-side import command |
| `com.etzhayyim.apps.openUnispsc.supplier` | supplier registration vertex + BPMN instance contract | `supplier.bpmn` |
| `com.etzhayyim.apps.openUnispsc.procurement` | procurement request vertex + BPMN instance contract | `procurement.bpmn` |
| `com.etzhayyim.apps.openUnispsc.flagArmsCommodity` | direct arms commodity BPMN flag | `flagArmsCommodity.bpmn` |
| `com.etzhayyim.apps.openUnispsc.flagDualUseCommodity` | direct dual-use commodity BPMN flag | `flagDualUseCommodity.bpmn` |
| `com.etzhayyim.apps.openUnispsc.runItemWorkflow` | spec + supplier + procurement + compliance + merged graphWritePlan | all selected open-unispsc BPMN refs |
| `com.etzhayyim.apps.openUnispsc.coverageSnapshot` | dispatcher + lexicon + seed/down SQL + Alembic wrapper + BPMN + graph-target coverage report | all expected open-unispsc MCP refs |

The direct `supplier`, `procurement`, and compliance flag tools also return a deterministic
`graphWritePlan` that targets the existing graph tables:

| Tool | Graph target |
|---|---|
| `com.etzhayyim.apps.openUnispsc.supplier` | `vertex_open_unispsc_supplier` |
| `com.etzhayyim.apps.openUnispsc.procurement` | `vertex_open_unispsc_procurement` + `edge_open_unispsc_procurement_commodity` |
| `com.etzhayyim.apps.openUnispsc.flagArmsCommodity` | `vertex_open_defence_event` |
| `com.etzhayyim.apps.openUnispsc.flagDualUseCommodity` | `vertex_open_defence_event` |

`com.etzhayyim.apps.openUnispsc.applyGraphWritePlan` validates those plans against
an open-unispsc table/column allowlist and returns parameterized upsert SQL in
`dryRun=true`; with `dryRun=false` it applies the same validated statements via
the existing DB sync helper.

`com.etzhayyim.apps.openUnispsc.runItemWorkflow` composes the item spec, supplier
screening, procurement approval plan, and compliance flag tools into one
workflow response. It returns `workflowStatus` (`ready`, `manual-review`, or
`blocked`) plus one merged `graphWritePlan` for downstream validation or apply.

Verification gate:

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py
uv run python scripts/verify_open_unispsc_mcp.py --pretty --report-path artifacts/open-unispsc-mcp-verifier.json
```

The verifier calls `coverageSnapshot`, runs `runItemWorkflow` scenarios for
`ready`, `manual-review`, and `blocked`, checks the UNSPSC segment fanout,
UNSPSC → okaimono catalog import/sync, and purchase-flow contracts, and
dry-runs `applyGraphWritePlan` against the regulated sample; it exits non-zero
if any step fails or coverage reports missing artifacts. The CI workflow
uploads the same JSON report as
`open-unispsc-mcp-verifier`.

Existing BPMN reference set:

| BPMN | Use in item design |
|---|---|
| `procurement.bpmn` | procurement amount, approval tier, CAB routing, procurement→commodity edge |
| `supplier.bpmn` | supplier KYC, quality score, blocked/manual-review/approved routing |
| `flagArmsCommodity.bpmn` | segment 46 / arms-security commodities |
| `flagDualUseCommodity.bpmn` | dual-use / regulated goods segments such as chemicals, electronics, labs, defense, pharma |

### Entity Management (ISCO pattern)

| Command | 用途 | WRecord kind |
|---|---|---|
| `register-commodity` | commodity entity 登録 | `unispsc.commodity` |
| `register-commodities-bulk` | 一括登録 (UNSPSC master) | `unispsc.commodity` |
| `list-commodities` | 一覧 (family/class/search filter) | — (read) |
| `get-commodity` | 詳細取得 | — (read) |

### Commodity Operations (parameterized by commodity_code)

| Command | 用途 | WRecord kind |
|---|---|---|
| `get-spec` | 製品仕様取得 | — (read) |
| `search-variants` | SKU/variant 検索 | — (read) |
| `evaluate-supplier` | サプライヤー評価 | `unispsc.supplier` |
| `generate-rfp` | RFP/RFQ 生成 | `unispsc.rfp` |
| `record-procurement` | 調達イベント記録 | `unispsc.procurement` |
| `get-standards` | 適用品質規格 | — (read) |
| `assess-risk` | リスク評価 | `unispsc.risk` |
| `get-concordance` | CPC/HS/ISIC mapping | — (read) |
| `get-contract-info` | 規制・契約情報 | — (read) |

## WIT Architecture

### WIT 階層

| 層 | WIT namespace | 数 | 例 |
|---|---|---|---|
| **Shared core** | `etzhayyim:unispsc-product-classification@1.0.0` | 1 | types, classification, concordance, procurement, quality-standards, entity-management |
| **Segment APP** | `etzhayyim:unispsc-seg-{NN}@1.0.0` | ~55 | `etzhayyim:unispsc-seg-43/it-telecom@1.0.0` |

### world.wit 必須構造

```wit
package etzhayyim:unispsc-seg-{NN};

world component {
    include kotodama:runtime/kotodama-component@1.0.0;
    import kotodama:contract/agreement@1.0.0;
    import kotodama:div/information@1.0.0;
    import kotodama:div/documents@1.0.0;
    import kotodama:div/materiel@1.0.0;
    import etzhayyim:isic-resource-flow/labor@1.0.0;
    import etzhayyim:isic-resource-flow/materials@1.0.0;
    import etzhayyim:isic-resource-flow/capital@1.0.0;
    import etzhayyim:isic-resource-flow/products@1.0.0;
    import etzhayyim:cpc-product-classification/classification@1.0.0;
    export etzhayyim:unispsc-seg-{NN}/{segment-slug}@1.0.0;
}
```

## WIT Packages

| Package | Path | 内容 |
|---|---|---|
| `etzhayyim:unispsc-product-classification@1.0.0` | `wit/unispsc-product-classification/` | Shared core: types, classification, concordance, procurement, quality-standards, entity-management |
| `etzhayyim:unispsc-seg-{NN}@1.0.0` | `wasm/etzhayyim-wasm-unispsc-seg-{NN}-*/wit/` | Per-segment capability (~55) |

## SQL Graph Schema

### Nodes

| Node | Properties | 用途 |
|---|---|---|
| `:UNSPSCSegment` | code, name, app_nanoid, commodity_count | Segment (APP 対応) |
| `:UNSPSCFamily` | code, name, segment | Family 階層 |
| `:UNSPSCClass` | code, name, segment, family | Class 階層 |
| `:UNSPSCCommodity` | code, name, name_en, segment, family, class_, description, spec_template, standards, risk_profile, app_nanoid | Commodity entity (~70,000) |
| `:UNSPSCProcurement` | id, commodity_code, buyer, supplier, value, status | 調達レコード |
| `:UNSPSCStandard` | id, name, body, commodity_codes, status | 品質規格マッピング |

### Edges

| Edge | From → To | 用途 |
|---|---|---|
| `:BELONGS_TO` | `:UNSPSCCommodity` → `:UNSPSCClass` | 階層 |
| `:BELONGS_TO` | `:UNSPSCClass` → `:UNSPSCFamily` | 階層 |
| `:BELONGS_TO` | `:UNSPSCFamily` → `:UNSPSCSegment` | 階層 |
| `:PROCURES` | `:Organization` → `:UNSPSCCommodity` | 組織 → 製品調達 |
| `:SUPPLIES` | `:Organization` → `:UNSPSCCommodity` | 組織 → 製品供給 |
| `:CONFORMS_TO` | `:UNSPSCCommodity` → `:UNSPSCStandard` | 品質規格準拠 |
| `:UNSPSC_CPC_MAP` | `:UNSPSCCommodity` → `:CPCProduct` | UNSPSC-CPC concordance |

## cross-actor Discovery

Segment APP の capability tags で commodity を discoverable にする:

```go
// 外部 APP が commodity を検索
kotodama.Invoke("", "get-spec", `{"commodity_code":"43211501"}`)
// → segment 43 APP に routing → commodity entity lookup → spec 返却
```

## Coverage Target

| Level | Count | Entity Type |
|---|---|---|
| Segment | ~55 | APP (App) |
| Family | ~400 | SQL node |
| Class | ~900 | SQL node |
| Commodity | ~70,000 | SQL node + Lexicon record (entity) |

## Chotatsu Integration

`90-docs/adr/2607193200-remaining-doc-only-apps-retire.edn` の canonical chotatsu spec (公共調達) が UNSPSC commodity code で品目分類する。`Invoke("", "get-spec", ...)` で commodity entity の調達仕様を取得。

## okaimono.etzhayyim.com Integration (EC Marketplace)

okaimono (ok4imn1o) が全 51 UNSPSC segment を Follow → commodity 登録 commit を reactive に受信 → `okaimono_catalog_item` として自動カタログ登録。

**フロー**: UNSPSC `register-commodities-bulk` → `com.etzhayyim.apps.unispsc.commodity` commit → okaimono `handleUpstreamUnispscCommodity()` → catalog item 作成 → 購入可能

**okaimono 側 command**: `import-unispsc-segment`, `import-unispsc-all`, `catalog-search-unispsc`

**SQL edge**: `(:OkaimonoCatalogItem)-[:CLASSIFIED_BY]->(:UNSPSCCommodity)`

設計: `260326-unispsc-okaimono-integration-design.md`

## Governance Integration

| Governance WIT | UNSPSC 適用 |
|---|---|
| `kotodama:governance/raci` | 調達承認の RACI 宣言 |
| `kotodama:governance/rbac` | 調達データアクセス制御 |
| `governance.data-classification` | 調達データの sensitivity |
| `governance.standards-profile` | 製品品質規格 (ISO, IEC, JIS) の採用状況 |
| `governance.supply-chain` | サプライヤーリスク評価 |
