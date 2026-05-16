import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_insatsu_print_partner (
      vertex_id VARCHAR PRIMARY KEY,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      actor_id VARCHAR,
      partner_did VARCHAR,
      slug VARCHAR,
      display_name VARCHAR,
      country VARCHAR,
      region VARCHAR,
      print_methods JSONB,
      mail_classes JSONB,
      supports_certified_mail BOOLEAN,
      daily_capacity_pages BIGINT,
      base_cost_usd DOUBLE PRECISION,
      per_page_usd DOUBLE PRECISION,
      service_levels JSONB,
      downstream_actor_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_insatsu_print_mail_job (
      vertex_id VARCHAR PRIMARY KEY,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      actor_id VARCHAR,
      job_id VARCHAR,
      status VARCHAR,
      document_url TEXT,
      destination_country VARCHAR,
      recipient_name VARCHAR,
      address_line1 TEXT,
      postal_code VARCHAR,
      page_count BIGINT,
      quantity BIGINT,
      print_method VARCHAR,
      mail_class VARCHAR,
      service_level VARCHAR,
      partner_did VARCHAR,
      partner_display_name VARCHAR,
      route_type VARCHAR,
      downstream_actor_did VARCHAR,
      estimated_cost_usd DOUBLE PRECISION,
      estimated_total_days BIGINT,
      case_id VARCHAR,
      subject TEXT,
      downstream_dispatch JSONB,
      created_at VARCHAR
    )
  `.execute(db);

  for (const table of ["edge_insatsu_partner_mail_job", "edge_insatsu_job_downstream_actor"]) {
    await sql`
      CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
        edge_id VARCHAR PRIMARY KEY,
        src_vid VARCHAR,
        dst_vid VARCHAR,
        relation VARCHAR,
        job_id VARCHAR,
        sensitivity_ord BIGINT,
        owner_did VARCHAR,
        actor_id VARCHAR,
        created_at VARCHAR
      )
    `.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_job`)} ON ${sql.table(table)} (job_id)`.execute(db);
  }

  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_partner_did ON vertex_insatsu_print_partner (partner_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_partner_slug ON vertex_insatsu_print_partner (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_partner_country_region ON vertex_insatsu_print_partner (country, region)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_partner_downstream ON vertex_insatsu_print_partner (downstream_actor_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_partner_print_methods ON vertex_insatsu_print_partner USING GIN (print_methods)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_partner_mail_classes ON vertex_insatsu_print_partner USING GIN (mail_classes)`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_job_id ON vertex_insatsu_print_mail_job (job_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_job_status_created ON vertex_insatsu_print_mail_job (status, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_job_destination ON vertex_insatsu_print_mail_job (destination_country)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_job_partner ON vertex_insatsu_print_mail_job (partner_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_job_downstream ON vertex_insatsu_print_mail_job (downstream_actor_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_insatsu_job_case ON vertex_insatsu_print_mail_job (case_id)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_insatsu_partner_capacity AS
    SELECT
      partner_did,
      max(slug) AS slug,
      max(display_name) AS display_name,
      max(country) AS country,
      max(region) AS region,
      max(downstream_actor_did) AS downstream_actor_did,
      max(daily_capacity_pages) AS daily_capacity_pages,
      min(base_cost_usd) AS base_cost_usd,
      min(per_page_usd) AS per_page_usd,
      count(*) AS profile_versions
    FROM vertex_insatsu_print_partner
    GROUP BY partner_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_insatsu_print_mail_job_status AS
    SELECT
      status,
      destination_country,
      partner_did,
      count(*) AS job_count,
      sum(page_count * quantity) AS total_pages,
      sum(estimated_cost_usd) AS estimated_cost_usd,
      max(created_at) AS latest_created_at
    FROM vertex_insatsu_print_mail_job
    GROUP BY status, destination_country, partner_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_insatsu_print_mail_job_status`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_insatsu_partner_capacity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_insatsu_job_downstream_actor`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_insatsu_partner_mail_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_insatsu_print_mail_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_insatsu_print_partner`.execute(db);
}
