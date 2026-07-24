# murakumo (CF Worker, etzhayyim kotoba rewrite)

LiteLLM gateway + async inference job tracker. Per ADR-2605191358 step 2.

## Substrate boundary

This worker MUST use `@etzhayyim/sdk` as the only durable-state client. Prohibited imports (enforced by `lint:kotoba`):

- `@atproto/api` (use `@etzhayyim/sdk` PDS verbs)
- `viem` (use `@etzhayyim/sdk` L2 verbs)
- `kysely`, `@etzhayyim/kotodama-host-sdk`, anything `kotoba` / `hyperdrive` flavored

No HYPERDRIVE binding in `wrangler.jsonc`.

## Architecture

```
Client → murakumo.etzhayyim.com (this Worker)
       → LITELLM_URL (LiteLLM gateway)
       → Mac-mini fleet (Tier-1, ADR-2605191346) / RunPod (legacy)
```

Durable state:

| Concern | Lexicon | rkey |
|---|---|---|
| Platform API key | `com.etzhayyim.murakumo.apiKey` | `sha256(rawKey)` lowercase hex |
| Inference job header | `com.etzhayyim.murakumo.inferenceJob` | UUID (`jobId`) |
| Inference job event (status transition) | `com.etzhayyim.murakumo.inferenceJobEvent` | `${jobId}~${seq:02}` |

The job state machine is event-sourced. Reading a job: `getRecord(inferenceJob, id)` + `listRecords(inferenceJobEvent, prefix=${id}~)`, reduce events in seq order. No UPDATE.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | none | Chat UI (HMAC chat-anon token issued inline) |
| GET | `/health` | none | Gateway + fleet roster |
| GET | `/_app/meta` | none | Meta + roster |
| GET | `/.well-known/agent.json` | none | ERC-8004 agent card |
| GET | `/v1/models` | required | OpenAI model list |
| POST | `/v1/chat/completions` | required | LiteLLM proxy (streaming + keepalive) |
| GET | `/v1/jobs` | required | Recent jobs |
| POST | `/v1/jobs` | required | Enqueue async job |
| GET | `/v1/jobs/:id` | required | Poll job status |
| POST | `/xrpc/com.etzhayyim.apps.murakumo.cronTick` | none | Zeebe cron tick → fleet health refresh |
| GET | `/internal/capacity` | none | Capacity summary |

## Auth tiers

1. Service Auth JWT (ES256, JWKS from `authn.etzhayyim.com`, internal services)
2. Platform API key `sk_live_*` / `sk_test_*` — looked up via `com.etzhayyim.murakumo.apiKey`
3. Chat anon HMAC `mkc_*` — 1h TTL, issued at `/`
4. Break-glass `MURAKUMO_API_KEY` (deprecated, env-only)

## Secrets to set

```bash
wrangler secret put LITELLM_MASTER
wrangler secret put MURAKUMO_CHAT_SECRET
# Either a resumable session JSON or handle+password JSON:
wrangler secret put MURAKUMO_PDS_SESSION   # {"did","handle","accessJwt","refreshJwt"}
wrangler secret put MURAKUMO_PDS_AUTH      # {"handle","password"}
wrangler secret put MURAKUMO_API_KEY       # optional break-glass
wrangler secret put OPENROUTER_API_KEY     # optional deepseek routing
```

## Local checks

```bash
pnpm typecheck
pnpm lint:kotoba
pnpm build
```

## References

- ADR-2605172000 (kotoba hard rule)
- ADR-2605191346 (Vultr-free + Murakumo Mac-mini Tier-1)
- ADR-2605191358 (yoro/murakumo kotoba rewrite map — this worker = step 2)
- Upstream legacy: `etzhayyim-root/50-infra/cloudflare/workers/murakumo/` (Kysely+Hyperdrive — retired)
