import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_nokyo_* tables for Nokyo (JA 農業協同組合) actor.
 *
 * 9 landing tables matching AT Record lexicons at
 *   00-contracts/lexicons/ai/gftd/apps/nokyo/*.json
 *
 * Promoted-column / typed / GraphAr-native. RLS 3-col (owner_did + rkey + repo)
 * + created_date + sensitivity_ord + actor_id follow house convention.
 *
 * kyosaiPolicy.beneficiary_enc carries Signal-encrypted ciphertext
 * (signal:v1:{ct}) — plaintext PII not persisted (ADR-0018, PII Tier 3).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_member (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      member_id         VARCHAR,
      coop_path         VARCHAR,
      member_type       VARCHAR,
      full_name         VARCHAR,
      pref_code         VARCHAR,
      joined_date       DATE,
      investment_shares BIGINT,
      created_at        VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_farm (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      farm_id           VARCHAR,
      member_id         VARCHAR,
      land_use          VARCHAR,
      area_m2           DOUBLE PRECISION,
      pref_code         VARCHAR,
      city_code         VARCHAR,
      parcel_number     VARCHAR,
      latitude          DOUBLE PRECISION,
      longitude         DOUBLE PRECISION,
      soil_type         VARCHAR,
      created_at        VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_crop_plan (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,
      crop_plan_id        VARCHAR,
      member_id           VARCHAR,
      farm_id             VARCHAR,
      coop_path           VARCHAR,
      pref_code           VARCHAR,
      crop_name           VARCHAR,
      crop_category       VARCHAR,
      season              VARCHAR,
      planting_date       DATE,
      harvest_date        DATE,
      expected_yield_kg   DOUBLE PRECISION,
      fertilizer_plan     VARCHAR,
      pesticide_plan      VARCHAR,
      quota_kg            DOUBLE PRECISION,
      created_at          VARCHAR,
      actor_id            VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_purchase_order (
      vertex_id                 VARCHAR PRIMARY KEY,
      _seq                      BIGINT,
      created_date              DATE,
      sensitivity_ord           BIGINT,
      owner_did                 VARCHAR,
      rkey                      VARCHAR,
      repo                      VARCHAR,
      order_id                  VARCHAR,
      member_id                 VARCHAR,
      coop_path                 VARCHAR,
      item_code                 VARCHAR,
      item_name                 VARCHAR,
      category                  VARCHAR,
      quantity                  DOUBLE PRECISION,
      unit                      VARCHAR,
      unit_price_jpy            DOUBLE PRECISION,
      requested_delivery_date   DATE,
      status                    VARCHAR,
      created_at                VARCHAR,
      actor_id                  VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_sale_lot (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      lot_id            VARCHAR,
      crop_plan_id      VARCHAR,
      member_id         VARCHAR,
      coop_path         VARCHAR,
      product_name      VARCHAR,
      grade             VARCHAR,
      quantity_kg       DOUBLE PRECISION,
      harvest_date      DATE,
      shipped_date      DATE,
      destination       VARCHAR,
      buyer_name        VARCHAR,
      price_jpy_per_kg  DOUBLE PRECISION,
      created_at        VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_kyosai_policy (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      policy_id             VARCHAR,
      member_id             VARCHAR,
      coop_path             VARCHAR,
      product_type          VARCHAR,
      product_name          VARCHAR,
      effective_date        DATE,
      expiration_date       DATE,
      premium_jpy_monthly   DOUBLE PRECISION,
      sum_insured_jpy       DOUBLE PRECISION,
      beneficiary_enc       VARCHAR,
      status                VARCHAR,
      created_at            VARCHAR,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_loan_application (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,
      application_id      VARCHAR,
      member_id           VARCHAR,
      coop_path           VARCHAR,
      loan_type           VARCHAR,
      principal_jpy       DOUBLE PRECISION,
      term_months         BIGINT,
      interest_rate_bps   BIGINT,
      purpose             VARCHAR,
      collateral          VARCHAR,
      status              VARCHAR,
      submitted_date      DATE,
      created_at          VARCHAR,
      actor_id            VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_advisory_note (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      crop_plan_id      VARCHAR,
      coop_path         VARCHAR,
      verdict           VARCHAR,
      advisory_text     VARCHAR,
      flagged_risks     VARCHAR,
      advisor_did       VARCHAR,
      reviewed_by       VARCHAR,
      created_at        VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_nokyo_direct_sales_item (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      item_id           VARCHAR,
      member_id         VARCHAR,
      coop_path         VARCHAR,
      market_path       VARCHAR,
      product_name      VARCHAR,
      category          VARCHAR,
      price_jpy         DOUBLE PRECISION,
      quantity          BIGINT,
      unit              VARCHAR,
      harvest_date      DATE,
      displayed_at      VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      actor_id          VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_nokyo_direct_sales_item`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_advisory_note`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_loan_application`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_kyosai_policy`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_sale_lot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_purchase_order`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_crop_plan`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_farm`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_nokyo_member`.execute(db);
}
