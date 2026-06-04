---
id: adr-2605141500-shinshi-review-generation-quality-loop
title: "ADR-2605141500: Shinshi Review Generation Quality Loop"
status: active
doc_type: adr
topic: shinshi-review-generation-quality-loop
authoritative: true
last_verified: 2026-05-14
priority: 7.4
axis: architecture
weight: 0.72
priority_note: "Makes Shinshi generation review a first-class MCP/XRPC graph with deterministic gates and optional VLM aesthetic scoring."
authoritative_for:
  - Shinshi reviewGenerationBatch MCP/XRPC contract
  - Deterministic generated scene record quality scoring
  - Optional aesthetic/VLM scoring as a downgrade-only review layer
  - minScore threshold semantics for generated post review
depends_on:
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
related:
  - adr-2605080200-pydantic-l6-validation-contract
  - adr-2605091900-yoro-flower-fruit-lifecycle
  - adr-2605102100-keiei-llm-vultr-cpu-inference
amends:
  - adr-2605082200-langgraph-single-task-and-row-driven-runtime
supersedes: []
superseded_by: []
---

# ADR-2605141500: Shinshi Review Generation Quality Loop

**Status**: accepted
**Date**: 2026-05-14
**Deciders**: Jun Kawasaki

## Context

Shinshi scene generation already had render-time checks for empty PNGs,
unexpected dimensions, low resolution, short render time, and publishing
failures. The remaining gap was batch-level review after records land in the
repo projection:

- operators need a tool to inspect recent generated posts per model DID or slug;
- the appview and MCP surfaces need a typed contract for review output;
- deterministic record checks must be cheap and available without a VLM;
- visual or aesthetic judgment should be possible, but optional and non-blocking.

The existing LangGraph server for Shinshi is the correct runtime boundary:
it already exposes MCP and XRPC compatibility, reads RisingWave projections,
and owns the generation graphs.

## Decision

### D1. Add `reviewGenerationBatch` as the canonical review tool

The canonical NSID is:

```text
com.etzhayyim.apps.shinshi.reviewGenerationBatch
```

It is exposed through:

- `00-contracts/lexicons/com/etzhayyim/apps/shinshi/reviewGenerationBatch.json`
- `lg_shinshi.server` MCP `tools/list` and `tools/call`
- `/xrpc/com.etzhayyim.apps.shinshi.reviewGenerationBatch`
- generated Svelte contract `svelte/src/lib/contracts/shinshi-mcp.ts`

Inputs:

- `did` or `slug` plus `appDid`
- `limit`
- `minScore`
- `includeAesthetic`
- `aestheticLimit`

Outputs include totals, per-review score/decision/reasons, optional aesthetic
score/reasons, and an improvement plan.

### D2. Deterministic scoring is always first

`lg_shinshi.quality.score_scene_record` remains the base review layer. It
checks text length, image embed presence, blob CID, MIME type, alt text, and
expected self-labels.

The deterministic decision thresholds are:

```text
score >= 0.86 -> accept
score >= 0.60 -> retry
else          -> quarantine
```

`minScore` is applied after deterministic scoring. If a record is otherwise
accepted but below the requested threshold, it becomes `retry` with
`below_min_score`.

### D3. Aesthetic scoring is optional and downgrade-only

`includeAesthetic=true` routes through an additional `aesthetic_review` graph
node. The graph calls an OpenAI-compatible VLM endpoint configured by:

```text
SHINSHI_AESTHETIC_REVIEW_URL
SHINSHI_VLM_REVIEW_URL
SHINSHI_AESTHETIC_REVIEW_MODEL
SHINSHI_AESTHETIC_REVIEW_API_KEY
```

The VLM response is expected to be compact JSON:

```json
{"score": 0.0, "reasons": []}
```

`merge_aesthetic_score` can only downgrade records already marked `accept`.
It does not upgrade deterministic `retry` or `quarantine` records. This keeps
broken publishing records under deterministic control and prevents aesthetic
review from masking structural failures.

### D4. Missing aesthetic endpoint is a visible review reason

When aesthetic review is requested but unavailable, the graph records
`aesthetic_review_unavailable` or the specific endpoint failure reason. It
does not fail the whole review batch. The improvement plan tells operators to
configure the VLM endpoint before relying on visual quality scoring.

### D5. Test and contract gates

The closing verification set for this decision is:

```text
node scripts/generate-shinshi-mcp-contract.mjs
node scripts/check-api-surface.mjs
npm run check
tests/test_smoke.py
```

At acceptance, the Python smoke suite passed with 16 tests and Svelte reported
0 errors with the existing warnings.

### D6. Gemma 4 E4B vision is the active aesthetic reviewer

As of 2026-05-14, Shinshi aesthetic review uses `google/gemma-4-E4B-it`
through the k8s-local keiei LLM service:

```text
http://keiei-llm-e4b.keiei-llm.svc.cluster.local:8080/v1/chat/completions
```

The `lg-shinshi` server is the runtime boundary for the review graph. The
SvelteKit edge remains thin: it calls the typed MCP/XRPC surface and does not
open DB connections, Hyperdrive connections, or direct model connections.

For Gemma 4 E4B under `llama.cpp`, multimodal input is only valid when the
server is started with the matching mmproj file:

```text
--model /model/gemma-4-E4B-it-Q4_K_M.gguf
--mmproj /model/mmproj-gemma-4-E4B-it-F16.gguf
--image-max-tokens 280
```

Without `--mmproj`, the OpenAI-compatible endpoint accepts text but rejects
image input. The review graph therefore treats `gemma-4` models as `vision`
mode, sends image content before text content, and passes
`chat_template_kwargs.enable_thinking=false` for deterministic compact JSON.

The active deployment settings are:

```text
SHINSHI_AESTHETIC_REVIEW_MODE=vision
SHINSHI_AESTHETIC_REVIEW_TIMEOUT_SEC=90
SHINSHI_AESTHETIC_REVIEW_CACHE_ENABLED=true
SHINSHI_AESTHETIC_REVIEW_MODEL=gemma-4-E4B-it
```

### D7. Aesthetic review results are cached in RisingWave

Live aesthetic calls are expensive enough to cache, but not authoritative
enough to replace deterministic scoring. `lg-shinshi` stores successful
aesthetic review outputs in:

```text
vertex_shinshi_aesthetic_review
```

The cache key is derived from post URI, image URL, review mode, and model.
Changing model or mode intentionally misses the cache. Output now includes:

- `aestheticReviewMode`
- `aestheticReviewModel`
- `aestheticReviewSource` (`live` or `cache`)
- `aestheticReviewLatencyMs`

The cache was introduced by migration:

```text
20260514193000_vertex_shinshi_aesthetic_review_cache
```

Live verification on 2026-05-14 showed the first public review call returning
`aestheticReviewSource="live"` and the second returning
`aestheticReviewSource="cache"` with request latency reduced from seconds to
approximately 100 ms.

## Consequences

- Shinshi now has a closed review loop for generated records without requiring
  a model call by default.
- Operators can request stronger visual inspection by setting
  `includeAesthetic=true`, bounded by `aestheticLimit`.
- Generated contract drift is caught by the appview API surface check.
- Future VLM providers can be swapped behind the environment variable without
  changing the public MCP/XRPC contract.
- Gemma 4 E4B vision review now works on the edge-only architecture because
  the model call stays inside k8s and SvelteKit only observes the typed
  MCP/XRPC response.
- Cached aesthetic review prevents repeated page refreshes or operator checks
  from repeatedly spending a live multimodal model call for the same post,
  model, and review mode.

## Alternatives Considered

### Always run VLM review

Rejected. It would add latency and provider dependency to a read-side quality
tool that must still work during model endpoint outages.

### Let aesthetic scoring upgrade records

Rejected. A good-looking image must not override missing blob references,
wrong MIME type, missing labels, or other publishing defects.

### Keep review as a local script

Rejected. MCP/XRPC exposure is required so appview, operators, and future
agents can use the same review contract.

## References

- Commit `8e595f6da6a`: `feat(shinshi+legal-corpus): reviewGenerationBatch quality loop + LangGraph wiring`
- Commit `f4d5e741653`: `feat(shinshi): add optional aesthetic review gate`
- `60-apps/etzhayyim-project-shinshi/lg/lg_shinshi/graphs/review_generation_batch.py`
- `60-apps/etzhayyim-project-shinshi/lg/lg_shinshi/quality.py`
- `00-contracts/lexicons/com/etzhayyim/apps/shinshi/reviewGenerationBatch.json`
- `30-graph/graph-schema/sql_migrations/20260514193000_vertex_shinshi_aesthetic_review_cache.up.sql`
- `50-infra/vultr/keiei-llm-pool/values.yaml`
