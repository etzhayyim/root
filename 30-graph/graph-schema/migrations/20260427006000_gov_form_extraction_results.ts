import type { Kysely } from "kysely";
import { sql } from "kysely";

// Results produced by local-government form extraction workers. The result is
// intentionally evidence-first: it records observed page/document metadata,
// inferred fields/documents, and confidence without claiming legal finality.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gov_form_extraction_result (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      task_id                varchar NOT NULL,
      country_iso3           varchar NOT NULL,
      admin1_name            varchar,
      municipality_code      varchar,
      municipality_name      varchar,
      procedure_variant_id   varchar,
      procedure_key          varchar,
      base_procedure_key     varchar,
      source_url             varchar NOT NULL,
      source_kind            varchar,
      locale                 varchar,
      language_name          varchar,
      task_kind              varchar,
      extraction_status      varchar NOT NULL,
      http_status            int,
      content_type           varchar,
      final_url              varchar,
      field_keys             varchar,
      required_doc_keys      varchar,
      action_urls            varchar,
      confidence_score       double precision,
      descriptor_json        varchar,
      extracted_at           varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_form_extraction_result_coverage AS
    SELECT
      country_iso3,
      admin1_name,
      base_procedure_key,
      locale,
      task_kind,
      extraction_status,
      COUNT(*) AS result_count,
      COUNT(DISTINCT municipality_code) AS municipality_count,
      COUNT(DISTINCT procedure_variant_id) AS procedure_count
    FROM vertex_gov_form_extraction_result
    GROUP BY country_iso3, admin1_name, base_procedure_key, locale, task_kind, extraction_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_form_extraction_result_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_form_extraction_result`.execute(db);
}
