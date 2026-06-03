# ameno deploy runbook (Phase 1–5c)

Concrete kubectl / wrangler / pnpm commands to bring the ameno stack
(Phase 1 worker scaffold through Phase 5c credit metering) live. Every
phase already landed on `260512-agent-loop-main`; nothing here is
green-field. The runbook makes the chain reproducible and surfaces the
known operational gotchas before they bite during a live rollout.

- Actor: `did:web:ameno.etzhayyim.com` (nanoid `d94d27cb`)
- Edge: CF Worker `ameno.etzhayyim.com` (XRPC dispatcher; ADR-2605111200 — no DB)
- Pod: `ameno-langserver` in namespace `mitama-udf` (pymagatama image)
- Persist: `vertex_ameno_inferenceresult` on RisingWave (Vultr VKE)
- Firehose: NATS JetStream `pds.repo.commit.app_bsky_feed_post`
  (existing `pds-firehose-bridge` deployment)
- Credits: `vertex_credits_af_event` (Tier 2 reward; ADR-2605091700)

## Prerequisites

- 1Password: signed in (`op signin`); Vault `etzhayyim Japan株式会社` reachable.
- macOS Keychain: `etzhayyim.rw / KAISYA_URL` present (read-only RW); root
  URL pulled from 1Password by the schema loader.
- kubectl context: Vultr VKE `a61d513b-…` (lax). Verify with
  `kubectl get nodes -o wide` — should list `risingwave-pool-58gb-*` plus
  pool members for `mitama-udf`.
- Wrangler: `npx wrangler whoami` returns the etzhayyim CF account.
- ghcr: `gh auth token | docker login ghcr.io -u $(gh api user -q .login) --password-stdin`.
- Repo at the head with the Phase 5c commit (`a59a22265a4`) or later.

## Pre-flight checklist (one screen, do not skip)

```bash
# 1. PDS firehose bridge is running and producing the NATS subject
kubectl -n nats get deploy pds-firehose-bridge -o wide
kubectl -n nats logs deploy/pds-firehose-bridge --tail=20 | grep -E 'pds.repo.commit'

# 2. RW cluster is healthy (no recovery, no SlowDown)
50-infra/vultr/risingwave/rw-health-gate.sh

# 3. RW pool node has spare capacity (ameno-langserver = 256Mi/100m,
#    256Mi peak when both NATS subscriber + sync psycopg pool are warm)
kubectl -n mitama-udf top pod | sort -k4 -h | tail -5
```

If the firehose bridge is not publishing or rw-health-gate exits non-zero,
**stop here** and triage upstream. ameno is downstream-only; deploying it
on a broken substrate just stretches the failure radius.

## 1. Apply the inferenceresult schema

Phase 5i landed the Alembic counterpart, so the standard graph-schema
flow works:

```bash
source 30-graph/graph-schema/scripts/load-database-url.sh   # ROOT_URL
cd 30-graph/graph-schema
pnpm db:migrate
pnpm db:gen        # regenerates src/database.ts with the new Row type
pnpm db:drift      # must report OK before continuing
cd -

# Verify
psql "$DATABASE_URL" -c "\d vertex_ameno_inferenceresult"
```

If `pnpm db:migrate` errors with `Multiple head revisions` (the
chain-fork situation documented in `30-graph/graph-schema/CLAUDE.md`),
fall back to targeted upgrade:

```bash
cd 30-graph/graph-schema
pnpm exec alembic -c alembic.ini upgrade r_20260515031000_vertex_ameno_inferenceresult
cd -
```

`vertex_credits_af_event` (Phase 5c writes here too) already exists
from migration `20260429216000_credits_zeebe_support.ts`; no action.

The Phase 2 Kysely file at
`30-graph/graph-schema/migrations/20260515031000_vertex_ameno_inferenceresult.ts`
is kept as historical lineage and carries a SUPERSEDED header pointing
at the Alembic revision; do not replay it.

## 2. Rebuild the pymagatama image

The pod ships dispatcher routing, the SSE proxy, the ameno NSID
handlers, and the credit AF write. All four landed in this branch and
none of them are in the current production image
`pymagatama:maps-worldmonitor-market-91d57ab127d-20260514082800-amd64`.

```bash
# Remote BuildKit only (50-infra/CLAUDE.md — no local docker for VKE
# images; OrbStack/Rosetta is not a fallback).
70-tools/scripts/buildkit/remote-build.sh \
  --image ghcr.io/etzhayyim/pymagatama \
  --tag ameno-phase5c-$(date -u +%Y%m%d%H%M)-amd64 \
  --context 20-actors/magatama/py
```

Note the new tag — every later step substitutes it as `${IMAGE_TAG}`.

## 3. Apply the ameno-langserver manifest

```bash
# Bump the image to the freshly-built tag (or hand-edit the YAML).
sed -i.bak \
  "s|pymagatama:maps-worldmonitor-market-[^[:space:]]*|pymagatama:${IMAGE_TAG}|" \
  50-infra/k8s/ameno-langserver/ameno-langserver.yaml

kubectl apply -k 50-infra/k8s/ameno-langserver/

kubectl -n mitama-udf rollout status deploy/ameno-langserver --timeout=120s
kubectl -n mitama-udf get pod -l app.kubernetes.io/name=ameno-langserver -o wide
```

Smoke the pod's own surface before attaching any external traffic:

```bash
POD=$(kubectl -n mitama-udf get pod -l app.kubernetes.io/name=ameno-langserver \
        -o jsonpath='{.items[0].metadata.name}')

kubectl -n mitama-udf exec "$POD" -- curl -sS http://localhost:8081/healthz
kubectl -n mitama-udf exec "$POD" -- curl -sS http://localhost:8081/readyz
# subscribeBriefs handler — must emit `event: ready` within 6s.
kubectl -n mitama-udf exec "$POD" -- timeout 8 curl -sS -N \
  'http://localhost:8081/xrpc/com.etzhayyim.apps.ameno.subscribeBriefs?maxEvents=1&idleTimeoutSec=6' \
  -H 'accept: text/event-stream' | head -5
```

If `subscribeBriefs` errors with `nats connect failed`, the pod cannot
reach NATS — re-check `NATS_URL` (Phase 5a env) and the
`nats.nats.svc.cluster.local:4222` Service exists.

## 4. Bounce the bpmn-dispatcher (picks up new image)

The dispatcher Helm chart already references the same `pymagatama`
image — push the new tag through to it so `_proxy_to_lg_pod_sse`,
`AMENO_LANGSERVER_PROXY_NSIDS`, and the `subscribeBriefs` route exist
in-process.

```bash
helm -n mitama-udf upgrade --reuse-values bpmn-dispatcher \
  50-infra/vultr/mitama-udf-pool \
  --set dispatcher.imageFullRef="ghcr.io/etzhayyim/pymagatama:${IMAGE_TAG}"

kubectl -n mitama-udf rollout status deploy/bpmn-dispatcher --timeout=120s

# Sanity: dispatcher must route ameno saveResult to the langserver.
curl -sS https://dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.ameno.listHistory \
  --get --data-urlencode 'actorDid=did:web:ameno-smoke.etzhayyim.com' \
  --data-urlencode 'limit=1' | head -200
```

## 5. Rebuild + redeploy the atproto.etzhayyim.com PDS Worker

`50-infra/cloudflare/workers/atproto/src/routing-table.ts` got 4 ameno
entries across Phase 2 / 4a / 5g (`saveResult`, `listHistory`,
`subscribeBriefs`, `listActorAdapters`). Until the PDS is rebuilt those
NSIDs return 404 at the public edge.

```bash
cd 50-infra/cloudflare/workers/atproto
pnpm install
pnpm exec vitest run --reporter dot   # routing-table tests included
npx wrangler deploy
cd -

# Confirm one routed NSID is live before continuing.
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://atproto.etzhayyim.com/xrpc/com.etzhayyim.apps.ameno.cardHome
```

`cardHome` is local-only on the ameno worker, so it should return 200
even before step 6; the smoke just confirms the PDS itself is healthy.

## 6. Deploy the ameno worker

```bash
cd 60-apps/etzhayyim-project-ameno/appview/etzhayyim-wasm-ameno-d94d27cb
pnpm install
pnpm --filter ./svelte build       # produces svelte/.svelte-kit/cloudflare/
etzhayyim deploy --smoke-url https://d94d27cb.etzhayyim.com/health
cd -
```

`etzhayyim deploy` reads `magatama.jsonld` for the embed URL (Phase 1) and
publishes the `ameno.etzhayyim.com` route. The smoke-url flag fails the
deploy if `/health` is not 200 within ~30s.

## 7. End-to-end smoke test

```bash
# Default = atproto.etzhayyim.com (PDS, public edge). -v for raw responses.
70-tools/scripts/ameno/smoke-test.sh

# Run it again pointed at the worker directly to exercise the
# ameno.etzhayyim.com → sdk.pds.xrpc() → atproto.etzhayyim.com forward path.
AMENO_BASE_URL=https://ameno.etzhayyim.com 70-tools/scripts/ameno/smoke-test.sh
```

All three checks must pass:

- `saveResult persisted/queued`
- `listHistory contains probe`
- `subscribeBriefs ready`

`listHistory contains probe` can lag for a few seconds after a fresh
INSERT while the streaming MV catches up — re-run once if it fails.

## 8. Verification queries

```bash
source 30-graph/graph-schema/scripts/load-database-url.sh

# Inference results from the smoke test (and any earlier runs)
psql "$DATABASE_URL" -c "
  SELECT created_at, model_id, output_tokens, tokens_per_sec
  FROM vertex_ameno_inferenceresult
  WHERE actor_did = 'did:web:ameno-smoke.etzhayyim.com'
  ORDER BY created_at DESC
  LIMIT 5;
"

# Tier 2 credits attributed to the smoke probe
psql "$DATABASE_URL" -c "
  SELECT created_at, event_type, amount
  FROM vertex_credits_af_event
  WHERE user_id = 'did:web:ameno-smoke.etzhayyim.com'
    AND event_type = 'ameno_browser_inference'
  ORDER BY created_at DESC
  LIMIT 5;
"
```

A passing smoke run ⇒ one row in each. The credit row's `vertex_id`
should be `af://credits/did:web:ameno-smoke.etzhayyim.com/{resultId}`.

## Rollback

The four moving parts roll back independently. Pick the smallest scope
that covers the regression.

| Symptom | Roll back |
|---|---|
| `subscribeBriefs` returns 5xx | `kubectl -n mitama-udf rollout undo deploy/ameno-langserver` |
| `saveResult` 404 from `atproto.etzhayyim.com` | re-deploy the previous PDS Worker bundle (`wrangler rollback`) |
| `ameno.etzhayyim.com` HTML / chat broken | `etzhayyim deploy` the previous tag from `60-apps/.../wrangler.jsonc` (or `wrangler rollback`) |
| Schema regret | `DROP TABLE vertex_ameno_inferenceresult;` (no streaming MV depends on it as of Phase 5c, so the drop is safe) |

The credit AF events are append-only and best-effort; nothing rolls
those back. To stop accruing them, set `AMENO_CREDIT_BASE=0` in the
ameno-langserver Deployment env and `kubectl rollout restart`.

## Known gaps (track for the next phase)

- WebGPU LoRA weight merge in the browser is **wired but not
  applied** — selected adapters are recorded in
  `saveResult.loraAdapters` but `transformers.js` weights are
  unmodified. Per-actor inference quality matches base.
- `ameno.etzhayyim.com` CORS for cross-origin EventSource against
  `atproto.etzhayyim.com` is **assumed** healthy (PDS standard). Verify with
  the browser console once the chat page is open.
- Generated lexicon bundle files (`lexicon-registry.gen.ts` etc.) are
  intentionally never staged in Phase 1–5c commits because they
  collide with parallel WIP from other actors. The agent that lands
  the next ameno change should regen + commit those once the in-flight
  branches converge.

(Phase 5i closed the Kysely→Alembic gap previously listed here.)
