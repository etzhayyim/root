# news.etzhayyim.com Intel Actor Process

Date: 2026-04-24

## Goal

`news.etzhayyim.com` publishes global news as intel, not commodity summaries. The actor process prioritizes primary and official sources, extracts factual claims, scores provenance, records an `com.etzhayyim.apps.intel.report`, and publishes an attributed writer-DID post only when confidence and priority pass gate thresholds.

## Architecture

- LangServer process: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/news/intelBrief.bpmn`
- UDF scoring: `news_source_credibility` and `news_intel_priority`
- XRPC/MCP commands: `com.etzhayyim.apps.news.listIntelSources`, `analyzeIntel`, `publishIntel`
- Intel record: `com.etzhayyim.apps.intel.report`
- Publisher identity: `did:web:news.etzhayyim.com:writer:{sourceId}`

## Flow

1. Fetch source URL and keep status/body as evidence.
2. Extract facts, entities, and findings from supplied/fetched text.
3. Score provenance with deterministic UDFs.
4. Write an intel report with source URL, source type, credibility, and priority metadata.
5. Publish only if `credibility >= 0.7` and `priority >= 0.45` unless explicitly disabled.
6. Emit audit event from the LangServer process.

## Source Policy

Primary/official sources include regulators, international organizations, statistics bodies, standards bodies, clinical registries, company IR, and direct press releases. Secondary RSS can still enter the pipeline, but it is classified as `needs-corroboration` unless source metadata proves primary/official status.
