# Fund / M&A Actor Activation Runbook

Status: phase plan for turning the fund manager and M&A BPMN actors from
contract coverage into working operators.

## Current State

The durable runtime path already exists:

```text
client or app
  -> /xrpc/{nsid}
  -> bpmn-dispatcher
  -> Zeebe process instance
  -> kotodama.zeebe_worker_main
  -> Kotoba/Datomic graph rows / PDS / external tools
```

The fund and M&A contracts now have:

- BPMN process definitions:
  - `fund_manager_discovery`
  - `ma_start_deal_workflow`
  - `business_person_collect_public_roles`
- Lexicon bindings:
  - `com.etzhayyim.apps.fund.managerDiscovery`
  - `com.etzhayyim.apps.ma.startDealWorkflow`
  - `com.etzhayyim.apps.businessPerson.collectPublicRoles`
- graph seed bindings in `vertex_bpmn_process_def` and
  `vertex_bpmn_lexicon_binding`
- MA graph spine tables:
  - `vertex_ma_deal`
  - `vertex_ma_candidate`
  - `vertex_ma_valuation`
  - `vertex_ma_match`
  - `edge_ma_deal_candidate`
  - `edge_ma_deal_buyer`
- Python Zeebe task handlers for the first deterministic M&A flow:
  - `ma.salesOrigination.intake`
  - `ma.targetScreening.score`
  - `ma.investmentAdviser.valuation`
  - `ma.buyerMatching.rank`
  - `ma.tradeBroker.negotiate`
  - `ma.integration.closeAndHandoff`
  - `ma.writeGraph`
- integration manifest:
  - `60-apps/etzhayyim-project-ma/kotodama.toml`

Important limitation: the current M&A handlers are deterministic workflow
primitives. They create IDs, scores, ranges, buyer ranking, and graph rows.
They do not yet perform real outbound research, send email, negotiate with
counterparties, run due diligence over documents, or solicit LPs.

## Ingest Integration Design

The M&A app is the operator, but it does not own every collector. The standard
integration point is `60-apps/etzhayyim-project-ma/kotodama.toml`, with ADR
coverage in `90-docs/adr/2604271200-ma-fund-person-lei-ingest-integration.md`.

```text
GLEIF / legal registries
  -> OpenLEI / Legal Entity ingest
  -> vertex_open_lei_entity + ownership graph
  -> entity resolution for fund, business-person, and MA records

SEC ADV / fund sources
  -> fund_manager_discovery BPMN
  -> fund.* Zeebe tasks
  -> vertex_fund_manager / vertex_fund / fund edges
  -> MA buyer matching, LP sourcing, sponsor DD

public filings / corporate leadership pages
  -> business_person_collect_public_roles BPMN
  -> etzhayyim-project-business-person seed and collection jobs
  -> businessPerson PDS records + vertex_business_person
  -> MA company profile, officer context, approved outreach context

MA deal intake
  -> ma_start_deal_workflow BPMN
  -> matching / valuation / approval / mailer / graph write
```

### Fund Manager

Fund manager ingest is designed as a Zeebe worker family, not a direct cron
writer. The process is `fund_manager_discovery`, exposed through
`com.etzhayyim.apps.fund.managerDiscovery`. The current worker tasks plan SEC ADV
shards, normalize managers and funds, optionally enrich through GLEIF, compute
safe metric rows, write fund graph rows, and verify coverage.

It is integrated with MA as upstream intelligence. MA should consume fund
manager rows for buyer matching, LP candidate sourcing, sponsor profile, and DD
context. The remaining production gap is the source-specific fetcher pod and
resumable cursor scheduling for full SEC ADV/GLEIF backfills.

### Business Person

Business-person ingest now has a BPMN wrapper:
`business_person_collect_public_roles`, exposed through
`com.etzhayyim.apps.businessPerson.collectPublicRoles`. The wrapper dispatches
public collection jobs to the business-person PDS app, prepares
source-specific public registry requests, fetches the public `sourceUrl`,
checks Kotoba/Datomic health, normalizes public role rows, writes
`vertex_business_person`, and verifies graph visibility before MA matching
uses the rows. The first extractor is
`businessPerson.extractCorporateHpRoles`,
which handles supplied public leadership page HTML/text by reading JSON-LD
`Person` records and conservative leadership lines. The second extractor is
`businessPerson.extractCompaniesHouseOfficers`, which parses supplied Companies
House officers API JSON into public officer role rows.
The third extractor is `businessPerson.extractGbizinfoRepresentatives`, which
parses supplied gBizINFO corporate JSON into representative role rows keyed by
corporate number.
The fourth extractor is `businessPerson.extractEdinetOfficers`, which parses
supplied EDINET document metadata or extracted filing JSON into public
officer/representative rows keyed by document ID or EDINET code.
The fifth extractor is `businessPerson.extractSecEdgarOfficers`, which parses
supplied SEC EDGAR submissions, ownership, or filing-derived JSON into public
officer rows keyed by CIK.
The sixth extractor is `businessPerson.extractHandelsregisterOfficers`, which
parses supplied Handelsregister officer or company entry JSON into public
officer rows keyed by register number.
`60-apps/etzhayyim-project-business-person/seed.ts` still owns the seeded source
registry and role taxonomy.

It is explicitly public-disclosure-only: EDINET, gBizINFO, SEC EDGAR,
Companies House, Handelsregister, and official corporate leadership pages.

For MA, this stream supplies officer, director, registered-agent, and
affiliation context. It should link each role to a legal entity by LEI when
available, otherwise by source registry ID and source URL. It must not infer
private emails, private phone numbers, or non-public relationships.

The next implementation step is durable cursor persistence, scheduler
execution, and HTML-to-JSON conversion for each registry source. Source URL
builders, source cursor advancement, next-page scheduler handoff, Companies
House basic auth via `COMPANIES_HOUSE_API_KEY`, SEC User-Agent via
`SEC_USER_AGENT`, optional gBizINFO token support via `GBIZINFO_API_TOKEN`,
generic public `sourceUrl` fetch, Corporate HP extraction, Companies House
officer JSON extraction, gBizINFO representative extraction, EDINET officer
extraction, SEC EDGAR officer extraction, Handelsregister officer extraction,
the BPMN wrapper, deterministic writer, and graph visibility gate are now
present.

### LEI / Legal Entity

LEI is the shared identity resolver. OpenLEI/GLEIF tasks already exist in the
worker path:

- `openLei.gleif.manifest.plan`
- `openLei.gleif.bulk.collect`
- `openLei.gleif.record.normalize`
- `openLei.gleif.ems.match`

The graph side uses `vertex_open_lei_entity`, `vertex_open_lei_ownership`, and
`edge_open_lei_ownership_pair`. Fund managers, portfolio companies, buyers,
sellers, and business-person affiliations should resolve through LEI first
when a LEI exists. Non-LEI entities keep source registry IDs and evidence URLs
so a later LEI match can merge them deterministically.

## Minimum Path To Make Them Run

1. Apply the graph migration that seeds the process definitions, lexicon
   bindings, and MA graph tables:

```bash
cd 30-graph/graph-schema
pnpm install
pnpm kysely migrate:latest
```

Use the repo's actual graph migration command if this package has a wrapper in
the deployment environment. The required migration is:

```text
30-graph/graph-schema/migrations/20260427040000_seed_fund_ma_bpmn_actors.ts
```

2. Build and deploy a `kotodama` image that includes the new `ma.py` task
   registrations. The current checked-in Helm values still point at an older
   image tag, so rebuilding is required before production pods know about the
   new MA task types.

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py
SHA=$(git rev-parse --short HEAD)
IMG=ghcr.io/etzhayyim/kotodama:${SHA}

docker buildx build \
  --platform linux/amd64 \
  --tag "${IMG}" \
  --push \
  .

cd ../../..
helm upgrade --install mitama-udf-pool \
  ./50-infra/vultr/mitama-udf-pool \
  --namespace mitama-udf \
  --set image.tag="${SHA}" \
  --set image.fullRef="" \
  --wait --timeout 5m
```

3. Ensure runtime services and secrets exist:

- Zeebe gateway reachable from the worker:
  `ZEEBE_GATEWAY=zeebe-gateway.mitama-udf.svc:26500`
- Kotoba/Datomic URL in `mitama-udf-pool-rw/KOTOBA_URL`
- dispatcher strict auth secret when exposed through `dispatcher.etzhayyim.com`
- `VULTR_SERVERLESS_KEY` or a working `RUNPOD_LLM_URL` for LLM-backed tasks
- PDS service auth settings if BPMN tasks call `generic.pds.dispatch`
- mailer.etzhayyim.com available for standard email send/receive
- `SS_RESEND_API_KEY` on the mailer Worker for outbound Resend delivery
- Cloudflare Email Routing catch-all for inbound `*@etzhayyim.com`

4. Confirm the dispatcher deployed the BPMN rows into Zeebe:

```bash
kubectl -n mitama-udf logs deploy/bpmn-dispatcher --tail=200 | rg "ma_start_deal_workflow|fund_manager_discovery|deployed"
```

If deployment does not happen, check that `vertex_bpmn_process_def.deployed_at`
is still `NULL`, the XML is present, and the binding allowlist permits the
tables referenced by the process.

5. Start a smoke workflow through the dispatcher:

```bash
curl -sf -X POST "https://dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.ma.startDealWorkflow" \
  -H "x-internal-trust: ${DISPATCHER_INTERNAL_SECRET}" \
  -H "content-type: application/json" \
  -d '{
    "side": "sell-side",
    "clientName": "Acme Holdings",
    "targetName": "Acme Robotics",
    "sector": "robotics",
    "jurisdiction": "JP",
    "expectedValueUsd": 50000000,
    "operatorDid": "did:web:operator.etzhayyim.com"
  }' | jq
```

Expected result: the response contains `ok: true`, `bpmnProcessId:
ma_start_deal_workflow`, and variables with `dealId`, valuation fields,
matches, `pmiHandoffId`, and graph write counts.

6. Verify graph visibility:

```sql
SELECT deal_id, side, client_name, target_name, status, stage
FROM vertex_ma_deal
ORDER BY created_date DESC
LIMIT 10;

SELECT candidate_name, candidate_kind, fit_score, status
FROM vertex_ma_candidate c
LEFT JOIN vertex_ma_match m ON m.buyer_candidate_id = c.candidate_id
ORDER BY fit_score DESC NULLS LAST
LIMIT 20;
```

## Capability Matrix

| Capability | Current implementation | What is needed for real work |
| --- | --- | --- |
| Fund manager discovery | SEC ADV normalization, GLEIF enrichment, graph writer | real fetcher pod for SEC ADV bulk artifacts, resumable cursors, scheduled `fund_manager_discovery` runs |
| M&A intake | deterministic `ma.salesOrigination.intake` | authenticated app/UI intake, conflict check, client authorization record |
| Research | generic `http.fetch`, LLM JSON, GLEIF/OpenLEI pieces exist | source-specific research tasks for company, market, sanctions, litigation, filings, news, ownership |
| Buyer / LP matching | deterministic ranking from supplied candidates | candidate sourcing from graph, CRM, fund manager graph, public registries, private lists |
| Email drafting | `ma.outreach.composeDraft` creates a mailer.etzhayyim.com draft envelope | approval UI / human task, then `com.etzhayyim.apps.mailer.sendEmail` |
| Email sending | mailer.etzhayyim.com sends through Resend | external recipients must default to draft-only; direct send only after policy approval |
| Negotiation | `ma.tradeBroker.negotiate` prepares a negotiation envelope | term sheet state machine, counterparty messages, human approval, versioned offers |
| Due diligence | not implemented as MA tasks | data room ingest, checklist graph, document extraction, red-flag scoring, Q&A workflow |
| LP gathering | not implemented as MA tasks | investor suitability/accreditation status, consent, jurisdiction rules, outreach cadence, opt-out |
| Closing / PMI | deterministic handoff marker | closing checklist, signatures, funds-flow, integration tasks, post-close obligations |

## External Outreach Policy

External communication and LP solicitation must not be fully autonomous at the
first production level.

Use four operating levels:

- Level 0: simulation only. No external calls except public research.
- Level 1: internal research and graph writes. No outbound messages.
- Level 2: draft external emails and negotiation messages, but require human
  approval before send.
- Level 3: send approved messages and track replies; still require human
  approval for offers, term changes, NDA changes, LP solicitation, and closing
  instructions.
- Level 4: autonomous sending is reserved for low-risk internal notifications
  only, not M&A negotiation or LP solicitation.

For LP gathering, enforce before any outreach:

- jurisdiction
- investor type
- accreditation / professional investor status where applicable
- consent source
- relationship source
- offering restrictions
- opt-out status
- human owner

## Next Implementation Units

### Unit 1: Research and DD Tasks

Add worker tasks:

- `ma.research.companyProfile`
- `ma.research.marketMap`
- `ma.research.sanctionsLitigationCheck`
- `ma.dd.createChecklist`
- `ma.dd.ingestDocument`
- `ma.dd.extractRedFlags`
- `ma.dd.writeGraph`

These can use existing primitives:

- `generic.http.fetch`
- `generic.llm.json`
- `open_lei` / GLEIF handlers
- `generic.db.insert` or dedicated graph writers

### Unit 2: Email and Human Approval

Add worker tasks:

- `ma.outreach.composeDraft`
- `ma.outreach.createApprovalTask`
- `ma.outreach.sendApproved`
- `ma.outreach.recordReply`

Use `mailer.etzhayyim.com` as the standard provider:

- outbound: `com.etzhayyim.apps.mailer.sendEmail` -> Resend
- inbound: Cloudflare Email Routing -> `email-relay` ->
  `com.etzhayyim.apps.mailer.inboundEmail`
- sender addresses: `{local}@etzhayyim.com`, for example `ma@etzhayyim.com`

External-recipient policy should create a draft/approval envelope first. The
actual `com.etzhayyim.apps.mailer.sendEmail` call is allowed only after human
approval.

### Unit 3: Negotiation State Machine

Replace the current single `ma.tradeBroker.negotiate` placeholder with a small
state machine:

- `ma.negotiation.prepareTermSheet`
- `ma.negotiation.submitForApproval`
- `ma.negotiation.sendCounterpartyDraft`
- `ma.negotiation.recordCounter`
- `ma.negotiation.compareTerms`
- `ma.negotiation.escalateDecision`

Every outbound term change should be immutable and linked to the deal graph.

### Unit 4: LP Sourcing

Add tasks:

- `ma.lp.sourceCandidates`
- `ma.lp.screenEligibility`
- `ma.lp.composeIntroDraft`
- `ma.lp.recordConsent`
- `ma.lp.writeGraph`

LP outreach must run behind a compliance gate and should be disabled by default
until the jurisdiction and suitability schema is present.

### Unit 5: Observability

Add dashboards and smoke checks:

- active process instances by BPMN ID
- Zeebe incidents by task type
- graph rows written per process instance
- email drafts created / sent / rejected
- DD red flags by severity
- LP candidates by eligibility state

## Practical Answer

To make these actors actually work, do not try to make one giant "M&A agent".
Keep BPMN as the orchestrator and give it small, auditable tools:

```text
research -> graph evidence
DD -> checklist + document findings
matching -> ranked candidates
outreach -> draft + approval + send
negotiation -> versioned offers + approvals
LP gathering -> eligibility + consent + approved outreach
closing -> checklist + handoff graph
```

The current repo is ready for the first smoke run after image rebuild and
deployment. It is not yet ready for autonomous email, negotiation, DD, or LP
solicitation without the additional task handlers and approval gates above.
