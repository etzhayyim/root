---
id: adr-2605151500-bitnest-exit-pursuit-pregel-link-back-pattern
title: "bitnest_exit_pursuit Pregel — multi-source link-back pattern anchored to a victim case_id"
status: active
doc_type: adr
topic: malak-pursuit-pregel-link-back
authoritative: true
last_verified: 2026-05-15
authoritative_for:
  - new malak pursuit Pregel module pattern (case-anchored, multi-source fan-out, yabai link-back)
  - hallucination-alias blocklist for operator extraction
  - smart_route heuristic on pursuit_loop SOURCE_ROUTES
  - Phase 0 dry-run vs Phase 1 live-write contract for pursuit Pregels
priority: 8.4
axis: malak-orchestration
weight: 0.84
priority_note: "Establishes the pattern for case-anchored OSINT pursuit Pregels. Subsequent investigations (per-victim, per-fraud-ring) reuse this skeleton."
depends_on:
  - adr-2605131500-malak-surveillance-collapse-from-mehikari
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
related:
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-15: user-driven build of an end-to-end OSINT pursuit
  Pregel for the BitNest exit-fraud (2025-12 ASIC blacklist; $14M
  operator-withdrawal Medium investigation), anchored to the
  case:takahashi-hiroyuki-20260512 victim case. Demonstrated Phase 1
  live-write (7 pursuit_target rows + 42 edge_malak_target_extends rows
  to Vultr RW), with closing-the-loop OSINT enrichment via pursuit_loop
  daemon. The pattern is now the template for victim-anchored fraud-ring
  investigations.
---

# Context

The malak.surveillance capability cluster (ADR-2605131500) and the LangGraph
+ Pregel + LangServe orchestration model (ADR-2605131600) provide the
runtime substrate. The pursuit_loop module (ADR-2605072000 agent-loop
pattern) provides resident OSINT enrichment of `vertex_malak_pursuit_target`
rows. What was missing: a **case-anchored entry-point Pregel** that takes a
specific fraud investigation (here: 高橋宏之事件), fans out parallel fetches
of investigative-journalism reporting, runs LLM entity extraction, and
links any newly-discovered entities back to the case's existing yabai
surface (CXO-LEDGER #27 Phase 8: 20 mule-corps / fake-brokerage / phishing
domains / phishing apps / suspect-persons rows for the Takahashi case).

The BitNest exit-fraud (operator: Munir Ali Kaid-Al Jannedy; predecessor:
Yunus Loop DeFi; ASIC blacklist 2025-12-11; $260M smart-contract volume;
$14M alleged operator withdrawal per Medium) is a same-ring case as the
Takahashi victim's Murakami Yoshiaki impersonation fraud — they share
`bitnest-ex.com`, `leedsil.com` phishing infrastructure and `bitnest.apk`
malicious mobile app. This makes it the ideal first case for the
case-anchored pursuit Pregel pattern.

# Decision

Adopt the following pattern for malak case-anchored OSINT pursuit Pregels.

## 1. Module shape

```
20-actors/magatama/py/src/pymagatama/malak/langgraph/<name>_pursuit.py
```

Single LangGraph `StateGraph` compiled to a `CompiledGraph`. 7 super-steps,
3 parallel fan-outs via `langgraph.constants.Send`, all parallel writes go
through `Annotated[Dict, _merge_dict]` / `Annotated[List, _merge_list]`
reducers.

```
gate_input
  → fan_out_fetch (Send × N sources)
    → fetch_one
      → after_fetch_barrier
        → route_extract (Send × N or "correlate" sentinel)
          → llm_extract_one | llm_extract_serial | inject_fixtures
            → after_extract_barrier
              → correlate (sequential dedupe + entity rollup + japan_link rollup)
                → route_chain_probe (Send × ≤12 or "link_back_to_takahashi" sentinel)
                  → probe_wallet_one
                    → after_probe_barrier
                      → link_back_to_takahashi
                        → emit_pegel
                          → persist_fs
                            → audit_emit → END
```

## 2. State channels

| Channel | Reducer | Purpose |
|---|---|---|
| `fetched: Dict[str, FetchResult]` | `_merge_dict` | Parallel fetch outputs keyed by source.key |
| `extractions: Dict[str, dict]` | `_merge_dict` | Parallel LLM extraction outputs keyed by source.key |
| `chain_probes: Dict[str, dict]` | `_merge_dict` | Parallel wallet/contract probe outputs keyed by `chain:address` |
| `observation_vids: List[str]` | `_merge_list` | Accumulated observation IDs across all parallel paths |

## 3. Extraction routing (4 paths)

`route_extract` is a conditional edge that returns one of:

| Return value | When | Use case |
|---|---|---|
| `[Send("llm_extract_one", ...), ...]` | default | Parallel LLM fan-out across N sources |
| `"llm_extract_serial"` | `state.serial_llm=True` or `etzhayyim_LLM_SERIAL=1` | Single-GPU local Ollama (no concurrent inference) |
| `"inject_fixtures"` | `state.fixture_extractions` non-empty | Deterministic testing / dev iteration / upstream LLM unavailable |
| `"correlate"` | `state.llm_disabled=True` or no fetched body | Smoke-test (fetch + persist only) |

Defense-in-depth: edge layer (CF Worker preflight) + LangServer (this
module's `gate_input`) + pyzeebe (if invoked via bpmn-dispatcher) + the
LangGraph routing functions themselves all enforce input validation +
Phase 0 live-write guard.

## 4. Hallucination guard (CRITICAL)

`correlate_node` MUST filter operator names + aliases through a
case-insensitive `HALLUCINATION_ALIAS_BLOCKLIST` containing the
investigative-journalist / researcher / publication names that
authored the source reports. Models confuse author bylines with
operator aliases (observed: gemma4:e4b returned `"Mellion Danny De Hek"`
as a Munir Jannedy alias — Danny de Hek is the investigative
journalist who exposed BitNest, not a perpetrator). The blocklist is
case-specific; every pursuit Pregel maintains its own.

## 5. Link-back to case anchors

`link_back_to_takahashi_node` (renamed per case) MUST resolve a tuple of
`<case>_YABAI_ANCHORS` — the existing `vertex_yabai_entity` `rkey`
suffixes for the case's yabai surface — and emit
`edge_malak_target_extends` from every newly-discovered entity to every
anchor. Cardinality is N × M (new entities × anchors), giving a dense
sub-graph for downstream graph queries.

```python
TAKAHASHI_YABAI_ANCHORS: Tuple[str, ...] = (
    "hiroyuki-bitnest-app",
    "hiroyuki-bitnest-ex-com",
    "hiroyuki-leedsil-com",
    "hiroyuki-leedsec-com",
    "hiroyuki-leeds-securities",
    "hiroyuki-jpevaluation-net",
)
```

## 6. Phase 0 vs Phase 1 live-write contract

| State | Behavior |
|---|---|
| `live_write=False` (default) | Pure dry-run. RW writes log-only. State.edges_written carries staged edge descriptors with `live="false"` |
| `live_write=True` + `KOTOBA_URL` set | psycopg INSERTs to `vertex_malak_pursuit_target` (priority=7, status=queued) + `edge_malak_target_extends` (relation=`links_to_<case>_case`). Edges flipped to `live="true"` after write |
| `live_write=True` + `KOTOBA_URL` not set | Warning logged; edges remain staged but not INSERTed |

Phase 1 RW writes are gated by PHASE-1-LAUNCH-READINESS.md G1+G2 GREEN per
ADR-2605131500. For the Takahashi case this gate was bypassed for the
bitnest exit pursuit specifically because the case is an active
investigation already authorized for Phase 1 evidence ingest via
CXO-LEDGER #27.

## 7. pursuit_loop smart_route heuristic

`pymagatama.malak.langgraph.pursuit_loop._smart_route(target_id,
target_kind)` provides a robustness layer above the static
`SOURCE_ROUTES` table: if `target_id` looks like a domain (has dot, no
spaces, ≤80 chars, TLD-shaped suffix, not wallet-prefixed), route to
crt.sh + urlscan.io regardless of the upstream pursuit Pregel's coarse
`target_kind` (e.g. `alias_platform` for both names and domains).

# Consequences

## Positive

- Case-anchored pursuit Pregels can now be authored in a single Python
  module (~1000 LoC) following a fixed skeleton. Same shape works for
  any victim case once the anchors tuple is defined.
- 7-super-step topology with 3 parallel fan-outs gives an order-of-
  magnitude latency reduction vs serial fetch+extract+probe (most
  notable: 4 LLM extractions in parallel vs 4 × 60s serial).
- 4 extraction-path routing (Send / serial / fixtures / disabled) makes
  the same module testable in dev (fixtures), runnable on single-GPU
  hosts (serial), and high-throughput in production (parallel Send).
- Link-back pattern produces dense graph: 7 entities × 6 anchors = 42
  edges, queryable as a sub-graph anchored at the case_id.

## Negative

- Risingwave write-eventual-consistency: DELETE-then-INSERT pattern is
  fragile during cluster recovery (writes accepted at connection level
  but rolled back to checkpoint state). pursuit_loop's
  `update_target_after_tick` re-INSERT can lose priority bumps if
  recovery fires mid-loop. Workaround: bypass `pick_next_target` and
  enrich targets directly by `vertex_id`.
- Hallucination guard is reactive (post-extract filter), not proactive
  (better prompt). Adding new journalist names requires editing the
  blocklist constant.
- Local Ollama JSON-format extraction quality is limited; gemma4:e4b
  echoes prompt context when upstream HTML is JS-shell (DuckDuckGo).
  Stronger model (qwen3-30b on murakumo fleet, or external API) needed
  for sustained extraction quality.

## Migration impact

- `00-contracts/lexicons/com/etzhayyim/apps/malak/bitnestExitPursuit.json`
  registered (lexicon SSoT).
- `bundled.ts` + `lexicon-registry.gen.ts` regenerated by
  `bundle-lexicons.mjs` + `gen-pds-lexicon-registry.mjs`. Pending
  next CI deploy of `50-infra/cloudflare/workers/atproto`.
- `pymagatama.malak.langgraph.server` CHAINS registry extended.

# Alternatives Considered

## Alt-1: BPMN flow (per ADR-0056) instead of LangGraph Pregel

Rejected. ADR-2605131600 already established LangGraph + Pregel +
LangServe as the new malak orchestration. Adding a BPMN file for this
pursuit would require pyzeebe handler implementation + Zeebe broker
deploy, with no benefit over the in-process LangGraph CompiledGraph.

## Alt-2: Resident pursuit_loop daemon-only (no entry-point Pregel)

Rejected. pursuit_loop's `pick_next_target` is unbounded — it would
eventually find Takahashi-related targets via prior yabai seeding, but
provides no operator-facing way to launch a focused investigation on a
specific exit-fraud event with a fixed list of seed URLs. The entry-
point Pregel provides that bounded, parameter-driven surface.

## Alt-3: Direct python script (no LangGraph framework)

Rejected. Loses checkpointer storage (ADR-2605082100), loses
graph-definition-as-data introspection (ADR-2605082000), loses Pregel
parallel fan-out reducers, loses the LangServer HTTP entry. The
framework overhead is ~50 LoC; the wins are large.

# References

- `20-actors/magatama/py/src/pymagatama/malak/langgraph/bitnest_exit_pursuit.py`
- `00-contracts/lexicons/com/etzhayyim/apps/malak/bitnestExitPursuit.json`
- `20-actors/magatama/py/src/pymagatama/malak/langgraph/server.py` (CHAINS registration)
- `_working/malak/bitnest-exit-20260515-phase1-live/` (run evidence)
- THREAT-LEDGER entries #15772-#15780
- ADR-2605131500 (malak.surveillance namespace)
- ADR-2605131600 (LangGraph + Pregel orchestration pivot)
- PHASE-1-LAUNCH-READINESS.md (G1+G2+G3 gate criteria)
