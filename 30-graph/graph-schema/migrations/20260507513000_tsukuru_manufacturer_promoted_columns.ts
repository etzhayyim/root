import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS slug VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS legal_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS country_iso3 VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS category VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS industry_code VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS verification_tier VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS risk_tier VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS onboarding_status VARCHAR`.execute(db);

  await sql`
    UPDATE vertex_tsukuru_manufacturer
    SET
      did = coalesce(nullif(did, ''), value_json::jsonb ->> 'did', vertex_id),
      slug = coalesce(nullif(slug, ''), value_json::jsonb ->> 'slug'),
      legal_name = coalesce(nullif(legal_name, ''), value_json::jsonb ->> 'legalName'),
      country_iso3 = coalesce(nullif(country_iso3, ''), value_json::jsonb ->> 'countryIso3'),
      category = coalesce(nullif(category, ''), value_json::jsonb ->> 'category'),
      industry_code = coalesce(nullif(industry_code, ''), value_json::jsonb ->> 'industryCode'),
      verification_tier = coalesce(nullif(verification_tier, ''), value_json::jsonb ->> 'verificationTier'),
      risk_tier = coalesce(nullif(risk_tier, ''), value_json::jsonb ->> 'riskTier'),
      onboarding_status = coalesce(nullif(onboarding_status, ''), value_json::jsonb ->> 'onboardingStatus')
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_country_category_promoted
      ON vertex_tsukuru_manufacturer (country_iso3, category)
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_did ON vertex_tsukuru_manufacturer (did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_slug ON vertex_tsukuru_manufacturer (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_industry_code ON vertex_tsukuru_manufacturer (industry_code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_risk_tier ON vertex_tsukuru_manufacturer (risk_tier)`.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_onboarding_tier
      ON vertex_tsukuru_manufacturer (onboarding_status, verification_tier)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_manufacturer_industry_counts AS
    SELECT industry_code, risk_tier, onboarding_status, count(*) AS cnt
    FROM vertex_tsukuru_manufacturer
    GROUP BY industry_code, risk_tier, onboarding_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_manufacturer_industry_counts`.execute(db);
}
