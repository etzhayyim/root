---
id: adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
title: "ADR-2605180900: UNSPSC + ISIC LangGraph Pregel fleet — langserver-resident, exposed as Actor / Lexicon / XRPC / MCP, Haiku-routed bulk"
status: in-progress
doc_type: adr
topic: unispsc-isic-langserver
authoritative: true
last_verified: 2026-05-18
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "Operationalizes the 18,343-agent UNSPSC fleet (ADR-2605171300) and authorizes a parallel ISIC Rev. 4 fleet (~428 agents). Establishes one langserver per taxonomy with lazy importlib registry, four call surfaces (HTTP / Kotodama actor / XRPC / MCP), and a Haiku-default model policy with confidence-based Sonnet escalation."
authoritative_for:
  - per-class agent fleet operational pattern (langserver-resident, lazy registry, LRU)
  - four-call-surface contract (direct HTTP, Actor, XRPC, MCP)
  - model routing policy (Haiku default, Sonnet escalation, embedding pre-filter)
  - ISIC Rev. 4 fleet generation pattern (Haiku Batch API, ast.parse validation)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - 2605171300
  - adr-2605172000-etzhayyim-kotoba-substrate
related:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
supersedes: []
superseded_by: []
---

# ADR-2605180900: UNSPSC + ISIC LangGraph Pregel fleet — langserver-resident, four call surfaces, Haiku-routed

**Status**: in-progress (7 of 9 phases complete; 1 gated, 1 pending)
**Date**: 2026-05-18
**Deciders**: Jun Kawasaki

## Implementation status (2026-05-18 session close)

| Phase | Title                                    | Status                | PR  | Notes |
|-------|------------------------------------------|-----------------------|-----|-------|
| P1    | Lexicon contract                          | ✅ complete           | #17 | 4 UNSPSC + 5 ISIC JSON lexicons under `00-contracts/lexicons/com/etzhayyim/apps/{unispsc,isic}/` |
| P2    | ISIC fleet generation script              | ✅ complete           | #17 | `70-tools/scripts/gen-isic/gen_isic_agents.py` — Haiku Batch runner; `ast.parse` + top-level `graph` validation gate; `--dry-run` / `--execute` / `--resume` modes |
| P3    | ISIC fleet first generation run           | ⏸ gated               | —   | Requires `ANTHROPIC_API_KEY` + explicit operator approval (~$0.30 Anthropic Batch spend) |
| P4    | UNSPSC langserver pod                     | ✅ manifests-ready    | #19 | `50-infra/k8s/lg-open-unispsc/` Deployment + Service + HPA + Dockerfile; 18,342 agents lazy-loaded; smoke against `c10101501` PASS in 11 ms |
| P5    | ISIC langserver pod                       | ✅ manifests-ready    | #19 | `50-infra/k8s/lg-open-isic/` same shape; empty registry is a valid steady state until P3 |
| P6    | Kotodama actor wrapper                    | ✅ complete           | #21 | `@etzhayyim/kotodama-host-sdk/langserver-actor`; `UnispscActor` + `IsicActor` + `LangserverActorError`; 12/12 vitest |
| P7    | XRPC handler + AppView                    | ✅ complete           | #27 | `@etzhayyim/kotodama-host-sdk/langserver-xrpc-handler` (Hono); 2 CF Workers bound to `unispsc.etzhayyim.com` + `isic.etzhayyim.com`; 10/10 vitest |
| P8    | MCP server                                | ✅ complete           | #22 | `@etzhayyim/unispsc-isic-mcp` v0.1.0; 9 MCP tools (zod 4 schemas); stdio + programmatic HTTP transports; 25/25 vitest |
| P9    | Real Anthropic-SDK-backed classifier      | ⏳ pending            | —   | Replaces `stub_classifier` in `kotodama.langserver.router`; requires `ANTHROPIC_API_KEY` at runtime |

**Four-surface architecture is functionally complete** (HTTP / Actor / XRPC / MCP).
Remaining work: spend gate (P3) and runtime LLM wiring (P9). Both are
independent of each other and of the merged manifests.

# Context

The repo already contains the UNSPSC LangGraph Pregel fleet authorized by
ADR-2605171300: **18,343 per-commodity Python files** at
`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/unispsc_agents/c{code}.py`,
each exposing a compiled `graph = StateGraph(...).compile()` at module top
level. Today these files exist as source only — there is no resident process
serving them, no remote call surface, and no per-class agent fleet on the
ISIC Rev. 4 side (only three section-level classifier graphs at
`60-apps/etzhayyim-project-open-isic/lg/lg_open_isic/graphs/` plus 428 class
JSONs at `data/classes/`).

Three forces converge:

1. **Operational reachability**. UNSPSC agents must be invokable end-to-end
   from outside the Python process — from TypeScript apps (XRPC), from MCP
   clients, from internal Kotodama actors. Today only `dynamic_runner.py`
   can load them, and only in-process.
2. **Symmetry**. The 18-fold investment in UNSPSC has no ISIC analogue.
   Class-level economic activity classification (4-digit ISIC) is a similar
   structural problem with a much smaller surface (428 vs 18,343), and the
   same per-class deterministic-state-transducer pattern fits.
3. **Cost**. Calling 18,343 + 428 = 18,771 agent codepaths from any default
   model (Sonnet/Opus) for bulk classification is prohibitive. The bulk
   classification step is a routing problem — Haiku is structurally adequate
   for top-K candidate selection over a finite vocabulary, with Sonnet kept
   in reserve for ambiguous cases.

# Decision

Adopt a four-surface langserver architecture per taxonomy, with a shared
model routing policy and a one-time Haiku-driven generation pass for the
ISIC fleet.

## Architecture

```
                ┌─ XRPC (10-protocol/xrpc + 60-apps AppView)
Caller ─────────┼─ MCP server (40-engine/kotoba/crates/kotoba-kotodama/mcp/)
                ├─ Kotodama Actor (40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk)
                └─ Direct HTTP (LangServe /invoke /batch /stream)
                          │
                          ▼
            Lexicon validation
            (00-contracts/lexicons/com/etzhayyim/apps/{unispsc,isic}/*.json)
                          │
                          ▼
       AppView dispatch
       (60-apps/etzhayyim-project-open-{unispsc,isic}/)
                          │
                          ▼
         LangServer pod
         (50-infra/k8s/lg-open-{unispsc,isic}/)
            ├─ lazy importlib registry, LRU 1k entries
            ├─ embedding pre-filter (top-20 candidates)
            ├─ model_router: Haiku-4.5 → Sonnet-4.6 on low confidence
            └─ pregel agent.ainvoke(state)
                          │
                          ▼
         SDK substrate (optional)
         — PDS record write for traceable classifications
         — L2 anchor batch for cross-org auditable history
```

## Call surface 1: Direct HTTP (LangServe)

Each langserver exposes `/invoke`, `/batch`, `/stream`, `/health`, and
`/agents` over FastAPI + LangServe. Internal calls inside the cluster use
the in-cluster Service DNS (`lg-open-unispsc.lg-open-unispsc.svc:8000`).

## Call surface 2: Kotodama Actor

`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk` gets two new actor wrappers:

```typescript
const unispsc = sdk.actor("unispsc");
const { candidates } = await unispsc.classify({ description: "..." });
const result = await unispsc.invokeAgent({ code: "10101501", payload: {} });

const isic = sdk.actor("isic");
const { path } = await isic.hierarchicalClassify({
  description: "...",
  stopAt: "class",
});
```

Implementation is a thin HTTP client targeting the in-cluster langserver
Service DNS. Kotodama auto-generates the actor card and capability
declaration from the lexicon set per the host-sdk convention.

## Call surface 3: XRPC

Lexicons are authored under `00-contracts/lexicons/com/etzhayyim/apps/{unispsc,isic}/`:

| NSID | Type | Purpose |
|---|---|---|
| `com.etzhayyim.apps.unispsc.classify` | procedure | description → top-K UNSPSC codes |
| `com.etzhayyim.apps.unispsc.invokeAgent` | procedure | code → agent.ainvoke(state) |
| `com.etzhayyim.apps.unispsc.listAgents` | query | paged registry listing |
| `com.etzhayyim.apps.unispsc.health` | query | langserver health probe |
| `com.etzhayyim.apps.isic.classify` | procedure | single-level class classification |
| `com.etzhayyim.apps.isic.hierarchicalClassify` | procedure | section → division → group → class |
| `com.etzhayyim.apps.isic.invokeAgent` | procedure | classCode → agent.ainvoke(state) |
| `com.etzhayyim.apps.isic.listAgents` | query | paged registry listing |
| `com.etzhayyim.apps.isic.health` | query | langserver health probe |

XRPC handler lives in the corresponding AppView under `60-apps/etzhayyim-project-open-{unispsc,isic}/`.
The handler validates the input against the Lexicon schema, then dispatches
to the langserver via in-cluster HTTP.

## Call surface 4: MCP

A new MCP server at `40-engine/kotoba/crates/kotoba-kotodama/mcp/unispsc-isic-mcp/` exposes the
four primary lexicons as MCP tools (`classify_unispsc`, `classify_isic`,
`invoke_agent`, `list_agents`). Each tool body is a thin wrapper that
constructs the same lexicon-shaped XRPC payload, so validation and
dispatch are shared with surface 3. The MCP server supports both stdio
transport (for desktop hosts) and HTTP transport (for service-mesh clients).

## LangServer internals

### Lazy registry

The 18,343 UNSPSC files must not all import at startup — memory pressure
would be ~3-5 GB. Instead:

1. On startup, the server scans the `unispsc_agents/` directory for
   filenames matching `c\d+\.py` and builds an in-memory **registry**
   (code → module path), **without** importing.
2. On first call to `invokeAgent(code)`, the server does
   `importlib.import_module(...)`, calls `getattr(mod, "graph")`, and
   inserts the compiled graph into an LRU cache (1000 entries, 1.5 GB cap).
3. On LRU eviction, the module is removed from the cache but **not**
   unloaded from `sys.modules` (avoids spurious re-import work on warm-back).

The same registry shape applies to ISIC after fleet generation.

### Model router

```
model_hint = state.get("modelHint", "auto")
if model_hint == "auto":
    candidates = haiku_classify(description)
    if max(candidates, key=lambda c: c.confidence).confidence < THRESHOLD:
        candidates = sonnet_classify(description, prior=candidates)
        escalated = True
    return candidates, "haiku-4.5" if not escalated else "sonnet-4.6", escalated
```

Embedding pre-filter (delegated to `30-graph/vectorization/`) narrows the
candidate space to top-20 codes before Haiku sees the prompt, reducing
per-call cost to roughly $0.001 / classify.

Model identifiers come from the `MODEL_REGISTRY` SSoT in the kotodama
host-sdk per existing convention; no hardcoded model strings in app code.

## ISIC fleet generation

`70-tools/scripts/gen-isic/gen_isic_agents.py` reads the 428 class JSONs
and submits them as an Anthropic Batch API job to Haiku 4.5. For each
class, it produces a single Python file matching the UNSPSC pattern
(TypedDict state + 2-4 deterministic transition functions +
top-level compiled `graph`). Each generated file is validated via
`ast.parse()` plus a structural check ("module exposes top-level `graph`
binding") before being written. Failed validations are reported but
**not** written — the pass is rerun for those specific class codes.

Cost estimate: 428 × ~2k input + ~500 output tokens via Haiku 4.5 Batch
API (50% discount) is approximately $0.30 for a full pass. The script is
idempotent (skips classes whose output file already exists) so partial
reruns are cheap.

Generated files land at:

```
40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/isic_agents/c{classCode}.py
```

## Phase ordering

```
Phase 1  Lexicon contract                 (this PR — done)
Phase 2  ISIC fleet generation script     (this PR — done; no API spend yet)
Phase 3  ISIC fleet first generation run  (separate PR; spends ~$0.30 of Haiku)
Phase 4  Langserver pod for UNSPSC        (50-infra/k8s/lg-open-unispsc/)
Phase 5  Langserver pod for ISIC          (50-infra/k8s/lg-open-isic/)
Phase 6  Kotodama actor wrapper           (40-engine/kotoba/crates/kotoba-kotodama/sdk)
Phase 7  XRPC handler + AppView           (10-protocol/xrpc + 60-apps)
Phase 8  MCP server                       (40-engine/kotoba/crates/kotoba-kotodama/mcp/)
Phase 9  Model-router policy hardening    (eval suite + escalation tuning)
```

Phase 1 and Phase 2 land together because they are zero-spend artifact
work and together they unblock every following phase.

# Consequences

## 正の効果

- **Per-class economic-activity agents become first-class callable units**
  across the four surfaces a Kotodama-shaped runtime knows about.
- **Bulk classification cost collapses** from Opus/Sonnet pricing to
  Haiku pricing while preserving Sonnet as a quality-gated escalation.
- **ISIC reaches parity with UNSPSC** for a one-time spend of ~$0.30.
- **Lexicon is the single contract source** — XRPC, MCP, and the actor
  wrapper all reuse the same input/output schemas, so drift between the
  surfaces is bounded by codegen rather than human discipline.

## 負の効果 / コスト

- **Two langservers to operate** (one per taxonomy). HPA + lazy registry
  keep the steady-state cost low but cluster footprint is non-zero.
- **Generated ISIC agents are stylized**, not domain-expert authored.
  The deterministic-state-transducer pattern is meant as a routing
  scaffold, not a substantive domain model. Domain experts can replace
  any generated file later without changing the call surfaces.
- **MCP surface duplicates XRPC semantics**. This is intentional (MCP
  clients are not always lexicon-aware) but requires either a shared
  validation library or careful regeneration to prevent drift.

## Out of scope

- **Replacing existing UNSPSC agents** with regenerated content. The
  authorized fleet from ADR-2605171300 is preserved as-is.
- **PDS / L2 anchoring** of each individual classification call. The SDK
  hook is wired but disabled by default; opt-in per AppView per the
  privacy implications of permanent record creation.

# Alternatives Considered

## A. Single langserver hosting both taxonomies

却下理由: per-taxonomy registries differ in size by ~40×; co-tenancy
forces unfortunate LRU eviction patterns and obscures HPA signals.

## B. Embed agents inside the Kotodama actor process directly

却下理由: 18,343 modules + LangGraph runtime is too heavy for the
TS-native Worker target. The actor wrapper is the right shape; the agents
themselves belong in a Python langserver.

## C. Skip ISIC generation; reuse UNSPSC-style classification only

却下理由: ISIC and UNSPSC index different ontologies (economic activity
vs commodity). An entity classifier that only knows UNSPSC cannot answer
"which ISIC class is this entity in" without a translation layer that
doesn't exist.

## D. Author the 428 ISIC files by hand

却下理由: ~5 minutes × 428 = 35+ hours of human authoring for content
that is structurally generative. Haiku Batch API does the same job for
$0.30 and 30 minutes wall-clock.

# References

- ADR-2605170900 — etzhayyim/root as canonical home for open ADRs
- ADR-2605171300 — Open-UNSPSC generative agent fleet (18,343 agents)
- ADR-2605172000 — kotoba substrate (langservers must not depend on RW)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/unispsc_agents/`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/dynamic_runner.py`
- `60-apps/etzhayyim-project-open-isic/data/classes/` (428 ISIC Rev. 4 class JSONs)
- `00-contracts/lexicons/com/etzhayyim/apps/{unispsc,isic}/*.json` (this PR)
- `70-tools/scripts/gen-isic/gen_isic_agents.py` (this PR)
