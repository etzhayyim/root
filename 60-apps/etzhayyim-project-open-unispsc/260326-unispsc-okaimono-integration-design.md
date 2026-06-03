# UNSPSC 70K DID Registration + okaimono EC Integration Design

## Overview

UNSPSC ~70,000 commodity を path-based DID として登録し、okaimono.etzhayyim.com で Amazon ライクに購入可能にする。

## Architecture

```
UNSPSC (51 segment APPs)
  ├── register-commodities-bulk → ~70,000 unispsc_commodity records
  ├── register-commodity-profiles → ~70,000 path-based DIDs
  │     did:web:unispsc.etzhayyim.com:seg{NN}:commodity:c{8-digit}
  └── Social post per commodity DID

        ↓ Follow (ComAtprotoSyncSubscribeRepos)

okaimono (ok4imn1o)
  ├── handleUpstreamUnispscCommodity()
  │     → auto-create catalog_item per commodity
  │     → unispsc_code, segment, family, class_ fields
  ├── import-unispsc-segment command
  │     → bulk query G("unispsc_commodities") → catalog upsert
  └── catalog-search + catalog-get
        → unispsc_code filter
        → UNSPSC hierarchy navigation
```

## DID Schema (canonical, from 260326-unispsc-did-design.md)

- App: `did:web:unispsc.etzhayyim.com`
- Segment: `did:web:unispsc.etzhayyim.com:seg{NN}`
- Commodity: `did:web:unispsc.etzhayyim.com:seg{NN}:commodity:c{8-digit}`

## Data Flow

### Phase 1: UNSPSC DID Registration (per segment)

```
invoke seg-43 register-commodities-bulk {commodities: [...]}
  → ComAtprotoRepoCreateRecord("unispsc_commodity", {code, name, ...})
  → DIDCreate("commodity:{code}", {displayName, description})
  → AppBskyFeedPostAs(commodityDID, "Commodity registered")
```

### Phase 2: okaimono Ingest (reactive)

```
ComAtprotoSyncSubscribeRepos
  → collection == "com.etzhayyim.apps.unispsc.commodity"
  → handleUpstreamUnispscCommodity(commit)
    → G("unispsc_commodities").Where(Eq{"rkey": rkey}).Query()
    → ComAtprotoRepoCreateRecord("okaimono_catalog_item", {
        product_id: "unispsc-{code}",
        sku: "UNSPSC-{code}",
        title: name,
        category: "unispsc:{segment}:{family}:{class}",
        unispsc_code: code,
        unispsc_segment: segment,
        unispsc_family: family,
        unispsc_class: class_,
        commodity_did: "did:web:unispsc.etzhayyim.com:seg{NN}:commodity:c{code}",
        active: true,
      })
```

### Phase 3: Purchase Flow

```
Customer → okaimono catalog-search {keyword: "laptop"}
  → G("catalog_items").Where(Contains{"title": "laptop"}).Query()
  → returns items with unispsc_code

Customer → order-create {items: [{product_id: "unispsc-43211501", qty: 1}]}
  → Checkout SAGA (chk8uty2)
  → procurement-find-offers → Invoke(unispsc-seg43, "get-spec", {commodity_code})
  → fulfillment-create-shipment
```

## Cypher Graph Integration

```cypher
// UNSPSC → okaimono catalog mapping
(:OkaimonoCatalogItem {product_id: "unispsc-43211501"})
  -[:CLASSIFIED_BY]->(:UNSPSCCommodity {code: "43211501"})

// Procurement path
(:OkaimonoCatalogItem)-[:CLASSIFIED_BY]->(:UNSPSCCommodity)
  -[:BELONGS_TO]->(:UNSPSCClass)-[:BELONGS_TO]->(:UNSPSCFamily)
  -[:BELONGS_TO]->(:UNSPSCSegment {app_nanoid: "s43t7k2m"})
```

## Changes Required

### UNSPSC side
- Add `sync-all-commodity-dids` orchestration command (calls register-commodities-bulk + register-commodity-profiles per segment via cross-actor invoke)

### okaimono side
1. Follow all 51 UNSPSC segment nanoids
2. Subscribe to `com.etzhayyim.apps.unispsc.commodity` collection
3. Add `handleUpstreamUnispscCommodity()` reactive handler
4. Add `import-unispsc-segment` command (bulk import)
5. Add `unispsc_code` field to catalog_item schema
6. Add WIT import for UNSPSC classification
