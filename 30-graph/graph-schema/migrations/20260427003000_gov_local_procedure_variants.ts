import type { Kysely } from "kysely";
import { sql } from "kysely";

// Local procedure/form/language variation layer.
// This complements vertex_gov_municipality and vertex_ind_efiling_format:
// national formats remain canonical, while state/municipality differences
// are represented as override rows with source URLs and language tags.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gov_procedure_variant (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      procedure_key          varchar NOT NULL,
      base_procedure_key     varchar,
      country_iso3           varchar NOT NULL,
      admin1_name            varchar,
      municipality_code      varchar,
      municipality_name      varchar,
      locality_scope         varchar NOT NULL,
      actor_did              varchar,
      gov_org_key            varchar,
      form_key               varchar,
      format_key             varchar,
      language_tags          varchar,
      script_tags            varchar,
      required_doc_keys      varchar,
      fee_min_minor          bigint,
      fee_max_minor          bigint,
      fee_currency           varchar,
      sla_min_days           int,
      sla_max_days           int,
      portal_url             varchar,
      source_url             varchar,
      source_kind            varchar,
      variant_status         varchar NOT NULL,
      descriptor_json        varchar,
      last_verified_at       varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gov_form_language_variant (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      form_key               varchar NOT NULL,
      format_key             varchar,
      country_iso3           varchar NOT NULL,
      admin1_name            varchar,
      municipality_code      varchar,
      locale                 varchar NOT NULL,
      language_name          varchar,
      script_tag             varchar,
      translation_status     varchar NOT NULL,
      source_url             varchar,
      descriptor_json        varchar,
      last_verified_at       varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gov_local_variation_gap (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      country_iso3           varchar NOT NULL,
      admin1_name            varchar,
      municipality_code      varchar,
      municipality_name      varchar,
      site_url               varchar,
      gap_kind               varchar NOT NULL,
      gap_status             varchar NOT NULL,
      reason                 varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    DELETE FROM vertex_gov_procedure_variant
    WHERE country_iso3 = 'IND'
      AND procedure_key IN (
        'ind.itr1.fileReturn',
        'ind.itr1.prefill',
        'ind.gstr3b.fileReturn',
        'ind.epfo.submitMonthlyEcr',
        'ind.esic.submitMonthlyContribution'
      )
  `.execute(db);

  await sql`
    INSERT INTO vertex_gov_procedure_variant (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      procedure_key, base_procedure_key, country_iso3, locality_scope,
      actor_did, form_key, format_key, language_tags, script_tags,
      source_url, source_kind, variant_status, descriptor_json,
      last_verified_at, created_at, org_id, user_id, actor_id
    )
    SELECT
      CONCAT('at://', actor_did, '/com.etzhayyim.apps.gov.procedureVariant/', format_key),
      20260427003000 + ROW_NUMBER() OVER (ORDER BY format_key),
      DATE '2026-04-27',
      2,
      actor_did,
      CASE
        WHEN format_key = 'ind.itr1.eriSubmitFlow.v1_1' THEN 'ind.itr1.fileReturn'
        WHEN format_key = 'ind.itr1.prefillSchema.v6_5' THEN 'ind.itr1.prefill'
        WHEN format_key = 'ind.gstr3b.gspFramework.v3' THEN 'ind.gstr3b.fileReturn'
        WHEN format_key = 'ind.epfo.ecrFile.forEmployers' THEN 'ind.epfo.submitMonthlyEcr'
        WHEN format_key = 'ind.esic.monthlyContribution.portal' THEN 'ind.esic.submitMonthlyContribution'
        ELSE format_key
      END,
      format_key,
      'IND',
      'national',
      actor_did,
      CASE
        WHEN jurisdiction = 'itr1' THEN 'itr1-form-v1'
        WHEN jurisdiction = 'gstr3b' THEN 'gstr3b-form-v1'
        WHEN jurisdiction = 'epfo' THEN 'epfo-ecr-form-v1'
        WHEN jurisdiction = 'esic' THEN 'esic-monthly-form-v1'
        ELSE ''
      END,
      format_key,
      'en',
      'Latn',
      official_source_url,
      format_kind,
      status,
      descriptor_json,
      last_verified_at,
      '2026-04-27T00:30:00Z',
      'ind',
      'system',
      'sys.gov.local.variant'
    FROM vertex_ind_efiling_format
  `.execute(db);

  await sql`
    DELETE FROM vertex_gov_form_language_variant
    WHERE country_iso3 = 'IND'
      AND form_key IN ('itr1-form-v1', 'gstr3b-form-v1', 'epfo-ecr-form-v1', 'esic-monthly-form-v1')
  `.execute(db);

  await sql`
    INSERT INTO vertex_gov_form_language_variant (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      form_key, format_key, country_iso3, locale, language_name, script_tag,
      translation_status, source_url, descriptor_json, last_verified_at,
      created_at, org_id, user_id, actor_id
    )
    SELECT
      CONCAT('at://', actor_did, '/com.etzhayyim.apps.gov.formLanguageVariant/', form_key, '-en'),
      20260427003100 + ROW_NUMBER() OVER (ORDER BY form_key),
      DATE '2026-04-27',
      2,
      actor_did,
      form_key,
      format_key,
      'IND',
      'en-IN',
      'English',
      'Latn',
      'source_available',
      source_url,
      CONCAT('{"source":"', source_kind, '","scope":"national"}'),
      last_verified_at,
      '2026-04-27T00:31:00Z',
      'ind',
      'system',
      'sys.gov.local.variant'
    FROM vertex_gov_procedure_variant
    WHERE country_iso3 = 'IND'
      AND locality_scope = 'national'
      AND form_key IS NOT NULL
      AND form_key <> ''
  `.execute(db);

  await sql`
    DELETE FROM vertex_gov_local_variation_gap
    WHERE country_iso3 = 'IND'
  `.execute(db);

  await sql`
    INSERT INTO vertex_gov_local_variation_gap (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      country_iso3, admin1_name, municipality_code, municipality_name, site_url,
      gap_kind, gap_status, reason, created_at, org_id, user_id, actor_id
    )
    SELECT
      CONCAT('at://did:web:gov.etzhayyim.com/com.etzhayyim.apps.gov.localVariationGap/ind-', municipality_code),
      20260427003200 + ROW_NUMBER() OVER (ORDER BY municipality_code),
      DATE '2026-04-27',
      1,
      COALESCE("actorDid", 'did:web:gov.etzhayyim.com'),
      'IND',
      prefecture,
      municipality_code,
      city,
      site_url,
      'procedure_form_language',
      'needs_official_source',
      'Municipality exists in vertex_gov_municipality, but per-procedure form/language overrides are not yet sourced.',
      '2026-04-27T00:32:00Z',
      'ind',
      'system',
      'sys.gov.local.variant'
    FROM vertex_gov_municipality
    WHERE municipality_code IS NOT NULL
      AND prefecture IS NOT NULL
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_local_variation_coverage AS
    SELECT
      country_iso3,
      admin1_name,
      locality_scope,
      COUNT(*) AS variant_count,
      COUNT(DISTINCT municipality_code) AS municipality_count,
      COUNT(DISTINCT form_key) AS form_count,
      COUNT(DISTINCT format_key) AS format_count,
      COUNT(DISTINCT language_tags) AS language_variant_count
    FROM vertex_gov_procedure_variant
    GROUP BY country_iso3, admin1_name, locality_scope
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_local_variation_gap AS
    SELECT
      country_iso3,
      admin1_name,
      gap_kind,
      gap_status,
      COUNT(*) AS municipality_count
    FROM vertex_gov_local_variation_gap
    GROUP BY country_iso3, admin1_name, gap_kind, gap_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_local_variation_gap`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_local_variation_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_local_variation_gap`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_form_language_variant`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gov_procedure_variant`.execute(db);
}
