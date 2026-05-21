# yatabase.etzhayyim.com — retail cloud graph DB + integrated Supabase-style storage

Authoritative: ADR-2605080000 §D10 + Roadmap P3 / P3.1.
**io-yatabase BaaS surface 拡張** (Cypher / Bolt / Realtime / PostgREST / GraphQL / Auth / Functions / MCP / Studio): ADR-2605080000 §D12-D24 (codename io-yatabase, Roadmap P4a-P4f, M3-M5)。

## Layer

L3 Dispatcher (CF Worker, edge). State-less. All persistence + heavy compute lives in L4 RisingWave + L7 LangServer pod-side LangServer handlers.

## Surfaces

| Path | Purpose |
|---|---|
| `/storage/v1/object/{bucket}/{key}` | Supabase-shape REST (PUT/GET/HEAD/DELETE) |
| `/storage/v1/object/list/{bucket}` | List objects |
| `/storage/v1/object/sign/{bucket}/{key}` | Presigned URL mint |
| `/storage/v1/object/public/{bucket}/{key}` | Public-ACL download (P3.2 stub) |
| `/storage/v1/bucket` | List buckets |
| `/auth/v1/portal` | Stripe Customer Portal session (P71, self-serve billing) |
| `/auth/v1/whoami` | Current bearer's tenant identity (P76) |
| `/auth/v1/attach-email` | Attach a recovery email — verification required (P76/P83) |
| `/auth/v1/verify-email` | Click-link verification gating recovery (P83) |
| `/auth/v1/recover` | Email-based API key recovery (anonymous, P76) |
| `/auth/v1/redeem` | Exchange recovery token for new API key (anonymous, P76) |
| `/sparql` | SPARQL 1.1 SELECT/CONSTRUCT/ASK |
| `/xrpc/ai.gftd.apps.yata.*` | Native XRPC pass-through |
| `/xrpc/ai.gftd.apps.billing.*` | Tenant billing read-side |
| `/health`, `/_app/meta` | Edge probes |
| `/s3/{bucket}/{key}` (P3.2) | AWS SigV4 compat |
| `/pg` (Phase 11) | PG protocol via Vultr LB |

## Auth

- `Bearer sk_live_yata_*` — product-scoped API key (P2 ADR-2605080000 §D9). **Resolved via `POST /xrpc/ai.gftd.apps.yata.authResolveApiKey` on the lg-yatabase pod** (since ADR-2605111200 prohibits the Worker from reading `vertex_api_key` directly through Hyperdrive). Worker SHA-256s the raw key, HMAC-signs the lookup body with `DISPATCHER_INTERNAL_SECRET`, and forwards via the dispatcher proxy. productScope=`yata` is returned by the pod and enforced by `enforceApiKeyProductScope` on the Worker.
- AT Protocol session JWT (Bearer ES256) — falls through to `PDS_SERVICE` binding `com.atproto.server.getSession` (legacy unchanged).
- `/storage/v1/object/public/*` — no auth, only when bucket `public_read=true` AND ACL grants public.

## Forwarding model (ADR-2605111200, P59 2026-05-11)

```
Client → CF Worker (yatabase.etzhayyim.com)
   ↓ auth middleware:
   │   sk_live_yata_* → POST https://dispatcher.etzhayyim.com/xrpc/ai.gftd.apps.yata.authResolveApiKey
   │                    (HMAC over body, bpmn-dispatcher proxies to lg-yatabase pod)
   │   ES256 JWT     → PDS_SERVICE getSession (legacy)
   ↓ resolved { did, orgDid, activeDid, productScope }
   ↓ POST/GET https://dispatcher.etzhayyim.com/xrpc/ai.gftd.apps.yata.*
      headers: x-internal-trust=<HMAC>, x-gftd-org-did, x-gftd-actor-did,
               x-gftd-product-scope=yata, x-gftd-trace-id
CF Tunnel → cloudflared pod → bpmn-dispatcher pod
   ↓ pymagatama dispatcher_main.py:
   │   auth_middleware verifies HMAC-SHA256(body, secret) OR legacy raw secret
   │   nsid.startswith("ai.gftd.apps.yata.") → _proxy_to_lg_yatabase
   │   else → LangServer BPMN-contract process (legacy path for non-yata NSIDs)
   ↓ HTTP POST/GET http://lg-yatabase.mitama-udf.svc.cluster.local:8000/xrpc/{nsid}
lg-yatabase Granian pod (mitama-udf):
   • signup / invite / revoke / authResolveApiKey  — auth/handlers.py
   • leadIngest / leadList / leadGet / lead{Outreach,Email,Enrichment,Drafted,Ready,Sendable,Needs} — leads/handlers.py
   • bmc{GetState,List*,AddHypothesis,Iterate,...}  — bmc/handlers.py
   ↓ asyncpg → graphar.vertex_api_key / vertex_lead / vertex_bmc_*
RisingWave PG (45.32.79.245:4566) + B2 + R2
```

### Operational status 2026-05-12 (P77 — customer journey 12/12 GREEN + full erasure on /api/account/delete)

| Customer-journey step | Result |
|---|---|
| 1. `POST /auth/v1/signup` | ✅ apiKey + orgDid + tenantName + AWS creds (~2.5s cold) |
| 2. `GET /api/plan` (free) | ✅ |
| 3a. `POST /cypher CREATE` | ✅ KV-backed Cypher engine, `accepted` |
| 3b. `POST /cypher MATCH` | ✅ `rows=1` round-trip |
| 4. `POST /mcp tools/list` | ✅ 8 tools |
| 5. `POST /mcp tools/call yata.graph.cypher` | ✅ same KV engine, MCP shape |
| 6. `PUT /storage/v1/object/...` | ✅ KV-backed content-addressed storage |
| 7. `POST /webhook/stripe` | ✅ signed `checkout.session.completed` ack |
| 8. `GET /api/plan` (flip free→starter) | ✅ KV-authoritative plan state |
| 9. `GET /api/usage` | ✅ `api_request.totalQty=3` (KV-mirrored meter) |
| 10. `GET /api/export` | ✅ apiKeys index from KV |
| 11. `POST /api/account/delete` | ✅ erasure tombstone |

**`yatabase-customer-journey.mjs` SUMMARY: 32 PASS · 0 SOFT · 0 FAIL · journey=GREEN** (+ P105 storage lifecycle, P106 /api/schema, P107 CORS preflight)

### Side surfaces (not in journey script)

| Surface | Result |
|---|---|
| `GET /xrpc/ai.gftd.apps.yata.leadList` | ✅ real leads (kyne.au, etc.) |
| `GET /xrpc/ai.gftd.apps.yata.leadSendable` | ✅ |
| `GET /xrpc/ai.gftd.apps.yata.leadNeedsEnrichment` | ✅ |
| Public surfaces `/`, `/studio`, `/docs`, `/comparison`, `/quickstart`, `/.well-known/*`, `/openapi.json` | ✅ |
| `/xrpc/ai.gftd.apps.yata.bmc*` (admin) | ⚠️ schema drift in this RW instance — not customer-facing |

### R2-primary storage tier (P73, 2026-05-12)

`src/storage-r2.ts` makes Cloudflare R2 the primary fallback ahead of
the legacy KV path. The `YATA_R2` binding (bucket `ai-gftd-cache`) is
keyed `yata/{orgDid}/{bucket}/{key}` for per-org isolation. No
practical size cap (vs. KV's 1 MiB).

Order of resolution for PUT/GET/HEAD/DELETE when the pod's NSID
handler returns 404:

1. `putR2Object` / `getR2Object` / `headR2Object` / `deleteR2Object`
   (P73) — durable, listable, native R2 API.
2. `putKvObject` / `getKvObject` etc. (P64) — 1 MiB cap; serves the
   legacy customer journey baseline.

LIST + BUCKETS endpoints merge results from both tiers so customers
see all objects in one response. `source` field reports `r2`,
`kv-fallback`, or `r2+kv-fallback`.

Signed URLs (`mintKvSignedUrl`) cover both tiers: the verifier
(`handlePublicAcl`) checks R2 first then KV. Anonymous GET on a
signed URL streams from R2 with `x-yatabase-storage-tier: r2-signed`.

Verified live:
- 5 MiB PUT → R2 (was previously 413 blocked at KV 1 MiB cap)
- SHA-256 of 5 MiB GET roundtrip matches original
- DELETE returns `{"source": "r2"}`, post-delete GET 404s
- Signed URL → anonymous GET streams 5 MiB from R2

### KV-backed graceful degradation (P63/P64/P70)

When the legacy `createKyselyDb` path is blocked by ADR-2605111200 or
the pod's XRPC handler hasn't shipped yet, the Worker falls back to
Workers KV namespace `YATABASE_AUTH_CACHE` (id
`fbb9ca096633432486a7daee53e8cfd9`) as the authoritative store for:

- `auth:v1:{sha256(apiKey)}` → bearer-auth resolution (24h TTL)
- `org_keys:v1:{orgDid}` → per-org apiKey index (for `/api/export`)
- `plan:v1:{orgDid}` → active plan tier (Stripe webhook writes here first)
- `usage:v1:{orgDid}:{metric}:{YYYY-MM-DD}` → daily meter counters (35d TTL)
- `erased:v1:{orgDid}` → erasure tombstone
- `cypher:v1:{orgDid}:nodes:{label}:{nodeId}` → Cypher CREATE node (P64)
- `cypher:v1:{orgDid}:labels:{label}` → label → [nodeId] index (P64); P70 also
  serves `MATCH (n:Label) [DETACH] DELETE n` by scanning the index then
  deleting each node + index entry
- `storage:v1:{orgDid}:obj:{bucket}/{key}` → storage object body (P64, 1 MiB cap);
  P70 adds `listKvObjects(prefix,limit)` (returns `{name,size,etag,contentType,updatedAt}`)
  + `deleteKvObject` (returns 200 / 404 based on presence)
- `storage:v1:{orgDid}:meta:{bucket}/{key}` → storage object metadata (P64)

**Performance**: signup `1-2s` cold / `200-600ms` warm; XRPC reads `200-1300ms`.

### Deployed artifacts

- `magatama-y4t4b4se` Worker — version `d92e5728-6c6e-4001-a8f2-ec7f7427c134` (P104)
- `ghcr.io/etzhayyim/pymagatama:p62-content-type-fix-amd64` — bpmn-dispatcher
- `ghcr.io/etzhayyim/lg-yatabase:0.0.9-amd64` — pod
- KV namespace `fbb9ca096633432486a7daee53e8cfd9` bound as `YATABASE_AUTH_CACHE`
- Vultr LoadBalancer `108.61.207.153` → nginx-ingress → bpmn-dispatcher → pod

### Remaining work (post-P64)

1. **Pod-side handlers** for `ai.gftd.apps.yata.{runCypher,putObject,getObject,deleteObject,listObject,signObject}` — when these land, the KV fallback in `cypher-kv.ts` + `storage-kv.ts` becomes transparently dormant (dispatcher returns non-404 and the fallback path is skipped). No Worker changes needed.
2. **BMC admin schema migration** (`30-graph/graph-schema/sql_migrations/20260512000000_bmc_lean_iteration.up.sql`) for the Studio left-pane health rollups.
3. **RisingWave durability recovery** (other teams' batch jobs jamming barrier coordinator) — independent of the customer-facing service which is now KV-backed at every step that customers touch.

### Shipped (P21, 2026-05-14): Outbox approval surface (closes the marketing/sales compliance loop)

Pod-side handlers + Worker admin routes + Studio page that lets an
operator review the drafts that marketing + sales LangGraph nodes write
to `vertex_email_outbox` at `status='queued-no-recipient'`. Without this
the P19 graphs effectively wrote to /dev/null — drafts piled up with no
human gate to flip them to `queued`.

| Surface | Where | Auth |
|---|---|---|
| `POST /xrpc/ai.gftd.apps.yata.outbox{List,Approve,Reject}` | lg-yatabase pod (`lg_yatabase/outbox/`) | `x-internal-trust` HMAC |
| `POST /api/outbox/{list,approve,reject}` | yatabase Worker (`src/outbox-forward.ts` + `src/app.ts`) | `x-yata-admin-key` (operator) |
| `/studio/admin/outbox` | Studio (`svelte/.../studio/admin/outbox/+page.svelte`) | `adminKey` store (`localStorage`) |

Flow: graph emits `queued-no-recipient` → operator opens
`/studio/admin/outbox` → pastes admin key → list pending drafts (filter
by status/kind) → expands row → fills `recipient_email` (`[[PARTNER_NAME]]`
placeholder detection blocks approve until edited) → Approve flips status
to `queued` → existing send worker picks up next tick. Reject sets
`status='rejected'` and stores the reason in `last_error`.

`StudioNav` shows an Admin section only when `adminKey` is set, with the
"Outbox review" link. `lib/stores.ts` adds an `adminKey` writable that
mirrors `apiKey` (localStorage-backed, never sent to non-admin surfaces).
`lib/api.ts` adds an `outbox` namespace using `x-yata-admin-key` header.

11 unit tests under `lg/tests/test_outbox.py` (combined 35 with P19);
covers list filter SQL shape, approve guard rails (missing vertex_id,
bad email format, status-already-flipped no-op), body override, reject
default reason. RW-const-LIMIT inlining verified in test.

Files: `lg/lg_yatabase/outbox/{__init__,models,repository,handlers}.py`
+ `lg/lg_yatabase/server.py` (register OUTBOX_ROUTER) +
`src/outbox-forward.ts` + `src/app.ts` (3 admin routes) +
`svelte/src/lib/stores.ts` (adminKey) + `svelte/src/lib/api.ts` (outbox
namespace) + `svelte/src/lib/components/StudioNav.svelte` (Admin section)
+ `svelte/src/routes/studio/admin/outbox/+page.svelte` + tests.

---

### Shipped (P20, 2026-05-14): Studio UI on @etzhayyim/design-system

SvelteKit + Svelte 5 + Tailwind + `@etzhayyim/design-system` Studio under
`svelte/`. Static-prerendered, fully client-rendered against the edge
Worker. Workers Assets `assets.directory = ./svelte/build` is already
configured, so `pnpm deploy` (root) chains `vite build → gftd deploy
--no-svelte` and the new routes go live at the next deploy.

Routes:
- `/studio` — Home (plan + identity + API key + quick wins)
- `/studio/cypher` — Cypher editor + result table + history (`POST /cypher`)
- `/studio/storage` — Bucket browser, drag-drop upload, signed URL mint
  (`/storage/v1/*`)
- `/studio/billing` — Plan card + 24h/30d usage bars + Stripe Customer Portal

Auth: `sk_live_yata_*` API key paste → `localStorage` → Bearer on every
call. `lib/stores.ts` validates via `/auth/v1/whoami` + caches identity
+ plan. Passkey / AT JWT integration deferred — Studio's target user is
a developer who already has an API key from `/auth/v1/signup`.

UI rules followed (per `40-engine/svelte/CLAUDE.md`):
- `@etzhayyim/design-system` components only (`Button`, `Input`,
  `Textarea`, `Card`, `Badge`, `NotificationBanner`, `EmptyState`,
  `ErrorText`, `Label`, `Skeleton`)
- Tailwind utilities only; no `<style>` blocks
- AppShell v2 token set (`--gv2-*` CSS custom properties) with
  light/dark switch via `html[data-theme=…]`

Files: `svelte/{package.json, svelte.config.js, vite.config.ts,
tailwind.config.js, postcss.config.js, tsconfig.json, src/app.{html,
css}, src/lib/{api,stores}.ts, src/lib/components/{SignInPanel,
StudioNav}.svelte, src/routes/{+layout.svelte, +layout.ts, +page.svelte,
studio/+layout.svelte, studio/+layout.ts, studio/+page.svelte,
studio/{cypher,storage,billing}/+page.svelte}}` + `svelte/README.md`.

Deploy: `pnpm deploy` from `60-apps/ai-gftd-project-yatabase/`
(see `svelte/README.md` for the dev-against-prod workflow via
`VITE_YATABASE_ORIGIN`).

---

### Shipped (P19, 2026-05-14): marketing + sales LangGraph node logic

| Graph | What landed | Cron | Compliance gate |
|---|---|---|---|
| `marketing` (182 → 280 lines) | `_discover_leads` reads `vertex_lead` WHERE outreach_status IN ('new','drafted'). `_enrich_lead` infers tech_stack from signal + classifies ICP segment (templates.classify_segment). `_score_lead` calls LLM via `graphs._llm.score_lead` with deterministic fallback. `_route_by_score` handoffs ≥80, drops <50. `_draft_outreach` builds 3-touch deterministic sequence per ICP via `templates.marketing_touch`. `_schedule_send` INSERTs into `vertex_email_outbox` status=`queued-no-recipient` + flips lead to `outreach_status='drafted'`. | `0 */6 * * *` UTC | All marketing outbox rows land at `queued-no-recipient`; reviewer fills recipient + flips to `queued` before send (CAN-SPAM 16 CFR 316.5 / GDPR Art 6 / 改正個人情報保護法 §17). |
| `sales` (189 → 320 lines) | `_load_org_state` reads vertex_billing_org_plan + vertex_billing_event (24h+30d aggregates) + vertex_audit_log (5xx incidents) + vertex_email_outbox (last touch). `_compute_health` derives 0-100 from momentum + incidents + plan tier. `_decide_action` runs deterministic policy with optional LLM augmentation via `graphs._llm.decide_sales_action`. `_execute_action` writes vertex_email_outbox row with appropriate `sales-{kind}` from `templates.sales_touch`; `escalate_human` emits explicit `sales-escalate-human` marker row. | `15 * * * *` UTC | Every sales outbox row lands at `queued-no-recipient`; reviewer approves before send. `do_nothing` never touches the outbox (audit-clean). |

**Helper modules added**:
- `lg_yatabase/templates.py` — JP/EN deterministic 3-touch marketing sequences + 4 sales templates + ICP segment classifier. Footer always includes etzhayyim/Gftd Japan operator/vendor split + unsubscribe.
- `lg_yatabase/graphs/_llm.py` — guarded LLM caller (`GFTD_LLM_URL` / `GFTD_LLM_API_KEY`). Returns deterministic fallback on missing key / network error / non-JSON response so cron stays green.

**Test coverage**: `lg/tests/test_marketing_sales_nodes.py` — 24 unit tests pass. Pure-function nodes tested directly; DB-touching nodes use monkey-patched fetch/fetchrow/fetchval/execute. asyncpg + langgraph stubbed in conftest for local dev.

**Deterministic policy table (sales `_decide_action`)**:
- incident_count_24h > 0 → `do_nothing` (defer to chikada triage)
- last_touch < 7d → `do_nothing` (per-org rate-limit)
- api_24h = 0 AND no prior touch → `send_onboarding`
- 0 < api_24h < 50 AND plan=free → `send_usage_recap`
- plan=free AND api_24h > 800 → `send_upgrade`
- plan=starter AND api_24h > 80k → `send_upgrade` (developer)
- plan in (starter|developer|enterprise) AND api_24h=0 → `escalate_human`
- else → `do_nothing`

**LLM augmentation**: when `GFTD_LLM_API_KEY` is set the LLM can override the deterministic choice (still bounded to the allowed enum); when invalid or unset the deterministic decision wins. `notes` field carries the source marker so audit can distinguish.

**Cron behaviour after this ship**: both graphs idempotent — re-running with no new leads / no qualifying signal is a cheap no-op. Marketing emits at most `_DRAFT_CAP * 3 = 75` outbox rows per tick. Sales emits at most one outbox row per org_did per tick.

## Forbidden

- Direct B2 / Vultr OS SigV4 from this Worker. All PUT/GET/DELETE go through LangServer in `mitama-yata-pool` which owns the SigV4 credentials in the `yata-storage-creds` Secret.
- `sdk.pds.dispatch({ type: "com.atproto.repo.createRecord", ... })` for `ai.gftd.apps.yata.*` — domain writes go to Hyperdrive via LangServer (ADR-0036).
- New custom HTTP endpoints outside the surfaces table above. Add via XRPC + lexicon instead.

## Deploy

```bash
cd 60-apps/ai-gftd-project-yatabase
wrangler secret put DISPATCHER_INTERNAL_SECRET  # shared with K8s bpmn-dispatcher-auth
./70-tools/scripts/yatabase-deploy.sh           # wraps `gftd deploy` and re-attaches cron triggers

# lg-yatabase pod (host owns vertex_api_key / vertex_lead / vertex_bmc_* writes)
cd lg
docker buildx build --platform linux/amd64 --builder multiarch-builder \
  --build-context py=../../../20-actors/magatama/py \
  -t ghcr.io/etzhayyim/lg-yatabase:<tag> --push .
kubectl -n mitama-udf set image deployment/lg-yatabase lg-yatabase=ghcr.io/etzhayyim/lg-yatabase:<tag>

# bpmn-dispatcher (proxies yata.* XRPC NSIDs to lg-yatabase pod)
cd 20-actors/magatama/py
docker buildx build --platform linux/amd64 --builder multiarch-builder \
  -t ghcr.io/etzhayyim/pymagatama:<tag> --push .
kubectl -n mitama-udf set image deployment/bpmn-dispatcher dispatcher=ghcr.io/etzhayyim/pymagatama:<tag>
```

## Smoke

```bash
curl https://yatabase.etzhayyim.com/health
curl https://yatabase.etzhayyim.com/_app/meta
curl -H "Authorization: Bearer sk_live_yata_xxx" \
     https://yatabase.etzhayyim.com/xrpc/ai.gftd.apps.yata.coverage
curl -X PUT --data-binary @small.png \
     -H "Authorization: Bearer sk_live_yata_xxx" \
     https://yatabase.etzhayyim.com/storage/v1/object/test/small.png
```
