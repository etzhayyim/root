# etzhayyim-project-kotodama — Goose Agent Platform Observability

## Overview

**Dashboard for the Goose agent platform.** Surfaces recipe inventory, cron
cadence, and recent run history for agents running on the Mac mini fleet.

Responsibility separation (2026-04-20):

| Layer | URL | Role |
|---|---|---|
| **murakumo** | `murakumo.etzhayyim.com` | OpenAI-compatible inference API (LiteLLM → 10 Ollama backends) |
| **kotodama** | `kotodama.etzhayyim.com` | Goose agent platform observability (recipes, cron, runs, fleet mirror) |
| **goose** | (judah, LaunchAgent via @reboot crontab) | Per-recipe agent runtime (ollama provider, MCP tool loop) |

## Architecture

```
Browser → kotodama.etzhayyim.com (CF Worker, Hono)
  ├─ GET /                  → dashboard HTML (auto-refresh 15s)
  ├─ GET /_app/meta          → {recipes, runs, murakumo}
  ├─ GET /api/goose/runs     → recent vertex_repo_commit rows
  └─ GET /api/goose/recipes  → aggregated runs per {repo, collection}

Data sources:
  HYPERDRIVE binding → RisingWave public.vertex_repo_commit
                       (filtered to GOOSE_REPOS = goose-driven agent DIDs)
  MURAKUMO binding   → Worker RPC → GET /_app/meta (fleet+LiteLLM status)
```

## Goose Cron Wrapper (ADR-0034)

judah only. crontab `@reboot` + per-recipe schedule entries. Each entry
invokes `~/.etzhayyim/goose-cron-wrapper.sh` with env vars:

| Env | Purpose |
|---|---|
| `RECIPE` | `~/.config/goose/recipes/<name>.yaml` |
| `REPO_DID` | `did:web:{agent}.etzhayyim.com` |
| `COLLECTION` | `ai.etzhayyim.apps.{agent}.{eventType}` |
| `CADENCE_MS` | joucho-throttle baseline (overridable via `vertex_actor_shinka_state`) |

Wrapper steps (abridged):
1. Resolve `RW_URL` via macOS Keychain (`etzhayyim.rw`) → fallback `~/.etzhayyim/rw-url`
2. Query `vertex_actor_shinka_state.cadence_ms` for dynamic cadence override
3. Decide `[fire]` / `[skip]` based on (elapsed vs cadence)
4. `INSERT INTO public.vertex_repo_commit` (primary side-effect, owns
   reliability per ADR-0034 — goose LLM body is optional enrichment)
5. Optional `app.bsky.feed.post` via `etzhayyim agent-token` (skipped if no token)
6. Append `[done]` + invoke goose (LLM) for narrative enrichment

**Why the wrapper owns writes**: qwen3.5:9b intermittently drops tool_calls
when >3 shell steps are present. Heartbeats must be deterministic; goose
enrichment is allowed to be spotty.

## Recipes (judah `~/.config/goose/recipes/`)

| Recipe | Collection | Cadence |
|---|---|---|
| `yoro-profile-heartbeat.yaml` | `ai.etzhayyim.yoro.heartbeat` | 1h |
| `yoro-persona-cron.yaml` | `ai.etzhayyim.yoro.personaCron` | 4h |
| `yoro-mention-drain.yaml` | `ai.etzhayyim.yoro.mentionDrain` | (as configured) |

Multi-agent expansion: as more agents join the goose platform, add their
DIDs to `GOOSE_REPOS` in `50-infra/cloudflare/workers/kotodama/src/worker.ts`
(or migrate to an `agent_origin` column per ADR-0034 §Pending).

## Files

| Path | Role |
|---|---|
| `50-infra/cloudflare/workers/kotodama/src/worker.ts` | Hono entry + Kysely queries |
| `50-infra/cloudflare/workers/kotodama/src/dashboard-html.ts` | Self-contained dashboard HTML + polling JS |
| `50-infra/cloudflare/workers/kotodama/wrangler.jsonc` | Route `kotodama.etzhayyim.com/*` + `HYPERDRIVE` + `MURAKUMO` bindings |
| `50-infra/cloudflare/workers/routing-gateway/wrangler.jsonc` | `WORKER_KOTODAMA` service binding |
| `60-apps/etzhayyim-project-murakumo/ansible/roles/goose/` | goose install + recipe deploy + cron registration |
| `60-apps/etzhayyim-project-murakumo/ansible/roles/litellm/` | LiteLLM router (consumed by murakumo layer, not goose — goose uses native Ollama to preserve tool_calls) |
| `90-docs/adr/0034-agent-cron-goose-risingwave-direct.md` | Design rationale |

## Deploy

```bash
# kotodama Worker
cd 50-infra/cloudflare/workers/kotodama
npx wrangler deploy

# Register service binding (once)
cd ../routing-gateway
npx wrangler deploy

# Verify
curl -sS https://kotodama.etzhayyim.com/health
curl -sS https://kotodama.etzhayyim.com/_app/meta | jq '.recipes | length, .runs | length'
```

## Related

- **ADR-0038: kotodama organizer — joucho shinka × Shannon × Bayes** (this
  dashboard's governor; LLM narrative + auto-archive + cross-repo rebalancing)
- ADR-0034: Goose + RisingWave direct (agent-cron wrapper design)
- ADR-0022: Auth topology (scoped API keys, relevant when goose writes to PDS)
- `[[migrations]] yoro-cron-goose-migration` (status: in-progress → this dashboard
  surfaces its operational state)
- `60-apps/etzhayyim-project-murakumo/CLAUDE.md` §Goose agent runtime
