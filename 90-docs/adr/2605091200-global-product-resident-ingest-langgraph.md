---
id: adr-2605091200-global-product-resident-ingest-langgraph
title: "ADR-2605091200: Global Product Resident Ingest on LangGraph"
status: active
doc_type: adr
topic: global-product-resident-ingest-langgraph
authoritative: true
last_verified: 2026-05-09
priority: 8.6
axis: architecture
weight: 0.86
priority_note: "Defines Google-Shopping-like global product ingest as a resident LangGraph actor, with official-site evidence, webfetch, intel, and inference inside the graph."
authoritative_for:
  - global product ingest architecture
  - resident LangGraph placement for yoro/gtin/kakaku product intelligence
  - official company/product homepage acquisition policy
  - webfetch, intel, and inference node placement inside product ingest graphs
  - GTIN canonical product vs merchant offer responsibility split
related:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
  - adr-2605072000-langgraph-agent-loop-pattern
supersedes: []
superseded_by: []
---

# ADR-2605091200: Global Product Resident Ingest on LangGraph

**Status**: accepted
**Date**: 2026-05-09
**Deciders**: Jun Kawasaki

## Context

The current product ingest path has the right storage backbone for a
Google-Shopping-like product graph:

- `vertex_gtin_product` owns canonical global product identity.
- `vertex_kakaku_product`, `vertex_kakaku_merchant`,
  `vertex_kakaku_offer`, and `vertex_kakaku_price_history` own
  merchant-specific catalog, offer, and price observations.
- `yoro_product_ingest` already runs as a LangGraph graph and forwards offers
  to `com.etzhayyim.apps.kakaku.ingestOfferFromUrl`.

The gap is source quality and runtime shape. The current yoro path is mostly a
category/query trigger against retailer surfaces. Global product intelligence
needs a resident loop that continuously discovers product pages, fetches
official manufacturer evidence, resolves brand/owner identity, extracts
structured facts with inference, and only then writes canonical product and
offer rows.

The system must not depend on Google Shopping scraping. Google Shopping-like
means the internal data model and user experience: one canonical product,
many merchants, current offers, price history, official product facts, and
evidence lineage.

## Decision

### 1. Runtime shape

Global product ingest becomes a resident LangGraph actor, not a collection of
one-off scraper scripts.

The resident actor is a long-lived assistant thread hosted by
`mitama-langgraph-pool` in the non-default `mitama-udf` namespace. K8s CronJobs
are allowed only as small tickers that enqueue work or wake the resident
thread through `/runs`; they do not own product logic.

```
K8s ticker / UI / API
  -> LangGraph Server /runs or /threads/{product-ingest}/runs
    -> resident graph
      -> discovery
      -> webfetch official pages
      -> webfetch merchant pages
      -> extract structured facts
      -> intel entity resolution
      -> inference-based matching / confidence
      -> gtin canonical write
      -> kakaku offer / price-history write
      -> evidence and audit write
```

### 2. Graph decomposition

Use two assistants so scheduling and state are clear:

| Assistant | Responsibility | State scope |
|---|---|---|
| `global_product_ingest_resident` | Continuous backlog loop, frontier prioritization, retry, per-domain rate policy | actor thread |
| `global_product_enrich_one` | One product/URL enrichment transaction | product/job thread |

`global_product_ingest_resident` chooses the next work item and dispatches
`global_product_enrich_one`. It should checkpoint after every external IO
boundary so pod restart does not lose queue progress.

### 3. Per-product graph nodes

`global_product_enrich_one` is the authoritative graph shape:

| Node | Input | Output | Notes |
|---|---|---|---|
| `seed` | query, productUrl, merchantUrl, brand hint, GTIN hint | normalized job | validates scope and idempotency key |
| `discover_candidates` | query / seed URL | official URLs, merchant URLs | retailer APIs, sitemap, Common Crawl/CDX, existing `vertex_kakaku_*` |
| `fetch_official_pages` | brand/product official URLs | markdown/html/jsonld evidence | calls `site.etzhayyim.com` / webfetch, respects robots and rate limits |
| `fetch_merchant_pages` | offer/product URLs | price/stock evidence | calls `site.crawlPage`; direct fetch only as fallback |
| `extract_product_facts` | evidence bundle | name, brand, model, GTIN/JAN/UPC/EAN, MPN, specs, images | deterministic JSON-LD/meta first, LLM fallback second |
| `resolve_brand_owner` | brand/site/domain | legal entity / website / country candidates | uses intel entity resolution and graph lookup |
| `resolve_canonical_product` | identifiers + facts | canonical `gtin` product DID, confidence | GTIN wins; brand+model+pack only if no barcode |
| `match_offers` | canonical product + merchant evidence | offer upserts, match candidates | creates manual-review candidate on weak/conflicting match |
| `quality_gate` | full trace | accept/retry/review/drop | LLM judge plus deterministic confidence thresholds |
| `write_graph` | accepted trace | `vertex_gtin_product`, `vertex_kakaku_*`, evidence rows | idempotent write by DID/key |
| `emit_audit` | result | audit event | non-fatal but visible |

Webfetch, intel, and inference are not sidecars hidden outside the graph. They
are explicit graph nodes with checkpointed inputs/outputs.

### 4. Source policy

Source priority is:

1. Manufacturer / brand official product page.
2. Manufacturer / brand support/specification/download pages.
3. Official merchant/API feeds with product identifiers.
4. Retailer product pages.
5. Common Crawl or search-derived candidates.
6. LLM-only inference as fallback evidence, never as sole write authority for
   GTIN identity.

Official pages are used to enrich the global product node: product name,
brand, model, MPN, dimensions, pack size, official image, manuals, and
canonical product URL. Retailer pages are used to enrich merchant offer and
price history.

### 5. Storage ownership

Keep the existing actor split:

| Actor/table | Owns | Does not own |
|---|---|---|
| `gtin.etzhayyim.com` / `vertex_gtin_product` | canonical product identity and barcode-family identifiers | prices, merchant availability |
| `kakaku.etzhayyim.com` / `vertex_kakaku_*` | merchant product, merchant, offer, price history, match candidates | global identity truth |
| `yoro.etzhayyim.com` / `vertex_yoro_product_research` | research runs, summaries, operator-facing recommendations | canonical identity or price truth |

Add evidence tables in the implementation phase:

| Table | Purpose |
|---|---|
| `vertex_product_source_page` | normalized official/merchant page evidence with URL, domain, source kind, fetch time, content hash |
| `vertex_product_fact_evidence` | extracted product facts with field name, value, source page, method, confidence |
| `edge_product_official_source` | canonical product DID to official page / brand site |
| `edge_product_brand_owner` | product/brand to legal entity or website owner |

Until these tables exist, `global_product_enrich_one` may write the current
`vertex_yoro_product_research` summary, but that is not the durable evidence
model.

### 6. Matching policy

Identity resolution order:

1. Valid GTIN/JAN/UPC/EAN with check digit.
2. Existing `vertex_gtin_product` alias/canonical match.
3. Manufacturer official URL + brand + model + pack size.
4. Merchant SKU / MPN + brand + normalized title.
5. LLM similarity between official facts and merchant page facts.

Rules:

- Valid barcode conflict creates `vertex_kakaku_match_candidate` with
  `manual_review`; it must not silently merge products.
- Brand+model-only matching is never higher than medium confidence unless an
  official source and merchant source agree on MPN or specs.
- Pack-size differences split canonical product identity.
- Price observations always land in `kakaku`; they never mutate
  `vertex_gtin_product`.

### 7. Inference placement

Inference is used for:

- official page vs merchant page product matching,
- unstructured spec extraction where JSON-LD/meta is missing,
- brand owner disambiguation,
- quality-gate explanation,
- retry/review/drop routing.

Inference is not used for:

- barcode check digit validation,
- direct price arithmetic,
- idempotency key creation,
- source authority ranking when deterministic source kind is known.

Use Murakumo/OpenAI-compatible inference through the LangGraph node resolver or
MCP tool boundary. The graph state must store model id, prompt version,
citations/source URLs, and confidence.

### 8. Deployment policy

All Kubernetes resources for this ingest must declare a non-default namespace.
The default placement is `mitama-udf` for LangGraph Server hosted jobs.
If yoro-specific worker pods are added later, they live in `yoro-actors`.
No product ingest resource may be created in `default`.

### 9. Implementation phases

Phase 1:

- Keep existing `yoro_product_ingest`.
- Add `global_product_enrich_one` as a py_factory graph using current XRPC
  surfaces: `site.crawlPage`, `gtin.lookupProduct/registerProduct`,
  `kakaku.ingestOfferFromUrl`, and intel resolution where available.
- Add the evidence tables.

Phase 2:

- Add `global_product_ingest_resident` as the resident backlog loop.
- Move category CronJobs to small tickers that wake the resident assistant.
- Add product frontier rows and retry state.

Phase 3:

- Convert both graphs from `py_factory` to data-driven `topology` rows per
  ADR-2605082000.
- Express webfetch, intel, inference, and writes as `mcp_tool` / `llm` /
  `sql_udf` nodes.

Phase 4:

- Expand sources beyond JP retailers: official manufacturer sites, open feeds,
  regulatory/product registries, marketplace APIs, Common Crawl, and
  country-specific retailer adapters.

## Consequences

- Product identity quality improves because official pages become first-class
  evidence, not optional decoration.
- The ingest plane becomes restartable and observable through LangGraph run,
  checkpoint, and audit rows.
- Existing `kakaku` price comparison remains useful and does not need to own
  global identity.
- Initial implementation adds schema and graph complexity, but it avoids
  coupling product truth to retailer scraping.

## Alternatives Considered

### Scrape Google Shopping directly

Rejected. It is not a stable or clean source boundary. The internal product
graph should be Google-Shopping-like, not Google-Shopping-dependent.

### Put everything in `kakaku`

Rejected. `kakaku` owns merchant offers and price history. Global product
identity belongs in `gtin`; research summaries belong in `yoro`.

### Keep CronJob-only ingest

Rejected. CronJobs are good tickers, but they do not provide resident memory,
checkpointed reasoning, retry policy, or backlog prioritization.

## References

- `20-actors/gtin/CLAUDE.md`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/yoro_product_ingest.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/yoro_product.py`
- `30-graph/graph-schema/migrations/0001_initial_schema.ts`
- `50-infra/vultr/mitama-langgraph-pool/values.yaml`
