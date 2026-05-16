import type { Kysely } from "kysely";
import { sql } from "kysely";

// Restricted/public Demining AppView graph store.
// Public rows mirror AT record semantics; Tier 3 rows replace edge D1 storage.
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_atrecord_demining_public (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT NOT NULL,
      owner_did        VARCHAR NOT NULL,
      record_type      VARCHAR NOT NULL,
      record_id        VARCHAR NOT NULL,
      collection       VARCHAR NOT NULL,
      record_json      VARCHAR NOT NULL,
      sensitivity_tier INTEGER NOT NULL,
      created_at       TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_demining_tier3_field (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      record_id            VARCHAR NOT NULL,
      record_type          VARCHAR NOT NULL,
      field_name           VARCHAR NOT NULL,
      field_value          VARCHAR NOT NULL,
      jurisdiction         VARCHAR,
      actor_did            VARCHAR NOT NULL,
      released             BOOLEAN NOT NULL,
      released_at          TIMESTAMPTZ,
      released_by_decision VARCHAR,
      created_at           TIMESTAMPTZ NOT NULL,
      updated_at           TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_atrecord_demining_tier3_audit (
      vertex_id    VARCHAR PRIMARY KEY,
      _seq         BIGINT NOT NULL,
      occurred_at  TIMESTAMPTZ NOT NULL,
      actor_did    VARCHAR NOT NULL,
      action       VARCHAR NOT NULL,
      record_id    VARCHAR,
      record_type  VARCHAR,
      field_name   VARCHAR,
      jurisdiction VARCHAR,
      reason       VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX idx_demining_public_type_seq ON vertex_atrecord_demining_public (record_type, _seq DESC)`.execute(db);
  await sql`CREATE INDEX idx_demining_public_record ON vertex_atrecord_demining_public (record_id)`.execute(db);
  await sql`CREATE INDEX idx_demining_tier3_record_field ON vertex_atrecord_demining_tier3_field (record_id, field_name)`.execute(db);
  await sql`CREATE INDEX idx_demining_tier3_audit_record ON vertex_atrecord_demining_tier3_audit (record_id, occurred_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_atrecord_demining_tier3_audit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_demining_tier3_field`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_atrecord_demining_public`.execute(db);
}
