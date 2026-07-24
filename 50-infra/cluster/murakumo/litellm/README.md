# LiteLLM gateway (etzhayyim Murakumo Tier-1)

Stateless OpenAI-compatible router for the etzhayyim Murakumo Mac-mini fleet.
Per ADR-2605191346 (Vultr-free, Mac-mini-only) and ADR-2605191358 (kotoba
inference substrate; durable job state lives in the CF Worker via
`@etzhayyim/sdk`, not here).

## Files

| File | Purpose |
|---|---|
| `config.yaml` | LiteLLM model_list + router settings. **No database.** |
| `com.etzhayyim.litellm.plist` | launchd LaunchAgent unit |
| `install.sh` | One-shot installer (venv + plist + log dirs + launchctl load + health probe) |

## Substrate boundary

LiteLLM is configured as a stateless proxy:

- `general_settings.master_key` is sourced from env (Keychain at install).
- **`database` field is absent** — no Prisma, no Postgres, no RW.
- Per-tenant accounting / usage / API-key auth lives in the CF Worker at
  `murakumo.etzhayyim.com` against `com.etzhayyim.murakumo.*` lexicons via
  `@etzhayyim/sdk` (ADR-2605191358 §RW sites replaced).

If billing or rate-limiting features ever need persistence, the storage
target MUST be the @etzhayyim/sdk substrate (MST + IPFS + L2). Adding a
local Postgres for LiteLLM would violate ADR-2605172000.

## Install

```bash
# 1. On the Mac-mini that will host the gateway (typically a low-utilization
#    fleet node), register the master key in Keychain:
KEY="sk-litellm-$(openssl rand -hex 32)"
security add-generic-password -s "etzhayyim.litellm" -a "MASTER_KEY" -w "$KEY" -U

# 2. Run the installer:
bash install.sh

# 3. Configure CF Tunnel ingress in the etzhayyim-murakumo-fleet tunnel:
#      murakumo-serve.etzhayyim.com → http://localhost:4000
#    Then DNS CNAME murakumo-serve.etzhayyim.com → <tunnel-id>.cfargotunnel.com.

# 4. Match the secret in each CF Worker that calls this gateway:
wrangler secret put LITELLM_MASTER   # paste $KEY
```

## Backend env (on the LiteLLM host)

```bash
# During transition from RunPod to Mac-mini Ollama:
export RUNPOD_GEMMA4_OPENAI_BASE="https://api.runpod.ai/v2/<endpoint-id>/openai/v1"
export RUNPOD_API_KEY="…"
```

Future: when the Mac-mini Ollama fleet replaces RunPod, swap the `api_base`
entries in `config.yaml` to `http://192.168.1.<n>:11434/v1` per node and
remove `RUNPOD_*` env. See `50-infra/cluster/murakumo/README.md` (tailmesh)
for the inter-node mesh.

## What did NOT migrate from upstream

The legacy `etzhayyim-root/60-apps/etzhayyim-project-murakumo/` carried
an Ansible-based provisioning tree (`roles/postgres`, `roles/langgraph`,
`roles/litellm` with a dormant `litellm_database_url` default, etc.). That
tree is **not** brought over because:

- etzhayyim provisioning is launchd (Mac) per ADR-2605191229 (Path A) and
  systemd (Linux) per ADR-2605191257 — not Ansible.
- The LangGraph control plane Postgres (langgraph.env.j2's `POSTGRES_URI`)
  must be replaced with `@etzhayyim/sdk`'s checkpointer
  (`20-actors/etzhayyim-sdk/src/checkpointer.ts`) before that workload can
  land in etzhayyim. Deferred to a follow-up ADR; not part of step 3.
- goose recipes (originally cited in ADR-2605191358 §murakumo cluster) were
  retired upstream 2026-04-30; no migration needed.

## References

- ADR-2605172000 (kotoba hard rule)
- ADR-2605191346 (Vultr-free; Murakumo Mac-mini Tier-1)
- ADR-2605191358 (yoro/murakumo kotoba rewrite map — this directory = step 3 minus deferred LangGraph)
- `50-infra/cloudflare/workers/murakumo/` (step 2 — the CF Worker that owns inference job state)
