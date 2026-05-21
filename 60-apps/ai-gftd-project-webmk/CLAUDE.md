# ai-gftd-project-webmk — Web Marketing Proposal Agent

**URL**: `https://webmk.gftd.ai` / `https://wbmk0001.gftd.ai`  
**DID**: `did:web:webmk.gftd.ai`  
**nanoid**: `wbmk0001`  
**ADR**: `90-docs/adr/2605072000-langgraph-agent-loop-pattern.md`

## Architecture

- **Server**: TS thin-edge CF Worker (proxies XRPC to dispatcher)
- **Agent Loop**: LangGraph (Python, L8 pod) via LangServer
- **Delivery**: Resend (email)
- **Ad Integration**: ads.gftd.ai `createCampaign` (optional, per request)
- **Data**: RisingWave via Hyperdrive

## Flow

```
createProposal XRPC
  → CF Worker → Dispatcher → LangServer message
    → BPMN: webmk_create_proposal
      1. webmk.run_proposal_agent  (LangGraph: research→competitors→strategy→copy→quality_gate→store)
      2. webmk.deliver_via_resend  (Resend transactional email)
      3. webmk.create_ad_campaign  (ads.gftd.ai createCampaign, if createAdCampaign=true)
```

## LangGraph Nodes

| Node | Tool | Output |
|---|---|---|
| `research_company` | Playwright scrape + Claude extract | `company_context` |
| `analyze_competitors` | common-crawl XRPC + Claude diff | `competitor_summary` |
| `generate_strategy` | Claude claude-sonnet-4-6 | `strategy_json` |
| `generate_copy` | Claude claude-sonnet-4-6 | `copy_markdown` |
| `quality_gate` | score ≥ 0.7 → proceed, else retry once | `quality_score` |
| `store_proposal` | RisingWave INSERT vertex_webmk_proposal | `proposalId` |

## XRPC Endpoints

### Procedure (2)
`ai.gftd.apps.webmk.{createProposal, deliverProposal}`

### Query (2)
`ai.gftd.apps.webmk.{getProposal, listProposals}`

## RisingWave Tables

| Table | Purpose |
|---|---|
| `vertex_webmk_proposal` | Proposal records (status, strategyJson, copyMarkdown, qualityScore) |
| `vertex_webmk_client` | Client records (clientName, websiteUrl, industry) |
| `edge_webmk_campaign_link` | Proposal → ads.gftd.ai campaignId linkage |

## Python Worker

`20-actors/magatama/py/src/pymagatama/webmk_worker_main.py`

Job types handled:
- `webmk.run_proposal_agent` — LangGraph loop (main agent)
- `webmk.deliver_via_resend` — Resend email delivery
- `webmk.create_ad_campaign` — XRPC to ads.gftd.ai

## Env Requirements

```
AGENTGATEWAY_MCP_URL   — LangServer gRPC (default 127.0.0.1:26500)
RW_URL          — RisingWave postgres URL
ANTHROPIC_API_KEY
RESEND_API_KEY
RESEND_FROM     — e.g. "webmk@gftd.ai"
ADS_XRPC_URL    — ads.gftd.ai base URL (default https://adsm4d5c.gftd.ai)
```

## Deploy

```bash
cd 60-apps/ai-gftd-project-webmk/appview/webmk-wbmk0001
gftd deploy

# Start Python worker
python -m pymagatama.webmk_worker_main

# Smoke test
curl https://wbmk0001.gftd.ai/health
curl -X POST https://wbmk0001.gftd.ai/xrpc/ai.gftd.apps.webmk.createProposal \
  -H "Content-Type: application/json" \
  -d '{"clientName":"ACME Corp","websiteUrl":"https://acme.example.com","industry":"retail","deliveryEmail":"test@example.com"}'
```
