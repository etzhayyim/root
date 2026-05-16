import { Kysely, sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 20260501110000: Corpus2Skill hierarchical navigation tree.
 *
 * arXiv 2604.14572 "Don't Retrieve, Navigate" — offline distills a corpus
 * into a hierarchical skill tree via recursive K-means + LLM summarisation.
 * At query time the LLM navigates the tree level-by-level to reach a leaf
 * cluster, then the IVF+PQ searcher retrieves WET chunks from that cluster.
 *
 * Tree depth: 4 levels (L0 root → L1 category → L2 topic → L3 leaf).
 * Each leaf maps to 1-N IVF cluster IDs via edge_skill_doc.
 *
 * This table is intentionally separate from vertex_corpus_skill_extraction_run
 * (which tracks evidence edges from corpus vertices to ESCO skills).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_corpus_skill_node (
      node_id            VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      parent_id          VARCHAR,
      level              BIGINT  NOT NULL DEFAULT 0,
      domain             VARCHAR NOT NULL,
      summary            VARCHAR,
      doc_count          BIGINT  NOT NULL DEFAULT 0,
      centroid           REAL[],
      label              VARCHAR,
      keywords_csv       VARCHAR,
      distill_version    VARCHAR NOT NULL,
      status             VARCHAR NOT NULL DEFAULT 'active'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_corpus_skill_node_parent
      ON vertex_corpus_skill_node (parent_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_corpus_skill_node_domain_level
      ON vertex_corpus_skill_node (domain, level, distill_version, status)
  `.execute(db);

  // Edges from leaf skill nodes (level=3) to WET chunk vertex IDs.
  // cluster_id mirrors vertex_wet_chunk_pq.ivf_cluster_id for fast join.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_skill_doc (
      edge_id            VARCHAR PRIMARY KEY,
      node_id            VARCHAR NOT NULL,
      chunk_vertex_id    VARCHAR NOT NULL,
      domain             VARCHAR NOT NULL,
      cluster_id         BIGINT,
      distill_version    VARCHAR NOT NULL,
      distance           DOUBLE PRECISION
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_skill_doc_node
      ON edge_skill_doc (node_id, distill_version)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_skill_doc_cluster
      ON edge_skill_doc (domain, cluster_id, distill_version)
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_skill_doc_cluster`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_skill_doc_node`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_skill_doc`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_corpus_skill_node_domain_level`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_corpus_skill_node_parent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_corpus_skill_node`.execute(db);
}
