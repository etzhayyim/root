import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604270330 — Japan My Number electronic application and PMH graph extension.
// tier: B for runtime application/medical request vertices.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_electronic_application (
      vertex_id                  varchar PRIMARY KEY,
      _seq                       bigint,
      created_date               date,
      sensitivity_ord            int,
      owner_did                  varchar,
      person_ref                 varchar NOT NULL,
      requester_agency           varchar NOT NULL,
      procedure_code             varchar NOT NULL,
      purpose_code               varchar NOT NULL,
      application_payload_hash   varchar NOT NULL,
      status                     varchar NOT NULL,
      external_reference         varchar,
      submitted_at               varchar NOT NULL,
      updated_at                 varchar NOT NULL,
      org_id                     varchar,
      user_id                    varchar,
      actor_id                   varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_jpn_mynumber_medical_info_request (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      person_ref         varchar NOT NULL,
      requester_agency   varchar NOT NULL,
      purpose_code       varchar NOT NULL,
      dataset_code       varchar NOT NULL,
      consent_id         varchar,
      status             varchar NOT NULL,
      response_ref       varchar,
      requested_at       varchar NOT NULL,
      updated_at         varchar NOT NULL,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_open_jpn_mynumber_request_consent (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      from_vertex_id   varchar NOT NULL,
      to_vertex_id     varchar NOT NULL,
      edge_type        varchar NOT NULL,
      created_at       varchar NOT NULL,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_jpn_mynumber_electronic_application_status AS
    SELECT
      vertex_id AS application_id,
      person_ref,
      requester_agency,
      procedure_code,
      purpose_code,
      application_payload_hash,
      status,
      external_reference,
      submitted_at,
      updated_at
    FROM vertex_open_jpn_mynumber_electronic_application
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_jpn_mynumber_medical_info_status AS
    SELECT
      vertex_id AS medical_request_id,
      person_ref,
      requester_agency,
      purpose_code,
      dataset_code,
      consent_id,
      status,
      response_ref,
      requested_at,
      updated_at
    FROM vertex_open_jpn_mynumber_medical_info_request
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_jpn_mynumber_medical_info_status`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_jpn_mynumber_electronic_application_status`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_jpn_mynumber_request_consent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_jpn_mynumber_medical_info_request`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_jpn_mynumber_electronic_application`.execute(db);
}
