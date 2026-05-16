// tier: C
import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ir_company (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT NOT NULL DEFAULT 1,
      owner_did        VARCHAR,
      lei              VARCHAR,
      edinet_code      VARCHAR,
      securities_code  VARCHAR,
      ticker           VARCHAR,
      exchange         VARCHAR,
      company_name     VARCHAR NOT NULL,
      company_name_ja  VARCHAR,
      ir_url           VARCHAR,
      ir_rss_url       VARCHAR,
      ir_host          VARCHAR,
      ir_status        VARCHAR NOT NULL DEFAULT 'active',
      ir_last_crawled_at VARCHAR,
      ir_crawl_interval_hours BIGINT NOT NULL DEFAULT 6,
      country_code     VARCHAR,
      created_at       VARCHAR NOT NULL,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ir_scraper_run (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT NOT NULL DEFAULT 1,
      owner_did            VARCHAR,
      company_vertex_id    VARCHAR,
      lei                  VARCHAR,
      ir_url               VARCHAR,
      ir_rss_url           VARCHAR,
      status               VARCHAR NOT NULL DEFAULT 'queued',
      method               VARCHAR,
      articles_found       BIGINT,
      articles_inserted    BIGINT,
      error_message        VARCHAR,
      queued_at            VARCHAR,
      started_at           VARCHAR,
      completed_at         VARCHAR,
      created_at           VARCHAR NOT NULL,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ir_pressrelease (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT NOT NULL DEFAULT 1,
      owner_did            VARCHAR,
      company_vertex_id    VARCHAR,
      lei                  VARCHAR,
      title                VARCHAR,
      url                  VARCHAR,
      published_at         VARCHAR,
      body_snippet         VARCHAR,
      lang                 VARCHAR,
      kind                 VARCHAR NOT NULL DEFAULT 'other',
      method               VARCHAR,
      intel_subject_vid    VARCHAR,
      crawled_at           VARCHAR NOT NULL,
      created_at           VARCHAR NOT NULL,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_ir_pressrelease`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ir_scraper_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ir_company`.execute(db);
}
