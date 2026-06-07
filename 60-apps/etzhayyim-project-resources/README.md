# etzhayyim-project-resources

Public resource repository for ETZHAYYIM. Content under `content/` is stored as JSON-LD entity files and published to `https://resources.etzhayyim.com/`.

## Public namespace

The `resources.etzhayyim.com` CDN app now serves:

- `https://resources.etzhayyim.com/etzhayyim-project-resources/`
- All JSON-LD documents under `60-apps/etzhayyim-project-resources` including `TECH_STACK.jsonld`.
- `https://resources.etzhayyim.com/etzhayyim-project-resources/PROJECT.jsonld`

The `TECH_STACK.jsonld` file contains the comprehensive technology stack for this project (language, package manager, Pulumi/CDN/CDCI/Kubernetes, and data persistence model).


## Japanese Laws Dataset

All publicly available Japanese laws from the e-Gov Law API are collected as JSON-LD at:

- `content/legal/jp/laws.jsonld`

Regenerate with:

```bash
python 60-apps/etzhayyim-project-resources/tools/fetch_jp_laws_jsonld.py
```

## Compliance Rule Bundles

Compiled jurisdiction bundles for `etzhayyim:compliance` are published at:

- `content/legal/compliance-bundles/*.jsonld`
- `content/legal/jurisdictions/index.jsonld` (integration status by jurisdiction)

Regenerate with:

```bash
python 60-apps/etzhayyim-project-resources/tools/compile_compliance_bundles.py
python 60-apps/etzhayyim-project-resources/tools/compile_legal_jurisdiction_index.py
```

These bundles are derived from:

- `content/legal/jp/laws.jsonld`
- `content/legal/jp/compliance/jp-privacy-article-map.jsonld`
- `60-apps/etzhayyim-project-contracts/data/social-contracts/*.jsonld`

`jp-privacy-v1` is curated beyond title heuristics and now includes APPI article / PPC guideline provenance in `legal_bases`, plus obligation-level `source_basis_ids`.

`content/legal/jurisdictions/index.jsonld` joins the global legal source registry, currently published raw corpora, and compiled compliance bundles so `resources.etzhayyim.com` exposes which jurisdictions are still scaffold-only versus actually integrated.

## Threat Intelligence (TI)

Threat intelligence entities are written by the TI collector service into:

- `content/ti/indicator/<type>/<id>.jsonld`
- `content/ti/host/<id>.jsonld`
- `content/ti/locale/<id>.jsonld` (when provided)

### Network Intel Collector ingest

`etzhayyim-project-collector` (`collector.export_jsonld`) ingest is provided as a
App component:

- `60-apps/etzhayyim-project-resources/wasm/components/resources-collector-ingest-r8n4c1j6`

```bash
cd 60-apps/etzhayyim-project-resources/wasm/components/resources-collector-ingest-r8n4c1j6
etzhayyim build
kubectl apply -f <repo-deploy-config>
```

MCP tools:

- `ingest.run` (`endpoint`, `run_id`, `trigger_run`, `include_docs`)
- `ingest.status` (`limit`)
- `ingest.export_jsonld` (`refresh`, `endpoint`, `run_id`, `trigger_run`)

HTTP endpoints:

- `/api/mcp`
- `/scheduler/trigger`
- `/snapshot/latest`

## Crawler Data (crawler.etzhayyim.com)

Web crawl data collected by `crawler.etzhayyim.com` is normalized to JSON-LD and stored under `content/crawl/`.

### Storage Paths

| Entity | Path | Key | Description |
|---|---|---|---|
| CrawlJob | `content/crawl/job/<job_id>.jsonld` | `crawl/job/<job_id>` | One file per crawl job |
| CrawlPage | `content/crawl/page/<result_id>.jsonld` | `crawl/page/<result_id>` | One file per crawled page |
| WebSite | `content/crawl/site/<domain>.jsonld` | `crawl/site/<domain>` | Aggregated site summary |

### JSON-LD Types

| `@type` | Schema | Description |
|---|---|---|
| `etzhayyim:CrawlJob` | `shacl/crawler/shapes.jsonld` | Crawl job metadata (seed URL, depth, status, timestamps) |
| `etzhayyim:CrawlPage` | `shacl/crawler/shapes.jsonld` | Per-page crawl result (URL, HTTP status, title, size, links) |
| `schema:WebSite` | `shacl/crawler/shapes.jsonld` | Site-level aggregation (page count, last crawled) |

### JSON-LD Context

All crawler documents use `shacl/crawler/context.jsonld` as the shared `@context`. This maps:
- `schema:` (schema.org) for standard web properties (url, name, contentSize)
- `prov:` (W3C PROV) for provenance (generatedAtTime, wasGeneratedBy)
- `etzhayyim:` (resources.etzhayyim.com/ontology#) for crawler-specific terms (depth, httpStatus, linkCount)

### Example: CrawlJob

```json
{
  "@context": "https://resources.etzhayyim.com/ontology/crawler/context.jsonld",
  "@type": "etzhayyim:CrawlJob",
  "@id": "https://resources.etzhayyim.com/content/crawl/job/crawl-1739760000",
  "identifier": "crawl-1739760000",
  "url": "https://etzhayyim.com",
  "actionStatus": "completed",
  "depth": 2,
  "maxPages": 100,
  "pagesFound": 42,
  "startTime": "2026-02-17T00:00:00Z",
  "generatedAtTime": "2026-02-17T06:00:00Z",
  "userAgent": "etzhayyim-crawler/1.0"
}
```

### Example: CrawlPage

```json
{
  "@context": "https://resources.etzhayyim.com/ontology/crawler/context.jsonld",
  "@type": "etzhayyim:CrawlPage",
  "@id": "https://resources.etzhayyim.com/content/crawl/page/res-001",
  "identifier": "res-001",
  "url": "https://etzhayyim.com",
  "jobId": "crawl-1739760000",
  "name": "ETZHAYYIM - Artificial Organism",
  "httpStatus": 200,
  "contentSize": 24576,
  "linkCount": 18,
  "generatedAtTime": "2026-02-17T00:00:00Z"
}
```

### Example: WebSite (site summary)

```json
{
  "@context": "https://resources.etzhayyim.com/ontology/crawler/context.jsonld",
  "@type": "schema:WebSite",
  "@id": "https://resources.etzhayyim.com/content/crawl/site/etzhayyim.com",
  "url": "https://etzhayyim.com",
  "name": "ETZHAYYIM",
  "pageCount": 42,
  "lastCrawledAt": "2026-02-17T06:00:00Z",
  "hasPart": [
    "https://resources.etzhayyim.com/content/crawl/page/res-001",
    "https://resources.etzhayyim.com/content/crawl/page/res-002"
  ]
}
```

### Data Flow

```
crawler.etzhayyim.com (App MCP)
    |
    | MCP tools/call: crawler.list_results
    | REST: GET /crawls/{id}/results
    v
resource-writer (scheduler / Tekton task)
    |
    | 1. Fetch completed crawl jobs + results
    | 2. Normalize to JSON-LD (CrawlJob, CrawlPage, WebSite)
    | 3. Validate against shacl/crawler/shapes.jsonld
    | 4. Write to content/crawl/ via gitstate
    v
etzhayyim-project-resources (git repo)
    |
    | content/crawl/job/<job_id>.jsonld
    | content/crawl/page/<result_id>.jsonld
    | content/crawl/site/<domain>.jsonld
    v
resources.etzhayyim.com (published)
```

### SHACL Validation

Shapes are defined in `shacl/crawler/shapes.jsonld`:
- `etzhayyim:CrawlJobShape` - validates CrawlJob entities
- `etzhayyim:CrawlPageShape` - validates CrawlPage entities
- `etzhayyim:CrawlSiteShape` - validates WebSite (site summary) entities

## Public Company IR/News Ingest (incremental)

First increment supports one-company-at-a-time ingest with feed-based normalization.

### Company + Source definitions

- Company profile: `content/public-company/company/<company-id>.jsonld`
- Feed sources: `content/public-company/source/<company-id>.jsonld`
- Generated entities: `content/public-company/entity/<company-id>/*.jsonld`

Example (Vale S.A.):

- `content/public-company/company/vale-sa.jsonld`
- `content/public-company/source/vale-sa.jsonld`

### Ingest command

```bash
python 60-apps/etzhayyim-project-resources/tools/260303-public-company-ir-news-ingest.py \
  --company-id vale-sa \
  --dry-run
```

Remove `--dry-run` to write entity files and `index.jsonld`.

## Arrow Snapshot (DEPRECATED — legacy tooling)

JSON-LD files can be materialized into Arrow-schema tables via `jsonld-arrow-ingest`.
Storage backend has migrated to Cypher graph (kotodama WIT).

Tool:

- `60-apps/etzhayyim-project-resources/tools/jsonld-arrow-ingest`

Default output tables:

- `resources_jsonld_documents_current`
- `resources_jsonld_nodes_current`
- `resources_jsonld_properties_current`

## Curated Arrow-First Tables

For arrow-first typed tables, use:

- `60-apps/etzhayyim-project-resources/tools/curated-arrow-ingest`

Default current tables:

- `resources_cybersecurity_companies_current`
- `resources_cybersecurity_products_current`
- `resources_public_company_profiles_current`
- `resources_public_company_sources_current`
- `resources_public_company_signals_current`

Dry-run example:

```bash
cd 60-apps/etzhayyim-project-resources/tools/curated-arrow-ingest
go run . --dry-run
```

Writer tools that emit JSON-LD under this project now invoke the Arrow/Lance
sync automatically after successful writes. Use `--skip-lance-sync` on
`collector-ingest`, `crawl-ingest`, `fetch_jp_laws_jsonld.py`, or
`260303-public-company-ir-news-ingest.py` to opt out. The public-company IR
writer now sends a direct payload to `curated-arrow-ingest` for typed current
tables first, then refreshes the generic `jsonld-arrow-ingest` compatibility
snapshot for the full project so every JSON-LD document is represented in
`resources_jsonld_documents_current`, `resources_jsonld_nodes_current`, and
`resources_jsonld_properties_current`.
