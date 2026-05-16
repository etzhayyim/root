import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0037: IP cluster (patent / trademark / copyright) vertex + edge tables.
 *
 * 3 actor domains each get a dedicated vertex table with P10v2 promoted columns
 * (typed instead of JSON props). Edge tables model cross-links:
 *   - edge_patent_cites                 patent → patent  (backward/forward/NPL)
 *   - edge_family_member         family  → patent (INPADOC simple/extended/docdb)
 *   - edge_classified_as         patent/trademark → ipc_class/nice_class (system)
 *   - edge_owned_by              patent/trademark/work → legal_entity/natural_person
 *   - edge_authored_by           work → natural_person (order + role)
 *
 * Drives: 20-actors/{patent,trademark,copyright}/actor-manifest.jsonld SQL pipelines.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_patent ──────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_patent (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      did               VARCHAR,
      status            VARCHAR,
      jurisdiction      VARCHAR,
      app_number        VARCHAR,
      pub_number        VARCHAR,
      grant_number      VARCHAR,
      title             VARCHAR,
      abstract          VARCHAR,
      ipc_codes         VARCHAR,
      cpc_codes         VARCHAR,
      filed_at          VARCHAR,
      published_at      VARCHAR,
      granted_at        VARCHAR,
      source_url        VARCHAR,
      source_did        VARCHAR,
      collected_at      VARCHAR
    )
  `.execute(db);

  // ── vertex_trademark ───────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_trademark (
      vertex_id               VARCHAR PRIMARY KEY,
      _seq                    BIGINT,
      created_date            DATE,
      sensitivity_ord         BIGINT,
      owner_did               VARCHAR,
      rkey                    VARCHAR,
      repo                    VARCHAR,
      did                     VARCHAR,
      status                  VARCHAR,
      jurisdiction            VARCHAR,
      reg_number              VARCHAR,
      app_number              VARCHAR,
      mark                    VARCHAR,
      mark_type               VARCHAR,
      nice_classes            VARCHAR,
      vienna_codes            VARCHAR,
      filed_at                VARCHAR,
      registered_at           VARCHAR,
      expires_at              VARCHAR,
      madrid_intl_reg_number  VARCHAR,
      source_url              VARCHAR,
      source_did              VARCHAR,
      collected_at            VARCHAR
    )
  `.execute(db);

  // ── vertex_work (copyright) ────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_work (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      status               VARCHAR,
      kind                 VARCHAR,
      title                VARCHAR,
      publisher_did        VARCHAR,
      author_dids          VARCHAR,
      doi                  VARCHAR,
      isbn13               VARCHAR,
      isrc                 VARCHAR,
      iswc                 VARCHAR,
      registry             VARCHAR,
      reg_id               VARCHAR,
      license              VARCHAR,
      first_published_at   VARCHAR,
      jurisdiction         VARCHAR,
      berne_automatic      BOOLEAN,
      source_url           VARCHAR,
      source_did           VARCHAR,
      collected_at         VARCHAR
    )
  `.execute(db);

  // ── edge tables ────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_patent_cites (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      kind            VARCHAR,
      category        VARCHAR,
      examiner_did    VARCHAR,
      cited_at        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_family_member (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      kind            VARCHAR,
      added_at        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_classified_as (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      system          VARCHAR,
      code            VARCHAR,
      attached_at     VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_owned_by (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      role            VARCHAR,
      linked_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_authored_by (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      author_order    BIGINT,
      role            VARCHAR,
      linked_at       VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_authored_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_owned_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_classified_as`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_family_member`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_patent_cites`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_work`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_trademark`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_patent`.execute(db);
}
