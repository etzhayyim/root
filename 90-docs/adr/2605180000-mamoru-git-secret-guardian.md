---
id: adr-2605180000-mamoru-git-secret-guardian
title: "mamoru — git secret guardian: CF Worker + LangGraph pod + GitHub Partner Program"
status: active
doc_type: adr
topic: mamoru-secret-scanning
authoritative: true
last_verified: 2026-05-18
authoritative_for:
  - mamoru secret scanning architecture
  - GitHub Secret Scanning Partner Program integration
  - processSecretAlert pipeline
  - repository.publicized webhook handling
priority: 8.5
axis: mamoru-security
weight: 0.85
related:
  - adr-2604282300
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
supersedes: []
superseded_by: []
---

# Context

Leaked credentials in git commits are one of the highest-signal security
signals available. GitGuardian demonstrated that scanning all public GitHub
repositories for secrets provides far broader coverage than installation-scoped
webhook scanning. mamoru (守る) is the etzhayyim implementation of this concept,
operating as an L3 Dispatcher CF Worker fronting a LangGraph pod.

Two gaps existed in the initial design:

1. **Coverage gap**: Only repositories with the GitHub App installed triggered
   scans. Repos made public, or repos belonging to other organisations that
   commit etzhayyim-issued keys, were invisible.

2. **Notification gap**: `MAMORU_NOTIFY_WEBHOOK_URL` was an empty string in
   `values.yaml`; the pod's notify node never fired.

# Decision

## Architecture

```
GitHub (all public repos)
  ├─ push webhook (installed repos)           → POST /webhook/github
  ├─ repository.publicized webhook             → POST /webhook/github (action=publicized)
  └─ Secret Scanning Partner Program          → POST /webhook/github-secret-scanning
          ↓ (all paths)
CF Worker mamoru.etzhayyim.com  (L3 Dispatcher, stateless)
          ↓ x-internal-trust HMAC
bpmn-dispatcher  (K8s ClusterIP)
          ↓ NSID routing
mamoru-langgraph pod  (mitama-udf namespace, Granian ASGI)
          ↓
RisingWave  (vertex_mamoru_{scan,incident,occurrence})
          ↓
Slack webhook  (mamoru-notify K8s Secret)
```

## 1. repository.publicized support

`POST /webhook/github` now handles both `push` and `repository` events.
When `action === "publicized"`, the worker fires `scanRepo` (full commit
history scan) instead of `scanCommit`.

GitHub App webhook settings must subscribe to the **Repositories** event
in addition to **Push events**.

## 2. GitHub Secret Scanning Partner Program

**Endpoint**: `POST /webhook/github-secret-scanning`

**Verification**: ECDSA-NIST-P256V1-SHA256 using GitHub's rotating public
keys fetched from `https://api.github.com/meta/public_keys/secret_scanning`.
Keys are cached in-module with a 5-minute TTL. The `github-public-key-identifier`
and `github-public-key-signature` headers are mandatory; requests without
them return 400.

**Token handling**: Raw token values are hashed (SHA-256) by the CF Worker
before logging. The raw value is forwarded exclusively over the
`x-internal-trust` HMAC channel to the pod for validity probing, then
discarded.

**Secret pattern registered with GitHub**:

| Name | Pattern |
|---|---|
| `etzhayyim_api_key` | `(?i)\bsk_live_[A-Za-z0-9]{32,}\b` |

**Application**: Sent to `secret-scanning@github.com` on 2026-05-18.
Message-ID: `d8dbcf17-1548-4817-8af8-6a5ae32daae6`.

## 3. processSecretAlert XRPC method

New lexicon: `com.etzhayyim.apps.mamoru.processSecretAlert` (procedure).

The pod handles pre-detected tokens directly — the 9-node scan pipeline
(parse_diff → detect_secrets → …) is bypassed. Instead:

1. Map GitHub token type → internal detector ID (`_gh_type_to_detector_id`)
2. Run validity probe via the detector's `.probe(token)` method
3. Score severity: valid=900, indeterminate=600, invalid=100 permille
4. Insert `vertex_mamoru_incident` + `vertex_mamoru_occurrence`
5. POST Slack notification if `MAMORU_NOTIFY_WEBHOOK_URL` is set and
   severity ≥ 600 permille

Token type mappings:

| GitHub type | Detector |
|---|---|
| `etzhayyim_api_key` | `etzhayyim-api-key` |
| `github_personal_access_token` / `github_oauth_access_token` / `github_app_installation_token` | `github-token` |
| `aws_access_key_id` | `aws-access-key-id` |
| `amazon_aws_secret_access_key` | `aws-secret-access-key` |
| (others) | `generic-high-entropy` |

## 4. Notification via K8s Secret

`MAMORU_NOTIFY_WEBHOOK_URL` is now injected from K8s Secret `mamoru-notify`
(key: `MAMORU_NOTIFY_WEBHOOK_URL`, `optional: true`). To enable Slack
notifications:

```bash
kubectl create secret generic mamoru-notify \
  --from-literal=MAMORU_NOTIFY_WEBHOOK_URL=https://hooks.slack.com/services/... \
  -n mitama-udf --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/mamoru-langgraph -n mitama-udf
```

## 5. SPA routing fix

Hono CF Worker now has a catch-all `GET *` route that forwards unmatched
paths to the Workers Assets binding (`ASSETS.fetch`), enabling SvelteKit
client-side routing for `/scan` and `/incident/[id]`.

# Surfaces

| Path | Method | Auth | Description |
|---|---|---|---|
| `/webhook/github` | POST | HMAC-SHA256 | push + repository.publicized |
| `/webhook/github-secret-scanning` | POST | ECDSA-P256 | Partner Program alerts |
| `/xrpc/com.etzhayyim.apps.mamoru.scanCommit` | POST | Bearer | manual / webhook-triggered scan |
| `/xrpc/com.etzhayyim.apps.mamoru.scanRepo` | POST | Bearer | full repo scan |
| `/xrpc/com.etzhayyim.apps.mamoru.processSecretAlert` | POST | Bearer (internal) | Partner Program pipeline |
| `/xrpc/com.etzhayyim.apps.mamoru.listIncidents` | GET | Bearer | incident list with filters |
| `/xrpc/com.etzhayyim.apps.mamoru.getIncident` | GET | Bearer | incident detail + occurrences |
| `/xrpc/com.etzhayyim.apps.mamoru.resolveIncident` | POST | Bearer | revoke / false_positive / accepted_risk |
| `/health`, `/_app/meta` | GET | none | edge probes |

# Deployment

- **CF Worker**: `magatama-m4m0ru01`, routes `mamoru.etzhayyim.com/*` + `m4m0ru01.etzhayyim.com/*`
- **Pod image**: `ghcr.io/etzhayyim/pymagatama:0.3.110-mamoru-20260518104334-amd64`
- **Helm release**: `mitama-mamoru-pool` (namespace `mitama-udf`, revision 4)
- **Dashboard**: `https://mamoru.etzhayyim.com/` (SvelteKit SPA, dark theme)

# Forbidden

- Direct LLM calls from the CF Worker
- `createKyselyDb` / `env.HYPERDRIVE` INSERT in the CF Worker
- Storing raw token values in RisingWave or logs (only SHA-256 hash)
- `com.atproto.repo.createRecord` for mamoru domain records
