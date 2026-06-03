---
id: adr-2604271200
title: MA Fund Person LEI Ingest Integration
status: accepted
doc_type: adr
topic: ma-ingest
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - ma-ingest-integration
  - fund-manager-ma-inputs
  - business-person-ma-inputs
  - lei-entity-resolution
related:
  - 60-apps/etzhayyim-project-ma/magatama.toml
  - 90-docs/260427-fund-ma-actor-activation-runbook.md
  - adr-2604261200
  - 30-graph/graph-schema/migrations/20260427040000_seed_fund_ma_bpmn_actors.ts
  - 30-graph/graph-schema/migrations/20260424161100_seed_open_lei_bpmn_actors.ts
supersedes: []
superseded_by: []
---

# Context

M&A execution needs three separate intelligence streams before the actor can
work as an operator rather than a demo workflow:

- fund manager and fund intelligence for LP sourcing, buyer matching, and
  sponsor analysis
- public business-person intelligence for officers, directors, registered
  agents, and relationship context
- LEI / legal-entity intelligence for stable organization identity, ownership,
  and cross-registry matching

These streams must not be collapsed into one generic "M&A ingest". They have
different provenance, privacy, licensing, retry, and graph-write rules.

# Decision

The MA app owns orchestration and use of these streams, but not every source
collector. `60-apps/etzhayyim-project-ma/magatama.toml` is the local integration
manifest that records the wiring.

The integration boundary is:

- BPMN / Zeebe orchestrates durable ingest and deal workflows.
- Python `pymagatama` workers run deterministic task handlers.
- PDS app records keep source and app-level records.
- RisingWave graph tables provide queryable deal, fund, person, and legal
  entity state.
- `mailer.etzhayyim.com` is the only standard email path. Outbound mail uses Resend;
  inbound mail uses Cloudflare Email Routing for `*@etzhayyim.com`.

As of 2026-04-27, the `business_person_collect_public_roles` path is no longer
just a BPMN wrapper. The local manifest now records the source request builder,
fetch adapter, and cursor handoff contract explicitly, with durable cursor
persistence still marked as planned.

# Stream Design

Fund manager ingest is already a Zeebe worker family under
`fund_manager_discovery`. The current task contract is:

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

It writes fund graph rows such as `vertex_fund_manager`, `vertex_fund`, and
fund relationship edges. It feeds MA buyer matching, DD counterparty profile,
and LP sourcing.

Business-person ingest has a BPMN wrapper under
`business_person_collect_public_roles`. It registers public collection jobs
through the business-person PDS app, prepares source-specific public registry
requests, fetches the public `sourceUrl`, and verifies graph visibility before
MA matching uses the results. It also has deterministic worker tasks to
normalize public role rows and write `vertex_business_person`. The first
source-specific extractors are:

- corporate HP: parses supplied public leadership page HTML/text, prefers
  JSON-LD `Person` records, and falls back to conservative leadership-line
  extraction
- Companies House: parses supplied officers API JSON `items` into public
  officer role rows
- gBizINFO: parses supplied corporate JSON into public representative role
  rows keyed by corporate number
- EDINET: parses supplied document metadata or extracted filing JSON into
  public officer/representative rows keyed by document ID or EDINET code
- SEC EDGAR: parses supplied submissions, ownership, or filing-derived JSON
  into public officer rows keyed by CIK
- Handelsregister: parses supplied German registry officer/company entry JSON
  into public officer rows keyed by register number

The first deterministic source parsers, source URL builders, generic public
`sourceUrl` fetch task, single-run cursor advancement, and next-page scheduler
handoff are present. The fetch adapter reads
`COMPANIES_HOUSE_API_KEY` for Companies House basic auth,
`SEC_USER_AGENT` for SEC EDGAR requests, and optional `GBIZINFO_API_TOKEN` for
gBizINFO. `businessPerson.advanceSourceCursor` computes `cursor`,
`nextSourceUrl`, and `hasNextPage` for paginated registry payloads such as
Companies House, and `businessPerson.scheduleNextPage` emits the next
business-person collection job payload when another page should be scheduled.
Production still needs durable cursor persistence, scheduler execution, and
HTML-to-JSON conversion before these workers can run continuously from
external registries. Existing seed coverage registers public registry sources,
role types, and
corporate HP collection jobs in
`60-apps/etzhayyim-project-business-person/seed.ts`. It must stay
public-disclosure-only: official filings, public leadership pages, and
registry data. It feeds MA research, matching, and approved outreach context,
but it must not fabricate private contact data.

The MA manifest records the business-person request and cursor contract
explicitly:

- `businessPerson.prepareSourceRequest` builds public source URLs from
  source-specific identifiers such as `companyNumber`, `corporateNumber`,
  `docId`, `cik`, and `registerNumber`.
- `businessPerson.fetchPublicSource` fetches the prepared URL and maps the
  response into source-specific workflow variables such as
  `companiesHouseJson`, `gbizInfoJson`, `edinetJson`, `secEdgarJson`,
  `handelsregisterJson`, or `htmlText`.
- `businessPerson.advanceSourceCursor` computes `nextSourceUrl`, `cursor`,
  and `hasNextPage`.
- `businessPerson.scheduleNextPage` emits a
  `com.atproto.repo.createRecord` payload for
  `com.etzhayyim.apps.businessPerson.collectionJob`.

This is a scheduler handoff, not yet durable cursor persistence. Durable
cursor tables, scheduled execution, and retry observability remain explicit
production work.

LEI ingest is the legal-entity resolver shared by both streams. OpenLEI/GLEIF
workers register:

- `openLei.gleif.manifest.plan`
- `openLei.gleif.bulk.collect`
- `openLei.gleif.record.normalize`
- `openLei.gleif.ems.match`

They write tables such as `vertex_open_lei_entity`,
`vertex_open_lei_ownership`, and `edge_open_lei_ownership_pair`. MA, fund, and
business-person records should link to these rows by LEI when available, and
fall back to source registry IDs plus source URLs when LEI is absent.

# Consequences

This gives MA a clear operating model:

1. Resolve organizations through LEI/legal-entity first.
2. Attach fund manager/fund/investor/investee context to legal entities.
3. Attach public person roles to legal entities.
4. Run MA intake, research, matching, DD, outreach approval, negotiation, and
   close/handoff against the combined graph.

The current repo is integrated enough for deterministic MA smoke runs,
fund-manager graph ingest pilots, and business-person public collection job
dispatch plus deterministic public-role graph writes from supplied rows. Full
production operation still needs business-person durable cursor persistence,
scheduler execution, fund fetcher pods, DD document tasks, LP eligibility
schema, and policy-gated outbound messaging.

# Rejected Alternatives

A single cross-domain ingest process was rejected because retries, licensing,
privacy, and graph visibility checks differ between fund data, public person
data, and legal-entity ownership data.

Direct autonomous outreach from ingest results was rejected. External email,
negotiation, DD requests, and LP solicitation must pass through human approval
and policy gates before `com.etzhayyim.apps.mailer.sendEmail`.
