---
name: etzhayyim-cf-worker-deploy-check
description: Drive computer-use-clj to inspect a Cloudflare Worker's deployment state on the dash — why the active version is pinned, whether Workers Builds (git CI) owns it, and how to advance it. Read-only by default; gated promote optional. Built for the ADR-2606272300 Step-2 activation blocker (etzhayyim-did-web).
adr: 2606272300
tool: computer-use-clj
posture: read-only-default
---

# etzhayyim-cf-worker-deploy-check

A **computer-use-clj**-driven ops skill that visually inspects a Cloudflare
Worker's **deployment state** in the Cloudflare dashboard and reports it as EDN.

## Why this exists

ADR-2606272300 Step 2 (serve `com.atproto.sync.getRepo` from the edge in the
apex `etzhayyim-did-web` Worker) is **code-complete and merged** (PR #2580, the
handler lives in `cljs/src/did_web/xrpc.cljs`; routing verified
`core.cljs:268 :xrpc → xrpc/handle`), and the 3 actor repo CARs are published
to `ACTOR_KV` (`d33de8e0…`). But the change is **not live** because:

- the live worker's **active version is pinned to a 2026-06-25 build**
  (`c6507364…`), and
- manual `wrangler deploy` + `wrangler versions deploy <id>@100%` report
  SUCCESS but **do not advance the active version**, and
- no merge this session (incl. #2580) auto-advanced it → there is likely a
  **Workers Builds (git CI)** integration that owns the active-version pointer,
  OR a gradual-deployment / pinned-deployment setting.

`wrangler`'s output is contradictory on this, so the ground truth lives in the
**Cloudflare dashboard**. This skill drives a computer-use agent to read it.

## What it checks (read-only)

For the worker (default `etzhayyim-did-web`, account
`4da88288dc30d9ee257f319d3c33ecf0`) it reads and saves:

- the **active (100%) deployment**: version id, deployed-at, and **Source**
  (`Upload` = wrangler/API · `Workers Builds` = git CI · `Version` = gradual),
- whether **Workers Builds** is connected (Settings → Build) and to which
  **GitHub repo + branch**,
- the recent version/deployment history,
- **how the active version is set** (manual Deploy vs auto on git push), and
- the **exact dashboard control** to advance the active version to the latest.

→ `cf-worker-deploy-check.edn` (`:cf/active-version-id`, `:cf/active-source`,
`:cf/workers-builds-connected`, `:cf/how-active-set`, `:cf/promote-instructions`, …).

## Run

The runnable task is `examples/cf_worker_deploy_check.clj` in
`orgs/com-junkawasaki/computer-use-clj` (sibling of `sumitclub_meisai.clj`).
Have a browser open and your Cloudflare dash session signed in (or provide a
vault item; login goes through `type_secret`, never a raw credential).

```sh
cd orgs/com-junkawasaki/computer-use-clj

# read-only inspection (recommended model = anthropic for dashboard nav;
# local Ollama gemma-4-QAT also works, tools+vision)
LLM=anthropic ANTHROPIC_API_KEY=… \
  clojure -M:dev:examples -e "(require 'cf-worker-deploy-check) (cf-worker-deploy-check/-main)"

# inspect a different worker / account / output:
CF_WORKER=etzhayyim-did-web CF_ACCOUNT_ID=4da88288dc30d9ee257f319d3c33ecf0 \
CF_OUT=/tmp/cf-check.edn  LLM=anthropic ANTHROPIC_API_KEY=… \
  clojure -M:dev:examples -e "(require 'cf-worker-deploy-check) (cf-worker-deploy-check/-main)"
```

### Gated promote (explicit opt-in)

Once the check confirms the active version is stale and the latest merged build
is the one to serve, advance it with the **promote** mode — it performs exactly
ONE change (promote the newest version to 100%) and nothing else:

```sh
CF_PROMOTE=1 LLM=anthropic ANTHROPIC_API_KEY=… \
  clojure -M:dev:examples -e "(require 'cf-worker-deploy-check) (cf-worker-deploy-check/-main \"promote\")"
```

## Guardrails (in the agent's system prompt)

- **Credentials** — only `type_secret` (vault ref); the secret never enters the
  prompt, message history, or the Datomic action log. Unexpected 2FA/SSO with no
  secret_ref → `done success=false`.
- **Read-only default** — never Deploy / Promote / Rollback / Edit / Save /
  Delete / Disconnect / Retry-build / Rename / toggle anything; cancel any
  change dialog.
- **Promote mode** — one change only: advance the **newest** version to 100%;
  never edit code, change settings, or roll back; confirms the version id+date
  before acting; no-op if it's already active.
- Every action is an auditable datom (`:caction/*`); the secret is recorded only
  as its ref.

## After the check

Use the findings to finish ADR-2606272300:

1. If **Workers Builds (git)** owns the active version → the merge of #2580 will
   (or already did) build it; confirm/retry the build, then verify edge serving:
   `curl -sD- "https://etzhayyim.com/xrpc/com.atproto.sync.getRepo?did=did:web:etzhayyim.com:actor:unspsc-10101500"`
   should carry `x-etzhayyim-substrate: edge-content-addressed`.
2. If it's **manual/gradual** → run the gated **promote** to advance to the
   merged build.
3. Then ADR Step 3 (did.json `#atproto_pds` → `etzhayyim.com`) + Step 4 (retire
   the asher/laptop PDS + tunnel).
