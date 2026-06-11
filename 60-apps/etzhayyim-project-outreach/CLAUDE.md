---
id: outreach-claude
title: Sales Outreach Automation — Runbook
status: active
doc_type: how-to
topic: outreach-runbook
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - outreach actor runbook
related:
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-0018-pii-tier3-cohort-first
---

# Sales Outreach Automation (`outreach.etzhayyim.com`)

ADR-2605072000 business model ③ of 5.

## Actor

- DID: `did:web:outreach.etzhayyim.com`
- Nanoid: `otch0001`
- CF Worker: `60-apps/etzhayyim-project-outreach/appview/outreach-otch0001/`
- Python worker: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/outreach_worker_main.py`
- BPMN: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/outreach/`

## Flow

```
createSequence XRPC
  → LangServer: outreach.check_dnc            (15s) — abort if on DNC
  → LangServer: outreach.run_research_agent   (180s) — LangGraph loop
      → research_prospect → draft_opening → quality_gate → store_step
  → LangServer: outreach.send_via_resend      (60s, step 1)
  → Timer: 3-day reply wait
  → ReplyGateway:
      replied=true  → RepliedEnd (mark sequence replied, stop)
      replied=false → outreach.send_via_resend (step 2 follow-up)
                    → outreach.create_sponsor_slot (optional ads.etzhayyim.com)
```

Reply detection: `subscribeRepos` on `com.etzhayyim.apps.gmail.message` +
`com.etzhayyim.apps.m365Ingest.email`. Worker correlates thread to active LangServer instance.

## PII Policy (ADR-0018)

- Tier 3 (sensitivity_ord=3): `email`, `prospectName`, `title`, `company`
- Cohort-first: `cohortName` required for `addProspect`
- DNC table: `vertex_outreach_dnc` — checked before every send step

## Tables

| Table | Purpose |
|---|---|
| `vertex_outreach_prospect` | Prospect PII (Tier 3) |
| `vertex_outreach_sequence` | Sequence state |
| `vertex_outreach_step` | Per-step draft + send record |
| `vertex_outreach_dnc` | Do Not Contact list |
| `edge_outreach_sent` | Sequence → prospect send edge |

## Env

```
AGENTGATEWAY_MCP_URL       gRPC address (default 127.0.0.1:26500)
RW_URL              RisingWave postgres URL
ANTHROPIC_API_KEY
RESEND_API_KEY
RESEND_FROM         sender (default outreach@etzhayyim.com)
ADS_XRPC_URL        ads.etzhayyim.com base (default https://adsm4d5c.etzhayyim.com)
```

## Start worker

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py
python -m kotodama.outreach_worker_main
# or: kotodama-outreach-worker
```
