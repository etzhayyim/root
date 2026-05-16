import { Kysely, sql } from "kysely";

// ADR 2605011200 — graph expansion proposal landing table.
// tier: C
//
// One row per LLM-proposed (source_vid, edge_kind, dst_label) triple.
// status='proposed' until a downstream review step promotes it to a real
// edge_* row. Never written to by anything other than the
// `graph_expand_tick` BPMN (enforced via vertex_bpmn_lexicon_binding
// .write_table_allowlist = 'vertex_graph_expand_proposal').
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_graph_expand_proposal (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      source_vid         VARCHAR NOT NULL,
      proposed_dst_vid   VARCHAR,
      proposed_dst_label VARCHAR,
      edge_kind          VARCHAR NOT NULL,
      confidence         DOUBLE PRECISION NOT NULL,
      rationale          VARCHAR,
      llm_model          VARCHAR NOT NULL,
      status             VARCHAR NOT NULL DEFAULT 'proposed',
      created_at         VARCHAR NOT NULL,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_graph_expand_proposal_source
      ON vertex_graph_expand_proposal (source_vid, llm_model, created_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_graph_expand_proposal_status
      ON vertex_graph_expand_proposal (status, confidence)
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_graph_expand_proposal_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_graph_expand_proposal_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_graph_expand_proposal`.execute(db);
}
