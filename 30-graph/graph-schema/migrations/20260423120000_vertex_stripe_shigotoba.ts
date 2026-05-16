import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A
// tier: B
// tier: C

/**
 * Stripe / Shigotoba typed read models.
 *
 * Purpose:
 * - Eliminate fallback reads from catch_all_vertex / vertex_repo_record JSON scans.
 * - Materialize app collections into dedicated vertex_* + edge_* + mv_* models.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // --- Auth ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_auth_account (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      org_id VARCHAR,
      handle VARCHAR,
      display_name VARCHAR,
      email VARCHAR,
      membership_plan VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auth_account_user_id ON vertex_auth_account (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auth_account_actor_id ON vertex_auth_account (actor_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auth_account_membership_plan ON vertex_auth_account (membership_plan)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auth_account_updated_at ON vertex_auth_account (updated_at)`.execute(db);

  // --- Shigotoba ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shigotoba_job_posting (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      title VARCHAR,
      company_name VARCHAR,
      company_id VARCHAR,
      location VARCHAR,
      country VARCHAR,
      city VARCHAR,
      employment_type VARCHAR,
      remote_type VARCHAR,
      min_salary_usd DOUBLE PRECISION,
      max_salary_usd DOUBLE PRECISION,
      tags_json VARCHAR,
      source_url VARCHAR,
      source VARCHAR,
      source_job_id VARCHAR,
      description VARCHAR,
      fetched_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_job_posting_id ON vertex_shigotoba_job_posting (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_job_posting_company_id ON vertex_shigotoba_job_posting (company_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_job_posting_actor_created ON vertex_shigotoba_job_posting (actor_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_job_posting_source ON vertex_shigotoba_job_posting (source)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shigotoba_company_profile (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      name VARCHAR,
      source VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_company_profile_id ON vertex_shigotoba_company_profile (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_company_profile_actor_name ON vertex_shigotoba_company_profile (actor_id, name)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_shigotoba_posting_company (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      posting_vid VARCHAR,
      company_vid VARCHAR,
      posting_id VARCHAR,
      company_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shigotoba_edge_posting_company ON edge_shigotoba_posting_company (posting_id, company_id)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_shigotoba_job_posting_count AS
    SELECT actor_id, source, count(*)::bigint AS cnt
    FROM vertex_shigotoba_job_posting
    GROUP BY actor_id, source
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_shigotoba_company_profile_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_shigotoba_company_profile
    GROUP BY actor_id
  `.execute(db);

  // --- Stripe ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_stripe_cardholder (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      user_id VARCHAR,
      name VARCHAR,
      email VARCHAR,
      phone VARCHAR,
      auth_tier VARCHAR,
      stripe_cardholder_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_cardholder_user_id ON vertex_stripe_cardholder (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_cardholder_stripe_id ON vertex_stripe_cardholder (stripe_cardholder_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_stripe_issued_card (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      cardholder_id VARCHAR,
      user_id VARCHAR,
      card_type VARCHAR,
      last_four VARCHAR,
      currency VARCHAR,
      spending_limit_amount BIGINT,
      spending_limit_interval VARCHAR,
      stripe_card_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_issued_card_user_id ON vertex_stripe_issued_card (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_issued_card_cardholder ON vertex_stripe_issued_card (cardholder_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_issued_card_stripe_card_id ON vertex_stripe_issued_card (stripe_card_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_stripe_authorization (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      stripe_card_id VARCHAR,
      amount BIGINT,
      currency VARCHAR,
      decision VARCHAR,
      reason VARCHAR,
      available_before BIGINT,
      available_after BIGINT,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_auth_user_created ON vertex_stripe_authorization (user_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_auth_card_created ON vertex_stripe_authorization (card_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_auth_decision ON vertex_stripe_authorization (decision)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_stripe_card_credit_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      amount BIGINT,
      allocated_total BIGINT,
      consumed_total BIGINT,
      available_total BIGINT,
      destination_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_alloc_card_created ON vertex_stripe_card_credit_allocation (card_id, created_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_stripe_card_credit_consumption (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      stripe_card_id VARCHAR,
      amount BIGINT,
      allocated_total BIGINT,
      consumed_total BIGINT,
      available_total BIGINT,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_consumption_card_created ON vertex_stripe_card_credit_consumption (card_id, created_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_stripe_spending_limit (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      amount BIGINT,
      interval VARCHAR,
      categories_json VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_spending_limit_card_created ON vertex_stripe_spending_limit (card_id, created_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_stripe_cardholder_card (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      cardholder_vid VARCHAR,
      card_vid VARCHAR,
      cardholder_id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_stripe_edge_cardholder_card ON edge_stripe_cardholder_card (cardholder_id, card_id)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_stripe_cardholder_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_stripe_cardholder
    GROUP BY actor_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_stripe_issued_card_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_stripe_issued_card
    GROUP BY actor_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_stripe_authorization_count AS
    SELECT actor_id, count(*)::bigint AS cnt
    FROM vertex_stripe_authorization
    GROUP BY actor_id
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_stripe_authorization_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_stripe_issued_card_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_stripe_cardholder_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_shigotoba_company_profile_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_shigotoba_job_posting_count`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_stripe_cardholder_card`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_stripe_spending_limit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_stripe_card_credit_consumption`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_stripe_card_credit_allocation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_stripe_authorization`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_stripe_issued_card`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_stripe_cardholder`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_shigotoba_posting_company`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shigotoba_company_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shigotoba_job_posting`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_auth_account`.execute(db);
}
