import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_saikin_signal — novel environmental signals detected by bacteria probe
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saikin_signal (
      vertex_id        VARCHAR PRIMARY KEY,
      record_id        VARCHAR NOT NULL,
      owner_did        VARCHAR NOT NULL,
      label            VARCHAR NOT NULL DEFAULT 'saikin_signal',
      status           VARCHAR NOT NULL DEFAULT 'unprocessed',
      stream_id        VARCHAR NOT NULL DEFAULT '',
      agent_did        VARCHAR NOT NULL DEFAULT '',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      input_kind       VARCHAR NOT NULL DEFAULT 'text',
      raw_ref          VARCHAR NOT NULL DEFAULT '',
      signal_hash      VARCHAR NOT NULL DEFAULT '',
      probe_source     VARCHAR NOT NULL DEFAULT '',
      transferred_at   TIMESTAMP WITH TIME ZONE
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_saikin_signal_status ON vertex_saikin_signal (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_saikin_signal_hash ON vertex_saikin_signal (signal_hash)`.execute(db);

  // vertex_saikin_colony — cooperative colony of related signals (biofilm)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_saikin_colony (
      vertex_id        VARCHAR PRIMARY KEY,
      record_id        VARCHAR NOT NULL,
      owner_did        VARCHAR NOT NULL,
      label            VARCHAR NOT NULL DEFAULT 'saikin_colony',
      status           VARCHAR NOT NULL DEFAULT 'active',
      stream_id        VARCHAR NOT NULL DEFAULT '',
      agent_did        VARCHAR NOT NULL DEFAULT '',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      colony_label     VARCHAR NOT NULL DEFAULT '',
      member_count     INT NOT NULL DEFAULT 0,
      formed_at        TIMESTAMP WITH TIME ZONE NOT NULL,
      lysed_at         TIMESTAMP WITH TIME ZONE
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_saikin_colony_status ON vertex_saikin_colony (status)`.execute(db);

  // edge_saikin_transfer — HGT-style signal transfer between actor namespaces
  await sql`
    CREATE TABLE IF NOT EXISTS edge_saikin_transfer (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      relation_kind     VARCHAR NOT NULL DEFAULT 'saikin_transfer',
      value_json        VARCHAR NOT NULL DEFAULT '{}',
      created_at        TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at        TIMESTAMP WITH TIME ZONE NOT NULL,
      owner_did         VARCHAR NOT NULL,
      sensitivity_ord   INT NOT NULL DEFAULT 0,
      signal_id         VARCHAR NOT NULL DEFAULT '',
      target_actor_did  VARCHAR NOT NULL DEFAULT '',
      transfer_kind     VARCHAR NOT NULL DEFAULT 'horizontal',
      transferred_at    TIMESTAMP WITH TIME ZONE NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_saikin_transfer_src ON edge_saikin_transfer (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_saikin_transfer_signal ON edge_saikin_transfer (signal_id)`.execute(db);

  // edge_saikin_member — colony membership edges
  await sql`
    CREATE TABLE IF NOT EXISTS edge_saikin_member (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR NOT NULL,
      dst_vid          VARCHAR NOT NULL,
      relation_kind    VARCHAR NOT NULL DEFAULT 'saikin_member',
      value_json       VARCHAR NOT NULL DEFAULT '{}',
      created_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      updated_at       TIMESTAMP WITH TIME ZONE NOT NULL,
      owner_did        VARCHAR NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 0,
      colony_id        VARCHAR NOT NULL DEFAULT '',
      signal_id        VARCHAR NOT NULL DEFAULT '',
      joined_at        TIMESTAMP WITH TIME ZONE NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_saikin_member_colony ON edge_saikin_member (colony_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_saikin_member`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_saikin_transfer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_saikin_colony`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_saikin_signal`.execute(db);
}
