import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * vertex_yabai_* tables for Risk Intelligence (AML/CTI) app.
 *
 * Prior to this migration yabai T3 writes flowed via PDS createRecord but
 * reads returned [] because no vertex tables existed. The graph-worker
 * convention fallback (`com.etzhayyim.apps.yabai.{entity}` → `vertex_yabai_{snake(entity)}`)
 * now has landing tables.
 *
 * Columns match fields emitted by
 *   60-apps/etzhayyim-project-yabai/appview/etzhayyim-wasm-yabai-y8b41k0x/src/app.ts
 * plus extended fields from 1400+ baseline JSON-LD records in `content/`.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_entity (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      entity_id         VARCHAR,
      entity_type       VARCHAR,
      name              VARCHAR,
      value             VARCHAR,
      canonical_name    VARCHAR,
      aliases           VARCHAR,
      source            VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_evidence (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,
      evidence_id         VARCHAR,
      entity_id           VARCHAR,
      category            VARCHAR,
      confidence          DOUBLE PRECISION,
      severity            BIGINT,
      probability         DOUBLE PRECISION,
      source              VARCHAR,
      source_reliability  VARCHAR,
      jurisdiction        VARCHAR,
      summary             VARCHAR,
      description         VARCHAR,
      verification_id     VARCHAR,
      occurred_at         VARCHAR,
      created_at          VARCHAR,
      org_id              VARCHAR,
      user_id             VARCHAR,
      actor_id            VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_risk (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      entity_id             VARCHAR,
      entity_type           VARCHAR,
      entity_name           VARCHAR,
      entity_value          VARCHAR,
      risk_score            DOUBLE PRECISION,
      well_becoming_score   DOUBLE PRECISION,
      penalty               DOUBLE PRECISION,
      penalty_score         DOUBLE PRECISION,
      wb_score              DOUBLE PRECISION,
      info_risk             DOUBLE PRECISION,
      level                 VARCHAR,
      evidence_count        BIGINT,
      categories            VARCHAR,
      scored_at             VARCHAR,
      org_id                VARCHAR,
      user_id               VARCHAR,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_alert (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      alert_id          VARCHAR,
      entity_id         VARCHAR,
      entity_type       VARCHAR,
      entity_name       VARCHAR,
      risk_score        DOUBLE PRECISION,
      alert_level       VARCHAR,
      status            VARCHAR,
      categories        VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_enforcement (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      enforcement_id    VARCHAR,
      action            VARCHAR,
      deny_count        BIGINT,
      challenge_count   BIGINT,
      monitor_count     BIGINT,
      deny_ips          VARCHAR,
      challenge_ips     VARCHAR,
      monitor_ips       VARCHAR,
      synced_at         VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  // vertex_yabai_flag — also written by PDS middleware/rate-limit.ts,
  // hence `did` + `label` columns for that code path.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_flag (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      did               VARCHAR,
      label             VARCHAR,
      node_id           VARCHAR,
      account_did       VARCHAR,
      entity_vid        VARCHAR,
      entity_type       VARCHAR,
      flag_type         VARCHAR,
      severity          VARCHAR,
      confidence        DOUBLE PRECISION,
      tlp               VARCHAR,
      notes             VARCHAR,
      tags              VARCHAR,
      expires_at        VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_intel_access_log (
      vertex_id                       VARCHAR PRIMARY KEY,
      _seq                            BIGINT,
      created_date                    DATE,
      sensitivity_ord                 BIGINT,
      owner_did                       VARCHAR,
      rkey                            VARCHAR,
      repo                            VARCHAR,
      access_id                       VARCHAR,
      email                           VARCHAR,
      normalized_email                VARCHAR,
      ip                              VARCHAR,
      ip_did                          VARCHAR,
      user_agent                      VARCHAR,
      path                            VARCHAR,
      method                          VARCHAR,
      request_id                      VARCHAR,
      decision                        VARCHAR,
      deny_reasons                    VARCHAR,
      linked_registration_ban_rkey    VARCHAR,
      registration_prohibited         BOOLEAN,
      yabai_score                     DOUBLE PRECISION,
      risk_level                      VARCHAR,
      scored_entity_type              VARCHAR,
      scored_entity_id                VARCHAR,
      created_at                      VARCHAR,
      org_id                          VARCHAR,
      user_id                         VARCHAR,
      actor_id                        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yabai_registration_ban (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      email             VARCHAR,
      normalized_email  VARCHAR,
      reason            VARCHAR,
      val_json          VARCHAR,
      banned_at         VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_yabai_registration_ban`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_intel_access_log`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_flag`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_enforcement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_alert`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_risk`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_evidence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yabai_entity`.execute(db);
}
