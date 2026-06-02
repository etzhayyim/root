# etzhayyim-project-open-seiyaku

`etzhayyim-project-open-seiyaku` is the monorepo entry point for a
pharmaceutical manufacturing actor built with BPMN-as-actor. Phase 1 covers:

- batch record registration by plant operators
- QA review and disposition
- amendment / deviation handling
- confidential payload retention purge

Canonical executable assets live under:

- `00-contracts/bpmn/com/etzhayyim/open-seiyaku/`
- `00-contracts/forms/com/etzhayyim/open-seiyaku/`
- `00-contracts/lexicons/com/etzhayyim/apps/openSeiyaku/`
- `30-graph/graph-schema/migrations/20260423190000_vertex_open_seiyaku.ts`
- `30-graph/graph-schema/migrations/20260423191000_seed_open_seiyaku_bpmn_actors.ts`

The project intentionally mirrors the implementation style used by
`ADR-0051`-driven actors in this repository, while applying it to
pharmaceutical manufacturing rather than payroll.
