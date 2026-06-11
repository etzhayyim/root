# lg-webmk — LangGraph Server actor for webmk.etzhayyim.com

Web Marketing Proposal Agent. OSS LangGraph FastAPI pattern (mirrors lg-yukkuri).

## Layout

```
lg/
├── langgraph.json                           # 5 graphs manifest
├── pyproject.toml
├── Dockerfile                               # OSS, no licensed base
├── lg_webmk/
│   ├── __init__.py
│   ├── audit.py                             # fire-and-forget BPMN generic.audit.emit
│   ├── checkpointer.py                      # _RwAsyncPostgresSaver (RW ON CONFLICT 回避)
│   └── graphs/
│       ├── health.py                        # com.etzhayyim.apps.webmk.health
│       ├── create_proposal.py               # com.etzhayyim.apps.webmk.createProposal
│       ├── deliver_proposal.py              # com.etzhayyim.apps.webmk.deliverProposal
│       ├── get_proposal.py                  # com.etzhayyim.apps.webmk.getProposal
│       └── list_proposals.py               # com.etzhayyim.apps.webmk.listProposals
└── tests/
    └── test_smoke.py                        # smoke tests
```

## NSID Coverage (5 of 5)

| NSID | assistant_id | graph file | status |
|---|---|---|---|
| `com.etzhayyim.apps.webmk.health` | `health` | health.py | ✅ |
| `com.etzhayyim.apps.webmk.createProposal` | `create_proposal` | create_proposal.py | ✅ |
| `com.etzhayyim.apps.webmk.deliverProposal` | `deliver_proposal` | deliver_proposal.py | ✅ |
| `com.etzhayyim.apps.webmk.getProposal` | `get_proposal` | get_proposal.py | ✅ |
| `com.etzhayyim.apps.webmk.listProposals` | `list_proposals` | list_proposals.py | ✅ |

## Proposal Lifecycle

DAG: `validate_input → generate_content → store_proposal → notify_delivery`

1. **validate_input** — Validates proposal request fields (company, budget, goals).
2. **generate_content** — LLM generates proposal sections (executive summary, tactics, KPIs, budget breakdown).
3. **store_proposal** — Persists to `vertex_webmk_proposal` with `actor_did`/`org_did` RLS columns (ADR-0095).
4. **notify_delivery** — Emits audit event; delivery triggers via `notifyCompany` pattern.

## LLM Models

| Role | Model | Trigger |
|---|---|---|
| Proposal generation | `gemma-4-e4b-it` | `createProposal` with content generation enabled |

Routes through `llm.etzhayyim.com` (LiteLLM gateway → murakumo-serve fleet).

## Env Vars

| Var | Default | Purpose |
|---|---|---|
| `RW_URL` / `LG_CHECKPOINTER_URL` | (required) | RisingWave PG :4566 |
| `WEBMK_APP_DID` | `did:web:webmk.etzhayyim.com` | Actor DID for audit |
| `WEBMK_LLM_URL` | `http://llm.etzhayyim.com` | LiteLLM gateway |
| `WEBMK_LLM_API_KEY` | `""` | Bearer token |
| `WEBMK_LLM_MODEL` | `gemma-4-e4b-it` | Proposal generation model |
| `WEBMK_LLM_TIMEOUT` | `30` | LLM request timeout (sec) |
| `LG_API_KEY` | `""` | Optional /runs auth key |

## Helm Chart

`50-infra/vultr/lg-webmk-pool/` — Deployment only (no CronJob; webmk has no resident cron loops).

## DB Schema

Graph table: `vertex_webmk_proposal` (migration `20260516650000_vertex_webmk_proposal_rls_columns.up.sql`).

Columns include `actor_did VARCHAR NOT NULL DEFAULT 'anon'`, `org_did VARCHAR NOT NULL DEFAULT 'anon'` per ADR-0095.

## Phases

| Phase | Scope | Status |
|---|---|---|
| **P1** LangGraph scaffold | 5 graphs + server + Dockerfile + langgraph.json | ✅ 2026-05-16 |
| **P1** DB schema | `vertex_webmk_proposal` | ✅ migration `20260516650000` |
| **P1** Helm chart | `50-infra/vultr/lg-webmk-pool/` | ✅ deployment.yaml |
| **P1** CF tunnel route | cloudflared ConfigMap webmk NSID routes | ✅ 2026-05-16 added to bpmn-dispatcher-tunnel.yaml |
| **P1** Lexicon | `00-contracts/lexicons/com/etzhayyim/apps/webmk/` | ✅ 5 lexicons (health + 4 XRPC) |
| **P2** LLM proposal content | Full gemma-4-e4b-it proposal generation | ✅ implemented in create_proposal.py |
| **P3** Delivery integration | Email/notification deliver pathway | ⏳ deliver_proposal.py stub wired, delivery backend pending |
