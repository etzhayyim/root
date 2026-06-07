---
id: adr-2605141600-mangaka-phase-c-activation-and-emotion-loop
title: "mangaka Phase C activation + Hume-driven per-node emotion loop"
status: active
doc_type: adr
topic: mangaka-phase-c-emotion-loop
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - mangaka compose_scene_3d Phase C activation (data-driven topology row, v2)
  - in-cluster MCP NSID override pattern (MCP_NSID_OVERRIDE_* env)
  - Hume image-head persist → distil → consume loop for emotionAlignment scoring
  - per-node `_emotion` attachment for ai-image + panel nodes in the Genko document graph
  - pymagatama resolver enhancements (make_llm_vision_node, DMN condition router)
priority: 8.5
axis: orchestration
weight: 0.85
priority_note: "Closes the 6 Phase C blockers + sub-blockers from ADR-2605141200 §P6 and wires the emotion loop end-to-end (corpus persistence → centroid distillation → per-node attachment → Canvas display)."
depends_on:
  - adr-2605141200-mangaka-3d-scene-pregel-kami-sdk
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2604261100-rego-dmn-policy-decision-layers
  - adr-2604300135-hume-distillation-artifact-persistence
related:
  - adr-0044-kotoba-udf-language-strategy
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
supersedes: []
superseded_by: []
---

# Context

ADR-2605141200 (mangaka 3D scene Pregel + kami SDK) established the
9-super-step `compose_scene_3d` LangGraph + the `kami-mangaka-scene`
Rust crate, with a clear P0–P6 roadmap. By 2026-05-14 P0–P4 were in
production and P5 (wasm-pack interactive preview) was live at
`https://mangaka.etzhayyim.com/scene-3d-preview.htm`. P6 — the migration to a
fully data-driven `kind='topology'` assistant row per
ADR-2605082000 — was scaffolded but blocked behind a board of six
items that this ADR closes:

| # | Blocker | Closing artefact |
|---|---|---|
| 1   | LLM prompt inlining (text)                                 | `compose_scene_3d.topology.yaml` inlines all three LLM `args.system` / `args.user_template` blocks; `tests/test_compose_scene_3d_prompts.py` guards drift against the Python source constants. |
| 1b  | Vision LLM resolver (multimodal critic node)               | `pymagatama.langgraph_node_resolvers.make_llm_vision_node` + `pymagatama.llm.call_tier_vision_json` resolve `kind="llm_vision"` against B2 blob fetch + OpenAI-compatible vision endpoint; `blob_fetcher` callback keeps pymagatama storage-agnostic. |
| 2   | Cinematography + critique post-processor MCP tools         | `com.etzhayyim.mangaka.tools.validateCameraPlan` and `.aggregateCritique` in `lg_mangaka.tools`, with topology nodes between the LLM stages and the downstream simulate / refinement edges. Phase A in-tree path re-uses the same tools (single SSoT). |
| 3   | DMN refinement policy seed                                 | `00-contracts/dmn/com/etzhayyim/policies/mangaka/composeScene3dRefinement.dmn` + alembic seed into `vertex_dmn_model`. Drift between the DMN rules table and the Phase A Python predicate guarded by `tests/test_compose_scene_3d_refinement_dmn.py`. |
| 3b  | DMN evaluator in `_compile_topology`                       | `pymagatama.langgraph_node_resolvers.make_dmn_condition_router` + `_resolve_dmn_ref` + the FEEL-lite `_eval_dmn_input_entry` (supports `-`, `< N`, `<= N`, `> N`, `>= N`, `== N`, bare literals, and named-input refs like `< maxIter`). |
| 4   | MCP tool serving endpoint                                  | `lg_mangaka.server` exposes `POST /xrpc/com.etzhayyim.mcp.message` (JSON-RPC tools/call envelope) on top of the existing `/xrpc/{nsid}` direct route. In-cluster Pregel short-circuits via the new `MCP_NSID_OVERRIDE_<prefix>` env pattern in the resolver. |

Beyond the Phase C closure, the same session wired an end-to-end
Hume-driven emotion loop. The persistence side
(`tool_persist_hume_emotion_observation` writing `humeObservation.v1`
rows to `vertex_vector_emotion_signal`) was already shipped under P4;
this ADR adds the consumer side and the per-node attachment surface
the user can see in Genko canvas today.

# Decision

## 1. Phase C activation — single alembic flip

`r_20260514170000_topology_compose_scene_3d` is the canonical Phase C
flip: it INSERTs the v2 topology assistant + every per-node binding
row, then bumps `vertex_langgraph_deployment` so the bpmn-dispatcher
watcher re-resolves the NSID. `downgrade()` reverts to the Phase A
py_factory shape. Behaviour is bit-identical across paths — the Phase
A in-tree `_step_*` nodes already call the same `lg_mangaka.tools.*`
pure functions the topology nodes will resolve to.

## 2. MCP serving — pod IS the endpoint

The lg-mangaka pod (`lg_mangaka.server`) is the canonical MCP serving
endpoint for `com.etzhayyim.mangaka.tools.*`. Two routes converge on
`_dispatch_mcp_tool → _TOOL_NSID_TO_HANDLER → lg_mangaka.tools.*`:

* `POST /xrpc/{nsid}` — direct (used by the in-tree Phase A path and
  by direct XRPC callers).
* `POST /xrpc/com.etzhayyim.mcp.message` — JSON-RPC 2.0 `tools/call`
  envelope (used by Phase C topology and external MCP clients).

The in-cluster Pregel short-circuits the external trip through
`mangaka.etzhayyim.com` via the new
`MCP_NSID_OVERRIDE_<key>=<base_url>` env var pattern in
`pymagatama.langgraph_node_resolvers._resolve_mcp_nsid`. `<key>` is the
NSID prefix with dots replaced by underscores; segment-boundary match
prevents substring collisions; longest-prefix wins on conflict.
`lg-mangaka-pool` Helm values emit
`MCP_NSID_OVERRIDE_ai_etzhayyim_apps_mangaka_tools=http://localhost:8000`
so the topology Pregel never leaves the container for tool dispatch.

**External MCP clients** still resolve `actor_host = mangaka.etzhayyim.com`
from the registry and hit the CF Worker (SvelteKit edge). Forwarding
that path through to the pod is a deferred residual — Phase C
activation does not depend on it.

## 3. Hume corpus → distilled student model → consumer loop

The compose_scene_3d Pregel writes one `humeObservation.v1` row per
candidate render into `vertex_vector_emotion_signal` (provider =
`Hume AI`, model_id = `hume-image-head`, modality = `image`,
`raw_json` = `{input: {imageFeatures}, labels: {targetMood, targetFamily},
primary, topEmotions, humeScore, ...}`). Rejected candidates are
kept as negative training examples (`selected: false`).

`lg_mangaka.hume_distill` consumes the corpus:

1. `fetch_observations(rw_url, *, limit, since)` — async psycopg query.
2. `parse_observation_row(raw_json_str)` — rebinds the persisted shape
   so `pymagatama.primitives.hume_image_head.train_image_centroid`
   reads teacher distribution under `labels.primary` /
   `labels.topEmotions` and keeps author intent under `labels.author`.
3. `run_distillation(observations, *, min_rows=10)` — calls
   `train_image_centroid`, emits `{model, metrics{rows, familyCoverage,
   primaryCoverage}}`. Refuses tiny corpora (`DistillationError`).

`scripts/distill_hume_emotion.py` is the CLI runner. The trained
`visual_centroid_v1` model JSON is loaded back into the consumer side
via `MANGAKA_HUME_STUDENT_MODEL=<path>` env on the lg-mangaka pod;
`lg_mangaka.graphs.score_emotion._load_student_model` accepts both the
bare model dict and the `{model, metrics}` wrapper. The
`lg_mangaka.hume_emotion.score_emotion_alignment(..., model=<dict>)`
entry point flows the dict down to
`pymagatama.primitives.hume_image_head.predict_image_emotion`, so
both `compose_scene_3d` (for the `emotionAlignment` axis) and
`score_emotion` (for per-node attachment) automatically pick up the
distilled centroid when present — heuristic fallback otherwise.

## 4. Per-node emotion attachment in the Genko graph

`com.etzhayyim.mangaka.scoreEmotion` is a 4-step Pregel in
`lg_mangaka.graphs.score_emotion`:

| Step               | Output |
|---|---|
| `load_target`      | SELECT `vertex_mangaka kind='document'`, resolve ai-image nodes (single via `imageNid` or batch), bind each to its parent panel via `_panelChildren`. |
| `fetch_and_score`  | GET each blob via `_BLOB_BASE/blob/{cid}?did=anonymous`, run `predict_image_emotion` with the loaded student model when available. |
| `aggregate`        | For each panel with scored children, the highest `primary.score` wins; ties broken by sum of `topEmotions` scores. Emits `sourceCount` + `winningChild`. |
| `persist`          | Patch each ai-image / panel node's `data._emotion`, DELETE-then-INSERT the document row. |

Emotion record shape:

```
{
  "primary":      {"name": str, "score": float},
  "topEmotions":  [{"name": str, "score": float}, ...],
  "imageFeatures": {luminance, r_weight, g_weight, b_weight, saturation, contrast},
  "algorithm":    "visual_heuristic_v1" | "visual_centroid_v1",
  "scoredAt":     "<UTC ISO 8601>",
  "sourceCount":  int,           // 1 for ai-image, #scored children for panel
  "winningChild": str | null,    // panel-only, identifies the dominant child
}
```

## 5. Canvas display + side-panel interaction

`kami-engine-sdk/.../Canvas.svelte` renders a small **emotion chip**
(mood-coloured 1.5 px border, name + score pill, tooltip with
algorithm + scoredAt + sourceCount) in the top-left of every ai-image
and panel node that carries `_emotion.primary`. The chip is
`pointer-events: none` so it never blocks overlay drag/resize.

`kami-engine-sdk/.../Genko.svelte` adds a side-panel "感情" section for
both ai-image and panel selectables: primary name + score +
algorithm + top-4 emotions, plus a 🎭 採点 button that fires
`com.etzhayyim.mangaka.scoreEmotion` (single mode for ai-image, batch
mode for panel — the panel then picks its own `panelEmotion[nid]` out
of the response).

# Consequences

* Phase C topology flip is a single alembic revision now, not a
  multi-step manual procedure. Phase A behaviour is preserved as the
  rollback target.
* `pymagatama.langgraph_node_resolvers` gains two new node kinds
  (`llm_vision`, dispatched via `make_llm_vision_node`) and one new
  conditional-edge scheme (`condition_ref: dmn:<key>@<version>`,
  dispatched via `make_dmn_condition_router`). Both are additive —
  existing `mcp_tool` / `llm` / `sql_udf` / `py_ext_udf` / `foreach`
  paths are unchanged.
* The MCP NSID override pattern generalises beyond mangaka: any future
  actor whose Pregel runs co-located with the MCP serving endpoint can
  set `MCP_NSID_OVERRIDE_<prefix>` to short-circuit the registry
  lookup. The pattern is documented in the resolver docstring; no
  ADR-specific opt-in.
* The Hume student model is hot-swappable via
  `MANGAKA_HUME_STUDENT_MODEL` — no code path change is required
  when a new corpus produces a better centroid. Cold-start lookup
  happens once at module load.
* External MCP clients calling `actor_host = mangaka.etzhayyim.com` still
  404 because the CF Worker is a pure SvelteKit edge with no MCP
  forwarder. This is intentional for the current cut and tracked in
  `[[migrations]] mangaka-external-mcp-forwarding-2026-05-14` for
  later closure (either Cloudflare Tunnel to the pod or
  `actor_host = atproto.etzhayyim.com` flip).
* `_panelChildren` is now a load-bearing field in the Genko document
  model — without it, the `aggregate` step can't roll ai-image
  emotions up to their parent panel. Existing docs without
  `_panelChildren` get per-ai-image chips but no panel aggregate
  (graceful degradation).

# Alternatives considered

## A. Per-tool MCP serving endpoint registration

Each `vertex_mcp_tool_def` row could carry an `endpoint_url` column
that overrides `actor_host` for that specific NSID. Rejected because
it pushes per-deployment topology details into the registry instead
of the deployment env, requiring DB writes on every pod restart and
breaking the "deployment = one env block" invariant.

## B. wRPC service-binding from CF Worker to pod

Bypass the registry entirely by having the mangaka Worker hold a
direct service binding to the lg-mangaka pod. Rejected because the
pod is in-cluster (ClusterIP) and CF Workers can't service-bind
across the public boundary without Cloudflare Tunnel. The override
pattern achieves the same routing collapse without new infra.

## C. Server-side emotion auto-emit at compose_scene_3d persist

Patch the source panel record's `props.emotion` from `_step_persist`
in the compose_scene_3d Pregel directly, side-stepping the need to
call `scoreEmotion` explicitly. Rejected because compose_scene_3d
operates on `vertex_mangaka kind='panel'` records (a different graph
entity than Genko document nodes); dual-writing both surfaces
introduces drift risk. The canonical source is
`vertex_vector_emotion_signal`; downstream consumers JOIN as
needed. Genko documents stay the source of truth for
in-canvas presentation.

## D. ML-grade centroid trainer (sklearn / pytorch)

Use a real classifier instead of the stdlib-only
`train_image_centroid`. Rejected for the same reason ADR-0044
prefers SQL UDFs / embedded Rust for rule-based work: the centroid is
trained on six floats, no per-row tensor compute, and the heuristic
fallback is already useful. The student model is hot-swappable, so
upgrading the trainer later is a drop-in replacement of the JSON
artefact — no graph changes required.

# Roadmap

| Phase | Scope | Status |
|---|---|---|
| Phase C — alembic flip      | `r_20260514170000_topology_compose_scene_3d` applied in dev DB, watcher re-resolves NSID, smoke test compose_scene_3d invocation against the v2 row | ✅ ready (waiting on dev DB apply) |
| Hume distillation cron     | Schedule `scripts/distill_hume_emotion.py` to run nightly, persist the model JSON to a stable path on the pod, watch corpus growth | ⏳ |
| External MCP forwarding    | Either CF Worker `/xrpc/com.etzhayyim.mcp.message` → pod via tunnel, OR flip `actor_host = atproto.etzhayyim.com` and let the existing MCP adapter forward | ⏳ |
| `_panelChildren` backfill  | Walk existing Genko documents that predate this ADR and infer panel→ai-image children from canvas geometry, so historical docs gain panel emotion aggregates | ⏳ |

# References

- ADR-2605141200 — mangaka 3D scene Pregel + kami-mangaka-scene SDK (parent)
- ADR-2605082000 — LangGraph graph definition as data
- ADR-2605111200 — CF Worker edge-only, no RW connection
- ADR-2604261100 — Rego + DMN as decision-table SSoT
- ADR-2604300135 — Hume distillation artefact persistence
- `00-contracts/dmn/com/etzhayyim/policies/mangaka/composeScene3dRefinement.dmn`
- `60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/graphs/{compose_scene_3d,score_emotion}.py`
- `60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/{hume_distill,hume_emotion}.py`
- `50-infra/vultr/lg-mangaka-pool/values.yaml` (mcpOverrides)
