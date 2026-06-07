---
id: adr-2604261200
title: Fund Intel Zeebe Ingest
status: accepted
doc_type: adr
topic: fund-intel
authoritative: true
last_verified: 2026-04-26
authoritative_for:
  - fund-manager-ingest
  - fund-intel-worker-contract
related:
  - 90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md
  - adr-2604271200
  - 60-apps/etzhayyim-project-ma/magatama.toml
  - 90-docs/adr/0094-kotoba-stable-three-node-topology.md
  - 30-graph/graph-schema/migrations/20260416134500_fund_graph_spine_and_coverage.ts
supersedes: []
superseded_by: []
---

# Context

Fund intel needs durable ingest and analysis of fund managers, funds, LPs,
portfolio companies, AUM, commitments, distributions, growth signals, and
return metrics. The existing graph spine already has:

- `vertex_fund`
- `vertex_fund_manager`
- `vertex_fund_investor`
- `vertex_fund_investee`
- `edge_fund_managed_by`
- `edge_fund_backed_by`
- `edge_fund_invests_in`
- `edge_fund_sponsored_by`

The blocker is not table absence. The blocker is ingestion architecture:
global fund data is mixed public/private, partially licensed, and often
estimated. A CronJob that writes directly into Kotoba/Datomic would repeat the
same instability seen in bulk ingest incidents: retries can duplicate rows,
cursor advancement can outrun visibility, and RW recovery windows can turn a
source outage into graph corruption.

# Decision

Fund intel ingestion is a Zeebe-orchestrated Python worker family. It is not a
direct CronJob-to-Kotoba/Datomic pipeline.

The first pilot covers:

- SEC Form ADV for investment adviser / private fund manager discovery.
- GLEIF for legal-entity enrichment and LEI resolution.

Later sources can add SEC Form D, 13F, N-PORT, Preqin/PitchBook/Crunchbase-like
licensed feeds, pension disclosures, SWF annual reports, and fund websites,
but every source must enter through the same durable contract.

The BPMN task contract is:

- `fund.planSources`
- `fund.fetchRaw`
- `fund.persistArtifact`
- `fund.normalizeManager`
- `fund.normalizeFund`
- `fund.normalizeLp`
- `fund.normalizeInvestment`
- `fund.enrichEntity`
- `fund.computeReturns`
- `fund.writeGraph`
- `fund.verifyCoverage`

Required invariants:

- Raw artifacts are persisted before normalized graph writes.
- Entity IDs are deterministic and source-scoped.
- LP, return, AUM, and valuation values carry `sourceUrl`, `sourceLicense`,
  `confidence`, and a metric kind (`reported`, `estimated`, `derived`, or
  `unknown`).
- Estimated returns are never presented as reported facts.
- `rw.health.probe` must pass before `fund.writeGraph` writes to Kotoba/Datomic.
- Cursor advancement happens only after graph write visibility is verified.
- During RW degraded windows, workers may fetch and persist artifacts, but must
  skip graph writes.

# Consequences

This lets Zeebe provide durable retries and compensation while Python owns
source-specific parsing and entity resolution. It also lets fund intel scale by
source and shard without increasing Kotoba/Datomic write pressure during recovery.

The existing schema is enough for the first pilot, but it is incomplete for
full fund intelligence. A follow-up migration should add typed metric/history
tables for:

- fund metrics: `tvpi`, `dpi`, `irr`, `moic`, `aum`, `nav`,
  `committedCapital`, `calledCapital`, `distributedCapital`
- metric metadata: `asOfDate`, `periodStart`, `periodEnd`, `metricKind`,
  `sourceConfidence`, `sourceLicense`, `sourceUrl`
- person-level manager/partner attribution separate from organization-level
  adviser attribution

# Alternatives Considered

Direct CronJob ingest was rejected because it lacks durable per-source state
and makes RW instability user-visible.

Putting JSON blobs into a generic table was rejected as the canonical model.
Raw JSON is useful as an artifact, but queryable fund intel needs typed
columns for identity, money, dates, confidence, and relationships.

# References

- `90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md`
- `90-docs/adr/0094-kotoba-stable-three-node-topology.md`
- `30-graph/graph-schema/migrations/20260416134500_fund_graph_spine_and_coverage.ts`
