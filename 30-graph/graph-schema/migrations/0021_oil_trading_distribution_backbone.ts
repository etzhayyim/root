import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0021: oil trading + distribution backbone.
 *
 * Completes the next reverse-topology slice after upstream/midstream/refining:
 * trader deals, offtake contracts, product terminals and wholesale hubs.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oil_trade (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      trade_id VARCHAR,
      trader_did VARCHAR,
      counterparty_did VARCHAR,
      commodity VARCHAR,
      grade_code VARCHAR,
      benchmark_code VARCHAR,
      country_code VARCHAR,
      volume BIGINT,
      unit VARCHAR,
      price_basis VARCHAR,
      delivery_window VARCHAR,
      status VARCHAR,
      collection VARCHAR
    )`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_offtake_contract (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      contract_id VARCHAR,
      seller_did VARCHAR,
      buyer_did VARCHAR,
      commodity VARCHAR,
      benchmark_code VARCHAR,
      volume BIGINT,
      unit VARCHAR,
      delivery_term VARCHAR,
      country_code VARCHAR,
      status VARCHAR,
      collection VARCHAR
    )`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_product_terminal (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      terminal_code VARCHAR,
      locode VARCHAR,
      country_code VARCHAR,
      operator_did VARCHAR,
      product_family VARCHAR,
      storage_capacity BIGINT,
      status VARCHAR,
      collection VARCHAR
    )`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wholesale_hub (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      repo VARCHAR,
      hub_code VARCHAR,
      country_code VARCHAR,
      operator_did VARCHAR,
      hub_type VARCHAR,
      product_family VARCHAR,
      throughput_bpd BIGINT,
      status VARCHAR,
      collection VARCHAR
    )`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_wholesale_hub`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_product_terminal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_offtake_contract`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oil_trade`.execute(db);
}
