---
id: 260426-site-common-crawl-zeebe-python-worker-design
title: "site.etzhayyim.com Common Crawl Zeebe / Python worker design"
status: implemented
doc_type: design
topic: ingest-orchestration
last_verified: 2026-04-26
related:
  - 90-docs/adr/0057-common-crawl-domain-ingest-coverage-topology.md
  - 90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md
---

# Summary

`site.etzhayyim.com` owns the web page archive and site read models. Common Crawl
remains an acquisition pipeline, while durable orchestration moves to Zeebe and
the write commit point stays in domain ingest.

# Process

`ingest_site_common_crawl_delta` is the canonical BPMN process.

1. `site.commonCrawl.createRun` records `vertex_ingest_run`.
2. `rw.health.probe` gates heavy work on Kotoba/Datomic health.
3. `site.commonCrawl.plan` validates crawl id, domain filter, selected phases,
   and artifact directory.
4. `site.commonCrawl.acquireCursor` locks one crawl/domain shard.
5. `site.commonCrawl.runPhase` executes selected phases:
   `download`, `graph`, `intel`, `domain-ingest`.
6. `site.commonCrawl.recordArtifacts` persists handoff artifacts to the ingest
   artifact spine.
7. `site.commonCrawl.verifyVisibility` checks site read-model visibility.
8. Cursor and run are completed only after verification.

# Safety

Subprocess execution is disabled unless the process variable
`allowSubprocess=true` or `SITE_CC_EXEC_ENABLED=1` is set. The chart defaults
to suspended dry-run mode because real Common Crawl runs may touch multi-TB
local artifacts.

# Files

- BPMN: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/ingest/siteCommonCrawlDelta.bpmn`
- Worker entrypoint: `20-actors/magatama/py/src/pymagatama/site_common_crawl_worker_main.py`
- Task handlers: `20-actors/magatama/py/src/pymagatama/ingest/site_common_crawl.py`
- Seed migration: `30-graph/graph-schema/migrations/20260426233000_seed_site_common_crawl_bpmn.ts`
- Helm: `50-infra/vultr/mitama-udf-pool/templates/site-common-crawl-worker.yaml`
  and `templates/cronjob-site-common-crawl.yaml`
