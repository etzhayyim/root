---
id: 2605150000
title: "lg-isin — Resident LangServer for Global Listed-Company Data Ingest"
status: accepted
doc_type: adr
topic: lg-isin-listed-company-ingest-langserver
date: 2026-05-15
---
# ADR-2605150000: lg-isin — Resident LangServer for Global Listed-Company Data Ingest

- **Status**: Accepted
- **Date**: 2026-05-15
- **Author**: Jun Kawasaki
- **Supersedes**: —
- **Related**: ADR-2605080600 (LangGraph Server + Granian L3 Runtime), ADR-2605111200 (CF Worker edge-only)

---

## Context

No unified system existed for ingesting and normalising global public listed-company
organisational data. Company securities, exchange filings, IR pages, press releases, and
regulatory documents (e.g. EDINET 有価証券報告書) were scattered or absent. Downstream
consumers (legal-entity clustering, GLEIF LEI matching, fund NAV analysis) required a
reliable, incrementally-refreshed store of `vertex_isin_security` / `vertex_isin_filing` /
`vertex_isin_ir_doc` rows in the graphar schema.

Markets required:

| Market | Source | Volume |
|---|---|---|
| US | SEC EDGAR company_tickers + OpenFIGI `/v3/mapping` | ~13 K tickers |
| JP | OpenFIGI TSE range 1000–9999 | ~9 K numeric codes |
| HK | OpenFIGI HKEX range 1–3999 | ~4 K numeric codes |
| AU | ASX Listed Companies CSV | ~2 K tickers |
| EU | OpenFIGI `/v3/filter` (GY/FP/NA/BB/IM/LN exchCodes) | ~6 K+ |

---

## Decision

Deploy a single **resident LangServer pod** (`lg-isin`) in Kubernetes namespace
`mitama-udf` that owns all listed-company ingest. The pod exposes:

- **`/healthz`** — liveness / readiness probe
- **`/tools`** — JSON tool manifest (17 tools)
- **`/invoke`** — synchronous tool invocation
- **`/cron/*`** — async cron trigger endpoints (return 200 immediately, fire
  `asyncio.create_task`)

All database writes use `asyncpg` directly against `DATABASE_URL` (Kotoba/Datomic PostgreSQL
wire). No CF Worker hyperdrive binding. No Alembic migration runner at pod startup — schema
is pre-applied via separate migration jobs (ADR-2605111200 edge-only constraint).

### Graph Schema

```
vertex_isin_security        — one row per listed company
vertex_isin_filing          — SEC/EDINET filing metadata
vertex_isin_ir_doc          — IR page / PDF / Excel / Word text content
edge_isin_lei_match         — ISIN ↔ GLEIF LEI match
edge_isin_security_filing   — security ↔ filing linkage
mv_isin_security_country_cnt  — streaming count per country_code
mv_isin_filing_ticker_cnt     — streaming count per ticker
mv_isin_ir_doc_type_cnt       — streaming count per doc_type
```

### Tools (17)

| Tool NSID | Description |
|---|---|
| `listed.ingest.usSecurities` | SEC EDGAR tickers → OpenFIGI batch → vertex_isin_security |
| `listed.ingest.jpSecurities` | TSE numeric range → OpenFIGI → vertex_isin_security |
| `listed.ingest.hkSecurities` | HKEX numeric range → OpenFIGI → vertex_isin_security |
| `listed.ingest.auSecurities` | ASX CSV → vertex_isin_security |
| `listed.ingest.euSecurities` | OpenFIGI /filter (6 EU exchCodes) → vertex_isin_security |
| `listed.enrich.cik` | EDGAR CIK enrichment → exchange_mic, sic columns |
| `listed.ingest.edinetFiling` | EDINET filing list (documents.json) → vertex_isin_filing |
| `listed.ingest.edinetPdf` | EDINET PDF download → vertex_isin_ir_doc (requires EDINET key) |
| `listed.ingest.edinetSweep` | Rolling sweep of JP securities → filing + PDF |
| `listed.normalize.linkLeiIsin` | GLEIF LEI ↔ ISIN match → edge_isin_lei_match |
| `listed.normalize.linkSecurityFiling` | security ↔ filing → edge_isin_security_filing |
| `listed.news.fetchPressReleases` | RSS press-release fetch (on-demand) |
| `listed.ingest.irPage` | IR webpage scrape → vertex_isin_ir_doc |
| `listed.ingest.irPdf` | IR PDF download + pdfplumber extract → vertex_isin_ir_doc |
| `listed.ingest.irExcel` | IR Excel download + openpyxl extract → vertex_isin_ir_doc |
| `listed.ingest.irWord` | IR Word download + python-docx extract → vertex_isin_ir_doc |
| `listed.coverage.tick` | Coverage snapshot (SELECT COUNT per table) |

### CronJobs (10)

| CronJob | Schedule (UTC) | Endpoint | Notes |
|---|---|---|---|
| `isin-sweep-us` | Mon–Fri 02:03 | `/cron/sweep-us` | batchSize=500, advances `_us_cursor` |
| `isin-sweep-jp` | Mon–Fri 01:03 | `/cron/sweep-jp` | batchSize=50, TSE range |
| `isin-sweep-hk` | Mon–Fri 01:33 | `/cron/sweep-hk` | batchSize=50, HKEX range |
| `isin-sweep-au` | Monday 03:33 | `/cron/sweep-au` | batchSize=200, ASX CSV |
| `isin-sweep-eu` | Mon–Fri 02:33 | `/cron/sweep-eu` | batchSize=200, 6 EU exchanges |
| `isin-enrich-cik` | Sunday 03:07 | `/cron/enrich-cik` | limit=20, EDGAR CIK |
| `isin-link-lei` | Sunday 04:07 | `/cron/link-lei` | limit=200, GLEIF match |
| `isin-link-filing` | Sunday 04:37 | `/cron/link-filing` | limit=200, edge wiring |
| `isin-edinet-sweep` | Saturday 02:07 | `/cron/edinet-sweep` | limit=10, activeDeadlineSeconds=1800 |
| `isin-coverage-tick` | Daily 00:07 | `/cron/coverage` | coverage snapshot |

### Rolling In-Memory Cursors

```python
_us_cursor:    int  = 0       # offset into EDGAR tickers list
_jp_cursor:    int  = 1000    # OpenFIGI TSE ticker start
_hk_cursor:    int  = 1       # OpenFIGI HKEX ticker start
_au_cursor:    int  = 0       # offset into ASX CSV rows
_eu_exch_idx:  int  = 0       # index into _EU_EXCH_CODES list
_eu_cursors:   dict = {}      # OpenFIGI /filter `next` cursors per exchCode
_edinet_cursor: int = 0       # offset into JP securities for EDINET sweep
```

Cursors reset to initial values on pod restart. Ingest is dedup-safe (upsert pattern:
`INSERT … WHERE NOT EXISTS`), so restart-triggered re-ingest is harmless.

### Bootstrap

A one-shot `isin-bootstrap` Kubernetes Job triggers `/cron/bootstrap`, which fires
`asyncio.create_task(_run_bootstrap())` and returns 200 immediately. Bootstrap performs
a full sweep of all five markets (~44 min total) using sequential tool invocations inside
the async task. Apply once after initial deployment:

```bash
kubectl apply -f 50-infra/k8s/lg-isin/bootstrap-job.yaml
kubectl exec -n mitama-udf deploy/lg-isin -- \
  curl -s localhost:8080/cron/coverage
```

### Secrets

| Secret | Key | Use |
|---|---|---|
| `mitama-udf-pool-rw` | `KOTOBA_URL` | asyncpg connection string |
| `lg-isin-secrets` | `EDINET_SUBSCRIPTION_KEY` | EDINET PDF download (optional) |

EDINET key absence is handled gracefully: filing metadata is always ingested;
PDF download returns `{"ok": true, "blocked": "EDINET_KEY_MISSING"}`.

---

## Implementation Phases

### Phase 1 — IR Document Ingest (2026-05-15)
Added tools: `listed.ingest.irPage`, `listed.ingest.irPdf`, `listed.ingest.irExcel`,
`listed.ingest.irWord`. Requires `pdfplumber`, `openpyxl`, `python-docx`, `beautifulsoup4`
in the container image.

### Phase 2 — CronJobs + Bootstrap (2026-05-15)
Added 10 CronJobs in `cronjob.yaml`. Added `bootstrap-job.yaml` (one-shot full sweep).
Added `/cron/*` FastAPI endpoints with `asyncio.create_task` fire-and-forget pattern.
Added 3 streaming MVs via migration `20260515140000_isin_graph_wiring`.

### Phase 3 — HK / AU / EU Market Expansion (2026-05-15)
Added OpenFIGI HKEX numeric range ingest, ASX CSV ingest, OpenFIGI `/v3/filter` EU
pagination with `next` cursor. Added `_hk_cursor`, `_au_cursor`, `_eu_exch_idx`,
`_eu_cursors` rolling globals. EU exchCodes: `GY` (DE), `FP` (FR), `NA` (NL), `BB` (BE),
`IM` (IT), `LN` (GB), `SW` (CH).

### Phase 4 — EDINET 自動巡回 (2026-05-15)
Added `listed.ingest.edinetPdf` (single-doc PDF download) and `listed.ingest.edinetSweep`
(rolling sweep of JP securities → filing metadata + PDF). Added `_edinet_cursor` global.
Added `isin-edinet-sweep` CronJob (Saturday 02:07 UTC). EDINET subscription key is
injected from `lg-isin-secrets` secret (optional — metadata-only mode if absent).

---

## Migrations Applied

| Migration | Tables / Objects |
|---|---|
| `20260515120000_alter_vertex_isin_tables` | ALTER vertex_isin_security, vertex_isin_filing; CREATE edge_isin_lei_match |
| `20260515130000_vertex_isin_ir_doc` | CREATE vertex_isin_ir_doc + 3 indexes |
| `20260515140000_isin_graph_wiring` | CREATE edge_isin_security_filing + 3 streaming MVs |

Applied via psycopg2 phased DDL (table → index → MV, ~1.5s settle between phases) due to
active multi-head Alembic fork. See `30-graph/graph-schema/CLAUDE.md §Multi-Head Alembic
Workaround`.

---

## Consequences

**Positive**
- All global listed-company ingest is consolidated into a single, observable pod.
- Weekday sweeps keep the 5 major markets continuously refreshed within a 24h window.
- EDINET 有報 PDF text is available for downstream LLM analysis (fund/legal workflows).
- 3 streaming MVs provide sub-second coverage KPIs with no query overhead.
- IR document types (page / PDF / Excel / Word) are stored uniformly in `vertex_isin_ir_doc`.

**Negative / Trade-offs**
- In-memory cursors reset on pod restart — a restart mid-sweep duplicates a small window of
  ingest (harmless due to dedup, but adds latency).
- Bootstrap takes ~44 minutes. Monitor via `/cron/coverage`.
- OpenFIGI rate limits (2.6s sleep per batch) dominate per-market sweep latency.
- EDINET PDF requires a subscription key; without it, PDF content is unavailable.

---

## Monitoring

```bash
# Coverage snapshot
kubectl exec -n mitama-udf deploy/lg-isin -- \
  curl -s localhost:8080/cron/coverage | jq

# Recent logs
kubectl logs -n mitama-udf deploy/lg-isin --tail=100

# Cursor state (embedded in /cron/coverage response as sweepCursors)
kubectl exec -n mitama-udf deploy/lg-isin -- \
  curl -s localhost:8080/cron/coverage | jq .sweepCursors
```

---

## Files

```
50-infra/k8s/lg-isin/
  worker.py            — FastAPI LangServer (~1550 lines, 17 tools)
  deployment.yaml      — Deployment + ServiceAccount + Service
  cronjob.yaml         — 10 CronJobs
  bootstrap-job.yaml   — one-shot bootstrap trigger
  kustomization.yaml   — resources: [deployment.yaml, cronjob.yaml]
  Dockerfile           — python:3.12-slim + apt libxml2 + pip requirements
  requirements.txt     — asyncpg/aiohttp/fastapi/uvicorn/bs4/lxml/pdfplumber/openpyxl/python-docx
```
