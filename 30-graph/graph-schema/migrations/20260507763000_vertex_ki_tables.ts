import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_ki_absorb — xylem input: absorbed processed signals
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ki_absorb (
      vertex_id        VARCHAR PRIMARY KEY,
      record_id        VARCHAR NOT NULL,
      owner_did        VARCHAR NOT NULL,
      label            VARCHAR NOT NULL DEFAULT 'ki_absorb',
      status           VARCHAR NOT NULL DEFAULT 'absorbed',
      stream_id        VARCHAR NOT NULL DEFAULT '',
      agent_did        VARCHAR NOT NULL DEFAULT '',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      source_vertex_id VARCHAR NOT NULL DEFAULT '',
      input_kind       VARCHAR NOT NULL DEFAULT 'text',
      content_hash     VARCHAR NOT NULL DEFAULT '',
      absorbed_at      TIMESTAMP WITH TIME ZONE NOT NULL,
      synthesized_at   TIMESTAMP WITH TIME ZONE
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_ki_absorb_status ON vertex_ki_absorb (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ki_absorb_hash ON vertex_ki_absorb (content_hash)`.execute(db);

  // vertex_ki_artifact — synthesized knowledge artifact (phloem output)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ki_artifact (
      vertex_id        VARCHAR PRIMARY KEY,
      record_id        VARCHAR NOT NULL,
      owner_did        VARCHAR NOT NULL,
      label            VARCHAR NOT NULL DEFAULT 'ki_artifact',
      status           VARCHAR NOT NULL DEFAULT 'synthesized',
      stream_id        VARCHAR NOT NULL DEFAULT '',
      agent_did        VARCHAR NOT NULL DEFAULT '',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      absorb_id        VARCHAR NOT NULL DEFAULT '',
      artifact_kind    VARCHAR NOT NULL DEFAULT 'insight',
      synthesis        VARCHAR NOT NULL DEFAULT '',
      confidence       DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      artifact_hash    VARCHAR NOT NULL DEFAULT '',
      bloomed_at       TIMESTAMP WITH TIME ZONE
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_ki_artifact_status ON vertex_ki_artifact (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ki_artifact_kind ON vertex_ki_artifact (artifact_kind)`.execute(db);

  // vertex_ki_ring — growth ring (versioned knowledge checkpoint / 年輪)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ki_ring (
      vertex_id        VARCHAR PRIMARY KEY,
      record_id        VARCHAR NOT NULL,
      owner_did        VARCHAR NOT NULL,
      label            VARCHAR NOT NULL DEFAULT 'ki_ring',
      status           VARCHAR NOT NULL DEFAULT 'active',
      stream_id        VARCHAR NOT NULL DEFAULT '',
      agent_did        VARCHAR NOT NULL DEFAULT '',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      period           VARCHAR NOT NULL DEFAULT 'P1D',
      snapshot_count   INT NOT NULL DEFAULT 0,
      ring_at          TIMESTAMP WITH TIME ZONE NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_ki_ring_at ON vertex_ki_ring (ring_at)`.execute(db);

  // edge_ki_vascular — vascular flow edge (absorb → artifact; artifact → ring)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_ki_vascular (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR NOT NULL,
      dst_vid          VARCHAR NOT NULL,
      relation_kind    VARCHAR NOT NULL DEFAULT 'ki_vascular',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      owner_did        VARCHAR NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      flow_kind        VARCHAR NOT NULL DEFAULT 'xylem',
      flow_at          TIMESTAMP WITH TIME ZONE NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_ki_vascular_src ON edge_ki_vascular (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ki_vascular_kind ON edge_ki_vascular (flow_kind)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_ki_vascular`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ki_ring`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ki_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ki_absorb`.execute(db);
}
