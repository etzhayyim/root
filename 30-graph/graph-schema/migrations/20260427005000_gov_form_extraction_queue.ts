import type { Kysely } from "kysely";
import { sql } from "kysely";

// Queue for turning discovered local-government form documents and service
// pages into language-aware structured form/procedure extraction work.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gov_form_extraction_task (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      country_iso3           varchar NOT NULL,
      admin1_name            varchar,
      municipality_code      varchar,
      municipality_name      varchar,
      procedure_variant_id   varchar NOT NULL,
      procedure_key          varchar,
      base_procedure_key     varchar,
      source_url             varchar NOT NULL,
      source_kind            varchar NOT NULL,
      source_text            varchar,
      locale                 varchar NOT NULL,
      language_name          varchar,
      script_tag             varchar,
      language_status        varchar,
      task_kind              varchar NOT NULL,
      task_status            varchar NOT NULL,
      priority               int,
      descriptor_json        varchar,
      last_verified_at       varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_form_extraction_queue_coverage AS
    SELECT
      country_iso3,
      admin1_name,
      base_procedure_key,
      locale,
      task_kind,
      task_status,
      COUNT(*) AS task_count,
      COUNT(DISTINCT municipality_code) AS municipality_count,
      COUNT(DISTINCT procedure_variant_id) AS procedure_count
    FROM vertex_gov_form_extraction_task
    GROUP BY country_iso3, admin1_name, base_procedure_key, locale, task_kind, task_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_form_extraction_queue_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_form_extraction_task`.execute(db);
}
