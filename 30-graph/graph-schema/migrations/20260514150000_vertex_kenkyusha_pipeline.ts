import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations.
// tier: B (research/scholarly knowledge — derivable from public bunken citation graph)

/**
 * kenkyusha — AI Research Frontier Explorer schema (Phase 1, 2C, 2H, 2K).
 *
 * Consolidates the DDL from five Alembic drafts (20260514_0001..0005) into
 * a single Kysely migration because vertex_* / edge_* belong in the
 * graph-schema TypeScript scope (per Alembic env.py guard).
 *
 * Tables created
 * --------------
 *   vertex_kenkyusha_discipline      ISCED-F detailed-field actor roster
 *   vertex_kenkyusha_frontier        Research frontiers (citationGap / temporalDecay / ...)
 *                                    + parent_frontier_id / split_reason / depth (Phase 2C)
 *                                    + rollup_{supports,contradicts,strong_children,last_at} (Phase 2K)
 *   vertex_kenkyusha_hypothesis      Testable hypotheses (elo-ranked, Pregel super-step lineage)
 *   vertex_kenkyusha_evidence        Per-source evidence rows
 *   vertex_kenkyusha_submission      arxiv manuscript persistence (Phase 2H)
 *
 *   edge_kenkyusha_supports          hypothesis → evidence (supporting)
 *   edge_kenkyusha_contradicts       hypothesis → evidence (contradicting)
 *   edge_kenkyusha_spawned_from      parent frontier → child frontier (Phase 2C)
 *
 * Why one migration?
 *   Kysely's FileMigrationProvider applies migrations in lexicographic
 *   order; bundling related tables in one file keeps the rollback story
 *   atomic. The Alembic seed migrations (discipline rows, MCP tool
 *   registration in vertex_capability, langgraph_assistant row) remain
 *   in 20-actors/magatama/py/alembic/versions/ as INSERT-only DDL-free
 *   files — they bypass the env.py vertex_* guard because INSERTs aren't
 *   matched by the DDL regex.
 *
 * RisingWave constraints honored:
 *   - No transactions (each `sql` statement auto-commits).
 *   - No FK constraints (referential integrity in application layer).
 *   - No NOT NULL DEFAULT on ALTER ADD COLUMN (use UPDATE-to-0 after).
 *   - No soft delete (hard delete only — ADR root rules).
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_kenkyusha_discipline ─────────────────────────────────────
  await sql`
    CREATE TABLE vertex_kenkyusha_discipline (
      vertex_id           varchar PRIMARY KEY,
      rkey                varchar NOT NULL,
      repo                varchar NOT NULL,
      did                 varchar NOT NULL,
      isced4              varchar NOT NULL,
      isced_broad         varchar NOT NULL,
      isced_narrow        varchar NOT NULL,
      name_en             varchar NOT NULL,
      name_ja             varchar,
      paradigm            varchar NOT NULL,
      maturity            varchar NOT NULL,
      interdisciplinarity varchar NOT NULL,
      cohort_hash         varchar,
      publication_count   integer NOT NULL,
      citation_count      integer NOT NULL,
      frontier_count      integer NOT NULL,
      actor_did           varchar NOT NULL,
      org_did             varchar NOT NULL,
      created_at          varchar NOT NULL,
      sensitivity_ord     integer NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_discipline_isced4 ON vertex_kenkyusha_discipline (isced4)`.execute(db);

  // ── vertex_kenkyusha_frontier ───────────────────────────────────────
  // Carries Phase 2C lineage cols (parent_frontier_id / split_reason /
  // depth) and Phase 2K rollup cols inline so no follow-up ALTER is needed.
  await sql`
    CREATE TABLE vertex_kenkyusha_frontier (
      vertex_id                varchar PRIMARY KEY,
      rkey                     varchar NOT NULL,
      repo                     varchar NOT NULL,
      frontier_id              varchar NOT NULL,
      did                      varchar NOT NULL,
      title                    varchar NOT NULL,
      description              varchar,
      detection_method         varchar NOT NULL,
      primary_discipline       varchar NOT NULL,
      secondary_disciplines    varchar,
      urgency                  varchar NOT NULL,
      evidence_level           varchar NOT NULL,
      consensus_level          varchar NOT NULL,
      cohort_hash              varchar,
      hypothesis_count         integer NOT NULL,
      evidence_count           integer NOT NULL,
      status                   varchar NOT NULL,
      source_did               varchar,
      detected_at              varchar NOT NULL,
      last_analyzed_at         varchar NOT NULL,
      parent_frontier_id       varchar,
      split_reason             varchar,
      depth                    integer,
      rollup_supports_total    integer,
      rollup_contradicts_total integer,
      rollup_strong_children   integer,
      rollup_last_at           varchar,
      actor_did                varchar NOT NULL,
      org_did                  varchar NOT NULL,
      created_at               varchar NOT NULL,
      sensitivity_ord          integer NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_frontier_status      ON vertex_kenkyusha_frontier (status, urgency)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_frontier_discipline  ON vertex_kenkyusha_frontier (primary_discipline)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_frontier_pending_sub ON vertex_kenkyusha_frontier (status, depth, parent_frontier_id)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_frontier_parent      ON vertex_kenkyusha_frontier (parent_frontier_id)`.execute(db);

  // ── vertex_kenkyusha_hypothesis ─────────────────────────────────────
  await sql`
    CREATE TABLE vertex_kenkyusha_hypothesis (
      vertex_id              varchar PRIMARY KEY,
      rkey                   varchar NOT NULL,
      repo                   varchar NOT NULL,
      hypothesis_id          varchar NOT NULL,
      frontier_id            varchar NOT NULL,
      statement              varchar NOT NULL,
      rationale              varchar,
      supporting_evidence    integer NOT NULL,
      contradicting_evidence integer NOT NULL,
      confidence_score       integer NOT NULL,
      elo_rating             integer NOT NULL,
      super_step             integer NOT NULL,
      parent_hypothesis_id   varchar,
      mutation_kind          varchar,
      llm_model              varchar NOT NULL,
      status                 varchar NOT NULL,
      actor_did              varchar NOT NULL,
      org_did                varchar NOT NULL,
      created_at             varchar NOT NULL,
      sensitivity_ord        integer NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_hypothesis_frontier ON vertex_kenkyusha_hypothesis (frontier_id, status)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_hypothesis_elo      ON vertex_kenkyusha_hypothesis (frontier_id, elo_rating)`.execute(db);

  // ── vertex_kenkyusha_evidence ───────────────────────────────────────
  await sql`
    CREATE TABLE vertex_kenkyusha_evidence (
      vertex_id        varchar PRIMARY KEY,
      rkey             varchar NOT NULL,
      repo             varchar NOT NULL,
      evidence_id      varchar NOT NULL,
      frontier_id      varchar NOT NULL,
      hypothesis_id    varchar,
      source_type      varchar NOT NULL,
      source_did       varchar,
      source_uri       varchar,
      source_title     varchar,
      source_year      integer,
      relevance_score  integer NOT NULL,
      evidence_type    varchar NOT NULL,
      extracted_claim  varchar,
      llm_model        varchar NOT NULL,
      actor_did        varchar NOT NULL,
      org_did          varchar NOT NULL,
      created_at       varchar NOT NULL,
      sensitivity_ord  integer NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_evidence_frontier   ON vertex_kenkyusha_evidence (frontier_id)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_evidence_hypothesis ON vertex_kenkyusha_evidence (hypothesis_id, evidence_type)`.execute(db);

  // ── vertex_kenkyusha_submission ─────────────────────────────────────
  await sql`
    CREATE TABLE vertex_kenkyusha_submission (
      vertex_id              varchar PRIMARY KEY,
      rkey                   varchar NOT NULL,
      repo                   varchar NOT NULL,
      submission_id          varchar NOT NULL,
      frontier_id            varchar NOT NULL,
      winner_hypothesis_id   varchar NOT NULL,
      evidence_ids           varchar,
      arxiv_category         varchar NOT NULL,
      title                  varchar NOT NULL,
      abstract               varchar,
      manuscript_tex         varchar NOT NULL,
      manuscript_byte_size   integer NOT NULL,
      consensus_level        varchar NOT NULL,
      evidence_supports      integer NOT NULL,
      evidence_contradicts   integer NOT NULL,
      llm_model              varchar NOT NULL,
      status                 varchar NOT NULL,
      tarball_path           varchar,
      arxiv_id               varchar,
      submitted_at           varchar,
      accepted_at            varchar,
      actor_did              varchar NOT NULL,
      org_did                varchar NOT NULL,
      created_at             varchar NOT NULL,
      sensitivity_ord        integer NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_submission_frontier ON vertex_kenkyusha_submission (frontier_id)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_submission_status   ON vertex_kenkyusha_submission (status, created_at)`.execute(db);

  // ── edge_kenkyusha_supports ─────────────────────────────────────────
  await sql`
    CREATE TABLE edge_kenkyusha_supports (
      vertex_id  varchar PRIMARY KEY,
      src        varchar NOT NULL,
      dst        varchar NOT NULL,
      weight     integer NOT NULL,
      created_at varchar NOT NULL,
      actor_did  varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_supports_src ON edge_kenkyusha_supports (src)`.execute(db);

  // ── edge_kenkyusha_contradicts ──────────────────────────────────────
  await sql`
    CREATE TABLE edge_kenkyusha_contradicts (
      vertex_id  varchar PRIMARY KEY,
      src        varchar NOT NULL,
      dst        varchar NOT NULL,
      weight     integer NOT NULL,
      created_at varchar NOT NULL,
      actor_did  varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_contradicts_src ON edge_kenkyusha_contradicts (src)`.execute(db);

  // ── edge_kenkyusha_spawned_from (Phase 2C) ──────────────────────────
  await sql`
    CREATE TABLE edge_kenkyusha_spawned_from (
      vertex_id     varchar PRIMARY KEY,
      src           varchar NOT NULL,
      dst           varchar NOT NULL,
      split_reason  varchar NOT NULL,
      depth         integer NOT NULL,
      created_at    varchar NOT NULL,
      actor_did     varchar NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_spawned_from_src    ON edge_kenkyusha_spawned_from (src)`.execute(db);
  await sql`CREATE INDEX idx_kenkyusha_spawned_from_reason ON edge_kenkyusha_spawned_from (split_reason, depth)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_kenkyusha_spawned_from`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kenkyusha_contradicts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kenkyusha_supports`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_submission`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_evidence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_hypothesis`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_frontier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kenkyusha_discipline`.execute(db);
}
