import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0049 D4 — adr / legal-aid as BPMN-as-actor (ADR-0056).
// Adds the vertex tables their BPMN handlers write to.
//
// Tier (ADR-0040):
//   - vertex_adr_arbitrator: tier B (public arbitrator roster, same as judge/lawyer)
//   - vertex_adr_case: tier C (international arbitration confidentiality;
//     parties_enc / claim_amount_enc carry signal:v1: ciphertext, ADR-0018)
//   - vertex_legal_aid_office: tier B (public office directory)
//   - vertex_legal_aid_case: tier C (PII Tier 3, applicant identity hashed +
//     signal:v1: encrypted; ADR-0018 + ADR-0049 D5)

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_adr_arbitrator (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      arbitrator_did     varchar NOT NULL,
      full_name          varchar NOT NULL,
      institution        varchar NOT NULL,
      panel              varchar,
      nationality        varchar,
      languages_csv      varchar,
      expertise_csv      varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);
  await sql`CREATE INDEX idx_adr_arbitrator_did ON vertex_adr_arbitrator(arbitrator_did)`.execute(db);
  await sql`CREATE INDEX idx_adr_arbitrator_institution ON vertex_adr_arbitrator(institution)`.execute(db);

  await sql`
    CREATE TABLE vertex_adr_case (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      case_ref           varchar NOT NULL,
      institution        varchar NOT NULL,
      panel              varchar,
      seat               varchar,
      governing_law      varchar,
      parties_enc        varchar,
      claim_amount_enc   varchar,
      currency           varchar,
      status             varchar NOT NULL,
      opened_at          varchar,
      award_at           varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);
  await sql`CREATE INDEX idx_adr_case_institution ON vertex_adr_case(institution)`.execute(db);

  await sql`
    CREATE TABLE vertex_legal_aid_office (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      office_did         varchar NOT NULL,
      display_name       varchar NOT NULL,
      jurisdiction       varchar NOT NULL,
      office_type        varchar NOT NULL,
      address_locality   varchar,
      languages_csv      varchar,
      specialties_csv    varchar,
      intake_url         varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);
  await sql`CREATE INDEX idx_legal_aid_office_did ON vertex_legal_aid_office(office_did)`.execute(db);
  await sql`CREATE INDEX idx_legal_aid_office_jurisdiction ON vertex_legal_aid_office(jurisdiction)`.execute(db);

  await sql`
    CREATE TABLE vertex_legal_aid_case (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      office_did         varchar NOT NULL,
      applicant_hash     varchar NOT NULL,
      applicant_pii_enc  varchar,
      matter_area        varchar NOT NULL,
      income_bracket     varchar,
      language_code      varchar,
      intake_channel     varchar,
      opened_at          varchar NOT NULL,
      closed_at          varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);
  await sql`CREATE INDEX idx_legal_aid_case_office ON vertex_legal_aid_case(office_did)`.execute(db);
  await sql`CREATE INDEX idx_legal_aid_case_applicant ON vertex_legal_aid_case(applicant_hash)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_legal_aid_case`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_legal_aid_office`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_adr_case`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_adr_arbitrator`.execute(db);
}
