---
id: adr-260509-pokopia-research-agent-loop-provenance
title: Pokopia Research Agent Loop Provenance
status: active
doc_type: adr
topic: pokopia-research-agent-loop-provenance
date: 2026-05-09
implemented_date: 2026-05-16
---

# Pokopia Research Agent Loop Provenance

## Context

Pokopia item and guide facts are currently persisted as game item vertices and
domain-knowledge documents/chunks. That is enough for RAG answers, but not
enough to answer operational questions such as:

- which agent researched the fact
- which session produced the write
- which source URLs were inspected
- which claim came from which source
- which vertex/chunk/item rows were written as a result
- whether later refreshes superseded the claim

The 2026-05-09 チーゴのみ / Rawst Berry ingest used the existing live tables:

- `vertex_game_item`
- `vertex_domain_knowledge_document`
- `vertex_domain_knowledge_chunk`
- `vertex_domain_knowledge_source`
- `edge_domain_knowledge_cites`
- `vertex_agent_action_log`
- `vertex_agent_observation`

The saved session id is `codex-session-20260509-pokopia-chigo-berry`.
The saved item id is `did:etzhayyim:gameitem:pokemon-pokopia:chigo-berry`.

## Decision

Introduce a first-class research provenance graph for game knowledge curation.
The graph is append-only for observations and claims, while derived item/domain
rows may be overwritten by the existing Kotoba/Datomic primary-key behavior.

DDL is not applied by this ADR. Kotoba/Datomic DDL must go through the normal DDL
queue / health gate path.

## Vertex Design

### `vertex_research_session`

One row per autonomous or human-assisted research run.

Required fields:

- `vertex_id`: `research-session:{session_id}`
- `session_id`
- `agent_did`
- `agent_kind`: `codex | browser-agent | media-gamers-curator | human`
- `task_kind`: `game-item-research | guide-refresh | contradiction-check`
- `domain`
- `game_slug`
- `query_text`
- `status`: `running | complete | partial | failed | superseded`
- `started_at`
- `completed_at`
- `summary`
- `owner_did`, `org_id`, `user_id`, `actor_id`, `sensitivity_ord`

### `vertex_research_source_snapshot`

One row per URL/page/API payload inspected during a session.

Required fields:

- `vertex_id`: `source-snapshot:{session_id}:{source_hash}`
- `session_id`
- `source_url`
- `source_kind`: `official | guide | wiki | reddit | video | api | local-db`
- `publisher`
- `retrieved_at`
- `content_hash`
- `excerpt`
- `reliability_score`
- `license_note`
- `line_refs_json`
- `raw_artifact_uri`

### `vertex_research_claim`

Atomic normalized claim extracted from one or more sources.

Required fields:

- `vertex_id`: `claim:{claim_hash}`
- `session_id`
- `subject_id`: e.g. `did:etzhayyim:gameitem:pokemon-pokopia:chigo-berry`
- `predicate`: `acquisition | use | recipe | location | farming | caveat`
- `object_text`
- `normalized_json`
- `lang`
- `confidence`
- `status`: `active | contradicted | superseded | rejected`
- `created_at`
- `updated_at`

Example claim:

```json
{
  "predicate": "acquisition",
  "normalized_json": {
    "item": "チーゴのみ",
    "english_name": "Rawst Berry",
    "method": "チーゴの木にずつきして拾う",
    "seed_location": "キラキラうきしまの街・北西の島の隠し部屋",
    "english_location": "Sparkling Skylands, northwest island hidden room"
  }
}
```

### `vertex_research_write`

Materialization record for rows written into production knowledge tables.

Required fields:

- `vertex_id`: `research-write:{session_id}:{target_table}:{target_id_hash}`
- `session_id`
- `target_table`
- `target_vertex_id`
- `target_collection`
- `write_kind`: `insert | update | overwrite | delete`
- `write_sql_hash`
- `payload_hash`
- `created_at`

## Edge Design

### `edge_research_session_used_source`

`research_session -> source_snapshot`.

Fields:

- `edge_id`
- `src_vid`
- `dst_vid`
- `relation_kind = 'used_source'`
- `rank`
- `created_at`

### `edge_research_source_supports_claim`

`source_snapshot -> research_claim`.

Fields:

- `edge_id`
- `src_vid`
- `dst_vid`
- `relation_kind = 'supports' | 'contradicts' | 'qualifies'`
- `confidence`
- `evidence_excerpt`
- `line_refs_json`
- `created_at`

### `edge_research_claim_materialized_as`

`research_claim -> research_write`.

Fields:

- `edge_id`
- `src_vid`
- `dst_vid`
- `relation_kind = 'materialized_as'`
- `target_table`
- `created_at`

### `edge_research_write_targets_vertex`

`research_write -> target game/domain vertex`.

Fields:

- `edge_id`
- `src_vid`
- `dst_vid`
- `relation_kind = 'writes'`
- `target_table`
- `created_at`

## MV Design

### `mv_research_fact_lineage`

Purpose: answer "who put this fact here and from where?"

Shape:

```sql
SELECT
  w.target_table,
  w.target_vertex_id,
  c.subject_id,
  c.predicate,
  c.object_text,
  c.confidence,
  s.session_id,
  rs.agent_did,
  rs.agent_kind,
  ss.source_url,
  ss.publisher,
  ss.retrieved_at,
  esc.evidence_excerpt,
  w.created_at AS materialized_at
FROM vertex_research_write w
JOIN edge_research_claim_materialized_as cm ON cm.dst_vid = w.vertex_id
JOIN vertex_research_claim c ON c.vertex_id = cm.src_vid
JOIN edge_research_source_supports_claim esc ON esc.dst_vid = c.vertex_id
JOIN vertex_research_source_snapshot ss ON ss.vertex_id = esc.src_vid
JOIN vertex_research_session rs ON rs.session_id = c.session_id;
```

### `mv_game_item_research_status`

Purpose: list item coverage freshness per game.

Key fields:

- `game_slug`
- `item_id`
- `item_name`
- `latest_session_id`
- `latest_agent_did`
- `source_count`
- `claim_count`
- `latest_retrieved_at`
- `freshness_state`: `fresh | stale | needs-review | contradicted`

### `mv_research_agent_quality`

Purpose: score agent runs without reading large text blobs.

Key fields:

- `agent_did`
- `task_kind`
- `completed_runs`
- `failed_runs`
- `avg_sources_per_claim`
- `contradiction_rate`
- `materialized_claim_count`
- `last_completed_at`

## Index Design

Use Kotoba/Datomic secondary indexes only after health gate approval.

Recommended indexes:

```sql
CREATE INDEX idx_research_session_game_time
ON vertex_research_session(game_slug, completed_at);

CREATE INDEX idx_research_claim_subject_predicate
ON vertex_research_claim(subject_id, predicate, status);

CREATE INDEX idx_research_source_url_hash
ON vertex_research_source_snapshot(source_url, content_hash);

CREATE INDEX idx_research_write_target
ON vertex_research_write(target_table, target_vertex_id);

CREATE INDEX idx_edge_research_source_supports_claim_dst
ON edge_research_source_supports_claim(dst_vid);

CREATE INDEX idx_edge_research_claim_materialized_dst
ON edge_research_claim_materialized_as(dst_vid);
```

## Agent Loop Actor

Actor id: `did:web:media-gamers-research.etzhayyim.com`

Runtime:

- T1 logical actor for scheduling and policy
- L3 LangGraph Server execution for multi-step research
- RW direct read/write for graph persistence
- Browser/search capability only during source collection

Loop:

1. `plan_query`
   - Input: `{game_slug, topic, locale, requested_by}`
   - Output: source candidates and claim schema.
2. `collect_sources`
   - Fetch official, primary, and high-quality guide sources.
   - Save `vertex_research_source_snapshot`.
3. `extract_claims`
   - Convert source text into atomic claims.
   - Save `vertex_research_claim`.
4. `cross_check`
   - Require at least one high-confidence source or two independent medium
     sources before materialization.
   - Mark contradictions instead of overwriting silently.
5. `materialize`
   - Write `vertex_game_item`, `vertex_domain_knowledge_document/chunk/source`,
     and citation edges.
   - Save `vertex_research_write`.
6. `publish_lineage`
   - Emit `vertex_agent_action_log` and update MVs.
7. `refresh_policy`
   - Stale after 30 days for guide content, 7 days for event/patch content, and
     immediate refresh after patch-note source changes.

## PREGEL / Pregel Graph Step

Use a small Pregel-style iterative graph job for contradiction and authority
propagation. The job is called PREGEL in task metadata:

`Provenance Evidence Graph Evaluation Loop`.

Supersteps:

1. Source authority propagation:
   - official source starts at 1.0
   - named guide starts at 0.7
   - social source starts at 0.4
2. Claim support aggregation:
   - supporting edges add authority-weighted confidence
   - contradicting edges subtract authority-weighted confidence
3. Claim status update:
   - score >= 0.80: `active`
   - 0.50 <= score < 0.80: `needs-review`
   - score < 0.50 or contradiction from official source: `contradicted`
4. Materialization eligibility:
   - only `active` claims can update production item/domain rows
   - `needs-review` claims stay in research graph only

## Current Chigo Berry Materialization

The 2026-05-09 run saved:

- item vertex: `did:etzhayyim:gameitem:pokemon-pokopia:chigo-berry`
- document: `at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-chigo-berry`
- chunks:
  - acquisition/location
  - farming/restoration
  - uses
- source URLs:
  - `https://game8.jp/pocoapokemon/772056`
  - `https://pokopia.dev/guides/berries`
  - `https://www.dexerto.com/wikis/pokopia/how-to-get-all-berries-in-pokopia/`
- provenance rows:
  - `vertex_agent_action_log`: `agent-action:codex-session-20260509-pokopia-chigo-berry:research-save`
  - `vertex_agent_observation`: one row per inspected source

## Consequences

- Current RAG can answer チーゴのみ questions from existing domain-knowledge
  tables immediately.
- The research provenance graph is deployed (2026-05-16).
- Future game-item writes can be audited through `mv_research_fact_lineage`
  without parsing JSON props.

## Implementation (2026-05-16)

Three migrations applied to Kotoba/Datomic:

1. **`202605150100_pokopia_ditto_doll_ja_knowledge`** — Japanese-language
   domain-knowledge document + chunk + alias/token rows for メタモン人形 (Ditto
   doll). Enables chat.etzhayyim.com to answer Japanese acquisition questions for the
   item.

2. **`202605150200_vertex_research_provenance`** — Full DDL for the provenance
   graph: 4 vertex tables, 4 edge tables, 8 indexes, 3 MVs
   (`mv_research_fact_lineage`, `view_game_item_research_status`,
   `mv_research_agent_quality`).

3. **`202605150300_seed_pokopia_research_langgraph`** — Seeds
   `vertex_langgraph_assistant` (kind=`py_factory`,
   factory_path=`kotodama.langgraph_graphs.pokopia_research_agent_loop`) and
   `vertex_langgraph_deployment` (status=`active`).

LangGraph graph file:
`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/pokopia_research_agent_loop.py`

7 async nodes: `plan_query → collect_sources → extract_claims → cross_check →
materialize → publish_lineage → refresh_policy`. Pregel superstep is
`_run_pregel()` (pure Python, no DB/LLM deps, up to 6 supersteps, δ < 0.005
convergence).
