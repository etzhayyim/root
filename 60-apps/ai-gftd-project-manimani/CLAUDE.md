# manimani.gftd.ai — personal knowledge router (LangGraph user-intake routing)

Authoritative: ADR-2605080800 + ADR-2605080600 (LangGraph Server) + ADR-2604282300 (CF Worker = edge facade).

## Layer

L3 Dispatcher (CF Worker, edge). State-less. All compute lives in
`mitama-manimani-pool` LangGraph Server (Granian) which calls Anthropic
API (or vLLM Gemma4 on RunPod) via `pymagatama.llm.call_tier`, and writes
intake / project / artifact rows to RisingWave directly via Hyperdrive.

## Surfaces

| Path | Purpose |
|---|---|
| `/xrpc/ai.gftd.apps.manimani.ingest` | procedure — submit text/url/file_ref/email intake, returns `runId` |
| `/xrpc/ai.gftd.apps.manimani.classify` | procedure — re-classify an intake into a different project |
| `/xrpc/ai.gftd.apps.manimani.process` | procedure — re-process an intake with a different model / kind |
| `/xrpc/ai.gftd.apps.manimani.resumeRun` | procedure — resume a HITL-paused run with `decision: approve|reject|reassign` (Phase 4) |
| `/xrpc/ai.gftd.apps.manimani.getProject` | query — fetch project + recent artifacts |
| `/xrpc/ai.gftd.apps.manimani.listProjects` | query — list active projects in actor scope |
| `/xrpc/ai.gftd.apps.manimani.coverage` | query — counters + 24h delta + unrouted count |
| `/health`, `/_app/meta` | edge probe |

## Project kinds

| kind | Processor | LLM tier | Output (`vertex_manimani_artifact.artifact_kind`) |
|---|---|---|---|
| `knowledge` | `extract_facts` — fact extraction + claim/source split | balanced | `facts_jsonl` |
| `task` | `expand_todo` — action item + due/owner inference | balanced | `todos_jsonl` |
| `memo` | `summarize` — 280-char summary + tag | fast | `summary_text` |
| `unsorted` | `defer_for_user_review` — no LLM call, raw passthrough | — | `raw_passthrough` |

## Auth

- `Bearer sk_live_*` — gftd API key (PDS verifies via `vertex_api_key`)
- `Bearer <ES256-JWT>` — AT Protocol session JWT
- Worker forwards Authorization to PDS service binding
  `/_internal/resolve-auth`, gets `{ did, orgDid, activeDid, productScope }`,
  then HMAC-signs forward to bpmn-dispatcher.

## Forwarding model

```
Client → CF Worker (manimani.gftd.ai)
   ↓ auth middleware → PDS_SERVICE binding /_internal/resolve-auth
   ↓ resolved { did, orgDid, activeDid, productScope }
   ↓ POST https://dispatcher.gftd.ai/xrpc/ai.gftd.apps.manimani.{method}
      headers: x-internal-trust=<HMAC>, x-gftd-{org,actor}-did, x-gftd-trace-id
bpmn-dispatcher (K8s ClusterIP)
   ↓ NSID prefix routing (ai.gftd.apps.manimani.* → langgraph backend)
manimani-langgraph (mitama-manimani-pool, Granian :8000)
   ↓ POST /runs — start StateGraph
   ↓ Pregel: parse → classify → route → {extract_facts | expand_todo | summarize | defer} → persist → audit
   → Anthropic / vLLM (LLM tier resolves via pymagatama.llm)
   → RisingWave Hyperdrive INSERT (vertex_manimani_intake/project/artifact/run + edge_manimani_belongs_to)
```

## Forbidden

- Direct LLM API calls from this CF Worker. LLM only known to LangGraph Server pod env.
- Direct Hyperdrive INSERT from this CF Worker. Domain writes go from LangGraph nodes only (ADR-0036).
- `sdk.pds.dispatch({ type: "com.atproto.repo.createRecord", ... })` for `ai.gftd.apps.manimani.*` — non-federable, default block.
- AT Repo emit (federable) of intake / project / artifact rows. Social derive is opt-in only via explicit `pds.dispatch({type:"app.bsky.feed.post"})` from a downstream actor.
- Adding new XRPC endpoints outside the 6 lexicons in `00-contracts/lexicons/ai/gftd/apps/manimani/`. New methods require an ADR addendum + lexicon PR.
- Hardcoded LLM model names in dispatcher routing. Use `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL` SSoT (LLM Model SSoT convention).

## Deploy

```bash
cd 60-apps/ai-gftd-project-manimani
wrangler secret put DISPATCHER_INTERNAL_SECRET  # shared with K8s bpmn-dispatcher-auth
gftd deploy --no-svelte
```

## Smoke

```bash
# 1. Edge health (no auth)
curl https://manimani.gftd.ai/health
curl https://manimani.gftd.ai/_app/meta

# 2. Submit a text intake (Bearer required)
curl -X POST https://manimani.gftd.ai/xrpc/ai.gftd.apps.manimani.ingest \
  -H "Authorization: Bearer sk_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceKind": "text",
    "rawText": "TODO: review the Q3 OKR draft by Friday and ping Alice",
    "lang": "ja"
  }'
# → { "runId": "...", "intakeId": "...", "status": "running", "estimatedSeconds": 3 }

# 3. List projects (auto-emerged on first ingest)
curl https://manimani.gftd.ai/xrpc/ai.gftd.apps.manimani.listProjects \
  -H "Authorization: Bearer sk_live_xxxxx"

# 4. Re-classify an intake
curl -X POST https://manimani.gftd.ai/xrpc/ai.gftd.apps.manimani.classify \
  -H "Authorization: Bearer sk_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "intakeId": "...",
    "newProject": { "slug": "okr-q3", "title": "OKR Q3", "kind": "task" }
  }'

# 5. Coverage snapshot
curl 'https://manimani.gftd.ai/xrpc/ai.gftd.apps.manimani.coverage?windowDays=7' \
  -H "Authorization: Bearer sk_live_xxxxx"
```
