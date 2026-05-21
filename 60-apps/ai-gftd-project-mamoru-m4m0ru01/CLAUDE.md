# mamoru.gftd.ai — git secret guardian

ADR refs: 2605080800 + 2605080600 (LangGraph Server) + 2604282300 (CF Worker = edge facade).

## Layer

L3 Dispatcher (CF Worker, stateless). All compute lives in
`mitama-mamoru-pool` LangGraph Server (Granian) which runs the 9-node
detection pipeline and writes incidents / occurrences to RisingWave.

## Surfaces

| Path | Purpose |
|---|---|
| `/webhook/github` | GitHub App push webhook (HMAC-256 verification) |
| `/xrpc/ai.gftd.apps.mamoru.scanCommit` | procedure — scan a commit diff |
| `/xrpc/ai.gftd.apps.mamoru.scanRepo` | procedure — full repo scan (Phase 2) |
| `/xrpc/ai.gftd.apps.mamoru.listIncidents` | query — list incidents |
| `/xrpc/ai.gftd.apps.mamoru.getIncident` | query — incident detail + occurrences |
| `/xrpc/ai.gftd.apps.mamoru.resolveIncident` | procedure — resolve/dismiss incident |
| `/health`, `/_app/meta` | edge probe |

## Detection pipeline (LangGraph pod)

```
parse_diff → detect_secrets → filter_false_pos → validate_credentials
    → score_severity → deduplicate → persist_findings → notify → emit_audit
```

Detectors (P1): aws-access-key-id, aws-secret-access-key, github-token, generic-high-entropy

## Auth

- `Bearer sk_live_*` — gftd API key (PDS verifies)
- `Bearer <ES256-JWT>` — AT Protocol session JWT
- `/webhook/github` — `X-Hub-Signature-256` HMAC-SHA256 (env `GITHUB_WEBHOOK_SECRET`)

## Forwarding model

```
GitHub App push webhook
    ↓ HMAC verify @ CF Worker
    ↓ POST /xrpc/ai.gftd.apps.mamoru.scanCommit → dispatcher.gftd.ai
bpmn-dispatcher (K8s ClusterIP)
    ↓ NSID routing → mamoru-langgraph.mitama-udf.svc.cluster.local:8000
mamoru LangGraph pod
    ↓ 9-node Pregel pipeline
    → RisingWave INSERT (vertex_mamoru_incident / occurrence / scan)
```

## Secrets (wrangler secrets)

```bash
wrangler secret put GITHUB_WEBHOOK_SECRET    # from GitHub App webhook settings
wrangler secret put DISPATCHER_INTERNAL_SECRET
```

## Deploy

```bash
cd 60-apps/ai-gftd-project-mamoru-m4m0ru01
gftd deploy
```

## Smoke

```bash
curl https://mamoru.gftd.ai/health
curl https://mamoru.gftd.ai/_app/meta

# List incidents (Bearer required)
curl 'https://mamoru.gftd.ai/xrpc/ai.gftd.apps.mamoru.listIncidents?limit=10' \
  -H "Authorization: Bearer sk_live_xxxxx"

# Manual scan trigger
curl -X POST https://mamoru.gftd.ai/xrpc/ai.gftd.apps.mamoru.scanCommit \
  -H "Authorization: Bearer sk_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "repoId": "gftdcojp/ai-gftd-apps-gftdcojp",
    "commitSha": "abc123",
    "diffPayload": "<base64-diff>"
  }'
```

## Forbidden

- Direct LLM API calls from this CF Worker
- Direct Hyperdrive INSERT from this CF Worker
- `sdk.pds.dispatch({type:"com.atproto.repo.createRecord",...})` for mamoru domain
- Any AT Repo emit of incident / occurrence rows (non-federable)
